<!-- claims-lint: allow-file reason="Owner-AI plan execution; TZ 90%/SLA/MEP as blocked; OOS unsigned; NO_GO" -->
---
title: "Owner-AI plan execution — 2026-08-27"
date: "2026-08-27"
last_updated: "2026-08-28"
status: active
version: "1.1.0"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_level: coverage_map_only
detected_count: 0
claim_boundary: >
  Execution of the quality plan after TZ v1 pin and live-tree triage.
  Scaffolds and honesty gates. Not product accuracy. Not customer SLA.
  Not MEP delivered. Unsigned OOS does not license skip. Checkpoint NO_GO.
---

# Owner-AI plan execution (27.08.2026)

Машина: `python -c "from aerobim.domain.owner_ai_plan import plan_snapshot"`.  
Снимок: [`../evidence/owner-ai-plan-execution-2026-08.json`](../evidence/owner-ai-plan-execution-2026-08.json). IUA `PLAN-00`…`PLAN-05`.

Checkpoint **`NO_GO`**. `detected_count: 0`. Семь задач сравнения остаются **Uncertain**.

Не склеивать четыре бумаги: бриф ТЗ v1 (6 стр.); ТЗ v2 (ТР-1…62); семь задач Техлаба; проектное ТЗ объекта.

## Этот проход (агент)

| ID | Что сделано | Что это не значит |
|---|---|---|
| P0-01 | Инвентарь `files/` пишется только в `.local/`; в git — обезличенные счётчики | sha256 NDA-пакета; имена площадок |
| P0-02 | Пакет = ПД; РД нет; «после экспертизы» — zip | PD↔RD pairing как будто есть IFC РД |
| P1-* | Unsigned OOS: QTO / MEP / стержни (`samples/oos/`) | skip лицензирован; RT CLOSED |
| P1-EXTRACT | 0 hits extractor = `extraction_gap` | «в ТЗ нет огнестойкости/площадей» |
| P2-PUBLISH | interim 0.60; `PrecisionClaim.publishable=false` | цифра v1 «>90%» как замер |
| P3-GATE | cap IFC 256 MiB; KR ≠ KZH; DeterminismGate | поднять cap из-за одного АР |
| P4-KT3 / P4-MIK | речь КТ#3; M2/M8 = `VERIFY_WITH_OPERATOR` | самодельные формы Фонда |

CLI:

```text
python -m aerobim.tools.inventory_owner_files --output ../.local/files-pack-inventory.json
python -m aerobim.tools.evaluate_signed_oos --snapshot
python -m aerobim.tools.export_owner_ai_plan --write-docs-evidence
```

Публичный rehearsal (без имён, без хэшей): 4 папки, 2383 файла, 15 IFC (1 над cap), 27 RVT, 24 расчётных бинаря, 1127 PDF, 470 DWG. Не парсим RVT/NWD/LIRA. Не поднимаем cap.

Дополнение 28.08: в пин добавлены 21 NWD/NWC, 70 файлов со «замечания» в имени, из них 2 чек-листа типовых замечаний (соцобъекты, ~760/~837 пунктов). Чек-листы **не внесены** в каталог типовых ошибок: `customer_confirmed_patterns` остаётся 0, «каталог принят» запрещено (RT-TYP-CATALOG).

## Owner-blocked (не закрывается кодом)

| ID | Нужен объект | Стоп |
|---|---|---|
| P1-QTO | экспорт `NetFloorArea` **или** подписанный OOS | ТЭП Does-not при Missing QTO |
| P1-MEP | федеративный ИОС IFC **или** подписанный OOS | MEP delivered |
| P1-REBAR | `IfcReinforcingBar` **или** подписанный OOS п.7 | pitch pset = класс 4 |
| P2-RATERS | два независимых разметчика + κ/α | publishable без κ |
| P2-IDS | IDS назначающей стороны + `approval_ref` / `pack_hash` | городской АГР = профиль Самолёта |
| P4-MIK | формы Фонда от оператора | выдуманные M2/M8 |

Подписанный OOS лицензирует только речь «канал не измеряем». Он **не** закрывает RT-001/002/003.

## Калибровка литературы (не product score)

EGCC [arXiv:2607.29058](https://arxiv.org/abs/2607.29058) — 4-статус + HITL, не автономный approve. ARCHER [arXiv:2607.25566](https://arxiv.org/abs/2607.25566) — детерминированная оркестрация, не `summary.passed` от LLM. Ishigaki-IDS [arXiv:2606.08545](https://arxiv.org/abs/2606.08545) — черновик IDS, не `customer_approved`. DrawingVQA / AECV-Bench — VLM advisory. IfcTester / bSI IDS-Audit — checking; Xbim IDS — AGPL, не тащить в MIT runtime молча.

## DoD этого прохода

Скаффолды OOS unsigned. Инвентарь не в git. Карта семи задач Uncertain. NO_GO пока RT-001/002b/003 OPEN.
