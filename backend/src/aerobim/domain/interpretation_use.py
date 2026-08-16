"""Kane IUA ledger: which inferences current scores may support.

Validity is a property of an inference from a score to a use (Messick 1995;
Kane 2013), not of the tool. This module is the executable SSOT for that
boundary across Samolet TZ, TechLab/MIK checkpoints, tracker tasks, and
industry standards.

No row licenses customer precision, Checkpoint GO, native DWG, MEP delivered,
or CDE-ready BCF. RT-001 / RT-002 / RT-003 stay OPEN.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

LEDGER_ID = "aerobim_interpretation_use_ledger"
SCHEMA_VERSION = "1.0.0"
AUDITED_HEAD = "f9389bf"
CHECKPOINT = "NO_GO"
CLAIM_BOUNDARY = (
    "Kane IUA over existing AeroBIM scores. Licensed uses stop at fixture "
    "demo, engine regression, open-bench countable subsets, gold-IDS "
    "processability, and protocol planning. Not customer precision, not TZ "
    ">90%, not customer SLA, not Checkpoint GO."
)

LICENSED_USES = frozenset(
    {
        "fixture_demo",
        "engine_regression",
        "open_bench",
        "document_processability",
        "protocol_planning",
        "operational_hygiene",
        "not_licensed",
    }
)
FORBIDDEN_LICENSED_USES = frozenset(
    {
        "customer_precision",
        "checkpoint_go",
        "native_dwg",
        "mep_delivered",
        "cde_ready",
    }
)


@dataclass(frozen=True)
class InferenceRow:
    """One licensed/blocked inference. ``licensed_use`` must stay in LICENSED_USES."""

    row_id: str
    source: str
    requirement: str
    licensed_inference: str
    blocked_inference: str
    evidence: str
    kt3_condition: str
    licensed_use: str
    closes_rt001: bool = False
    closes_rt002: bool = False
    closes_rt003: bool = False

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["checkpoint"] = CHECKPOINT
        return payload


def _row(
    row_id: str,
    source: str,
    requirement: str,
    licensed_inference: str,
    blocked_inference: str,
    evidence: str,
    kt3_condition: str,
    licensed_use: str,
) -> InferenceRow:
    if licensed_use not in LICENSED_USES:
        raise ValueError(f"unknown licensed_use: {licensed_use}")
    if licensed_use in FORBIDDEN_LICENSED_USES:
        raise ValueError(f"forbidden licensed_use: {licensed_use}")
    return InferenceRow(
        row_id=row_id,
        source=source,
        requirement=requirement,
        licensed_inference=licensed_inference,
        blocked_inference=blocked_inference,
        evidence=evidence,
        kt3_condition=kt3_condition,
        licensed_use=licensed_use,
    )


LEDGER: tuple[InferenceRow, ...] = (
    _row(
        "SAM-01",
        "samolet",
        "ТР-1: ассистент эксперта, не замена ГИП",
        "HITL + Claims Lock + ADR-001: модель не ставит summary.passed",
        "Система заменяет экспертизу / лицензированного специалиста",
        "docs/architecture/ADR-001-verdict-ownership-2026.md",
        "Без изменения роли: эксперт остаётся уполномочивающим (ISO 19650-2 5.7)",
        "fixture_demo",
    ),
    _row(
        "SAM-02",
        "samolet",
        "IFC + IDS / атрибуты BIM",
        "IfcOpenShell + IfcTester на fixture и open packs; IDS 1.0 checking",
        "Профиль приёмки Самолёта / CIM-compliance / RT-002 CLOSED",
        "python -m aerobim.tools.run_demo_ifc_acceptance_gate",
        "Подписанный EIR/IDS Самолёта + customer_pack_hash",
        "engine_regression",
    ),
    _row(
        "SAM-03",
        "samolet",
        "2D PDF + подсветка замечания",
        "pypdfium2 overlay на fixture; finding_id / evidence_refs",
        "CV-счёт дверей/окон; AECV-Bench как product accuracy",
        "python -m aerobim.tools.run_demo_vertical_slice",
        "Размеченный 2D-корпус заказчика; VLM остаётся advisory",
        "fixture_demo",
    ),
    _row(
        "SAM-04",
        "samolet",
        "Нативный DWG в ТЗ",
        "Fail-closed intake: dwg_native=NOT_IMPLEMENTED / FAILED",
        "DWG-ready / тихий пропуск DWG",
        "docs/architecture/ADR-003-dwg-oda-trial-kt3-2026.md",
        "ODA trial = измерение KT#3, не покупка и не product claim",
        "not_licensed",
    ),
    _row(
        "SAM-05",
        "samolet",
        "Коллизии / MEP / «точность >90%»",
        "Generic IfcClash на fixture; tiny-skip fail-closed; protocol TP/(TP+FP)≥0.60",
        "Customer clash precision; mep_system_clash=OK; TZ >90%",
        "docs/pilot/QUALITY_MEASUREMENT_PROTOCOL_2026_08.md",
        "Корпус + ≥2 разметчика + κ/α; federated MEP + signed clearance (RT-003)",
        "protocol_planning",
    ),
    _row(
        "SAM-06",
        "samolet",
        "SLA «до 30 минут»",
        "measure_package_sla на согласованном fixture; StageBudget sum=30 min",
        "Customer SLA / любой комплект Самолёта",
        "python -m aerobim.tools.measure_package_sla",
        "Замер на customer pack с corpus_kind=customer",
        "protocol_planning",
    ),
    _row(
        "SAM-07",
        "samolet",
        "BCF замечания в СОД",
        "BCF 2.1 ZIP export (структурный)",
        "CDE import VERIFIED / T2 roundtrip",
        "docs/pilot-claim-boundary-2026.md",
        "Log + screenshot + hashes именованного CDE Самолёта",
        "fixture_demo",
    ),
    _row(
        "TRK-01",
        "tracker",
        "Задача 1: доработать продукт к КТ#2 (20.08)",
        "IFC Acceptance Gate + HD fail-closed; live CLI; Checkpoint NO_GO",
        "Checkpoint GO / market GO = customer GO",
        "docs/partners/_2026_08_16.md",
        "КТ#3 — итоговое решение; победителей определяют заказчики",
        "fixture_demo",
    ),
    _row(
        "TRK-02",
        "tracker",
        "Задача 2: таблица IFC2X3 / IFC4 / IFC4X3",
        "Fixture kernel n=20: findings 5/4/6, passed=false, clash=skipped",
        "Product accuracy / customer SLA по релизам IFC",
        "docs/evidence/ifc-release-matrix-2026-08.md",
        "Повтор на customer packs, не на wall-fixture",
        "engine_regression",
    ),
    _row(
        "TRK-03",
        "tracker",
        "Задача 3: поиск и прогон открытых датасетов",
        "IFC-Bench 27/1026 countable; PNST CLI skip-honest; Ishigaki XML processability",
        "Open bench = RT-001; свежий 18/22; Harbor agent run; DrawingVQA в MIT tree",
        "docs/evidence/DATASET_HUNT_LOG_2026_08.md",
        "Корпус ПД+экспертиза по-прежнему отсутствует",
        "open_bench",
    ),
    _row(
        "TRK-04",
        "tracker",
        "Задача 4:  / ИТ-ментор Михаил",
        "Вопросы и демо-ссылка в репозитории",
        "Выдуманные минуты консультаций",
        "docs/demo/CONSULTATIONS_2026_08_14.md",
        "Минуты только после заметок владельца",
        "operational_hygiene",
    ),
    _row(
        "TRK-05",
        "tracker",
        "Задача 5: KPI = назначенные демо (3–5)",
        "Живой счёт только .local/commercial-ops/",
        "Назначенные демо как git-факт",
        "docs/gtm/COMMERCIAL_AND_OPEN_CORE_2026_08_14.md",
        "Owner file; git не изобретает воронку",
        "operational_hygiene",
    ),
    _row(
        "TRK-06",
        "tracker",
        "Задача 6: монетизация при открытом коде",
        "Варианты A/B к обсуждению; LICENSE MIT; ADR-002 accepted",
        "Трекер согласовал Tangl/10D/SKU",
        "docs/architecture/ADR-002-open-core-commercial-boundary-2026.md",
        "Решение коммерции — вне кода",
        "operational_hygiene",
    ),
    _row(
        "TL-01",
        "techlab",
        "КТ#2 (до 20.08): этап МИК «доработка»",
        "Предварительная версия в ЛК; GitHub прототип; видео — человек",
        "Валидация эффективности начата; внедрение начато",
        "docs/pilot/KT2_UPLOAD_PACK_2026_08_14.md",
        "КТ#3 03–21.09 — итоговое решение",
        "fixture_demo",
    ),
    _row(
        "TL-02",
        "techlab",
        "Критерии пилота 2 млн ₽ (interim ≥0.60, SLA, BCF в СОД)",
        "Протокол измерения согласован как методика",
        "Фактическое достижение критериев на комплекте Самолёта",
        "docs/partners/PROTOCOL_QUALITY_ACCEPTANCE_TASK07_2026_08.md",
        "Замеры только после intake-gates",
        "protocol_planning",
    ),
    _row(
        "MIK-01",
        "mik",
        "Соглашение / акт / финотчётность Фонда (M2, M7, M8)",
        "Контур документирован; формы не сочиняем",
        "Самодельные шаблоны Фонда; акт с fixture-цифрами",
        "docs/partners/MIK_PILOT_COMPLIANCE_2026.md",
        "VERIFY_WITH_OPERATOR до получения форм",
        "not_licensed",
    ),
    _row(
        "MIK-02",
        "mik",
        "Четырёхэтапная модель: доработка → валидация → внедрение",
        "Стадия = доработка (КТ#2)",
        "Валидация эффективности / внедрение как текущий факт",
        "docs/docs.md",
        "Следующие этапы — после решения заказчиков на КТ#3",
        "operational_hygiene",
    ),
    _row(
        "IND-01",
        "industry",
        "buildingSMART IDS 1.0 (final standard, 1 June 2024)",
        "IDS checking (IfcTester) + IDS audit (XmlIdsDocumentAuditor / XSD 1.0)",
        "IDS audit = checking = Samolet EIR; IDS 1.1 как approved standard",
        "samples/ids-xsd/ids.xsd",
        "Customer IDS pack remains RT-002",
        "engine_regression",
    ),
    _row(
        "IND-02",
        "industry",
        "ISO 19650-2:2018 cl. 5.6–5.7 (review / authorize)",
        "summary.passed = Shared-gate technical status (ADR-001)",
        "Automated check replaces appointing-party authorization",
        "docs/architecture/ADR-001-verdict-ownership-2026.md",
        "Организационный акт 5.7 остаётся за экспертом",
        "fixture_demo",
    ),
    _row(
        "IND-03",
        "industry",
        "Solihin & Eastman 2015 rule classes",
        "Class 1–3 inventory of in-repo rules; class 4 not claimed",
        "SP 63 template = proof of solution",
        "docs/evidence/solihin-rule-classes-2026-08.md",
        "Class 4 только с расчётным solver, которого нет",
        "engine_regression",
    ),
    _row(
        "IND-04",
        "industry",
        "ПНСТ 909-2024 (Renga publisher pack)",
        "Aggregated 18/22 IDS runtime_clean snapshot 05.08 after ToS GO",
        "Свежий 18/22; customer precision; эталон Самолёта",
        "docs/evidence/PNST909_22_SCENARIO_COVERAGE_AXIS_2026_08.md",
        "Полный extract + сценарии 3/18/21/22, если издатель даст IDS",
        "open_bench",
    ),
    _row(
        "IND-05",
        "industry",
        "IFC-Bench v2 / Ishigaki-IDS-Bench (open science)",
        "Countable 27/1026; gold XML processability 166/166; observation unit stated",
        "Paper generation F1; 514 false-pass; product accuracy",
        "docs/evidence/ifc-bench-v2-smoke-latest.json",
        "Не заменяет L3 customer corpus (Mushkani et al. project-level unit)",
        "open_bench",
    ),
    _row(
        "IND-06",
        "industry",
        "AEC-Bench (Mankodiya et al. 2026, arXiv:2603.29199)",
        "Inventory 196 tasks / 9 families; Harbor agent NOT_RUN; authors: coding agents fail visual grounding",
        "AEC-Bench run as product drawing literacy / RT-001 CLOSED",
        "docs/quality/ACADEMIC_LITERATURE_TRIAGE_2026_08.md",
        "Harbor only as labeled open-bench, never as Samolet PD",
        "open_bench",
    ),
    _row(
        "IND-07",
        "industry",
        "LLM-as-judge 2026 (arXiv:2606.19544; 2509.20293; 2604.15224)",
        "VLM remains advisory candidate; TP/FP require dual human raters and κ",
        "Model confirms findings / judges precision / stakes-framed verdict",
        "docs/quality/ACADEMIC_LITERATURE_TRIAGE_2026_08.md",
        "PrecisionClaim.publishable remains the only accuracy gate",
        "protocol_planning",
    ),
    _row(
        "IND-08",
        "industry",
        "Clash management 2026 (Buildings 16(13):2623) + Mehrbod/Hu/Lin",
        "Geometric overlap on fixture; mep_system_clash=NOT_VERIFIED",
        "MEP delivered; AABB inventory as coordination-complete",
        "docs/roadmap/MEP_SYSTEM_CLASH_GAP_2026_07.md",
        "Signed clearance + federated customer IFC (RT-003)",
        "protocol_planning",
    ),
    _row(
        "IND-09",
        "industry",
        "ISO 19650-6:2025 health and safety information",
        "Not implemented; Shared-gate is 5.6-like control only (ADR-001)",
        "ISO 19650 compliant / Part 6 delivered / 5.7 automated",
        "docs/architecture/ADR-001-verdict-ownership-2026.md",
        "Do not claim Part 6; 5.7 stays human",
        "not_licensed",
    ),
    _row(
        "IND-10",
        "industry",
        "buildingSMART IDS 1.1 (feedback 2026, not final)",
        "IDS 1.0 remains the approved standard (1 June 2024)",
        "IDS 1.1 as current standard / certified profile",
        "samples/ids-xsd/ids.xsd",
        "Stay on IDS 1.0 checking + audit split until 1.1 is final",
        "engine_regression",
    ),
)


def validate_ledger(rows: tuple[InferenceRow, ...] = LEDGER) -> None:
    """Fail closed if a row licenses a forbidden use or claims RT closed."""

    seen: set[str] = set()
    for row in rows:
        if row.row_id in seen:
            raise ValueError(f"duplicate row_id: {row.row_id}")
        seen.add(row.row_id)
        if row.licensed_use not in LICENSED_USES:
            raise ValueError(f"{row.row_id}: bad licensed_use")
        if row.licensed_use in FORBIDDEN_LICENSED_USES:
            raise ValueError(f"{row.row_id}: forbidden licensed_use")
        if row.closes_rt001 or row.closes_rt002 or row.closes_rt003:
            raise ValueError(f"{row.row_id}: must not close RT-001/002/003")


def ledger_payload(*, generated_at: str) -> dict[str, Any]:
    validate_ledger()
    return {
        "artifact_type": LEDGER_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "audited_head": AUDITED_HEAD,
        "checkpoint": CHECKPOINT,
        "claim_boundary": CLAIM_BOUNDARY,
        "framework": [
            "Messick 1995 (construct validity aspects)",
            "Kane 2013 (Interpretation/Use Argument)",
            "Wilson 1927 / Brown–Cai–DasGupta 2001 (interval, not a score use)",
            "ISO 19650-2:2018 cl. 5.6–5.7",
            "buildingSMART IDS 1.0 (2024-06-01)",
            "Solihin & Eastman 2015",
            "Hellin et al. 2026 ifc-bench v2 (arXiv:2605.01698) — QA ≠ package acceptance",
            "Mankodiya et al. 2026 AEC-Bench (arXiv:2603.29199) — Harbor not a customer run",
            "LLM-as-judge 2026 (arXiv:2606.19544) — agreement ≠ Cohen κ",
            "ISO 19650-6:2025 — H&S sharing, not 5.7 authorization",
        ],
        "closes_rt001": False,
        "closes_rt002": False,
        "closes_rt003": False,
        "row_count": len(LEDGER),
        "rows": [row.as_dict() for row in LEDGER],
        "note": (
            "Executable companion of docs/quality/INTERPRETATION_USE_LEDGER_2026_08.md. "
            "PrecisionClaim.publishable remains the only product-accuracy gate."
        ),
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        '<!-- claims-lint: allow-file reason="Kane IUA ledger; TZ 90%/SLA as blocked inferences; NO_GO" -->',
        "---",
        'title: "Interpretation/Use ledger — Самолёт × трекер × Техлаб/МИК × отрасль"',
        f'date: "{str(payload.get("generated_at") or "")[:10]}"',
        "status: active",
        f'version: "{payload.get("schema_version")}"',
        "closes_rt001: false",
        "closes_rt002: false",
        "closes_rt003: false",
        "claim_boundary: >-",
        f"  {CLAIM_BOUNDARY}",
        "---",
        "",
        "# Interpretation/Use ledger (КТ#2 → КТ#3)",
        "",
        "Валидность — свойство **вывода из оценки**, не свойства программы "
        "(Messick 1995; Kane 2013). Этот файл — SSOT: что текущие цифры AeroBIM "
        "имеют право значить для Самолёта, , Техлаба, МИК и "
        "отраслевых стандартов, и чего они значить не имеют.",
        "",
        f"- Checkpoint **{CHECKPOINT}**",
        f"- audited_head `{payload.get('audited_head')}`",
        f"- closes_rt001/002/003: **false**",
        f"- CLI: `python -m aerobim.tools.export_interpretation_use_ledger --write-docs-evidence`",
        "",
        "Продуктовая точность по-прежнему только через `PrecisionClaim.publishable` "
        "(corpus_kind=customer, ≥2 разметчика, κ/α). Этот ledger её не выдаёт.",
        "",
        "| ID | Источник | Требование | Лицензированный вывод | Запрещённый вывод | licensed_use |",
        "|---|---|---|---|---|---|",
    ]
    for row in payload.get("rows") or []:
        lines.append(
            "| {row_id} | {source} | {requirement} | {licensed_inference} | "
            "{blocked_inference} | `{licensed_use}` |".format(**row)
        )
    lines.extend(
        [
            "",
            "## KT#3 (03–21.09) — что должно измениться, чтобы снять NO_GO",
            "",
            "NO_GO снимается только при CLOSED RT-001 + RT-002 + RT-003, не этим файлом.",
            "",
            "| ID | Условие КТ#3 |",
            "|---|---|",
        ]
    )
    for row in payload.get("rows") or []:
        lines.append(f"| {row['row_id']} | {row['kt3_condition']} |")
    lines.extend(
        [
            "",
            "## Evidence pointers",
            "",
        ]
    )
    for row in payload.get("rows") or []:
        lines.append(f"- `{row['row_id']}`: `{row['evidence']}`")
    lines.append("")
    return "\n".join(lines)
