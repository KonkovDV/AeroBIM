# Phase 0 Audit Report — AeroBIM (2026-07-18)

**Role:** Principal / Staff / BIM / Red Team  
**Repo:** https://github.com/KonkovDV/AeroBIM  
**HEAD at audit start:** `55bdedd`  
**Checkpoint:** **`NO_GO`** (RT-001 / RT-002 / RT-003 still customer-blocked)

---

## 1. What was checked

| Gate | Result (after local env repair) |
|------|----------------------------------|
| `ruff format --check` | PASS (219 files) |
| `ruff check` | PASS |
| `mypy src` | PASS (after optional-import overrides for enterprise/cad/vision) |
| `pytest tests` | **537 passed, 4 skipped** (was 60 ERROR + 18 FAIL due to missing `python-multipart` / `jsonschema` in local venv) |
| Frontend `vitest` | **21 passed** |
| Layer / seam / signoff architecture tests | Present under `backend/tests/test_layer_boundaries.py`, `test_architecture_seams.py`, etc. |
| Claims Lock / CRITICAL_BLOCKERS / KNOWN_BUGS | Read and reconciled vs code |

**Env note (not a product defect):** editable install had drifted — `python-multipart` and `jsonschema` declared in `pyproject.toml` but absent from `.venv`. Fixed via `pip install -e ".[dev]"`.

---

## 2. What was found

### Holds (healthy)

| Invariant | Evidence |
|-----------|----------|
| Domain ↛ infrastructure | `test_layer_boundaries.py` + grep clean |
| AI/advisory cannot alone set `summary.passed` | `DeterminismGate` + advisory ON/OFF tests |
| Capability `FAILED` blocks pass | `signoff_policy.py` + tests |
| NormPack `customer_approved` needs `approval_ref` | loader + schema tests |
| Auth fail-closed non-dev | `Settings.require_secure_auth` + API tests |
| Path jail / upload size | `path_jail.py` + API tests |
| Capability honesty for DWG/MEP/CV/calc | `enforce_honesty_capabilities` |

### Risk register (remediable vs blocked)

| ID | Severity | Layer | Finding | Remediable without customer data? |
|----|----------|-------|---------|-----------------------------------|
| RT-001 | **BLOCKER** | Claims | Customer accuracy / >90% not evidenced | **No** — corpus + ≥2 adjudicators |
| RT-002 | **BLOCKER** | Norms | Approved customer norm pack absent | **No** — signed pack |
| RT-003 | **BLOCKER/CRITICAL** | MEP | System-aware MEP clash not runtime | **No** — federated IFC + provider |
| A-ENV-001 | **HIGH** (local/CI drift) | Ops | Optional-core deps can be missing from venv → API suite ERROR cluster | **Yes** — document + CI assert |
| A-HYBRID-001 | **MEDIUM** | Infra | Allowlist degrade shadowed by vision-extra check | **Yes** — fixed this session |
| A-MYPY-001 | **MEDIUM** | Tooling | mypy overrides incomplete for optional extras | **Yes** — fixed this session |
| A-UI-001 | **HIGH** | Frontend | Capabilities / divergences / system honesty not rendered in review-shell | **Yes** — Phase 1 |
| A-DOC-001 | **MEDIUM** | Docs | Contour ownership: `passed` written in EvidenceAssembler from deterministic inputs (doc says DETERMINISTIC contour) | **Yes** — clarify ADR |
| A-CLASH-001 | **HIGH** (pilot policy) | Application | Default `clash_affects_pass=False` | **Yes** — Samolet profile flag docs/tests |
| A-DOMAIN-IO-001 | **MEDIUM** | Domain | `system_capabilities.py` reads filesystem | **Yes** — move to infra/core |
| A-BCF-CDE-001 | **MEDIUM** | Claims | BCF ZIP structural ≠ CDE import | Honest — keep NOT_VERIFIED |
| A-STUB-001 | **LOW/MEDIUM** | Application | IDS assist `@sota-stub` | Tracked in KNOWN_BUGS |

---

## 3. Claims impact

| Claim surface | Status |
|---------------|--------|
| Kernel architecture coherent / fail-closed seams | **Supported** by tests |
| Fixture extraction F1 / fixture SLA | **Allowed** under Claims Lock |
| Product accuracy >90% / approved norms / MEP delivered / CDE-ready BCF / native DWG | **Forbidden** — unchanged NO_GO |
| README “active review shell” | **Partial** — triage works; honesty dashboard missing (A-UI-001) |

---

## 4. Changes in this session (Phase 0 → start Phase 1)

1. `backend/pyproject.toml` — broaden mypy `ignore_missing_imports` for optional extras.
2. `hybrid_drawing_analyzer.py` — allowlist gate before vision-extra check.
3. Local venv repair: `pip install -e ".[dev]"` (operator, not committed).
4. This audit artifact.

---

## 5. How correctness is proven

```text
cd backend
python -m ruff format --check src tests
python -m ruff check src tests
python -m mypy src
python -m pytest tests -q
cd ../frontend && npm test -- --run
```

**Baseline after hybrid + mypy fix:** ruff/mypy green; pytest **537 passed / 4 skipped**; frontend **21 passed**.

---

## Phase 3 follow-up (same day)

| Item | Status |
|------|--------|
| Ambiguous Pset alignment → ERROR + AMBIGUOUS_MAPPING + HITL | Done |
| Unrecognized section keys → ERROR + section_pairing FAILED | Done |
| NormPack version store defense-in-depth for approval_ref | Done |
| pytest | **539 passed / 4 skipped** |
| Still open | RT-001/002/003 |

---

## 6. Next phases (ordered)

1. ~~Phase 1~~ · ~~Phase 2~~ · ~~Phase 3~~
2. **Phase 4** — Security/jobs/idempotency/retention hardening
3. **Phase 5+** — API/UI polish; pilot GO still blocked on RT-001/002/003
