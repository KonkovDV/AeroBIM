# Red-team test plan (2026)

| Area | Existing evidence | This-cycle status |
|---|---|---|
| License gate | `test_dependency_license_gate.py` | run required |
| License isolation | `test_license_isolation_guard.py` | run required |
| Extraction integrity | `test_extraction_integrity.py` | run required |
| Prompt injection / LLM advisory | `test_llm_prompt_injection.py`, hybrid tests | run required |
| Path jail / ACL / SSRF / ZIP / XXE / upload / tenancy / LLM advisory | `docs/evidence/security-rerun-2026-07-31.json` | **REPRODUCED 2026-07-31 evening:** 190 passed / 1 skipped |
| Offline smoke | `offline_bundle` | Docker; optional heavy |
| IDS XSD / Level B | injected defect tests | run sample |
| BCF ladder | T0/T1 evidence; T2 empty | no CDE claim |

Principle: document-as-data; AI cannot set `summary.passed`.
