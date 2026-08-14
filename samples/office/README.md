# Synthetic MS Office fixtures

Committed `.docx` / `.xlsx` for native Office ingest (TZ row 27).

- Not customer documents.
- Not Samolet TZ originals.
- Round-trip only: `OfficeDocumentIngestor` must recover the planted strings.

See `backend/tests/test_office_native_ingest.py`.
