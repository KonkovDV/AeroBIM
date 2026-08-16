---
title: "Round 7 — Atomic hunt: unthinkable combinations + world literature radar + white-hat prompt"
status: active
version: "1.1.0"
last_updated: "2026-08-16"
claim_boundary: "Original pass was audit-only. Disposition records verification + fail-closed remediations. Checkpoint NO_GO; RT-001/002/003 OPEN. Companion to docs/ai/MASTER_RED_TEAM_PROMPT_2026_08_16.md."
audited_head: "375109c + working tree"
auditor: "ZCode, white-hat persona (50y experience emulation), round 7"
---

# Round 7 — атомная охота + литература

## 1. Новые атомарные находки

### HD7-IDS-03 (MEDIUM): type-confusion через truthiness на spec-уровне

`ifc_tester_ids_validator.py:127` — `spec_status = spec.get("status")` без проверки типа, дальше `if spec_status: continue`. Если будущий ifctester (или ручной путь) отдаст статус **строкой** `"false"`, Python посчитает её truthy → спецификация молча «пройдена». Requirement-уровень уже защищён (`is True`, фикс HD3-IDS-01), spec-уровень — нет: `is True` проверяет и тип, и значение; truthy-проверка — только «непустость». Направление: `if spec_status is True: continue` + в gate-функцию `isinstance(status, bool)`-гейт для не-bool.

### HD7-IFC-01 (LOW, верификация): unparsable observed → тихий skip?

`_to_float` (`ifc_open_shell_validator.py:414-420`) возвращает `None` на неразборчивом значении (запятая обрабатывается, thousand-разделители `"1.234,56"` — нет). Вопрос 50-летнего белошапочника: что происходит с проверкой, когда observed=None при существующем expected? Если skip без finding — это «тишина = успех» для числовых правил. Проверить путь использования `_to_float` и добавить «cannot verify»-finding вместо skip.

### HD7-COMBO-01 (INFO): карта «немыслимых комбинаций» — проверено/осталось

- Acceptance Gate на legacy-отчёте без `outcome` — безопасно (fallback `:148-149`, derived из passed).
- Unicode-tenant: NFKC + `!hex`-кодирование токена — коллизий не нашёл.
- IFC-путь = каталог: `exists()` пропустит, ifcopenshell упадёт → generic fail — приемлемо.
- Один пакет, разный `remark_locale`: remarks не входят в engine_signature → один reproducibility-hash на два разных HTML. Не баг вердикта, но артефактная неоднозначность (INFO).
- Осталось непроверенным: BCF-ingest враждебного zip × quota-гонка; OIDC lab-сессия × rate-limit бакет; двойной отказ (Redis down + non-dev) — кандидаты для дрели вашего ИИ.

## Disposition (верификация + fail-closed)

Исходный проход читал `if spec_status: continue`. В дереве на момент разбора уже было `if spec_status is True: continue` (`ifc_tester_ids_validator.py`, HD3-IDS-01). Строка `"false"` **не** уходила в silent-pass через truthy-`continue`. Оставалась дыра: не-bool / `False` + пустой `requirements[]` (и не prohibited) → ноль findings = тишина как успех.

| ID | Статус | Доказательство |
|---|---|---|
| HD7-IDS-03 | **FIXED** (хвост) | `ids_reporter_status_is_bool` + `RULE_STATUS_TYPE`; после цикла: `status is not True` и ноль findings → ERROR. Pin: `test_string_false_empty_spec_is_not_a_pass`, `test_string_true_empty_spec_is_not_a_pass`, `test_bool_false_empty_spec_is_not_a_pass` |
| HD7-IFC-01 | **EXPLAINED** + harden | `_matches_requirement`: `observed=None` при numeric expected **не** skip. Раньше string-fallback; `"1.234,56"` vs `"1234.56"` уже был mismatch. Harden: mixed parse → `False` (finding ERROR у caller). Alphanumeric EQUALS (оба unparsable) остаётся string compare. Не «cannot-verify» как отдельный класс — fail-closed mismatch |
| HD7-COMBO-01 | **INFO** | Карта принята. Не прогнано: BCF zip × quota; OIDC lab × rate-limit; Redis down + non-dev |
| HD2-UP-01 / HD3-BFF-01 | **FIXED** ранее | Не открывать заново. См. [`RED_TEAM_REAUDIT_POST_FIX_2026_08_16.md`](RED_TEAM_REAUDIT_POST_FIX_2026_08_16.md) |
| HDX-LINT-01 | **PARTIAL** | `excluded_by_fragment`; directory-unblind не сделан |
| HD2-RL-02 | **BY-DESIGN** | `max_events<=0` = off |
| Dias 2026 | **FILED** | Строка в [`../samolet-techlab-alignment-2026.md`](../samolet-techlab-alignment-2026.md) §2; DOI `10.1016/j.autcon.2026.107043` (не year-twin) |
| bSI Validation Service | **FILED** | Сноска-baseline в [`../demo/KT2_TASK07_COMPARISON_2026_08.md`](../demo/KT2_TASK07_COMPARISON_2026_08.md); не шестой конкурент Задачи 07; не «как Validation Service» |

White-hat промт (§3) остаётся копируемым. HD8-охота — только по команде «фаззинг» / «полный прогон» / «дрель-комбо».

## 2. Литературный радар (август 2026, веб)

