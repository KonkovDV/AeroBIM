"""UI expert-workplace Red Team triage — 2026-09-01.

The review shell is not a full-cycle expert seat. Path must not contain
the hyphenated token blocked by pre-commit. Checkpoint NO_GO.
"""

from __future__ import annotations

from typing import Final

CLAIM_LEVEL: Final = "coverage_map_only"
CHECKPOINT: Final = "NO_GO"
CLAIM_BOUNDARY: Final = (
    "UI expert-workplace Red Team triage. Current git is a review shell over "
    "persisted reports. TZ wants upload → run → triage → remark → export. "
    "Natives stay fail-closed. UI does not write summary.passed. "
    "Not a 10D/Tangl connector. Checkpoint NO_GO."
)

# Eight-screen IA. git is the honest status, not a delivery claim.
SCREEN_ROWS: Final[tuple[dict[str, str], ...]] = (
    {
        "id": "SCR-PROJECTS",
        "title": "Projects and packs",
        "git": "partial",
        "note": "Persisted report list; picking a pack opens the expert three-pane",
    },
    {
        "id": "SCR-UPLOAD",
        "title": "Pack upload",
        "git": "partial",
        "note": "POST /v1/uploads dropzone + progress + cancel; natives fail-closed in copy",
    },
    {
        "id": "SCR-RUN",
        "title": "Analyze run",
        "git": "partial",
        "note": "jobs/{job_id} poll; engine groups from capabilities; SSE not shipped",
    },
    {
        "id": "SCR-EXPERT",
        "title": "Expert workplace",
        "git": "partial",
        "note": "TZ three-pane: findings | 2D/3D | remark; report index is SCR-PROJECTS",
    },
    {
        "id": "SCR-REMARK",
        "title": "Remark card and editor",
        "git": "partial",
        "note": "HITL remark + review-events history; storey/axis or «нет в индексе»",
    },
    {
        "id": "SCR-EXPORT",
        "title": "Report and export",
        "git": "partial",
        "note": "HTML JSON BCF 2.1/3.0 PDF; XLSX not an API; do not ship a fake 200",
    },
    {
        "id": "SCR-DIFF",
        "title": "Pack version diff",
        "git": "partial",
        "note": "HTTP finding delta; no_longer_reported does not claim resolved",
    },
    {
        "id": "SCR-USER",
        "title": "User-role dashboard",
        "git": "partial",
        "note": (
            "TZ map + intake snapshot + review-kpi; OIDC BFF stays 501"
        ),
    },
)

