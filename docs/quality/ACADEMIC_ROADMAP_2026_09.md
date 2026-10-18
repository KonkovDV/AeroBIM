---
title: "Academic Roadmap — что доделать на академическом уровне"
status: active
version: "1.3.0"
last_updated: "2026-10-18"
claim_boundary: "Дорожная карта научного слоя. Checkpoint GO; customer_go false; RT-001/002/003 OPEN. Все числа — из артефактов; forbidden_wording действует и для статьи."
---

# Академическая дорожная карта и математический аппарат (2026)

Вопросы партнёру (не статья): [`../partners/CUSTOMER_QUESTIONS_GROUNDED_2026_09_03.md`](../partners/CUSTOMER_QUESTIONS_GROUNDED_2026_09_03.md).

## 0. Состояние на 18.10.2026

Инженерно-математический аппарат ниже уже в `main` и защищён CI. Это не закрытие RT и не `customer_go`.

- **Конформность IDS 1.0:** официальный набор buildingSMART IDS 1.0 (290 пар в `samples/ids/buildingsmart-testcases/`) прогоняется в CI (`scripts/run_ids_official_testsuite.py`), разделяя известные особенности `IfcTester` и намеренные закрытые расхождения AeroBIM (`BSI 0101` `ifcVersion`, `is_skipped` → `ERROR`).
- **Ядро IfcOpenShell / IfcTester / IfcClash 0.9:** переход на линейку `0.9` со сравнением `0.8.5` против `0.9.0.post1` на открытых моделях (`CC BY 4.0`, SHA-256 в `scripts/large_real_ifc_manifest.json`), открытием предфинальных `IFC4x3` / `ADD1` / `TC1` через `IFC4X3_ADD2` со сверкой числа SPF-сущностей (`IfcPreFinalSchemaError` при потере экземпляров) и сверкой `RocksDB` против SPF (`IfcRocksDbReconcileError`).
- **Локальная схема IDS 1.0 без выхода в сеть:** `ensure_ifctester_offline_schema()` и `load_offline_ids_schema()` (`xml_ids_document_auditor.py`) отображают базовые схемы W3C на локальные копии `xmlschema` при `allow="local"`, исключая сетевые обращения из `ifctester.ids.open`.
- **Калибровка вероятностных оценок:** в `compute_reliability_report.py` и `eval_statistics.py` наряду с равными по массе бинами ECE и доверительными интервалами Уилсона считается оценка Брайера $\text{BS} = \frac{1}{n}\sum_{i=1}^n (f_i - o_i)^2$ (`publishable=false` вне корпуса заказчика).
- **Трёхзначная логика воздержания на штампах 2D:** `stamp_dual_read.py` выдаёт `AGREED` только при совпадении нормализованного векторного слоя и OCR при $c_{\text{ocr}} \ge \tau_{\min}$; любое расхождение переводится в `ABSTAIN` или `NOT_VERIFIED` с маршрутизацией в HITL.
- **Репетиция протокола двух разметчиков:** `rt001_dual_rater_simulation.py` считает $\kappa$ Коэна, $\alpha$ Криппендорфа и устойчивый к дисбалансу классов коэффициент $\text{AC}_1$ Гвета на 28 единицах учебного комплекта (разметка двумя людьми `RT-001b` остаётся `OPEN`).
- **Десятичная полоса допуска и идентичность марок:** `measured_delta` и `within_epsilon` в `quantity.py`; сворачивание омоглифов марки стали и коротких списков стояков в `label_identity.py` и `target_ref.py`. Не коллизия систем.
- **Единица наблюдения сверки расчёта:** `element_id × section_id × parameter_id` в `calculation_table_compare.py`. Неполная или расходящаяся тройка даёт `observation_status=NOT_VERIFIED`. `MATCH` объявленных значений не становится корректностью расчёта. Безразмерная полоса идёт через `within_epsilon`, а не через двоичную разность.
- **Кривая воздержания:** `abstention_sweep.py` прогоняет сетку $\tau \in \{0.35, 0.45, 0.60, 0.75\}$ по учебному `drawing-advisory`. Доля `hitl_required` не убывает с ростом порога. ECE и Бриер не считаются: у фикстуры нет меток исхода. Это не прогон модели и не калибровка.
- **Ансамбль e-процессов под $H_0$:** `e_process_simulation.py`, фиксированный LCG, seed `20261018`. Неравенство Вилля ограничивает долю траекторий, пересёкших $1/\alpha$, а не одну траекторию. Наивное правило «$p < \alpha$ на любом шаге» тратит $\alpha$ на каждом шаге.
- **Таблицы рукописи и контракт обмена:** `manuscript_tables.py` печатает ячейку только если у пина `attested_by=ci` и непустой `claim_level` (генератор базовой линии пишет `claim_level=fixture_engineering`). `exchange_contract.py` (`1.0.0`) не выпускает находку без `finding_id` и `evidence_refs`, требует заметку на отказ / ложное срабатывание / уточнение и держит `writes_summary_passed=False`.

