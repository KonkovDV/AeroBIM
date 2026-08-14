# Official SPb GAU «ЦГЭ» IDS 1.0

**Source page:** https://www.spbexp.ru/bim/docs/  
**Retrieved:** 2026-08-14  
**Claim:** public machine-readable examination requirements (IDS 1.0). Second GAU jurisdiction pack after MOEXP. Organ methodology, **not** GrK art. 49. Not a Samolet customer-approved acceptance profile. Does not close Checkpoint GO / RT-002.

AeroBIM does not claim authorship. Files are redistributed as published by СПб ГАУ «Центр государственной экспертизы».

## IDS archives (SHA-256 of downloaded `.zip`)

| Domain | Published | URL | SHA-256 | Bytes |
| --- | --- | --- | --- | ---: |
| ЦИМ ОКС ред. 3.1.0 | 09.12.2024 | https://www.spbexp.ru/upload/iblock/2db/n3go3nmktwlmysgro5yzkw6zv6wdirrf/Trebovaniya-k-TSIM-OKS-_V.3.1.0.zip | `8ea565d4697e549caa346a56a854d54e89230d4cf2754225f6c492fa4364dea7` | 116839 |
| ЦИМ РИИ ред. 1.1.0 | 10.12.2024 | https://www.spbexp.ru/upload/iblock/f0c/mxezto7crx282ywsavv7i7n8ctxugw0k/Trebovaniya-k-TSIM-RII_V.1.1.0.zip | `a9a7956c570d88df1dbc22f1f791daeee455195932acf01e211caa3b0a6aa77b` | 16408 |

Extracted IDS XML: [`pack/`](pack/) (17 ОКС + 5 РИИ).

## Not in this pack

- PDF textual requirements (archive on the same page).
- Topographic-sign IFC library zip.
- SPb typical-remark HTML catalogs (already cited for Exp B; not IDS).

## Regenerate coverage

```text
cd backend
python -m aerobim.tools.export_public_ids_pack_coverage --pack spbexp
```
