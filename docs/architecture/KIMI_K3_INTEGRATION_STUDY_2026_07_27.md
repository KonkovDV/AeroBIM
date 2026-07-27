---
title: "Kimi K3 — исследование и дизайн подключения к AeroBIM (advisory-контур)"
status: study
version: "1.0.0"
last_updated: "2026-07-27"
claim_boundary: "Kimi K3 — кандидат в AI_ADVISORY контур: VLM/reasoning как вспомогательный слой. Никогда не выставляет summary.passed (ADR-001, DeterminismGate). Никаких заявлений точности до размеченного корпуса (RT-001). Не критерий приёмки MVP."
tags: [aerobim, kimi-k3, vlm, advisory, moonshot, integration, study]
---

# Kimi K3 → AeroBIM: что это и как подключать

Полная сценарная матрица «от и до» по требованиям Самолёта (ТР-3..24 + 20 типовых
ошибок): [`KIMI_K3_SCENARIO_MATRIX_2026_07_27.md`](KIMI_K3_SCENARIO_MATRIX_2026_07_27.md).

Исследование выхода **Kimi K3** (Moonshot AI, анонс 16.07.2026, веса — 27.07.2026)
и дизайн интеграции в AeroBIM строго в контур `AI_ADVISORY`. Документ — study/design,
**не** capability claim и **не** реализация. Привязан к реальным швам кода
(`MultimodalDrawingPipeline`, `AdvisoryToolContract`, `outbound_url`) и к
[`../pilot/VLM_OCR_COMPARISON_PROTOCOL_2026_08.md`](../pilot/VLM_OCR_COMPARISON_PROTOCOL_2026_08.md).

## 1. Верифицированные факты (с источниками)

| Свойство | Значение | Источник (дата) |
|---|---|---|
| Разработчик / тип | Moonshot AI; мультимодальная reasoning-модель | kimi.com/blog/kimi-k3 (16.07) |
| Параметры / MoE | 2.8T total; активны 16 из 896 экспертов (Stable LatentMoE) | офиц. блог |
| Архитектура | Kimi Delta Attention (KDA) + Attention Residuals; MXFP4 веса / MXFP8 активации (QAT) | офиц. блог |
| Контекст | 1 048 576 токенов (1M) | офиц. блог / northflank |
| Вход | текст + изображения (подтверждено API); видео — в продуктах Kimi | northflank (незав. тест) |
| API | OpenAI-совместимый; `kimi-k3`; $0.30 cache-in / $3 in / $15 out за MTok | офиц. блог |
| Веса | ~1.4 ТБ (MXFP4), live на HuggingFace с 00:00 UTC 27.07.2026 | HF blog / AI Weekly (27.07) |
| Железо (prod) | supernode **64+ ускорителей**; min-конфиг НЕ опубликован; vLLM + KDA prefill cache | northflank (17.07) |
| Мультимодальные бенчи | PerceptionBench, MMMU-Pro, ZeroBench, **OfficeQA Pro** (PDF как изображения, без machine-readable текста) | офиц. блог footnotes |
| Известные лимитации | max reasoning effort по умолчанию (латентность/стоимость); **«excessive proactiveness»** (решает за пользователя); чувствительность к thinking-history | офиц. блог §Limitations |

## 2. НЕ верифицировано / противоречиво (не заявлять как факт)

- **Лицензия**: источники расходятся — «Modified MIT» (enterprisedna, 27.07) vs
  «изменилась» (roo.beehiiv) vs «не указана» (howaiworks). **Требование:**
  прочитать реальный `LICENSE` в HF-репозитории до любого self-host/редистрибуции;
  до этого статус — `VERIFY_WITH_SOURCE`.
- **Точность на инженерных чертежах** — не измерена нами; общие бенчи ≠ доменное
  качество. Enginuity/SeePhys показывают, что frontier-VLM перефразируют
  обозначения и <60% на структурных диаграммах (см. протокол §Академические якоря).
- **Минимальное жизнеспособное железо** — Moonshot не опубликовал; 64+ —
  рекомендация prod, не минимум.

## 3. Почему это релевантно AeroBIM

1. **Native vision + OfficeQA Pro** (PDF рендерятся как изображения) — ровно наш
   кейс: растровые чертежи/сканы/штампы/спецификации (задачи T1–T4 протокола).
2. **1M контекст** — потенциально весь комплект ПД/РД в одном запросе (но дорого:
   §6 — использовать retrieval, не full-dump).
3. Kimi уже заявлен кандидатом в [протоколе VLM/OCR](../pilot/VLM_OCR_COMPARISON_PROTOCOL_2026_08.md);
   моё исследование **подтвердило** его caveat: 2.8T MoE вне пилотного железа.

## 4. Жёсткие ограничения AeroBIM (не подлежат обходу)

| Ограничение | Как применяется к K3 |
|---|---|
| **ADR-001 / DeterminismGate** | K3 — только `AI_ADVISORY`; `origin="advisory"`; **никогда** не флипает `summary.passed`; при расхождении AI↔движок побеждает движок |
| **`AdvisoryToolContract`** | контракт жёстко поднимает `ValueError`, если `can_change_verdict=True`; K3-инструмент регистрируется с `can_change_verdict=False`, `evidence_required=True`, `timeout`, `max_steps`, allowlist по tenant |
| **Claims Lock** | запрещено «AI читает чертежи как инженер»; результаты — fixture-only до корпуса (RT-001) |
| **Закрытый контур (NDA Самолёта)** | данные заказчика **не** уходят в публичный API; см. §5 tiers |
| **SSRF-гард** | любой outbound в Kimi API — через `assert_safe_outbound_url` + `safe_urlopen` (публичный хост проходит; редиректы/приватные IP блокируются) |
| **Advisory grounding** | вывод K3 маппится на `DrawingRegionRef`/`ProblemZone` с `confidence`; сырой текст VLM не идёт в правило без нормализации (Enginuity: paraphrase divergence) |

