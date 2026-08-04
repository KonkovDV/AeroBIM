---
title: "AECV publish framing — dual macro + MAPE + B.5"
date: 2026-08-04
status: active
version: "1.1.0"
claim_level: open_bench_only
closes_rt001: false
errata: >-
  v1.1: Table 1 is five-field (Space included). Headline = macro_extended 0.4325.
  Four-class 0.5064 is reference only — do not compare to Table 1.
---

# I.5 — Публикация метрики AECV

Источник: [`aecv-bench-eval-latest.json`](../evidence/aecv-bench-eval-latest.json) → `object_counting_live.summary`.  
Валидация скорера: [`aecv-scorer-validation-2026-08-04.md`](../evidence/aecv-scorer-validation-2026-08-04.md).

## Два macro (иерархия после errata)

| Ключ | Значение | Публиковать? |
|---|---:|---|
| **`macro_extended`** (= canonical `macro_exact_match_rate`) | **0.4325** | **Да** — 5 полей, сопоставимо с Table 1 / upstream `mean_accuracy` |
| `macro_bench_protocol` | 0.5064 | Справка — 4 класса (проза §3.1.1); **не** против Table 1 |

Округление для слайдов: **0.43** с оговоркой «five-field Table 1 metric».  
При засчёте 3 отказов как промахов: ≈ **0.422**.

**Запрещено:** сравнивать 0.5064 с Table 1 (0.51 Gemini) — это разные метрики в свою пользу.

## Сопоставление с Table 1 (одинаковая метрика)

| Модель | Mean EM (5 полей) |
|---|---:|
| Gemini 3 Pro (paper) | 0.51 |
| GPT-5.2 | 0.49 |
| **AeroBIM live `qwen3.6-35b-a3b` Yandex** | **0.4325** |
| Claude Opus 4.5 | 0.42 |
| GLM-4.6V (best open in paper) | 0.39 |

Выше Claude Opus 4.5 и открытых в выборке; ниже Gemini и GPT-5.2.  
Формулировка «порядка фронтирных» — защитима **без** притязания на первое место.

## MAPE

| Поле | mape (live) |
|---|---:|
| Door | 0.322 |
| Window | 0.365 |
| Bedroom | 0.128 |
| Toilet | 0.095 |
| Space | 0.294 |
| `macro_mape` (5-field) | 0.241 |

## Ворота B.5

1. Промпт дословно §3.1.2? (`prompt_verbatim` = PARTIAL)
2. Три отказа вендора: exclude (117 → 0.4325) vs miss (120 → ≈0.422)
3. OpenRouter/Cohere vs Yandex preprocess
4. Модель ≠ paper `Qwen3-VL-8B`
5. Headline только `macro_extended` против Table 1

## Разрешённая / запрещённая формулировка

**OK:** «Открытая модель через российское облако на публичном AECV-Bench достигает порядка фронтирных проприетарных систем на этой задаче (ниже Gemini/GPT-5.2, выше Claude Opus 4.5 и открытых в Table 1; five-field metric).»

**Forbidden:** «Мы обошли Gemini» · «точность AeroBIM = 0.51» · сравнение 4-классного live с Table 1 · закрытие RT-001.

`claim_level=open_bench_only`, `closes_rt001=false`, Checkpoint **NO_GO**.
