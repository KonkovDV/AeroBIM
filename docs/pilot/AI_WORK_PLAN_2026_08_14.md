<!-- claims-lint: allow-file reason="Detailed work plan for AI agent; forbidden phrases listed as non-claims; NO_GO explicit" -->
---
title: "AeroBIM — детальный план работы для ИИ (14.08.2026, код не трогаем)"
date: "2026-08-14"
status: active
claim_boundary: >
  Plan only. Checkpoint NO_GO. No code changes. No new ports/DI. Fixture-scoped
  metrics. Not customer accuracy. Not moscow_agr complete profile. Not Tangl/10D
  integration. Not product >90%. Not MEP delivered. Not CDE-ready. Not DWG-ready.
---

# Детальный план работы для ИИ (код не трогаем)

**Дата:** 14 августа 2026  
**Checkpoint:** **NO_GO** (RT-001/002/003)  
**Окно:** до загрузки КТ#2 **20.08.2026**  
**Режим:** только документы, речь, интейк, координация. **Код не исправлять.**

---

## 0. Что уже сделано (не переделывать)

| Артефакт | Статус | Ссылка |
|---|---|---|
| OSINT Самолёт + вектор | **DONE** | [`docs/gtm/SAMOLET_OSINT_VECTOR_KT2_2026_08_14.md`](../gtm/SAMOLET_OSINT_VECTOR_KT2_2026_08_14.md) |
| Конкурентная матрица RU | **DONE** | [`docs/partners/COMPETITIVE_MATRIX_2026_08.md`](../partners/COMPETITIVE_MATRIX_2026_08.md) |
| Интейк stack-aware | **DONE** | [`docs/partners/SAMOLET_WHAT_WE_NEED_2026_07-ru.md`](../partners/SAMOLET_WHAT_WE_NEED_2026_07-ru.md) |
| Речь жюри/трекера | **DONE** | [`docs/demo/KT2_JURY_FAQ_2026_08_12.md`](../demo/KT2_JURY_FAQ_2026_08_12.md) · [`docs/demo/TRACKER_MEETING_2026_08_14.md`](../demo/TRACKER_MEETING_2026_08_14.md) |
| НПА АГР / СтроимПросто | **DONE** | [`docs/regulatory-baseline-2026.md`](../regulatory-baseline-2026.md) |
| Честность демо-IFC | **DONE** | [`samples/ifc/README.md`](../../samples/ifc/README.md) |
| Red Team OSINT-пакета | **DONE** | [`docs/quality/RED_TEAM_SAMOLET_OSINT_VECTOR_2026_08_14.md`](../quality/RED_TEAM_SAMOLET_OSINT_VECTOR_2026_08_14.md) |
| Коммит + push | **DONE** | `0905e60` → `origin/main` |

---

## 1. Открытые проблемы (из чата «от и до»)

### 1.1 Блокеры Checkpoint (не закрываются кодом)

| ID | Проблема | Почему открыта | Что нужно |
|---|---|---|---|
| **RT-001** | Нет корпуса «ПД РФ + заключение экспертизы» | Публично не существует; ЕГРЗ не даёт пар | Подписанный корпус Самолёта (intake) |
| **RT-002** | Нет подписанного профиля приёмки Самолёта | IDS МОГЭ публичны, но не подписаны заказчиком | Письменный scope memo + IDS от Самолёта |
| **RT-003** | Federated MEP clash NOT_VERIFIED | Нет публичных federated IFC с clash ground truth | Модели Самолёта или согласованный публичный корпус |

### 1.2 Технические заглушки (не закрываются до КТ#3)

| ID | Проблема | Статус | Когда |
|---|---|---|---|
| **DWG** | Native DWG parser отсутствует | **FAILED** (ADR-003) | КТ#3: ODA trial 60 дней |
| **OIDC BFF** | 501 stub | **NOT production-ready** | После КТ#2 |
| **MEP system-aware** | Только AABB overlap, не clash | **NOT_VERIFIED** | После корпуса |

### 1.3 Операционные задачи (человек, не ИИ)

| Задача | Когда | Кто |
|---|---|---|
| Видео 3 мин | 19.08 | **Человек** |
| Загрузка в ЛК | 19.08–20.08 | **Человек** |
| Подпись акта МИК | После пилота | **Самолёт + оператор** |

### 1.4 Задачи, которые ИИ может делать (без кода)