## 5. Варианты развёртывания (tiers) и блокер закрытого контура

| Tier | Данные | Развёртывание | Статус |
|---|---|---|---|
| A. Dev / fixture / open | Не-NDA (`samples/`) | Kimi API (OpenAI-совм.) через SSRF-гард | **Допустимо** — для бенчей VLM/OCR |
| B. On-prem full K3 | NDA заказчика | self-host весов (64+ ускорителей, ~1.4 ТБ) | **Нереалистично для пилота** (железо) |
| C. On-prem малый Kimi-VL | NDA заказчика | vLLM, 1×H100-класс | **Кандидат** — тестировать младшие Kimi-VL, не K3 |
| D. Kimi Enterprise (data-privacy) | NDA — только при подписи | managed, договор о приватности | `VERIFY_WITH_OPERATOR` + согласие Самолёта |

**Вывод:** для пилота на данных Самолёта K3 (tier B) не проходит по железу; путь —
tier A для бенчмарков на открытых данных и tier C (малый Kimi-VL) для закрытого
контура. **Fail-closed правило протокола:** модель без подтверждённого локального
запуска в контуре не участвует в выборе, какова бы ни была её точность.

## 6. Швы интеграции (когда/если выбран по протоколу)

1. **`KimiVlmDrawingPipeline(MultimodalDrawingPipeline)`** — `analyze(source, mode="detector_vlm")`
   → `MultimodalDrawingResult` (annotations + regions); OCR-degrade обязателен при
   отсутствии extra (как у существующего пайплайна).
2. **Advisory-инструмент**: расширить `AdvisoryToolName` (например `drawing_vlm_read`)
   c контрактом `can_change_verdict=False`, `evidence_required=True`,
   `timeout_seconds`, `max_steps`, per-tenant allowlist; каждый вызов —
   `validate_invocation` + `advisory_trace_record` (реплей).
3. **Клиент**: `infrastructure/adapters/kimi_k3_client.py` — OpenAI-совместимый
   `chat.completions` с image-контентом; endpoint/ключ из env
   (`AEROBIM_KIMI_API_BASE_URL`, `AEROBIM_KIMI_API_KEY`); ключ не логируется;
   outbound строго через `safe_urlopen`.
4. **Config-гейт**: `AEROBIM_KIMI_K3_ENABLED` (default **off**); если включён, но
   не сконфигурирован — capability `FAILED` (fail-closed), не тихий skip; на
   customer-профиле с NDA-данными — запрет tier A (только tier C/D).
5. **Детерминизм для eval**: `temperature=0`, фикс `max_tokens`, пин снапшота
   (sha256), полные request/response логи — по §«Условия прогона» протокола;
   advisory-OFF==ON тест обязан держаться (K3 off vs on → идентичный `summary.passed`).
6. **Стоимость/латентность**: max-effort дорог → бюджет токенов, таймаут, retrieval
   вместо 1M-dump; cache-hit ($0.30) для повторяемых системных промптов.

## 7. Риски и митигации

| Риск | Митигация |
|---|---|
| «Excessive proactiveness» (решает за пользователя) | Архитектурно обезврежено: advisory-only, вердикт у движка/эксперта; явные ограничения в system-prompt/AGENTS.md |
| Non-determinism (temp=1.0 default) | eval с temp=0 + логи + пин; advisory не влияет на `passed` |
| Paraphrase divergence обозначений | Нормализация + grounding к region/GUID; сырой вывод не идёт в правило |
| Утечка NDA-данных в публичный API | tier-гейт: customer-данные только tier C/D; SSRF-гард; ключ из env |
| Лицензионная неоднозначность | Прочитать реальный LICENSE до self-host; юр-ревью (совместимость с MIT-репо) |
| Стоимость 2.8T max-effort | Бюджеты, retrieval, cache; сравнить TCO с малым Kimi-VL/Qwen3-VL |

## 8. Фазовый план (окно протокола 4–20 авг)

1. **Сейчас (27.07)**: зафиксировать веса/лицензию (sha256 + LICENSE-ревью);
   обновить строку Kimi в [протоколе](../pilot/VLM_OCR_COMPARISON_PROTOCOL_2026_08.md) (сделано, §ниже).
2. **4–20 авг**: прогнать T1–T4 на fixture-корпусе (tier A, открытые данные) для K3
   API **и** малых Kimi-VL (tier C); сравнение — `compare_extraction_runs`
   (paired permutation + Holm, CI), primary endpoint macro-F1 T2.
3. **После выбора**: если победитель проходит closed-contour fail-closed —
   реализовать §6 швы (adapter + контракт + config-гейт + тесты advisory-OFF==ON).
4. **Customer-данные**: только после scope memo + режима обработки (tier C/D),
   не ранее intake (RT-001).

## 9. Явно НЕ заявляется

- K3 не «понимает чертежи как инженер»; VLM — подсветка/кандидаты + HITL.
- Никаких чисел точности без CI/p-values и без корпуса заказчика (RT-001).
- Лицензия/минимальное железо — не утверждаются до чтения первоисточника.
- Подключение K3 **не** меняет Checkpoint (остаётся `NO_GO` до RT-001/002/003).