Остаются незакрытыми: E1 ручной таймер эксперта (`t_manual_s: null`), прогон модели VLM с метками исхода, E5 разметка двух людей (`n_labeled=0`; расчётный объём — не замер), подпись методолога на shortlist сверки расчёта и чистовая сборка текста препринта. `summary.passed` по-прежнему пишет только детерминированное ядро, а тома RT-001b/c, RT-002c, RT-003c открыты.

## 1. Фаза E — исполнение протоколов (каждый = число для статьи)

| # | Протокол готов | Прогон | Критерий приёмки | Блокер |
|---|---|---|---|---|
| E1 | Лабораторный до/после (чередование проходов) | `t_manual_s: null` — ручной «до»-проход | ≥1 полный комплект, обе ветви, журнал с хешем | человек + часы |
| E2 | Дефект-инъекция recall (`inject_defects`, seed 20260824) | **прогон 03.09 зафиксирован** (дом-5 0/6; mini-IFC 1/8; Wilson lower 0.000 / 0.022) | recall по классам + манифест в evidence | нет — **артефакт есть**, `synthetic_only`, RT-001 OPEN |
| E3 | Калибровка VLM-уверенности (`VLM_CONFIDENCE_TUNING_PROTOCOL_2026_09`) | сетка порогов на учебной фикстуре есть; прогона модели и меток исхода нет | доля HITL не убывает; ECE/Brier не публикуются без меток | нет модели в этом шаге; `t_manual_s` по-прежнему пуст |
| E4 | МГСУ предрегистрация | подпись/комплект от кафедры | письмо + комплект + протокол замечаний | внешняя сторона (письмо ушло) |
| E5 | Adjudication n≥30 (Wilson CI, κ/α) | расчётный объём есть; `n_labeled=0`, `study_executed=false` | n≥30, 2 судьи, holdout по объектам | **D1–D2 заказчика канала (08.09)** |
| E6 | Сверка расчётов: единица наблюдения (элемент × сечение × параметр) | тройка и `NOT_VERIFIED` в коде; shortlist 274 строк не размечен | методолог принимает единицу; код уже не выдаёт COMPLETE без тройки | подпись методолога, не движок |

## 2. Фаза P — сборка статьи (после E2/E3 можно начинать)

| # | Раздел | Источник (готово) | Что дописать |
|---|---|---|---|
| P1 | Вклад (contributions) | novelty-окна (verdict-neutrality доказуема, fail-closed к дрейфу, evidence-контракт, RU-контур) | заморозить 4 формулировки + границы |
| P2 | Related Work | ACADEMIC_LIT_REVIEW матрица (14 позиций вериф.) | секция EN + контраст с Iversen&Huang/Fuchs |
| P3 | Architecture | ADR-001/002, DeterminismGate, hybrid gate, state machine | систем-раздел с инвариантами |
| P4 | Evaluation | E1–E3 артефакты + AECV 0.43 (расхождение с авторами ≤0.02) + IFC-Bench 27/1026 + ПНСТ 18/22 | числа после прогонов |
| P5 | Limitations | honesty-серия как источник | «ограничения» как сила: NO_GO-механика |
| P6 | World precedent | CORENET X мандат, Китай CBIMS, Эстония реестр | введение/дискуссия |

