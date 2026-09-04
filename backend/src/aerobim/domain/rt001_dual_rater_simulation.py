
"""Dual-rater *protocol rehearsal* on the in-repo fixture pack.

Two independent deterministic labeling policies walk the *same* unit list
(synthetic gold + Level-B injections + planted IfcClash + Experiment B
openers). Cohen's κ / Krippendorff's α / Gwet AC1 are the live domain
statistics. This is not two humans, not an LLM-as-rater, not
``corpus_kind=customer``, and it does not close undifferentiated RT-001.
"""

from __future__ import annotations

import csv
import io
import json
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Literal

from aerobim.domain.checkpoint import CHECKPOINT
from aerobim.domain.eval_statistics import agreement_artifact
from aerobim.domain.tz_proxy_constructs import typical_remark_taxonomy_proxy

SCHEMA_VERSION: Final = "1.0.0"
CLAIM_LEVEL: Final = "protocol_rehearsal_not_human"
MIN_UNITS: Final = 24
RATER_A: Final = "sim-rater-a"
RATER_B: Final = "sim-rater-b"
STAMP_A: Final = "2026-09-04T12:00:00+03:00"
STAMP_B: Final = "2026-09-04T12:05:00+03:00"
CSV_REL: Final = "samples/benchmarks/detection-precision/rt001-dual-rater-simulation.csv"
EVIDENCE_JSON_REL: Final = "docs/evidence/rt001-dual-rater-simulation-2026-09.json"
EVIDENCE_MD_REL: Final = "docs/evidence/rt001-dual-rater-simulation-2026-09.md"

SYNTHETIC_REL: Final = "samples/benchmarks/detection-precision/labels-synthetic.json"
INJECTION_REL: Final = "samples/benchmarks/injected-defects-level-b.json"
PLANTED_REL: Final = "docs/evidence/federated-clash-planted-2026-08.json"
SPRINT21_REL: Final = "samples/benchmarks/sprint-2-1/expected/findings.json"

Verdict = Literal["TP", "FP", "FN"]

CLAIM_BOUNDARY: Final = (
    "Two simulated independent passes on the same in-repo fixture units. "
    "Not two human raters. LLM is not a rater. Fixture author is not counted "
    "twice. corpus_kind stays synthetic. closes_rt001 stays false. "
    "PrecisionClaim.publishable stays false. Checkpoint GO "
    "(regulatory_measurement_mvp; customer_go false)."
)

POLICY_A: Final = (
    "strict planted-gold: TP if the frozen contract says the defect is real "
    "and expected; FP if excluded/control; FN if unresolved or known miss"
)
POLICY_B: Final = (
    "conservative evidence: TP only with machine-checkable evidence "
    "(GUID / IDS / canonical LOAD / inventory rule); geometric pipe-vs-wall "
    "is not system MEP; free-text narrative is out of сверка"
)


class Rt001DualRaterSimulationError(ValueError):
    """Simulation inventory missing or an honesty lock leaked."""


@dataclass(frozen=True)
class RehearsalUnit:
    finding_id: str
    case_id: str
    finding_class: str
    rule_id: str
    target_ref: str
    element_guid: str
    match_key: str
    discipline: str
    criticality: str
    modality: str
    gold_kind: str
    has_machine_evidence: bool
    pipe_vs_wall_not_mep: bool
    narrative_out_of_sverka: bool
    source: str


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise Rt001DualRaterSimulationError(f"expected JSON object in {path}")
    return data


def _synthetic_units(repo: Path) -> list[RehearsalUnit]:
    payload = _load_json(repo / SYNTHETIC_REL)
    units: list[RehearsalUnit] = []
    for case in payload.get("cases") or []:
        if not isinstance(case, dict):
            continue
        case_id = str(case.get("case_id") or "")
        discipline = "ST" if "KJ" in case_id or "KZH" in case_id else "AR"
        for index, finding in enumerate(case.get("expected_findings") or [], start=1):
            if not isinstance(finding, dict):
                continue
            status = str(finding.get("adjudication_status") or "")
            rule_id = str(finding.get("rule_id") or "")
            target = str(finding.get("target_ref") or "")
            finding_class = str(finding.get("finding_class") or "")
            finding_id = f"{case_id}-{index:02d}"
            has_guid = "GUID-" in target
            section_pair = rule_id.startswith("SECTION-PAIR")
            units.append(
                RehearsalUnit(
                    finding_id=finding_id,
                    case_id=case_id,
                    finding_class=finding_class,
                    rule_id=rule_id,
                    target_ref=target,
                    element_guid=target if has_guid else "",
                    match_key=rule_id,
                    discipline=discipline,
                    criticality="error" if finding_class == "clash" else "warning",
                    modality="ifc" if finding_class == "clash" else "cross_doc",
                    gold_kind=status,
                    has_machine_evidence=has_guid or (section_pair and "AREA" not in rule_id),
                    pipe_vs_wall_not_mep=False,
                    narrative_out_of_sverka=False,
                    source=SYNTHETIC_REL,
                )
            )
    return units


