---
title: "Red Team Hyper-Deep Round 4 — academic level: invariants, statistics, bibliography, cryptography"
status: active
version: "1.0.0"
last_updated: "2026-08-16"
claim_boundary: "Audit report plus later remediations. Checkpoint stays NO_GO. Round 4 of HD-series (IDs HD4-*): formal and numerical verification of the claims the code makes about itself."
audited_head: "2768058 (committed) + uncommitted working tree 2026-08-16"
auditor: "ZCode autonomous triage, round 4 (solo)"
---

# Red Team Hyper-Deep Round 4 — академический уровень

Четвёртый проход меняет оптику: не «найти баг», а **проверить утверждения кода о самом себе** — формальные инварианты, статистическую математику, библиографию, криптографию приватности. Метод: перечисление писателей состояний, численное воспроизведение заявленных чисел, сверка формул с первоисточниками, инвентаризация цитирований.

**Сквозной вывод раунда 4:** академическая дисциплина проекта — **подлинная и проверяемая**. Формула Вильсона совпадает с учебной до знака; заявленное «n=111» численно воспроизводится из кода; инвариант «advisory не пишет ERROR» подтверждён полным перечислением; errata-дисциплина цитирований реально исполнена. Remediation (1.6.25): leak-scan JSON-атомы + документированный порог; TokenVault LRU; `lint_citation_twins`; граница доказательства INV-02 в docstring. Checkpoint **NO_GO**.

---

## 1. Реестр находок

| ID | Sev | Зона | Объект | Суть | Статус |
|---|---|---|---|---|---|
| HD4-INV-01 | OK-CONFIRM | вердикт | 73 сайта `Severity.ERROR` | Полное перечисление: ни один advisory/LLM/VLM-адаптер не конструирует ERROR — инвариант «advisory не флипает вердикт» подтверждён на уровне писателей | OK-CONFIRM |
| HD4-INV-02 | INFO | вердикт | конвенция vs тип | Инвариант обеспечивается дисциплиной конструирования и DeterminismGate, не системой типов; путь десериализации (чтение отчёта из стора) полагается на integrity-hash | DOCUMENTED |
| HD4-STAT-01 | OK-CONFIRM | статистика | `study_design.py:66-90` | Формула Вильсона — точное совпадение с Wilson 1927 (center/spread форма, z через `NormalDist().inv_cdf`, clamp [0,1], `point=p̂`) | OK-CONFIRM |
| HD4-STAT-02 | OK-CONFIRM | статистика | `required_n_for_wilson_halfwidth` | Численно воспроизведено: `required_n(0.60, hw=0.09) = 111` — заявленное в доках «recommended_n=111 for interim 0.60» **ровно** совпадает с выводом кода | OK-CONFIRM (регресс-тест) |
| HD4-STAT-03 | OK-CONFIRM | статистика | `eval_statistics.py` TOST | Эквивалентность fail-closed по CI-inclusion (Berger & Hsu 1996): `equivalent=True` только когда интервал целиком в (−margin, +margin) — корректная форма TOST | OK-CONFIRM |
| HD4-CIT-01 | OK-CONFIRM | библиография | `docs/research/CITATION_ERRATA_2026_08_04.md` | Фабрикованный DOI `10.1016/j.aei.2026.103676` (twin-паттерн с 2025) помечен FABRICATED с приказом «Delete everywhere» — и действительно удалён везде, кроме самих errata-доков (audit trail). Дисциплина исполнена | OK-CONFIRM |
| HD4-CIT-02 | LOW | библиография | вся дерево цитат | 25+ уникальных DOI/arXiv; верификация ручная (errata-доки), машинной проверки twin-паттернов/404 нет — рецидив возможен | FIXED (`lint_citation_twins`) |
| HD4-PG-01 | OK-CONFIRM | криптография | `privacy_guard.py` HMAC | Length-prefixed HMAC-SHA256 domain separation (tenant, kind, value) — корректно устраняет delimiter-collision; per-tenant unlinkability при общем salt | OK-CONFIRM |
| HD4-PG-02 | LOW | приватность | leak-scan | `str(value)` vs JSON-сериализация — bool/None регистр-мисс; порог `len>=3` не документирован | FIXED |
| HD4-PG-03 | LOW | жизненный цикл | TokenVault | TokenVault растёт без предела на процесс (каждый tokenize — навсегда в памяти) — тот же класс, что HD3-IFC-01 | FIXED (LRU 4096/tenant) |
| HD4-IFCV-01 | OK-CONFIRM | IFC-движок | `ifc_open_shell_validator.py:106-110` | Отказ извлечения unit-scale → **ERROR** («numeric comparisons cannot be trusted») — числовой контур fail-closed на уровне движка | OK-CONFIRM |