| Задача | Статус | Дата |
|---|---|---|
| Harbor 160 AEC-Bench | **SKIPPED** или прогон | 17.08 |
| N43 baseline SHA drift | **Мониторинг** | 17.08 |
| IFC-Bench 514 false-pass | **SKIPPED** (25/1026 countable) | Не выдумывать % |
| Renga IFC для демо | **Intake** | После встречи с Самолётом |

---

## 2. План работы для ИИ (по дням)

### 14.08 (сегодня, после встречи 08:00)

| # | Задача | Выход | Статус 14.08 |
|---|---|---|---|
| 14.1 | Итоги встречи с трекером | [`../demo/TRACKER_MEETING_2026_08_14_FOLLOWUP.md`](../demo/TRACKER_MEETING_2026_08_14_FOLLOWUP.md) | **DONE** — заметок Сигиневича в repo нет; протокол не выдуман |
| 14.2 | CI / claims | README `not claimed`; относительные ссылки плана | **PARTIAL** — `lint_claims.py` OK; docs-links этого плана чиним; typecheck/test/`--full-docs` красные **до** этого пакета, код freeze |
| 14.3 | Шаблон запроса Renga IFC | [`../partners/SAMOLET_RENGA_IFC_REQUEST_2026_08_14.md`](../partners/SAMOLET_RENGA_IFC_REQUEST_2026_08_14.md) | **DONE** — не просит Tangl API |

### 15–16.08 (выходные, если трекер не дал правок)

| # | Задача | Выход | Статус 14.08 |
|---|---|---|---|
| 15.1 | Overlay e2e | [`../demo/KT2_CLONE_TO_DEMO_CHECK_2026_08_14.md`](../demo/KT2_CLONE_TO_DEMO_CHECK_2026_08_14.md) | **PARTIAL** — контракт + committed PNG; live CLI **SKIPPED** (нет `.venv`) |
| 15.2 | Сценарий видео 3 мин | [`../demo/KT2_VIDEO_SCRIPT_3MIN_2026_08_19.md`](../demo/KT2_VIDEO_SCRIPT_3MIN_2026_08_19.md) | **DONE** (запись — человек 19.08) |
| 15.3 | README clone-to-demo | тот же check | **DONE** — команда в README есть |

### 17.08 (понедельник)

| # | Задача | Выход | Статус 14.08 |
|---|---|---|---|
| 17.1 | Harbor 160 | [`HARBOR_160_DECISION_2026_08_14.md`](HARBOR_160_DECISION_2026_08_14.md) | **PREP** — default SKIPPED; подтвердить 17.08 |
| 17.2 | N43 drift | [`../audit/N43_MONITORING_SNAPSHOT_2026_08_14.md`](../audit/N43_MONITORING_SNAPSHOT_2026_08_14.md) | **PREP** — **62 > 50**; не активировать |
| 17.3 | Пакет КТ#2 | [`KT2_UPLOAD_PACK_2026_08_14.md`](KT2_UPLOAD_PACK_2026_08_14.md) | **PREP** — список готов; грузит человек |

### 18.08 (вторник)

| # | Задача | Выход | Статус 14.08 |
|---|---|---|---|
| 18.1 | Claims | `python scripts/lint_claims.py` | **PARTIAL** — default OK; `--full-docs` красный на старых файлах |
| 18.2 | Cursor trailers | `git log --format=full -15` | **DONE** — нет `Co-authored-by: Cursor` |
| 18.3 | Буфер 20.08 | [`KT2_BUFFER_20_08_2026.md`](KT2_BUFFER_20_08_2026.md) | **DONE** |

### 19.08 (среда, человек)

| # | Задача | Статус |
|---|---|---|
| 19.1 | Видео 3 мин | **BLOCKED: человек** |
| 19.2 | Загрузка в ЛК | **BLOCKED: человек** |
| 19.3 | Финальный коммит | этот pack — docs only |

### 20.08 (четверг, буфер)

| # | Задача | Статус |
|---|---|---|
| 20.1 | Ничего нового | ещё не наступило |
| 20.2 | Скриншот ЛК | **BLOCKED: человек** |

---

## 3. Что ИИ НЕ делает (запреты)

