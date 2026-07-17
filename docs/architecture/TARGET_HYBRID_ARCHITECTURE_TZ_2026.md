---
title: "AeroBIM Target Hybrid Architecture for Samolet TechLab TZ"
status: active
version: "1.0.0"
last_updated: "2026-07-17"
tags: [aerobim, architecture, openbim, tz, sota-2026, hybrid-ai]
claim_boundary: "Design proposal only. Checkpoint remains NO_GO until RT-001/002/003 evidenced."
---

# Target Hybrid Architecture — AeroBIM × ТЗ Техлаб / Самолёт (SOTA 2026)

**Scope:** architecture, Protocol port signatures, DI tokens, evaluation plan.  
**Not in scope:** full adapter implementations; claims of product accuracy >90%; CDE-ready BCF; customer SLA.

**Authority alignment:** preserves existing four contours in `domain/architecture.py` (`INGESTION → DETERMINISTIC_VALIDATION → AI_ADVISORY → EVIDENCE_REPORTING`) and the hard rule that **only** `DETERMINISTIC_VALIDATION` may set `summary.passed`.

---

## 0. Normative design thesis

Mirhosseini, Shojaei & Sabri (*Building Research & Information*, 2026) formalize an **Accuracy–Flexibility trade-off**: rule/ontology systems give legal traceability but brittle coverage; LLM/ML systems give coverage but opacity and hallucination risk. Their recommended pathway is **hybrid symbolic + neural**. AeroBIM already encodes this as contours; the target architecture **extends ports** without inverting the dependency rule or promoting LLM to sign-off authority.

Complementary anchors:

| Source | Implication for AeroBIM |
|--------|-------------------------|
| Buildings 2026 HITL KG rule-base | Expert confirm/edit → versioned norm pack (already: `NormRulePackVersionStore` + HITL UC) |
| ArchCAD-400k / DPSS (~87.8% semantic F1) | Vector CAD symbol spotting is SOTA baseline; product >90% needs fine-tune **plus** deterministic post-filters |
| TUM / Iversen & Huang 2026 agentic ACC | ReAct + tool-calling over IFC/measurement tools; LLM selects tools, engines execute |
| MCP4IFC / MCP agent pipelines | Tool registry over deterministic IFC APIs outperforms pure RAG for compliance verdicts |
| Claims Lock 2026-07-17 | Forbidden wording until evidence: DWG-ready, MEP-done, calc correctness, >90%, CDE-ready BCF |

---

## 1. Current architecture (as-is)

Package root: `backend/src/aerobim/`.

```text
presentation/http/api.py          FastAPI /v1, capabilities, BCF export
        │ resolve(Tokens.*)
application/use_cases/*           AnalyzeProjectPackage, jobs, IDS, HITL, BCF push
application/services/*            signoff_policy, confidence, spatial, ids_assist stub
        │ depends on Protocols only
domain/ports.py + models.py       Protocol ports, ReportCapabilities honesty
domain/architecture.py            Contours, PrecisionClaim, StageBudget (30 min)
        ▲ implemented by
infrastructure/adapters/*         IfcOpenShell, IfcTester, IfcClash*, RapidOCR*, Docling*, BCF…
infrastructure/di/bootstrap.py    Token → factory wiring
core/di/{tokens,container}.py     String-token DI
```

### Layer responsibilities today

| Layer | Responsibility | Strength |
|-------|----------------|----------|
| **Core** | Settings, DI container, path jail | Adequate |
| **Domain** | ~20 Protocols; findings provenance; honesty capabilities | Strong for IFC/IDS; weak for CV/NLP/DWG |
| **Application** | Package analyze orchestrator; DeterminismGate; ComplianceAgent; async jobs; sign-off | Strong deterministic path; agent advisory-only |
| **Infrastructure** | Real I/O adapters + optional extras | Strong openBIM; OCR optional; no product VLM |
| **Presentation** | HTTP API + frontend review HITL | Adequate for expert assist templates |

### Contour ownership (SSOT)

```text
INGESTION:     RequirementExtractor, DrawingAnalyzer, RasterDrawingAnalyzer, DocumentIdentity,
               CadModelIngestor, OfficeDocumentIngestor, MultimodalDrawingPipeline
DETERMINISTIC: IfcValidator, IdsValidator, ClashDetector, NormRulePackLoader,
               SectionDiffAnalyzer, ExternalEvidenceVerifier, MepSystemGraphProvider,
               QuantityConsistencyChecker, LoadEvidenceVerifier, LogicConsistencyAnalyzer
AI_ADVISORY:   IdsAssistDraftPort (stub), RequirementToIdsCompiler, NormCorpusRetriever,
               ComplianceAgentOrchestrator
EVIDENCE:      AuditReportStore, ReviewEventStore, NormRulePackVersionStore,
               BcfApiClient, RemarkGenerator
```

