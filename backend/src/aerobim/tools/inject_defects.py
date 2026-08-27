"""Deterministic defect injector for recall measurement (below the validator).

Mutates IFC STEP text and sheet/brief sidecars **before** AeroBIM sees them.
Does not call the analyze API. Does not write ``summary.passed``. Does not
claim recall until a clean pack exists and a protocol is run.

Claim boundary: injected defects are a mutation test, not Samolet accuracy,
not product accuracy >90%, not RT-001 closed. Checkpoint NO_GO.

Example::

    python -m aerobim.tools.inject_defects \\
        --source samples/packs/clean_pd \\
        --output var/injected \\
        --seed 20260824
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import shutil
from pathlib import Path
from typing import Any

DEFECT_CLASSES: tuple[str, ...] = (
    "AREA_MISMATCH",
    "LEVEL_MISMATCH",
    "PD_RD_DIVERGENCE",
    "TZ_UNSATISFIED",
    "MISSING_ELEMENT",
    "UNIT_MISMATCH",
    "CALC_INCONSISTENCY",
    "IDS_VIOLATION",
    "CONTROL",
)

_IFC_SUFFIXES = {".ifc", ".ifcxml"}
_TEXT_SUFFIXES = {".txt", ".csv", ".md", ".tsv"}
_MAX_FILE_BYTES = 80 * 1024 * 1024


def _posix(path: Path) -> str:
    return path.resolve().as_posix().lower()


def _reject_unsafe_inject_trees(source: Path, output: Path) -> None:
    """Refuse nested trees and gitignored NDA roots (RT-INJ-NEST / RT-INJ-NDA)."""

    src = source.resolve()
    out = output.resolve()
    if src == out:
        raise ValueError("inject_defects output must not be the source tree")
    if src in out.parents or out in src.parents:
        raise ValueError("inject_defects source and output must not nest")
    posix = _posix(src)
    if "/samples/customer" in posix:
        raise ValueError("gitignored customer trees cannot be inject_defects sources")
    if "/aerobim/files/" in posix or posix.endswith("/aerobim/files"):
        raise ValueError("owner files/ trees cannot be inject_defects sources")


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _copy_tree(source: Path, dest: Path) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(source, dest)


def _iter_files(root: Path, suffixes: set[str]) -> list[Path]:
    return sorted(
        path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in suffixes
    )


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")


def _mutate_area(text: str, rng: random.Random) -> tuple[str, str]:
    match = re.search(r"(IFCQUANTITYAREA\([^,]*,[^,]*,[^,]*,)([0-9]+(?:\.[0-9]+)?)", text, re.I)
    if match:
        original = match.group(2)
        mutated = f"{float(original) * (1.15 + rng.random() * 0.2):.3f}"
        return text[: match.start(2)] + mutated + text[
            match.end(2) :
        ], f"area {original}->{mutated}"
    match = re.search(r"\b([0-9]+\.[0-9]+)\b", text)
    if not match:
        return text, "no-area-token"
    original = match.group(1)
    mutated = f"{float(original) + 3.5:.3f}"
    return text[: match.start(1)] + mutated + text[match.end(1) :], f"numeric {original}->{mutated}"


def _mutate_level(text: str, rng: random.Random) -> tuple[str, str]:
    match = re.search(
        r"(IFCBUILDINGSTOREY\([^)]*?\.ELEMENT\.,)([-+]?[0-9]+(?:\.[0-9]+)?)",
        text,
        re.I,
    )
    if match:
        original = match.group(2)
        mutated = f"{float(original) + 1.2 + rng.random():.3f}"
        return text[: match.start(2)] + mutated + text[
            match.end(2) :
        ], f"storey {original}->{mutated}"
    if "IFCBUILDINGSTOREY" in text.upper():
        mutated = text.replace("Level 1", "Level 9", 1).replace("Этаж 1", "Этаж 9", 1)
        if mutated != text:
            return mutated, "storey-name"
    return text, "no-storey-token"


def _mutate_missing_element(text: str) -> tuple[str, str]:
    pattern = re.compile(r"^#\d+=IFCWALL.*?;\s*$", re.I | re.M)
    match = pattern.search(text)
    if not match:
        pattern = re.compile(r"^#\d+=IFCSPACE.*?;\s*$", re.I | re.M)
        match = pattern.search(text)
    if not match:
        return text, "no-element-token"
    return text[: match.start()] + text[match.end() :], f"removed {match.group(0)[:48]}"


def _mutate_unit(text: str) -> tuple[str, str]:
    if ".MILLI." in text:
        return text.replace(".MILLI.", ".", 1), "si-prefix-milli-removed"
    if ".METRE." in text:
        return text.replace(".METRE.", ".FOOT.", 1), "metre-to-foot"
    return text, "no-unit-token"


def _mutate_ids(text: str) -> tuple[str, str]:
    for token in ("RusSet_Common", "RUS_Name", "RUS_Area", "GrossFloorArea"):
        if token in text:
            return text.replace(token, f"{token}X", 1), f"ids-token {token}"
    return text, "no-ids-token"


def _mutate_text_number(text: str, delta: float) -> tuple[str, str]:
    match = re.search(r"([0-9]+(?:[.,][0-9]+)?)", text)
    if not match:
        return text, "no-numeric"
    original = match.group(1)
    value = float(original.replace(",", "."))
    mutated = f"{value + delta:.3f}"
    return text[: match.start(1)] + mutated + text[match.end(1) :], f"{original}->{mutated}"


def _apply_class(defect_class: str, dest: Path, rng: random.Random) -> dict[str, Any]:
    record: dict[str, Any] = {
        "class": defect_class,
        "applied": False,
        "locator": None,
        "note": None,
    }
    ifc_files = _iter_files(dest, _IFC_SUFFIXES)
    text_files = _iter_files(dest, _TEXT_SUFFIXES)

    def _mutate_first_ifc(mutator: Any) -> dict[str, Any]:
        if not ifc_files:
            record["note"] = "no-ifc"
            return record
        path = ifc_files[0]
        original = _read_text(path)
        mutated, note = mutator(original)
        if mutated == original:
            record["note"] = note
            return record
        _write_text(path, mutated)
        record["applied"] = True
        record["locator"] = str(path.relative_to(dest)).replace("\\", "/")
        record["note"] = note
        record["source_sha256"] = _sha256_bytes(original.encode("utf-8"))
        record["mutated_sha256"] = _sha256_bytes(mutated.encode("utf-8"))
        return record

    def _mutate_named_text(needles: tuple[str, ...], delta: float) -> dict[str, Any]:
        candidates = [
            path for path in text_files if any(needle in path.name.lower() for needle in needles)
        ] or text_files
        if not candidates:
            record["note"] = "no-text-sidecar"
            return record
        path = candidates[0]
        original = _read_text(path)
        mutated, note = _mutate_text_number(original, delta)
        if mutated == original:
            record["note"] = note
            return record
        _write_text(path, mutated)
        record["applied"] = True
        record["locator"] = str(path.relative_to(dest)).replace("\\", "/")
        record["note"] = note
        return record

    if defect_class == "CONTROL":
        record["applied"] = True
        record["note"] = "unmutated-control"
        return record
    if defect_class == "AREA_MISMATCH":
        return _mutate_first_ifc(lambda text: _mutate_area(text, rng))
    if defect_class == "LEVEL_MISMATCH":
        return _mutate_first_ifc(lambda text: _mutate_level(text, rng))
    if defect_class == "MISSING_ELEMENT":
        return _mutate_first_ifc(_mutate_missing_element)
    if defect_class == "UNIT_MISMATCH":
        return _mutate_first_ifc(_mutate_unit)
    if defect_class == "IDS_VIOLATION":
        return _mutate_first_ifc(_mutate_ids)
    if defect_class == "PD_RD_DIVERGENCE":
        return _mutate_named_text(("rd", "pd", "sheet", "vedom"), 4.0)
    if defect_class == "TZ_UNSATISFIED":
        return _mutate_named_text(("tz", "brief", "eir"), 2.0)
    if defect_class == "CALC_INCONSISTENCY":
        return _mutate_named_text(("calc", "note", "kmd"), 5.0)
    record["note"] = "unknown-class"
    return record


def inject_defects(
    source: Path,
    output: Path,
    *,
    seed: int = 20260824,
    classes: tuple[str, ...] | None = None,
) -> dict[str, Any]:
    """Copy ``source`` per class, mutate below the validator, write a manifest."""

    if not source.is_dir():
        raise FileNotFoundError(f"source pack directory not found: {source}")
    _reject_unsafe_inject_trees(source, output)
    source_posix = source.resolve().as_posix().lower()
    if "moscow-agr-examples" in source_posix:
        raise ValueError(
            "City AGR CIM examples are not a clean PD pack; inject_defects is blocked. "
            "Checkpoint NO_GO."
        )
    selected = classes or DEFECT_CLASSES
    unknown = [name for name in selected if name not in DEFECT_CLASSES]
    if unknown:
        raise ValueError(f"unknown defect classes: {unknown}")
    output.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    variants: list[dict[str, Any]] = []
    for defect_class in selected:
        dest = output / defect_class.lower()
        _copy_tree(source, dest)
        record = _apply_class(defect_class, dest, rng)
        variants.append(record)

    manifest: dict[str, Any] = {
        "artifact": "injection_manifest",
        "seed": seed,
        "source": str(source.resolve()),
        "source_tree_hint": source.name,
        "claim_boundary": (
            "Mutation test inputs. Not Samolet accuracy. Not product accuracy. "
            "Recall is not measured until a clean pack passes moscow_agr_2026 "
            "with summary.passed=true. Checkpoint NO_GO. RT-001 stays OPEN."
        ),
        "injects_below_validator": True,
        "calls_aerobim_api": False,
        "variants": variants,
    }
    manifest_path = output / "injection_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    manifest["manifest_sha256"] = _sha256_file(manifest_path)
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True, help="Clean pack directory")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20260824)
    parser.add_argument(
        "--classes",
        default="",
        help="Comma-separated subset of defect classes (default: all + CONTROL)",
    )
    args = parser.parse_args(argv)
    classes = (
        tuple(part.strip().upper() for part in args.classes.split(",") if part.strip()) or None
    )
    manifest = inject_defects(
        args.source.resolve(),
        args.output.resolve(),
        seed=args.seed,
        classes=classes,
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
