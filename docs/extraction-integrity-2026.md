# Extraction integrity (2026)

**Capability:** `extraction_integrity` on `ReportCapabilities`.  
**Default:** `not_verified` (signals not yet produced by ingestion).  
**Gate:** `FAILED` ∈ pass-blocking (`capability_policy` / sign-off).

## VERIFIED

- Domain assessor: `backend/src/aerobim/domain/extraction_integrity.py`
- Invariant: «text not extracted» ≠ «text absent»
- Adversarial fixture catalog: `samples/benchmarks/extraction-integrity-adversarial.json`
- Tests: `backend/tests/test_extraction_integrity.py`
- **Producer wired (2026-07-31):** `PyMuPDFExtractionIntegrityProducer` +
  `probe_extraction_integrity` on analyze ingestion for PDF drawing sources;
  capability set via `build_report_capabilities(extraction_integrity=...)`
- Advisory ON/OFF must not flip `summary.passed` (hybrid / LLM advisory tests)

## NOT VERIFIED / gap

| Gap | Status |
|---|---|
| Full visual render-vs-extract (raster OCR vs text layer) | NOT VERIFIED — producer is text-layer signal only |
| Complete red-team PDF corpus as runtime detectors | PARTIAL |
| LLM receives only integrity-tagged text end-to-end | PARTIAL |

## Forbidden claims

«Render-vs-extract проверка PDF реализована как продукт» — запрещено.
«Producer wired» ≠ product-grade visual integrity.