---

## 2. Формальный анализ инвариантов

### 2.1 Инвариант «advisory не пишет ERROR» (HD4-INV-01)

Метод: полное перечисление. `grep severity=Severity.ERROR` по `src/` → **73 сайта записи** в 20 файлах: package_completeness (11), egrz_intake_xml_checks (10), xml_ids_document_auditor (9), signature_audit_runner (8), basic_ifc_schema_validator (6), ids_compliance_runner (6), ifc_open_shell_validator (5), analyze_orchestrators (5 — intake/hard-gate), ingestion (4), mep_scope_probe (4), clash_detection_runner (4)… **Ноль** в `llm_*`, `vlm_*`, `remark_*`, `hybrid_drawing_*`, `agent_*`. Вместе с DeterminismGate (демоция advisory-only → INFO, `determinism_gate.py:131`) и precedence-решёткой outcome (`package_outcome.py:47-55`) инвариант выполняется по всем конструктивным путям.

### 2.2 Граница доказательства (HD4-INV-02)

Инвариант — конвенция конструирования, не ограничение типа: ничто в `ValidationIssue` не запрещает severity=ERROR из advisory-источника архитектурно. Держат его: (а) дисциплина кода, (б) gate-демоция на слиянии, (в) mutation-тесты. Отдельная граница — **десериализация**: `_reconstruct_issue` (filesystem store) восстанавливает severity из JSON; защита от подмены — content-hash integrity-verify (RTATOM-G11), т.е. крипто-, не типо-граница. Для академической записи корректная формулировка: «инвариант выполняется на всех путях конструирования в текущем коде и защищён тестами; формальной изоляции типов нет». Направление (долго): `NewType`/фабрика `AdvisoryIssue` без поля severity=ERROR.

### 2.3 Решётка исходов

`FAILED ≻ BLOCKED ≻ REVIEW_REQUIRED ≻ PASS_WITH_WARNINGS ≻ PASS` — проверена на монотонность: нарушение поглощает неопределённость (`error_count>0` доминирует над `hitl`), неполнота не даёт PASS (`capability_blocked` при нулевых ошибках). Отсутствует путь ослабления исхода при добавлении данных — только ужесточение. Формально: outcome-функция монотонна по информационному порядку. Соответствие внешней модели (four-state contract, Mushkani et al. arXiv:2607.29058) — заявлено в docstring; локально непроверяемо, внешний источник в дереве цитируется консистентно.

## 3. Статистическая верификация

1. **Вильсон, формула** (`study_design.py:66-90`): `center=(p̂+z²/2n)/(1+z²/n)`, `spread=(z/(1+z²/n))·√(p̂(1−p̂)/n+z²/4n²)` — в точности Wilson 1927; z точный (`inv_cdf`), clamp консервативен, `point=p̂` (не center) — корректный выбор точечной оценки. Планировщик (`:93-113`) — детерминированный линейный поиск с округлённым k и капом; честно документирован как «planning variant».
2. **Числовое воспроизведение заявки**: прогон кода даёт `wilson(0.60, n=111).half_width = 0.0895` и `required_n(0.60, hw=0.09) = 111`. Документированное «recommended_n=111 for interim 0.60 @ expected 0.75» — **воспроизводится в точности** (при expected 0.75 тот же hw=0.09 требует n=87; выбор n по консервативному 0.60 — корректен методологически: планирование по нижней границе).
3. **TOST** (`eval_statistics.py:424-426,485`): CI-inclusion-форма (Berger & Hsu 1996; Lakens 2017 90%-CI при α=0.05 упомянут) с fail-closed `equivalent`. Точный бином через `math.comb` (`:116-126`) — корректно, без нормальной аппроксимации.
4. **Bootstrap percentile CI** (`:58`) — кластерная структура учитывается (`n_clusters`-гейт, `:70`). Методологически зрело.

Замечание (не находка): точность `half_width` округляется только на экспорте (`round(...,6)` в `as_dict`), вычисления в full precision — правильно.

## 4. Библиографический аудит

Инвентаризация: **25+ уникальных** идентификаторов (arXiv: 2601.04819 ×19, 2603.29199 ×12, 2607.29058 ×8, 2605.01698 ×8, 2605.22079 ×6, 2605.30794 ×5, …; DOI: zenodo.19722012 ×6, icdmw69685.2025.00203, autcon.2015.03.003, buildings16040719, aei.2025.103676…). Ключевые проверки:

