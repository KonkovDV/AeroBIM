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

from aerobim.domain.copyleft_lane import GPLV3_IFC_BENCH_PROJECTS

CLAIM_BOUNDARY = (
    "IFC-Bench open_bench_only: deterministic countable subset via "
    "IfcOpenShell. NOT product accuracy. Never claim >90%. Does not close RT-001."
)
_GPL_PROJECTS = frozenset(GPLV3_IFC_BENCH_PROJECTS)
_INCOMPLETE_GT_RE = re.compile(
    r"cannot|not available|information not|no (?:explicit )?(?:heating|hvac) ",
    re.IGNORECASE,
)

# HF card listed this for an earlier snapshot; measured 2026-08-04 after dedup = e47c…
_PINNED_V2_SHA_MEASURED = "e47ccd097306f5bca49b9c8ac0b4cd72f296df9f7ff7a02625b3f06c1691da9b"
_PINNED_V1_SHA_HF = "f67a48770d74b6e0ff0868c923c3e1d976110350b2c439564d7ceccc16a46f35"

_NUMBER_RE = re.compile(
    r"(?P<n>\d+(?:\.\d+)?)\s*(?:sqm|m2|m²|rooms?|doors?|windows?|bedrooms?|"
    r"fixtures?|steps?|radiators?)?",
    re.IGNORECASE,
)
_WORD_NUMBERS = {
    "one": 1.0,
    "two": 2.0,
    "three": 3.0,
    "four": 4.0,
    "five": 5.0,
    "six": 6.0,
    "seven": 7.0,
    "eight": 8.0,
    "nine": 9.0,
    "ten": 10.0,
    "eleven": 11.0,
    "twelve": 12.0,
}


_MAX_IFC_HASH_BYTES = 80 * 1024 * 1024


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
    question_id: str = ""
    skip_reason: str | None = None


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _repo_relative_or_redact(path_str: str) -> str:
    try:
        resolved = Path(path_str).resolve()
        return resolved.relative_to(repo_root().resolve()).as_posix()
    except (OSError, ValueError):
        return "<redacted>"


def _sanitize_docs_evidence(payload: dict[str, Any]) -> dict[str, Any]:
    docs = json.loads(json.dumps(payload, ensure_ascii=False))
    if not isinstance(docs, dict):
        raise TypeError("sanitized report must be a JSON object")
    bench = docs.get("benchmark")
    if isinstance(bench, dict) and bench.get("dataset_root"):
        bench["dataset_root"] = _repo_relative_or_redact(str(bench["dataset_root"]))
    docs.pop("output_path", None)
    return docs


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _ifc_inventory_entry(path: Path, dataset_root: Path) -> dict[str, Any]:
    size = path.stat().st_size
    rel = str(path.relative_to(dataset_root)).replace("\\", "/")
    if size > _MAX_IFC_HASH_BYTES:
        return {
            "path": rel,
            "bytes": size,
            "sha256": None,
            "sha256_skipped": "oversize",
        }
    return {"path": rel, "bytes": size, "sha256": _sha256_file(path)}


def _eval_split_coverage(dataset_root: Path, scored: list[ProbeResult]) -> dict[str, Any]:
    note = (
        "Published test split is 514 rows. This block only says how many of the "
        "deterministic scored probes fall in that split. It is not a 514 false-pass rate."
    )
    path = dataset_root / "questions" / "eval-split-hellin2026.csv"
    if not path.is_file():
        return {"present": False, "note": note}
    with path.open(encoding="utf-8", newline="") as fh:
        mapping = {
            str(row.get("id") or "").strip(): str(row.get("split") or "").strip()
            for row in csv.DictReader(fh)
        }
    in_test = 0
    in_train = 0
    unlisted = 0
    for row in scored:
        split = mapping.get(row.question_id)
        if split == "test":
            in_test += 1
        elif split == "train":
            in_train += 1
        else:
            unlisted += 1
    return {
        "present": True,
        "path": "questions/eval-split-hellin2026.csv",
        "published_test_rows": sum(1 for split in mapping.values() if split == "test"),
        "published_train_rows": sum(1 for split in mapping.values() if split == "train"),
        "scored_in_test": in_test,
        "scored_in_train": in_train,
        "scored_unlisted": unlisted,
        "note": note,
    }


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
        r"total heating components:\s*(\d+)",
        r"total air terminals:\s*(\d+)",
        r"total railings:\s*(\d+)",
        r"heating systems:\s*(\d+)\s+systems",
        r"(\d+)\s+columns\b",
        r"(?:there are|are)\s+(\d+(?:\.\d+)?)",
    ):
        m = re.search(pattern, text, re.I)
        if m:
            return float(m.group(1))
    word = re.search(
        r"(?:there are|are|includes)\s+(one|two|three|four|five|six|seven|eight|nine|ten|"
        r"eleven|twelve)\b",
        text,
        re.I,
    )
    if word:
        return _WORD_NUMBERS[word.group(1).lower()]
    counted = re.search(
        r"\b(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+"
        r"(?:thermostats?|boilers?|bathrooms?|rooms?)\b",
        text,
        re.I,
    )
    if counted:
        return _WORD_NUMBERS[counted.group(1).lower()]
    unit = re.search(
        r"(\d+(?:\.\d+)?)\s*(?:mm|cm|m2|m²|sqm|m\b)",
        text,
        re.I,
    )
    if unit:
        return float(unit.group(1))
    m = _NUMBER_RE.search(text)
    return float(m.group("n")) if m else None


