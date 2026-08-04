---
title: "AECV publish framing — dual macro + MAPE + B.5"
date: 2026-08-04
status: active
version: "1.0.0"
claim_level: open_bench_only
closes_rt001: false
---

# I.5 — Публикация метрики AECV

Источник чисел: [`docs/evidence/aecv-bench-eval-latest.json`](../evidence/aecv-bench-eval-latest.json) → `object_counting_live.summary` / `executive_summary.live`.  
Доказательство харнесса: [`aecv-scorer-validation-2026-08-04.md`](../evidence/aecv-scorer-validation-2026-08-04.md).

## Два macro (обязательно оба)

| Ключ | Значение | Публиковать? |
|---|---:|---|
| **`macro_bench_protocol`** (= canonical `macro_exact_match_rate`) | **0.5064** | **Да** — 4 класса (проза статьи / live headline) |
| `macro_extended` | 0.4325 | Внутренний / Table 1 alignment (5 полей, как upstream visualizer) |

Округление для слайдов: **0.507** / **0.51** с оговоркой «four-class protocol» **и** воротами B.5.

**Не смешивать ключи:** опубликованные Table 1 means совпадают с `macro_extended` (max \|Δ\|≤0.02), не с четырёхклассовым protocol у чужих моделей.

## MAPE (вторая метрика статьи)

| Поле | mape (live) |
|---|---:|
| Door | 0.322 |
| Window | 0.365 |
| Bedroom | 0.128 |
| Toilet | 0.095 |
| Space (не в paper mean) | 0.294 |
| `macro_mape` (5-field mean in artifact) | 0.241 |

Для сопоставления с Table 2 статьи считать среднее **по четырём** классам:  
`(0.322+0.365+0.128+0.095)/4 ≈ **0.227**` → зафиксировано ниже как `mape_bench_protocol`.

## Сопоставление (только после B.5)

| Модель | Mean EM (4 класса) |
|---|---:|
| Gemini 3 Pro (paper) | 0.51 |
| AeroBIM live `qwen3.6-35b-a3b` Yandex | **0.507** |
| GPT-5.2 | 0.49 |
| Claude Opus 4.5 | 0.42 |
| GLM-4.6V (best open in paper) | 0.39 |

## Ворота B.5 (до публичной таблицы)

1. Промпт дословно §3.1.2 статьи? (`prompt_verbatim` = PARTIAL until checked)
2. Три error-плана: exclude (117) vs miss (120 → ~0.494)?
3. OpenRouter/Cohere vs Yandex preprocess?
4. Модель ≠ paper `Qwen3-VL-8B`.
5. Не смешивать `macro_bench_protocol` (headline) с Table 1 row, выровненной по `macro_extended`.

## Разрешённая / запрещённая формулировка

**OK:** «Открытая модель, доступная через российское облако, достигает уровня фронтирных проприетарных систем на этой задаче (open bench, 4 класса).»

**Forbidden:** «Мы обошли Gemini» · «точность AeroBIM = 0.51» · закрытие RT-001.

`claim_level=open_bench_only`, `closes_rt001=false`, Checkpoint **NO_GO**.