- **Twin-паттерн** `aei.2025.103676` vs `aei.2026.103676`: errata от 04.08 квалифицировала 2026-вариант как FABRICATED (Crossref 404; «Elsevier article numbers are not reused across years with a year-digit edit») с приказом удалить везде. Проверка деревом: живой **только** внутри трёх errata/verification-доков как audit-trail. **Дисциплина исполнена** (HD4-CIT-01).
- Остаточный риск (HD4-CIT-02): верификация цитат — ручной процесс с человеческой errata; машинного линта (twin-детект по DOI-цифрам, контроль формата arXiv-ID) нет. Twin-паттерн — типичный LLM-артефакт, а проект активно использует LLM при написании доков → рецидив вероятен. Дешёвое направление: скрипт-линк в CI.
- Согласованность: AEC-Bench `2603.29199` цитируется одинаково (196-инвентарь) в README и docs; Mushkani `2607.29058` — в docstring `package_outcome.py` и docs синхронно.

## 5. Криптографический разбор PrivacyGuard

`domain/hybrid/privacy_guard.py` (прочитан полностью, 189 строк):

- **Конструкция токенов** (`:116-129`): HMAC-SHA256(salt) с 8-байтовым length-prefix каждого компонента (tenant, kind, value) — корректная domain separation, устраняющая delimiter-shift коллизии; 32-hex (128 бит) усечение с collision-детекцией в vault (`:80-82`) — обоснованный баланс. Свойство «unlinkable across tenants, joinable within tenant» **следует из конструкции** (tenant входит в MAC-вход при общем salt) — docstring честен.
- **Fail-closed политика полей** (`:158`): `rules.get(key, "remove")` — не перечисленное утекать не может; `keep` на вложенных контейнерах запрещён (`:160-162`) — защита от контрабанды полей.
- **Residual-leak скан** (`:52-57`): сериализует masked-JSON и ищет сырое значение как подстроку. Краевые случаи (HD4-PG-02): `str(True)="True"` vs JSON `"true"` — регистровый мисс для нестроковых типов; порог `len≥3` не документирован (тривиальные значения типа «А1» не проверяются осознанно, но молча). Для строковых полей (основной кейс) скан корректен.
- **TokenVault** (`:71-86`): in-memory, без эвикции — бесконечный рост на процесс (HD4-PG-03), тот же ресурсный класс, что IFC-кэш (HD3-IFC-01). Restore — per-tenant, неправильный тенант → None. Salt в payload не входит. Соответствует заявленному «masking ≠ anonymity».

## 6. Ядро IFC-движка (карта + целевые срезы)

`ifc_open_shell_validator.py` (420 строк, структурная карта + срезы severity): unit-scale extraction failure → **ERROR** с честным текстом «numeric comparisons cannot be trusted» (:106-110) — движковый fail-closed для числового контура; property/quantity ошибки — ERROR/WARNING по семантике; `_fast_guid_lookup`/`_get_element_psets` с кэш-ключами; исключения в per-element циклах локализованы (`noqa` с обоснованием). Построчное чтение 420 строк не выполнялось (residual), но severity-срез и fail-closed точки проверены.

## 7. Сводка четырёх раундов (финальная матрица)

| Измерение | Раунд | Вердикт |
|---|---|---|
| Вердикт-честность (бизнес) | 1 | образцово |
| Вердикт-честность (парсеры) | 3 | швы: HD3-IDS-01, HD3-CLASH-01 |
| Security-периметр | 1–2 | сильно; остатки — proxy-env, datastore-pin, middleware-порядок |
| Конкурентность/жизненный цикл | 2–4 | слабейшее измерение: DI-lock, JWKS-ротация, quota-race, IFC-кэш, TokenVault, stale-локи |
| Воспроизводимость | 2 | HD2-RM-01 (origin-фильтр) |
| Статистика/методология | 4 | **подлинная**: формулы точны, числа воспроизводятся |
| Библиография/errata | 4 | дисциплина исполнена; линта нет |
| Криптография приватности | 4 | конструкция корректна; краевые случаи leak-scan |
| Docs/claims | 1 | guard=README-only, RU-маркеры, drift чисел |

**Академическое резюме:** это редкий случай, когда академические заявления кода (формулы, цитаты, инварианты, крипто-свойства) выдерживают независимую проверку. Слабости — не в заявленном, а в незаявленном: ресурсные пределы, конкурентные сценарии, устойчивость к дрейфу форматов внешних движков.

## 8. Residual после четырёх раундов

Непрочитано построчно: `ifc_open_shell_validator.py` полный, `core/simple_pdf.py`, `report_html.py` макро-логика, postgres-стор SQL-слой, VLM-адаптеры (`region_restricted_vlm_pipeline`, `vlm_drawing_pipeline`), `App.tsx` целиком, ~290 тест-файлов, внешняя верификация цитат (WebSearch не выполнялся — среда). Пятый проход при необходимости: VLM-пайплайны + postgres + полный IFC-валидатор.
