<!-- claims-lint: allow-file reason="Red Team Stage B remediation log; no product accuracy claims" -->
---
title: "Red Team Stage B remediation — 2026-08-11"
date: "2026-08-11"
head_before: "a818bfe2eeeaa2cf2b5c98cdd331887e519aacf7"
stage: "B"
claim_boundary: "Code fixes for Stage A VERIFIED P1/P2 only. Not full-repo GO. Not customer accuracy."
---

# Stage B remediation (atomic slices)

Base: Stage A snapshot + diff at HEAD `a818bfe`.

## Slice 1 — immutable outbound headers (P1 / P2)

| Finding | Fix |
| --- | --- |
| RT-20260811-01 | `VlmAdvisoryClient._request_headers` uses `merge_outbound_headers`; forces Auth/Content-Type/Accept; denies folder/logging from extras |
| RT-20260811-06 | `OpenAICompatLlmProvider._request_headers` forces Content-Type/Accept/Auth after extras; ctor `folder_id` wins |

Files:

- `backend/src/aerobim/core/security/immutable_http_headers.py` (new)
- `backend/src/aerobim/infrastructure/adapters/vlm_advisory_client.py`
- `backend/src/aerobim/infrastructure/adapters/openai_compat_llm_provider.py`
- `backend/tests/test_immutable_security_headers.py` (new)

Verification: `python -m unittest discover -s tests -p "test_immutable_security_headers.py" -v` → OK; yandex VLM + qwen advisory suites → OK.

## Slice 2 — exact Yandex host gate (P1) + gate tests (P2)

| Finding | Fix |
| --- | --- |
| RT-20260811-02 | Replaced `"yandex" in host` with exact hosts + `.cloud.yandex.net` / `.yandexcloud.net` suffixes |
| RT-20260811-03 | Added `tests/test_vlm_endpoint_gate.py` |

Files:

- `backend/src/aerobim/core/config/vlm_endpoint_gate.py`
- `backend/tests/test_vlm_endpoint_gate.py` (new)

Verification: gate suite 11 tests OK. `not-yandex.evil` no longer classified as Yandex without provider.

## Slice 3 — architecture import gate (P2)

| Finding | Fix |
| --- | --- |
| RT-20260811-04 | AST import-direction gate for `core` / `domain` / `application` |

Files:

- `backend/tests/test_architecture_import_gate.py` (new)

Verification: 0 violations on current tree; test OK.

## Still open (not in Stage B)

- RT-20260811-05 dirty IFC benchmark evidence (owner)
- OIDC 501 / RT-001..003 / native DWG / MEP / TZ>90% (owner / customer)
- N43 / RUF100 / N59 deferred dates
- Full Phase 19 mutation audit
- Stage C clean-checkout matrix

## Recommended next owner action

1. Review + commit Stage B slice files (signed).
2. Confirm Stage C scope or next P2/P3 from Stage A.