def _numbers_close(a: float | int, b: float | int, *, tol: float = 0.01) -> bool:
    return abs(float(a) - float(b)) <= tol


def _open_ifc(path: Path) -> Any:
    import ifcopenshell

    return ifcopenshell.open(str(path))


def _entity_count(model: Any, type_name: str) -> int:
    """Count entities; missing schema types are 0, not a smoke abort."""
    try:
        return len(model.by_type(type_name))
    except Exception:
        return 0


def _gt_incomplete(answer: str) -> bool:
    return bool(_INCOMPLETE_GT_RE.search(answer or ""))


def _classify_skip(*, project: str, answer: str, expected: float | None, mapped: bool) -> str:
    if project in _GPL_PROJECTS:
        return "gpl_project_excluded"
    if _gt_incomplete(answer):
        return "incomplete_info"
    if expected is None:
        return "non_numeric_gt"
    if not mapped:
        return "unmapped_nl"
    return "non_numeric_gt"


def _skip_breakdown(results: list[ProbeResult]) -> dict[str, Any]:
    counts = {
        "unmapped_nl": 0,
        "non_numeric_gt": 0,
        "incomplete_info": 0,
        "gpl_project_excluded": 0,
    }
    first_number_on_unmapped = 0
    how_many_unmapped_non_gpl = 0
    for row in results:
        if row.status != "skipped":
            continue
        reason = row.skip_reason or "unmapped_nl"
        if reason in counts:
            counts[reason] += 1
        else:
            counts["unmapped_nl"] += 1
        if reason == "unmapped_nl" and row.expected is not None:
            first_number_on_unmapped += 1
        if (
            reason == "unmapped_nl"
            and "how many" in (row.question or "").lower()
            and row.project not in _GPL_PROJECTS
        ):
            how_many_unmapped_non_gpl += 1
    return {
        **counts,
        "first_number_on_unmapped": first_number_on_unmapped,
        "how_many_unmapped_non_gpl": how_many_unmapped_non_gpl,
        "note": (
            "A first-number parse on an unmapped row is not a safe countable probe. "
            "Do not treat first_number_on_unmapped as extra product accuracy. "
            "GPLv3 projects are excluded from the MIT smoke, not scored as errors."
        ),
    }


def _is_external_door(door: Any) -> bool | None:
    vals = _merged_psets(door)
    if "IsExternal" in vals:
        return bool(vals["IsExternal"])
    return None


def _is_load_bearing(element: Any) -> bool | None:
    vals = _merged_psets(element)
    if "LoadBearing" in vals:
        return bool(vals["LoadBearing"])
    return None


def _merged_psets(obj: Any) -> dict[str, Any]:
    import ifcopenshell.util.element as el

    merged: dict[str, Any] = {}
    for vals in el.get_psets(obj).values():
        if isinstance(vals, dict):
            merged.update(vals)
    return merged


def _storey_elevation(model: Any, *names: str) -> float | None:
    wanted = {name.casefold() for name in names}
    for storey in model.by_type("IfcBuildingStorey"):
        if (storey.Name or "").strip().casefold() in wanted:
            elev = getattr(storey, "Elevation", None)
            if elev is None:
                return None
            return float(elev)
    return None


