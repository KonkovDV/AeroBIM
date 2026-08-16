---
title: "Round 8 — atomic sweep: evidence tools, P2-04 chain, pattern siblings"
status: active
version: "1.1.0"
last_updated: "2026-08-16"
claim_boundary: "Original pass was audit-only. Disposition records verification + fail-closed remediations. Checkpoint NO_GO; RT-001/002/003 OPEN. Eighth round of the 16.08 series (IDs HD8-*)."
audited_head: "375109c + working tree"
auditor: "ZCode, atomic sweep"
---

# Round 8 — атомный свеп: братья багов по паттернам

## Находки

### HD8-TOOL-01 (MEDIUM): fail-open дефолт выжил в генераторе доказательств

`tools/export_moexp_ids_coverage.py:162` — `passed = bool(spec.get("status", True))`. Тот же паттерн, что был исправлен в основном валидаторе (HD3-IDS-01), но фикс-волна не затронула tools/: скрипт, который **генерирует публичный evidence-артефакт покрытия MOEXP IDS**, при отсутствующем ключе `status` (дрейф ifctester) записывает в доказательство «спецификация пройдена». Опасность выше, чем у обычного инструмента: артефакт уходит в пакеты и слайды. Направление: `spec.get("status") is True` + счётчик skipped/unknown с выводом в артефакт; греп-гейт на `get("status", True)` по всему дереву.

### HD8-P204-01 (OK-CONFIRM): цепочка P2-04 fail-closed по построению

Проверена вся цепочка «немыслимой комбинации»: отказ spatial-index (`ifc_open_shell_validator.py:61-65` → None) → `_confirm_annotation_ifc_links(links, None)` → `confirm_annotation_ifc_links` возвращает ссылки без изменений (`annotation_ifc_matching.py:217-218`). Безопасно, потому что обе точки конструирования (`:88`, `:133`) создают ссылки с `ifc_guid=None`, и заполнить его может только `confirm_link_against_spatial_index`. Гарантия «claimed GUID → ifc_guid только после presence-check» держится даже при падении индекса.

### HD8-PAT-01 (OK-CONFIRM): паттерн-свеп по дереву — чисто

- Мутабельные дефолты (`=[]`/`={}`) в src: **0**.
- `norm_pack_hash.py`: `sort_keys=True` + `sorted(rglob)` — порядок в хеш детерминирован.
- Lock-age логика везде консистентна (`time.time()` против `st_mtime` — wall-clock к wall-clock).
- Аннотированные `except Exception → return None/[]` (spatial_index, pdf-ориентация, aabb-фильтр) — задокументированные degrade-пути в advisory/degraded capabilities, не источники вердикта.

## Итог серии (8 раундов)

Открытые код-находки: **HD8-TOOL-01** (первый в очереди — генератор доказательств), HD7-IDS-03 (spec-level truthiness), HD7-IFC-01 (verify `_to_float` → skip), HD2-UP-01, HD3-BFF-01, HDX-LINT-01, HD2-RL-02 (by-design). Серия 16.08 закрыта; продолжение — по промту White Hat (§3 RED_TEAM_ATOMIC) режимами «фаззинг»/«интерливинг».

## Disposition (верификация + fail-closed)

Исходный closer открывал HD7-IDS-03 / HD7-IFC-01 / HD2-UP-01 / HD3-BFF-01 — это **не** открыто (см. [`RED_TEAM_ATOMIC_2026_08_16.md`](RED_TEAM_ATOMIC_2026_08_16.md) v1.1.0 и re-audit). HD8-TOOL-01 = тот же баг, что RT16-MOEXP-01.

| ID | Статус | Доказательство |
|---|---|---|
| HD8-TOOL-01 | **FIXED** | `specification_row_from_reporter`: pass только при `status is True`; missing/non-bool → `STATUS_UNKNOWN` + `status_drift` + счётчик `unknown_or_skipped`. Schema coverage **1.2.0**. Grep-гейт: `test_no_ids_status_true_default_in_backend_src`. Checked-in `docs/evidence/norm-pack-moexp-coverage-2026-08.json` **не** перегенерирован (следующий CLI-прогон) |
| HD8-P204-01 | **OK-CONFIRM** + harden | Конструкторы `:88`/`:133` ставят `ifc_guid=None`. Index=None раньше возвращал links as-is; теперь pre-set `ifc_guid` тоже сбрасывается. Pin: `test_confirm_strips_preset_guid_when_index_none` |
| HD8-PAT-01 | **OK-CONFIRM** | `get("status", True)` в `backend/src` = 0 после фикса. Мутабельные дефолты `=[]`/`={}` в src: 0 (повторный grep) |
| HD7-IDS-03 / HD7-IFC-01 | **FIXED / EXPLAINED** ранее | Не открывать |
| HD2-UP-01 / HD3-BFF-01 | **FIXED** ранее | Не открывать |
| HDX-LINT-01 | **PARTIAL** | |
| HD2-RL-02 | **BY-DESIGN** | |

Снапшот MOEXP coverage на диске — исторический прогон; не выдавать его schema 1.1.0 как доказательство нового гейта. Checkpoint **NO_GO**.