---

## 2. Gap analysis (ТЗ → status → blocker)

| # | Требование ТЗ | Статус | Что мешает / почему |
|---|---------------|--------|---------------------|
| G1 | Загрузка MS Office, PDF, DWG, IFC | **PARTIAL** | PDF/IFC live. **I1:** `OfficeDocumentIngestor` + `CadModelIngestor` (DXF/ezdxf). Native DWG fail-closed without ODA; `dwg_dxf` never OK (NOT_VERIFIED/FAILED/MISSING) |
| G2 | Анализ 2D (вектор + сканы): объекты, размеры, текст | **PARTIAL** | `RasterDrawingAnalyzer` + structured JSON. **I3:** OCR multimodal degrade; `cv_human_level=MISSING` (no detector+VLM) |
| G3 | BIM: геометрия + атрибуты (стены, перекрытия, сети) | **STRONG / PARTIAL(MEP)** | IfcOpenShell + IDS. **I2a:** `MepSystemGraphProvider` **DI-wired** as Unconfigured → `mep_system_clash=NOT_VERIFIED` (not delivered) |
| G4 | Сопоставление ПД↔РД, расчёты, ТЗ, нормы | **PARTIAL** | SectionDiff + norm packs + OpenRebar/load **сверка**. `calculation_correctness=NOT_IMPLEMENTED`. Customer-approved pack = RT-002 |
| G5 | Коллизии инженерных систем + геометрия | **PARTIAL** | Generic `ClashDetector` (`ifcclash` optional). System-aware MEP clash не runtime |
| G6 | Расчётные ошибки (нагрузки), площади, пространство, логика, missing elements, размеры | **PARTIAL / WEAK depth** | **I2b:** Quantity/Load/Logic ports wired (сверка semantics). Depth ≠ solver correctness; missing-elements/VLM still gap |
| G7 | AI: CV, OCR, NLP, anomalies | **PARTIAL** | OCR + deterministic IDS compile + norm retrieve. **I5:** ComplianceAgent allowlist (advisory→DeterminismGate). LLM IDS = `@sota-stub`; no product VLM/MCP server |
| G8 | Поддержка эксперта: подсветка, RU/EN замечания, edit | **PARTIAL** | Remarks + HITL. **I7:** `drawing_regions` / `divergences` / `advisory_ids_draft` on report; frontend overlay types still incomplete |
| G9 | Точность >90% | **BLOCKED** | PrecisionClaim + κ/α + intake gate. Checkpoint **NO_GO** (RT-001) |
| G10 | Комплект ≤30 мин | **PARTIAL** | StageBudget + jobs; customer SLA **не доказан** |
| G11 | Масштабируемость / стабильность | **PARTIAL** | Redis/Postgres/S3 extras; нет parallel section fan-out как продуктовый контракт |
| G12 | Снижение когнитивной нагрузки | **PARTIAL** | Confidence + priority + BCF; agent evidence packs without VLM reasoning chain |

---

## 3. Target architecture (to-be)

### 3.1 ASCII — five layers + new seams

