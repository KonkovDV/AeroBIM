# Extraction integrity (2026)

**Capability:** `extraction_integrity` on `ReportCapabilities`.  
**Default:** `not_verified` when signals absent.  
**Gate:** `FAILED` ∈ pass-blocking (`capability_policy` / sign-off).

## VERIFIED

- Domain assessor: `backend/src/aerobim/domain/extraction_integrity.py`
- Invariant: «text not extracted» ≠ «text absent»
- Adversarial fixture catalog: `samples/benchmarks/extraction-integrity-adversarial.json`
- Tests: `backend/tests/test_extraction_integrity.py`,
  `backend/tests/test_ocr_aware_extraction_integrity.py`
- **Producer wired:** default `OcrAwareExtractionIntegrityProducer`
  (pdfminer text-layer + optional RapidOCR on pypdfium2 renders when `raster` extra present)
- Advisory ON/OFF must not flip `summary.passed` (hybrid / LLM advisory tests)

## PARTIAL (engineering deepen, 2026-08-01)

| Signal | Status |
|---|---|
| Text-layer hidden / off-page / zero-size | VERIFIED (pdfminer path) |
| Optional OCR char-count vs extracted ratio | ENG_PARTIAL — fills `ocr_char_count` when RapidOCR available; domain WARNING on disagreement |
| Full visual render-vs-extract product | **NOT VERIFIED** — forbidden claim |

## Forbidden claims

«Render-vs-extract проверка PDF реализована как продукт» — запрещено.  
«OCR vs text-layer wired» ≠ product-grade visual integrity / accuracy claim.
