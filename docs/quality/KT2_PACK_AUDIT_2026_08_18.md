---
title: "КТ#2 — аудит пакета подачи (18.08.2026)"
status: active
version: "1.0.0"
last_updated: "2026-08-18"
claim_boundary: >
  Pack audit only. Checkpoint NO_GO; RT-001/002/003 OPEN.
  Fixture evidence ≠ customer корпус.
---

# Аудит пакета КТ#2 — 2026-08-18

**Объект:** работа вечера 17.08 — коммиты `8bdf6d1..386dba8` (7 штук), пять полей формы, CI на `main`.

## Что проверено утром 18.08

| Проверка | Как | Результат |
|---|---|---|
| Быстрые гейты CI | `scripts/pre_push_gate.py` (ruff, claims ×4, baseline, metadata, links, S-band, handoff) | ok; одно warn (commits-behind, в CI не работает из-за shallow checkout) |
| Честность формулировок | pytest: honesty lock, handoff, wording guard, lint claims, metadata | 85 passed |
| Живой показ | `python -m aerobim.tools.run_demo_ifc_acceptance_gate` на текущем HEAD | `passed=false` ожидаем (дефект заложен), `checkpoint_verdict=NO_GO`, 9 находок / 7 блокирующих, `reproducibility_hash` присутствует |
| Честность capabilities в прогоне | тот же артефакт | `ids_validation=OK`, `property_validation=OK`, `geometry=SKIPPED`, `dwg_native=MISSING`, `mep_system_clash=NOT_VERIFIED` |
| Дека в git | `git ls-files` + сверка текста слайдов | `aerobim_kt2.pptx` + `aerobim_kt2.pdf` отслеживаются; `NO_GO`, команда гейта и формула стадии на месте; запрещённых формулировок нет |
| CI / CodeQL на `main` | run 32068658760 на `386dba8` | success / success |
| Дерево | `git status` | чистое; `.local/` не трекается |

## Что было найдено и закрыто вечером 17.08

| Находка | Реакция |
|---|---|
| Деку «готовил оператор», в git её не было | pptx/pdf закоммичены; поля 01/02/05 и карта ТЗ указывают на деку; тест `test_submission_surfaces_are_consistent_about_deck_and_video` фиксирует |
| README тащил скриншот фикстуры как витрину | Блок удалён из обоих README; доказательство осталось в evidence-пакете |
| N-43 дрейф baseline (тест LOC 51404 → 51459) | Обновление из CI-артефакта прогона 32064789304, не из локального pytest |
| `ruff format` локально не гонялся | Формат применён; `scripts/pre_push_gate.py` + `.githooks/pre-push` зеркалят быстрые гейты CI до push |

Продуктовый код не менялся: все правки — docs, тесты честности, гейт-инструментарий.

## Остаётся человеку (не код)

1. ЛК: пять полей, файлы собраны в `.local/lk-upload-kt2/` (видео-поле пустое — показ живой CLI).
2. Письмо Самолёту: четыре пункта запроса ([`../partners/SAMOLET_KT2_ASK_2026_08_15.md`](../partners/SAMOLET_KT2_ASK_2026_08_15.md)).
3. Репетиция ответов: [`../demo/KT2_HOSTILE_QA_PLAYBOOK_2026_08_16.md`](../demo/KT2_HOSTILE_QA_PLAYBOOK_2026_08_16.md).

## Вердикт

Пакет подачи — честный `NO_GO`: пять полей формы заполнены, заявления совпадают с доказательствами, CI зелёный на `386dba8`. Checkpoint не двигается: RT-001/002/003 закрываются только поставками заказчика.
