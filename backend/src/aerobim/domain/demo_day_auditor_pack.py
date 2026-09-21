# ruff: noqa: E501
"""Demo-day auditor pack — blocks A–F for TechLab 21.09.2026.

Pins already in git. Does not close RT-001/002/003.
Does not put census fingerprints on licensed slide lines.
Checkpoint GO; customer_go false.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Final

from aerobim.domain.checkpoint import CHECKPOINT
from aerobim.domain.deep_study_facts import PUBLIC_DEEP_STUDY
from aerobim.domain.demo_day_speech_lock import (
    AECV_VALUE,
    AUTH_BFF_DEFAULT,
    CDE_IMPORT,
    DUPLEX_CLASH_COUNT,
    EXPERIMENT_B_KR_DETECTED,
    EXPERIMENT_B_KR_N,
    MOEXP_IDS_FILES,
    MOEXP_IDS_SPECS,
    PUBLIC_IDS_FILES,
    PUBLIC_IDS_SPECS,
    RECOMMENDED_N,
    SPACE_AREA_FROM_GEOMETRY,
    ifcspace_total,
)
from aerobim.domain.finding_volume import REPORT_PHRASE
from aerobim.domain.mik_commission_scoring import TRL_SELF_ASSESS, trl_5_claimed
from aerobim.domain.unpack_census import PUBLIC_UNPACK_CENSUS

CLAIM_LEVEL: Final = "audit_table_not_score"
CLAIM_BOUNDARY: Final = (
    "Auditor table for TechLab demo day blocks A–F. Carrier census is not "
    "pack processed. Fixture SLA is not customer SLA. Open-bench clash is not "
    "partner AR↔MEP. Checkpoint GO (regulatory_measurement_mvp; customer_go false)."
)

STATUSES: Final = (
    "VERIFIED_CUSTOMER",
    "VERIFIED_INTERNAL",
    "SYNTHETIC",
    "NOT_VERIFIED",
    "NEEDS_CUSTOMER",
    "NO_DATA",
)

E1_TEXT: Final = "Один лишний круг согласования РД на типовой секции существует"
E2_TEXT: Final = "Длительность круга — **N рабочих дней** (N задаёт заказчик)"
E3_TEXT: Final = "Стоимость дня комплекта — их внутренняя цифра (не публикуем)"
E4_TEXT: Final = (
    "Система снимает **не больше одного** круга на эталонном корпусе "
    "после канонической пары ревизий"
)
E5_TEXT: Final = "Повторяемость на типовой секции > единичный дефект"

NON_CLAIM_COUNT: Final = 40
SLIDE_LINE_MAX: Final = 90

# Census fingerprints stay in value/source, never in slide_line.
_FINGERPRINT_TOKENS: Final = ("2552", "6408", "10599")


def _runtime_baseline() -> dict[str, Any]:
    path = (
        Path(__file__).resolve().parents[4] / "docs" / "evidence" / "runtime-baseline-latest.json"
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("runtime-baseline-latest.json must be an object")
    return payload


def _ci_backend_line() -> str:
    backend = _runtime_baseline()["backend"]
    return (
        f"{backend['tests_passed']} / {backend['tests_collected']} / "
        f"{backend['tests_failed']} / {backend['tests_skipped']}"
    )


def _ci_frontend_line() -> str:
    frontend = _runtime_baseline()["frontend"]
    return f"{frontend['tests_passed']} / {frontend['tests_failed']}"


def _ci_backend_slide() -> str:
    backend = _runtime_baseline()["backend"]
    return (
        f"CI: бэкенд {backend['tests_passed']} из {backend['tests_collected']}, "
        f"{backend['tests_failed']} упало, {backend['tests_skipped']} skipped."
    )


def _ci_frontend_slide() -> str:
    frontend = _runtime_baseline()["frontend"]
    return f"CI: фронт {frontend['tests_passed']} / {frontend['tests_failed']}. Только из runtime-baseline."


def _row(
    fact_id: str,
    claim: str,
    value: str,
    source: str,
    status: str,
    slide: bool,
    slide_line: str,
) -> dict[str, str | bool]:
    if status not in STATUSES:
        raise ValueError(f"unknown status {status} for {fact_id}")
    line = slide_line if slide else (slide_line or "не на слайд")
    if len(line) > SLIDE_LINE_MAX:
        raise ValueError(f"{fact_id} slide_line {len(line)} > {SLIDE_LINE_MAX}")
    for token in _FINGERPRINT_TOKENS:
        if token in line:
            raise ValueError(f"{fact_id} slide_line carries fingerprint {token}")
    return {
        "id": fact_id,
        "claim": claim,
        "value": value,
        "source": source,
        "status": status,
        "slide": "да" if slide else "нет",
        "slide_line": line,
    }


def _space_total() -> int:
    return ifcspace_total()


FACT_ROWS: Final[tuple[dict[str, str | bool], ...]] = (
    # --- A. Channel pack 25.08 ---
    _row(
        "A-01",
        "Канал комплекта получен",
        "2026-08-25; hashed pack not in git; names/hashes false",
        "audit/evidence/customer-intake-gate.json §share_received_at; docs/evidence/unpack-census-latest.json names_in_git",
        "VERIFIED_INTERNAL",
        True,
        "Канал 25.08 получен. Хеш-пакета в git нет. Не говорить «данных нет».",
    ),
    _row(
        "A-02",
        "Файлов в обёртке (вечерний census)",
        str(PUBLIC_UNPACK_CENSUS["wrapper_file_count"]),
        "docs/evidence/unpack-census-latest.json wrapper_file_count; domain/unpack_census.py",
        "VERIFIED_INTERNAL",
        False,
        "счётчик census не на слайд",
    ),
    _row(
        "A-03",
        "Файлов в unpack-дереве (вечерний census)",
        str(PUBLIC_UNPACK_CENSUS["unpacked_file_count"]),
        "docs/evidence/unpack-census-latest.json unpacked_file_count",
        "VERIFIED_INTERNAL",
        False,
        "счётчик census не на слайд",
    ),
    _row(
        "A-04",
        "Уникальные IFC на канале",
        f"{PUBLIC_DEEP_STUDY['unique_ifc_count']} unique SPF; unpack holds 4 copies of wrapper files",
        "docs/evidence/deep-study-carrier-facts-2026-08.md §IFC; unpack-census-latest.json wrapper_ifc_count=15 unpacked_ifc_count=4",
        "VERIFIED_INTERNAL",
        True,
        "15 уникальных IFC (IFC2X3). 4 IFC в unpack — копии, не новый объём.",
    ),
    _row(
        "A-05",
        "Версия схемы IFC канала",
        str(PUBLIC_DEEP_STUDY["ifc_schema"]),
        "docs/evidence/deep-study-carrier-facts-latest.json ifc_schema; unpack-census ifc_schema",
        "VERIFIED_INTERNAL",
        True,
        "На канале только IFC2X3. Учебный IFC4 помечать «учебный».",
    ),
    _row(
        "A-06",
        "IFC выше SPF-капа 256 МиБ",
        str(PUBLIC_DEEP_STUDY["ifc_over_spf_cap_count"]),
        "docs/evidence/unpack-census-latest.json ifc_over_spf_cap_count; deep-study pack C AR",
        "VERIFIED_INTERNAL",
        True,
        "Один IFC выше 256 МиБ SPF: инвентарь, не подъём капа.",
    ),
    _row(
        "A-07",
        "Объём комплекта в байтах/ГиБ",
        "NO_DATA in git; tracker «43 ГБ» is the assigned task title, not this measurement",
        "docs/evidence/unpack-census-2026-08.md claim_boundary; DATA_STATEMENT_2026_08.md §2",
        "NO_DATA",
        False,
        "несжатый объём в git не публикуем",
    ),
    _row(
        "A-08",
        "Пакет обработан (processed)",
        "false",
        "docs/evidence/unpack-census-latest.json processed; domain/finding_volume.py is_pack_processed",
        "VERIFIED_INTERNAL",
        True,
        "Пакет не обработан. Инвентарь носителей, не акт прогона.",
    ),
    _row(
        "A-09",
        "Публикуемое число находок на канале",
        "0",
        "backend/src/aerobim/domain/finding_volume.py publishable_finding_count; SIG01_CHANNEL_TRIAGE_2026_08.md",
        "VERIFIED_INTERNAL",
        True,
        "Публикуемых находок на канале: 0. Фраза: объём находок получен.",
    ),
    _row(
        "A-10",
        "Сырой total / классы находок канала (штуки)",
        "NO_DATA in git (OA-9; totals stay .local)",
        "docs/quality/FINDING_VOLUME_CLAIM_BOUNDARY_2026_08.md; SIG01_CHANNEL_TRIAGE_2026_08.md Channel totals stay .local",
        "NO_DATA",
        False,
        "сырой total канала не в git",
    ),
    _row(
        "A-11",
        "Лицензированная фраза SIG-01",
        REPORT_PHRASE,
        "backend/src/aerobim/domain/finding_volume.py REPORT_PHRASE",
        "VERIFIED_INTERNAL",
        True,
        "Объём находок на канале получен. Это не список дефектов.",
    ),
    _row(
        "A-12",
        "Пример «геометрия» на канале как дефект заказчика",
        "NO_DATA; 837 IfcClash is open IFC-Bench duplex, not the channel",
        "docs/evidence/federated-clash-duplex-2026-08.json clash_count; closes_rt003=false",
        "SYNTHETIC",
        True,
        "837 пересечений — открытый duplex, не АР↔ИОС канала.",
    ),
    _row(
        "A-13",
        "Пример «атрибут» на носителе канала",
        "Wall FireRating filled class EI 45 (pack A); unsigned demo expected REI60; not SP fail",
        "docs/evidence/deep-study-carrier-facts-2026-08.md FireRating; IUA CH-09; FINDING_VOLUME_CLAIM_BOUNDARY",
        "VERIFIED_INTERNAL",
        True,
        "Наблюдаемый FireRating стен EI 45. Это не провал СП.",
    ),
    _row(
        "A-14",
        "Пример «состав комплекта»",
        "Native RVT/NWD/DWG/LIRA unread (fail-closed); 1 IFC over SPF cap",
        "docs/tz/NATIVE_AUTODESK_INGEST_BOUNDARY_2026.md; unpack-census parse_rvt_nwd_lira=false",
        "VERIFIED_INTERNAL",
        True,
        "RVT/NWD/DWG/LIRA — отказ. Читаем IFC и PDF/A.",
    ),
    _row(
        "A-15",
        "Пример шва модель↔ведомость↔ТЗ как published finding",
        "IfcSpace QTO NetFloorArea=0 on all packs; sheet-vs-IFC area not a published customer finding",
        "docs/evidence/deep-study-carrier-facts-2026-08.md NetFloorArea; space_area_from_geometry=not_implemented",
        "VERIFIED_INTERNAL",
        True,
        f"{_space_total()} IfcSpace; NetFloorArea в QTO = 0. Площадь по геометрии нет.",
    ),
    _row(
        "A-16",
        "Доля находок с нормой + этажом/осью + GUID (канал)",
        "NO_DATA (channel totals not in git; triad engine exists on fixtures)",
        "docs/quality/FINDING_VOLUME_CLAIM_BOUNDARY_2026_08.md OA-9; domain/remark_completeness.py; TZ_COMPLIANCE_MATRIX §3.4",
        "NO_DATA",
        False,
        "доля триады на канале в git отсутствует",
    ),
    _row(
        "A-17",
        "Стена FireRating заполнена (пакет A, покрытие)",
        "3538 of 62033 walls (5.7%), class EI 45 only",
        "docs/evidence/deep-study-carrier-facts-2026-08.md table IFC pack A",
        "VERIFIED_INTERNAL",
        False,
        "покрытие FireRating не на слайд как точность",
    ),
    _row(
        "A-18",
        "Оси IfcGrid по пакетам",
        "0 / 13 / 53 (A / B AR / C AR)",
        "docs/evidence/deep-study-carrier-facts-2026-08.md IfcGrid; domain/deep_study_facts.py",
        "VERIFIED_INTERNAL",
        True,
        "IfcGrid: 0 / 13 / 53. Нулевые оси только у EDM-экспорта.",
    ),
    _row(
        "A-19",
        "IfcReinforcingBar / воздуховоды-трубы-кабели в IFC канала",
        "0 / 0",
        "docs/evidence/deep-study-carrier-facts-2026-08.md IfcReinforcingBar; duct/pipe/cable",
        "VERIFIED_INTERNAL",
        True,
        "Арматура в IFC = 0. Сети в IFC = 0. Не заявлять проверку ИОС.",
    ),
    _row(
        "A-20",
        "NWD-федерации как носители",
        "3 present; native NWD fail-closed",
        "docs/evidence/deep-study-carrier-facts-2026-08.md NWD federations; NATIVE_AUTODESK_INGEST_BOUNDARY",
        "VERIFIED_INTERNAL",
        True,
        "Три NWD как носители. Нативно не читаем.",
    ),
    _row(
        "A-21",
        "Wall-clock прогона канала (пакет / полное / CPU/RAM / профиль)",
        "NO_DATA in git; tool-side elapsed measured locally; totals .local until OA-9",
        "docs/evidence/deep-study-carrier-facts-2026-08.md §Дополнения 31.08–03.09 Lab journal; TRACKER_EIGHT_TASKS",
        "NO_DATA",
        False,
        "время канала в git нет",
    ),
    _row(
        "A-22",
        "Репетиция IFC 26.08 (fixture IDS на локальной копии)",
        "14 IFC analysed under cap; 1 over cap inventory-only; detected_count=0; not ingested in git",
        "audit/evidence/customer-intake-gate.json owner_machine_engine_rehearsal; TZ_SEAM_COVERAGE_MAP_2026_08.md",
        "VERIFIED_INTERNAL",
        True,
        "14 IFC под капом, учебные IDS. detected_count=0. Не акт заказчика.",
    ),
    _row(
        "A-23",
        "SIG-01 rerun 31.08",
        "EXECUTED locally after ALL/GUID/Qto fixes; pack_volume_not_accuracy; totals not in git",
        "docs/evidence/deep-study-carrier-facts-2026-08.md SIG-01 channel rerun EXECUTED; SIG01_CHANNEL_TRIAGE",
        "VERIFIED_INTERNAL",
        True,
        "Локальный перегон SIG-01 был. Сырой total не публикуем.",
    ),
    _row(
        "A-24",
        "Повторы канала бит-в-бит",
        "NO_DATA for the NDA pack; DeterminismGate covers verdict on fixtures",
        "docs/architecture/ADR-001-verdict-ownership-2026.md; TZ v2 ТР-27; no channel hash in git",
        "NO_DATA",
        False,
        "бит-в-бит канала не доказан в git",
    ),
    _row(
        "A-25",
        "Акт/протокол прогона канала",
        "NO_DATA; M7 site act BLOCKED_CUSTOMER_DATA",
        "docs/partners/MIK_PILOT_COMPLIANCE_2026.md M7; customer-intake-gate.json nda_signed=false",
        "NO_DATA",
        False,
        "подписанного акта прогона нет",
    ),
    _row(
        "A-26",
        "Форматы обёртки (suffix/magic, не «прогнаны»)",
        "IFC 15, PDF 1208, DWG 551, DXF 67, RVT 27, Navis 21, .lir 20+21 tilde",
        "docs/evidence/unpack-census-latest.json wrapper_*_count",
        "VERIFIED_INTERNAL",
        False,
        "поформатный census не «пакет обработан»",
    ),
    _row(
        "A-27",
        "Отчёты слотов канала в git",
        "HTML/JSON/PDF/BCF stay .local-only (OA-9/OA-22); git does not host or send customer reports; processed remains false",
        "docs/quality/FINDING_VOLUME_CLAIM_BOUNDARY_2026_08.md OA-9",
        "VERIFIED_INTERNAL",
        True,
        "Отчёты слотов — только .local. Git не шлёт. Пакет не processed.",
    ),
    # --- B. TZ R1–R15 (task-page matrix) ---
    _row(
        "B-R1",
        "R1 2D drawings",
        "closed_by_code (PDF/OCR/overlay) on fixtures; customer PDFs inventoried, not drawing findings",
        "docs/techlab-alignment-2026.md §3 R1; TZ_COMPLIANCE_MATRIX §3.1; CHANNEL_LOCAL_MAX_PASS PDF HITL",
        "VERIFIED_INTERNAL",
        True,
        "Чертежи: учебный оверлей. Листы канала — очередь HITL, не CV.",
    ),
    _row(
        "B-R2",
        "R2 BIM models",
        "closed_by_code IFC+IDS; customer: 15 IFC2X3 inventory, processed=false",
        "docs/techlab-alignment-2026.md R2; deep-study-carrier-facts-2026-08.md",
        "VERIFIED_INTERNAL",
        True,
        "BIM: IFC+IDS в коде. Канал — инвентарь IFC2X3, не акт.",
    ),
    _row(
        "B-R3",
        "R3 TZ + calculations",
        "closed_by_code on fixtures; customer .lir unread (native_lir=not_implemented)",
        "docs/techlab-alignment-2026.md R3; CALCULATION_COMPARE_FOUR_CHECKS; unpack-census parse_rvt_nwd_lira",
        "VERIFIED_INTERNAL",
        True,
        "Сверка заявленных величин — да. Решатель ЛИРА — нет.",
    ),
    _row(
        "B-R4",
        "R4 Match docs + norms",
        "artifact: public IDS (50 files / 847 specs); customer_approved IDS=false",
        "docs/techlab-alignment-2026.md R4; demo_day_speech_lock PUBLIC_IDS_*; deep-study customer_approved_ids",
        "VERIFIED_INTERNAL",
        True,
        f"Публичные IDS: {PUBLIC_IDS_FILES} файлов, {PUBLIC_IDS_SPECS} spec. Подписи заказчика канала нет.",
    ),
    _row(
        "B-R5",
        "R5 Collisions / clashes",
        "code+planted/open rehearsal; customer MEP IFC entities=0; 837≠channel",
        "docs/techlab-alignment-2026.md R5; federated-clash-duplex-2026-08.json; deep-study mep_duct_pipe_cable_count",
        "SYNTHETIC",
        True,
        "Clash движка — на фикстуре и открытом duplex. Не их АР↔ИОС.",
    ),
    _row(
        "B-R6",
        "R6 Calculation / dimension / area errors",
        "code on fixtures; channel NetFloorArea=0; geometry area not_implemented",
        "docs/techlab-alignment-2026.md R6; system_capabilities space_area_from_geometry",
        "VERIFIED_INTERNAL",
        True,
        "Площади канала: QTO пуст. Геометрию IfcSpace не считаем.",
    ),
    _row(
        "B-R7",
        "R7 Logic / missing elements",
        "closed_by_code IDS exists/bounds; channel unsigned ALL is coverage_map, not defects",
        "docs/techlab-alignment-2026.md R7; FINDING_VOLUME_CLAIM_BOUNDARY target_ref=ALL",
        "VERIFIED_INTERNAL",
        True,
        "IDS exists работает. Unsigned ALL на канале — покрытие, не дефект.",
    ),
    _row(
        "B-R8",
        "R8 Highlight problem zones",
        "closed_by_code+artifact on fixture overlay; not customer sheets",
        "docs/techlab-alignment-2026.md R8; docs/evidence/drawing-overlay-smoke-2026-08/README.md",
        "SYNTHETIC",
        True,
        "Подсветка зоны — учебный оверлей, не лист заказчика.",
    ),
    _row(
        "B-R9",
        "R9 Prioritize remarks",
        "closed_by_code AEROBIM_PRIORITY_PROFILE=customer; not measured on customer queue",
        "docs/techlab-alignment-2026.md R9; domain/review_priority.py",
        "VERIFIED_INTERNAL",
        False,
        "профиль приоритета в коде; замер очереди заказчика нет",
    ),
    _row(
        "B-R10",
        "R10 Designer comments",
        "closed_by_code RU/EN templates + HITL edit + BCF ZIP; no customer HITL log in git",
        "docs/techlab-alignment-2026.md R10; TemplateRemarkGenerator; ADR-001",
        "VERIFIED_INTERNAL",
        True,
        "Черновик замечания: норма, этаж/ось, GUID. Пишет не LLM.",
    ),
    _row(
        "B-R11",
        "R11 Faster review",
        "target_metric; fixture SLA only",
        "docs/techlab-alignment-2026.md R11; audit/evidence/sla-fixture-honesty-2026-07-17.json",
        "SYNTHETIC",
        False,
        "ускорение ревью на комплекте заказчика не замерено",
    ),
    _row(
        "B-R12",
        "R12 Expert remains accountable",
        "closed_by_artifact ADR-001 DeterminismGate; independent_human_raters=0",
        "docs/architecture/ADR-001-verdict-ownership-2026.md; accuracy-answer-2026-09.json independent_human_raters",
        "VERIFIED_INTERNAL",
        True,
        "Вердикт пишет движок. Эксперт подтверждает находки. LLM не rater.",
    ),
    _row(
        "B-R13",
        "R13 MVP + visualization + reports",
        "closed_by_code API/HTML/JSON/BCF + review shell (eight IA screens partial)",
        "docs/techlab-alignment-2026.md R13; UI_EXPERT_WORKPLACE_TRIAGE_2026_09.md",
        "VERIFIED_INTERNAL",
        True,
        "Отчёт JSON/HTML/BCF есть. Оболочка — review shell, не сданное РМ.",
    ),
    _row(
        "B-R14",
        "R14 Typical error catalog",
        "artifact scaffold ≥20; customer_confirmed_patterns=0",
        "docs/techlab-alignment-2026.md R14; samples/benchmarks/typical-errors-catalog.json; accuracy-answer typical_error_class_coverage",
        "SYNTHETIC",
        True,
        "Каталог ≥20 на шаблоне. Подтверждённых заказчиком: 0.",
    ),
    _row(
        "B-R15",
        "R15 ≤30 min package SLA",
        "target_metric; fixture 576.87 ms; customer pack NO_DATA; 25.08 answers do not confirm the criterion",
        "docs/techlab-alignment-2026.md R15; sla-fixture-honesty-2026-07-17.json; TZ_COMPLIANCE_MATRIX §6",
        "SYNTHETIC",
        True,
        "30 минут — цель ТЗ. На комплекте заказчика не замерено.",
    ),
    _row(
        "B-IDS-MOEXP",
        "IDS Мособлгосэкспертизы (не профиль назначающей стороны)",
        f"{MOEXP_IDS_FILES} files / {MOEXP_IDS_SPECS} specifications",
        "backend/src/aerobim/domain/demo_day_speech_lock.py MOEXP_IDS_*; docs/evidence (norm-pack-moexp-coverage)",
        "VERIFIED_INTERNAL",
        True,
        "389 спецификаций — 24 файла МОГЭ, не все 50 публичных IDS.",
    ),
    # --- C. Prototype / CI / accuracy ---
    _row(
        "C-01",
        "CI backend tests passed / collected / failed / skipped",
        _ci_backend_line(),
        "docs/evidence/runtime-baseline-latest.json backend.*; attestation.attested_by=ci",
        "VERIFIED_INTERNAL",
        True,
        _ci_backend_slide(),
    ),
    _row(
        "C-02",
        "CI frontend tests passed / failed",
        _ci_frontend_line(),
        "docs/evidence/runtime-baseline-latest.json frontend",
        "VERIFIED_INTERNAL",
        True,
        _ci_frontend_slide(),
    ),
    _row(
        "C-03",
        "Quality gates ruff/mypy/pytest/vitest/build",
        "PASS / PASS / PASS / PASS / PASS",
        "docs/evidence/runtime-baseline-latest.json quality_gates",
        "VERIFIED_INTERNAL",
        True,
        "Пять ворот качества: PASS. Числа файлов mypy в пине нет.",
    ),
    _row(
        "C-04",
        "attested_by / publishable / corpus_kind",
        "ci / true / fixture",
        "docs/evidence/runtime-baseline-latest.json attestation.attested_by, publishable, corpus_kind",
        "VERIFIED_INTERNAL",
        True,
        "Пин attested_by=ci. Локальный pytest на слайд не ставить.",
    ),
    _row(
        "C-05",
        "Architecture inventory",
        "48 protocols / 76 adapters / 63 DI tokens",
        "docs/evidence/runtime-baseline-latest.json architecture_inventory",
        "VERIFIED_INTERNAL",
        False,
        "инвентарь архитектуры не критерий жюри",
    ),
    _row(
        "C-06",
        "Fixture extraction macro_f1",
        "0.86 (fixture; not product accuracy)",
        "docs/evidence/runtime-baseline-latest.json metrics.extraction_macro_f1; accuracy-answer-2026-09.json claim_boundary",
        "SYNTHETIC",
        True,
        "F1 0,86 — учебный корпус извлечения, не точность продукта.",
    ),
    _row(
        "C-07",
        "Fixture AABB clash P/R",
        "precision=1.0 recall=1.0 n=6; Wilson 95% lower ≈0.61; publishable=false",
        "docs/evidence/accuracy-answer-2026-09.json rows fixture_aabb_clash; clash-measurement-slice-2026-08",
        "SYNTHETIC",
        False,
        "n=6 не exhibit; нижняя Уилсона ≈0,61",
    ),
    _row(
        "C-08",
        "Defect-injection recall (mini-IFC)",
        "1/8=0.125; Wilson 95% [0.022; 0.471]; lower <0.50; publishable=false",
        "docs/evidence/accuracy-answer-2026-09.json defect_injection_recall; DEFECT_INJECTION_RECALL_RUN_2026_09.md",
        "SYNTHETIC",
        False,
        "нижняя Уилсона 0,022 < 0,50 — не на слайд",
    ),
    _row(
        "C-09",
        "Defect-injection recall (channel IFC mutations)",
        "0/6 killed; Wilson lower 0.000; synthetic_only",
        "docs/evidence/DEFECT_INJECTION_RECALL_RUN_2026_09.md; TIER0_INDEX row E2",
        "SYNTHETIC",
        False,
        "0/6 на канальном IFC — синтетика, не recall заказчика",
    ),
    _row(
        "C-10",
        "AECV object counting",
        f"macro_extended={AECV_VALUE}; n_field_scores_extended=585; is_f1=false; publishable=false",
        "docs/evidence/accuracy-answer-2026-09.json aecv_object_counting; aecv-bench-eval-latest.json",
        "SYNTHETIC",
        True,
        "0,4325 — macro_extended открытого бенча, не F1.",
    ),
    _row(
        "C-11",
        "Dual-rater simulation",
        "κ=0.705 n=28; independent_human_raters=0; labelled=simulation",
        "docs/evidence/accuracy-answer-2026-09.json dual_rater_simulation; rt001-dual-rater-simulation-2026-09.json",
        "SYNTHETIC",
        True,
        "κ≈0,70 — симуляция протокола. Живых разметчиков: 0.",
    ),
    _row(
        "C-12",
        "Experiment B KR coverage",
        f"{EXPERIMENT_B_KR_DETECTED}/{EXPERIMENT_B_KR_N} ≈16.7%; coverage_map_only; not product recall",
        "docs/evidence/weekly-eng-status-latest.json coverage_map; EXPERIMENT_B_TYPICAL_REMARKS_KR_COVERAGE_2026_08.md",
        "SYNTHETIC",
        True,
        "КР ≈16,7% (4/24) — карта покрытия, не recall.",
    ),
    _row(
        "C-13",
        "Pilot n (interval width vs power)",
        f"recommended_n={RECOMMENDED_N}; power_design n=62; interim precision 0.60",
        "docs/evidence/weekly-eng-status-latest.json adjudication_corpus_plan",
        "VERIFIED_INTERNAL",
        True,
        "Размер выборки пилота n=111. 62 — только мощность.",
    ),
    _row(
        "C-14",
        "PrecisionClaim.publishable",
        "false (corpus_kind≠customer; <2 human adjudicators)",
        "docs/evidence/accuracy-answer-2026-09.json precision_claim_publishable; customer-intake-gate.json",
        "VERIFIED_INTERNAL",
        True,
        "Точность продукта не публикуется. Гейт PrecisionClaim закрыт.",
    ),
    _row(
        "C-15",
        "TRL self-assess / TRL 5 claimed",
        f"{TRL_SELF_ASSESS} / {trl_5_claimed()}",
        "docs/quality/TRL_GOST_R_58048_SELF_ASSESS_2026.md; domain/mik_commission_scoring.py",
        "VERIFIED_INTERNAL",
        True,
        "Самооценка ГОСТ Р 58048 — TRL 4. Уровень 5 не заявляется.",
    ),
    _row(
        "C-16",
        "Non-claims in pilot-claim-boundary",
        f"{NON_CLAIM_COUNT} numbered items (§Non-claims 1–{NON_CLAIM_COUNT})",
        "docs/pilot-claim-boundary-2026.md §Non-claims; CLAIMS_LOCK_2026_07_17.md Pass 14",
        "VERIFIED_INTERNAL",
        False,
        "полный список non-claims — в границе заявлений, не на обложку",
    ),
    _row(
        "C-17",
        "Open duplex IfcClash count",
        str(DUPLEX_CLASH_COUNT),
        "docs/evidence/federated-clash-duplex-2026-08.json runs[0].clash_count; elapsed_ms=5959.65",
        "SYNTHETIC",
        True,
        "837 — открытый duplex IFC-Bench, 6 с. Не канал заказчика.",
    ),
    # --- D. Integration ---
    _row(
        "D-01",
        "Команда офлайн-развёртывания",
        "python -m aerobim.tools.offline_bundle closed-contour --smoke (from backend/)",
        "docs/offline-deployment-2026.md; audit/evidence/offline-closed-contour-docker-2026-08.json",
        "VERIFIED_INTERNAL",
        True,
        "Офлайн: Docker load + --network none. Bare-metal — вне скоупа.",
    ),
    _row(
        "D-02",
        "Время до первого прогона (минуты)",
        "NO_DATA; smoke PASS 2026-08-08, wall-clock minutes not recorded",
        "docs/evidence/offline-closed-contour-docker-2026-08.md; offline-closed-contour-docker-2026-08.json",
        "NO_DATA",
        False,
        "минут до первого прогона в git нет",
    ),
    _row(
        "D-03",
        "Образ офлайн-бандла",
        "tar 864927744 bytes; tag aerobim-backend:offline-bundle; date 2026-08-08",
        "docs/evidence/offline-closed-contour-docker-2026-08.md table Image",
        "VERIFIED_INTERNAL",
        False,
        "размер tar не SLA",
    ),
    _row(
        "D-04",
        "Ядра CPU / требуемый RAM стенда",
        "NO_DATA (required cores); RAM planning multiplier 10 is literature not appointing-party RSS",
        "docs/quality/IFC_ANALYZE_VS_INGEST_CAP_2026_08.md; KT3_JURY_FAQ RSS на файле заказчика не замерен",
        "NO_DATA",
        False,
        "RSS на файле заказчика не замерен",
    ),
    _row(
        "D-05",
        "GPU",
        "not required for deterministic analyze; optional YOLO/VLM advisory",
        "docs/architecture/TARGET_HYBRID_ARCHITECTURE_TZ_2026.md GPU optional; sla-benchmark-protocol-2026.md",
        "VERIFIED_INTERNAL",
        True,
        "GPU для детерминированного прогона не нужен.",
    ),
    _row(
        "D-06",
        "Интернет на стенде",
        "not required for Docker air-gap smoke (--network none); LLM/VLM default deny",
        "docs/offline-deployment-2026.md smoke path; BUILD_WITHOUT_EXTERNAL_MODELS_2026.md",
        "VERIFIED_INTERNAL",
        True,
        "Закрытый контур: Docker без сети. Облачный LLM по умолчанию выключен.",
    ),
    _row(
        "D-07",
        "Вход / выход",
        "in: IFC, PDF, Office OOXML; native RVT/NWD/DWG/.lir fail-closed. out: JSON, HTML, PDF, BCF ZIP 2.1/3.0",
        "README.md Limits; TZ_COMPLIANCE_MATRIX §4; bcf-structural-handoff-2026-07-25.json",
        "VERIFIED_INTERNAL",
        True,
        "Вход: IFC+PDF/A+Office. Выход: JSON, HTML, BCF ZIP.",
    ),
    _row(
        "D-08",
        "Лимиты объёмов",
        "SPF 256 MiB; model ingest/analyze 1.5 GB RocksDB on customer_pilot/production; Office 500 MB",
        "README.md AEROBIM_MAX_IFC_BYTES / MAX_MODEL_BYTES / MAX_OFFICE_BYTES; IFC_ANALYZE_VS_INGEST_CAP",
        "VERIFIED_INTERNAL",
        True,
        "Капы: 256 МиБ SPF, 1,5 ГБ диск, 500 МБ Office.",
    ),
    _row(
        "D-09",
        "Ключевые эндпоинты",
        "POST /v1/analyze/project-package, POST /v1/uploads, GET /v1/system/capabilities, export HTML/PDF/BCF, review-events, review-kpi",
        "README.md API table; presentation/http/routes",
        "VERIFIED_INTERNAL",
        False,
        "карта API не слайд эффекта",
    ),
    _row(
        "D-10",
        "BCF 2.1 / 3.0 ZIP",
        "T1 structural OK (XSD passed, 2 topics each); cde_import=NOT_VERIFIED",
        "audit/evidence/bcf-structural-handoff-2026-07-25.json; docs/architecture/BCF_EVIDENCE_LADDER_T0_T4_2026_07.md",
        "VERIFIED_INTERNAL",
        True,
        "BCF ZIP 2.1 и 3.0 — структура T1. Импорт в СОД не доказан.",
    ),
    _row(
        "D-11",
        "BCF API 3.0 push",
        "foundation endpoint POST .../export/bcf-api/push; T2 still NOT_VERIFIED",
        "docs/pilot-claim-boundary-2026.md BCF API 3.0; tests/test_wave2_cde_integration.py; CDE_IMPORT",
        "NOT_VERIFIED",
        True,
        "Push BCF API есть как фундамент. Журнала импорта в СОД нет.",
    ),
    _row(
        "D-12",
        "SSO / OIDC BFF",
        f"default GET /v1/auth/bff = {AUTH_BFF_DEFAULT}; JWT validator exists; full SSO post-pilot",
        "docs/pilot-claim-boundary-2026.md Full OIDC; domain/demo_day_speech_lock.py AUTH_BFF_DEFAULT",
        "VERIFIED_INTERNAL",
        True,
        "GET /v1/auth/bff по умолчанию 501. SSO на их IdP не живой.",
    ),
    _row(
        "D-13",
        "ACL: чужой отчёт",
        "deny → 404 (not 403)",
        "docs/pilot-claim-boundary-2026.md Cross-tenant ACL; tests/test_mutation_kills_http_context.py test_cross_tenant_job_access_is_404; test_oidc_bff_hitl_rbac.py",
        "VERIFIED_INTERNAL",
        True,
        "Чужой объект — 404, не 403. Перечень не светим.",
    ),
    _row(
        "D-14",
        "SSRF на исходящих URL",
        "JWKS / bSI / OpenCDE URL guard; tests block RFC1918 and loopback",
        "docs/pilot-claim-boundary-2026.md Outbound SSRF; tests/test_outbound_guard_invariant.py; test_defensive_engineering_pass_2026_08.py; test_oidc_bff_phase3.py",
        "VERIFIED_INTERNAL",
        True,
        "Исходящие URL режутся. Приватные адреса не ходят.",
    ),
    _row(
        "D-15",
        "Сервисный токен не подписывает вердикт HITL",
        "is_service_token cannot append accepted/rejected; even when role gate off",
        "domain/object_acl.py principal_may_append_hitl_event; tests/test_rt_wave3_remediation_2026_08.py HitlRbacTests",
        "VERIFIED_INTERNAL",
        True,
        "Общий bearer не подписывает accept/reject. Нужен эксперт.",
    ),
    _row(
        "D-16",
        "cde_import machine status",
        CDE_IMPORT,
        "audit/evidence/bcf-structural-handoff-2026-07-25.json cde_import.status; BCF_EVIDENCE_LADDER T2",
        "NOT_VERIFIED",
        True,
        "Статус импорта в СОД: NOT_VERIFIED.",
    ),
    # --- E. Effect ---
    _row(
        "E-01",
        "Допущение E1 (дословно)",
        E1_TEXT,
        "docs/partners/CUSTOMER_CYCLE_ECONOMICS_ASSUMPTIONS_2026_09.md table E1",
        "NEEDS_CUSTOMER",
        True,
        "E1: лишний круг на типовой секции — их факт, не наш замер.",
    ),
    _row(
        "E-02",
        "Допущение E2 (дословно)",
        E2_TEXT,
        "docs/partners/CUSTOMER_CYCLE_ECONOMICS_ASSUMPTIONS_2026_09.md table E2",
        "NEEDS_CUSTOMER",
        True,
        "E2: длительность круга задаёт заказчик. Не спорить «у нас 30 мин».",
    ),
    _row(
        "E-03",
        "Допущение E3 (дословно)",
        E3_TEXT,
        "docs/partners/CUSTOMER_CYCLE_ECONOMICS_ASSUMPTIONS_2026_09.md table E3",
        "NEEDS_CUSTOMER",
        False,
        "рубли дня комплекта не публикуем",
    ),
    _row(
        "E-04",
        "Допущение E4 (дословно)",
        E4_TEXT,
        "docs/partners/CUSTOMER_CYCLE_ECONOMICS_ASSUMPTIONS_2026_09.md table E4",
        "NEEDS_CUSTOMER",
        True,
        "E4: не больше одного круга и только на эталоне с парой ревизий.",
    ),
    _row(
        "E-05",
        "Допущение E5 (дословно)",
        E5_TEXT,
        "docs/partners/CUSTOMER_CYCLE_ECONOMICS_ASSUMPTIONS_2026_09.md table E5",
        "NEEDS_CUSTOMER",
        True,
        "E5: эффект на типовой секции, не разовый дефект.",
    ),
    _row(
        "E-06",
        "Что система считает сама (эффект)",
        "HITL review-kpi: opened/triaged/accepted/rejected/acceptance_rate/avg_latency_ms — not CDE cycle days, not pre-expertise share, not re-entry",
        "backend/src/aerobim/application/services/review_kpi.py summarize_review_events; GET /v1/reports/{id}/review-kpi; README.md",
        "VERIFIED_INTERNAL",
        True,
        "Экран «Эффект» — журнал HITL. Это не дни цикла СОД.",
    ),
    _row(
        "E-07",
        "Число 1 от заказчика канала: календарные дни круга согласования РД",
        "NO_DATA; who: technological-customer director / PMO of the section",
        "docs/partners/CUSTOMER_CYCLE_ECONOMICS_ASSUMPTIONS_2026_09.md E2; DEMO_DAY_SPEECH_LOCK three numbers",
        "NEEDS_CUSTOMER",
        False,
        "запросить письмом",
    ),
    _row(
        "E-08",
        "Число 2 от заказчика канала: часы эксперта «до» на эталонном комплекте",
        "NO_DATA; t_manual_s is null; A1–A8 empty; who: chief expert / project office",
        "docs/partners/BEFORE_AFTER_MEASUREMENT_PROTOCOL_2026_09.md; ECONOMIC_MODEL_LABELED_ASSUMPTIONS_2026_08.md",
        "NEEDS_CUSTOMER",
        False,
        "запросить письмом",
    ),
    _row(
        "E-09",
        "Число 3 от заказчика канала: сколько лишних кругов они считают нормой на типовой секции",
        "NO_DATA; who: information-modelling lead (typification) + tech-customer",
        "docs/partners/CUSTOMER_CYCLE_ECONOMICS_ASSUMPTIONS_2026_09.md E1 E5",
        "NEEDS_CUSTOMER",
        False,
        "запросить письмом",
    ),
    _row(
        "E-10",
        "Baseline «до» в репозитории",
        "NO_DATA partner hours; lab t_manual_s=null; fixture SLA 0.0096 min is not baseline-before",
        "docs/evidence/deep-study-carrier-facts-2026-08.md t_manual_s is null; sla-fixture-honesty-2026-07-17.json claim_level=fixture_only",
        "NO_DATA",
        True,
        "Замера «до» на часах партнёра в git нет.",
    ),
    # --- F. Docs / handoff ---
    _row(
        "F-01",
        "Лицензия собственного кода",
        "MIT; third-party under own licenses (IfcOpenShell LGPL; PyMuPDF optional AGPL extra not in runtime lock)",
        "LICENSE; docs/license-policy-2026.md; audit/dependency_license_inventory.json",
        "VERIFIED_INTERNAL",
        True,
        "MIT — свой код. Сторонние компоненты — свои лицензии.",
    ),
    _row(
        "F-02",
        "ADR",
        "ADR-001 verdict; ADR-002 open-core; ADR-003 DWG/ODA; ADR-004 prize IP; ADR-005 customer data",
        "docs/architecture/ADR-001-verdict-ownership-2026.md … ADR-005-customer-data-handling-2026.md",
        "VERIFIED_INTERNAL",
        True,
        "Пять ADR. Вердикт — ADR-001. Данные канала — ADR-005.",
    ),
    _row(
        "F-03",
        "Протокол приёмочных испытаний (подписанный)",
        "NO_DATA; protocol drafts exist, site act does not",
        "docs/partners/PROTOCOL_QUALITY_ACCEPTANCE_TASK07_2026_08.md claim_level=protocol_only; MIK_PILOT_COMPLIANCE M6/M7",
        "NO_DATA",
        False,
        "подписанного протокола испытаний нет",
    ),
    _row(
        "F-04",
        "Методика замера",
        "QUALITY_MEASUREMENT_PROTOCOL_2026_08.md + Wilson planner n=111; protocol_only",
        "docs/pilot/QUALITY_MEASUREMENT_PROTOCOL_2026_08.md; weekly-eng-status-latest.json recommended_n",
        "VERIFIED_INTERNAL",
        True,
        "Методика замера есть. Замера на их корпусе нет.",
    ),
    _row(
        "F-05",
        "Инструкция офлайн-сборки",
        "docs/offline-deployment-2026.md + INSTALL_OFFLINE.md in bundle",
        "docs/offline-deployment-2026.md",
        "VERIFIED_INTERNAL",
        True,
        "Офлайн-сборка: Docker-бандл. Без Docker не обещаем.",
    ),
    _row(
        "F-06",
        "Передача прав / IP приза",
        "ADR-004 fork path; LICENSE unchanged; п.6.3 prize IP not closed",
        "docs/architecture/ADR-004-prize-ip-mit-fork-2026.md; docs/quality/KT3_DELIVERY_BOM_2026_08.md",
        "NOT_VERIFIED",
        False,
        "п.6.3 передачи прав не закрыт",
    ),
    _row(
        "F-07",
        "Что показать жюри без NDA",
        "git fixtures + run_kt3_jury; public IDS; CI pin; speech lock; not NDA tree, not .local totals, not JK names",
        "docs/demo/KT3_OPERATOR_RUNBOOK_2026_08_25.md; docs/evidence/DATA_STATEMENT_2026_08.md; JURY_SURFACES",
        "VERIFIED_INTERNAL",
        True,
        "Жюри: учебный CLI из git. Файлов заказчика в репозитории нет.",
    ),
    _row(
        "F-08",
        "customer_go / Checkpoint",
        "customer_go=false; CHECKPOINT=GO (regulatory_measurement_mvp)",
        "docs/pilot-claim-boundary-2026.md; domain/checkpoint.py; AGENTS.md",
        "VERIFIED_INTERNAL",
        True,
        "Checkpoint GO — измерительный MVP. customer_go по-прежнему false.",
    ),
)

CONTRADICTIONS: Final[tuple[dict[str, str], ...]] = (
    {
        "id": "X-01",
        "where": "CLAIMS_LOCK_2026_07_17.md header vs live checkpoint",
        "drift": "Header still says Checkpoint verdict NO_GO; live product checkpoint is GO since 2026-09-04. Treat the July file as HISTORICAL_PIN plus Pass 14 wording, not as current SSOT.",
    },
    {
        "id": "X-02",
        "where": "weekly-eng-status-latest.json checkpoint vs TIER0",
        "drift": "CLOSED 2026-09-15: weekly pin regenerated via export_weekly_eng_status; checkpoint GO; runtime_baseline SHA is the attested pin 139896709507. The 2026-08-17 NO_GO snapshot is historical. Do not mix the August file with HEAD.",
    },
    {
        "id": "X-03",
        "where": "techlab-alignment R1–R15 checkmarks vs this pack",
        "drift": "Alignment uses ✅ on several rows that this audit marks fixture-only or target_metric (R11/R15 SLA, R5 clash, R14 catalog). Prefer this table’s weaker status.",
    },
    {
        "id": "X-04",
        "where": "Desktop deck 13.09 vs git",
        "drift": "Deck (outside git) printed УГТ-5, 837 as partner AR↔MEP, 0.43 as F1, n≥62, KR 17%, 389-in-50, SSO/BCF-ready. Licensed copy is submission/03-presentation/demo_day_slides.md. PPTX itself is still the owner’s file.",
    },
    {
        "id": "X-05",
        "where": "AUDITOR_BRIEF freeze 2026-09-04 vs HEAD docs",
        "drift": "Standalone auditor brief is dated 04–08.09 and must not be read as HEAD evidence counts. CI integers live only in runtime-baseline-latest.json.",
    },
    {
        "id": "X-06",
        "where": "System A vs System B weights",
        "drift": "Selection 40/20/15/15/10 vs finalist 30/20/20/20/10. Desktop scan 14.09 matches both tables; PDF still not in git. Do not cite as attested_by=ci.",
    },
    {
        "id": "X-07",
        "where": "Intake-gate status vs channel received",
        "drift": "customer-intake-gate.json claim_level=not_ready and gates.* = false, but share_received_at=2026-08-25. Do not say «нет данных». Do not say gates are green.",
    },
    {
        "id": "X-08",
        "where": "CLAIMS_LOCK vs live GO formula",
        "drift": "Allowed-wording bullet still uses the pre-measurement formula (RF PD+expertise). Residual RT volumes stay OPEN; the product flag is nevertheless GO (measurement MVP). Speak both sentences, never one.",
    },
)

DANGEROUS_QUESTIONS: Final[tuple[dict[str, str], ...]] = (
    {
        "id": "Q-01",
        "q": "Вы прогнали наш комплект. Сколько дефектов?",
        "a": "Карта выгрузки снята. Это не акт дефектов объекта. Публикуемых находок как дефектов заказчика: 0. Фраза: объём находок на канале получен.",
    },
    {
        "id": "Q-02",
        "q": "Какая точность? Вы же писали >90% / 0,43 F1?",
        "a": "Точность продукта не публикуется. 0,86 F1 — фикстура извлечения. 0,4325 — macro_extended открытого бенча, не F1. n пилота 111.",
    },
    {
        "id": "Q-03",
        "q": "837 коллизий АР↔ИОС на наших файлах?",
        "a": "Нет. 837 — открытый IFC-Bench duplex. В переданных IFC воздуховоды/трубы/кабели = 0.",
    },
    {
        "id": "Q-04",
        "q": "Почему УГТ-5, если комплект уже у вас?",
        "a": "Самооценка ГОСТ Р 58048 — TRL 4. Уровень 5 требует контура партнёра в измерении и двух человеческих разметчиков. Их нет.",
    },
    {
        "id": "Q-05",
        "q": "Укладываетесь в 30 минут на наш пакет?",
        "a": "На комплекте заказчика время в git отсутствует. Фикстура 577 мс не SLA. Критерий 25.08 не подтверждён.",
    },
    {
        "id": "Q-06",
        "q": "Замечания уже падают в наш 10D / СОД?",
        "a": "BCF ZIP структурно T1. Импорт в СОД NOT_VERIFIED. GET /v1/auth/bff = 501.",
    },
    {
        "id": "Q-07",
        "q": "Вы читаете RVT и NWD? У нас три федерации.",
        "a": "Нативно нет, fail-closed. Три NWD есть как носители. Обмен — IFC + PDF/A.",
    },
    {
        "id": "Q-08",
        "q": "Где недобор арматуры относительно ЛИРЫ?",
        "a": "IfcReinforcingBar = 0. Бинарный .lir не разбираем. Сверка заявленных полей — не пересчёт.",
    },
    {
        "id": "Q-09",
        "q": "Сколько денег сэкономим на круге согласования?",
        "a": "Ни один множитель E1–E5 не измерен. Нужны их дни круга, часы «до» и сколько кругов они считают нормой.",
    },
    {
        "id": "Q-10",
        "q": "Кто отвечает, если машина пропустит дефект?",
        "a": "Эксперт. summary.passed пишет только детерминированный движок (ADR-001). LLM не rater и не вердикт.",
    },
)

CUSTOMER_LETTER: Final = (
    "Коллеги, чтобы на демо-дне поставить блок эффекта на ваши цифры, "
    "а не на чужую модель, нужны три числа вашего контура.\n"
    "1) Сколько рабочих дней у вас занимает один круг согласования рабочей "
    "документации по типовой секции.\n"
    "2) Сколько часов эксперт тратит на тот же эталонный комплект без нашей "
    "системы (прогон «до»).\n"
    "3) Сколько лишних кругов на типовой секции вы сами считаете нормальной "
    "практикой сегодня.\n"
    "Цифры можно дать интервалом и без рублей. Их знают директор по "
    "техзаказчику, проектный офис и руководитель информационного моделирования.\n"
    "Отдельно просим письменно подтвердить режим данных по уже переданному "
    "каналу 25 августа и порог приёмки пилота: промежуточная точность 0,60 "
    "по согласованной методике либо ваш иной порог. Молчание не считаем "
    "согласием с цифрой из брифа.\n"
    "Готовы показать учебный прогон и карту пригодности выгрузки без публикации "
    "имён объектов и без записи в вашу СОД."
)

DEMO_20S: Final[tuple[str, ...]] = (
    "0–3 с: терминал, каталог backend/, команда python -m aerobim.tools.run_kt3_jury.",
    "3–8 с: дождаться artifacts/kt3-jury/latest.json; не открывать NDA-дерево и не seed-fixture.",
    "8–14 с: открыть report.html из того же прогона; строка IDS-Wall Fire Rating Multi, GUID 1XYVUKGoDDbREfVxRKsHkl (REI60 vs REI30).",
    "14–18 с: не кликать первую REQ-AREA-* (ifc_guid пустой). Показать, что summary.passed=false на учебной фикстуре — сценарий.",
    "18–20 с: указать findings.bcfzip рядом; сказать: файл BCF, не реестр СОД. stderr MEP-CLASH-001 не есть падение демо.",
)


def fact_by_id() -> dict[str, dict[str, str | bool]]:
    return {str(row["id"]): row for row in FACT_ROWS}


def demo_day_auditor_snapshot() -> dict[str, Any]:
    pin = PUBLIC_DEEP_STUDY
    census = PUBLIC_UNPACK_CENSUS
    return {
        "artifact_type": "demo_day_auditor_pack",
        "claim_level": CLAIM_LEVEL,
        "checkpoint": CHECKPOINT,
        "closes_rt001": False,
        "closes_rt002": False,
        "closes_rt003": False,
        "customer_go": False,
        "claim_boundary": CLAIM_BOUNDARY,
        "detected_count": 0,
        "is_accuracy": False,
        "is_pack_processed": False,
        "publishable_finding_count": 0,
        "precision_claim_publishable": False,
        "trl_self_assess": TRL_SELF_ASSESS,
        "trl_5_claimed": trl_5_claimed(),
        "ifcspace_total": _space_total(),
        "netfloorarea_count": int(pin["netfloorarea_count"]),
        "unique_ifc_count": int(pin["unique_ifc_count"]),
        "processed": bool(census["processed"]),
        "recommended_n": RECOMMENDED_N,
        "non_claim_count": NON_CLAIM_COUNT,
        "cde_import": CDE_IMPORT,
        "auth_bff_default": AUTH_BFF_DEFAULT,
        "space_area_from_geometry": SPACE_AREA_FROM_GEOMETRY,
        "fact_count": len(FACT_ROWS),
        "contradiction_count": len(CONTRADICTIONS),
        "dangerous_question_count": len(DANGEROUS_QUESTIONS),
        "slide_yes_count": sum(1 for row in FACT_ROWS if row["slide"] == "да"),
        "status_counts": {
            status: sum(1 for row in FACT_ROWS if row["status"] == status) for status in STATUSES
        },
        "e1": E1_TEXT,
        "e2": E2_TEXT,
        "e3": E3_TEXT,
        "e4": E4_TEXT,
        "e5": E5_TEXT,
        "report_phrase": REPORT_PHRASE,
        "fact_ids": [str(row["id"]) for row in FACT_ROWS],
    }


def render_fact_table() -> str:
    lines = [
        "| ID | утверждение | точное значение | источник (путь + раздел) | статус | можно на слайд | формулировка для слайда |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in FACT_ROWS:
        lines.append(
            "| {id} | {claim} | {value} | {source} | {status} | {slide} | {slide_line} |".format(
                **{k: str(row[k]).replace("|", "/") for k in row}
            )
        )
    return "\n".join(lines)


def _non_claims_section() -> str:
    path = Path(__file__).resolve().parents[4] / "docs" / "pilot-claim-boundary-2026.md"
    text = path.read_text(encoding="utf-8")
    start = text.index("## Non-claims")
    end = text.index("## Reproducibility")
    body = text[start:end].strip()
    # Boundary lives in docs/; this file lives in docs/quality/.
    return body.replace("](evidence/", "](../evidence/").replace("](quality/", "](")


def render_auditor_document() -> str:
    snap = demo_day_auditor_snapshot()
    counts = snap["status_counts"]
    contra = "\n".join(
        f"| {row['id']} | {row['where']} | {row['drift']} |" for row in CONTRADICTIONS
    )
    questions = "\n\n".join(
        f"**{row['id']}. {row['q']}**\n{row['a']}" for row in DANGEROUS_QUESTIONS
    )
    demo = "\n".join(f"{i}. {step}" for i, step in enumerate(DEMO_20S, start=1))
    return f"""<!-- claims-lint: allow-file reason="Demo-day auditor A–F table; TZ 90%/SLA/CDE as non-claims; Checkpoint GO; customer_go false" -->