TRIAGE_ROWS: Final[tuple[dict[str, str], ...]] = (
    {
        "id": "RT-UI-PASSED-FRONT",
        "verdict": "KILL",
        "attack": "Compute or override summary.passed in the browser",
        "brake": "ADR-001: display only; EvidenceAssembler owns the flag",
    },
    {
        "id": "RT-UI-LLM-VERDICT",
        "verdict": "KILL",
        "attack": "Let LLM/VLM text look like a signed expert verdict",
        "brake": "ai_generated stays a draft mark; expert confirmation required",
    },
    {
        "id": "RT-UI-GREEN-SKIP",
        "verdict": "KILL",
        "attack": "Paint a green pack when a required engine is skipped",
        "brake": "Silence is never success; skipped banner above the report",
    },
    {
        "id": "RT-UI-ACCURACY",
        "verdict": "KILL",
        "attack": "Show fixture or competitor percent as product accuracy",
        "brake": "detected_count 0; PrecisionClaim.publishable remains the gate",
    },
    {
        "id": "RT-UI-PARSE-BROWSER",
        "verdict": "KILL",
        "attack": "Parse a 1.5 GB customer model in the tab",
        "brake": "Heavy convert stays on the backend; web-ifc is a fixture viewer",
    },
    {
        "id": "RT-UI-NATIVE-RVT",
        "verdict": "KILL",
        "attack": "UI copy says RVT/NWD/DWG ingest is the KT#3 exchange",
        "brake": "IFC + PDF/A; natives fail-closed before upload",
    },
    {
        "id": "RT-UI-CDE-10D",
        "verdict": "KILL",
        "attack": "Ship live 10D / Tangl / CADLib buttons on MVP",
        "brake": "Customer wrote file import/export; connectors stay unbuilt",
    },
    {
        "id": "RT-UI-SLA",
        "verdict": "KILL",
        "attack": "Print 5-10 packs/day or 30 minutes as a measured SLA",
        "brake": "TZ goal; not a published timer from this shell",
    },
    {
        "id": "RT-UI-FRAG-FED",
        "verdict": "KILL",
        "attack": "Load a federated ~1 GB fragment set into the viewer",
        "brake": "ThatOpen issue; stream by storey/discipline or do not ship",
    },
    {
        "id": "RT-UI-FIO",
        "verdict": "KILL",
        "attack": "Put sitting-member names in the UI or in this pin",
        "brake": "Seat briefs are roles; OA-2",
    },
    {
        "id": "RT-UI-XLSX-FAKE",
        "verdict": "KILL",
        "attack": "Export XLSX button that 404s labeled as delivered",
        "brake": "HTML JSON BCF PDF only until an export route exists",
    },
    {
        "id": "RT-UI-OIDC-LIVE",
        "verdict": "KILL",
        "attack": "Show production SSO while GET /v1/auth/bff is 501",
        "brake": "Lab cookie is not IdP; two roles stay API aliases",
    },
    {
        "id": "RT-UI-NOGO-MASK",
        "verdict": "KILL",
        "attack": "Workplace chrome implies Checkpoint GO or RT closed",
        "brake": "Banner stays NO_GO; UI does not close RT-001/002/003",
    },
    {
        "id": "RT-UI-STACK-CLAIM",
        "verdict": "KILL",
        "attack": "Claim TanStack Router Query Storybook Playwright as shipped",
        "brake": "Sprint 0 stack is a plan; current shell is Vite React vitest",
    },
    {
        "id": "RT-UI-SPLIT",
        "verdict": "HOLD",
        "attack": "Leave App.tsx as the only module forever",
        "brake": "Split by feature when tests stay green; do not gold-plate the stack",
    },
    {
        "id": "RT-UI-THEME",
        "verdict": "HOLD",
        "attack": "Ship neon dark or invent brand-book hex as official Samolet UI",
        "brake": "Laconic light; blue aliases; brand book is not in git",
    },
    {
        "id": "RT-UI-KEYBOARD",
        "verdict": "ACCEPT",
        "attack": "Mouse-only triage of hundreds of findings",
        "brake": "J/K/A/R/E/? plus windowed list above 40 findings",
    },
    {
        "id": "RT-UI-JOBS",
        "verdict": "HOLD",
        "attack": "Pretend SSE and 30-minute first-class timer are already product",
        "brake": "Poll jobs/{job_id}; timer is a TZ goal caption",
    },
    {
        "id": "RT-UI-KEEP-SHELL",
        "verdict": "HOLD",
        "attack": "Delete the review shell before upload-run-export exists",
        "brake": "Keep the shell; add the missing loop around it",
    },
    {
        "id": "RT-UI-HONEST-CAP",
        "verdict": "ACCEPT",
        "attack": "Capability table is enough if buried below the fold",
        "brake": "Blocking and skipped banners stay above findings",
    },
    {
        "id": "RT-UI-HITL-REMARK",
        "verdict": "ACCEPT",
        "attack": "No remark path exists so TZ inline editor is vapor",
        "brake": "review-events edited_remark / accepted / rejected already wire",
    },
    {
        "id": "RT-UI-COV-MAP",
        "verdict": "ACCEPT",
        "attack": "Coverage map is product accuracy",
        "brake": "Per-source family states; not summary.passed",
    },
    {
        "id": "RT-UI-SEAM",
        "verdict": "ACCEPT",
        "attack": "Pitch as a model checker against Tangl/10D",
        "brake": "Pack seam: model sheets TZ calculations; BCF file out",
    },
    {
        "id": "RT-UI-UPLOAD-WIRE",
        "verdict": "ACCEPT",
        "attack": "Upload API unused so TZ upload row looks missing forever",
        "brake": "Shell dropzone calls POST /v1/uploads with fail-closed copy",
    },
    {
        "id": "RT-UI-KPI-WIRE",
        "verdict": "ACCEPT",
        "attack": "review-kpi stays an undocumented endpoint",
        "brake": "Effect dashboard reads GET review-kpi; empty is empty",
    },
    {
        "id": "RT-UI-EIGHT",
        "verdict": "ACCEPT",
        "attack": "Eight screens are already the product",
        "brake": "IA map on this pin; git column is partial or missing",
    },
    {
        "id": "RT-UI-DEMO-PROD",
        "verdict": "KILL",
        "attack": "Treat POST /v1/demo/seed-fixture as a production product API",
        "brake": "Non-dev returns the public 404; samples are git fixtures",
    },
    {
        "id": "RT-UI-DEMO-ACCURACY",
        "verdict": "KILL",
        "attack": "Two IDS fire-rating hits on walls-multi-entity as product accuracy",
        "brake": "detected_count 0; PrecisionClaim.publishable remains the gate",
    },
    {
        "id": "RT-UI-DEMO-PACK",
        "verdict": "KILL",
        "attack": "Call the git seed a processed customer pack",
        "brake": "IDS+IFC walls fixture only; drawings TZ calcs are not in that POST",
    },
    {
        "id": "RT-UI-SEED-PASSED",
        "verdict": "KILL",
        "attack": "Echo summary.passed on the seed JSON so the browser owns the flag",
        "brake": "Seed returns report_id and issue_count; GET report displays the engine flag",
    },
    {
        "id": "RT-UI-TZ-MATRIX-DONE",
        "verdict": "KILL",
        "attack": "Read TZ compliance Web UI = done as workplace delivered",
        "brake": "Matrix row is partial; this pin is the SSOT",
    },
    {
        "id": "RT-UI-JURY-VITE",
        "verdict": "KILL",
        "attack": "Open Vite as the default KT#3 sitting-member laptop track",
        "brake": "Jury laptop stays run_kt3_jury; UI is the IT-mentor track",
    },
    {
        "id": "RT-UI-STORE-NOISE",
        "verdict": "HOLD",
        "attack": "A dirty local audit store looks like channel volume",
        "brake": "Mentor demo uses an empty AEROBIM_STORAGE_DIR; SIG-01 is not this list",
    },
    {
        "id": "RT-UI-FONTS",
        "verdict": "ACCEPT",
        "attack": "Jury or mentor laptop offline fails because fonts load from a CDN",
        "brake": "No fonts.googleapis.com import; system UI/mono stack",
    },
    {
        "id": "RT-UI-OPENAPI-DEMO",
        "verdict": "KILL",
        "attack": "Published OpenAPI lists seed-fixture as a product operation",
        "brake": "include_in_schema False; router mounted only when is_dev_environment",
    },
    {
        "id": "RT-UI-SEED-VOLUME",
        "verdict": "HOLD",
        "attack": "Seed JSON issue_count as SIG-01 channel volume",
        "brake": "Count is the git-fixture finding total; SIG-01 stays the channel phrase",
    },
    {
        "id": "RT-UI-ANON-BIND",
        "verdict": "HOLD",
        "attack": "Anonymous dev plus a non-loopback bind becomes a LAN seed oracle",
        "brake": "Default host is 127.0.0.1; ALLOW_ANONYMOUS_DEV is opt-in",
    },
    {
        "id": "RT-UI-DEMO-SEED",
        "verdict": "ACCEPT",
        "attack": "Empty report list means the shell cannot be shown",
        "brake": "Dev-only git seed copies samples under storage_dir then validates",
    },
    {
        "id": "RT-UI-VIEWER-ID",
        "verdict": "ACCEPT",
        "attack": "Reload IFC bytes on every report object identity change",
        "brake": "Viewer fetch keys on report_id after the 01.09 loop",
    },
    {
        "id": "RT-UI-EXPERT-PANE",
        "verdict": "ACCEPT",
        "attack": "Leave the report index as the left pane of the expert seat",
        "brake": "TZ three-pane is findings | 2D/3D | remark; report index is SCR-PROJECTS",
    },
    {
        "id": "RT-UI-INTAKE-WIRE",
        "verdict": "ACCEPT",
        "attack": "User dashboard hides RT-001/002/003 behind a green shell",
        "brake": "GET /v1/system/capabilities intake snapshot; UI does not flip gates",
    },
    {
        "id": "RT-UI-INTAKE-GREEN",
        "verdict": "KILL",
        "attack": "Treat true_gates or this screen as RT CLOSED / Checkpoint GO",
        "brake": "NO_GO; PrecisionClaim.publishable remains the gate",
    },
)


