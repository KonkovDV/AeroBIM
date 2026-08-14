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
| OSINT Самолёт + вектор | **DONE** | [`docs/gtm/SAMOLET_OSINT_VECTOR_KT2_2026_08_14.md`](docs/gtm/SAMOLET_OSINT_VECTOR_KT2_2026_08_14.md) |
| Конкурентная матрица RU | **DONE** | [`docs/partners/COMPETITIVE_MATRIX_2026_08.md`](docs/partners/COMPETITIVE_MATRIX_2026_08.md) |
| Интейк stack-aware | **DONE** | [`docs/partners/SAMOLET_WHAT_WE_NEED_2026_07-ru.md`](docs/partners/SAMOLET_WHAT_WE_NEED_2026_07-ru.md) |
| Речь жюри/трекера | **DONE** | [`docs/demo/KT2_JURY_FAQ_2026_08_12.md`](docs/demo/KT2_JURY_FAQ_2026_08_12.md) · [`docs/demo/TRACKER_MEETING_2026_08_14.md`](docs/demo/TRACKER_MEETING_2026_08_14.md) |
| НПА АГР / СтроимПросто | **DONE** | [`docs/regulatory-baseline-2026.md`](docs/regulatory-baseline-2026.md) |
| Честность демо-IFC | **DONE** | [`samples/ifc/README.md`](samples/ifc/README.md) |
| Red Team OSINT-пакета | **DONE** | [`docs/quality/RED_TEAM_SAMOLET_OSINT_VECTOR_2026_08_14.md`](docs/quality/RED_TEAM_SAMOLET_OSINT_VECTOR_2026_08_14.md) |
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

| # | Задача | Вход | Выход | Критерий готовности |
|---|---|---|---|---|
| 14.1 | Записать итоги встречи с трекером | Заметки Дмитрия а | `docs/demo/TRACKER_MEETING_2026_08_14_FOLLOWUP.md` | Список правок, если есть |
| 14.2 | Проверить, что OSINT-пакет не сломал CI | `git log --oneline -3` | CI green | `lint_claims.py` OK |
| 14.3 | Подготовить шаблон запроса Renga IFC | [`SAMOLET_WHAT_WE_NEED_2026_07-ru.md`](docs/partners/SAMOLET_WHAT_WE_NEED_2026_07-ru.md) §0.1 | Текст письма/сообщения | Не просить Tangl API |

### 15–16.08 (выходные, если трекер не дал правок)

| # | Задача | Вход | Выход | Критерий готовности |
|---|---|---|---|---|
| 15.1 | Проверить overlay e2e (уже на main) | `artifacts/vertical-slice-demo/` | Подтверждение, что PNG + HTML работают | `run_demo_vertical_slice` exit 0 |
| 15.2 | Подготовить сценарий видео 3 мин | [`TRACKER_MEETING_2026_08_14.md`](docs/demo/TRACKER_MEETING_2026_08_14.md) §«Что показать за 3 минуты» | Скрипт для человека | 3 мин, не больше |
| 15.3 | Проверить README clone-to-demo | `README.md` §«KT#2 vertical slice» | Подтверждение 10 мин от клона | Команда работает |

### 17.08 (понедельник)

| # | Задача | Вход | Выход | Критерий готовности |
|---|---|---|---|---|
| 17.1 | Harbor 160: **SKIPPED** или прогон | [`KT2_7DAY_PLAN_2026_08_13.md`](docs/pilot/KT2_7DAY_PLAN_2026_08_13.md) §17.08 | Решение: SKIPPED (по умолчанию) | Не выдумывать % false-pass |
| 17.2 | N43: проверить baseline SHA drift | `docs/evidence/runtime-baseline-latest.json` | Отчёт: drift ≤50 коммитов | Soft check, не блокер |
| 17.3 | Подготовить пакет для КТ#2 | Все evidence | Список файлов для загрузки | Ничего нового |

### 18.08 (вторник)

| # | Задача | Вход | Выход | Критерий готовности |
|---|---|---|---|---|
| 18.1 | Финальная проверка claims | `scripts/lint_claims.py --full-docs` | 0 violations | CI green |
| 18.2 | Проверить, что нет следов Cursor в коммитах | `git log --format=full -10` | Нет `Co-authored-by: Cursor` | Чисто |
| 18.3 | Подготовить буфер для 20.08 | — | Список «что может пойти не так» | План Б |

### 19.08 (среда, человек)

| # | Задача | Вход | Выход | Критерий готовности |
|---|---|---|---|---|
| 19.1 | **Видео 3 мин** (человек) | Скрипт из 15.2 | `artifacts/demo/kt2-demo.mp4` | 3 мин, не больше |
| 19.2 | **Загрузка в ЛК** (человек) | Пакет из 17.3 | Подтверждение загрузки | Скриншот |
| 19.3 | Финальный коммит (если правки) | — | `git push` | Только фиксы, не фичи |

### 20.08 (четверг, буфер)

| # | Задача | Вход | Выход | Критерий готовности |
|---|---|---|---|---|
| 20.1 | Ничего нового | — | — | Только критические фиксы |
| 20.2 | Подтверждение загрузки | ЛК | Скриншот | Дедлайн соблюдён |

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
| Называть текущие должности ой / а | Не публично |
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
| S1 | [`docs/gtm/SAMOLET_OSINT_VECTOR_KT2_2026_08_14.md`](docs/gtm/SAMOLET_OSINT_VECTOR_KT2_2026_08_14.md) | OSINT + вектор |
| S2 | [`docs/pilot/KT2_7DAY_PLAN_2026_08_13.md`](docs/pilot/KT2_7DAY_PLAN_2026_08_13.md) | План 13–20.08 |
| S3 | [`docs/pilot/WITHOUT_SAMOLET_PLAN_2026_08_14.md`](docs/pilot/WITHOUT_SAMOLET_PLAN_2026_08_14.md) | Что закрываем без Самолёта |
| S4 | [`docs/demo/KT2_JURY_FAQ_2026_08_12.md`](docs/demo/KT2_JURY_FAQ_2026_08_12.md) | Речь жюри |
| S5 | [`docs/demo/TRACKER_MEETING_2026_08_14.md`](docs/demo/TRACKER_MEETING_2026_08_14.md) | Речь трекеру |
| S6 | [`docs/quality/ACCEPTED_RISKS_REGISTRY_KT2_2026_08_09.md`](docs/quality/ACCEPTED_RISKS_REGISTRY_KT2_2026_08_09.md) | Отложенные риски |
| S7 | [`audit/reports/CRITICAL_BLOCKERS.md`](audit/reports/CRITICAL_BLOCKERS.md) | RT-001/002/003 |

---

## 7. Критерий завершения

План считается выполненным, если:

1. Все задачи 14.08–20.08 закрыты или явно отложены с причиной.
2. `lint_claims.py` — 0 violations.
3. Нет новых коммитов с кодом (только docs).
4. Видео и ЛК — человек, не ИИ.
5. Checkpoint остаётся **NO_GO**.

**Не критерий:** «всё идеально». Критерий: «ничего не сломано, ничего не выдумано, дедлайн соблюдён».
