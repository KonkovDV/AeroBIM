# RED TEAM FULL REPORT — AeroBIM (Samolet Task 07)

**Verdict:** `NO_GO`  
**Audit UTC:** 2026-07-16T20:59:16Z  
**SHA:** `c0c4b2bdc8f0a6e18dacfe674b616b4e4e61d04f` (`main`, dirty)  
**Author relationship:** self  

Companion artifacts:

- [`../evidence/audit-baseline.json`](../evidence/audit-baseline.json)
- [`../evidence/test-results.json`](../evidence/test-results.json)
- [`../evidence/runtime-paths.json`](../evidence/runtime-paths.json)
- [`../evidence/claims-inventory.json`](../evidence/claims-inventory.json)
- [`RED_TEAM_EXECUTIVE_SUMMARY.md`](RED_TEAM_EXECUTIVE_SUMMARY.md)
- [`CRITICAL_BLOCKERS.md`](CRITICAL_BLOCKERS.md)
- [`TZ_RUNTIME_MATRIX.md`](TZ_RUNTIME_MATRIX.md)
- [`CLAIMS_EVIDENCE_MATRIX.md`](CLAIMS_EVIDENCE_MATRIX.md)
- [`REMEDIATION_PLAN.md`](REMEDIATION_PLAN.md)

---

## Stage 0 — Inventory freeze

See `audit-baseline.json` for command-backed values. Headline:

| Item | Measured |
|---|---|
| OS | Windows 11 10.0.26200 AMD64 |
| Python | 3.13.7 |
| Node / npm | v24.11.0 / 11.6.1 |
| Backend src | 101 files / 15290 LOC |
| Backend tests | 63 files / 11149 LOC |
| Frontend src | 11 files / 3871 LOC |
| Docs md | 100 files / 8864 LOC |
| Pytest | 436 passed / 3 skipped / 0 failed (439 collected) |
| Frontend | 18 passed / **3 failed** |
| Optional: ifcclash, rapidocr, onnxruntime, boto3, docling | **all not importable** |
| CI latest main | success |
| Uncommitted | 20 paths |

Runtime entrypoints / API / CLI listed in baseline JSON.

**Note:** Naive whole-repo LOC is polluted by vendored/binary trees; audit uses scoped LOC only.

---

## Stage 1 — Architecture

### Layers

- Search found **no** `domain → infrastructure/presentation` imports.
- Vendor libraries (ifcopenshell, ifctester, ifcclash, pymupdf, redis, boto3, …) appear behind infrastructure adapters when present.
- Composition root: `infrastructure/di/bootstrap.py::bootstrap_container`.
- **Dead/scaffold port:** `MepSystemGraphProvider` / `UnconfiguredMepSystemGraphProvider` exist in `domain/mep.py` and are **not** registered in bootstrap.

### Contours

| Contour | Reality |
|---|---|
| INGESTION | Requirements/drawings/uploads; DocumentIdentity incomplete; revision guard only strong in dirty tree |
| DETERMINISTIC VALIDATION | IFC/IDS/cross-doc/clash/norm packs — real but fixture-heavy |
| AI ADVISORY | Stub assist; test proves pass flag stable OFF==ON |
| EVIDENCE/REPORTING | JSON/HTML/BCF + HITL events; provenance gaps on findings |

### Forced answers

1. **AI → summary.passed?** No (design + unit test).  
2. **Adapter failure → empty success?** Clash **SKIPPED** path yes-risk; FAILED path blocks.  
3. **Frontend invent findings?** Not observed.  
4. **Lose provenance?** Structurally yes — optional fields.  
5. **Silent revision merge?** Risk on committed HEAD; dirty tree adds guard; identity schema still incomplete vs auditor checklist.

---

## Stage 2 — Domain contracts

| Model | Verdict |
|---|---|
| ParsedRequirement | Frozen dataclass; rich optional norm fields; OK as additive model |
| ValidationIssue | **DEFECT vs auditor mandate** — no finding_id, evidence_refs[], document_identity, capability |
| ValidationReport | Present; capabilities optional |
| ProblemZone | Present optional |
| EvidenceRef | Defined in architecture; **not enforced** on issues |
| QuantityValue | Present; SI compare used |
| ConflictKind | Present incl. VERSION_MISMATCH |
| CapabilityStatus | ok/skipped/failed used |
| ReviewEvent | HITL; does not affect pass |
| DocumentIdentity | Partial — missing discipline, project_id, supersedes, created_at, effective_at |
| NormRule / packs | approval_ref required for customer_approved — **good** |
| PrecisionClaim | publishable gate — **good**; no customer corpus to publish |

---

## Stage 3 — Pipeline table

See `runtime-paths.json`. Summary: core analyze path is reachable; MEP not connected; OCR/clash extras absent in this env; calculation path is match/digest not independent verification; BCF export reachable; CDE import evidence absent.

---

## Stage 4 — TZ matrix

See `TZ_RUNTIME_MATRIX.md`. **No customer-VERIFIED rows.** MEP: NOT VERIFIED.

---

## Stage 5 — Norm packs Red Team

| Attack | Result |
|---|---|
| Rule without clause | Depends on loader validation — pack schema expects structured rules; synthetic packs may still be thin |
| customer_approved without approval_ref | **Rejected** (loader + HITL) |
| Failed pack blocks pass | **Yes** (capability FAILED) |
| Customer approved pack present | **НЕТ** |

```text
Есть ли утверждённый заказчиком нормативный пакет: НЕТ
```

---

## Stage 6 — MEP / Clash Red Team

```text
MEP system-aware clash: NOT VERIFIED
```

