# AeroBIM Benchmark Report (2026-05-20)

## Environment

- Platform: `Windows-11-10.0.26200-SP0`
- Python: `3.13.7`
- pip freeze hash: `2c7d42fcfd1b146f`
- ifcopenshell: `unknown`

## Extraction quality (RU corpus)

- Macro F1: **0.860**
- Macro precision: 0.860
- Macro recall: 0.860
- Fixtures: 10

### Per-discipline F1

| Discipline | Fixtures | Macro F1 |
|---|---:|---:|
| architecture | 3 | 0.733 |
| fire-safety | 2 | 0.800 |
| mep | 1 | 0.800 |
| structure | 4 | 1.000 |

## Multimodal ablation (A0–A3)

| Mode | Issues | Requirements | Cross-doc |
|---|---:|---:|---:|
| A0 | 2 | 0 | 0 |
| A1 | 8 | 6 | 0 |
| A2 | 17 | 11 | 3 |
| A3 | 8 | 6 | 0 |

## Claim boundary

Deterministic multimodal QA kernel with provenance — not full-code compliance.

_Generated at 2026-05-20T21:14:15.151473+00:00_