## 3. Фаза M — мини-статья e-values (отдельный след)

`sequential_inference.py` (p→e калибровка Вовка-Ванга, e-process, Ville, safe testing) — самостоятельная публикация «Anytime-valid regression gating for research software CI»: проблема (family-wise error на T прогонов), метод, кейс AeroBIM. Не ждёт ничего, кроме времени на письмо.

## 4. Фаза X — внешняя валидация

- Независимая репродукция по REPRODUCIBILITY-2026 одним внешним прогоном (закрывает класс «все прогоны авторские»).
- МГСУ-препринт совместный после E4.
- Venue-план: arXiv preprint → студенческая/отраслевая конференция (после E5).

## 5. Математический и алгоритмический аппарат в коде

1. **Изоляция вердикта (ADR-001, `DeterminismGate`):**
   технический статус комплекта $V(\mathcal{P}) \in \{0, 1\}$ вычисляется исключительно детерминированным ядром по множеству фатальных находок $E_{\text{det}}$ и вектору обязательных возможностей $C_{\text{req}}$:

   $$
   V(\mathcal{P}) = \mathbb{I}\!\left(\lvert E_{\text{det}}\rvert = 0 \;\land\; \forall c \in C_{\text{req}}:\; \operatorname{state}(c) = \text{OK}\right).
   $$

   Выходы языковых и визуальных моделей $A_{\text{llm}}$ имеют атрибут `origin="advisory"` и структурно исключены из области определения $V(\mathcal{P})$.

2. **Трёхзначная логика Клини с воздержанием на штампах (`stamp_dual_read.py`):**
   пусть $\nu(x) = \operatorname{casefold}\!\bigl(\operatorname{strip}(\operatorname{NFKC}(x))\bigr)$ (с предварительной заменой `ё` на `е`). Для векторного чтения $t_{\text{vec}}$, OCR-чтения $t_{\text{ocr}}$ с оценкой $c_{\text{ocr}}$ и порога $\tau_{\min}$ ($\tau_{\min} = 0.5$ по умолчанию):

   $$
   \operatorname{status}(t_{\text{vec}}, t_{\text{ocr}}, c_{\text{ocr}}) = \begin{cases}
   \text{NOT\_VERIFIED}, & \nu(t_{\text{vec}}) = \varnothing \;\land\; \nu(t_{\text{ocr}}) = \varnothing, \\
   \text{ABSTAIN}, & \nu(t_{\text{vec}}) = \varnothing \;\lor\; \nu(t_{\text{ocr}}) = \varnothing \;\lor\; c_{\text{ocr}} < \tau_{\min} \;\lor\; \nu(t_{\text{vec}}) \ne \nu(t_{\text{ocr}}), \\
   \text{AGREED}, & \nu(t_{\text{vec}}) = \nu(t_{\text{ocr}}) \ne \varnothing \;\land\; c_{\text{ocr}} \ge \tau_{\min}.
   \end{cases}
   $$

   Любой исход кроме `AGREED` выставляет `requires_hitl = True`.

3. **Интервал Уилсона и точная биномиальная мощность (`study_design.py`, `plan_adjudication_corpus.py`):**
   для $k$ успехов из $n$ испытаний при $\hat{p} = k/n$ и $z = \Phi^{-1}(1 - \alpha/2)$ границы интервала Уилсона:

   $$
   p_{\pm} = \frac{\hat{p} + \frac{z^2}{2n} \pm z\sqrt{\frac{\hat{p}(1-\hat{p})}{n} + \frac{z^2}{4n^2}}}{1 + z^2/n}.
   $$

   Планирование объёма выборки экспертной разметки решает точную одностороннюю задачу $H_0: p \le p_0$ против $H_1: p > p_0$ через хвост биномиального распределения $\sum_{i=k_{\text{crit}}}^n \binom{n}{i} p^i (1-p)^{n-i}$ без нормальной аппроксимации ($n_{\text{power}} = 62$, $n_{\text{width}} = 111$, $\text{recommended\_n} = \max(n_{\text{power}}, n_{\text{width}}) = 111$).