Missing: system assignment graph in runtime, connectivity, duct/pipe/tray classes, allowed intersection matrix, insulation/maintenance clearances, penetration workflow, fire compartment semantics, MEP corpus, two-engineer adjudication.

Generic IfcClash must not be marketed as MEP capability. Current env: `ifcclash` missing → SKIPPED.

---

## Stage 7 — 2D / OCR / CV

| Level | Status |
|---|---|
| L0 structured text | PARTIAL / fixture |
| L1 OCR | Extra absent here |
| L2 narrow CV | MISSING |
| L3 VLM | ADVISORY stub / not sign-off |
| L4 human drawing understanding | НЕ РЕАЛИЗОВАНО |

Advisory OFF==ON for `summary.passed`: covered by unit test (not full report-hash equality of all fields).

---

## Stage 8 — Calculations

- **Сверка с результатами расчёта:** PARTIAL (OpenRebar digest / evidence verifier / numeric compare).  
- **Независимая проверка корректности расчёта:** НЕ РЕАЛИЗОВАНО.

---

## Stage 9 — Revisions / documents

Required identity fields vs implementation: many missing. Attack scenarios (same name new revision, PD/RD mix, project mix) not fully covered by committed runtime. Dirty-tree revision-merge emits VERSION_MISMATCH for same logical doc different revisions — incomplete relative to AMBIGUOUS/REQUIRES_HITL/INCOMPLETE_PACKAGE taxonomy.

---

## Stage 10 — Reporting / BCF

- JSON/HTML export: runtime reachable.  
- BCF 2.1 / 3.0 ZIP: exporters exist.  
- Independent consumer: in-repo parsers/tests (dirty); **no external CDE import evidence artifact**.  
- ZIP existence alone ≠ ready.

---

## Stage 11 — API / security

| Control | Status |
|---|---|
| Bearer / OIDC | Present |
| Anonymous dev | Env-gated; dangerous if misconfigured |
| Tenant isolation | **Absent** |
| Path jail | Present on uploads/paths |
| Size limits | Present for IFC |
| Report artifact ACL | **IDOR-class risk** with shared token |
| Idempotency | Present in dirty tree for jobs |

---

## Stage 12 — SLA / reliability

Stage budgets exist (dirty). Measured customer SLA with package hash + machine + cold/warm: **НЕ ДОКАЗАНО** in this freeze. Process restart job durability exists for in-memory snapshot (failed interrupted jobs). Parallelism/OOM/disk: not evidenced.

---

## Stage 13 — Tests audit

| Class | Note |
|---|---|
| Volume | 436 backend passes — **not** quality proof |
| Fixture bias | Dominant |
| Frontend | **Failing** — critical path red |
| Skips | Conditional SkipTest for missing extras/fixtures |
| Mutation resistance | Not run in this audit; provenance mutations likely weak given optional fields |
| Customer-like | BLOCKED_BY_CUSTOMER_DATA |

---

## Stage 14 — Claims

See claims matrix. Hard forbid: >90%, full norms, DWG, human CV, MEP-as-done, external audit, production-ready, Solibri replacement.

---

## Stage 15 — Checkpoint readiness

```text
NO_GO
```

Critical blockers RT-001..RT-006 (and claim misuse of RT-003) are sufficient alone.

### Classification of capabilities (honest)

| Capability | Class |
|---|---|
| IFC property + IDS rails | реализовано, доказано только на synthetic/fixture |
| Cross-doc numeric/unit | реализовано, fixture |
| Generic clash | реализовано частично; env often skipped |
| MEP system clash | scaffold / не достигает runtime |
| Customer norms | отсутствует |
| DWG/DXF | отсутствует |
| OCR | заявлено optional; не подключено в audit env |
| CV/VLM | advisory / отсутствует |
| BCF export | реализовано; CDE import не доказан |
| SLA 30m | tool exists; customer proof отсутствует |
| Finding provenance contract | частично / дефект относительно аудита |
| Frontend review | реализовано частично; тесты красные |

---

## Closing rule applied

Where evidence insufficient: **НЕ ДОКАЗАНО**.  
Where only plans/scaffold: **НЕ РЕАЛИЗОВАНО** / **SCAFFOLD**.  
Where fixture-only: **РАБОТАЕТ ТОЛЬКО НА ФИКСТУРАХ**.  
Where code exists but unwired: **НЕ ДОСТИГАЕТСЯ В RUNTIME**.

No code was changed to “improve” claims during this audit. Remediation must follow [`REMEDIATION_PLAN.md`](REMEDIATION_PLAN.md) after acceptance of this report.

---

## Appendix — Independent explore corroboration (2026-07-16)

Two read-only explores completed after the freeze and confirmed the same `NO_GO` spine, adding residual risks RT-013..RT-017 in [`CRITICAL_BLOCKERS.md`](CRITICAL_BLOCKERS.md):

| Explore | Confirmed | Added |
|---|---|---|
| [Architecture layer audit](2546f775-77dd-4830-b1f6-8a53371eaaee) | Clean domain layers; AI cannot flip pass; MEP unwired; finding contract gaps | Empty-revision silent co-analysis; drawings out of identity set; raster OK+empty OCR; bSI WARNING; Postgres always→FS fallback; OpenRebar escalate can strip provenance fields |
| [Claims and TZ audit](b0b9a9d7-762e-4e4a-9173-4a33d4c58d33) | Self-authored evidence JSONs; synthetic norms only; no tenant ACL; BCF unit-only | Fixture SLA ~0.01 min class; narrow advisory OFF==ON test; README/pitch residual optimism vs claim-boundary docs |
