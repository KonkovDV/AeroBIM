# Claims Lock — dated freeze 2026-07-31

**Status:** active engineering freeze (supplements `CLAIMS_LOCK_2026_07_17.md`; does not replace RT-001/002/003).  
**HEAD at authoring:** `64c69b4f9cdd99779e9aac91ec87078367190339` (+ uncommitted audit/sprint-2.1 work may be present — verify with `git status`).  
**Checkpoint:** `NO_GO`.

## Allowed (with evidence)

- MIT **только** для собственного кода AeroBIM; сторонние компоненты — под своими лицензиями (`audit/dependency_license_inventory.json`).
- PyMuPDF = dual AGPL-3.0 / Artifex commercial; **optional `pdf-agpl` only** after
  LIC-001 Option B (2026-07-31). Production core PDF = pypdfium2 + pdfminer.six.
  Not a court opinion; disclosure of third-party licenses still required.
- Offline **image-track** install+runtime smoke (Docker load + `--network none`) — eng evidence; bare-metal **DEFERRED** (owner: Docker sufficient).
- `extraction_integrity` capability: default `not_verified` without PDF/producer; PDF text-layer producer on analyze path can set OK / NOT_VERIFIED / FAILED; `FAILED` blocks `summary.passed`; **not** a full render-vs-extract product.
- BCF ZIP structural (T0/T1) with evidence; CDE import T2+ NOT_VERIFIED.
- Calculation **сверка** PARTIAL; **корректность** NOT_IMPLEMENTED.
- LLM/VLM advisory only; cannot set `summary.passed`.
- **Report reproducibility** is ensured by the deterministic core. The language-model output is not a verdict input; it is stored as a provenanced annotation with hashes and on re-run is presented, not re-generated (see deep analysis §2.3).
- Yandex AI Studio / local OpenAI-compat advisory (`private_yandex_ai_studio` / `private_qwen_local`): same adapter, `base_url` swap; Studio cloud = PUBLIC/INTERNAL only (**never** `tier_defaults.private` — default private = local weights); host allowlist fail-closed (Alibaba Max blocked); token caps fail-closed; `model_revision` required when enabled; unavailable model → SKIPPED; Alibaba `qwen3.8-max` NOT_VERIFIED. See `docs/architecture/YANDEX_AI_STUDIO_GRANT_KT2_2026_08_03.md`.
- Sprint 2.1 engineering baseline on public/fixture/synthetic package only.
- Annotation↔IFC `ifc_guid` on report: only when annotation **claimed** a GUID (`claimed_guid:` evidence) **and** spatial index confirms presence — **not** human-adjudicated matching; region_overlap never sets guid.
- MEP graph `edge_kinds` (`co_presence` / `connects`) and matrix findings with `geometry_verified=False` — eng honesty only; **not** MEP delivered / not RT-003 closed.
- Optional MEP AABB broadphase (`aabb_filter:applied`) shrinks candidates only; **not** verified geometric clash.
- Наличие откреплённой подписи (envelope), целостность хеша содержимого и полнота ролей подписантов проверяются на fixture envelope (`samples/signatures/`, capability `qualified_signature` ENG_PARTIAL). `trust_chain_status` всегда `not_verified`.
- Norm pack schema 2.0.0 (RASE + `execution_mode` + `expert_confirmation_journal`): loader fail-closed without `customer_approved` + full approval object; LLM-drafted text is not checkable without expert journal; `expert_required` rules are list-only (`list_expert_required_norm_rules`). **RT-002 remains OPEN** — fixture/draft packs ≠ customer-approved evidence.

## Forbidden

- «AeroBIM целиком под MIT» / MIT without third-party disclosure
- «AGPL не применим» without legal opinion
- product accuracy >90%; customer SLA ≤30 min for any package
- native DWG / DWG-ready
- MEP system-aware clash delivered / full MEP clash
- independent calculation correctness / «проверка корректности расчётов»
- CDE_READY / BCF готов для СОД / integrated with 10D / S.Project integration (before ladder T5 + evidence)
- УКЭП проверена / подпись документа проверена / юридическая значимость квалифицированной подписи (trust chain = NOT_VERIFIED; ENG_PARTIAL ≠ legal OK)
- российское ПО / реестр российского ПО without legal gap analysis
- masking = anonymization
- OCR/VLM = engineer understanding
- LLM changes deterministic verdict
- «полностью российский стек на Yandex Cloud» as product readiness without on-prem pilot evidence for CONFIDENTIAL
- Studio cloud path for CONFIDENTIAL / RESTRICTED customer data
- customers «interested» without verified contact
- offline-ready bare-metal without wheelhouse evidence

## Evidence pointers

- Blockers: `CRITICAL_BLOCKERS.md`
- License: `docs/license-policy-2026.md`, inventory JSON, `test_dependency_license_gate.py`
- Offline: `docs/offline-deployment-2026.md`, `aerobim.tools.offline_bundle`
- Extraction: `docs/extraction-integrity-2026.md`, `domain/extraction_integrity.py`
- Signature: `docs/signature-and-immutability-2026.md`
- Full P-001…P-020 re-audit: `RED_TEAM_AUDIT_2026_07_31.md` §6 (reaudit addendum)