4. **Калибровка вероятностных оценок: ECE и оценка Брайера (`compute_reliability_report.py`, `eval_statistics.py`):**
   на разбиении упорядоченных прогнозов на $K$ равных по массе бинов $B_1, \dots, B_K$:

   $$
   \text{ECE} = \sum_{m=1}^{K} \frac{\lvert B_m\rvert}{n}\,\bigl\lvert\operatorname{acc}(B_m) - \operatorname{conf}(B_m)\bigr\rvert, \qquad \text{BS} = \frac{1}{n}\sum_{i=1}^{n} (f_i - o_i)^2.
   $$

   При $n < 100$ или `corpus_kind != "customer"` отчёт получает `publishable = False`.

5. **Согласие экспертов при дисбалансе классов (`eval_statistics.py`, `measure_adjudicator_agreement.py`):**
   наряду с $\kappa$ Коэна и номинальной $\alpha$ Криппендорфа вычисляется $\text{AC}_1$ Гвета:

   $$
   \text{AC}_1 = \frac{p_o - p_e^{(\gamma)}}{1 - p_e^{(\gamma)}}, \qquad p_e^{(\gamma)} = \frac{1}{q - 1}\sum_{c=1}^{q} \bar{\pi}_c (1 - \bar{\pi}_c),
   $$

   что устраняет парадокс падения $\kappa$ при высокой доле доминирующего класса.

6. **Последовательный контроль регрессий в CI через e-процессы (`sequential_inference.py`):**
   односторонние перестановочные $p$-значения переводятся в $e$-значения калибратором Вовка–Ванга или безпараметрической смесью, а для ограниченных разностей $d_t \in [-1, 1]$ ($x_t = (d_t + 1)/2$) используется игровой мартингал усечённого aGRAPA:

   $$
   f_\kappa(p) = \kappa p^{\kappa - 1}, \qquad F(p) = \frac{1 - p + p\ln p}{p(\ln p)^2}, \qquad W_T = \prod_{t=1}^{T} \left(1 + \lambda_t \left(x_t - \tfrac{1}{2}\right)\right).
   $$

   По неравенству Вилля $\mathbb{P}_0(\sup_{t \ge 1} E_t \ge 1/\alpha) \le \alpha$ при произвольном числе проверок.

7. **Десятичная разность измерений и идентичность марок листа (`quantity.py`, `label_identity.py`):**
   для конечных измерений в пространстве СИ:

   $$
   \delta(a, b) = \operatorname{Decimal}(\operatorname{str}(a)) - \operatorname{Decimal}(\operatorname{str}(b)), \qquad \lvert\delta(a, b)\rvert \le \operatorname{Decimal}(\operatorname{str}(\varepsilon)).
   $$

   Так граница $1.1$ и $1.0$ при $\varepsilon = 0.1$ не рвётся на двоичном хвосте. Омоглифы кириллицы в марке стали сворачиваются к латинице; латинская `I` не сворачивается. Список `В2.7,8,9` и короткий диапазон `В2.4–В2.6` совпадают с одной маркой в `target_ref`. Размер решётки с `*` списком не является. Это идентичность подписи на шве комплекта, не вердикт коллизии систем.

8. **Единица наблюдения сверки расчёта (`calculation_table_compare.py`):**
   пусть $u(r) = (e, s, p)$ — непустые идентификаторы элемента, сечения и параметра строки $r$. Для пары строк одной `field_id`:

   $$
   \operatorname{observation}(r_c, r_b) = \begin{cases}
   \text{COMPLETE}, & u(r_c) = u(r_b) \ne \varnothing, \\
   \text{NOT\_VERIFIED}, & u(r_c) = \varnothing \;\lor\; u(r_b) = \varnothing \;\lor\; u(r_c) \ne u(r_b).
   \end{cases}
   $$

   Согласие объявленных чисел внутри десятичной полосы $\varepsilon$ остаётся отдельным `outcome`. `COMPLETE` не входит в $V(\mathcal{P})$ и не означает корректность расчёта.

