# Official Moscow AGR XML (ДГП / «СтроимПросто»)

**Source page:** https://stroimprosto.mos.ru/knowledge/article/cim-agr/  
**Retrieved:** 2026-08-14  
**Claim:** public city example TEP XML + official Vedomost XSD. Class-1 exchange checks. Not the frozen `moscow_agr` DI port. Not a Samolet pack. Does not close RT-002.

## Files

| File | Role | SHA-256 | Bytes |
| --- | --- | --- | ---: |
| `AGR_TEO.xml` | Example TEP (`ArchitecturalUrbanPlanningSolution`) | `b769c1cfaa0118d84081f9b0643d44a90d4490ac7ee55a8806f720e9aeb0e575` | 1449 |
| `Vedomost_AGR.xml` | Example CIM inventory | `a914f483e1c9e4216046f4b202692e3d0be73350bb2f250ddd3e31da96553146` | 1551 |
| `Vedomost_AGR_VED_NEW.xsd` | Official Vedomost schema | `23d1d5cb7218d4f8f216483f629e2a373f477fbacf546e26cfa7f360b3612e7b` | 2117 |
| `IFC_RusSets_AGR_PROPERTY.txt` | Revit mapping example (not executed) | `3da9777327cfd67498370019a44fd827edb2d62399bc0a42646f1a13d56b35ce` | 41563 |

`Vedomost.zip` (xsd + xml): https://stroimprosto.mos.ru/storage/app/uploads/public/6a0/b00/cfd/6a0b00cfda44e070163890.zip  
SHA-256 `aa7f46e26982716c99dad8503397913585293b2bceb856ca91a2d6f608603d00` (1882 bytes).

`AGR_TEO.xml` URL: https://stroimprosto.mos.ru/storage/app/uploads/public/69c/d2f/65d/69cd2f65d46fb061145965.xml

Mapping URL: https://stroimprosto.mos.ru/storage/app/uploads/public/6a6/c82/cde/6a6c82cde4c68642350086.txt

## Honesty

- `AGR_TEO.xml` and `Vedomost_AGR.xsd` are **different documents**. Do not validate TEP against Vedomost XSD.
- No published XSD for `ArchitecturalUrbanPlanningSolution` was listed on the article (14.08.2026). Root-localname check is the class-1 proxy.
- Example IFC models on the article are **not** in git.
