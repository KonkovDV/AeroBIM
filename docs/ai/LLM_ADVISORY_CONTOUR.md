# LLM advisory contour

**claim_level:** architecture note · `fixture_only` / `synthetic_only`  
**Checkpoint:** NO_GO  

## Contour (ADR-001 hybrid)

```text
ingestion → deterministic Shared-gate → advisory overlay → evidence/HITL → honesty claims
```

| Layer | Role | Mutates `summary.passed`? |
|---|---|---|
| Deterministic engine (IDS, calc cross-check, schema pre-gates, …) | Verdict owner | Yes (Shared-gate) |
| LLM / VLM advisory | Remark draft, severity *suggestion*, uncertainty | **No** |
| HITL review events | Expert confirm / edit | Human-owned |
| Evidence bundle | Provenance + hashes | No |

Providers (DI): Yandex AI Studio / OpenAI-compat / optional Moonshot Kimi profile +
`MockLlmProvider`. Live drawing VLM adapter: `vlm_advisory_client.py`
(`AEROBIM_VLM_*`; deprecated alias `AEROBIM_KIMI_*`). Historical Kimi studies remain
under `docs/architecture/KIMI_*` (evidence only). Live calls remain **opt-in**.
Comparative mock bench: `python -m aerobim.tools.benchmark_llm_advisory`.

## Invariants

- Advisory OFF == ON for `summary.passed` and issue signature (`tests/test_advisory_vlm_off_equals_on.py`).
- `affects_summary_passed=false` on comparative artifacts.
- No triple live-model path on the production analyze route.
- Customer data egress blocked unless explicit policy allows.

## Architecture continuation (Sprint 2 — no GraphRAG)

Sprint 2 only documents this contour and closes baseline/demo honesty gaps. **No GraphRAG**, multi-agent orchestration sprawl, or mandatory cloud bake-off on CI. Next sprint may deepen evidence-bounded remark grounding and customer dual adjudication (RT-001) without changing the Shared-gate ownership.