def _injection_units(repo: Path) -> list[RehearsalUnit]:
    payload = _load_json(repo / INJECTION_REL)
    units: list[RehearsalUnit] = []
    for row in payload.get("defects") or []:
        if not isinstance(row, dict):
            continue
        defect_id = str(row.get("defect_id") or "")
        status = str(row.get("expected_status") or "")
        expected = row.get("expected_finding")
        rule_id = str(expected or f"CONTROL-{defect_id}")
        severity = str(row.get("expected_severity") or "warning")
        freetext = "freetext" in defect_id
        ids_vacuous = status == "known_undetected_ids_only"
        detected = status == "detected"
        units.append(
            RehearsalUnit(
                finding_id=defect_id,
                case_id="LEVEL-B",
                finding_class="ids_requirement"
                if "ifc" in defect_id or "ids" in defect_id
                else "calculation_mismatch",
                rule_id=rule_id,
                target_ref=defect_id,
                element_guid="",
                match_key=rule_id,
                discipline="AR",
                criticality="error" if severity == "error" else "warning",
                modality="ifc" if "ifc" in defect_id else "calculation",
                gold_kind=status,
                has_machine_evidence=detected or ids_vacuous,
                pipe_vs_wall_not_mep=False,
                narrative_out_of_sverka=freetext,
                source=INJECTION_REL,
            )
        )
    return units


def _planted_units(repo: Path) -> list[RehearsalUnit]:
    payload = _load_json(repo / PLANTED_REL)
    units: list[RehearsalUnit] = []
    for row in payload.get("runs") or []:
        if not isinstance(row, dict):
            continue
        label = str(row.get("label") or "")
        if row.get("status") != "RUN":
            continue
        pipe = "pipe" in label
        path_b = str(row.get("path_b") or "")
        units.append(
            RehearsalUnit(
                finding_id=label,
                case_id="PLANTED-CLASH",
                finding_class="clash",
                rule_id="SPATIAL-HARD-CLASH",
                target_ref=path_b,
                element_guid="GUID-PLANTED-A|GUID-PLANTED-B",
                match_key=label,
                discipline="MEP" if pipe else "AR",
                criticality="error",
                modality="ifc",
                gold_kind="planted_clash",
                has_machine_evidence=True,
                pipe_vs_wall_not_mep=pipe,
                narrative_out_of_sverka=False,
                source=PLANTED_REL,
            )
        )
    return units


def _sprint21_units(repo: Path) -> list[RehearsalUnit]:
    payload = _load_json(repo / SPRINT21_REL)
    units: list[RehearsalUnit] = []
    for row in payload.get("findings") or []:
        if not isinstance(row, dict):
            continue
        finding_id = str(row.get("finding_id") or "")
        rule_id = str(row.get("rule_id") or "")
        units.append(
            RehearsalUnit(
                finding_id=finding_id,
                case_id="SPRINT-2-1",
                finding_class="ids_requirement" if "IDS" in rule_id else "calculation_mismatch",
                rule_id=rule_id,
                target_ref=str(row.get("mutation_ref") or finding_id),
                element_guid="",
                match_key=rule_id,
                discipline="AR",
                criticality="error" if row.get("severity") == "critical" else "warning",
                modality="ifc" if "IDS" in rule_id else "calculation",
                gold_kind="detected",
                has_machine_evidence=True,
                pipe_vs_wall_not_mep=False,
                narrative_out_of_sverka=False,
                source=SPRINT21_REL,
            )
        )
    return units