```text
┌──────────────────────────────── PRESENTATION ────────────────────────────────┐
│  FastAPI /v1/analyze|reports|capabilities|hitl|bcf                           │
│  Frontend: highlight overlays from DrawingRegionRef + edited_remark          │
└─────────────────────────────────────┬────────────────────────────────────────┘
                                      │ Tokens.*
┌──────────────────────────────── APPLICATION ─────────────────────────────────┐
│  AnalyzeProjectPackageUseCase                                                │
│  ├── ComplianceAgentOrchestrator  (ReAct plan; calls ports only)             │
│  ├── DeterminismGate              (engine ≻ LLM; log DIVERGENCE warning)     │
│  ├── SectionParallelScheduler     (fan-out PD/RD + discipline partitions)    │
│  └── ApplyNormRuleHitlEventUseCase / PushReportToBcfApiUseCase               │
└───────────────┬───────────────────────────────┬──────────────────────────────┘
                │ Protocols                     │ Protocols (advisory read)
┌───────────────▼── DOMAIN (pure) ──────────────▼──────────────────────────────┐
│  Contours + PrecisionClaim + EvidenceRef + ValidationIssue provenance          │
│  NEW: CadModelIngestor, OfficeDocumentIngestor, MultimodalDrawingPipeline      │
│       RequirementToIdsCompiler, NormCorpusRetriever, LlmRemarkComposer         │
│       QuantityConsistencyChecker, LoadEvidenceVerifier, LogicConsistencyAnalyzer│
│       MepSystemGraphProvider (promote), DrawingRegionRef, DivergenceRecord     │
│  FORBIDDEN: LLM/VLM/RAG SDK, process.env, ifcopenshell imports                 │
└───────────────────────────────────▲──────────────────────────────────────────┘
                                    │ adapters implement
┌───────────────────────────────────┴── INFRASTRUCTURE ────────────────────────┐
│  EXISTING: IfcOpenShell*, IfcTester*, IfcClash*, RapidOCR*, Docling*, BCF*     │
│  NEW: EzdxfCadIngestor / OdaCadIngestor, LibreOfficeOrDoclingOfficeIngestor    │
│       YoloOrDpssSymbolSpotter, RegionVlmParser, HybridMultimodalPipeline       │
│       ProviderAgnosticLlmClient, VectorNormCorpusStore, McpToolBridge          │
│       QuantityIfcEngine, LoadTableMatcher, CrossSectionLogicEngine             │
│       WiredMepSystemGraphProvider                                              │
└───────────────────────────────────▲──────────────────────────────────────────┘
┌───────────────────────────────────┴── CORE ──────────────────────────────────┐
│  Settings · Container · Tokens (+ new token strings) · path jail               │
└──────────────────────────────────────────────────────────────────────────────┘

Sign-off gate (hard):
  AI_ADVISORY outputs ──► DeterminismGate ──► may ADD warnings / draft remarks
  DETERMINISTIC outputs ──► sole writers of summary.passed / blocking FAILED caps
```

### 3.2 DeterminismGate (mandatory)

```text
for each finding_id:
  if deterministic_engine.has(finding_id):
      verdict = engine.verdict
      if llm_suggests_contrary:
          emit DivergenceRecord(severity=WARNING, source="llm_vs_engine")
          # expert sees warning; sign-off unchanged
  elif only llm.has(finding_id):
      severity = ADVISORY  # never FAIL package alone
      requires_expert_confirm = True
```

Policy already partially present via `signoff_policy.py` (FAILED capabilities block pass) and `IdsAssistDraftPort` boundary. Target: elevate to an explicit application service with persisted `DivergenceRecord` on the report.

---

## 4. New domain ports (signatures)

```python
# --- Ingestion ---

class CadModelIngestor(Protocol):
    """DWG/DXF → canonical drawing graph. Honesty: capability stays MISSING until real I/O."""

    def ingest(self, path: Path, *, revision: str | None = None) -> CadIngestResult: ...


class OfficeDocumentIngestor(Protocol):
    """DOCX/XLSX/PPTX → text + tables as RequirementSource fragments."""

    def ingest(self, path: Path) -> RequirementSource: ...


class MultimodalDrawingPipeline(Protocol):
    """Detector + VLM with mandatory degrade to RasterDrawingAnalyzer when extras absent."""

    def analyze(
        self,
        source: DrawingSource,
        *,
        mode: Literal["auto", "ocr_only", "detector_vlm"],
    ) -> MultimodalDrawingResult: ...


# --- AI advisory (never writes summary.passed) ---

class RequirementToIdsCompiler(Protocol):
    """TZ / narrative norms → draft IDS 1.0 XML and/or Code-Act callable specs."""

    def compile(self, source: RequirementSource) -> IdsCompileDraft: ...


class NormCorpusRetriever(Protocol):
    """RAG over СП/СНиП/ГОСТ + internal standards; returns passages with citations."""

    def retrieve(self, query: str, *, top_k: int = 8) -> list[NormPassage]: ...


class LlmRemarkComposer(Protocol):
    """RU/EN narrative over an already-decided ValidationIssue (+ evidence refs)."""

    def compose(self, issue: ValidationIssue, *, locale: Literal["ru", "en"]) -> GeneratedRemark: ...


# --- Deterministic validation extensions ---

class QuantityConsistencyChecker(Protocol):
    """Areas / space metrics from IFC (+ optional drawing dims). Match vs declared."""

    def check(self, ifc_path: Path, declared: Sequence[QuantityClaim]) -> list[ValidationIssue]: ...


class LoadEvidenceVerifier(Protocol):
    """Load table / calc sheet сверка (numeric match). Not independent solver correctness."""

    def verify(self, request: ValidationRequest) -> list[ValidationIssue]: ...


class LogicConsistencyAnalyzer(Protocol):
    """Cross-section logical gaps (missing paired sheets, orphan refs, revision skew)."""

    def analyze(self, package_manifest: PackageManifest) -> list[ValidationIssue]: ...


class MepSystemGraphProvider(Protocol):  # already in domain/mep.py — wire to DI
    def build(self, ifc_path: Path) -> MepSystemGraph: ...


# --- Application-owned orchestration contracts (not infra) ---

class ComplianceAgentPlan(Protocol):
    """Pure plan object produced by orchestrator; tools are domain port names only."""

    steps: Sequence[AgentToolStep]


@dataclass(frozen=True)
class DivergenceRecord:
    finding_key: str
    engine_verdict: str
    advisory_verdict: str
    resolution: Literal["engine_wins"]
    severity: Literal["WARNING"]
```

