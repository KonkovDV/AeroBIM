# AeroBIM multimodal ablation study (paper table)

| Mode | Pack | Requirements | Issues | Cross-doc | Category breakdown |
|------|------|-------------:|-------:|----------:|--------------------|
| A0 | `project-package-ablation-a0` | 0 | 2 | 0 | ids-validation=2 |
| A1 | `project-package-ablation-a1` | 6 | 8 | 0 | ids-validation=2, ifc-validation=6 |
| A2 | `project-package-ablation-a2` | 11 | 17 | 3 | cross-document=3, ids-validation=2, ifc-validation=12 |
| A3 | `project-package-ablation-a3` | 6 | 8 | 0 | ids-validation=2, ifc-validation=6 |

Modes: **A0** IDS-only → **A1** + IFC properties → **A2** + cross-document → **A3** reduced multimodal.

Pack count: 4. Source JSON: [`ablation-study-report.json`](ablation-study-report.json). Regenerate via `python -m aerobim.tools.run_ablation_study`.