def _experiment_b_units() -> list[RehearsalUnit]:
    taxonomy = typical_remark_taxonomy_proxy()
    catalogs = {
        str(row.get("id")): row for row in taxonomy.get("catalogs") or [] if isinstance(row, dict)
    }
    kirov = catalogs.get("kirov-kr") or {}
    openers = kirov.get("detectable_openers") or []
    units: list[RehearsalUnit] = []
    for opener in openers:
        rule_id = str(opener)
        units.append(
            RehearsalUnit(
                finding_id=f"EXPB-{rule_id}",
                case_id="EXPERIMENT-B-KR",
                finding_class="cross-document",
                rule_id=rule_id,
                target_ref=rule_id,
                element_guid="",
                match_key=rule_id,
                discipline="ST",
                criticality="warning",
                modality="cross_doc",
                gold_kind="confirmed",
                has_machine_evidence=True,
                pipe_vs_wall_not_mep=False,
                narrative_out_of_sverka=False,
                source="tz_proxy_constructs.typical_remark_taxonomy_proxy",
            )
        )
    return units


def rehearsal_units(repo: Path) -> list[RehearsalUnit]:
    """Frozen unit list: one pack, both simulated raters see the same IDs."""

    units = [
        *_synthetic_units(repo),
        *_planted_units(repo),
        *_injection_units(repo),
        *_sprint21_units(repo),
        *_experiment_b_units(),
    ]
    ids = [unit.finding_id for unit in units]
    if len(ids) != len(set(ids)):
        raise Rt001DualRaterSimulationError("duplicate finding_id in rehearsal pack")
    if len(units) < MIN_UNITS:
        raise Rt001DualRaterSimulationError(f"need ≥{MIN_UNITS} units, got {len(units)}")
    return units


def verdict_a(unit: RehearsalUnit) -> Verdict:
    """Independent pass A — planted/gold contract, blind to B."""

    if unit.gold_kind in {"confirmed", "detected", "planted_clash"}:
        return "TP"
    if unit.gold_kind in {"excluded", "control_clean"}:
        return "FP"
    if unit.gold_kind in {"unresolved", "known_undetected", "known_undetected_ids_only"}:
        return "FN"
    raise Rt001DualRaterSimulationError(f"unknown gold_kind {unit.gold_kind!r}")


def verdict_b(unit: RehearsalUnit) -> Verdict:
    """Independent pass B — conservative evidence, blind to A."""

    if unit.narrative_out_of_sverka:
        return "FP"
    if unit.pipe_vs_wall_not_mep:
        return "FP"
    if unit.gold_kind in {"excluded", "control_clean"}:
        return "FP"
    if unit.gold_kind in {"unresolved", "known_undetected", "known_undetected_ids_only"}:
        return "FN"
    if unit.gold_kind in {"confirmed", "detected", "planted_clash"}:
        return "TP" if unit.has_machine_evidence else "FP"
    raise Rt001DualRaterSimulationError(f"unknown gold_kind {unit.gold_kind!r}")


