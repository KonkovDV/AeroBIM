---
title: "Optional Adapters Smoke 2026"
status: active
version: "1.0.0"
last_updated: "2026-05-20"
tags: [aerobim, pilot, adapters]
---

# Optional Adapters Smoke

Pilot default install: `pip install -e ".[dev,raster]"`. Optional extras are **not** required for Moscow pilot gates.

## Capability matrix

| Extra | Capability | Pilot |
|---|---|---|
| `raster` | PDF/OCR drawing extraction (PyMuPDF + RapidOCR) | Required |
| `clash` | IfcClash detection | Optional |
| `docling` | Docling document parser | Optional |
| `enterprise` | Postgres/S3 adapters | Post-pilot |

## Clash extra smoke

```bash
cd backend
pip install -e ".[clash]"
python -m pytest tests/test_clash_detection.py -q
```

If IfcClash is unavailable in the environment, tests skip — document skip reason in weekly log.

## Docling extra smoke

```bash
pip install -e ".[docling]"
python -m pytest tests -k docling -q
```

## Operator messaging

README and [`pilot-claim-boundary-2026.md`](pilot-claim-boundary-2026.md) must list which extras were active during pilot runs. Do not claim clash or Docling paths without this smoke passing on the pilot VM.