- **Dias et al., 2026, Automation in Construction — «openBIM workflow based on Information Delivery Specification»** ([ScienceDirect](https://www.sciencedirect.com/science/article/pii/S0926580526002840), [doi:10.1016/j.autcon.2026.107043](https://doi.org/10.1016/j.autcon.2026.107043)): requirement-driven openBIM workflow. **Disposition:** строка в alignment §2; analog only (не IDScribe, не cost QTO).
- **buildingSMART IFC Validation Service** ([официальный](https://www.buildingsmart.org/users/services/validation-service/)) — референс-кейс валидации IFC от вендоров; использовать в сравнительной таблице как «базовую линию валидации».
- Практический контур IDS: [BIM Corner](https://bimcorner.com/ids-stop-manual-checking-automate-bim-validation/), [Digital Construction Week](https://www.digitalconstructionweek.com/beyond-geometry-lessons-from-automating-ifc-data-checks-with-ids/), [Data Octopus guide](https://dataoctopus.net/blog-ids-ifc-validation-guide-2025) — подтверждение: IDS-валидация стала мейнстримом 2025–2026 → «мы проверяем IDS» уже не дифференциатор (совпадает с «Анализ 2», боль C) — дифференциатор: evidence + fail-closed + кросс-документность.
- [Solibri data validation](https://www.solibri.com/solutions/bim-quality-assurance/data-validation) — актуальный коммерческий якорь для слайда сравнения.

## 3. Промт «White Hat 50 лет» для вашего ИИ

```text
Ты — белый хакер с 50-летним стажем аудита систем (от CDC до cloud-native), прикреплён
к проекту AeroBIM (C:\plans\AeroBIM). Твоя работа — находить баги там, где их «не может
быть». Код не исправлять; только находки, доказательства и diff-направления.

ПАМЯТЬ: docs/quality/RED_TEAM_HYPERDEEP_*_2026_08_16.md (серия HD…HD5),
REAUDIT_POST_FIX (HDX), ATOMIC (HD7, этот файл). Перед работой прочитай их реестры —
не дублируй закрытое.

ТВОИ ПРИНЦИПЫ (выжимка 50 лет):
1. Типы лгут: ищи truthiness-проверки там, где нужен `is True`/`isinstance`;
   строки-"false", 0/1/"0", None-пробросы.
2. Тишина = успех: каждый `continue`, каждый `.get(k, default)`, каждый `except: pass`
   — спроси «что если данные придут не в том формате?» Дрейф внешних систем — норма.
3. Гонки живут на стыках: lock → работа → unlock; reserve → commit; cache → evict;
   DNS-check → connect. Найди окно — опиши интерливинг по шагам.
4. Комбинации важнее одиночных багов: отказ движка × quota; auth-провал × rate-limit;
   legacy-объект × новый код; Unicode × файловая система × Windows.
5. Математика — тоже код: пересчитывай руками формулы, границы, округления, зоны.
6. Ошибка оператора — твой враг: любое «оператор должен помнить» = будущий инцидент.
7. Если не можешь воспроизвести — не заявляй CRITICAL; заявляй с уровнем уверенности.

МЕТОД (цикл):
а) выбери модуль из непрочитанных (реестр residual: ifc_open_shell_validator полный,
   VLM-пайплайны, App.tsx, ~290 тестов, postgres SQL-детали);
б) прочитай построчно; на каждое решение спроси «что если вход — мусор/пусто/огромное/
   не-тот тип/двойной вызов/параллельный вызов?»;
в) каждую гипотезу проверь grep-ом путей вызова до границы системы;
г) находку запиши: [SEV] HD8-<zone>-NN — файл:строка — доказательство — интерливинг/
   сценарий — направление фикса. Сохрани в docs/quality/RT_RUN_<дата>.md.

СПЕЦ-РЕЖИМЫ ПО КОМАНДЕ:
- «фаззинг <модуль>» — сгенерируй 20 враждебных входов (типы, кодировки, размеры,
  вложенность, пустоты) и проследи каждый по коду до исхода; докладывай только
  не-fail-closed исходы.
- «интерливинг <функция>» — распиши все параллельные исполнения функции по шагам,
  найди потерянные атомарности.
- «литрадар» — сверь citations проекта со свежими публикациями (web): что 2025–2026
  по IDS/model checking/compliance LLM не цитируется; каждая свежая работа — строка
  в related-work план preprint'а.
- «дрель-комбо» — сгенерируй 5 «немыслимых комбинаций» отказов и проверь кодом-чтением,
  что система остаётся fail-closed в каждой.

ГРАНИЦЫ: не правь код; не выдумывай числа; не повышай SEV без доказательства;
запрещённые формулировки — audit/claims_forbidden_wording.json; вывод — по-русски,
термины как в коде, экономно.
```

## 4. Итог серии 16.08

Семь раундов. Точную сумму «~65» не пинить. После исправлений **нет CRITICAL** в серии. Checkpoint **NO_GO** (RT-001/002/003 OPEN).

Открытые / residual: HDX-LINT-01 PARTIAL; HD2-RL-02 BY-DESIGN; RT16-UNCOMMIT-01 (gate 1.1.0 не на origin/main); RT16-VIDEO-01 (чеклист ≠ mp4); непрогнанные комбо HD7-COMBO-01. RT16-MOEXP-01 / HD8-TOOL-01 **FIXED** (coverage schema 1.2.0; снапшот evidence не перегнан).

Закрыто в этом disposition: HD7-IDS-03 хвост; HD7-IFC-01 (не silent skip + mixed-parse harden); Dias + bSI baseline в alignment/сравнении. HD2-UP-01 и HD3-BFF-01 **не** открыты.
