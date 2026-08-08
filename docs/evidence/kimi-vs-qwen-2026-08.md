<!-- claims-lint: allow-file reason="Claims-boundary doc citing forbidden phrases as non-claims per pilot-claim-boundary / Claims Lock (WP-A5)" -->
---
title: "Sprint 3 — Kimi vs Qwen LLM extraction comparison"
date: 2026-08-07
status: canonical
claim_boundary: >-
  fixture_only · live_provider=false · advisory only · cannot change summary.passed.
  No product accuracy >90%. Checkpoint NO_GO.
---

# Kimi vs Qwen — LLM extraction (Sprint 3, August 2026)

**Canonical Sprint 3 comparison document.** Machine summary: [`kimi-vs-qwen-2026-08.json`](kimi-vs-qwen-2026-08.json).  
Detailed per-fixture run: [`llm-extraction-kimi-vs-qwen-2026-08.json`](llm-extraction-kimi-vs-qwen-2026-08.json) (sibling artifact).

---

## Run configuration

| Field | Value |
|---|---|
| **claim_level** | `fixture_only` |
| **live_provider** | `false` — no API keys / provider budget = **$0** |
| **Corpus** | [`samples/benchmarks/russian-aec-ground-truth.json`](../../samples/benchmarks/russian-aec-ground-truth.json) |
| **Fixtures** | 10 |
| **Requirements (GT rows)** | 50 |
| **GT type** | RU technical-spec → IFC property expectations (**requirements extraction GT**) |
| **≠ expertise conclusions** | Does **not** measure expertise-remark correctness; RT-001 still **NO_GO** |

**Tool:** `backend/src/aerobim/tools/evaluate_llm_extraction.py`

---

## Live provider status

**Models were NOT executed live.** Kimi and Qwen providers returned `status: skipped` with `live_provider: false`.

| Planned compare target | Intended route when configured | Sprint 3 status |
|---|---|---|
| **Moonshot Kimi** | OpenAI-compatible endpoint (provider-config dependent) | **NOT RUN** |
| **Qwen** | vLLM or Yandex Studio when configured | **NOT RUN** |

**Do not invent version strings as measured.** Model IDs and endpoint versions are provider-config dependent and were not exercised this run.

When live keys exist, re-run:

```bash
python -m aerobim.tools.evaluate_llm_extraction \
  --corpus samples/benchmarks/russian-aec-ground-truth.json \
  --out docs/evidence/llm-extraction-kimi-vs-qwen-2026-08.json
```

---

## Summary metrics (macro over 10 fixtures)

| Provider | macro_f1 | precision | recall | hallucination_count | Status |
|---:|---:|---:|---:|---:|---|
| **regex** | **0.86** | **0.86** | **0.86** | **0.0** | scored |
| **kimi** | 0.0 | 0.0 | 0.0 | 0.0 | **skipped** |
| **qwen** | 0.0 | 0.0 | 0.0 | 0.0 | **skipped** |

Kimi/Qwen F1 = 0 because providers did not emit candidates (`fn` = full GT count per fixture). **Metrics for LLM paths are not established.**

---

## Cost and latency

| Item | This run |
|---|---|
| **LLM API cost** | **$0** (no live calls) |
| **License budget** | **$0** (no ODA/APS added) |
| **Latency observed** | Regex only (~0.2–0.4 ms per fixture); Kimi/Qwen skip ~0.002 ms |

---

## Advisory boundary

LLM extraction output is **advisory only**:

- Does **not** change deterministic engine findings
- Does **not** change `summary.passed` (ADR-001 Shared-gate)
- Does **not** substitute for dual-adjudicated customer GT
- Regex baseline on fixtures is **not** product accuracy

---

## Conclusion

**LLM worth-it vs regex is NOT established** without live provider keys and measured Kimi/Qwen runs on this fixture corpus.

| Question | Answer (Sprint 3) |
|---|---|
| Does regex beat 0 on fixtures? | Yes — macro_f1 = 0.86, hallucination = 0 |
| Does Kimi beat regex? | **Unknown** — NOT RUN |
| Does Qwen beat regex? | **Unknown** — NOT RUN |
| Can we claim product accuracy? | **No** — fixture requirements GT ≠ customer expertise GT |
| Checkpoint | **NO_GO** |

---

## Related artifacts

| File | Role |
|---|---|
| [`kimi-vs-qwen-2026-08.json`](kimi-vs-qwen-2026-08.json) | Canonical machine summary (this sprint) |
| [`llm-extraction-kimi-vs-qwen-2026-08.json`](llm-extraction-kimi-vs-qwen-2026-08.json) | Full per-fixture evaluator output |
| [`llm-extraction-kimi-vs-qwen-2026-08.md`](llm-extraction-kimi-vs-qwen-2026-08.md) | Legacy short table (superseded by this doc for Sprint 3) |
| [`expertise-corpus-scan-2026-08.md`](../datasets/expertise-corpus-scan-2026-08.md) | Why fixture GT ≠ RT-001 |
