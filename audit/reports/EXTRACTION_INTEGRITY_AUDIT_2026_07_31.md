# Extraction integrity audit — 2026-07-31

| Check | Status | Evidence |
|---|---|---|
| Domain signal core | VERIFIED | `domain/extraction_integrity.py` |
| Capability field + FAILED blocks pass | VERIFIED | models + capability_policy |
| PDF text-layer signal producer on analyze path | VERIFIED (pdfminer; optional OCR enrich) | `OcrAwareExtractionIntegrityProducer` |
| OCR vs text-layer char-count disagreement | ENG_PARTIAL | domain WARNING when both counts present; RapidOCR optional |
| Full visual render≠extract product | NOT VERIFIED | Claims Lock forbids |
| Adversarial fixtures | PARTIAL | `extraction-integrity-adversarial.json` |

See `docs/extraction-integrity-2026.md`.
