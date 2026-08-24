# Official Moscow AGR IDS (ДГП / «СтроимПросто»)

**Source page:** https://stroimprosto.mos.ru/knowledge/article/cim-agr/  
**Retrieved:** 2026-08-14  
**Claim:** public machine-readable AGR CIM checks (IDS). City methodology files, **not** the territorial NPA itself (that is 17-ПП + ДГП-Р-1/26). Not a Samolet customer-approved acceptance profile. Does not close Checkpoint GO / RT-002. Does not substitute GrK art. 49 expertise.

AeroBIM does not claim authorship. Files are redistributed as published by the City of Moscow knowledge base.

## IDS archive

| Published as | URL | SHA-256 | Bytes |
| --- | --- | --- | ---: |
| `IDS.zip` (ЦИМ АР, ЦИМ ПС, БиО, МССК) | https://stroimprosto.mos.ru/storage/app/uploads/public/6a7/c18/b72/6a7c18b72d32c323379811.zip | `d04f5dd82a80c80bf7be7ca0660399107c75d26d0ea7b8f1f3af612410ada1ec` | 12453 |

Extracted IDS: [`pack/`](pack/).

## Not in this pack

- Example IFC models on the same page — **not vendored** (size / city ToS). URLs + sizes: [`../../agr/dgp/CITY_IFC_MANIFEST.json`](../../agr/dgp/CITY_IFC_MANIFEST.json). Local pin: [`../../../docs/dataset/MOSCOW_AGR_CITY_EXAMPLES_LOCAL_PIN_2026_08_24.md`](../../../docs/dataset/MOSCOW_AGR_CITY_EXAMPLES_LOCAL_PIN_2026_08_24.md). Fetch: `python -m aerobim.tools.fetch_moscow_agr_city_examples`.
- TRM container zip (~5 MB) — `.local/` only.
- Login-walled XML АГР / САГР zip builders (`/lk/xmlagr`, `/lk/sagr-zip`).

## Related official XML (not IDS)

See [`samples/agr/dgp/SOURCE.md`](../../agr/dgp/SOURCE.md) for `Vedomost.zip` XSD and `AGR_TEO.xml`.

## Regenerate coverage

```text
cd backend
python -m aerobim.tools.export_public_ids_pack_coverage --pack moscow-agr
```
