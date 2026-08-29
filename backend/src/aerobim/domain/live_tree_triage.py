"""Live-tree Red Team triage 2026-08-27 — attacks, not RT CLOSED.

Pass 1: TZ v1 / inject_defects / kitchen tokens.
Pass 2: KT#3 jury CLI, tracker six tasks, unsigned OOS, owner inventory.
Pass 3: OOS manifest gate, remark storey/axis from IfcSpatialIndex, packs/day not SLA.
Pass 4: 25.08 channel speech, analyze cap vs ingest, axis not nearest-grid, OIDC BFF, RT-002b.
Pass 5: xlsx/docx table MATCH ≠ solver; PDF LIRA fragile; streaming design ≠ raised cap.
Pass 6: HTTP .lir/.spr honesty reason; JSON sidecar ≠ disk R-tree.
Pass 7: typical-remarks checklists in files/ ≠ accepted catalog; MVP page counts ≠ rehearsal pin.
Pass 8: share-link origin names the customer CDE ≠ import proven; demo-license
synthetic push is an engineering path, not customer-registry evidence.
Pass 9: TZ clash criterion >90% is unmeasurable on the delivered pack
(no federated / no RD IFC in the inventory pin) — never claim otherwise.
Pass 10: answers doc 25.08 beats the chat retelling — standards list was ISSUED
(internal links), federation lives in NWD, calc compare targets PDF/Excel notes,
direct CDE integration is NOT required (п. 2.2.2), numeric criteria stay
unconfirmed, spec-volume compare is a new mandatory gap.
Pass 11: leftover answers clauses — typical nodes are PDF/DWG only (п. 1.2.3);
cloud + per-project isolation (п. 3.1.1); scale is architecture-only (п. 3.2.2);
п. 3.1.2 is the customer's own depersonalization+NDA clause, not our extra ask.
Pass 12: denylist pointer and root-list class defect; version overlay and
machine-readable requirements are not differentiators; foreign metrics stay
attributed; GOST R 72514 self-assessment; licensed registry as alternate
norm path; questionnaire/video are publication.
Pass 13: remark shape is a schema, not prose; three finding gates are not
a 90% claim; SP63 cover template is not customer_approved; AeroBIM does
not replace the bSI Validation Service.
Pass 14: token scan is fail-closed on oversized and non-UTF-8 blobs;
document extract for PDF/Office/ZIP; guard files derived from imports;
CI denylist is B64-only.
Pass 15: spec vs schedule vs BIM quantities on declared triples (TR-67);
not estimate QTO; not customer-pack ingest.
Pass 16: 29.08 SOTA (drawings + clash) — FloorPlanCAD PQ not comparable
across papers; DPSS F1≠PQ; VLM is document assistant not drawing literacy;
clash-report ML numbers are not our filter.
Pass 17: DrawingVQA Gemini-3 77.2 is supplementary, not the main table
(Gemini-2.5-pro 71.7); DWG layers ≠ native DWG; OmniDocBench 0.95 ≠
construction OCR; IfcOpenShell R-tree discussion ≠ our disk index;
4B domain FT is not a shipped model.
Pass 18: attributed MIK commission weights (K1=40, mean, prize floor 50);
official GOST R 72514 card keeps order 64-st; 72515 is a taxonomy map,
not certification; bill 166424 is not in force.
Pass 19: System B (Appendix 3) B1=30; B2 needs partner metrics not pytest;
fixture SLA is not representative; handout 07 is not Appendix 4 №6.
Pass 20: evidence map is findability not a score; 42001 mapping is not
a certified AIMS; i.moscow/pilot is not the TechLab 2M prize; K1 template
person cells stay empty; LETI table corroborates Appendix 4 row 6.
Pass 21: prize floor reachable at top of K1-low if rest is high; 10 people
not required; K3 is fit not B2; TRL self-assess 4 is not TRL 5.
Does not raise IFC cap. Does not parse RVT/NWD/LIRA.
"""