9. **Монотонность воздержания (`abstention_sweep.py`):**
   для зафиксированного набора чтений индикатор маршрутизации в HITL не убывает с ростом порога $\tau$:

   $$
   \operatorname{hitl}(c, \tau) = \mathbb{I}\!\left(c < \tau \;\lor\; \neg\,\text{calibrated}\right), \qquad \tau_1 \le \tau_2 \implies \operatorname{hitl}(c, \tau_1) \le \operatorname{hitl}(c, \tau_2).
   $$

   Без меток исхода ECE и оценка Брайера не определяются.

10. **Ансамбль под нулём (`e_process_simulation.py`):**
    для неотрицательного супермартингала $E_t$ при $H_0$ неравенство Вилля и верхняя граница доли пересечений на ансамбле из $N$ траекторий с поправкой Хёффдинга ($\delta = 0.01$, $N = 400$):

    $$
    \mathbb{P}_0\!\left(\sup_{1 \le t \le T} E_t \ge \frac{1}{\alpha}\right) \le \alpha, \qquad \hat{r}_{\text{cross}} \le \min\!\left(1,\; \alpha + \sqrt{\frac{\ln(2/\delta)}{2N}}\right).
    $$

    Проверка — доля траекторий ансамбля, а не запрет пересечения на одном пути. Наивное правило $\exists t: p_t < \alpha$ такого ограничения не имеет.

11. **Цитируемая ячейка рукописи (`manuscript_tables.py`):**
    значение из пина $p$ попадает в таблицу Architecture или Evaluation тогда и только тогда, когда выполнены оба условия:

    $$
    \operatorname{citable}(p) = \mathbb{I}\!\left(\operatorname{attested\_by}(p) = \text{ci} \;\land\; \operatorname{claim\_level}(p) \in \Sigma^+ \setminus \mathcal{F}_{\text{forbidden}}\right).
    $$

    Иначе ячейка остаётся `withheld` и число не копируется.

## 6. Автономные модули, закрытые в репозитории

| Код | Что реализовано в репозитории | Проверка |
|---|---|---|
| `AI-E3-SWEEP` | Сетка $\tau \in \{0.35, 0.45, 0.60, 0.75\}$ на учебной фикстуре (`abstention_sweep.py`, `publishable=false`). ECE и Бриер без меток исхода не считаются | `test_hitl_rate_does_not_fall_as_the_floor_rises` |
| `AI-E6-CALC` | Тройка `element_id × section_id × parameter_id`, `NOT_VERIFIED` при неполноте и десятичная полоса в сверке таблиц. Дальше — shortlist и подпись методолога | `test_observation_unit_is_the_triple`; [`docs/calculation-evidence-boundary-2026.md`](../calculation-evidence-boundary-2026.md) |
| `AI-M1-EPROC` | Ансамбль под $H_0$ (`e_process_simulation.py`). Граница Вилля проверяется по доле пересечений на ансамбле | `test_crossing_rates_respect_the_ville_band` |
| `AI-P1-MANUSCRIPT` | Таблицы печатают ячейку только при `attested_by=ci` и непустом `claim_level`; генератор базовой линии пишет `claim_level=fixture_engineering` | `test_citable_cell_copies_the_pin_and_withheld_cells_do_not` |

## 7. Красные линии для статьи

- Формула публикации: «на замороженном наборе X при коммите Y получено Z» — никогда «точность продукта N%».
- `forbidden_wording` действует для статьи; fixture-метрики помечаются `fixture-only` (`publishable=false`).
- Checkpoint `GO` (`regulatory_measurement_mvp`), `customer_go=false` и открытые тома RT-001b/c, RT-002c, RT-003c отражаются в Limitations явно.
