<!-- claims-lint: allow-file reason="GNI anonymization script pin; execution SKIPPED" -->
---
title: "GNI anonymization script pin"
date: 2026-08-13
claim_level: gni_anonymization_pin
claim_boundary: >-
  MIT anonymization scripts from github.com/ZijianWang-ZW/GNI-BIM-Dataset are pinned by SHA-256. Execution is SKIPPED: scripts hardcode local paths and we only have already-anonymized Zenodo IFC. Not product accuracy.
---

# GNI anonymization script pin

- status: **PINNED**
- execution: **SKIPPED** — Scripts hardcode operator paths and depend on pandas/tqdm. Released GNI IFC are already anonymized. Do not rewrite.
- upstream: https://github.com/ZijianWang-ZW/GNI-BIM-Dataset
- content_sha256: `10087987dc16db8f47302183b30cb771feca366642adc2d96ddcd075a82ff403`

| path | present | sha256 |
| --- | --- | --- |
| `code/LICENSE` | True | `a6c2a55460bfc8b2c5610293ca92fe86f9ea2d111ec7dbb81a81ac6554bbb0a5` |
| `code/anonymize_bim_fundamentals.py` | True | `8222dee28e3233176a7a97b184eebc2963ca4c58d89469b9b877d154bfd6f7c5` |
| `code/anonymize_bim_projects.py` | True | `6278b95eaf084f27ac9358c5edcc33b4d14bf3637a48f3a79a668e8458da3c4c` |

```bash
git clone --depth 1 https://github.com/ZijianWang-ZW/GNI-BIM-Dataset .local/gni-bim-code
cd backend
python -m aerobim.tools.export_gni_anonymization_pin
```
