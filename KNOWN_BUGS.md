# KNOWN_BUGS — AeroBIM tracked stubs & honesty debt

> Status: living register. Every `@sota-stub` adapter MUST have an entry here.
> Checkpoint remains **NO_GO** until RT-001/002/003 with customer evidence.

## Active stubs

### STUB-IDS-ASSIST-001

| Field | Value |
|-------|-------|
| Stub ID | `STUB-IDS-ASSIST-001` |
| Tag | `@sota-stub` |
| Adapter | `backend/src/aerobim/application/services/ids_assist_boundary.py` (`StubIdsAssistDraftAdapter`) |
| Port | `IdsAssistDraftPort` |
| Severity | **LOW** |
| Effect | Advisory IDS assist only; never writes `summary.passed` |
| Blockers | Real provider-agnostic LLM client + DeterminismGate already required for any promotion |
| Target | Post-customer-corpus advisory wave; optional after I4 compiler path |
| Honesty | Does **not** flip `customer_approved` or intake gates |

## Closed / N/A

- Cad / OCR multimodal / MEP unconfigured adapters are real fail-closed or degrade paths (not `@sota-stub`).
