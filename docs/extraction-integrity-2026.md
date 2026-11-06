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
  (PDFium text layer, pdfminer.six only when PDFium cannot open the file;
  optional RapidOCR on pypdfium2 renders when the `raster` extra is present)
- Advisory ON/OFF must not flip `summary.passed` (hybrid / LLM advisory tests)

## PARTIAL (engineering deepen, 2026-08-03)

| Signal | Status |
|---|---|
| Text-layer hidden / off-page / zero-size | VERIFIED on the synthetic fixtures (PDFium font size, pdfminer fallback) |
| Optional OCR char-count vs extracted ratio | ENG_PARTIAL — WARNING when RapidOCR present |
| **Text-layer vs OCR digit-run collision** (≥3 digits) | **ENG_PARTIAL wired** — same-length spoof (visual «3000» / text «3300») → `FAILED` (pass-blocking); requires `raster`/OCR; not full literature coverage (arXiv:2606.15020) |
| Full visual render-vs-extract product | **NOT VERIFIED** — forbidden claim |

## Forbidden claims

«Render-vs-extract проверка PDF реализована как продукт» — запрещено.  
«OCR vs text-layer wired» ≠ product-grade visual integrity / accuracy claim / 25-gap literature closure.  
Digit-run collision with RapidOCR present ≠ OCR quality guarantee.  
Equality of PDFium and pdfminer digit runs is not claimed.

## How the text layer is read

A methods note. Not a fifth paper contribution and not a measurement on a customer corpus.

Two consumers share the layer. Neither writes `summary.passed`.

1. Drawing annotations. Regular expressions over assembled lines. The parent process does not parse the PDF. The walk runs in a child process (`pdfminer_extract_worker`) with a wall-clock timeout, a size cap and a page cap. PDFium reads the characters. pdfminer.six runs in that same child only when PDFium cannot open the file.
2. Integrity signals (`PdfMinerExtractionIntegrityProducer`; the class name is unchanged). Same order: PDFium, then pdfminer. Hidden text, off-page text, digit runs and the dominant script do not write `summary.passed`.

Characters arrive in content-stream order. The open line has vertical span $[b, t]$ in points, origin at the bottom-left. A character with box $[b_i, t_i]$ stays on that line if and only if

$$
b_i \le t + \sigma \quad\land\quad t_i \ge b - \sigma, \qquad \sigma = 1.
$$

Otherwise the line closes. A newline closes it immediately. The stored zone uses the top-left frame $y = H - t_{\mathrm{line}}$. The one-point slack exists because a hyphen's box lies inside the letter band while its bottom does not. Comparing bottoms alone splits `WALL-01`. The open line grows by at most that one point, so a tall glyph that merely overlaps the band does not pull the next line into it. This is stream-order assembly, not a proof that the line matches the typeset line. The band is measured on the viewed sheet. `/Rotate` of 90, 180 or 270 is applied to each character box first, with the same matrix pdfminer uses, because a PDFium box stays in the stored user space while the page size is already upright. The title-block corner and the off-page rectangle are that viewed sheet.

A hidden character is a non-empty, non-whitespace character whose font size $s \le 0.05$ pt. The size is `FPDFText_GetFontSize`. Tight glyph-box height is not a font size: a period in a normal font is short and is not hidden text. Off-page text is a tight box that lies entirely outside the page rectangle $[0, W] \times [0, H]$. Whitespace is not counted as hidden.

A digit run is a unique match of `\d{3,}`, sorted. Uniqueness stops a false `FAILED` when the same number is emitted twice. Equality with a pdfminer walk is not claimed. A collision with OCR is a disagreement between two channels, not an accuracy figure.

Let $n_C$ and $n_L$ be the Cyrillic and Latin letter counts. The layer is Cyrillic when $n_C \ge 40$ and $n_C > 2 n_L$, and Latin in the symmetric case. Otherwise the script is not measured. A Cyrillic layer is not sent to the bundled OCR model: that model does not read Cyrillic, so its digits are not a measurement. Skipping it does not assert that the text layer is correct.

A title-block caption is the field name in the top of the cell. The value is the single text line beneath it, overlapping on x, within 18 pt. Two candidate cells, or two captions over one cell, produce no pair. The pair is stored as a stamp reading (`source=stamp-caption-above`). It is not a length and it does not satisfy or fail a drawing rule. `writes_summary_passed` stays false. The vocabulary is the printed field names (sheet, stage, change, author, checker, cipher, name), not a customer stamp. On a page with a known size the pair is kept only when the line centre sits in the bottom-right title block, 190 mm by 70 mm. A GOST or SP citation under «Шифр» is not a package cipher. A paired size such as ``500×300`` is not one thickness, width, height or length. A different number on the same line is still that measure. The same measure printed as two numbers on two sheets is one drawing warning, and neither number is stored as the required value. Cipher and stage are package-stable: two different values across sheets are one drawing warning (`AEROBIM-STAMP-FIELD-DISAGREE`), not a cross-document contradiction. Neither reading is stored as the required value. Lookalike letters (`С` and `C`, Latin `I` excluded) are one token, the same fold as a steel grade. Sheet numbers may differ. The same sheet number on two sheets is one drawing warning. The sheet name is not package-stable. The single tallest short letter-line outside the title block is the body title (`source=sheet-body-title`). When it and the stamp name differ, that is one drawing warning (`AEROBIM-STAMP-BODY-TITLE`) and neither reading is the required name. Two equally tall different lines produce no body title. When sheet numbers were read and neither a cipher nor a change number appears, that is one drawing warning (`AEROBIM-STAMP-REVISION-UNMARKED`): revisions of the pack cannot be told apart. A short execution token is one measure. Two tokens on two sheets are the same drawing warning as two numbers, and neither is the required value. A piece count is one count, and `pcs` is stored as `шт`. A citation of a detail with no sheet title that names it is one drawing warning (`AEROBIM-DETAIL-CALLOUT-MISSING`). The citation is not proof the detail is absent from a signed set. The warning does not by itself fail the pack, and the interior vocabulary that names this class stays unsigned.

No separate Rust parser was added. PDFium is already the crop library in the core (pypdfium2, Apache-2.0 OR BSD-3-Clause, plus the PDFium notices). The character walk reads `FPDFText_GetUnicode` and reuses one character box for the page. A second parser would not replace that library. pdfminer.six stays in the core as the fallback. This remains LIC-001 option B. It is not a withdrawal of pdfminer and it is not a render-versus-extract product.
