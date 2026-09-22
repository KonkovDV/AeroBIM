# P0/P1 SOTA 2026 Upgrade — Completion Report

**Branch:** `feat/p0-p1-sota2026-upgrade`  
**Date:** 2026-09-22  
**Author:** AeroBIM Principal Engineering  
**Engine baseline:** see `docs/evidence/runtime-baseline-latest.json` (`attested_by=ci`). Do not copy the integers here.

---

## 1. Executive Summary

This change adds domain contracts and unit tests. It does not close the P0
and P1 gaps on the path that builds a report. `Analyze`, the Redis worker,
and `EvidenceAssembler` do not call these modules.

- **Deterministic package identity** (sha256-based, idempotent, tamper-detectable)
- **Durable job state machine** (QUEUED→EXPIRED cycle, heartbeat, stale recovery)
- **Evidence-first architecture** (every finding traceable to source hash + rule version + norm pack hash)
- **Regulatory Information Model** (norm→clause→interpretation→rule chain with review gates)
- **Finding lifecycle** (NEW/PERSISTED/RESOLVED/REGRESSED/REOPENED/SUPERSEDED)
- **Evaluation harness** (per-rule FN/FP/precision/recall, leakage protection, corpus split)
- **Double annotation protocol** (Cohen's kappa, adjudication, raw label preservation)
- **BCF 3.0 local roundtrip** (push + pull = same content hash)
- **MEP 5-layer split** (honest capability status per layer; no false claims)
- **AI provenance** (per-output record, allowlisted tool calls, NIST AI RMF aligned)

**What this upgrade does NOT do:**
- No rewrite of existing architecture
- No new framework dependencies
- No customer_go flip (remains false; customer gates are external)
- No false claims about MEP system-aware verification
- No AI taking deterministic verdict responsibility

---

## 2. Before / After

| Dimension | Live path today | New contract, not called by Analyze |
|---|---|---|
| Package identity | Random UUID per upload | `sha256(tenant+project+revision+file_hashes)` |
| Manifest integrity | None | `manifest_sha256` over all file entries |
| Job state | Redis worker, lease, and `job_transitions` | Separate `JobStatus` enum in `job_state.py` |
| Job dedup | Same key and fingerprint on the live store | `idempotency_key` helper, not used by the worker |
| Heartbeat | Lease heartbeat on the Redis job store | 120s helper on the unused contract |
| Evidence provenance | `finding_id + evidence_refs` | + `rule_version, norm_pack_hash, engine_version, config_hash, extraction_method` |
| Norm rule provenance | `norm_ref` string | Full `NormRef + RuleInterpretation` with 4 review statuses |
| Rule production gate | None | All 4 review statuses must be APPROVED |
| Finding lifecycle | NEW only | NEW/PERSISTED/RESOLVED/REGRESSED/REOPENED/SUPERSEDED |
| Remark workflow | Single text field | `generated / reviewer_edited / approved` (human text never overwritten) |
| Benchmark leakage | Fixture = evaluation | Immutable manifest with case_hash + manifest_hash |
| FN visibility | Hidden in macro_F1 | Per-rule `fn` + `false_negative_rate` always reported |
| Corpus separation | Single metric | PUBLIC / SYNTHETIC / CUSTOMER always separate |
| Double annotation | Simulation only | Formal protocol: Annotator A + B → Adjudicator → Gold |
| BCF roundtrip | Export only | Local CDE simulator: push + pull → content_hash equality check |
| MEP claims | Conflated layers | 5 formal layers with explicit CapabilityStatus per layer |
| AI provenance | `LLM_MODEL_SHA256` env var | Per-output `AIProvenanceRecord` with input/output hashes |
| AI tool access | Unrestricted | Allowlisted: 13 named tools only |

---

## 3. Architecture Changes

All changes are **additive domain modules**. No existing modules were rewritten.
Existing deterministic checker, advisory AI, evidence layer, capability policy,
claims lock, and fail-closed semantics are preserved.

### New modules

```
backend/src/aerobim/domain/
  package_manifest.py     # P0-A: deterministic intake
  job_state.py            # P0-C: durable job state machine
  evidence_provenance.py  # P0-G: evidence chain per finding
  finding_lifecycle.py    # P1-E: finding lifecycle + remark workflow
  regulation_model.py     # P1-A: regulatory information model
  annotation_protocol.py  # P1-H: double annotation + kappa
  ai_provenance.py        # P1-R: AI output provenance
  mep_layers.py           # P1-N: MEP 5-layer capability split
  cde_roundtrip.py        # P1-L: BCF 3.0 local CDE simulator

backend/src/aerobim/tools/
  evaluate_benchmark.py   # P1-G: evaluation harness

backend/tests/
  test_p0_p1_upgrade.py   # Tests for all new modules

docs/architecture/
  ADR-007-regulatory-information-model.md
  ADR-006-evaluation-harness-benchmark.md
```

### Architectural principle enforced

```
DeterministicVerdict(AI_ON) == DeterministicVerdict(AI_OFF)
```

Tested in `TestDeterminismInvariant`. AI_ADVISORY evidence is always marked;
it cannot set deterministic verdict. `EvidenceRecord.extraction_method` is
required; `AI_ADVISORY` method automatically sets `is_ai_advisory=True`.

---

## 4. P0 Closure

### P0-A: Robust Package Intake
- `PackageManifest` with deterministic `package_id` (sha256-based)
- Per-file: `logical_path, sha256, size, media_type, role, discipline, revision, source`
- `manifest_sha256` covers all files; tampering detectable via `verify_integrity()`
- `UploadState`: PENDING / COMPLETE / QUARANTINED / TOMBSTONED
- Tombstone preserves identity while clearing physical bytes
- **Integration with upload API / security regression tests: application layer task (P0-B)**

### P0-B: Tenant / Object Security
- `authenticate → authorize → fetch` principle documented
- Security regression test patterns specified in requirements
- **Runtime enforcement: application/infrastructure layer task (not changed in this PR)**
- Principle: package_id, tenant_id, project_id embedded in manifest and verified before fetch

### P0-C: Durable Job System
- Formal `JobStatus` enum: QUEUED/RUNNING/SUCCEEDED/FAILED/CANCEL_REQUESTED/CANCELLED/EXPIRED
- `_TRANSITIONS` table: illegal transitions raise `ValueError` (fail-closed)
- Heartbeat: `job.heartbeat()` → `last_heartbeat_at`; `is_stale()` checks 120s timeout
- Stale recovery: `expire_stale()` → EXPIRED → re-queue via `can_retry()`
- `idempotency_key = sha256(package_id+norm_pack_hash+engine_version+config_hash)`
- Duplicate job detection: same idempotency_key → return existing result
- Stage-level progress: `start_stage() / finish_stage() / progress_pct`

### P0-G: Evidence-First Architecture
- `EvidenceRecord` with full provenance: source_hash + locator + actual/expected +
  extraction_method + rule_version + norm_pack_version + norm_pack_hash +
  engine_version + configuration_hash
- `provenance_id = sha256(all_reproducibility_fields)[:24]`
- `ExtractionMethod.AI_ADVISORY` automatically sets `is_ai_advisory=True`
- AI_ADVISORY evidence cannot set deterministic verdict (enforced in application layer)
- `FindingProvenance` aggregates evidence chain; `is_reproducible` property

---

## 5. P1 Closure

### P1-A: Regulatory Information Model
- Full chain: `NormPack → ComplianceRule → NormRef + RuleInterpretation`
- `RuleInterpretation` with 4 independent review statuses; all must be APPROVED
- `ComplianceRule.stable_version` immutable after approval
- `rule_hash` over content fields; change → new version
- `NormPack.finalise()` seals `pack_hash` over all rule hashes
- `ExecutionProvenance` record for each run: pack_hash + rule_hash + input_hash +
  engine_version + configuration_hash + result_hash
- ADR-007 documents the decision. ADR-005 stays the customer-data policy.

### P1-B: Versioned Norm Packs
- `NormPack.finalise()` → immutable `pack_hash`
- `ExecutionProvenance` stores all hashes needed for reproduction
- Migration of existing norm packs to new schema: **application layer task**

### P1-E: Revision Intelligence
- `FindingStatus`: NEW/PERSISTED/RESOLVED/REGRESSED/REOPENED/SUPERSEDED/NOT_VERIFIED
- `fingerprint = sha256(rule_id:rule_version:sorted(evidence_refs))[:16]`
- `classify_finding_against_previous()`: NEW / PERSISTED / REGRESSED
- `ElementRevisionDiff.change_category`: includes `RULE_IMPACTING_CHANGE`
- `RemarkVersion` with `generated / reviewer_edited / approved` layers

### P1-G: Evaluation Harness
- `BenchmarkDatasetManifest` with `manifest_hash` sealing all `case_hash`es
- `case_hash = sha256(input_hash+gold_label+rule_id+corpus_type)`
- `verify_integrity()` checks all hashes before evaluation
- Per-rule `RuleMetrics`: tp/fp/tn/fn/abstained/errors
- `false_negative_rate` always computed and exposed
- Aggregate: macro + micro precision/recall/F1 + `macro_fn_rate`
- Corpus type always separate: `CorpusType.PUBLIC/SYNTHETIC/CUSTOMER`
- ADR-006 documents the decision

### P1-H: Double Annotation Protocol
- `Annotation` (annotator A + B) → `AnnotationPair` → `Adjudication` → gold label
- Raw labels never deleted; disagreement always preserved
- `compute_cohen_kappa(pairs)`: full confusion-matrix kappa
- `compute_batch_metrics()`: agreement_rate + kappa + adjudication_rate + categories
- Protocol document: `docs/evaluation/annotation-protocol.md` **(to be created)**

### P1-L: BCF 3.0 + Local CDE
- `BCFTopic` with BCF 3.0 fields + AeroBIM linkage (`finding_id, rule_id, norm_pack_hash`)
- `content_hash = sha256(topic_id+title+description+finding_id+revision_id+ifc_guids)`
- `LocalCDESimulator.verify_roundtrip()`: push → pull → hash equality
- `RoundtripRecord`: OK / HASH_MISMATCH / TOPIC_MISSING / FINDING_UNMATCHED
- **ENGINEERING: DONE** (roundtrip test passes) | **CUSTOMER: NOT_VERIFIED**

### P1-N: MEP 5-Layer Split
- Layer 1 Geometric clash: ENGINEERING_DONE / customer NOT_VERIFIED
- Layer 2 Clearance: PARTIAL / customer NOT_VERIFIED
- Layer 3 System semantics: NOT_VERIFIED / NOT_VERIFIED
- Layer 4 Connectivity/topology: NOT_VERIFIED / NOT_VERIFIED
- Layer 5 Rule-based system compliance: NOT_VERIFIED / NOT_VERIFIED
- `mep_capability_matrix()` exports current status as structured dict

### P1-R: AI Provenance
- `AIProvenanceRecord` per AI output: provider/model/model_version/prompt_template_version/
  toolset_version/temperature/input_hashes/output_hash/timestamp
- `compute_provenance_id(input_hashes, output_hash, model_version, template_version)`
- `AIToolCall.ALLOWED_TOOLS`: 13 named tools; any other raises `ValueError`
- `is_ai_advisory=True` by default; cannot be constructively flipped
- `AIEvaluationMetrics`: hallucination_rate + unsupported_claim_rate + abstention_rate

---

## 6. Security

### Enforced in this PR (domain layer)
- Package identity is content-addressed: tampering with files invalidates `manifest_sha256`
- Tombstone preserves identity while clearing physical bytes (no silent deletion)
- Job idempotency key prevents duplicate evidence on retry
- AI tool calls: allowlist of 13 tools; any unlisted tool raises `ValueError`

### To be enforced in application/infrastructure layer (follow-up)
- `authenticate → authorize → fetch` order for all artifact endpoints
- Security regression tests: cross-tenant object, path traversal, MIME spoofing
- OIDC Authorization Code + PKCE for production auth

---

## 7. Regulatory Traceability

Full chain is now formally modelled and machine-readable:

```
norm_pack (pack_id, version, pack_hash)
  → ComplianceRule (rule_id, stable_version, rule_hash)
    → NormRef (document_id, clause, jurisdiction)
    → RuleInterpretation (approved by 4 reviewers)
    → EvidenceRequirement[] (what must be found)
      → EvidenceRecord (actual, expected, locator, source_hash)
        → FindingProvenance (aggregates all hashes)
          → Finding (lifecycle state, remark versions)
            → BCFTopic (issue handoff contract)
              → CDERoundtrip (resolved/closed)
```

Answer to: *"Why did AeroBIM generate this remark?"*
→ `FindingProvenance.provenance_id` + `EvidenceRecord.provenance_id` per evidence ref
→ Reproducible by: same pack_hash + rule_hash + input_hash + engine_version + config_hash

---

## 8. Evaluation

### Framework status
- Harness: ✅ implemented (`evaluate_benchmark.py`)
- Manifest integrity: ✅ implemented (hash sealing + verification)
- Per-rule FN: ✅ always reported
- Corpus separation: ✅ enforced (no merge across PUBLIC/SYNTHETIC/CUSTOMER)

### Current metrics
| Metric | Value | Corpus | Notes |
|---|---|---|---|
| macro_F1 | 0.86 | SYNTHETIC | From `runtime-baseline-latest.json`; fixture-based |
| macro_F1 | NOT_VERIFIED | PUBLIC | No public dataset run yet |
| macro_F1 | NOT_VERIFIED | CUSTOMER | customer_go=false |
| FNR per rule | NOT_VERIFIED | Any | Requires new benchmark run with new harness |
| kappa | NOT_VERIFIED | Any | Double annotation not completed |

---

## 9. Benchmark

- Manifest versioning: change_reason required; new version on any case change
- Development fixtures (`test/fixtures/`) are structurally separate from evaluation cases
- `case_hash` includes `corpus_type` → PUBLIC case cannot be used as SYNTHETIC case
- `manifest_hash` changes on any case addition/removal/modification

---

## 10. Human Adjudication

- `AnnotationPair`: raw A + B labels preserved
- `Adjudication`: adjudicator creates gold label; outcome tracked
- `AdjudicationOutcome.UNRESOLVABLE`: flagged for protocol committee
- Annotation session_id: reproducibility of annotation environment
- Protocol SSOT: `docs/evaluation/annotation-protocol.md` **(pending)**

---

## 11. AI Governance

### NIST AI RMF alignment
- **GOVERN**: explicit limitations in `stated_limitations` per AI output
- **MAP**: `AIRiskLevel` classification (LOW/MEDIUM/HIGH) per output type
- **MEASURE**: `AIEvaluationMetrics` with hallucination_rate + unsupported_claim_rate
- **MANAGE**: allowlisted tool calls; human reviewer required for all AI_ADVISORY outputs

### ISO/IEC 42001 alignment
- AI management policy: `is_ai_advisory=True` is non-overridable
- Model/version provenance: `provider, model, model_version` per output
- Human oversight: `RemarkVersion` workflow requires `approved_by` for final text
- Reproducibility: `provenance_id` for every AI output

---

## 12. BCF / CDE

- BCF 3.0 topic structure: `topic_id, title, description, status, type, priority,
  author, creation_date, components, viewpoints`
- AeroBIM linkage: `aerobim_finding_id, aerobim_rule_id, aerobim_norm_pack_hash,
  aerobim_revision_id`
- Local CDE simulator: roundtrip identity verified by `content_hash`
- Status update flow: OPEN → IN_PROGRESS → RESOLVED → CLOSED
- openCDE Foundation/Documents APIs: interoperability target (not proprietary replacement)

**ENGINEERING: DONE** (local roundtrip)  
**CUSTOMER: NOT_VERIFIED** (no real customer CDE environment validated)

---

## 13. Revision Revalidation

- `classify_finding_against_previous()`: fingerprint-based lifecycle classification
- `ElementRevisionDiff.change_category`: `RULE_IMPACTING_CHANGE` triggers targeted re-check
- `FindingStatus.SUPERSEDED`: rule version changed; new evaluation replaces
- Targeted re-check scope: only elements with `is_rule_impacting=True` changes
- Proof of sufficient scope: `ElementRevisionDiff` records must cover all changed elements

---

## 14. Performance

- Performance test classes: SMALL / MEDIUM / LARGE (framework specified in requirements)
- Actual measurements: **pending** (requires instrumented pipeline run)
- No SLA claim until measurement satisfies claim policy

---

## 15. Claims Audit

### Claims that remain true after this PR
- `customer_go = false` ✅ (not changed)
- `mep_system_clash = NOT_VERIFIED` ✅ (Layer 3 explicitly NOT_VERIFIED)
- `cde_import = NOT_VERIFIED` (customer environment) ✅
- `macro_f1 = 0.86 (SYNTHETIC fixtures)` ✅ (corpus type label preserved)

### Claims now provable by code
- Deterministic package identity: `test_deterministic_id_same_inputs`
- Job state machine: `test_valid_transition_queued_to_running`
- FN visibility: `test_fn_is_visible`
- AI advisory marking: `test_ai_advisory_flag`
- BCF roundtrip: `test_roundtrip_identity`
- MEP honest claims: `test_layers_3_to_5_not_verified`

---

## 16. Customer Gates

Customer gates remain **external** and **NOT_VERIFIED**:

| Gate | Status | Required for |
|---|---|---|
| Real customer IFC corpus | NOT_VERIFIED | customer_go |
| Dual annotation on customer cases | NOT_VERIFIED | customer benchmark |
| Real CDE environment roundtrip | NOT_VERIFIED | CDE capability claim |
| MEP system-aware verification (Layers 3-5) | NOT_VERIFIED | MEP system claim |
| Customer sign-off (external) | NOT_VERIFIED | customer_go=true |
| Customer data secure storage pipeline | NOT_VERIFIED | RECEIVED→ACCEPTED flow |

`customer_go=false` is the correct and honest state.
It will remain false until all external gates are satisfied by real evidence.

---

## 17. Remaining Risks

| Risk | Severity | Mitigation status |
|---|---|---|
| Application layer doesn't enforce authenticate→authorize→fetch | HIGH | Domain principle documented; app layer implementation pending |
| Existing norm packs not migrated to RIM schema | MEDIUM | Migration script pending (P1-B) |
| No real PUBLIC benchmark run | MEDIUM | Harness ready; dataset licensing review needed |
| Double annotation protocol not yet executed | MEDIUM | Framework ready; annotator engagement needed |
| MEP Layers 3-5 not implemented | HIGH | Explicitly NOT_VERIFIED; honest claim maintained |
| Production auth OIDC not verified | HIGH | Domain policy documented; app layer implementation pending |
| Performance measurements not taken | LOW | Framework specified; SLA claim blocked until measured |

---

## 18. Evidence Artifacts

| Artifact | Location | Attests |
|---|---|---|
| Runtime baseline | `audit/evidence/runtime-baseline-latest.json` | macro_f1=0.86 SYNTHETIC |
| BCF structural handoff | `audit/evidence/bcf-structural-handoff-2026-07-25.json` | BCF export |
| Claims lock 07-17 | `audit/reports/CLAIMS_LOCK_2026_07_17.md` | Claim boundaries |
| Claims lock 07-31 | `audit/reports/CLAIMS_LOCK_2026_07_31.md` | Claim boundaries |
| ADR-001 | `docs/architecture/ADR-001-*.md` | Verdict ownership |
| ADR-007 | `docs/architecture/ADR-007-regulatory-information-model.md` | This PR |
| ADR-006 | `docs/architecture/ADR-006-evaluation-harness-benchmark.md` | This PR |
| P0/P1 tests | `backend/tests/test_p0_p1_upgrade.py` | All new modules |

---

## 19. Final Capability Matrix

| Capability | Engineering Status | Customer Status | Evidence | Limitation |
|---|---|---|---|---|
| Package intake (deterministic) | DONE | NOT_VERIFIED | test_p0_p1_upgrade::TestPackageManifest | App layer integration pending |
| Job state machine | DONE | NOT_VERIFIED | test_p0_p1_upgrade::TestJobStateMachine | Redis integration pending |
| Evidence provenance chain | DONE | NOT_VERIFIED | test_p0_p1_upgrade::TestEvidenceProvenance | App layer wiring pending |
| Regulatory Information Model | DONE | NOT_VERIFIED | test_p0_p1_upgrade::TestRegulationModel | Norm pack migration pending |
| Finding lifecycle | DONE | NOT_VERIFIED | test_p0_p1_upgrade::TestFindingLifecycle | App layer wiring pending |
| Evaluation harness | DONE | NOT_VERIFIED | test_p0_p1_upgrade::TestEvaluationBenchmark | Real benchmark runs pending |
| Double annotation | DONE | NOT_VERIFIED | test_p0_p1_upgrade::TestAnnotationProtocol | Annotator engagement pending |
| BCF 3.0 local roundtrip | DONE | NOT_VERIFIED | test_p0_p1_upgrade::TestCDERoundtrip | Real CDE not validated |
| MEP Layer 1 (geometric clash) | DONE | NOT_VERIFIED | runtime-baseline-latest.json | Customer env not validated |
| MEP Layer 2 (clearance) | PARTIAL | NOT_VERIFIED | – | Fixture-only; not all disciplines |
| MEP Layer 3 (system semantics) | NOT_VERIFIED | NOT_VERIFIED | – | No real IFC with IfcSystem |
| MEP Layer 4 (connectivity) | NOT_VERIFIED | NOT_VERIFIED | – | IfcDistributionPort not in corpus |
| MEP Layer 5 (rule-based system) | NOT_VERIFIED | NOT_VERIFIED | – | Blocked by Layers 3+4 |
| AI provenance | DONE | NOT_VERIFIED | test_p0_p1_upgrade::TestAIProvenance | Hallucination metrics pending |
| AI tool allowlist | DONE | NOT_VERIFIED | test_p0_p1_upgrade::TestAIProvenance | App layer enforcement pending |
| Production OIDC auth | NOT_VERIFIED | NOT_VERIFIED | – | Application layer implementation |
| Customer corpus pipeline | NOT_VERIFIED | NOT_VERIFIED | – | No customer data received |
| customer_go | false | false | – | External customer gates unmet |

---

## Checklist — 15 Definition of Done Questions

1. ✅ Can a user find out exactly why a finding appeared? → `FindingProvenance + EvidenceRecord`
2. ✅ Can a finding be reproduced on the same input/hash? → `provenance_id` over stable fields
3. ✅ Can the norm version used be determined? → `norm_pack_id + version + pack_hash`
4. ✅ Can the rule used be determined? → `rule_id + stable_version + rule_hash`
5. ✅ Can AI contribution be separated from deterministic result? → `is_ai_advisory` flag
6. ✅ Can a new revision be re-checked? → `classify_finding_against_previous()`
7. ✅ Can a finding be transferred via BCF? → `BCFTopic + LocalCDESimulator`
8. ✅ Can a CDE roundtrip be done via reference implementation? → `verify_roundtrip()`
9. ✅ Can FN/FP/precision/recall be computed? → `evaluate_predictions() + RuleMetrics`
10. ✅ Can expert disagreement be shown? → `AnnotationPair + Adjudication`
11. ✅ Can benchmark purity be proved? → `manifest_hash + case_hash + verify_integrity()`
12. ✅ Can the absence of customer validation be stated? → `customer_go=false` in all reports
13. ✅ Can the system say NOT_VERIFIED instead of false PASS? → `FindingStatus.NOT_VERIFIED`
14. ✅ Can an engineer reproduce execution by hash/version? → `ExecutionProvenance`
15. ✅ Can the full chain from norm to issue be explained? → Full provenance graph in domain

The new types can answer these questions in unit tests. The report a person
opens is still assembled by `EvidenceAssembler`. These fifteen answers are
not properties of that report yet. `customer_go` stays false. RT-001, RT-002,
and RT-003 stay open. A local BCF roundtrip is not an import into a customer CDE.
