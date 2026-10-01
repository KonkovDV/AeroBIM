---
title: "Data governance 2026 (P-018)"
status: active
version: "1.0.0"
date: "2026-07-31"
claim_boundary: "Факты из кода (VERIFIED); неизвестное помечено UNKNOWN. Не юридический аудит 152-ФЗ."
---

# Data governance (AeroBIM)

Каждое утверждение ниже опирается на код/конфигурацию репозитория; проверка 2026-07-31.

## Что и где хранится (VERIFIED)

| Данные | Место | Управление |
|---|---|---|
| Отчёты (JSON) | `AEROBIM_STORAGE_DIR` (default `var/reports`), FilesystemAuditStore; опц. Postgres summary-index (`AEROBIM_DB_URL`) | TTL: `AEROBIM_REPORT_TTL_DAYS` (unset = без ограничения) |
| Исходные IFC / drawing previews | ObjectStore (Local или S3/MinIO) | path jail; re-jail на FileResponse |
| HITL review-events | append-only JSONL (FilesystemReviewEventStore) | server-SSOT переходов |
| Загрузки | quarantine + ZIP/XML caps, IFC ≤256 MiB | reject `..`/absolute |

## Доступ (VERIFIED)

Bearer/OIDC на всех `/v1/*` (21/21); cross-tenant → **404**; ACL enforced в
pilot/production профилях; list_reports tenant-scoped даже при soft-ACL-off.

## Исходящий трафик (VERIFIED, grep-инвентарь + guard-тест)

Все shipped-вызовы наружу — только через `safe_urlopen` (SSRF host-check,
DNS-pin, без redirect): bSI validation, OpenCDE BCF push, Kimi advisory
(не wired в вердикт), OIDC JWKS. Телеметрии не найдено. Инвариант закреплён:
`backend/tests/test_outbound_guard_invariant.py`. LLM-egress по умолчанию
отсутствует (ModelRouter local-only; PrivacyGuard fail-closed).

## Что попадает в prompts / embeddings (VERIFIED-граница)

В вердикт-пайплайне LLM/VLM нет (ADR-001, OFF==ON). Hybrid-контур не wired в
живой egress; маскирование ≠ анонимность (Claims Lock).

## Удаление и retention (честно)

- TTL-очистка отчётов — есть (`AEROBIM_REPORT_TTL_DAYS`).
- **Объектного DELETE-API нет** (в 25 маршрутах нет DELETE) — удаление по
  запросу субъекта выполняется операционно (файловая система / бакет / TTL).
- Backup/purge/incident-response процедуры — **UNKNOWN** (вне репозитория;
  определяются контуром заказчика при развёртывании).

## UNKNOWN / нужно от заказчика

Требования локализации и сроков хранения; процесс удаления по запросу;
регламент инцидентов; юридическая оценка ПД в штампах чертежей (превью
отдаётся внутри tenant как есть — см. ТР-604).
