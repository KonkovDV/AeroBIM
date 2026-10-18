---
title: "Academic Roadmap — что доделать на академическом уровне"
status: active
version: "1.1.0"
last_updated: "2026-10-18"
claim_boundary: "Дорожная карта научного слоя. Checkpoint GO; customer_go false; RT-001/002/003 OPEN. Все числа — из артефактов; forbidden_wording действует и для статьи."
---

# Академическая дорожная карта и план ИИ-исполнителя (SOTA 2026)

Вопросы партнёру (не статья): [`../partners/CUSTOMER_QUESTIONS_GROUNDED_2026_09_03.md`](../partners/CUSTOMER_QUESTIONS_GROUNDED_2026_09_03.md).

## 0. Диагноз (срез 18.10.2026): ядро SOTA-2026 в `main`, впереди эмпирические прогоны E1/E3/E5

Инженерно-математический аппарат в `main` закрыт и защищён CI:
- **SOTA-A1 (конформность IDS 1.0):** официальный набор buildingSMART IDS 1.0 (290 пар в `samples/ids/buildingsmart-testcases/`) гоняется в CI (`scripts/run_ids_official_testsuite.py`), разделяя известные особенности `IfcTester` и намеренные fail-closed расхождения AeroBIM (`BSI 0101` `ifcVersion`, `is_skipped` → `ERROR`).
- **SOTA-A2 (ядро IfcOpenShell / IfcTester / IfcClash 0.9):** миграция на линейку `0.9` с матричным сравнением `0.8.5` против `0.9.0.post1` на открытых моделях (`CC BY 4.0`, SHA-256 в `scripts/large_real_ifc_manifest.json`), открытием предфинальных `IFC4x3` / `ADD1` / `TC1` через `IFC4X3_ADD2` со сверкой числа SPF-сущностей (`IfcPreFinalSchemaError` при потере экземпляров) и сверкой `RocksDB` против SPF (`IfcRocksDbReconcileError`).
- **SOTA-A3 (нулевой сетевой выход XSD):** `ensure_ifctester_offline_schema()` и `load_offline_ids_schema()` (`xml_ids_document_auditor.py`) отображают базовые схемы W3C на локальные копии `xmlschema` при `allow="local"`, исключая сетевые обращения из `ifctester.ids.open`.
- **K2A-P1-03 (правила строгого оценивания калибровки):** в `compute_reliability_report.py` и `eval_statistics.py` наряду с равными по массе бинами ECE и доверительными интервалами Уилсона считается оценка Брайера $\text{BS} = \frac{1}{n}\sum_{i=1}^n (f_i - o_i)^2$ (`publishable=false` вне корпуса заказчика).
- **K2A-P1-04 (трёхзначная алгебра воздержания на штампах 2D):** `stamp_dual_read.py` выдаёт `AGREED` только при совпадении нормализованного векторного слоя и OCR при $c_{\text{ocr}} \ge \tau_{\min}$; любое расхождение переводится в `ABSTAIN` или `NOT_VERIFIED` с маршрутизацией в HITL.
- **RT-001b1 (репетиция протокола двух разметчиков):** `rt001_dual_rater_simulation.py` фиксирует $\kappa$ Коэна, $\alpha$ Криппендорфа и устойчивый к дисбалансу классов коэффициент $\text{AC}_1$ Гвета на 28 единицах учебного комплекта (`RT-001b2` на людях остаётся `OPEN`).

Остаются незакрытыми: E1 ручной таймер эксперта (`t_manual_s: null`), E3 прогон кривой воздержания VLM по сетке порогов на открытых листах, E5 разметка двух экспертов-людей $n \ge 30$ и чистовая сборка текста препринта.

## 1. Фаза E — исполнение протоколов (каждый = число для статьи)

