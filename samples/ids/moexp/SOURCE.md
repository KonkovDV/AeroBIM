# Official MOEXP IDS pack (GAU MO «Мособлгосэкспертиза»)

**Source page:** https://www.moexp.ru/services/tekhnologii-informatsionnogo-modelirovaniya/  
**Retrieved:** 2026-08-13  
**Claim:** public machine-readable examination requirements (IDS 1.0/1.1). Organ methodology, **not** GrK art. 49. Not a Samolet customer-approved acceptance profile. Does not close Checkpoint GO.

AeroBIM does not claim authorship. Files are redistributed as published by the examination body.

## IDS archives (SHA-256 of downloaded `.7z`)

| Domain | Published | URL | SHA-256 | Bytes |
| --- | --- | --- | --- | ---: |
| ЦИМ АД и УДС | 23.03.2026 | https://www.moexp.ru/upload/iblock/9ba/ib1luwq73825cxhqoahr60ytf64jpl4b/IDS-k-TSIM-AD-i-UDS.7z | `0a7e72a81315dab8c79a83f9f7b89bde4a11da76d63578c88c60c3b92e6a62df` | 8930 |
| ЦИМ НИС | 24.03.2026 | https://www.moexp.ru/upload/iblock/feb/56o46b6x0k4mv3qrniyb83v7n7qwaf0j/IDS-k-TSIM-NIS.7z | `332a847be2f36f42ad1e99892955fa79bc5844abdeb7e1c1ad3cc893ee3e6338` | 11012 |
| ЦИМ пр./непр. ОКС | 23.03.2026 | https://www.moexp.ru/upload/iblock/a18/jqt68dtj9dpuizwwcs5kta7jmj4zbm88/IDS-po-trebovaniyam-MOGE-k-TSIM-pr-i-nepr-OKS.7z | `460175f3ac04440b78b8c235ec40754fd5ff4d6fa019c98c8775e5e4fa50d4c7` | 21896 |

Extracted IDS XML: [`pack/`](pack/).

## IFC4 mapping archives

| Domain | Published | URL | SHA-256 | Bytes |
| --- | --- | --- | --- | ---: |
| АД и УДС | 23.03.2026 | https://www.moexp.ru/upload/iblock/c53/foi73bsghbsw8m92qo252m3nm12l68nr/Fayl_mapping-IFC4-k-TSIM-AD-i-UDS.7z | `0497b63d2a8a45ac7e9d8c3fdbd7e5a7887b8095bd0fc3f87d5c692526dd97d0` | 8516 |
| НИС | 23.03.2026 | https://www.moexp.ru/upload/iblock/62e/6xww35x7a25l1xzmw30e5seob93gzb6n/Fayl_mapping-IFC4-k-TSIM-NIS.7z | `24f8bb3d388e31f0de0aa75f2307dbfb20a278897f7a19f2d2c0ee03b6f7d4b2` | 10192 |
| ОКС | 23.03.2026 | https://www.moexp.ru/upload/iblock/eb4/p98hs4mylhfe8p95ri7bapj63yf6cscx/Fayl_mapping-IFC4-trebovaniy-MOGE-k-TSIM-proizvodstvennykh-i-neproizvodstvennykh-OKS.7z | `f07bb25e468e3df83360d3ea9f355a287b8c7be09ca50dc27930652d91bfbf7a` | 61469 |

XML/ZIP extracts: [`pack/mappings/`](pack/mappings/). Topomatic Robur `.py` mapping scripts from the same archives are **not** imported or executed (architecture freeze; vendor scripts).

## Not in this pack

**ИЦММ 3.3** is published as PDF only on the same page (06.03.2026). No IDS file was listed as of 2026-08-13.

## Regenerate coverage

```text
cd backend
python -m aerobim.tools.export_moexp_ids_coverage
```