`ComplianceAgentOrchestrator` lives in **application** (not domain Protocol for the LLM itself): it depends on `NormCorpusRetriever`, validators, clash, multimodal pipeline, and `DeterminismGate`. Infrastructure supplies `ProviderAgnosticLlmClient` behind a thin `LlmCompletionPort` if needed for planning text — still advisory.

### Supporting domain types (minimal)

```python
@dataclass(frozen=True)
class DrawingRegionRef:
    sheet_id: str
    bbox_xyxy: tuple[float, float, float, float]  # PDF/CAD units
    confidence: float
    modality: Literal["ocr", "detector", "vlm", "vector"]


@dataclass(frozen=True)
class MultimodalDrawingResult:
    annotations: list[DrawingAnnotation]
    regions: list[DrawingRegionRef]
    pipeline_mode_used: str
    degraded: bool
```

---

## 5. Infrastructure adapters + DI tokens

| Adapter | Implements | Extra / license | Degrade |
|---------|------------|-----------------|---------|
| `EzdxfCadIngestor` | `CadModelIngestor` | `ezdxf` (open) | capability `partial` for DXF-only |
| `OdaCadIngestor` | `CadModelIngestor` | ODA/Teigha license | fail-closed if unset |
| `DoclingOfficeDocumentIngestor` | `OfficeDocumentIngestor` | `docling` | text-only fallback |
| `HybridMultimodalDrawingPipeline` | `MultimodalDrawingPipeline` | spotter+VLM extras | → existing RapidOCR |
| `DpssOrYoloSymbolSpotter` | internal helper | GPU optional | skip → OCR |
| `RegionVlmParser` | internal helper | provider-agnostic HTTP | skip → OCR text blocks |
| `HttpOrLocalLlmCompletion` | `LlmCompletionPort` | API key / local | stub advisory |
| `OpenAICompatibleRemarkComposer` | `LlmRemarkComposer` | same | → `TemplateRemarkGenerator` |
| `IdsCompileViaLlmAdapter` | `RequirementToIdsCompiler` | same | → `NarrativeRuleSynthesizer` |
| `ChromaOrPgvectorNormCorpus` | `NormCorpusRetriever` | vector store | empty retrieve + WARNING |
| `IfcQuantityConsistencyAdapter` | `QuantityConsistencyChecker` | ifcopenshell | SKIPPED |
| `SpreadsheetLoadEvidenceAdapter` | `LoadEvidenceVerifier` | openpyxl | SKIPPED |
| `ManifestLogicConsistencyAdapter` | `LogicConsistencyAnalyzer` | — | SKIPPED |
| `IfcMepSystemGraphProvider` | `MepSystemGraphProvider` | ifcopenshell | Unconfigured* |

### New `Tokens` (additive)

```text
CAD_MODEL_INGESTOR
OFFICE_DOCUMENT_INGESTOR
MULTIMODAL_DRAWING_PIPELINE
REQUIREMENT_TO_IDS_COMPILER
NORM_CORPUS_RETRIEVER
LLM_REMARK_COMPOSER
LLM_COMPLETION          # advisory planning only
QUANTITY_CONSISTENCY_CHECKER
LOAD_EVIDENCE_VERIFIER
LOGIC_CONSISTENCY_ANALYZER
MEP_SYSTEM_GRAPH_PROVIDER
DETERMINISM_GATE
COMPLIANCE_AGENT_ORCHESTRATOR
```