def csv_records(units: list[RehearsalUnit]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for unit in units:
        for rater, verdict, stamp, policy in (
            (RATER_A, verdict_a(unit), STAMP_A, POLICY_A),
            (RATER_B, verdict_b(unit), STAMP_B, POLICY_B),
        ):
            rows.append(
                {
                    "finding_id": unit.finding_id,
                    "case_id": unit.case_id,
                    "finding_class": unit.finding_class,
                    "rule_id": unit.rule_id,
                    "target_ref": unit.target_ref,
                    "element_guid": unit.element_guid,
                    "match_key": unit.match_key,
                    "adjudicator_id": rater,
                    "verdict": verdict,
                    "notes": policy,
                    "timestamp": stamp,
                    "discipline": unit.discipline,
                    "criticality": unit.criticality,
                    "modality": unit.modality,
                    "source": unit.source,
                    "human": "false",
                    "llm_rater": "false",
                }
            )
    return rows


def render_adjudication_csv(records: list[dict[str, str]]) -> str:
    if not records:
        raise Rt001DualRaterSimulationError("no adjudication rows")
    handle = io.StringIO()
    writer = csv.DictWriter(handle, fieldnames=list(records[0].keys()), lineterminator="\n")
    writer.writeheader()
    writer.writerows(records)
    return handle.getvalue()


def _agreement_payload(units: list[RehearsalUnit]) -> dict[str, Any]:
    pairs = [(verdict_a(unit), verdict_b(unit)) for unit in units]
    artifact_units = [{RATER_A: left, RATER_B: right} for left, right in pairs]
    artifact = agreement_artifact(artifact_units)
    confusion = Counter(pairs)
    disagree = [unit.finding_id for unit in units if verdict_a(unit) != verdict_b(unit)]
    return {
        **artifact,
        "paired_items": len(pairs),
        "disagreement_ids": disagree,
        "disagreement_count": len(disagree),
        "confusion_matrix": {f"{a}/{b}": count for (a, b), count in sorted(confusion.items())},
        "raw_agreement": round(sum(1 for a, b in pairs if a == b) / len(pairs), 4),
    }


def assemble_rt001_dual_rater_simulation(repo: Path) -> dict[str, Any]:
    """Live protocol rehearsal snapshot. Humans stay zero."""

    units = rehearsal_units(repo)
    agreement = _agreement_payload(units)
    kappa_ok = bool(agreement.get("pass_threshold_0_60"))
    alpha_ok = bool(agreement.get("pass_alpha_0_67"))
    ac1_ok = bool(agreement.get("pass_ac1_0_60"))
    protocol_closed = kappa_ok and alpha_ok and ac1_ok and len(units) >= MIN_UNITS
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "artifact_type": "rt001_dual_rater_simulation",
        "claim_level": CLAIM_LEVEL,
        "claim_boundary": CLAIM_BOUNDARY,
        "checkpoint": CHECKPOINT,
        "closes_rt001": False,
        "precision_claim_publishable": False,
        "corpus_kind": "synthetic",
        "independent_human_raters": 0,
        "llm_counts_as_rater": False,
        "fixture_author_counted_twice": False,
        "simulated_independent_passes": 2,
        "rater_a": {"id": RATER_A, "human": False, "llm": False, "policy": POLICY_A},
        "rater_b": {"id": RATER_B, "human": False, "llm": False, "policy": POLICY_B},
        "same_pack": True,
        "n": len(units),
        "n_pilot_protocol_max": 30,
        "b_protocol_rehearsal": "CLOSED" if protocol_closed else "OPEN",
        "b_criterion_dual_rater": "OPEN",
        "c_customer_corpus": "OPEN",
        "csv_rel": CSV_REL,
        "cohens_kappa": agreement.get("cohen_kappa"),
        "krippendorff_alpha": agreement.get("krippendorff_alpha"),
        "gwet_ac1": agreement.get("gwet_ac1"),
        "pass_kappa_0_60": kappa_ok,
        "pass_alpha_0_67": alpha_ok,
        "pass_ac1_0_60": ac1_ok,
        "raw_agreement": agreement.get("raw_agreement"),
        "disagreement_count": agreement.get("disagreement_count"),
        "disagreement_ids": agreement.get("disagreement_ids"),
        "confusion_matrix": agreement.get("confusion_matrix"),
        "strata": {
            "discipline": dict(Counter(unit.discipline for unit in units)),
            "criticality": dict(Counter(unit.criticality for unit in units)),
            "modality": dict(Counter(unit.modality for unit in units)),
        },
        "instruction_ref": "docs/pilot/EXPERT_LABELING_INSTRUCTION_2026.md",
        "protocol_ref": "docs/quality/RT001_LABELING_PROTOCOL_RT026_2026_08_03.md",
    }
    require_honest_rt001_dual_rater_simulation(payload)
    return payload


def require_honest_rt001_dual_rater_simulation(payload: Mapping[str, Any]) -> None:
    errors: list[str] = []
    if payload.get("checkpoint") != CHECKPOINT:
        errors.append(f"checkpoint={payload.get('checkpoint')!r}")
    if payload.get("closes_rt001") is not False:
        errors.append("closes_rt001 must stay false")
    if payload.get("precision_claim_publishable") is not False:
        errors.append("precision_claim_publishable must stay false")
    if payload.get("corpus_kind") != "synthetic":
        errors.append("corpus_kind must stay synthetic")
    if int(payload.get("independent_human_raters") or 0) != 0:
        errors.append("must not invent independent human raters")
    if payload.get("llm_counts_as_rater") is not False:
        errors.append("LLM must not count as a rater")
    if payload.get("fixture_author_counted_twice") is not False:
        errors.append("must not count the fixture author twice")
    if int(payload.get("simulated_independent_passes") or 0) != 2:
        errors.append("need two simulated independent passes")
    if payload.get("same_pack") is not True:
        errors.append("both passes must share one pack")
    if int(payload.get("n") or 0) < MIN_UNITS:
        errors.append(f"pilot n must be ≥{MIN_UNITS}")
    if payload.get("b_criterion_dual_rater") != "OPEN":
        errors.append("human dual-rater residual must stay OPEN")
    if payload.get("b_protocol_rehearsal") != "CLOSED":
        errors.append("protocol rehearsal must close on κ/α/AC1 + n")
    kappa = float(payload.get("cohens_kappa") or 0.0)
    if kappa >= 1.0:
        errors.append("perfect κ is not an independent dual pass")
    if kappa < 0.60:
        errors.append("eng gate κ≥0.60 not met")
    if float(payload.get("krippendorff_alpha") or 0.0) < 0.67:
        errors.append("eng gate α≥0.67 not met")
    if float(payload.get("gwet_ac1") or 0.0) < 0.60:
        errors.append("eng gate AC1≥0.60 not met")
    rater_a = payload.get("rater_a")
    rater_b = payload.get("rater_b")
    if not isinstance(rater_a, dict) or rater_a.get("human") is not False:
        errors.append("sim-rater-a is not a human")
    if not isinstance(rater_b, dict) or rater_b.get("human") is not False:
        errors.append("sim-rater-b is not a human")
    if isinstance(rater_a, dict) and rater_a.get("llm") is not False:
        errors.append("sim-rater-a is not an LLM rater")
    if isinstance(rater_b, dict) and rater_b.get("llm") is not False:
        errors.append("sim-rater-b is not an LLM rater")
    if errors:
        raise Rt001DualRaterSimulationError("; ".join(errors))


