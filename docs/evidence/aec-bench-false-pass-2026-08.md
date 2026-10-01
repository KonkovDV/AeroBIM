<!-- claims-lint: allow-file reason="AEC-Bench gold inventory; Harbor false-pass SKIPPED" -->
---
title: "AEC-Bench gold inventory and null baseline"
date: 2026-08-15
claim_level: open_bench_only
claim_boundary: >-
  AEC-Bench open_bench_only (arXiv:2603.29199). Prefetch/inventory of public agentic tasks plus gold-label inventory. Harbor agent trial scores are NOT AeroBIM product accuracy and do not close RT-001. null_always_clean is a gold-only baseline, not a drawing-reading agent.
---

# AEC-Bench gold inventory

- gt.json files: **196**
- labels: `{"clean": 50, "has_issue": 134, "qa": 12}`
- variants: `{"broken": 114, "clean": 34, "navigation": 12, "none": 36}`
- Harbor agent: **NOT_RUN**
- sheets on disk: **43** / 1340 manifest PDFs
- null_always_clean false_positive: **134**
- null_always_clean true_negative: **50**
- null_always_clean false_pass_rate_on_labeled: **0.7283**
- labeled_compliance_tasks: **184**

Harbor drawing-reading false-pass remains **NOT_MEASURED**. The Yandex Studio key already ran **AECV-Bench** counting (macro_extended=0.4325, 2026-08-04); Harbor is a different Codex/Claude agent and does not take that key. `null_always_clean` is a gold-only floor: always say compliant, never open a sheet. Not AeroBIM product accuracy. Not RT-001. Observation unit = task, not project cluster.

```bash
cd backend
python -m aerobim.tools.run_aec_bench_smoke --also-docs-evidence
```
