"""Import unmodified buildingSMART IDS TestCases (CC BY-ND 4.0) for open-corpora.

Honesty:
- Copies files **unmodified** (NoDerivatives). Attribution NOTICE required.
- Regression / binary match only — never product accuracy / >90%.
- Fails closed if source missing or license gate not satisfied.
- Does not invent case counts; writes honest_case_count from discovered pairs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

CLAIM_BOUNDARY = (
    "Unmodified buildingSMART IDS TestCases (CC BY-ND 4.0). "
    "Regression/binary match only — NOT product accuracy. Never claim >90%."
)

# Prefer an explicit --commit pin. Safe default: require --commit OR --source-dir.
# --allow-floating-tip downloads the development branch tip for local experiments only.
DEFAULT_REPO = "buildingSMART/IDS"
TESTCASES_REL = Path("Documentation") / "ImplementersDocumentation" / "TestCases"
NOTICE_TEXT = """buildingSMART IDS TestCases
Source: https://github.com/buildingSMART/IDS
License: Creative Commons Attribution-NoDerivatives 4.0 International (CC BY-ND 4.0)
https://creativecommons.org/licenses/by-nd/4.0/

These files are redistributed unmodified for implementer regression testing.
Do not modify TestCases contents. Attribution must be preserved.
AeroBIM claim boundary: regression/timing only — NOT product accuracy.
"""


def _win_path(path: Path) -> str:
    import os

    text = str(path.resolve())
    if os.name == "nt" and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def _rmtree(path: Path) -> None:
    if path.exists():
        shutil.rmtree(_win_path(path))


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def sha256_file(path: Path) -> str:
    import os

    digest = hashlib.sha256()
    text = str(path.resolve())
    if os.name == "nt" and not text.startswith("\\\\?\\"):
        text = "\\\\?\\" + text
    with open(text, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def discover_ids_ifc_pairs(testcases_root: Path) -> list[dict[str, str]]:
    """Find pass-/fail- IDS+IFC pairs under TestCases (unmodified layout)."""

    pairs: list[dict[str, str]] = []
    if not testcases_root.is_dir():
        return pairs
    for ids_path in sorted(testcases_root.rglob("*.ids")):
        stem = ids_path.name
        prefix_ok = stem.startswith("pass-") or stem.startswith("fail-")
        if not prefix_ok:
            continue
        ifc_path = ids_path.with_suffix(".ifc")
        if not ifc_path.is_file():
            # Some suites use same stem in sibling folder; skip unpaired.
            continue
        rel_ids = ids_path.relative_to(testcases_root).as_posix()
        rel_ifc = ifc_path.relative_to(testcases_root).as_posix()
        case_id = ids_path.stem
        pairs.append(
            {
                "case_id": case_id,
                "ids_rel": rel_ids,
                "ifc_rel": rel_ifc,
                "expected_outcome": "pass" if stem.startswith("pass-") else "fail",
            }
        )
    return pairs


def copy_unmodified_tree(src: Path, dest: Path) -> int:
    """Copy tree byte-for-byte; returns file count.

    Uses Windows long-path prefixes when needed (BSI TestCases have very long names).
    """

    import os

    def _win(path: Path) -> str:
        text = str(path.resolve())
        if os.name == "nt" and not text.startswith("\\\\?\\"):
            return "\\\\?\\" + text
        return text

    if dest.exists():
        shutil.rmtree(_win(dest) if dest.exists() else dest)
    dest.mkdir(parents=True, exist_ok=True)
    count = 0
    for path in src.rglob("*"):
        if path.is_file():
            rel = path.relative_to(src)
            target = dest / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(_win(path), _win(target))
            count += 1
    return count


def download_repo_zip(*, repo: str, commit: str, dest_zip: Path) -> None:
    url = f"https://github.com/{repo}/archive/{commit}.zip"
    dest_zip.parent.mkdir(parents=True, exist_ok=True)
    try:
        with urllib.request.urlopen(url, timeout=120) as response:  # noqa: S310
            dest_zip.write_bytes(response.read())
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"failed to download {url}: {exc}. "
            "Provide --source-dir pointing at a local buildingSMART/IDS clone."
        ) from exc


def extract_testcases(zip_path: Path, extract_to: Path) -> Path:
    import os

    def _win(path: Path) -> str:
        text = str(path.resolve())
        if os.name == "nt" and not text.startswith("\\\\?\\"):
            return "\\\\?\\" + text
        return text

    extract_to.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as archive:
        for info in archive.infolist():
            # Skip absolute / traversal members
            name = info.filename.replace("\\", "/")
            if name.startswith("/") or ".." in name.split("/"):
                continue
            target = extract_to / name
            if info.is_dir():
                Path(_win(target)).mkdir(parents=True, exist_ok=True)
                continue
            Path(_win(target.parent)).mkdir(parents=True, exist_ok=True)
            with archive.open(info) as src, open(_win(target), "wb") as dst:
                shutil.copyfileobj(src, dst)
    children = [p for p in extract_to.iterdir() if p.is_dir()]
    if not children:
        raise RuntimeError(f"empty extract: {extract_to}")
    root = children[0]
    testcases = root / TESTCASES_REL
    if not testcases.is_dir():
        raise RuntimeError(f"TestCases not found under {root / TESTCASES_REL}")
    return testcases


def materialize_pairs(
    testcases: Path,
    dest: Path,
    pairs: list[dict[str, str]],
) -> list[dict[str, Any]]:
    """Copy pair bytes unmodified into short Windows-safe case folders."""

    import os

    def _win(path: Path) -> str:
        text = str(path.resolve())
        if os.name == "nt" and not text.startswith("\\\\?\\"):
            return "\\\\?\\" + text
        return text

    if dest.exists():
        shutil.rmtree(_win(dest))
    dest.mkdir(parents=True, exist_ok=True)
    enriched: list[dict[str, Any]] = []
    for index, pair in enumerate(pairs, start=1):
        case_dir = dest / "cases" / f"{index:04d}"
        case_dir.mkdir(parents=True, exist_ok=True)
        src_ids = testcases / pair["ids_rel"]
        src_ifc = testcases / pair["ifc_rel"]
        # Keep original basename when short; otherwise hashed name (content unchanged).
        ids_name = Path(pair["ids_rel"]).name
        ifc_name = Path(pair["ifc_rel"]).name
        if len(ids_name) > 100:
            ids_name = f"{sha256_file(src_ids)[:16]}.ids"
        if len(ifc_name) > 100:
            ifc_name = f"{sha256_file(src_ifc)[:16]}.ifc"
        dst_ids = case_dir / ids_name
        dst_ifc = case_dir / ifc_name
        shutil.copy2(_win(src_ids), _win(dst_ids))
        shutil.copy2(_win(src_ifc), _win(dst_ifc))
        rel_ids = dst_ids.relative_to(dest).as_posix()
        rel_ifc = dst_ifc.relative_to(dest).as_posix()
        enriched.append(
            {
                "case_id": pair["case_id"],
                "expected_outcome": pair["expected_outcome"],
                "original_ids_rel": pair["ids_rel"],
                "original_ifc_rel": pair["ifc_rel"],
                "ids_rel": rel_ids,
                "ifc_rel": rel_ifc,
                "ids_sha256": sha256_file(dst_ids),
                "ifc_sha256": sha256_file(dst_ifc),
            }
        )
    return enriched


def write_regression_profile(
    *,
    dest_profile: Path,
    cases: list[dict[str, Any]],
    samples_prefix: str,
    commit: str,
) -> None:
    profile_cases = []
    for case in cases:
        expected_passed = case["expected_outcome"] == "pass"
        profile_cases.append(
            {
                "case_id": case["case_id"],
                "ids_path": f"{samples_prefix}/{case['ids_rel']}",
                "ifc_path": f"{samples_prefix}/{case['ifc_rel']}",
                "expected_passed": expected_passed,
                "pins": {
                    "ids_sha256": case["ids_sha256"],
                    "ifc_sha256": case["ifc_sha256"],
                },
            }
        )
    payload = {
        "schema_version": "1.0.0",
        "profile_id": "open-corpora-regression-bsi",
        "profile_kind": "regression",
        "description": (
            "Binary IDS↔IFC pass/fail from buildingSMART IDS TestCases (CC BY-ND 4.0). "
            "Engineering regression labels only — not expert TP/FP product labels."
        ),
        "honest_case_count": len(profile_cases),
        "target_case_count_note": (
            "WP-06 target ≥250 official pass/fail pairs when license-cleared. "
            f"Current honest count: {len(profile_cases)}. Do not claim a larger count."
        ),
        "claim_boundary": CLAIM_BOUNDARY,
        "source": {
            "pins": f"{samples_prefix}/IMPORT_PINS.json",
            "license": "CC-BY-ND-4.0",
            "upstream_commit": commit,
        },
        "cases": profile_cases,
    }
    dest_profile.parent.mkdir(parents=True, exist_ok=True)
    dest_profile.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def write_import_pins(
    *,
    dest: Path,
    cases: list[dict[str, Any]],
    commit: str,
) -> None:
    from datetime import UTC, datetime

    payload = {
        "artifact_type": "buildingsmart_ids_import_pins",
        "schema_version": "1.0.0",
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "upstream_repo": f"https://github.com/{DEFAULT_REPO}",
        "upstream_commit": commit,
        "upstream_prefix": TESTCASES_REL.as_posix(),
        "license": "CC-BY-ND-4.0",
        "case_count": len(cases),
        "min_target_cases": 250,
        "target_met": len(cases) >= 250,
        "claim_boundary": CLAIM_BOUNDARY,
        "cases": [
            {
                "case_id": case["case_id"],
                "ids_path": case["ids_rel"],
                "ifc_path": case["ifc_rel"],
                "expected_passed": case["expected_outcome"] == "pass",
                "pins": {
                    "ids_sha256": case["ids_sha256"],
                    "ifc_sha256": case["ifc_sha256"],
                },
                "upstream": {
                    "ids": case.get("original_ids_rel"),
                    "ifc": case.get("original_ifc_rel"),
                },
            }
            for case in cases
        ],
    }
    (dest / "IMPORT_PINS.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def update_license_manifest(repo: Path, *, commit: str, case_count: int, dest_rel: str) -> None:
    manifest_path = repo / "audit" / "dataset_license_manifest.json"
    if not manifest_path.is_file():
        return
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return
    assets = manifest.get("assets")
    if not isinstance(assets, list):
        return
    entry = {
        "id": "ids-test-suite-bsi",
        "path": dest_rel,
        "license": "CC-BY-ND-4.0",
        "public_benchmark": "ALLOWED_WITH_ATTRIBUTION_UNMODIFIED",
        "source": f"https://github.com/{DEFAULT_REPO}/tree/{commit}/{TESTCASES_REL.as_posix()}",
        "commit": commit,
        "honest_case_count": case_count,
        "claim_boundary": CLAIM_BOUNDARY,
        "note": "Unmodified TestCases only (NoDerivatives).",
    }
    replaced = False
    for idx, asset in enumerate(assets):
        if isinstance(asset, dict) and asset.get("id") in {
            "ids-test-suite",
            "ids-test-suite-bsi",
        }:
            assets[idx] = {**asset, **entry} if asset.get("id") == "ids-test-suite" else entry
            if asset.get("id") == "ids-test-suite":
                assets[idx] = entry
            replaced = True
            break
    if not replaced:
        assets.append(entry)
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def run_import(
    *,
    source_dir: Path | None,
    commit: str | None,
    allow_floating_tip: bool,
    max_cases: int | None,
) -> dict[str, Any]:
    repo = repo_root()
    dest_rel = "samples/ids/buildingsmart-testcases"
    dest = repo / dest_rel
    work = repo / "artifacts" / "ids-import-work"
    work.mkdir(parents=True, exist_ok=True)

    if source_dir is not None:
        testcases = Path(source_dir)
        if not testcases.is_dir():
            raise RuntimeError(f"--source-dir not a directory: {testcases}")
        # Accept either TestCases root or IDS repo root.
        if (testcases / TESTCASES_REL).is_dir():
            testcases = testcases / TESTCASES_REL
        resolved_commit = commit or "local-source-dir"
    else:
        if not commit and not allow_floating_tip:
            raise RuntimeError(
                "Refuse floating tip download. Pass --commit <sha> or --source-dir "
                "<local IDS clone>, or --allow-floating-tip for development tip."
            )
        pin = commit or "development"
        zip_path = work / f"ids-{pin}.zip"
        if not zip_path.is_file():
            download_repo_zip(repo=DEFAULT_REPO, commit=pin, dest_zip=zip_path)
        extract_root = work / f"extract-{pin}"
        existing = extract_root / f"IDS-{pin}" / TESTCASES_REL
        # Also accept GitHub's IDS-development style folder.
        if not existing.is_dir():
            pattern = "IDS-*/Documentation/ImplementersDocumentation/TestCases"
            candidates = list(extract_root.glob(pattern))
            existing = candidates[0] if candidates else existing
        if existing.is_dir():
            testcases = existing
        else:
            if extract_root.exists():
                _rmtree(extract_root)
            testcases = extract_testcases(zip_path, extract_root)
        resolved_commit = pin

    pairs = discover_ids_ifc_pairs(testcases)
    if max_cases is not None:
        pairs = pairs[: max(0, max_cases)]
    if not pairs:
        raise RuntimeError(
            f"no pass-/fail- IDS+IFC pairs under {testcases}; import aborted (fail-closed)"
        )

    enriched = materialize_pairs(testcases, dest, pairs)
    (dest / "NOTICE").write_text(NOTICE_TEXT, encoding="utf-8")
    (dest / "LICENSE_CC_BY_ND_4.0.txt").write_text(
        "See https://creativecommons.org/licenses/by-nd/4.0/legalcode\n",
        encoding="utf-8",
    )

    profile_path = (
        repo / "samples" / "benchmarks" / "open-corpora" / "profiles" / "regression-bsi.json"
    )
    write_regression_profile(
        dest_profile=profile_path,
        cases=enriched,
        samples_prefix=dest_rel,
        commit=resolved_commit,
    )
    write_import_pins(dest=dest, cases=enriched, commit=resolved_commit)
    update_license_manifest(
        repo, commit=resolved_commit, case_count=len(enriched), dest_rel=dest_rel
    )

    # Wire into open-corpora manifest if present.
    oc_manifest = repo / "samples" / "benchmarks" / "open-corpora" / "manifest.json"
    if oc_manifest.is_file():
        try:
            man = json.loads(oc_manifest.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            man = {}
        profiles = man.get("profiles")
        if isinstance(profiles, list):
            entry = {
                "profile_id": "open-corpora-regression-bsi",
                "path": "samples/benchmarks/open-corpora/profiles/regression-bsi.json",
                "kind": "regression",
            }
            if not any(
                isinstance(p, dict) and p.get("profile_id") == entry["profile_id"] for p in profiles
            ):
                profiles.append(entry)
            oc_manifest.write_text(
                json.dumps(man, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )

    return {
        "artifact_type": "buildingsmart_ids_testcase_import",
        "claim_boundary": CLAIM_BOUNDARY,
        "license": "CC-BY-ND-4.0",
        "source_commit": resolved_commit,
        "dest": dest_rel,
        "files_copied": len(enriched) * 2,
        "honest_case_count": len(enriched),
        "profile": str(profile_path.as_posix()),
        "note": "Unmodified file bytes; short case folders for path limits — not product accuracy",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=None,
        help="Local buildingSMART/IDS repo root or TestCases directory",
    )
    parser.add_argument("--commit", default=None, help="Git commit SHA to download from GitHub")
    parser.add_argument(
        "--allow-floating-tip",
        action="store_true",
        help="Allow downloading development tip when --commit omitted (not for release pins)",
    )
    parser.add_argument(
        "--max-cases",
        type=int,
        default=None,
        help="Optional cap for first-wave import (honest count = imported N)",
    )
    args = parser.parse_args(argv)
    try:
        report = run_import(
            source_dir=args.source_dir,
            commit=args.commit,
            allow_floating_tip=args.allow_floating_tip,
            max_cases=args.max_cases,
        )
    except Exception as exc:  # noqa: BLE001 — CLI fail-closed surface
        print(json.dumps({"status": "FAILED", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
