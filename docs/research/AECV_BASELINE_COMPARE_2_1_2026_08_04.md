---
title: "Исследовательский отчёт AeroBIM — вопрос 2.1 и аудит цитирования"
date: 2026-08-04
status: verified_analysis
version: "1.1.0"
claim_boundary: >-
  Сопоставление с опубликованными базовыми результатами. Не точность продукта,
  не закрытие RT-001. Checkpoint остаётся NO_GO. Публичное сравнение — только после
  ворот сопоставимости B.5.
---

# Отчёт: базовые результаты AECV-Bench и аудит библиографии

> Landed into repo from operator analysis 2026-08-04. Cross-checked against
> `SOURCE_VERIFICATION_REPORT_2026_08_04.md` (same session). Part D below is
> **amended** where that pass already verified items.

## Часть A — Аудит цитирования

### A.1. Коллизия DOI — разрешена

| Ссылка | Статус | Установлено |
|---|---|---|
| `10.1016/j.aei.2025.103676`, если приписан чужому названию («…code checking in AEC» / bridge VLM) | **PARTIAL** | DOI существует: Shi/Solihin/Yeoh, *Fine-tuning a large language model for automated code compliance of building regulations*, AEI 68(B), Nov 2025, BuildThemis. Исправить title/authors |
| `10.1016/j.aei.2026.103676` | **FABRICATED** | Crossref 404; номер 103676 занят 2025. Удалить |

**Действие:** внешний `research.md` (не в git) — поправить первую, удалить вторую.  
**Вывод:** смешанный корпус опаснее полностью фиктивного.

### A.2. Полнота

На 17.07.2026 обзор без AECV-Bench / AEC-Bench / BRAVO / MechVQA — неполон.

---

## Часть B — Вопрос 2.1

### B.1. Источник

Kondratenko et al., AECV-Bench, arXiv:2601.04819. **VERIFIED** (полный PDF).

### B.2. Метрика vs протокол бенчмарка

Статья оценивает **4** класса: Door, Window, Bedroom, Toilet (§3.1.1).  
Spaces упоминаются в промпте, **не** входят в Tables 1–2.

AeroBIM live усреднял **5** полей → macro_extended **0.4325**.  
По протоколу бенчмарка:

`macro_bench_protocol = (0.231+0.137+0.846+0.812)/4 = 0.5065`

В evidence: `executive_summary.live.macro_bench_protocol` / `macro_extended`.

### B.3. Сопоставление (внутреннее до закрытия B.5)

| Модель | Mean (4 класса) |
|---|---:|
| Gemini 3 Pro (paper) | 0.51 |
| **AeroBIM live Qwen 3.6-35b Yandex** | **0.507** |
| GPT-5.2 | 0.49 |
| Claude Opus 4.5 | 0.42 |
| GLM-4.6V (best open in paper) | 0.39 |

**Модель или харнесс?** Харнесс корректен на уровне протокола оценки. 0.507 в одном ряду с фронтиром paper; не «сломанный scorer». Формулировка: *более новая открытая модель через РФ-облако достигает порядка лучших проприетарных в Table 1* — **не** «мы обошли Gemini».

MAPE уже в `per_field` (Window 0.365 ≈ 36.5%).

### B.4. Градиент

Совпадает со статьёй: Bedroom/Toilet ≫ Door/Window. Window mean_bias **−2.58**.

### B.5. Ворота сопоставимости (до публичной таблицы)

1. Промпт дословно §3.1.2?  
2. 3 error plans: exclude vs miss → ~0.494 если miss.  
3. OpenRouter/Cohere vs Yandex preprocess.  
4. Модель ≠ paper `Qwen3-VL-8B`.

### B.6. Формулировка для КТ#2 (после B.5)

> На открытом бенчмарке AECV-Bench (arXiv:2601.04819) открытая модель через российское облако показывает средний exact-match **0.51** (4 класса) — порядок лучших проприетарных систем авторов бенчмарка. Это характеристика модели на публичном корпусе, **не** точность AeroBIM: нет материалов заказчика, нет междокументной сверки; **не** закрывает RT-001. `claim_level=open_bench_only`.

---

## Часть C — Позиционирование из статьи

**C.1** §4.2: symbol counting unreliable without human supervision → слайд «видит ≠ проверяет».  
**C.2** §4.3: vendors rarely publish transparent protocols → против «>90%» без методики.  
**C.3** §6 limits: 120 public plans, raster only, no cross-sheet → цитата в `OPEN_BENCH_VS_RT001_DECISION` (почему L1 ≠ RT-001).

---

## Часть D — Статус остальных вопросов (сверка с verification pass)

| Вопрос | В исходном черновике | После pass `cac5eb5` / этот commit |
|---|---|---|
| 2.2 разрешение | не исследован | измерен in-repo (токены); литература stamp-px **UNVERIFIED** |
| 2.3 LLM→IDS | BuildThemis meta only | Perov DOI **VERIFIED** Crossref; полный текст Perov **не** читан здесь |
| 2.4–2.6, 2.8 | не исследован | без изменений (UNVERIFIED / vendor) |
| 2.7 регуляторика | «не исследован» | **частично VERIFIED**: ПП 331 (Garant), 243-ФЗ (pravo); реестр+foreign weights **PARTIAL** |
| Structured AI $4.2M | «не проверен» | **VERIFIED** (getstructured.ai 2026-06-11 + ENR) |

---

## Источники

- AECV-Bench arXiv:2601.04819 — полный текст. **VERIFIED**
- Shi/Solihin/Yeoh AEI 68 103676 — метаданные. **VERIFIED** (title must match)
- AEC-Bench / MechVQA / BRAVO — **VERIFIED** (operator + ids)
- CubiCasa5K / CVC-FP — **PARTIAL** (via AECV citations)
