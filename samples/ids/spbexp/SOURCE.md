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

Files are included as published. Publisher rights remain with СПб ГАУ «Центр государственной экспертизы». The repository MIT license applies only to AeroBIM code.

## Hashing (two policies, on purpose)

| Object | Function | Why |
| --- | --- | --- |
| `.ids` XML | SHA-256 of **raw bytes** (`_sha256_file`) | Git treats `*.ids` as binary (`.gitattributes`). The publisher file is the artifact; CR bytes would be a different document. |
| Profile / dataset JSON | SHA-256 after CRLF→LF (`_sha256_text_ci`) | `*.json text eol=lf`. Evidence `manifest_sha256` must match `samples/DATASET_MANIFEST.json` on Linux CI, not a Windows worktree. |

Zip hashes in the table above are SHA-256 of the downloaded archive bytes, same rule as `.ids`.

## Publisher folder name (do not “fix”)

The OKS zip on the publisher page is `Trebovaniya-k-TSIM-OKS-_V.3.1.0.zip` (ОКС). The folder **inside** that zip is `Требования к ЦИМ ОК _V.3.1.0` — «ОК», a space before `_V`, as shipped by ЦГЭ. AeroBIM keeps that path byte-for-byte so SHA-256 stays stable. Cyrillic, spaces and parentheses in `.ids` paths are also publisher names; Linux/macOS CI (`validate_spb_cge_profile`) is what proves they open.

## Two evidence files, two counters

| File | Date | What it counts |
| --- | --- | --- |
| [`docs/evidence/norm-pack-spbexp-coverage-2026-08.json`](../../../docs/evidence/norm-pack-spbexp-coverage-2026-08.json) | 2026-08-14 | IfcTester **specification** pass/fail on the wall fixture: 195 pass / 161 fail of 356 specs. |
| [`docs/evidence/spb-cge-profile-validation-2026-08.json`](../../../docs/evidence/spb-cge-profile-validation-2026-08.json) | 2026-08-24 | Profile integrity + two full-profile runs: **1543 issue rows** per run. One specification can emit many entity-level issues. |

Do not add 195+161 and expect 1543. Same 22 files, different geometry. Neither number is CIM compliance or an expertise conclusion. Host checkout paths were stripped from the 14.08 JSON; the specification counts were not re-run.

## Not in this pack

- PDF textual requirements (archive on the same page).
- Topographic-sign IFC library zip.
- SPb typical-remark HTML catalogs (already cited for Exp B; not IDS).

## Regenerate coverage

```text
cd backend
python -m aerobim.tools.export_public_ids_pack_coverage --pack spbexp
```
