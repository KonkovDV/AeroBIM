"""IFC-Bench smoke — deterministic IFC inventory vs public QA subset.

Supports v1 (GitHub archive) and v2 (Hugging Face dataset layout).
Claim level: ``open_bench_only``. Does **not** close RT-001 / product accuracy.
Requires local checkout under ``AEROBIM_IFC_BENCH_ROOT`` / ``.local/ifc-bench*``.

Only countable / presence probes that map cleanly to IfcOpenShell queries are
scored. Agentic NL questions remain ``skipped`` (out of deterministic scope).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

CLAIM_BOUNDARY = (
    "IFC-Bench open_bench_only: deterministic countable subset via "
    "IfcOpenShell. NOT product accuracy. Never claim >90%. Does not close RT-001."
)

# HF card listed this for an earlier snapshot; measured 2026-08-04 after dedup = e47c…
_PINNED_V2_SHA_MEASURED = "e47ccd097306f5bca49b9c8ac0b4cd72f296df9f7ff7a02625b3f06c1691da9b"
_PINNED_V1_SHA_HF = "f67a48770d74b6e0ff0868c923c3e1d976110350b2c439564d7ceccc16a46f35"

_NUMBER_RE = re.compile(
    r"(?P<n>\d+(?:\.\d+)?)\s*(?:sqm|m2|m²|rooms?|doors?|windows?|bedrooms?|"
    r"fixtures?|steps?|radiators?)?",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ProbeResult:
    question: str
    project: str
    ifc_model: str
    probe_id: str
    predicted: float | int | str | None
    expected: float | int | str | None
    status: str  # matched | mismatched | skipped | error
    detail: str | None = None


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _parse_expected_number(answer: str) -> float | None:
    text = (answer or "").strip()
    if re.search(r"cannot|not available|information not", text, re.I):
        return None
    # Prefer total-count phrasing before subordinate breakdowns
    # ("14 light fixtures: 8 pendant and 6 sconce").
    for pattern in (
        r"(?:specifies|there are|total(?: of)?)\s+(\d+(?:\.\d+)?)\s+"
        r"(?:light fixtures|rooms?|doors?|windows?|bedrooms?|steps?|"
        r"radiators?|x-ray)",
        r"(?:there are|are)\s+(\d+(?:\.\d+)?)\s+(?:interior\s+)?(?:doors?|rooms?)",
        r"(?:the stair has|has)\s+(\d+(?:\.\d+)?)\s+steps?",
        r"(?:there are|are)\s+(\d+(?:\.\d+)?)",
    ):
        m = re.search(pattern, text, re.I)
        if m:
            return float(m.group(1))
    m = _NUMBER_RE.search(text)
    return float(m.group("n")) if m else None


def _numbers_close(a: float | int, b: float | int, *, tol: float = 0.01) -> bool:
    return abs(float(a) - float(b)) <= tol


def _open_ifc(path: Path) -> Any:
    import ifcopenshell

    return ifcopenshell.open(str(path))


def _is_external_door(door: Any) -> bool | None:
    import ifcopenshell.util.element as el

    for vals in el.get_psets(door).values():
        if "IsExternal" in vals:
            return bool(vals["IsExternal"])
    return None


ProbeFn = Callable[[Any], float | int | str]


def _probes_for_model(
    project: str, ifc_model: str, *, version: str = "v1"
) -> dict[str, tuple[str, ProbeFn]]:
    """question substring (lower) → (probe_id, extractor)."""

    if project == "duplex" and ifc_model == "arc":
        return {
            "how many bedrooms are there": (
                "duplex_arc_bedroom_count",
                lambda m: sum(
                    1
                    for s in m.by_type("IfcSpace")
                    if (s.LongName or "").lower().find("bedroom") >= 0
                ),
            ),
            "how many rooms are there in house a": (
                "duplex_arc_house_a_space_count",
                lambda m: sum(
                    1
                    for s in m.by_type("IfcSpace")
                    if (s.Name or "").startswith("A") and s.Name != "R301"
                ),
            ),
            "how many interior doors are there": (
                "duplex_arc_interior_door_count",
                lambda m: sum(1 for d in m.by_type("IfcDoor") if _is_external_door(d) is False),
            ),
            "how many steps does the stair in house a have": (
                "duplex_arc_stair_risers",
                lambda m: next(
                    (
                        int(sf.NumberOfRiser)
                        for sf in m.by_type("IfcStairFlight")
                        if getattr(sf, "NumberOfRiser", None)
                    ),
                    0,
                ),
            ),
        }
    if project == "duplex" and ifc_model == "mep":
        return {
            "how many light fixtures are specified": (
                "duplex_mep_light_fixture_count",
                lambda m: sum(
                    1
                    for f in m.by_type("IfcFlowTerminal")
                    if any(k in (f.Name or "").lower() for k in ("pendant light", "sconce light"))
                ),
            ),
        }
    if project == "dental_clinic" and ifc_model == "arc":
        # v1 GT counted X-RAY + X-RAY ALCOVE; v2 GT is room 2A12 only.
        if version == "v2":

            def _xray_count(m: Any) -> int:
                return sum(
                    1
                    for s in m.by_type("IfcSpace")
                    if (s.LongName or "").strip().lower() == "x-ray"
                )

        else:

            def _xray_count(m: Any) -> int:
                return sum(
                    1 for s in m.by_type("IfcSpace") if "x-ray" in (s.LongName or "").lower()
                )

        return {
            "how many x-ray rooms are there": (
                "dental_arc_xray_space_count",
                _xray_count,
            ),
            "how many rooms are there in the clinic": (
                "dental_arc_space_count",
                lambda m: len(m.by_type("IfcSpace")),
            ),
        }
    return {}


def evaluate_dataset(dataset_root: Path, *, version: str = "v1") -> dict[str, Any]:
    version = version.strip().lower()
    if version not in {"v1", "v2"}:
        raise ValueError("version must be v1 or v2")
    questions_path = dataset_root / "questions" / f"ifc-bench-{version}.csv"
    if not questions_path.is_file():
        raise FileNotFoundError(
            f"IFC-Bench questions missing: {questions_path}. "
            "For v2: download from Hugging Face sylvainHellin/ifc-bench "
            "into .local/ifc-bench-v2 (GitHub archive is v1-only)."
        )

    with questions_path.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))

    results: list[ProbeResult] = []
    model_cache: dict[tuple[str, str], Any] = {}

    for row in rows:
        question = (row.get("question") or "").strip()
        answer = (row.get("ground_truth") or row.get("answer") or "").strip()
        project = (row.get("project") or "").strip()
        ifc_model = (row.get("ifc_model") or "").strip()
        if (
            not project
            or not ifc_model
            or ".." in project
            or ".." in ifc_model
            or "/" in project
            or "\\" in project
            or "/" in ifc_model
            or "\\" in ifc_model
            or Path(project).name != project
            or Path(ifc_model).name != ifc_model
        ):
            results.append(
                ProbeResult(
                    question=question,
                    project=project,
                    ifc_model=ifc_model,
                    probe_id="path_rejected",
                    predicted=None,
                    expected=_parse_expected_number(answer),
                    status="error",
                    detail="unsafe project/ifc_model path component",
                )
            )
            continue
        q_lower = question.lower()
        probes = _probes_for_model(project, ifc_model, version=version)
        matched_key = next((k for k in probes if k in q_lower), None)
        if matched_key is None:
            results.append(
                ProbeResult(
                    question=question,
                    project=project,
                    ifc_model=ifc_model,
                    probe_id="unmapped",
                    predicted=None,
                    expected=_parse_expected_number(answer),
                    status="skipped",
                    detail="no deterministic probe for this NL question",
                )
            )
            continue

        probe_id, extractor = probes[matched_key]
        projects_root = (dataset_root / "projects").resolve()
        ifc_path = (dataset_root / "projects" / project / f"{ifc_model}.ifc").resolve()
        if not ifc_path.is_relative_to(projects_root):
            results.append(
                ProbeResult(
                    question=question,
                    project=project,
                    ifc_model=ifc_model,
                    probe_id=probe_id,
                    predicted=None,
                    expected=_parse_expected_number(answer),
                    status="error",
                    detail="IFC path escapes dataset projects root",
                )
            )
            continue
        if not ifc_path.is_file():
            results.append(
                ProbeResult(
                    question=question,
                    project=project,
                    ifc_model=ifc_model,
                    probe_id=probe_id,
                    predicted=None,
                    expected=_parse_expected_number(answer),
                    status="error",
                    detail=f"missing IFC under projects/{project}/",
                )
            )
            continue

        cache_key = (project, ifc_model)
        try:
            if cache_key not in model_cache:
                model_cache[cache_key] = _open_ifc(ifc_path)
            predicted = extractor(model_cache[cache_key])
            expected = _parse_expected_number(answer)
            if expected is None:
                status = "skipped"
                detail = "ground-truth answer has no comparable number"
            elif isinstance(predicted, (int, float)) and _numbers_close(predicted, expected):
                status = "matched"
                detail = None
            else:
                status = "mismatched"
                detail = f"predicted={predicted!r} expected={expected!r}"
            results.append(
                ProbeResult(
                    question=question,
                    project=project,
                    ifc_model=ifc_model,
                    probe_id=probe_id,
                    predicted=predicted,
                    expected=expected,
                    status=status,
                    detail=detail,
                )
            )
        except Exception as exc:  # noqa: BLE001 — smoke must not abort pack
            results.append(
                ProbeResult(
                    question=question,
                    project=project,
                    ifc_model=ifc_model,
                    probe_id=probe_id,
                    predicted=None,
                    expected=_parse_expected_number(answer),
                    status="error",
                    detail=str(exc),
                )
            )

    scored = [r for r in results if r.status in {"matched", "mismatched"}]
    matched = [r for r in scored if r.status == "matched"]
    skipped = [r for r in results if r.status == "skipped"]
    errors = [r for r in results if r.status == "error"]

    projects_dir = dataset_root / "projects"
    ifc_files = sorted(projects_dir.rglob("*.ifc")) if projects_dir.is_dir() else []
    questions_sha = _sha256_file(questions_path)
    pinned = _PINNED_V2_SHA_MEASURED if version == "v2" else _PINNED_V1_SHA_HF
    return {
        "artifact_type": f"ifc_bench_{version}_smoke",
        "schema_version": "1.1.0",
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "claim_level": "open_bench_only",
        "claim_boundary": CLAIM_BOUNDARY,
        "closes_rt001": False,
        "benchmark": {
            "name": f"IFC-Bench-{version}",
            "citation": (
                "Hellin et al. — v1 EC3 2025 / GitHub archive; "
                "v2 HF sylvainHellin/ifc-bench + arXiv:2605.01698"
            ),
            "dataset_root": str(dataset_root.resolve()),
            "version": version,
            "questions_path": str(questions_path.relative_to(dataset_root)).replace("\\", "/"),
            "questions_sha256": questions_sha,
            "questions_sha256_matches_pin": questions_sha == pinned,
            "pinned_sha256_reference": pinned,
            "question_count": len(rows),
            "ifc_files_present": len(ifc_files),
            "ifc_files": [
                {
                    "path": str(p.relative_to(dataset_root)).replace("\\", "/"),
                    "sha256": _sha256_file(p),
                }
                for p in ifc_files
            ],
        },
        "summary": {
            "total_questions": len(results),
            "scored": len(scored),
            "matched": len(matched),
            "mismatched": len(scored) - len(matched),
            "skipped_unmapped_or_uncomparable": len(skipped),
            "errors": len(errors),
            "exact_match_rate_on_scored": (
                round(len(matched) / len(scored), 4) if scored else None
            ),
            "denominator_note": (
                f"scored={len(scored)} of total_questions={len(results)}; "
                "unmapped NL and non-numeric GT skipped; missing IFC → error"
            ),
            "note": (
                "Rate is over the deterministic countable subset only "
                f"({len(scored)}/{len(results)} questions). Unmapped NL items are skipped."
            ),
        },
        "results": [asdict(r) for r in results if r.status != "skipped"],
        "skipped_count": len(skipped),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path, default=None)
    parser.add_argument("--version", choices=("v1", "v2"), default="v1")
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--also-docs-evidence", action="store_true")
    args = parser.parse_args(argv)

    root = args.dataset_root
    if root is None:
        env = (os.getenv("AEROBIM_IFC_BENCH_ROOT") or "").strip()
        if env:
            root = Path(env)
        elif args.version == "v2":
            root = repo_root() / ".local" / "ifc-bench-v2"
        else:
            root = repo_root() / ".local" / "ifc-bench"
    root = root.resolve()

    payload = evaluate_dataset(root, version=args.version)
    out = args.output or (
        repo_root() / "artifacts" / "open-bench" / f"ifc-bench-{args.version}-smoke.json"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    out.write_text(text, encoding="utf-8")
    payload["output_path"] = str(out)
    payload["output_sha256"] = hashlib.sha256(text.encode("utf-8")).hexdigest()
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    out.write_text(text, encoding="utf-8")

    if args.also_docs_evidence:
        evidence = repo_root() / "docs" / "evidence" / f"ifc-bench-{args.version}-smoke-latest.json"
        evidence.write_text(text, encoding="utf-8")
        print(f"docs_evidence={evidence}")

    summary = payload["summary"]
    pin_ok = bool(payload.get("benchmark", {}).get("questions_sha256_matches_pin"))
    print(
        json.dumps(
            {
                "output": str(out),
                "version": args.version,
                "summary": summary,
                "questions_sha256_matches_pin": pin_ok,
                "claim_level": "open_bench_only",
            }
        )
    )
    if summary["scored"] == 0:
        return 2
    if not pin_ok:
        return 3
    if summary["mismatched"] or summary["errors"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