| # | Протокол готов | Прогон | Критерий приёмки | Блокер |
|---|---|---|---|---|
| E1 | Лабораторный до/после (чередование проходов) | `t_manual_s: null` — ручной «до»-проход | ≥1 полный комплект, обе ветви, журнал с хешем | человек + часы |
| E2 | Дефект-инъекция recall (`inject_defects`, seed 20260824) | **прогон 03.09 зафиксирован** (дом-5 0/6; mini-IFC 1/8; Wilson lower 0.000 / 0.022) | recall по классам + манифест в evidence | нет — **артефакт есть**, `synthetic_only`, RT-001 OPEN |
| E3 | Калибровка VLM-уверенности (`VLM_CONFIDENCE_TUNING_PROTOCOL_2026_09`) | прогон по порогам не сделан | кривая abstention/hitl_required vs порог | нет |
| E4 | МГСУ предрегистрация | подпись/комплект от кафедры | письмо + комплект + протокол замечаний | внешняя сторона (письмо ушло) |
| E5 | Adjudication n≥30 (Wilson CI, κ/α) | 0 размеченных точек | n≥30, 2 судьи, holdout по объектам | **D1–D2 заказчика канала (08.09)** |
| E6 | Сверка расчётов: единица наблюдения (элемент/сечение/параметр) | решение не зафиксировано | решение методолога измерения + shortlist 274 строк в `calculation_table_compare` | слот методологической подписи |

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

## 5. Математический и алгоритмический аппарат в коде (справочник для статьи и ИИ)

1. **Изоляция вердикта (ADR-001, `DeterminismGate`):**
   технический статус комплекта $V(\mathcal{P}) \in \{0, 1\}$ вычисляется исключительно детерминированным ядром по множеству фатальных находок $E_{\text{det}}$ и вектору обязательных возможностей $C_{\text{req}}$:
   $$V(\mathcal{P}) = \mathbb{I}\!\left(|E_{\text{det}}| = 0 \;\land\; \forall c \in C_{\text{req}}:\; \text{state}(c) = \text{OK}\right).$$
   Выходы языковых и визуальных моделей $A_{\text{llm}}$ имеют атрибут `origin="advisory"` и структурно исключены из области определения $V(\mathcal{P})$.
2. **Трёхзначная логика Клини с воздержанием на штампах (`stamp_dual_read.py`):**
   пусть $\nu(x) = \text{casefold}(\text{NFKC}(x)[ё \mapsto е])$. Для векторного чтения $t_{\text{vec}}$, OCR-чтения $t_{\text{ocr}}$ с оценкой $c_{\text{ocr}}$ и порога $\tau_{\min}$:
   $$\text{status}(t_{\text{vec}}, t_{\text{ocr}}, c_{\text{ocr}}) = \begin{cases} \text{NOT\_VERIFIED}, & \nu(t_{\text{vec}}) = \varnothing \land \nu(t_{\text{ocr}}) = \varnothing, \\ \text{ABSTAIN}, & \nu(t_{\text{vec}}) = \varnothing \lor \nu(t_{\text{ocr}}) = \varnothing \lor c_{\text{ocr}} < \tau_{\min} \lor \nu(t_{\text{vec}}) \ne \nu(t_{\text{ocr}}), \\ \text{AGREED}, & \nu(t_{\text{vec}}) = \nu(t_{\text{ocr}}) \ne \varnothing \land c_{\text{ocr}} \ge \tau_{\min}. \end{cases}$$
   Любой исход кроме `AGREED` выставляет `requires_hitl = True`.
3. **Интервал Уилсона и точная биномиальная мощность (`study_design.py`):**
   для $k$ успехов из $n$ испытаний при $\hat{p} = k/n$ и $z = \Phi^{-1}(1 - \alpha/2)$ границы интервала Уилсона:
   $$p_{\pm} = \frac{\hat{p} + \frac{z^2}{2n} \pm z\sqrt{\frac{\hat{p}(1-\hat{p})}{n} + \frac{z^2}{4n^2}}}{1 + z^2/n}.$$
   Планирование объёма выборки экспертной разметки решает точную одностороннюю задачу $H_0: p \le p_0$ против $H_1: p > p_0$ через хвост биномиального распределения $\sum_{i=k_{\text{crit}}}^n \binom{n}{i} p^i (1-p)^{n-i}$ без нормальной аппроксимации.
