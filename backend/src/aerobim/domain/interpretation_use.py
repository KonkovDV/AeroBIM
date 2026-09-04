
"""Kane IUA ledger: which inferences current scores may support.

Validity is a property of an inference from a score to a use (Messick 1995;
Kane 2013), not of the tool. This module is the executable SSOT for that
boundary across Samolet TZ, TechLab/MIK checkpoints, tracker tasks, and
industry standards.

No row licenses customer precision, customer GO, native DWG, MEP delivered,
or CDE-ready BCF. RT-001 / RT-002 / RT-003 stay OPEN. Product checkpoint GO
is the regulatory-measurement MVP only.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from aerobim.domain.checkpoint import CHECKPOINT

LEDGER_ID = "aerobim_interpretation_use_ledger"
SCHEMA_VERSION = "1.2.1"
AUDITED_HEAD = "f9389bf"  # IUA freeze; hygiene commits after this do not reopen validity
CLAIM_BOUNDARY = (
    "Kane IUA over existing AeroBIM scores. Licensed uses stop at fixture "
    "demo, engine regression, open-bench countable subsets, gold-IDS "
    "processability, and protocol planning. Not customer precision, not TZ "
    ">90%, not customer SLA, not customer GO."
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
        "customer_go",
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
        "SAM-08",
        "samolet",
        "ТР-16/19: площади помещений / чертёж↔IFC",
        "AR IFC: rooms exist as objects; area QTO not runnable; coverage_map_only",
        "Площади квартир сверены с ТЭП; RT-001 CLOSED",
        "docs/quality/TZ_SEAM_COVERAGE_MAP_2026_08.md",
        "QTO area only after export with quantities or signed OOS",
        "engine_regression",
    ),
    _row(
        "SAM-09",
        "samolet",
        "ТР-8: огнестойкость стены vs ТЗ (класс II / C0)",
        "Wall FireRating sparse and ≠ TZ II/C0; coverage_map_only",
        "Fire check delivered; fixture REI60 = customer finding",
        "docs/quality/TZ_SEAM_COVERAGE_MAP_2026_08.md",
        "Customer IDS for fire class, not demo REI60",
        "engine_regression",
    ),
    _row(
        "SAM-10",
        "samolet",
        "ТЗ v1 (6 стр. бриф конкурса) vs v2 ТР vs семь сравнений vs проектное ТЗ",
        "v1 pin is coverage of the public brief; TBD filled in v2; >90% is not a product score",
        "Четыре бумаги Самолёта — один документ; v1 >90% измерено; семь задач сданы этим PDF",
        "docs/tz/TZ_V1_CONTEST_BRIEF_PIN_2026_08.md",
        "Keep paper-objects unmixed; MIK act cites interim 0.60",
        "engine_regression",
    ),
    _row(
        "PLAN-00",
        "techlab",
        "Инвентарь files/ (локальный NDA) как покрытие, не pack_hash",
        "27.08 public rehearsal pin plus 30.08 evening recensus after "
        "deleting covered source archives. Counts live in engineering pins, "
        "not the jury map. Live scan only under .local/. Not processed.",
        "sha256 пакета Самолёта в git; имена площадок в публичном дереве",
        "docs/quality/OWNER_AI_PLAN_EXECUTION_2026_08_27.md",
        "Keep NDA binaries and hashes out of git",
        "operational_hygiene",
    ),
    _row(
        "PLAN-01",
        "techlab",
        "QTO помещений или подписанный OOS (задача 3)",
        "Unsigned qto_space_area template; Missing QTO ≠ TEP Does-not",
        "Площади сверены с ТЭП; unsigned OOS = skip licensed",
        "samples/oos/qto_space_area.unsigned.json",
        "QTO export or appointing-party signed OOS",
        "protocol_planning",
    ),
    _row(
        "PLAN-02",
        "techlab",
        "ИОС IFC или подписанный MEP-OOS (задача 5 / RT-003)",
        "Unsigned mep_federated template; mep_system_clash=NOT_VERIFIED",
        "MEP delivered; unsigned OOS closes RT-003",
        "samples/oos/mep_federated.unsigned.json",
        "Federated MEP IFC or appointing-party signed OOS; RT-003 stays OPEN",
        "protocol_planning",
    ),
    _row(
        "PLAN-03",
        "techlab",
        "Стержни IFC или подписанный OOS п.7 (Solihin 4)",
        "Unsigned rebar_class4 template; .lir not parsed",
        "Арматура сверена с расчётом; pitch pset = class 4",
        "samples/oos/rebar_class4.unsigned.json",
        "Bar entities in IFC or appointing-party signed OOS of task 7",
        "protocol_planning",
    ),
    _row(
        "PLAN-04",
        "techlab",
        "Extractor по прозе проектного ТЗ: 0 hits = extraction_gap",
        "II/C0 and TEP prose ≠ fixture REI60 patterns; gap is mapping, not empty TZ",
        "В проектном ТЗ нет требований к огнестойкости и площадям",
        "docs/quality/OWNER_AI_PLAN_EXECUTION_2026_08_27.md",
        "Keep constructs unmixed; do not treat 0 hits as Does-not",
        "engine_regression",
    ),
    _row(
        "PLAN-05",
        "techlab",
        "Два независимых разметчика + κ/α до PrecisionClaim.publishable",
        "Protocol ready (RT-001 labeling); zero labeled customer points",
        "Один судья / LLM-as-judge = gold; >90% без κ",
        "docs/quality/RT001_LABELING_PROTOCOL_RT026_2026_08_03.md",
        "Dual named raters on a frozen remark set",
        "protocol_planning",
    ),
    _row(
        "TRK-01",
        "tracker",
        "Задача 1: доработать продукт к КТ#3 (03–21.09); КТ#2 был 20.08",
        "IFC Acceptance Gate + live CLI + run_kt3_jury; Checkpoint GO "
        "(regulatory_measurement_mvp; customer_go false)",
        "Checkpoint GO / market GO = customer GO",
        "docs/demo/KT3_TRACKER_SIX_TASKS_2026_08.md",
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
        "docs/demo/KT2_CORPUS_SSOT_2026_08.md",
        "Корпус ПД+экспертиза по-прежнему отсутствует",
        "open_bench",
    ),
    _row(
        "TRK-04",
        "tracker",
        "Задача 4: научный консультант / ИТ-ментор",
        "Вопросы и демо-ссылка в репозитории",
        "Выдуманные минуты консультаций",
        "docs/demo/KT3_JURY_FAQ_2026_08_25.md",
        "Минуты только после заметок владельца",
        "operational_hygiene",
    ),
    _row(
        "TRK-05",
        "tracker",
        "Задача 5: KPI = назначенные демо (3–5)",
        "Живой счёт только в локальном операторском слое (не в git)",
        "Назначенные демо как git-факт",
        "docs/demo/KT3_TRACKER_SIX_TASKS_2026_08.md",
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
        "SIG-01",
        "tracker",
        "Восемь задач 29.08: объём находок на канале IFC/PDF",
        "Report phrase: объём находок на канале получен. "
        "unrestricted_eq_sample is a capped unsigned ALL+eq sample, not a defect. "
        "EI 45 vs demo REI60 is SAM-09, not SP 2.13130.",
        "Product accuracy; pack processed; customer defect list; "
        "unsigned ALL+eq as SP; raising the mismatch cap as a defect export",
        "docs/quality/FINDING_VOLUME_CLAIM_BOUNDARY_2026_08.md",
        "Signed IDS (RT-002b) + dual raters (RT-001) before any publishable count",
        "operational_hygiene",
    ),
    _row(
        "SIG-02",
        "tracker",
        "Восемь задач 29.08: инвентарь канала (формат / processed / priority / legal)",
        "pack_probe + census pin; calc binaries are the majority of unpack bytes; "
        "Office token shortlist is not CC-2 MATCH. "
        "Uncompressed byte totals stay out of git.",
        "43 GB processed; native .lir parse; token shortlist as CC-2 MATCH; "
        "byte totals of the NDA tree in git",
        "docs/quality/CHANNEL_PACK_TRIAGE_2026_08.md",
        "Owner pastes name-free aggregate after OA-9; hashed TSV stays .local",
        "operational_hygiene",
    ),
    _row(
        "JURY-01",
        "mik",
        "Отборочная комиссия №7: роли на карте жюри, не ФИО и не census NDA",
        "Seat briefs are roles; three partner seats by agreement; "
        "unpack counts stay off TIER0; tracker paths have no personal names.",
        "Sitting-member list in git; OSINT bios as confirmed; unpack fingerprint "
        "counts on the jury map; pack processed",
        "docs/quality/JURY_PACK_TRIAGE_2026_09.md",
        "Keep FIO and NDA fingerprint counts off jury surfaces",
        "operational_hygiene",
    ),
    _row(
        "FMT-01",
        "tracker",
        "Восемь задач 29.08: закрытые CAD/solver как объект обмена, не как парсеры",
        "KT#3 exchange is IFC + PDF/A. Closed Autodesk CAD and .lir stay fail-closed. "
        "Stock Navisworks does not write IFC. ODA trial is measurement, not a product.",
        "DWG product; native RVT/NWD reader; parse .lir; OCR delivered; "
        "Sustaining 7500 USD = RVT; DrawingVQA as AeroBIM accuracy",
        "docs/quality/FORMAT_INGEST_TRIAGE_2026_09.md",
        "Appointing-party IFC/PDF; readable calc notes; NWD federation as IFC or OOS",
        "operational_hygiene",
    ),
    _row(
        "SPG-01",
        "tracker",
        "Консалтинг СПГ август 2026: речь про данные ПД/РД, не рынок FM и не SAM",
        "8-page construction cut is attributed speech. 60-page FM/PM cut is adjacent. "
        "PDFs stay off git. Filename stays off TIER0.",
        "SPG figures as AeroBIM SAM or accuracy; 49% TIM as pack ready; "
        "digital twin / FM product; HubEx percent as ours; ISUP by 21.09",
        "docs/quality/K4_COMMERCIAL_PATH_2026_08.md",
        "Keep the consulting pin; keep the filename off the jury map",
        "operational_hygiene",
    ),
    _row(
        "UI-01",
        "tracker",
        "ТЗ интерфейс: рабочее место полного цикла, не review shell как сдача",
        "Shell inspects persisted reports. This pass wires upload, job poll, KPI, "
        "eight-screen IA, and a dev-only git walls+IDS seed. UI does not write "
        "summary.passed. Natives fail-closed. Jury laptop stays CLI.",
        "Full-cycle workplace delivered; native RVT in UI; 30 min SLA measured; "
        "10D live; XLSX export; Checkpoint GO from chrome; seed as customer pack",
        "docs/quality/UI_EXPERT_WORKPLACE_TRIAGE_2026_09.md",
        "Jury laptop CLI; mentor may seed git fixture; keep NO_GO; natives fail-closed. "
        "Demo seed stays off published OpenAPI.",
        "operational_hygiene",
    ),
    _row(
        "TL-01",
        "techlab",
        "КТ#2 (до 20.08): этап МИК «доработка»",
        "Предварительная версия в ЛК; GitHub прототип; видео не прилагаем, показ = живой CLI",
        "Валидация эффективности начата; внедрение начато",
        "docs/docs.md",
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
        "TL-03",
        "techlab",
        "Участие в «Техлаб Москва»: физлица или команда 1–10 (FAQ i.moscow/techlab)",
        "ИП/ООО не условие входа; приз — платный пилот 2 млн ₽",
        "Без юрлица нельзя участвовать / нельзя принять приз — как факт Положения",
        "docs/partners/TECHLAB_TASK_07_READINESS_2026.md",
        "Оплату приза уточнять только по соглашению Партнёра и Фонда",
        "operational_hygiene",
    ),
    _row(
        "TL-04",
        "techlab",
        "Сравнение 1: ПД/РД ↔ АГО/АГР (листы, фасады, ТЭП)",
        "Filename coindex on coverage map; overlay remains fixture-only",
        "АГР/QTO сданы; задача 1 закрыта",
        "docs/quality/TECHLAB_SEVEN_TASKS_CARTOGRAPHY_2026_08.md",
        "Sheet gold + dual raters; VLM stays advisory",
        "engine_regression",
    ),
    _row(
        "TL-05",
        "techlab",
        "Сравнение 2: ПД ↔ каталоги / EIR LOD",
        "Catalog and EIR workbooks as carriers; not customer_approved IDS",
        "IDS Самолёта утверждён из Стандарта",
        "docs/quality/TECHLAB_SEVEN_TASKS_CARTOGRAPHY_2026_08.md",
        "Appointing-party IDS with pack_hash (RT-002b)",
        "protocol_planning",
    ),
    _row(
        "TL-06",
        "techlab",
        "Сравнение 3: планировки ОПР/ПД/РД (оси, помещения, двери)",
        "IfcSpace/IfcDoor presence is coverage_map_only; QTO absent is Missing",
        "Планировки сверены по стадиям; площади проверены",
        "docs/quality/TECHLAB_SEVEN_TASKS_CARTOGRAPHY_2026_08.md",
        "QTO export or signed OOS; RD IFC if stage compare is in scope",
        "engine_regression",
    ),
    _row(
        "TL-07",
        "techlab",
        "Сравнение 4: планировки ↔ ИРД / проектное ТЗ",
        "II/C0, wall EI, door EI, fixture REI60 are different constructs",
        "Планировки соответствуют ТЗ; огнестойкость сертифицирована",
        "docs/quality/TECHLAB_SEVEN_TASKS_CARTOGRAPHY_2026_08.md",
        "Customer fire IDS, not demo REI60",
        "engine_regression",
    ),
    _row(
        "TL-08",
        "techlab",
        "Сравнение 5: АР/КР/ПБ/ТХ/ИОС между собой",
        "AR+KR IFC; other disciplines PDF; IfcFlowTerminal in AR ≠ IOS model",
        "MEP delivered; federated clash delivered",
        "docs/quality/TECHLAB_SEVEN_TASKS_CARTOGRAPHY_2026_08.md",
        "Federated MEP IFC or written MEP-OOS (RT-003)",
        "protocol_planning",
    ),
    _row(
        "TL-09",
        "techlab",
        "Сравнение 6: повторная проверка ↔ выданные замечания",
        "After-tree thicker than before is coverage_map_only; OEP is not gold",
        "Замечания закрыты; книга ОЭП = gold",
        "docs/quality/TECHLAB_SEVEN_TASKS_CARTOGRAPHY_2026_08.md",
        "Dual named raters + κ on a frozen remark set (RT-001)",
        "protocol_planning",
    ),
    _row(
        "TL-10",
        "techlab",
        "Сравнение 7: армирование ↔ расчётные карты (Solihin 4)",
        "No IfcReinforcingBar; wall pitch pset ≠ class 4; .lir not parsed",
        "Арматура сверена с расчётом; LIRA solved",
        "docs/quality/TECHLAB_SEVEN_TASKS_CARTOGRAPHY_2026_08.md",
        "Bar entities in IFC or written OOS of task 7",
        "engine_regression",
    ),
    _row(
        "MIK-01",
        "mik",
        "Соглашение / акт / финотчётность Фонда (M2, M7, M8)",
        "Контур документирован; формы не сочиняем; 449-ПП ≠ вход в Техлаб",
        "Самодельные шаблоны Фонда; акт с fixture-цифрами; ИП как вход",
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
        "Inventory 196 tasks / 9 families; Harbor agent NOT_RUN; "
        "authors: coding agents fail visual grounding",
        "AEC-Bench run as product drawing literacy / RT-001 CLOSED",
        "docs/evidence/aec-bench-false-pass-2026-08.md",
        "Harbor only as labeled open-bench, never as Samolet PD",
        "open_bench",
    ),
    _row(
        "IND-07",
        "industry",
        "LLM-as-judge 2026 (arXiv:2606.19544; 2509.20293; 2604.15224)",
        "VLM remains advisory candidate; TP/FP require dual human raters and κ",
        "Model confirms findings / judges precision / stakes-framed verdict",
        "docs/architecture/ADR-001-verdict-ownership-2026.md",
        "PrecisionClaim.publishable remains the only accuracy gate",
        "protocol_planning",
    ),
    _row(
        "IND-08",
        "industry",
        "Clash management 2026 (Buildings 16(13):2623) + Mehrbod/Hu/Lin",
        "Geometric overlap on fixture; mep_system_clash=NOT_VERIFIED",
        "MEP delivered; AABB inventory as coordination-complete",
        "docs/evidence/federated-clash-planted-2026-08.md",
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
    _row(
        "IND-11",
        "industry",
        "EGCC 2026 (arXiv:2607.29058) constraint checking",
        "False-pass 41-52%; authors: not for autonomous approval",
        "EGCC % = AeroBIM on customer PD; autonomous approve",
        "docs/quality/TZ_SEAM_COVERAGE_MAP_2026_08.md",
        "Four-state Meets/Missing/Uncertain; expert stays in the loop",
        "open_bench",
    ),
    _row(
        "IND-12",
        "industry",
        "DrawingVQA 2026 (arXiv:2607.15418) issued-for-construction sheets",
        "Authors: main table professionals 94.9 vs Gemini-2.5-pro 71.7; "
        "supplementary Gemini-3-pro-preview 77.2 is not the main-table SOTA; "
        "QTO/R3 weak; not AeroBIM",
        "DrawingVQA as AeroBIM product accuracy / TZ task 1 done",
        "docs/quality/TZ_SEAM_COVERAGE_MAP_2026_08.md",
        "VLM advisory only; no sheet-level sign-off",
        "open_bench",
    ),
    _row(
        "IND-13",
        "industry",
        "Jurisdiction IFC pre-check 2026 (CORENET X, RAVA3.5.3, city AGR)",
        "City-as-publisher pattern = RT-002a analog; not appointing-party EIR",
        "Public permit IDS = Samolet-signed profile / Task 07 delivered",
        "docs/quality/TZ_SEAM_COVERAGE_MAP_2026_08.md",
        "Keep RT-002a and RT-002b unmixed",
        "open_bench",
    ),
    _row(
        "IND-14",
        "industry",
        "Panoptic CAD symbol spotting (FloorPlanCAD / ArchCAD-400k / VecFormer)",
        "Luo et al. arXiv:2503.22346: semantic F1 87.8 and panoptic PQ 70.6 "
        "on ArchCAD; PQ not comparable across FloorPlanCAD papers; "
        "cv_human_level=MISSING",
        "VecFormer/DPSS in-paper PQ or FloorPlanCAD as AeroBIM drawing literacy",
        "docs/architecture/TARGET_HYBRID_ARCHITECTURE_TZ_2026.md",
        "Keep cv_human_level=MISSING; no VecFormer/DPSS in runtime",
        "open_bench",
    ),
    _row(
        "IND-15",
        "industry",
        "Clash-report relevance ML (Ailem AiC 2026; Lin & Huang 2019)",
        "Ailem: false positives up to 60% on BIM clash reports. Lin hybrid "
        "0.96 is their corpus. AeroBIM triage is deterministic dedup/band/"
        "rank and never drops a clash",
        "Lin 0.96 or Ailem 60% as AeroBIM clash quality or a Navisworks killer",
        "docs/evidence/federated-clash-planted-2026-08.md",
        "Keep no-ML filter; RT-003 stays OPEN",
        "protocol_planning",
    ),
    _row(
        "IND-16",
        "industry",
        "SOTA 29.08: DWG layer/block/ATTRIB as almost-free symbol labels",
        "Native DWG parser is not implemented; optional ezdxf is DXF; "
        "layer labels are not a product DWG reader",
        "Most symbols identified from DWG layers without ML / native DWG delivered",
        "docs/architecture/ADR-003-dwg-oda-trial-kt3-2026.md",
        "Keep dwg_dxf MISSING on analyze",
        "not_licensed",
    ),
    _row(
        "IND-17",
        "industry",
        "SOTA 29.08: OmniDocBench / titleblock text-extract ~0.95 as drawing OCR",
        "RapidOCR is optional extra on raster; PubLayNet/DocLayNet are not "
        "construction sheets; GOST stamp template is not measured here",
        "0.95 OCR / titleblock accuracy as AeroBIM on customer sheets",
        "docs/pilot-claim-boundary-2026.md",
        "Keep cv_human_level=MISSING; OCR does not clear drawing ERROR",
        "open_bench",
    ),
    _row(
        "MIK-03",
        "mik",
        "Commission weights (attributed order 17.06.2026): K1=40 of 100",
        "Mean of sitting members; prize floor 50 is a program rule; "
        "low-K1 + high-rest totals 45-64 so 50 is not automatic",
        "Git HEAD predicts a prize-clearing AeroBIM total / Checkpoint GO",
        "docs/quality/MIK_COMMISSION_SCORING_2026_08.md",
        "Application roster is the K1 object; no numeric forecast from git",
        "protocol_planning",
    ),
    _row(
        "MIK-04",
        "mik",
        "Catalog roster vs signed commission order; partner seats by agreement",
        "Two Fund seats are staff; three partner seats are not guaranteed; "
        "sponsor quote is not the chair",
        "Catalog page is the sitting commission / partner seats are certain",
        "docs/quality/MIK_COMMISSION_SCORING_2026_08.md",
        "Prepare to the signed order; do not publish sitting-member lists",
        "operational_hygiene",
    ),
    _row(
        "MIK-05",
        "mik",
        "Owner-briefing B1-B5 (Regulation Appendix 3 unseen); tie-break B1 only",
        "B2 needs protocols AND confirmed partner metrics; pytest is not B2 high; "
        "NO_GO does not license a System B prize-clearing total",
        "Pytest / fixture SLA as Partner validation / System B already ≥50",
        "docs/quality/KT3_FIXTURE_VALIDATION_COVER_2026_08.md",
        "Keep confirmed_partner_validation_metrics False until RT-001",
        "protocol_planning",
    ),
    _row(
        "MIK-06",
        "mik",
        "Regulation 6.3: prize agreement may assign exclusive rights without extra pay",
        "LICENSE is MIT; ADR-002 is a commercial-boundary plan, not a patent wall",
        "IP is fenced / exclusive rights will not transfer",
        "docs/architecture/ADR-002-open-core-commercial-boundary-2026.md",
        "Do not promise a patent fence in the application",
        "operational_hygiene",
    ),
    _row(
        "TL-11",
        "techlab",
        "K1 scores the filed team (up to 10), not oral advisors",
        "FAQ already allows 1-10 with mixed scientific and engineering skill",
        "Consultants named in chat are on the scored roster / K1 closed",
        "docs/partners/TECHLAB_SAMOLET_APPLICATION_2026.md",
        "Owner files roles with evidence; git does not invent the roster",
        "operational_hygiene",
    ),
    _row(
        "IND-18",
        "industry",
        "GOST R 72514-2026 order 64-st on the official fund card",
        "protect.gost.ru lists 64-st / 30.01.2026; introduction 01.05.2026; "
        "self-assessment remains not certification",
        "Drop the order number / cite the self-assessment as certification",
        "docs/quality/AI_SYSTEM_IMPACT_ASSESSMENT_GOST_R_72514_2026.md",
        "Keep the card citation; do not claim a conformity mark",
        "protocol_planning",
    ),
    _row(
        "IND-19",
        "industry",
        "GOST R 72515-2026 (ISO/IEC 12792:2025) transparency taxonomy",
        "Maps onto NOT_IMPLEMENTED, advisory LLM/VLM, ADR-001; order 65-st on the fund card",
        "GOST R 72515 certificate / trusted-model listing",
        "docs/quality/AI_TRANSPARENCY_TAXONOMY_GOST_R_72515_2026.md",
        "Keep the taxonomy map; still not a conformity declaration",
        "protocol_planning",
    ),
    _row(
        "IND-20",
        "industry",
        "MinTsifry bill ID 166424 (planned force 01.09.2027)",
        "Draft not in the Duma; ADR-001 matches future synthetic-content "
        "logic as a K2 argument only",
        "In-force AI law / trusted model / AeroBIM is already compliant",
        "docs/quality/AI_TRANSPARENCY_TAXONOMY_GOST_R_72515_2026.md",
        "Cite as horizon; do not speak as if the bill is in force",
        "protocol_planning",
    ),
    _row(
        "MIK-07",
        "mik",
        "Criterion → git evidence map as findability, not a score",
        "Pointers for K1–K5 and B1–B5; predicted_aerobim_total stays None",
        "Evidence map = prize-clearing total / Checkpoint GO",
        "docs/quality/MIK_CRITERION_EVIDENCE_MAP_2026_08.md",
        "Keep the map as a pointer; do not mint a numeric forecast",
        "protocol_planning",
    ),
    _row(
        "IND-21",
        "industry",
        "GOST R 71476-2024 (ISO/IEC 22989:2022) AI concepts and terminology",
        "Order 1550-st / 28.10.2024 / in force 01.01.2025; terms only",
        "We standardized the industry / certified terminology",
        "docs/quality/NATIONAL_AI_GOST_STACK_KT3_2026.md",
        "Keep terminology map; still not a conformity mark",
        "protocol_planning",
    ),
    _row(
        "IND-22",
        "industry",
        "GOST R ISO/IEC 42001-2024 AI management system",
        "Official fund card 1549-st; HITL + ADR-001 + impact map = partial",
        "Certified AIMS / 42001 conformity mark / trusted-model listing",
        "docs/quality/NATIONAL_AI_GOST_STACK_KT3_2026.md",
        "Keep mapping; gost_42001_certified stays False",
        "protocol_planning",
    ),
    _row(
        "IND-23",
        "industry",
        "LETI public Appendix 4 table (30.04.2026): Partner task is row 6",
        "Paid pilot 2M; neighbouring row 7 is a different partner task",
        "Handout 07 = Appendix 4 number / row 7 is our Partner task",
        "docs/quality/MIK_COMMISSION_SCORING_2026_08.md",
        "Speak Appendix 4 №6; do not mix with the neighbouring row",
        "operational_hygiene",
    ),
    _row(
        "TL-12",
        "techlab",
        "i.moscow/pilot city grant vs TechLab prize 2M",
        "City pilots ask a legal entity and TRL-ish 6; 449-PP ≠ TechLab entry",
        "City grant / 449-PP is the TechLab 2M prize or the entry ticket",
        "docs/partners/MIK_PILOT_COMPLIANCE_2026.md",
        "Keep 449-PP VERIFY; do not substitute the prize instrument",
        "operational_hygiene",
    ),
    _row(
        "MIK-08",
        "mik",
        "Prize floor 50 is reachable inside K1-low if rest is high",
        "K1 16 + rest-high lo 36.6 = 52.6 identity; 10 people not required",
        "Need 10 named people / K1 must leave low / git predicts ≥50",
        "docs/quality/MIK_A_LEVERS_PAST_50_2026_08.md",
        "Keep predicted_aerobim_total None; do not sit at the bottom of K1-low",
        "protocol_planning",
    ),
    _row(
        "IND-24",
        "industry",
        "GOST R 58048-2017 TRL scale (order 2128-st)",
        "Self-assess TRL 4 (lab/CI/fixture); TRL 5 needs partner environment",
        "Independent OGT / TRL 5 / PP 2204 / city TRL 6 as this K2 score",
        "docs/quality/TRL_GOST_R_58048_SELF_ASSESS_2026.md",
        "Keep trl_5_claimed False; not an independent readiness exam",
        "protocol_planning",
    ),
    _row(
        "TL-13",
        "techlab",
        "K3 is partner-fit; B2 is partner validation metrics",
        "Public mandate ticksheet; 0.60 protocol is sign-ready not signed",
        "Empty partner metrics means K3 must be low / pytest is K3-high",
        "docs/quality/K3_PARTNER_FIT_TICKSHEET_2026_08.md",
        "Keep k3_equals_validation_metrics False",
        "protocol_planning",
    ),
    _row(
        "MIK-09",
        "mik",
        "K4 commercial path: TAM labeled, SAM empty, 2M prize is SOM",
        "GidMarket BIM 10.1 bn RUB 2022 via TAdviser is TAM; hours A1-A8 empty",
        "10.1 bn is our SAM / 72% analog is our effect / other MIK 500M packaging",
        "docs/quality/K4_COMMERCIAL_PATH_2026_08.md",
        "Keep k4_revenue_claimed and foreign_labor_cut_as_ours False",
        "protocol_planning",
    ),
    _row(
        "IND-25",
        "industry",
        "PNST 841-2023 AI quality evaluation (order 61-pnst)",
        "Maps onto 0.60 protocol + dual-rater + F1; preliminary, not GOST R",
        "SQuaRE certificate / certified AI quality assessment",
        "docs/quality/PNST_841_AI_QUALITY_EVAL_2026.md",
        "Keep pnst_841_certified False",
        "protocol_planning",
    ),
    _row(
        "TL-14",
        "techlab",
        "Seat briefs and application paste without a git roster",
        "One paragraph per role; mean of sitting seats; 0.60 cover is sign-ready",
        "Sitting FIO in git / predicted score from paste / protocol already signed",
        "docs/quality/MIK_SEAT_BRIEFS_2026_08.md",
        "Keep partner_kpis_agreed_in_writing False; person cells stay empty",
        "operational_hygiene",
    ),
    _row(
        "MIK-10",
        "mik",
        "Band identity 16+36.6=52.6 is not a predicted AeroBIM total",
        "reachable_inside_low_k1_if_rest_high is arithmetic; prize floor stays 50",
        "Quote 'floor reachable' / 52.6 as the team's expected score",
        "docs/quality/MIK_A_LEVERS_PAST_50_2026_08.md",
        "Keep predicted_aerobim_total None",
        "protocol_planning",
    ),
    _row(
        "TL-15",
        "techlab",
        "Public task-page names and sponsor quote vs signed commission",
        "Catalog FIO are publication; sponsor quote is not attested chair",
        "Those names sit the jury / fill K1 / chair the commission",
        "docs/partners/TECHLAB_SAMOLET_APPLICATION_2026.md",
        "Keep sponsor_quote_is_commission_chair False",
        "operational_hygiene",
    ),
    _row(
        "MIK-11",
        "mik",
        "Order p.2.1 selection is a mean; p.2.2 final is a sum; App 3 unseen",
        "K1-K5 recovered from the order protocol form; Regulation Appendix 3 "
        "not in git; prize floor 50 has unknown max if the sum table is unseen",
        "B1-B5 are Regulation Appendix 3 / final scored as a mean / 50 of 100 known",
        "docs/quality/MIK_COMMISSION_SCORING_2026_08.md",
        "Keep regulation_appendix_3_in_git False; ask organizers for the Regulation",
        "protocol_planning",
    ),
    _row(
        "MIK-12",
        "mik",
        "K4 after partner 1H2026 IFRS: zero entry, not a CAPEX ask",
        "Pay-on-result speech is not a signed SKU; IFRS loss is not our saving; "
        "200M AI program is theirs, not AeroBIM",
        "Invest in us / we offset the IFRS loss / RAS +31% is group IFRS",
        "docs/quality/K4_COMMERCIAL_PATH_2026_08.md",
        "Keep k4_asks_customer_capex and k4_offsets_partner_ifrs_loss False",
        "protocol_planning",
    ),
    _row(
        "TL-16",
        "techlab",
        "Four catalog cards are filtered survivors, not all applicants",
        "Neighbor-task 46 teams is a different Partner in the same first stream; "
        "peer card claims are not audited public fact",
        "Four cards = everyone who applied / 15 pilots and 600+ norms are verified",
        "docs/quality/K2_NOVELTY_VS_PEERS_2026_08.md",
        "Keep catalog_four_are_all_applicants False",
        "operational_hygiene",
    ),
    _row(
        "IND-26",
        "industry",
        "Stand-alone RAS 1H2026 revenue +31% is not group IFRS -31%",
        "Opposite signs on the same window; mixing them drops tech-customer trust",
        "Cite RAS growth as the group IFRS picture / one figure two signs",
        "docs/quality/K4_COMMERCIAL_PATH_2026_08.md",
        "Keep ras_ifrs_signs_are_the_same False",
        "protocol_planning",
    ),
    _row(
        "SAM-11",
        "samolet",
        "ТР-17: неэффективное использование пространства (продаваемая площадь / МОП / коридоры)",
        "IfcSpace inventory remains ADVISORY_ONLY until appointing-party "
        "thresholds are signed; scope is OA-14",
        "Space efficiency delivered / customer does not need the row / "
        "numeric KPI without signature",
        "docs/quality/KT3_WINDOW_CRITICAL_PATH_2026_09.md",
        "Owner records in-scope advisory vs out-of-MVP before the 22.09 rehearsal",
        "protocol_planning",
    ),
    _row(
        "IND-27",
        "industry",
        "ODA Sustaining vs BimRv/BimNv extensions (public 2026 list)",
        "Sustaining 7500/4500 USD is the SaaS DWG floor; RVT/NWD need 6250 USD extensions each",
        "7500 USD = native RVT/NWD / CADSoftTools 1660 USD as 2026 floor / LibreDWG in MIT core",
        "docs/quality/NATIVE_CAD_LICENSE_FORK_OSINT_2026_08.md",
        "Keep native Autodesk fail-closed; IFC exchange, not SDK purchase, for MVP",
        "protocol_planning",
    ),
    _row(
        "IND-28",
        "industry",
        "Wilson 1927 / Brown–Cai–DasGupta 2001: 6/6 is not unity for a jury",
        "wilson_interval(6,6) 95% lower ~0.61; fixture AABB P/R stays unpublished to the jury",
        "Show 1.0 at n=6 even with a caveat / treat as TZ clash >90%",
        "docs/evidence/clash-measurement-slice-2026-08/README.md",
        "Protocol n~100 + two raters before any publishable rate",
        "not_licensed",
    ),
    _row(
        "SAM-12",
        "samolet",
        "п. 1.1.4: офис 500 МБ / модели 1,5 ГБ — ingest + RocksDB; SPF/WASM 256 МиБ",
        "AEROBIM_MAX_IFC_BYTES stays 256 MiB SPF; files up to 1.5 GB open via "
        "IfcOpenShell RocksDB; WASM stays 256 MiB; HTTP 413 over 1.5 GB",
        "We already SPF-open 1.5 GB / raise default SPF cap because it is config / "
        "bSI 256 MB = our 256 MiB / WASM shows 1.5 GB",
        "docs/quality/IFC_ANALYZE_VS_INGEST_CAP_2026_08.md",
        "OA-16 RSS on a local over-SPF file via RocksDB; do not raise SPF default",
        "protocol_planning",
    ),
    _row(
        "IND-29",
        "industry",
        "IfcOpenShell SPF RAM ~8–10× disk (#7116, ~275–300 MB Riverside)",
        "Planning multiplier 10: 256 MiB analyze → ~2.5 GiB RSS; 1.5 GB ingest → ~15 GiB",
        "Raising the analyze cap is a one-line settings change / RSS equals file size",
        "docs/quality/IFC_ANALYZE_VS_INGEST_CAP_2026_08.md",
        "RocksDB is wired for over-SPF files; stream2/R-tree are not the analyze path",
        "not_licensed",
    ),
    _row(
        "PLAN-06",
        "techlab",
        "LIRA/RD compare is four declared-value checks, not a solver",
        "CC-2/CC-4 comparable when a readable note exists; CC-1/CC-3 sample; .lir closed",
        "Independent recalculation / As from IFC without IfcReinforcingBar / LIRA accuracy %",
        "docs/quality/CALCULATION_COMPARE_FOUR_CHECKS_2026_09.md",
        "Say the solver boundary aloud; partial method GO is not product accuracy",
        "protocol_planning",
    ),
    _row(
        "TL-17",
        "techlab",
        "Five former TBD TZ sections are a confirmation request, not a blank form",
        "TZ v2 fills architecture, code/build, solution image, presentation, accompanying docs",
        "Ask organizers to draft empty TBD from 09.07 / compare teams on unfilled bars",
        "docs/tz/TZ_SAMOLET_TECHLAB_TASK_07_V2_2026.md",
        "Send our edition for confirmation (OA-8)",
        "operational_hygiene",
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
            "EGCC 2026 (arXiv:2607.29058) — false-pass too high for autonomous approval",
            "DrawingVQA 2026 (arXiv:2607.15418) — drawing QA ≠ package acceptance",
            "ArchCAD-400k DPSS (arXiv:2503.22346) — semantic F1 87.8 ≠ panoptic PQ 70.6",
            "Ailem 2026 clash-report FP up to 60%; Lin 2019 hybrid 0.96 is not our filter",
            "GOST R 72514-2026 fund card 64-st — self-assessment ≠ certification",
            "GOST R 72515-2026 (ISO/IEC 12792:2025) — taxonomy map, not a certificate",
            "MinTsifry bill 166424 — draft, planned force 01.09.2027, not in-force law",
            "GOST R 71476-2024 order 1550-st — terminology, not an industry certificate",
            "GOST R ISO/IEC 42001-2024 fund card 1549-st — mapping ≠ certified AIMS",
            "LETI 30.04.2026 Appendix 4 row 6 = Partner paid-pilot task",
            "GOST R 58048-2017 TRL self-assess 4 is not TRL 5 or independent OGT",
            "PNST 841-2023 order 61-pnst — mapping is not a SQuaRE certificate",
            "GidMarket BIM TAM 10.1 bn RUB 2022 is not AeroBIM SAM",
            "SPbPU 25.1 bn RUB by 2030 is not AeroBIM revenue",
            "Task-page sponsor quote is not the attested commission chair",
            "Regulation Appendix 3 (final criteria) is not in git",
            "Partner 1H2026 IFRS loss is not an AeroBIM saving",
            "Stand-alone RAS +31% is not group IFRS -31%",
            "ODA Sustaining 2026 list is not BimRv/BimNv; CADSoftTools floor is quote-page 765 USD",
            "Wilson 6/6 95% lower ~0.61 is not a jury exhibit of unity",
            (
                "IfcOpenShell #7116 SPF RAM ~8–10× disk (Riverside ~275–300 MB); "
                "1.5 GB ingest is not that RSS"
            ),
            "MOEXP IDS 06.03.2026 is RT-002a (city-as-publisher), not Samolet RT-002b",
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
        "<!-- claims-lint: allow-file "
        'reason="Kane IUA ledger; TZ 90%/SLA as blocked inferences; NO_GO" -->',
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
        "имеют право значить для Самолёта, трекера проекта, Техлаба, МИК и "
        "отраслевых стандартов, и чего они значить не имеют.",
        "",
        f"- Checkpoint **{CHECKPOINT}**",
        f"- IUA freeze (construct-validity object, not HEAD): `{payload.get('audited_head')}`",
        "- closes_rt001/002/003: **false**",
        "- CLI: `python -m aerobim.tools.export_interpretation_use_ledger --write-docs-evidence`",
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
        evidence = row["evidence"]
        if evidence.startswith(("python -m ", "python ")):
            lines.append(f"- `{row['row_id']}`: `{evidence}`")
        else:
            lines.append(
                f"- `{row['row_id']}`: [{_evidence_label(evidence)}]({_evidence_href(evidence)})"
            )
    lines.append("")
    return "\n".join(lines)


def _evidence_label(path: str) -> str:
    return Path(path).name.replace("\\", "/")


def _evidence_href(path: str) -> str:
    for prefix, target in (
        ("docs/quality/", ""),
        ("docs/", "../"),
        ("samples/", "../../samples/"),
        ("audit/", "../../audit/"),
    ):
        if path.startswith(prefix):
            return target + path[len(prefix) :]
    return path