from __future__ import annotations

from typing import Final

CLAIM_LEVEL: Final = "coverage_map_only"
CHECKPOINT: Final = "NO_GO"
CLAIM_BOUNDARY: Final = (
    "Live-tree Red Team triage. Not customer precision. Not TZ v1 as a "
    "product score. MIK act uses interim 0.60. Checkpoint NO_GO. "
    "closes_rt001/002/003=false."
)

# Verdict is KILL / HOLD / ACCEPT. Brake is the code or speech stop, not a fix of RT.
TRIAGE_ROWS: Final[tuple[dict[str, str], ...]] = (
    {
        "id": "RT-V1-01",
        "verdict": "KILL",
        "attack": "Cite TZ v1 clash/nonconformity target as a measured AeroBIM score",
        "brake": "mik_act_may_cite_tz_v1_accuracy_as_measured() is False; IUA SAM-10",
    },
    {
        "id": "RT-V1-02",
        "verdict": "KILL",
        "attack": "Glue v1 brief, v2 TR, seven TechLab tasks, and house design TZ",
        "brake": "PAPER_OBJECTS length 4; snapshot not_the_same_as",
    },
    {
        "id": "RT-V1-03",
        "verdict": "KILL",
        "attack": "Commit the 6-page PDF binary or treat its sha256 as NDA pack_hash",
        "brake": "binary_in_git False; snapshot has no customer pack_hash",
    },
    {
        "id": "RT-V1-04",
        "verdict": "KILL",
        "attack": "MIK act cites v1 accuracy instead of interim 0.60",
        "brake": "pilot_interim_precision 0.60; mik_act_horizon interim_tp_fp_ge_0_60",
    },
    {
        "id": "RT-INJ-NEST",
        "verdict": "KILL",
        "attack": "inject_defects output nested in source rmtree/mutates the pack",
        "brake": "_reject_unsafe_inject_trees refuses equal and nested trees",
    },
    {
        "id": "RT-INJ-NDA",
        "verdict": "KILL",
        "attack": "inject_defects source is samples/customer or repo files/",
        "brake": "posix markers /samples/customer and /aerobim/files/",
    },
    {
        "id": "RT-KIT-01",
        "verdict": "KILL",
        "attack": "Re-introduce protected locators into the public tree",
        "brake": "lint_claims kitchen denylist (HMAC pin; literals outside git)",
    },
    {
        "id": "RT-KT3-01",
        "verdict": "KILL",
        "attack": "Fixture passed=false or a live CLI means Checkpoint GO",
        "brake": "require_kt3_jury_gate rejects passed=True; checkpoint stays NO_GO",
    },
    {
        "id": "RT-KT3-02",
        "verdict": "KILL",
        "attack": "Lead the jury with REQ-AREA and a null GUID",
        "brake": "select_jury_finding skips REQ-AREA and empty GUIDs",
    },
    {
        "id": "RT-KT3-03",
        "verdict": "KILL",
        "attack": "Fixture mep_system_clash=OK means MEP delivered",
        "brake": "require_kt3_jury_gate rejects OK/DELIVERED",
    },
    {
        "id": "RT-TRK-05",
        "verdict": "KILL",
        "attack": "Publish scheduled-demo KPI 3-5 as a git fact",
        "brake": "scheduled_demos_in_git is False; require_honest_kt3_payload",
    },
    {
        "id": "RT-TRK-GO",
        "verdict": "KILL",
        "attack": "Tracker agent_done_count means six customer tasks closed",
        "brake": "owner_blocked_count >= 4; checkpoint NO_GO",
    },
    {
        "id": "RT-OOS-01",
        "verdict": "KILL",
        "attack": "Unsigned OOS licenses skip, or signed OOS closes RT",
        "brake": "evaluate_oos: unsigned does not license skip; accepted never closes RT",
    },
    {
        "id": "RT-INV-01",
        "verdict": "KILL",
        "attack": "Write files/ names or hashes into docs/ or samples/",
        "brake": "require_local_only_output; public rehearsal names_in_git False",
    },
    {
        "id": "RT-OOS-MANIFEST",
        "verdict": "KILL",
        "attack": "Leave samples/oos on disk but omit them from DATASET_MANIFEST",
        "brake": "test_samples_manifest_gate; export_samples_manifest --merge-missing",
    },
    {
        "id": "RT-REMARK-LOC",
        "verdict": "KILL",
        "attack": "Invent storey/axis from OCR, target_ref, or LLM text",
        "brake": "TemplateRemarkGenerator uses stamped storey_name/grid_axis from IfcSpatialIndex",
    },
    {
        "id": "RT-PACKS-SLA",
        "verdict": "KILL",
        "attack": "Treat customer-stated 5-10 packs/day as a measured SLA",
        "brake": "peak_packs_per_day_mvp is stated text; thresholds publishable_sla is false",
    },
    {
        "id": "RT-NODATA-SPEECH",
        "verdict": "KILL",
        "attack": "Say customer sent no data after the 25.08 channel",
        "brake": "share_url_received; speech_forbid_no_customer_data; pack not in git",
    },
    {
        "id": "RT-IFC-RAISE",
        "verdict": "KILL",
        "attack": "Raise default AEROBIM_MAX_IFC_BYTES to the stated 1.5 GB model cap",
        "brake": "analyze default stays 256 MiB; ingest caps are separate",
    },
    {
        "id": "RT-AXIS-NEAR",
        "verdict": "KILL",
        "attack": "Claim nearest IfcGrid intersection as axis in remarks",
        "brake": "IfcGridAxis.AxisTag only; nearest intersection is not implemented",
    },
    {
        "id": "RT-CLOUD-OIDC",
        "verdict": "KILL",
        "attack": "HTTPS closed-cloud ask means browser OIDC BFF is live",
        "brake": "auth_bff NOT_IMPLEMENTED; production BFF still 501",
    },
    {
        "id": "RT-002-SPPACK",
        "verdict": "KILL",
        "attack": "An unsigned SP 63/20 pack closes RT-002b / RT-002",
        "brake": "RT-002a city IDS; RT-002b needs Samolet signature; closes_rt002 false",
    },
    {
        "id": "RT-LIRA-SOLVER",
        "verdict": "KILL",
        "attack": "Treat xlsx/docx table MATCH as calculation_correctness",
        "brake": "compare_declared_tables solver not_implemented; native_lir closed",
    },
    {
        "id": "RT-PDF-LIRA",
        "verdict": "KILL",
        "attack": "Parse LIRA PDF as a declared table compare",
        "brake": "extract status pdf_fragile; SpreadsheetLoadEvidenceAdapter LIRA-PDF",
    },
    {
        "id": "RT-IFC-STREAM",
        "verdict": "KILL",
        "attack": "Treat streaming design as live disk R-tree or raised analyze cap",
        "brake": "streaming_design_snapshot raises_default_cap False; 256 MiB default",
    },
    {
        "id": "RT-ZIP-SNIFF",
        "verdict": "KILL",
        "attack": "ZIP namelist on sniff prefix turns zip-bomb into 415",
        "brake": "sniff is magic only; inspect_zip_path 422 then Autodesk/LIRA 415",
    },
    {
        "id": "RT-LIRA-HTTP",
        "verdict": "KILL",
        "attack": "HTTP .lir/.spr as generic disallowed extension hides honesty",
        "brake": "NATIVE_LIRA_CLOSED_REASON 415; ZIP members after inspect_zip_path",
    },
    {
        "id": "RT-SIDECAR-RTREE",
        "verdict": "KILL",
        "attack": "JSON sidecar of IfcSpatialIndex is a live disk R-tree",
        "brake": "disk_r_tree designed_not_implemented; sidecar dump_only; cap 256 MiB",
    },
    {
        "id": "RT-TYP-CATALOG",
        "verdict": "KILL",
        "attack": "Call typical-errors catalog accepted while confirmed=0, checklists untriaged",
        "brake": "customer_share_ingested false; checklists ingested_into_patterns=0",
    },
    {
        "id": "RT-PAGE-DRIFT",
        "verdict": "KILL",
        "attack": "MVP page rows (11 Autodesk, 1133 scan PDF, 51 TZ) override the inventory pin",
        "brake": "PUBLIC_REHEARSAL 27 rvt + 21 navis + 1127 pdf; rehearsal_differs flags drift",
    },
    {
        "id": "RT-CDE-IDENT",
        "verdict": "KILL",
        "attack": "Share-link origin names the customer CDE, so claim CDE import/integration",
        "brake": "cde_import=NOT_VERIFIED until T2 log+shot+hashes; demo push ≠ customer registry",
    },
    {
        "id": "RT-CLASH-MEASURE",
        "verdict": "KILL",
        "attack": "Say the TZ clash criterion (>90%) is measurable or closed on the delivered pack",
        "brake": "PUBLIC_REHEARSAL federated_mep_ifc_present=False, rd_ifc_present=False",
    },
    {
        "id": "RT-NORM-ACCESS",
        "verdict": "KILL",
        "attack": "Repeat norm-pack blocker is missing customer data",
        "brake": "List issued 25.08 (two links in 1.2.1); blocker is ACCESS to internal folders",
    },
    {
        "id": "RT-NWD-FED",
        "verdict": "KILL",
        "attack": "Frame federated IFC as a customer gap we wait for",
        "brake": "Federation exists as NWD; ask NWD→IFC batch export on one building",
    },
    {
        "id": "RT-SPEC-VOL",
        "verdict": "KILL",
        "attack": "Treat п. 2.1.3 logical clashes as geometry or skip them",
        "brake": "spec_volume_compare on declared triples; not estimate QTO; not customer pack",
    },
    {
        "id": "RT-INTEGRATION-OWN",
        "verdict": "KILL",
        "attack": "Present direct CDE API integration as a customer requirement",
        "brake": "Answers п. 2.2.2: file exchange suffices; API demo is optional differentiator",
    },
    {
        "id": "RT-90-SILENCE",
        "verdict": "KILL",
        "attack": "Treat >90% clash / pack-time criteria as customer-confirmed",
        "brake": "Zero mentions of 90%/SLA/minutes in the answers doc; protocol question pending",
    },
    {
        "id": "RT-CLASS-TERM",
        "verdict": "KILL",
        "attack": "Write марка бетона/стали in our outputs",
        "brake": "СП 63 wording is класс; марка stays only as an input parser alias",
    },
    {
        "id": "RT-TYP-NODES",
        "verdict": "KILL",
        "attack": "Treat typical-node check as IFC-ready or as a missing customer gap",
        "brake": "п. 1.2.3: nodes are PDF/DWG in the closed 1.2.1 folders; no IFC nodes",
    },
    {
        "id": "RT-CLOUD-ISO",
        "verdict": "KILL",
        "attack": "Require on-prem deploy or treat HTTPS as the isolation requirement",
        "brake": "п. 3.1.1: cloud OK; isolation is per-project access, not encryption",
    },
    {
        "id": "RT-SCALE-MVP",
        "verdict": "KILL",
        "attack": "Promise load numbers or horizontal scale as an MVP deliverable",
        "brake": "п. 3.2.2: architecture points only; no load figures at defense",
    },
    {
        "id": "RT-NDA-STATED",
        "verdict": "KILL",
        "attack": "Frame the depersonalization/NDA ask as our extra caution",
        "brake": "п. 3.1.2 is the customer's own clause; ask organizers to execute it",
    },
    {
        "id": "RT-KIT-PTR",
        "verdict": "KILL",
        "attack": "Describe denylist composition in public files so a later search reconstructs it",
        "brake": "Guard invariant: no composition speech; literals stay outside git",
    },
    {
        "id": "RT-KIT-ROOTS",
        "verdict": "KILL",
        "attack": "Hand-list content directories so a new guard folder is a blind zone",
        "brake": "git ls-files walk; listing content roots is a class defect",
    },
    {
        "id": "RT-KIT-SCAN-SIZE",
        "verdict": "KILL",
        "attack": "Skip blobs larger than the scan window so a mid-size locator is never read",
        "brake": "Overlapping byte windows; skip is fail-open",
    },
    {
        "id": "RT-KIT-SCAN-BIN",
        "verdict": "KILL",
        "attack": "Skip non-UTF-8 files and leave pack document formats unscanned",
        "brake": "Raw-byte scan plus PDF/Office/ZIP text extract",
    },
    {
        "id": "RT-KIT-GUARD-LIST",
        "verdict": "KILL",
        "attack": "Hand-list guard files so a new importer is outside the invariant",
        "brake": "Guards = this module plus tracked importers",
    },
    {
        "id": "RT-KIT-PLAINTEXT",
        "verdict": "KILL",
        "attack": "Keep a plaintext multiline denylist secret after it already dropped tokens",
        "brake": "CI materialize accepts B64 only; pin count must match",
    },
    {
        "id": "RT-POS-VERDIFF",
        "verdict": "KILL",
        "attack": "Sell RD version overlay as a differentiator",
        "brake": "Forbidden wording SSOT; claim boundary §23 — customer already ships it",
    },
    {
        "id": "RT-POS-IDSADV",
        "verdict": "KILL",
        "attack": "Sell machine-readable information requirements as a market advantage",
        "brake": "Forbidden wording; IDS packs are an entry ticket, not a differentiator",
    },
    {
        "id": "RT-POS-FOREIGN-METRIC",
        "verdict": "KILL",
        "attack": "Copy a competitor or paper figure into our materials as our metric",
        "brake": "Foreign figure only with source attribution; never transferred as ours",
    },
    {
        "id": "RT-AI-IMPACT",
        "verdict": "KILL",
        "attack": "Leave AI risk-governance unanswered while GOST R 72514-2026 is in force",
        "brake": "GOST R 72514 self-assessment doc; compatibility is not certification",
    },
    {
        "id": "RT-NORM-MARKET",
        "verdict": "KILL",
        "attack": "Treat the customer internal-folder wait as the only path to a rule source",
        "brake": "Workplan: licensed requirements registry; customer signs a profile",
    },
    {
        "id": "RT-PUB-SURFACE",
        "verdict": "KILL",
        "attack": "Treat catalog questionnaire or demo video as outside the publication gate",
        "brake": "docs/quality/PUBLIC_SURFACES_PROTOCOL_2026.md; six checks per frame",
    },
    {
        "id": "RT-GATE-90",
        "verdict": "KILL",
        "attack": "Read schema/quality/regulatory counts as product accuracy >90%",
        "brake": "HTML finding-gates: grouping analog, not a 90% claim",
    },
    {
        "id": "RT-SP63-APPR",
        "verdict": "KILL",
        "attack": "Treat SP63-COVER-SLAB-001 template as customer_approved",
        "brake": "pack approval null; clause 8.3 (template); not table 8.1",
    },
    {
        "id": "RT-BSI-REPL",
        "verdict": "KILL",
        "attack": "Claim AeroBIM replaces the bSI Validation Service",
        "brake": "validation-layers doc: compatibility is not replacement",
    },
    {
        "id": "RT-REMARK-SHAPE",
        "verdict": "KILL",
        "attack": "Ship customer remarks as title+body without essence/clause/location",
        "brake": "validate_remark_shape; TemplateRemarkGenerator rejects",
    },
    {
        "id": "RT-SOTA-PQ-MIX",
        "verdict": "KILL",
        "attack": "Mix FloorPlanCAD PQ across papers or cite VecFormer/DPSS as ours",
        "brake": "PQ incomparable across papers; Luo F1 87.8 ≠ PQ 70.6; not AeroBIM",
    },
    {
        "id": "RT-SOTA-CLASH-ML",
        "verdict": "KILL",
        "attack": "Cite Lin 0.96 or Ailem 60% FP as our clash filter or differentiator",
        "brake": "Deterministic triage never drops a clash; no ML relevance model",
    },
    {
        "id": "RT-SOTA-VLM-LIT",
        "verdict": "KILL",
        "attack": "Treat VLM/AECV scores as drawing literacy or TZ sheet sign-off",
        "brake": "cv_human_level=MISSING; DrawingVQA/AECV stay open_bench_only",
    },
    {
        "id": "RT-SOTA-DWG-LAYER",
        "verdict": "KILL",
        "attack": "Cite SOTA layer/block/ATTRIB labels as native DWG reading",
        "brake": "dwg_dxf MISSING on analyze; ODA not on the analyze path",
    },
    {
        "id": "RT-SOTA-SUPPL",
        "verdict": "KILL",
        "attack": "Treat DrawingVQA supplementary Gemini-3 77.2 as the main-table SOTA",
        "brake": "Main table Gemini-2.5-pro 71.7 vs professionals 94.9; 77.2 is appendix",
    },
    {
        "id": "RT-SOTA-OCR-PROXY",
        "verdict": "KILL",
        "attack": "Cite OmniDocBench or titleblock ~0.95 as construction-sheet OCR",
        "brake": "RapidOCR extra; layout corpora are not AEC sheets; not GOST stamp",
    },
    {
        "id": "RT-SOTA-FT4B",
        "verdict": "KILL",
        "attack": "Cite MechVL-4B beating frontier as a model we ship",
        "brake": "No domain-FT 4B in runtime; VLM stays advisory if present",
    },
    {
        "id": "RT-SOTA-RTREE-LIT",
        "verdict": "KILL",
        "attack": "Cite IfcOpenShell SQLite R-tree discussion as our persistent index",
        "brake": "disk_r_tree designed_not_implemented; sidecar dump_only",
    },
    {
        "id": "RT-MIK-K1-GIT",
        "verdict": "KILL",
        "attack": "Treat git HEAD or oral advisors as K1=40 closed",
        "brake": "K1 object is the application roster; oral advisors do not score",
    },
    {
        "id": "RT-MIK-PRIZE-50",
        "verdict": "KILL",
        "attack": "Project a prize-clearing total from this repository",
        "brake": "predicted_aerobim_total is None; 50 is the program floor",
    },
    {
        "id": "RT-MIK-AVG",
        "verdict": "KILL",
        "attack": "Treat one harsh commissioner as ignorable for the total",
        "brake": "Aggregation is arithmetic mean, not median or drop-one",
    },
    {
        "id": "RT-MIK-TIE-K2",
        "verdict": "KILL",
        "attack": "Use novelty as the tie-break after equal totals",
        "brake": "Tie-break is K3 then K4; K2 is not in the order",
    },
    {
        "id": "RT-MIK-VITRINE",
        "verdict": "KILL",
        "attack": "Prepare only to the public catalog roster of partner seats",
        "brake": "Signed order beats catalog; three partner seats are by agreement",
    },
    {
        "id": "RT-GOST-ORDER-DROP",
        "verdict": "KILL",
        "attack": "Strip GOST R 72514 order 64-st because the catalog month is March",
        "brake": "Official fund card lists 64-st / 30.01.2026; still not certification",
    },
    {
        "id": "RT-GOST-72515-CERT",
        "verdict": "KILL",
        "attack": "Cite the GOST R 72515 mapping as a conformity certificate",
        "brake": "Taxonomy map of existing honesty; compatibility is not certification",
    },
    {
        "id": "RT-AI-BILL-FORCE",
        "verdict": "KILL",
        "attack": "Cite MinTsifry bill 166424 as in-force law or trusted-model status",
        "brake": "Draft, not in the Duma; planned force 01.09.2027; ADR-001 is not law",
    },
    {
        "id": "RT-MIK-SYS-B-METRICS",
        "verdict": "KILL",
        "attack": "Score System B B2 high because pytest and a protocol exist",
        "brake": "B2 needs partner metrics; confirmed_partner_validation_metrics False",
    },
    {
        "id": "RT-MIK-B2-FIXTURE-SLA",
        "verdict": "KILL",
        "attack": "Cite fixture SLA p95 as the Partner 30-minute pack time",
        "brake": "Fixture pack is not representative; TZ 30 min stays a goal",
    },
    {
        "id": "RT-MIK-TASK-NUM",
        "verdict": "KILL",
        "attack": "Speak the historical handout 07 as the Appendix 4 task number",
        "brake": "Attributed: Appendix 4 task 6; commission 7; 07 is a filename label",
    },
    {
        "id": "RT-MIK-TIE-B",
        "verdict": "KILL",
        "attack": "Use K3 or novelty as the System B tie-break",
        "brake": "Finalist tie-break is B1 only",
    },
    {
        "id": "RT-MIK-42001-CERT",
        "verdict": "KILL",
        "attack": "Cite the 42001 mapping as a certified AI management system",
        "brake": "Official card 1549-st; gost_42001_certified stays False",
    },
    {
        "id": "RT-MIK-CITY-PRIZE",
        "verdict": "KILL",
        "attack": "Cite i.moscow/pilot or 449-PP as the TechLab 2M prize",
        "brake": "City pilots need a legal entity; TechLab prize is separate",
    },
    {
        "id": "RT-MIK-EVIDENCE-SCORE",
        "verdict": "KILL",
        "attack": "Treat the criterion evidence map as a predicted total",
        "brake": "Map is findability; predicted_aerobim_total stays None",
    },
    {
        "id": "RT-MIK-K1-NAMES",
        "verdict": "KILL",
        "attack": "Fill the K1 git template with invented names",
        "brake": "Person cells stay empty; roster is the i.moscow application",
    },
    {
        "id": "RT-MIK-K1-TEN",
        "verdict": "KILL",
        "attack": "Treat ten named people as the only way K1 can clear 50",
        "brake": "LETI min team is 1; two classes; top of K1-low + rest-high ≥50",
    },
    {
        "id": "RT-MIK-K3-AS-B2",
        "verdict": "KILL",
        "attack": "Score System A K3 as if it were B2 partner validation metrics",
        "brake": "K3 is partner-fit; k3_equals_validation_metrics stays False",
    },
    {
        "id": "RT-MIK-TRL5",
        "verdict": "KILL",
        "attack": "Cite CI/fixture as TRL 5 or an independent GOST 58048 OGT",
        "brake": "Self-assess TRL 4; trl_5_claimed False; partner env is TRL 5",
    },
    {
        "id": "RT-MIK-FOREIGN-72",
        "verdict": "KILL",
        "attack": "Cite a published analog 72% labor cut as AeroBIM or partner hours",
        "brake": "foreign_labor_cut_as_ours False; A1-A8 hours stay empty",
    },
    {
        "id": "RT-MIK-BIM-TAM-AS-SAM",
        "verdict": "KILL",
        "attack": "Cite Russian BIM TAM 10.1 bn RUB as AeroBIM SAM or sales",
        "brake": "TAM is labeled context; SAM in rubles is empty; k4_revenue_claimed False",
    },
    {
        "id": "RT-MIK-500M",
        "verdict": "KILL",
        "attack": "Copy another MIK product's >=500M market packaging as this K4",
        "brake": "Different program packaging; TechLab K4 is the 2M paid-pilot path",
    },
    {
        "id": "RT-MIK-PNST-CERT",
        "verdict": "KILL",
        "attack": "Cite the PNST 841 mapping as a SQuaRE or GOST R certificate",
        "brake": "Preliminary standard; pnst_841_certified stays False",
    },
    {
        "id": "RT-MIK-IDENTITY-AS-SCORE",
        "verdict": "KILL",
        "attack": "Cite the 16+36.6 band identity or 'floor is reachable' as our total",
        "brake": "Identity is program arithmetic; predicted_aerobim_total stays None",
    },
    {
        "id": "RT-MIK-SPONSOR-CHAIR",
        "verdict": "KILL",
        "attack": "Treat the public task-page sponsor quote as commission chair or K1",
        "brake": "sponsor_quote_is_commission_chair False; catalog is not the signed roster",
    },
    {
        "id": "RT-MIK-25B-REV",
        "verdict": "KILL",
        "attack": "Cite SPbPU 25.1 bn RUB by 2030 as AeroBIM revenue or SAM",
        "brake": "tam_horizon_is_our_revenue stays False; TAM horizon is not ours",
    },
    {
        "id": "RT-MIK-PASTE-SCORE",
        "verdict": "KILL",
        "attack": "Treat the i.moscow paste file as a scored roster or predicted total",
        "brake": "Paste is field text; person cells empty; predicted_aerobim_total None",
    },
    {
        "id": "RT-SEAM-HOLD",
        "verdict": "HOLD",
        "attack": "Reopen RT-SEAM-01…18 / RT-CART-01…08 as if this pass closed them",
        "brake": "TZ_SEAM_COVERAGE_MAP §5 still Uncertain / coverage_map_only",
    },
    {
        "id": "RT-FULL-D01",
        "verdict": "HOLD",
        "attack": "POST /v1/validate/ifc greens under development sign-off in production",
        "brake": "DI injects settings.signoff_profile; soft passed is non-authoritative",
    },
    {
        "id": "RT-AGR-002",
        "verdict": "HOLD",
        "attack": "moscow_agr_2026 status=approved means Samolet customer_approved",
        "brake": "RT-002a city pack; RT-002b OPEN; profile not customer-hard",
    },
    {
        "id": "RT-INV-HOLD",
        "verdict": "HOLD",
        "attack": "Public rehearsal 2383/15/1 counts are a pack_hash / RT-001 CLOSED",
        "brake": "coverage_map_only; no names/hashes; intake still blocked",
    },
    {
        "id": "RT-ADR-001",
        "verdict": "ACCEPT",
        "attack": "LLM/VLM writes summary.passed",
        "brake": "DeterminismGate demotes advisory to INFO; never flips passed",
    },
    {
        "id": "RT-CAP-IFC",
        "verdict": "ACCEPT",
        "attack": "Raise AEROBIM_MAX_IFC_BYTES because one AR file is over cap",
        "brake": "default stays 256 MiB; owner flag only",
    },
)


def triage_snapshot() -> dict[str, object]:
    return {
        "artifact_type": "live_tree_red_team_triage",
        "claim_level": CLAIM_LEVEL,
        "checkpoint": CHECKPOINT,
        "closes_rt001": False,
        "closes_rt002": False,
        "closes_rt003": False,
        "claim_boundary": CLAIM_BOUNDARY,
        "detected_count": 0,
        "rows": [dict(row) for row in TRIAGE_ROWS],
        "kill_count": sum(1 for row in TRIAGE_ROWS if row["verdict"] == "KILL"),
        "hold_count": sum(1 for row in TRIAGE_ROWS if row["verdict"] == "HOLD"),
        "accept_count": sum(1 for row in TRIAGE_ROWS if row["verdict"] == "ACCEPT"),
    }


__all__ = ["CLAIM_BOUNDARY", "CHECKPOINT", "TRIAGE_ROWS", "triage_snapshot"]
