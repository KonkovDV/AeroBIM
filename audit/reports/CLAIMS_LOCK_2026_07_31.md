# Claims Lock — dated freeze 2026-07-31

**Status:** active engineering freeze (supplements `CLAIMS_LOCK_2026_07_17.md`; does not replace RT-001/002/003).  
**HEAD at authoring:** `64c69b4f9cdd99779e9aac91ec87078367190339` (+ uncommitted audit/sprint-2.1 work may be present — verify with `git status`).  
**Checkpoint:** `NO_GO`.

## Allowed (with evidence)

- MIT **только** для собственного кода AeroBIM; сторонние компоненты — под своими лицензиями (`audit/dependency_license_inventory.json`).
- PyMuPDF = dual AGPL-3.0 / Artifex commercial; lock `==1.28.0`; LIC-001 OPEN (legal review).
- Offline **image-track** install+runtime smoke (Docker load + `--network none`) — eng evidence; bare-metal wheelhouse NOT VERIFIED.
- `extraction_integrity` capability: default `not_verified` without PDF/producer; PDF text-layer producer on analyze path can set OK / NOT_VERIFIED / FAILED; `FAILED` blocks `summary.passed`; **not** a full render-vs-extract product.
- BCF ZIP structural (T0/T1) with evidence; CDE import T2+ NOT_VERIFIED.
- Calculation **сверка** PARTIAL; **корректность** NOT_IMPLEMENTED.
- LLM/VLM advisory only; cannot set `summary.passed`.
- Sprint 2.1 engineering baseline on public/fixture/synthetic package only.

## Forbidden

- «AeroBIM целиком под MIT» / MIT without third-party disclosure
- «AGPL не применим» without legal opinion
- product accuracy >90%; customer SLA ≤30 min for any package
- native DWG / DWG-ready
- MEP system-aware clash delivered / full MEP clash
- independent calculation correctness / «проверка корректности расчётов»
- CDE_READY / BCF готов для СОД / integrated with 10D / S.Project integration (before ladder T5 + evidence)
- УКЭП проверена / подпись документа проверена (QUALIFIED_SIGNATURE_VALIDATION = missing)
- российское ПО / реестр российского ПО without legal gap analysis
- masking = anonymization
- OCR/VLM = engineer understanding
- LLM changes deterministic verdict
- customers «interested» without verified contact
- offline-ready bare-metal without wheelhouse evidence

## Evidence pointers

- Blockers: `CRITICAL_BLOCKERS.md`
- License: `docs/license-policy-2026.md`, inventory JSON, `test_dependency_license_gate.py`
- Offline: `docs/offline-deployment-2026.md`, `aerobim.tools.offline_bundle`
- Extraction: `docs/extraction-integrity-2026.md`, `domain/extraction_integrity.py`
- Signature: `docs/signature-and-immutability-2026.md`
- Full P-001…P-020 re-audit: `RED_TEAM_AUDIT_2026_07_31.md` §6 (reaudit addendum)