---
title: "Аудиторский пакет демо-дня — блоки A–F (14.09.2026)"
date: "2026-09-14"
last_updated: "2026-09-21"
status: active
version: "1.1.1"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_level: audit_table_not_score
customer_go: false
precision_claim_publishable: false
claim_boundary: >
  Evidence table for TechLab demo day, task Appendix 4 №6, commission №7.
  Not a predicted score. Not pack processed. Census fingerprints are not
  a jury exhibit. Checkpoint GO; customer_go false.
---

# Аудиторский пакет A–F — демо-день 21.09.2026

Машина: `python -c "from aerobim.domain.demo_day_auditor_pack import demo_day_auditor_snapshot, render_fact_table"`.

Это **не** карта жюри и **не** exhibit. Счётчики census (обёртка / unpack / IfcSpace пакета A) живут в инженерных пинах, не в `JURY_SURFACES`. PPTX на рабочем столе этим файлом не переписывается — канон слайдов: [`../../submission/03-presentation/demo_day_slides.md`](../../submission/03-presentation/demo_day_slides.md).

Checkpoint **`GO`**; `customer_go` **false**. `PrecisionClaim.publishable` **false**. Строк `VERIFIED_CUSTOMER`: **0** (пакет `processed=false`, dual-rater = 0, акт площадки = NO_DATA). Слабый статус выбран сознательно.