| Запрет | Почему |
|---|---|
| Новые порты / адаптеры / DI-токены | Архитектура заморожена |
| Исправление кода | Пользователь: «код не исправлять» |
| Перекрас Checkpoint в GO | RT-001/002/003 не закрыты |
| Выдуманные цифры в docs | Только прогон → `artifacts/` |
| VLM ставит PASS | ADR-001 |
| Демо «двери/окна» | VLM 0.40–0.55, развалит показ |
| Формулировка «нет утверждённых норм» | Ложь: IDS МОГЭ публичны |
| «Интегрированы с Tangl / 10D» | Claims Lock |
| «Заменим Tangl Control / Value» | Не наш слой |
| «Закрыли ЦИМ АГР Москвы» | Профиль CUT |
| Называть текущие должности Поздняковой / Самоходкина | Не публично |
| Цитировать 6,1 тыс. штат или 200 млн ₽ ИИ как ROI AeroBIM | Не наши цифры |
| Покупка ODA / запуск 160 задач AEC-Bench до 17.08 | Календарь |
| Алиас `IFC4`↔`IFC4X3` | Снова fail-open |
| GPLv3 IFC в git | MIT-гигиена |
| LibreDWG | GPL-3 |
| Писать свой EXPRESS / Gherkin / ifcbench SQLite | Зовём upstream |
| `moscow_agr` как новый порт | CUT |
| Запись видео и загрузка в ЛК агентом | **Человек** |

---

## 4. Команды для проверки (не исправления)

```bash
# Claims lint (должен быть OK)
python scripts/lint_claims.py

# Проверка коммитов на следы Cursor
git log --format=full -10 | grep -i "co-authored-by"

# Проверка CI
git log --oneline -3

# Проверка демо (не запускать, только проверить, что команда есть)
# cd backend && python -m aerobim.tools.run_demo_vertical_slice

# Проверка evidence
ls docs/evidence/ids-fail-closed-2026-08.md
ls docs/evidence/norm-pack-moexp-coverage-2026-08.md
ls docs/evidence/federated-mep-inventory-2026-08.md
```

---

## 5. Речь на 20 секунд (если спросят)

«Самолёт уже на Renga, Tangl и 10D. Tangl проверяет модель, 10D ведёт документ. Мы проверяем **комплект** и честно валим IFC4X3 против IDS МОГЭ IFC4. Нормы открытые прогнаны. 25/1026 countable, не 514. West Riverside — инвентарь, не QA. Нет корпуса РФ-экспертизы и подписи Самолёта. Checkpoint **NO_GO**. GO не рисуем.»

---

## 6. Источники

| ID | Ссылка | Зачем |
|---|---|---|
| S1 | [`docs/gtm/SAMOLET_OSINT_VECTOR_KT2_2026_08_14.md`](../gtm/SAMOLET_OSINT_VECTOR_KT2_2026_08_14.md) | OSINT + вектор |
| S2 | [`docs/pilot/KT2_7DAY_PLAN_2026_08_13.md`](KT2_7DAY_PLAN_2026_08_13.md) | План 13–20.08 |
| S3 | [`docs/pilot/WITHOUT_SAMOLET_PLAN_2026_08_14.md`](WITHOUT_SAMOLET_PLAN_2026_08_14.md) | Что закрываем без Самолёта |
| S4 | [`docs/demo/KT2_JURY_FAQ_2026_08_12.md`](../demo/KT2_JURY_FAQ_2026_08_12.md) | Речь жюри |
| S5 | [`docs/demo/TRACKER_MEETING_2026_08_14.md`](../demo/TRACKER_MEETING_2026_08_14.md) | Речь трекеру |
| S6 | [`docs/quality/ACCEPTED_RISKS_REGISTRY_KT2_2026_08_09.md`](../quality/ACCEPTED_RISKS_REGISTRY_KT2_2026_08_09.md) | Отложенные риски |
| S7 | [`audit/reports/CRITICAL_BLOCKERS.md`](../../audit/reports/CRITICAL_BLOCKERS.md) | RT-001/002/003 |

---

## 7. Критерий завершения

План считается выполненным, если:

1. Все задачи 14.08–20.08 закрыты или явно отложены с причиной.
2. `lint_claims.py` — 0 violations.
3. Нет новых коммитов с кодом (только docs).
4. Видео и ЛК — человек, не ИИ.
5. Checkpoint остаётся **NO_GO**.

**Не критерий:** «всё идеально». Критерий: «ничего не сломано, ничего не выдумано, дедлайн соблюдён».

---

## 8. Исполнение 14.08.2026 (этот проход)

Код **не менялся**. Checkpoint **NO_GO**.

Deliverables: follow-up трекера, письмо Renga, скрипт видео, clone-to-demo check, Harbor default SKIPPED, N43=62, список ЛК, план Б, README `not claimed`, починка ссылок плана.

Red Team исполнения: [`../quality/RED_TEAM_AI_PLAN_EXECUTION_2026_08_14.md`](../quality/RED_TEAM_AI_PLAN_EXECUTION_2026_08_14.md).