Atomic delivery rule: each new port ships with adapter + token + `bootstrap.py` wiring + honesty field update + architecture test in one PR unit.

---

## 6. Metrics strategy (ТЗ KPIs)

### 6.1 Accuracy >90% (publishable)

1. **Ensemble acceptance:** finding accepted for automated severity≥WARNING only if  
   `spotter_conf ≥ τ_s ∧ vlm_conf ≥ τ_v ∧ (rule_hit ∨ deterministic_geometry)`  
   else demote to ADVISORY.
2. **Human-in-the-loop:** dual adjudication on customer corpus; Cohen κ / Krippendorff α (tooling already scaffolded) ≥ agreed threshold before pack approval.
3. **PrecisionClaim gate:** refuse public “>90%” unless `corpus_kind=customer` and `adjudicators≥2` (`architecture.PrecisionClaim`).
4. **Ablations in CI:** OCR-only | detector-only | detector+VLM | +rules — track per-discipline F1, not a single headline number.
5. **Literature realism:** ArchCAD-400k DPSS ~87.8% semantic F1 on CAD symbols; closing the gap to product >90% on *mismatches/collisions* requires rules+HITL, not VLM alone (Buildings 2026 “90% barrier” discussion).

### 6.2 Package ≤30 minutes

Reuse `DEFAULT_PACKAGE_STAGE_BUDGET` (5+18+2+5):

| Contour | Budget | Tactic |
|---------|--------|--------|
| Ingestion | 5 min | Parallel file-type workers; page-hash OCR cache |
| Deterministic | 18 min | Section fan-out; clash tile/partition; IDS early-exit on schema fail |
| AI advisory | 2 min | Hard timeout; drop leftover agent steps; never block pass |
| Evidence | 5 min | Streaming BCF topic build; async persist |

Customer SLA remains **unproven** until measured on customer packages (`measure_package_sla` schema 1.2.0 honesty).

---

## 7. Evaluation plan

| Layer | Method | Gate |
|-------|--------|------|
| Unit | Port contract tests + honesty `assert_honesty_capabilities_not_silently_ok` | PR |
| Fixture detection | Existing `evaluate_detection_precision` | PR |
| Per-discipline F1 | PD/RD, clash, extraction, remark usefulness (expert Likert) | nightly |
| Agent tool-calling | Synthetic AEC-Bench-style tasks: select IFC/IDS/clash/RAG tools correctly | staging |
| Ablation matrix | OCR / spotter / VLM / rules combinations | release |
| Threshold profiles | `ci/thresholds/{strict,pilot,experimental}.json` — experimental may enable VLM without flipping honesty to OK | CI |
| Divergence audit | Count `DivergenceRecord` / package; alert if advisory systematically contradicts engine | ops |
| Publishable precision | Only after RT-001/002 closed | Claims Lock |

---

## 8. Roadmap (iterations by TZ criticality)

| Iter | Priority | Deliverable | Unblocks |
|------|----------|-------------|----------|
| **I0** | P0 | Document DeterminismGate; extend Claims Lock for new ports; no capability→OK without evidence | Governance |
| **I1** | P0 | `CadModelIngestor` + `OfficeDocumentIngestor` + honesty transitions | G1 |
| **I2** | P0 | Wire `MepSystemGraphProvider`; add Quantity/Load/Logic ports (match semantics) | G3–G6 |
| **I3** | P1 | `MultimodalDrawingPipeline` with OCR degrade; region refs for UI highlight | G2, G8 |
| **I4** | P1 | `RequirementToIdsCompiler` + `NormCorpusRetriever` + HITL promote-to-pack | G4, G7 |
| **I5** | P1 | `ComplianceAgentOrchestrator` + MCP tool registry over existing deterministic ports | G7, G12 |
| **I6** | P0↔P2 | Customer corpus intake, κ/α, publishable PrecisionClaim, SLA proof | G9, G10 |
| **I7** | P1 | Persist divergences / IDS draft / regions; expand agent tools | G8, G12 |
| **I8** | P1 | Blueprint regions + RASE provenance + HITL region escalate | G2, G7, G8 |
| **I9** | P2 | IfcLLM-style knowledge-graph query port (advisory) | G3, G12 |

**Do not** claim GO after I1–I9 alone without RT-001/002/003.

---

## 9. Risks and mitigations

