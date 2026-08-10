# Red Team — VLM / mentor / vertical slice (2026-08-11)

**Scope:** advisory VLM, mentor demo, region smoke, mentor evidence pack.  
**Tests:** focused suite green after fixes.

## Findings closed this pass

| ID | Severity | Fix |
| --- | --- | --- |
| RT-P0-1 | High | Mentor crops now from PII-clipped plan tasks (`egress_crop`); sha matches live read |
| RT-P0-2 | High | Evidence uses real `vlm-report.json` (`status=roundtrip_ok`), not curated shape |
| RT-P0-3 | High | Folder id redacted in report + LIMITATIONS |
| RT-P0-4 | High | Verification checklist expects `roundtrip_ok` |
| RT-P1-1 | Medium | Yandex host + missing/wrong model refused (no silent kimi-k3 profile) |
| RT-P1-2 | Medium | Cache keys use `effective_region_prompt` for json_object rewrite |
| RT-P1-3 | Medium | `control_fields_ignored` / `dropped_count` plumbed into `RegionRead` + mentor report |
| RT-P2-1 | Low | Region smoke requires `--cache-namespace` with `--cache-dir` |
| RT-P2-2 | Low | Docstring Pdfium (not PyMuPDF); claim text without “Kimi” |

## Remaining accepted risks

- Whole-sheet smoke exists only behind `--allow-whole-sheet` (legacy).
- Product DI VLM still separate from `AEROBIM_LLM_*` (mentor may use LLM env; DI needs `AEROBIM_VLM_*`).
- Vertical-slice P4 remains offline schema check, not live VLM.

## Verification

```text
pytest mentor/caching/vlm/region/smoke suites — passed
live mentor demo — roundtrip_ok, 150 mm, egress bbox x0=0.1
```
