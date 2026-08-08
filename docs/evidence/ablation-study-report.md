# AeroBIM multimodal ablation study (paper table)

| Mode | Pack | Requirements | Issues | Cross-doc | Category breakdown |
|------|------|-------------:|-------:|----------:|--------------------|
| A0 | `project-package-ablation-a0` | 0 | 3 | 0 | ids-validation=2, spatial=1 |
| A1 | `project-package-ablation-a1` | 6 | 10 | 0 | ids-validation=2, ifc-validation=7, spatial=1 |
| A2 | `project-package-ablation-a2` | 11 | 19 | 3 | cross-document=3, ids-validation=2, ifc-validation=13, spatial=1 |
| A3 | `project-package-ablation-a3` | 6 | 12 | 1 | cross-document=1, drawing-validation=1, ids-validation=2, ifc-validation=7, spatial=1 |

Modes: **A0** IDS-only → **A1** + IFC properties → **A2** + cross-document → **A3** reduced multimodal.

Pack count: 4. Regenerate via `python -m aerobim.tools.run_ablation_study`.
