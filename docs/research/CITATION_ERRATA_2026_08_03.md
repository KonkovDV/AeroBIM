# Research citation errata — 2026-08-03

**Scope:** ClickUp Task 07 / remote Red Team noted attribution errors and missing baselines.  
**Repo note:** there is no `research.md` at repo root; apply these fixes wherever the citation is mirrored (ClickUp doc, decks, partner briefs).

## ASK-BIM journal

| Field | Wrong | Correct (VERIFIED 2026-08-03) |
|---|---|---|
| Venue | Information Fusion | **Data & Knowledge Engineering** |
| Evidence | — | DIGITAL.CSIC / Elsevier: *Data and Knowledge Engineering* 164; DOI [10.1016/j.datak.2026.102581](https://doi.org/10.1016/j.datak.2026.102581); ISSN 0169-023X |

## НРС exclusion (2 years)

Remote audit: thesis «повторные отрицательные заключения → исключение из НРС до двух лет» — **NOT VERIFIED** in open sources during that pass.  
**Rule:** do not put on slides without a cited norm. Prefer ГИП / audit-trail value prop (ГрК 55.5-1 framing) without the НРС claim.

## LLM → IDS baselines (RT-023) — add to research surface

These were cited in the remote Task 07 audit and were missing from local research notes. Status: **PUBLIC CLAIM / peer literature** — not AeroBIM product metrics.

| Work | Venue / id | Relevance to AeroBIM |
|---|---|---|
| Перов, Филатова, Тимощак, Насонов (ИТМО) — регламент→IDS | ICDM Workshops 2025, DOI [10.1109/icdmw69685.2025.00203](https://doi.org/10.1109/icdmw69685.2025.00203) | Peer pipeline near `RequirementToIdsCompiler` (planned): 138 expert reqs; 100% XML / 94.1% XSD / 77.5% Solibri-executable; ablation without repair-loop drops validity |
| Ishigaki-IDS | arXiv:[2606.08545](https://arxiv.org/abs/2606.08545) (2026-06-07) | Open-weight verifier-aware IDS drafting; HITL workflow, not silent product compiler |
| Ishigaki-IDS-Bench | arXiv:[2605.22079](https://arxiv.org/abs/2605.22079) (2026-05-21) | 166 expert cases; LLMs struggle on IDS XML/IFC vocabulary constraints |
| P4IR | arXiv:[2606.22402](https://arxiv.org/abs/2606.22402) (2026-06-21, NUS) | Two-stage RL against ACC rule hallucination |
| Zentgraf et al. | AEI 104735 (2026-05-11) | Level-4 Smart Standards → SHACL (not IDS) |

**Claim rule for TZ / decks:** do **not** write «мы напишем LLM→IDS компилятор» as SOTA without citing this level. Allowed: advisory compiler + HITL + compare metrics to published baselines, or partnership framing (e.g. ИТМО).

See also: [`LLM_TO_IDS_BASELINE_2026_08_03.md`](LLM_TO_IDS_BASELINE_2026_08_03.md).