Сводка статусов: VERIFIED_INTERNAL {counts["VERIFIED_INTERNAL"]}; SYNTHETIC {counts["SYNTHETIC"]}; NEEDS_CUSTOMER {counts["NEEDS_CUSTOMER"]}; NOT_VERIFIED {counts["NOT_VERIFIED"]}; NO_DATA {counts["NO_DATA"]}; VERIFIED_CUSTOMER {counts["VERIFIED_CUSTOMER"]}. Фактов: {snap["fact_count"]}. На слайд: {snap["slide_yes_count"]}.

Связанные: [замок речи](../demo/DEMO_DAY_SPEECH_LOCK_2026_09.md) · [красная черта деки](DEMO_DAY_DECK_REDLINE_2026_09.md) · [граница заявлений](../pilot-claim-boundary-2026.md) · [CLAIMS_LOCK](../../audit/reports/CLAIMS_LOCK_2026_07_17.md).

## 1) Основная таблица

{render_fact_table()}

{_non_claims_section()}

## 2) ПРОТИВОРЕЧИЯ

| ID | Где | Суть |
|---|---|---|
{contra}

## 3) ОПАСНЫЕ ВОПРОСЫ

{questions}

## 4) ЗАПРОС ЗАКАЗЧИКУ

{CUSTOMER_LETTER}

## 5) СЦЕНАРИЙ ДЕМО 20 СЕКУНД

{demo}

Не открывать NDA-дерево. Не нажимать «Загрузить демонстрационный комплект» (`POST /v1/demo/seed-fixture`) как «их комплект». Не ставить `AEROBIM_SIGNOFF_PROFILE=customer_pilot` на чужом ноутбуке.
"""