| Risk | Severity | Mitigation |
|------|----------|------------|
| LLM/VLM hallucinations → false compliance | CRITICAL | DeterminismGate; advisory-only contour; provenance mandatory; forbidden `summary.passed` writers |
| Poor scan quality | HIGH | Confidence τ; OCR fallback; expert highlight confirm |
| Lack of customer labeled data | CRITICAL | RT-001 intake gate; no publishable >90% |
| DWG ODA licensing / cost | MED | ezdxf first; ODA optional licensed adapter; honesty MISSING until evidenced |
| GPU / VLM cost vs 30 min budget | HIGH | Cap AI contour 2 min; batch regions; cache embeddings |
| Overfitting fixture macro_f1 | HIGH | Separate fixture vs customer metrics; Claims Lock |
| Agent infinite tool loops | MED | Max steps; allowlist tools = DI ports only; sandbox |
| Norm corpus copyright / licensing | MED | Customer-approved packs only for sign-off; RAG cite + pack version |

---

## 10. Mapping to existing honesty fields

| Field today | Target transition rule |
|-------------|------------------------|
| `dwg_dxf=MISSING` | → `PARTIAL` only with CadModelIngestor real I/O + tests; → `OK` only with customer DWG evidence |
| `cv_human_level=MISSING` | Never auto-OK; multimodal may set `PARTIAL` with F1 report on named corpus |
| `mep_system_clash=NOT_VERIFIED` | → evaluated after DI-wired provider + federated MEP fixture/customer |
| `calculation_match` | Load/OpenRebar сверка may be `OK/FAILED` |
| `calculation_correctness=NOT_IMPLEMENTED` | Remains until independent solver identity — do not conflate with match |

---

## 11. References (selected)

1. Mirhosseini N., Shojaei D., Sabri S. (2026). *A systematic review of methods for interpreting building code regulations in automated compliance systems.* Building Research & Information. https://doi.org/10.1080/09613218.2026.2637965  
2. Human-in-the-Loop Semantic Rule Base… Knowledge Graph Approach. *Buildings* 2026, 16(4), 719. https://doi.org/10.3390/buildings16040719  
3. Luo et al. ArchCAD-400K / DPSS — panoptic symbol spotting baseline (arXiv:2503.22346).  
4. Iversen & Huang (2026) / TUM agentic ACC tool-calling lineage (cited in EC3 multimodal ReAct distance-tool work).  
5. MCP4IFC (2025): MCP + IfcOpenShell tool registry for LLM–BIM interaction.  
6. Seefried et al. (2026). *Blueprint — Multimodal Retrieval for Complex Engineering Drawings* (arXiv:2602.13345) — region-detect → VLM OCR.  
7. Lamsal et al. (2026). *IfcLLM — NL querying of IFC via relational + graph backends* (arXiv:2605.13236).  
8. AeroBIM research map: [`RESEARCH_ALIGNMENT_AEC_AI_2025_2026_07.md`](RESEARCH_ALIGNMENT_AEC_AI_2025_2026_07.md).  
9. AeroBIM SSOT: `domain/architecture.py`, `audit/reports/CLAIMS_LOCK_2026_07_17.md`, `GET /v1/system/capabilities`.

---

## 12. Immediate next engineering slice (recommended)

**Shipped:** I0–I7 + Track E + **I8a/b/c**. Next engineering: **I9** IfcKnowledgeGraphPort. Customer: RT-001/002/003.

**Next (literature-aligned, still no engineering GO):**

1. **Customer-blocked (P0):** RT-001/002/003 — corpus, approved norms, federated MEP.  
2. **I9 (P2):** IfcLLM-style `IfcKnowledgeGraphPort` + allowlisted advisory query (never sign-off).  
3. Optional YOLO weights behind same `DrawingRegionDetector` port (cv stays MISSING).  
4. FE filter for `hitl_required` regions (UX polish).

See [`RESEARCH_ALIGNMENT_AEC_AI_2025_2026_07.md`](RESEARCH_ALIGNMENT_AEC_AI_2025_2026_07.md) · [`EXECUTION_PLAN_I8_I9_2026_07.md`](EXECUTION_PLAN_I8_I9_2026_07.md) · [`EXECUTION_PLAN_NEXT_2026_07.md`](EXECUTION_PLAN_NEXT_2026_07.md) · **гиперплан:** [`EXECUTION_PLAN_HYPERDEEP_2026_07.md`](EXECUTION_PLAN_HYPERDEEP_2026_07.md).

Checkpoint remains **NO_GO** until RT-001/002/003.
