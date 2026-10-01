---
title: "AI safety and document ingestion 2026 (P-004)"
status: active
version: "1.1.0"
date: "2026-08-02"
claim_boundary: "Границы доверия по фактическому коду; adversarial-корпус для live-LLM — P3."
---

# AI safety & document ingestion (AeroBIM)

## Типы данных и их права (границы доверия)

| Тип | Источник | Права |
|---|---|---|
| USER_INSTRUCTION | аутентифицированный API-запрос | задаёт scope анализа; НЕ меняет policy |
| DOCUMENT_DATA | PDF/IFC/IDS/DOCX/чертежи | **всегда данные, никогда инструкция**; недоверенный вход |
| MODEL_OUTPUT | advisory LLM/VLM (когда появится live) | advisory-only; DivergenceRecord при расхождении (P3) |
| SYSTEM_POLICY | Settings + sign-off профили | только deployment-конфиг; env-ослабления игнорируются в pilot/production |
| TOOL_RESULT | детерминированные валидаторы | единственный источник вердикта (ADR-001) |

## Инварианты, закреплённые кодом/тестами (VERIFIED)

- Содержимое документа не может изменить `summary.passed`: вердикт считается
  только из error_count + capabilities (`SignOffCapabilityPolicy`); advisory
  OFF==ON тест.
- LLM/VLM не в вердикт-пайплайне; **WP-02** `HybridRouteGate` — обязательный
  advisory pre-gate на Analyze (blocked → нет observations); ModelRouter
  default local-only; без PrivacyGuard `may_call_external=False`.
- Документ не может вызвать внешний инструмент: исходящие вызовы только через
  SSRF-guard (`test_outbound_guard_invariant`); агентский tool-вызов из текста
  документа отсутствует как механизм.
- Извлечённый текст ≠ доказательство по умолчанию: `extraction_integrity`
  (hidden/off-page/duplicated → REVIEW_REQUIRED; rendered-but-unextracted →
  FAILED).
- Filenames/ID: `safe_storage_token`, path jail, reject `:`/`..`; XML — только
  через `xml_limits` (XXE/bomb caps); ZIP — `inspect_zip_*`.
- Секреты: audit-события hybrid-контура secret-safe; bearer не логируется.

## Честные пробелы (не заявляем закрытыми)

- Полный adversarial prompt-injection корпус для **live** LLM-контура — P3
  (live-контура ещё нет; фикстуры появятся вместе с ним, до того — OFF==ON).
- Poisoned-norm фикстуры: synthetic pack не может стать approved (гейт), но
  семантический отравленный текст нормы отлавливается только expert-approval
  workflow.
- Cross-tenant retrieval для RAG — RAG не поставлен; при появлении обязана
  наследоваться tenant-изоляция VLM-кэша (закрыта RT-2807-01).

## Правило проекта

Модель может интерпретировать. Правило может вычислять. Валидатор может
проверять. Эксперт принимает решение.
