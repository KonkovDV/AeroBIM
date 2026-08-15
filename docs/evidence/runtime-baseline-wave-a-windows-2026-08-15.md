<!-- claims-lint: allow-file reason="Local Wave A pytest pin; not CI publishable; Checkpoint NO_GO" -->
---
title: "Wave A local pytest (Windows) — does not replace CI runtime pin"
date: 2026-08-15
claim_level: engineering_local
closes_rt001: false
closes_rt002: false
closes_rt003: false
---

# Wave A local pytest (Windows 2026-08-15)

Not a replacement for [`runtime-baseline-latest.json`](runtime-baseline-latest.json).  
N-26: local export is `attested_by=local`, `publishable=false`. Do not copy these counts into README.

| Field | Value |
|---|---|
| HEAD | `005b7bcb6fb2b9f353cc046b44fe68f1b519b776` |
| Interpreter | `backend/.venv-3.12` CPython 3.12.10 Windows |
| Command | `python -m pytest tests -q --junitxml=var/reports/pytest-junit.xml` |
| pytest summary | **2259 passed, 12 skipped, 0 failed** (194.07s); 165 subtests passed |
| ifcclash extra | installed (clearance live tests ran) |
| Golden pin | skipped locally: CI hash assumes `clash=skipped`; local geom-init on tiny baseline IFC sets `clash=failed` |
| CI pin remains | `tests_passed=2167`, frontend=54, `commit_sha=88e726be20bc` |
| Committed consistency fix | `tests_collected` 2178 → **2271** to match `test_functions` (Wave A loc bump) |

Do not use JUnit suite-attribute sums (`tests=2436` / `passed=2424`): they double-count unittest subtests. SSOT is the pytest summary line.

Checkpoint **NO_GO**. RT-001/002/003 remain OPEN.
