---
title: "Documentation Language Policy 2026"
status: active
version: "1.0.0"
last_updated: "2026-05-21"
tags: [aerobim, documentation, i18n, style]
---

# Documentation language policy (May 2026)

Aligns with [Diataxis](https://diataxis.fr/) (one primary language per document) and open-source norms for international reviewers ([Open Source Guides — documentation](https://opensource.guide/best-practices/), 2026).

## Rules

| Rule | Detail |
|------|--------|
| **One language per file** | Do not mix Russian and English sentences in the same section. |
| **English default** | README, CONTRIBUTING, architecture, pilot ops, Samolet alignment, evidence, and audits are **English**. |
| **Russian parallel** | Files suffixed `-ru.md` or `README.ru.md` are **Russian only**. |
| **Industry terms** | IFC, IDS, BCF, GUID, CDE, SLA, sign-off, fixture, benchmark, smoke, overlay, endpoint, pack — allowed in both languages. |
| **Product voice** | Say **assistive automation** or **decision-support**; do not market as an “AI product”. No vendor model names or IDE branding in public docs. |
| **Sign-off path** | Say **deterministic sign-off** or **non-deterministic adapters deferred**; port `RasterDrawingAnalyzer`; install extra **`.[raster]`** (not `vision`). |
| **User-facing remarks** | Russian **or** English strings via `AEROBIM_REMARK_LOCALE` (`template_remark_generator.py`) are intentional product locale, not documentation runglish. |

## File map

| Language | Examples |
|----------|----------|
| English | `README.md`, `docs/06-architecture-reference.md`, `docs/samolet-techlab-*.md`, `docs/pilot-*.md`, `docs/PROJECT-AUDIT-2026-05-20.md` |
| Russian | `README.ru.md`, `docs/archive/10-academic-audit-and-recommendations-ru.md`, `docs/contributor-git-ru.md`, `docs/pilot-case-study-report-ru.md` |

## Editing checklist

1. Pick language from filename; translate or split if mixed.
2. Replace runglish hybrids (`operator-документация`, `capability framing`, `One-report smoke`) with one-language equivalents.
3. Remove references to coding agents, donor control-planes, or proprietary IDE products.
4. Link bilingual pairs in front matter when both exist.

## Related

- [`REPOSITORY-HYGIENE-2026.md`](REPOSITORY-HYGIENE-2026.md)
- [`contributor-git-2026.md`](contributor-git-2026.md) (English)
- [`contributor-git-ru.md`](contributor-git-ru.md) (Russian)