4. **Калибровка вероятностных оценок: ECE и оценка Брайера (`compute_reliability_report.py`, `eval_statistics.py`):**
   на разбиении упорядоченных прогнозов на $K$ равных по массе бинов $B_1, \dots, B_K$:
   $$\text{ECE} = \sum_{m=1}^{K} \frac{|B_m|}{n}\,\bigl|\text{acc}(B_m) - \text{conf}(B_m)\bigr|, \qquad \text{BS} = \frac{1}{n}\sum_{i=1}^{n} (f_i - o_i)^2.$$
   При $n < 100$ или `corpus_kind != "customer"` отчёт получает `publishable = False`.
5. **Согласие экспертов при дисбалансе классов (`eval_statistics.py`, `measure_adjudicator_agreement.py`):**
   наряду с $\kappa$ Коэна и номинальной $\alpha$ Криппендорфа вычисляется $\text{AC}_1$ Гвета:
   $$\text{AC}_1 = \frac{p_o - p_e^{(\gamma)}}{1 - p_e^{(\gamma)}}, \qquad p_e^{(\gamma)} = \frac{1}{q - 1}\sum_{c=1}^{q} \bar{\pi}_c (1 - \bar{\pi}_c),$$
   что устраняет парадокс падения $\kappa$ при высокой доле доминирующего класса.
6. **Последовательный контроль регрессий в CI через e-процессы (`sequential_inference.py`):**
   односторонние перестановочные $p$-значения переводятся в $e$-значения калибратором Вовка–Ванга $f_\kappa(p) = \kappa p^{\kappa - 1}$ или безпараметрической смесью $F(p) = \frac{1 - p + p\ln p}{p(\ln p)^2}$, а для ограниченных разностей $d_t \in [-1, 1]$ используется игровой мартингал усечённого aGRAPA $W_T = \prod_{t=1}^T (1 + \lambda_t (x_t - \tfrac{1}{2}))$. По неравенству Вилля $\mathbb{P}_0(\sup_{t \ge 1} E_t \ge 1/\alpha) \le \alpha$ при произвольном числе проверок.

## 6. Очередь автономных задач для ИИ-исполнителя (без внешних блокеров)

| Код задачи | Что делает ИИ-исполнитель в репозитории | Выходной артефакт и проверка |
|---|---|---|
| `AI-E3-SWEEP` | Прогон сетки порогов $\tau \in \{0.35, 0.45, 0.60, 0.75\}$ на открытых фикстурах чертежей с выгрузкой кривой `hitl_required` против доли отсева и таблиц ECE/Brier (`fixture_only`, `publishable=false`) | JSON/MD в `docs/evidence/` + unit-тест инварианта монотонности доли `hitl_required` по $\tau$ |
| `AI-E6-CALC` | Формализация единицы наблюдения в `calculation_table_compare` (элемент × сечение × параметр) с явной отметкой `NOT_VERIFIED` при неполной тройке | Доменный тест + обновление `docs/calculation-evidence-boundary-2026.md` |
| `AI-M1-EPROC` | Автономный воспроизводимый скрипт симуляции траекторий $E_t$ (калибратор Вовка–Ванга vs усечённый aGRAPA vs наивный фиксированный $\alpha$) для раздела Evaluation мини-статьи Фазы M | Детерминированный отчёт с фиксированным seed + тест сохранения границы $\sup_t E_t < 1/\alpha$ при $H_0$ |
| `AI-P1-MANUSCRIPT` | Сборка воспроизводимых таблиц LaTeX/Markdown для разделов Architecture и Evaluation строго из JSON-пинов в `docs/evidence/` без ручного копирования чисел | Скрипт-генератор таблиц с проверкой `attested_by` и `claim_level` |

## 7. Красные линии для статьи и ИИ-исполнителя

- Формула публикации: «на замороженном наборе X при коммите Y получено Z» — никогда «точность продукта N%».
- `forbidden_wording` действует для статьи; fixture-метрики помечаются `fixture-only` (`publishable=false`).
- Checkpoint `GO` (`regulatory_measurement_mvp`), `customer_go=false` и открытые тома RT-001b/c, RT-002c, RT-003c отражаются в Limitations явно.