def _floor_to_floor_m(model: Any, upper: tuple[str, ...], lower: tuple[str, ...]) -> float:
    top = _storey_elevation(model, *upper)
    bottom = _storey_elevation(model, *lower)
    if top is None or bottom is None:
        return 0.0
    return round(top - bottom, 4)


def _guid_attr(model: Any, guid: str, attr: str) -> float:
    entity = model.by_guid(guid)
    value = getattr(entity, attr, None)
    return float(value) if value is not None else 0.0


def _insulated_panel_mm(model: Any) -> int:
    for layer_set in model.by_type("IfcMaterialLayerSet"):
        for layer in getattr(layer_set, "MaterialLayers", None) or []:
            material = getattr(layer, "Material", None)
            name = (getattr(material, "Name", None) or "").lower()
            if "insulated panel" not in name:
                continue
            thickness = getattr(layer, "LayerThickness", None)
            if isinstance(thickness, (int, float)):
                return int(round(float(thickness) * 1000.0))
    return 0


def _named_product_count(model: Any, type_name: str, needle: str) -> int:
    token = needle.lower()
    return sum(
        1
        for item in model.by_type(type_name)
        if token in ((item.Name or "") + (item.ObjectType or "")).lower()
    )


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
            "how many bathroom are there": (
                "duplex_arc_bathroom_count",
                lambda m: sum(
                    1 for s in m.by_type("IfcSpace") if "bathroom" in (s.LongName or "").lower()
                ),
            ),
            "width of the door 1hosvn6df7f8_7gcbwlrgq": (
                "duplex_arc_door_guid_width_m",
                lambda m: round(_guid_attr(m, "1hOSvn6df7F8_7GcBWlRGQ", "OverallWidth"), 4),
            ),
            "floor-to-floor height between the ground floor and first floor": (
                "duplex_arc_floor_to_floor_m",
                lambda m: _floor_to_floor_m(m, ("Level 2",), ("Level 1",)),
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
            "which rooms have thermostats installed": (
                "duplex_mep_thermostat_count",
                lambda m: _named_product_count(m, "IfcDistributionControlElement", "thermostat"),
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
            "how many windows are there in this building": (
                "dental_arc_window_count",
                lambda m: len(m.by_type("IfcWindow")),
            ),
            "how many doors are there in this building": (
                "dental_arc_door_count",
                lambda m: len(m.by_type("IfcDoor")),
            ),
            "how many toilet rooms are there on the second floor": (
                "dental_arc_floor2_toilet_count",
                lambda m: sum(
                    1
                    for s in m.by_type("IfcSpace")
                    if (s.Name or "").startswith("2") and "toilet" in (s.LongName or "").lower()
                ),
            ),
            "floor to floor height between the first and the second floor": (
                "dental_arc_floor_to_floor_m",
                lambda m: _floor_to_floor_m(m, ("Second Floor",), ("First Floor",)),
            ),
            "thickness of the insulation of the external walls": (
                "dental_arc_insulated_panel_mm",
                _insulated_panel_mm,
            ),
            "window with guid 0otfao0qpdahynjj6dmgh8": (
                "dental_arc_window_guid_height_m",
                lambda m: round(_guid_attr(m, "0otfaO0qPDAhynjJ6DmgH8", "OverallHeight"), 4),
            ),
        }
    if project == "digital_hub" and ifc_model == "arc":
        return {
            "how many walls are load-bearing compared with non-load-bearing": (
                "digital_hub_arc_load_bearing_wall_count",
                lambda m: sum(1 for wall in m.by_type("IfcWall") if _is_load_bearing(wall) is True),
            ),
        }
    if project == "digital_hub" and ifc_model == "heating":
        return {
            "which component types comprise the heating system": (
                "digital_hub_heating_distribution_element_count",
                lambda m: _entity_count(m, "IfcDistributionElement"),
            ),
            "what heating systems are present": (
                "digital_hub_heating_system_count",
                lambda m: _entity_count(m, "IfcSystem"),
            ),
        }
    if project == "digital_hub" and ifc_model == "ventilation":
        return {
            "how many air terminals serve each building storey": (
                "digital_hub_vent_air_terminal_count",
                lambda m: len(m.by_type("IfcAirTerminal")),
            ),
        }
    if project == "sixty5" and ifc_model == "str":
        return {
            "how many piles are used in this building": (
                "sixty5_str_pile_count",
                lambda m: len(m.by_type("IfcPile")),
            ),
        }
    if project == "wbdg_office" and ifc_model == "arc":
        return {
            "total number of railings": (
                "wbdg_arc_railing_count",
                lambda m: _entity_count(m, "IfcRailing"),
            ),
        }
    if project == "wbdg_office" and ifc_model == "mep":
        return {
            "how many mep components exist per type": (
                "wbdg_mep_flow_terminal_count",
                lambda m: len(m.by_type("IfcFlowTerminal")),
            ),
            "how many electrical receptacles are installed": (
                "wbdg_mep_receptacle_count",
                lambda m: _named_product_count(m, "IfcFlowTerminal", "receptacle"),
            ),
            "how many water heaters are in this building": (
                "wbdg_mep_water_heater_count",
                lambda m: _named_product_count(m, "IfcFlowStorageDevice", "water heater"),
            ),
        }
    if project == "wbdg_office" and ifc_model == "str":
        return {
            "which types of columns are present": (
                "wbdg_str_column_count",
                lambda m: len(m.by_type("IfcColumn")),
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
        question_id = str(row.get("id") or "").strip()
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
                    question_id=question_id,
                )
            )
            continue
        expected_preview = _parse_expected_number(answer)
        if project in _GPL_PROJECTS:
            results.append(
                ProbeResult(
                    question=question,
                    project=project,
                    ifc_model=ifc_model,
                    probe_id="gpl_excluded",
                    predicted=None,
                    expected=expected_preview,
                    status="skipped",
                    detail="GPLv3 IFC-Bench project excluded from MIT smoke",
                    question_id=question_id,
                    skip_reason="gpl_project_excluded",
                )
            )
            continue
        q_lower = question.lower()
        probes = _probes_for_model(project, ifc_model, version=version)
        matched_key = max((k for k in probes if k in q_lower), key=len, default=None)
        if matched_key is None:
            results.append(
                ProbeResult(
                    question=question,
                    project=project,
                    ifc_model=ifc_model,
                    probe_id="unmapped",
                    predicted=None,
                    expected=expected_preview,
                    status="skipped",
                    detail="no deterministic probe for this NL question",
                    question_id=question_id,
                    skip_reason=_classify_skip(
                        project=project,
                        answer=answer,
                        expected=expected_preview,
                        mapped=False,
                    ),
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
                    question_id=question_id,
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
                    question_id=question_id,
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
                skip_reason = _classify_skip(
                    project=project, answer=answer, expected=expected, mapped=True
                )
            elif isinstance(predicted, (int, float)) and _numbers_close(predicted, expected):
                status = "matched"
                detail = None
                skip_reason = None
            else:
                status = "mismatched"
                detail = f"predicted={predicted!r} expected={expected!r}"
                skip_reason = None
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
                    question_id=question_id,
                    skip_reason=skip_reason,
                )
            )
        except Exception as exc:
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
                    question_id=question_id,
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
        "schema_version": "1.3.0",
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
            "ifc_hash_max_bytes": _MAX_IFC_HASH_BYTES,
            "ifc_files": [_ifc_inventory_entry(path, dataset_root) for path in ifc_files],
        },
        "eval_split": _eval_split_coverage(dataset_root, scored),
        "summary": {
            "total_questions": len(results),
            "scored": len(scored),
            "matched": len(matched),
            "mismatched": len(scored) - len(matched),
            "skipped_unmapped_or_uncomparable": len(skipped),
            "errors": len(errors),
            "skip_breakdown": _skip_breakdown(results),
            "exact_match_rate_on_scored": (
                round(len(matched) / len(scored), 4) if scored else None
            ),
            "denominator_note": (
                f"scored={len(scored)} of total_questions={len(results)}; "
                "unmapped NL, incomplete GT, and GPLv3 projects skipped; missing IFC → error"
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
        docs_payload = _sanitize_docs_evidence(payload)
        docs_text = json.dumps(docs_payload, ensure_ascii=False, indent=2) + "\n"
        evidence = repo_root() / "docs" / "evidence" / f"ifc-bench-{args.version}-smoke-latest.json"
        evidence.write_text(docs_text, encoding="utf-8")
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
