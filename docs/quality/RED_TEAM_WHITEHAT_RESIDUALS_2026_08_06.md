# Red Team / White Hat residual audit — 2026-08-06 (evening)

**HEAD base:** `83cdb80`  
**Checkpoint:** **NO_GO**  
**claim_boundary:** Engineering remediations only. Does not close RT-001/002/003 or establish customer accuracy.

## Method

Live-code white-hat pass after Sprint 2 packaging. Verified prior RT-HD-01…10 holds on storage/HTTP; hunted residuals that reopen egress under absolute paths / tooling control plane.

## Findings fixed this pass

| ID | Severity | Defect | Fix |
|---|---|---|---|
| RT-WH-01 | **HIGH** | `_advisory_object_kind` substring `/samples/` on absolute deploy paths (e.g. `D:/work/samples/AeroBIM/var/tenants/…`) → `public_fixture` → cloud advisory egress | Discrete path components + trusted corpus children; deny `tenants`/`uploads`/`customer` |
| RT-WH-02 | **HIGH** | `run_aecv_bench_eval` default OpenAI host + raw `urlopen` | Host allowlist + `safe_urlopen`; empty default base URL; OpenAI path fail-closed |
| RT-WH-04 | **MEDIUM** | `LlmDataPolicy.allow_synthetic_public` dataclass default `True` | Default **`False`** (SSOT with compose) |
| RT-WH-05 | **MEDIUM** | Kimi VLM client SSRF-only, no LLM host allowlist | Allowlist on real transport; boot gate for `AEROBIM_KIMI_API_BASE_URL` |
| RT-WH-03 | **MEDIUM** | PDF integrity producers unbounded page loops | Cap **200** pages (pymupdf + pdfminer) |

## Held / verified clean

Prior RT-HD path jail, 404 cross-tenant, ZIP containment, quota tokens, App↛Infra, report ACL, OFF==ON verdict, frontend no VITE bearer, Sprint 2 evidence without env secrets.

## Evidence

- Tests: `backend/tests/test_rt_hyperdeep_2026_08_06.py` (absolute-path + policy default cases)
- Kimi allowlist rejection test; OFF==ON uses loopback allowlisted URL

## Not claimed

Product accuracy, customer SLA, native DWG, delivered MEP, CDE-ready BCF, Checkpoint GO.
