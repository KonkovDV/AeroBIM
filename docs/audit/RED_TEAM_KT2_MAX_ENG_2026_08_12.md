<!-- claims-lint: allow-file reason="Red Team max-eng KT#2; no product GO" -->
---
title: "Red Team — KT#2 max-eng densify 2026-08-12"
date: "2026-08-12"
claim_boundary: "Recheck after clash/overlay/BCF/FAQ densify. Checkpoint NO_GO."
---

# Red Team: KT#2 max-eng (2026-08-12 evening)

## Scope

WP from `KT2_MAX_ENG_PLAN_2026_08_12.md`: denser fixture clash, second overlay, BCF T1 in handoff, jury FAQ, demo rehearsal, N43 checklist (not activated), extended verify gate.

## Reproduction

```text
python -m aerobim.tools.measure_extent_clash_fixture --write-fixture
python -m aerobim.tools.render_drawing_overlay_evidence
python -m aerobim.tools.verify_bcf_structural_handoff --output ../docs/evidence/kt2-handoff-2026-08-11/bcf-t1/bcf-structural-handoff.json
python -m aerobim.tools.verify_kt2_handoff --write-status ../docs/evidence/kt2-handoff-2026-08-11/VERIFY.json
python -m unittest discover -s tests -p "test_tz_fixture_evidence_2026_08.py" -v
python -m unittest discover -s tests -p "test_verify_kt2_handoff.py" -v
python scripts/lint_claims.py --matrix-guard
```

## Results

| Check | Result | Status |
| --- | --- | --- |
| Clash n / micro | n=6 TP=6 FP=0 FN=0 fixture_only | VERIFIED |
| Near-miss walls | present; not counted as overlaps | VERIFIED (by construction + measure) |
| Overlay zones | wall_thickness + sheet_header PNGs | VERIFIED |
| BCF T1 | structural_ok=true; cde NOT_VERIFIED | VERIFIED |
| `verify_kt2_handoff` | ok=true, 15 checks | VERIFIED |
| matrix-guard | OK | VERIFIED |
| N43 | still deferred (correct on 12.08) | VERIFIED |
| Checkpoint | NO_GO | VERIFIED |

## Findings

### RT-KT2-MAX-01 — Early N43 flip avoided
- **Status:** VERIFIED / ACCEPTED  
- Checklist only; activate **17.08**.

### RT-KT2-MAX-02 — BCF must not be pitched as CDE-ready
- **Status:** VERIFIED mitigated  
- Evidence JSON forces `NOT_VERIFIED` + forbidden wording list.

### RT-KT2-MAX-03 — Fixture n=6 still not product accuracy
- **Status:** VERIFIED mitigated  
- Matrix + STATUS claim_boundary updated.

### P0 code defects
**None** in this densify path.

## Verdict
Intermediate pack is denser and jury-safer. **Show YES / customer GO NO.**
