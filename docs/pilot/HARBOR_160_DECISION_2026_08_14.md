<!-- claims-lint: allow-file reason="Harbor 160 default SKIPPED memo; not a false-pass percentage" -->
---
title: "AEC-Bench Harbor 160 — решение по умолчанию (подтвердить 17.08)"
date: "2026-08-14"
claim_boundary: "Default SKIPPED. Harbor NOT_RUN. Not product accuracy. Not RT-001. Do not invent 514 false-pass."
---

# Harbor 160 (пункт 17.1)

**Календарь:** не начинать прогон до 17.08.  
**Решение по умолчанию на 14.08:** оставить **SKIPPED**.

| Факт | Источник |
| --- | --- |
| 196 `gt.json` | [`../evidence/aec-bench-false-pass-2026-08.md`](../evidence/aec-bench-false-pass-2026-08.md) |
| Harbor agent | **NOT_RUN** |
| `null_always_clean` | 134 FP / 50 TN / 184 labeled (0.7283) — gold-only, задача ≠ проект |
| Ключ Studio | уже гонял **AECV-Bench**, не Harbor |

17.08 оператор либо (а) подтверждает SKIPPED одной строкой в этом файле, либо (б) запускает Harbor и пишет evidence.  
Запрещено: подставлять 0.7283 как false-pass AeroBIM; писать «514 false-pass» (IFC-Bench countable = **27/1026**).