def ui_expert_workplace_triage_snapshot() -> dict[str, object]:
    return {
        "artifact_type": "ui_expert_workplace_red_team_triage",
        "claim_level": CLAIM_LEVEL,
        "checkpoint": CHECKPOINT,
        "closes_rt001": False,
        "closes_rt002": False,
        "closes_rt003": False,
        "claim_boundary": CLAIM_BOUNDARY,
        "detected_count": 0,
        "is_accuracy": False,
        "is_full_cycle_workplace": False,
        "writes_summary_passed": False,
        "native_rvt_in_ui": False,
        "oidc_live": False,
        "xlsx_export": False,
        "cde_connector": False,
        "stack_shipped": False,
        "demo_seed_is_customer": False,
        "demo_seed_writes_passed": False,
        "jury_track_is_cli": True,
        "screens": [dict(row) for row in SCREEN_ROWS],
        "rows": [dict(row) for row in TRIAGE_ROWS],
        "kill_count": sum(1 for row in TRIAGE_ROWS if row["verdict"] == "KILL"),
        "hold_count": sum(1 for row in TRIAGE_ROWS if row["verdict"] == "HOLD"),
        "accept_count": sum(1 for row in TRIAGE_ROWS if row["verdict"] == "ACCEPT"),
    }


__all__ = [
    "CLAIM_BOUNDARY",
    "CHECKPOINT",
    "SCREEN_ROWS",
    "TRIAGE_ROWS",
    "ui_expert_workplace_triage_snapshot",
]
