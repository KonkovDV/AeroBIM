---
title: "Kimi K3 advisory scaffold — план подключения и реализация (Wave T)"
status: done
version: "1.0.0"
last_updated: "2026-07-27"
claim_boundary: "Инженерный advisory-скаффолд: config-гейт + SSRF-клиент + grounding + tool-contract. По умолчанию OFF, НЕ подключён в analyze-путь, НИКОГДА не выставляет summary.passed. Не заявляет качество на данных Самолёта (RT-001). Checkpoint NO_GO."
---

# Wave T — Kimi K3 advisory: план подключения + реализация (2026-07-27)

Реализация плана из [`../architecture/KIMI_K3_INTEGRATION_STUDY_2026_07_27.md`](../architecture/KIMI_K3_INTEGRATION_STUDY_2026_07_27.md)
и [`../architecture/KIMI_K3_SCENARIO_MATRIX_2026_07_27.md`](../architecture/KIMI_K3_SCENARIO_MATRIX_2026_07_27.md).
Заложены **швы** (config → SSRF-клиент → grounding → tool-contract), fail-closed,
advisory-only. **Живой вызов API и DI-wiring в analyze — сознательно НЕ включены**
(зависят от выбора модели по VLM/OCR-протоколу и от закрытого контура заказчика).

## Академические якоря (июль 2026)

| Столп | Якорь | Что реализовано |
|---|---|---|
| Structured output | Constrained-decoding консенсус 2026 (arXiv:2606.09395; «stop parsing JSON with regex») | строгая JSON-схема + tolerant parser; **schema deviation → fail-closed** (0 регионов + reason), не тихий best-effort |
| Neuro-symbolic guardrail | Castagnone 2026, MDPI *Buildings* 16(3):534 (нельзя полагаться только на LLM в структурной инженерии); arXiv:2605.26942 (neuro-symbolic verification high-stakes) | VLM-кандидат проверяется детерминизмом; вердикт у движка (ADR-001/ТР-2/27/31) |
| Confidence / abstention | VL-Calibration (Xiao et al., ACL 2026, arXiv:2604.09529); Khan et al. CVPR 2024 (black-box VLM confidence ненадёжна) | verbalized-confidence **не доверяется**: clamp [0,1] + below-threshold → `hitl_required` (abstention), не факт |

## Реализовано (код + тесты)

- `core/config/settings.py`: `kimi_k3_enabled` (default off), `kimi_api_base_url`
  (SSRF-gated at boot), `kimi_api_key` (не логируется), `kimi_model`; метод
  **`kimi_advisory_ready()`** — fail-closed: требует enabled+base+key И
  **hard-disable под `samolet_pilot`/`production`** (NDA не уходит в публичный API,
  on-prem wiring ещё нет).
- `domain/vlm_grounding.py` (domain-pure): `ground_vlm_drawing_response` →
  кандидатные `DrawingRegionRef` (`modality="vlm"`); clamp confidence; low-conf →
  `hitl_required`; любая schema deviation → `parse_ok=False` + reason; **никогда
  не вердикт**; evidence_refs (`vlm:<model>` + `sheet:<id>`).
- `infrastructure/adapters/kimi_k3_advisory_client.py`: OpenAI-совместимый
  `chat.completions` (image data-URL, `temperature=0`, `response_format=json_object`);
  outbound строго через `safe_urlopen` (SSRF: DNS-pin, no-redirect, private/metadata
  block); **bounded read** (cap → error); ключ только в Authorization, **redaction
  в `repr`**; инъектируемый `transport` (тесты без сети).
- `domain/ai_tool_registry.py`: контракт `drawing_vlm_read`
  (`can_change_verdict=False`, `evidence_required=True`, `max_steps=1`); **не**
  agent-step (нет в `AGENT_TOOL_TO_REGISTRY`) → `allowed_agent_tool_names()`
  остаётся 8 (регрессия не сломана).
- `tests/test_kimi_k3_advisory.py` — **18 тестов**: grounding (валид/low-conf
  abstention/clamp/6 вариантов schema-deviation); tool-contract (never-verdict,
  allowlist=8, trace требует evidence); клиент (parse, redaction ключа, нет choices,
  не-JSON, требует base+key, **SSRF блок private IP**, **cap размера ответа**);
  config-гейт (default off, enabled-но-не-настроен → not ready, dev-ready,
  **customer-профиль hard-disable**).

## Инвариант «advisory OFF==ON» (по построению)

K3 **не подключён** в `AnalyzeProjectPackageUseCase`/`bootstrap` и по умолчанию
`kimi_advisory_ready()==False`. Значит поведение вердикта в дефолте байт-в-байт
неизменно — существующий тест advisory-OFF==ON держится без правок.

## Фазовый план (что дальше, вне этой волны)

1. **4–20 авг** — прогон VLM/OCR-протокола (T1–T4) на fixture-данных: K3 API (tier A)
   + малые Kimi-VL (tier C); выбор через `compare_extraction_runs` (CI/p-values).
2. **После выбора победителя** — DI-wiring `KimiVlmDrawingPipeline`
   (`MultimodalDrawingPipeline`) под `kimi_advisory_ready()`, с тестом
   advisory-OFF==ON на реальном UC-пути и golden-hash реплеем.
3. **Customer-данные** — только tier C/D после scope memo (RT-001), не ранее intake.

## Явно НЕ сделано / НЕ заявлено

- Нет живого вызова Kimi API (нет ключа/сети в тестах; transport замокан).
- K3 не подключён в analyze-путь; вердикт не затронут.
- Никаких заявлений точности/качества на чертежах (RT-001) — только швы.
- Checkpoint остаётся **NO_GO** (RT-001/002/003).

## Gate evidence (2026-07-27 local)

`ruff format/check` PASS (354 files) · `mypy src` 209 files PASS ·
`pytest tests -q` **1173 passed, 7 skipped**.
