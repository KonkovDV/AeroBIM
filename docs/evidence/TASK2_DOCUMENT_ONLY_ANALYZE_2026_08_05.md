---
title: "Task 2 — document/partial package analyze (no IFC)"
date: 2026-08-05
ports_delta: "+0"
adapters_delta: "+0"
tokens_delta: "+0"
claim_boundary: >-
  Engineering partial-run only. IFC capabilities SKIPPED/NOT_VERIFIED when
  ifc_path omitted. Checkpoint NO_GO. Not product accuracy.
---

# Task 2 — честный частичный прогон без IFC

**Проблема:** analyze требовал `ifc_path` (HTTP 422); PDF/ТЧ/расчёты без модели не были first-class.

**Сделано (+0 портов):**

| Поверхность | Поведение |
|---|---|
| `AnalyzeProjectPackageRequest.ifc_path` | optional |
| `ValidationRequest` / `ValidationReport.ifc_path` | `Path \| None` |
| Document-only contour | drawings / ТЧ / calc / section-diff / package completeness работают |
| IFC engines | clash/quantity SKIPPED; mep NOT_VERIFIED; ifc_validation/schema SKIPPED |
| Hard require clash/MEP | FAILED (не зелёный pass) |
| HTTP без IFC и без документов | `ValueError` — нужен хотя бы один document input |

**Тест:** `backend/tests/test_document_only_analyze.py`

**Не сделано:** multipart upload path без IFC; package_inventory на HTTP schema; Exp A Minstry pack (owner).