def render_evidence_markdown(payload: Mapping[str, Any]) -> str:
    disagree = payload.get("disagreement_ids") or []
    if not isinstance(disagree, list):
        disagree = []
    matrix = payload.get("confusion_matrix") or {}
    matrix_rows = []
    if isinstance(matrix, dict):
        matrix_rows = [f"| `{key}` | {value} |" for key, value in matrix.items()]
    return "\n".join(
        [
            "<!-- claims-lint: allow-file reason="
            '"RT-001 dual-rater protocol rehearsal; simulated passes; '
            'humans stay 0; closes_rt001 false; customer_go false" -->',
            "---",
            'title: "RT-001b protocol rehearsal — two simulated independent passes"',
            'date: "2026-09-04"',
            f"checkpoint: {payload.get('checkpoint', CHECKPOINT)}",
            "closes_rt001: false",
            "independent_human_raters: 0",
            "llm_counts_as_rater: false",
            f"claim_level: {payload.get('claim_level')}",
            f'claim_boundary: "{CLAIM_BOUNDARY}"',
            "---",
            "",
            "# RT-001: симуляция двух независимых проходов",
            "",
            "Это **репетиция протокола** на учебном комплекте, не двое людей и не "
            "разметка LLM. Оба прохода видят те же `finding_id`. κ/α/AC1 считает "
            "`aerobim.domain.eval_statistics.agreement_artifact`.",
            "",
            f"- Checkpoint: **{payload.get('checkpoint')}**",
            f"- closes_rt001: **{json.dumps(bool(payload.get('closes_rt001')))}**",
            f"- independent_human_raters: **{payload.get('independent_human_raters')}**",
            f"- llm_counts_as_rater: **{json.dumps(bool(payload.get('llm_counts_as_rater')))}**",
            f"- `b_protocol_rehearsal`: **{payload.get('b_protocol_rehearsal')}**",
            f"- `b_criterion_dual_rater`: **{payload.get('b_criterion_dual_rater')}**",
            f"- n: **{payload.get('n')}** (пилот протокола ≤30)",
            f"- Cohen κ: **{payload.get('cohens_kappa')}** (порог 0.60)",
            f"- Krippendorff α: **{payload.get('krippendorff_alpha')}** (порог 0.67)",
            f"- Gwet AC1: **{payload.get('gwet_ac1')}** (порог 0.60)",
            f"- raw agreement: **{payload.get('raw_agreement')}**",
            f"- расхождений: **{payload.get('disagreement_count')}**",
            f"- CSV: `{payload.get('csv_rel')}`",
            "",
            f"- Проход A (`{RATER_A}`): {POLICY_A}",
            f"- Проход B (`{RATER_B}`): {POLICY_B}",
            "",
            "Расхождения (ожидаемы; иначе κ=1.0 не независимость):",
            "",
            ", ".join(f"`{item}`" for item in disagree) or "—",
            "",
            "| A/B | n |",
            "|---|---|",
            *matrix_rows,
            "",
            "Инструкция людей: `docs/pilot/EXPERT_LABELING_INSTRUCTION_2026.md`. "
            "Когда появятся двое живых разметчиков на комплекте заказчика, этот CSV "
            "не подменяется: заводится новый журнал с человеческими `adjudicator_id`.",
            "",
        ]
    )
