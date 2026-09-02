<!-- claims-lint: allow-file reason="Link/DOI fact-check snapshot 2026-09-02; not product accuracy; fabricated DOI only as errata; NO_GO" -->
---
title: "Link & Citation Fact-Check — все ссылки, DOI, arXiv репозитория"
status: active
version: "1.1.0"
last_updated: "2026-09-02"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_boundary: >
  Snapshot 2026-09-02. Not product accuracy. Not partner hours.
  External checks via Crossref/DataCite/arXiv API. Checkpoint NO_GO.
---

# Фактчек ссылок и цитирований (02.09.2026)

Снимок гигиены цитат на эту дату. Не точность продукта и не закрытие RT.
Lit-матрица: [`ACADEMIC_LIT_REVIEW_2026_09.md`](ACADEMIC_LIT_REVIEW_2026_09.md) · extract: [`../RELATED_WORK_PREPRINT_2026_09.md`](../RELATED_WORK_PREPRINT_2026_09.md).

## 1. Метод

Три слоя: (1) внутренние markdown-ссылки — own-scan по всему дереву; (2) внешние DOI/arXiv — инвентаризация регексом, верификация через Crossref API, DataCite API, arXiv API (батч); (3) контекстная классификация каждого непрошедшего. Плюс штатный чекер проекта (`python -m aerobim.tools.check_markdown_links`).

## 2. Результаты

| Слой | Объём | Результат |
|---|---|---|
| Штатный чекер проекта (`check_markdown_links`) | его скан-набор | **OK** |
| Внутренние ссылки (own-scan) | 1061 | **0 битых в собственных доках** (5 битых — внутри `backend/.venv`, чужой код) |
| Внешние URL | 156 уникальных | грузоподъёмные верифицированы в гранд-проходах (CORENET X, CBIMS, Solibri, ACCORD/CHEK, рынок — веб-подтверждены 02.09) |
| DOI → Crossref | 20 | **17 OK** + 3 (см. DataCite) |
| DOI → DataCite (второй проход) | 3 | **3 OK** (FAIR4RS, arXiv-DOI, Zenodo GNI BIM Dataset — запись жива; счётчик цитирований DataCite на эту дату не переносить как Scholar/AeroBIM) |
| arXiv ID | 27 | **27/27 резолвятся** (включая AECV-Bench, BLUEPRINT, BIM-Edit, Ishigaki-IDS) |

На эту дату: все 20 проверяемых DOI резолвятся с корректными названиями и годами; все 27 arXiv живы; fabricated-twin `aei.2026.103676` даёт 404 как и должно — он легально существует только в errata-доках как audit trail (`lint_citation_twins`).

## 3. Урок методологии (для инструментов проекта)

28 «FAIL» первой проверки оказались **ложными срабатываниями собственного регекса**: `10.3049/47868` — это «координата 10.3049 / узел 47868» из расчётных схем в `.local/pack-out/` (незакоммиченные операторские данные), `10.2025/лк-цнэ-3419` — фрагмент пути «замечания от 19.09».

Кодировка в `scripts/lint_claims.py`: `lint_citation_twins` пропускает `.local/` / `.venv` / `node_modules`; `is_citation_doi_candidate` требует citation-контекст (`doi.org` / `doi:`) или известный префикс издателя и отбрасывает кириллицу в токене.

## 4. Новые верифицированные источники (Crossref 02.09.2026; в матрице)

Уже цитировались в репо; строки добавлены в lit-матрицу. Их eval не наш.

- `10.1016/j.autcon.2026.107043` — Dias, Miceli Junior & Pellanda, *Information requirement-driven BIM verification for construction cost estimation… IDS*, AuC 189 (2026) 107043. Analog IR/IDS для **сметы**, не pack ACC.
- `10.1109/icdmw69685.2025.00203` — Perov, Filatova, Timoschak & Nasonov, *From Regulations to IDS: A Tool-Augmented LLM Pipeline for Automated BIM Rule Checks*, ICDMW 2025, 1696–1702. Рядом с Fuchs. Не склеивать с *Buildings* 15 art. 2927.
- `10.1061/jcemd4.coeng-18122` — Wang, Hwang, Han & Gupta, *Generative AI-Assisted Compliance Checking for Construction Requirements*, JCEM 152(8) 2026.
- `10.3390/buildings16040719` — Zhang et al., *Human-in-the-Loop Semantic Rule Base Generation…*, Buildings 16(4) 719 (фев 2026). Их 95.8 % — **их** eval.
- `10.1016/j.mlwa.2026.100911` — Hettiarachchi et al., *SNOWTEC…*, MLWA 24 art. 100911 (июнь 2026). Смежный IE, не вердикт.

## 5. Вердикт

На **02.09.2026**: 0 мёртвых внутренних ссылок в собственных доках; scholarly DOI/arXiv из проверяемого набора резолвятся; единственный фабрикованный DOI карантинизирован errata с 04.08. Это снимок фактчека, не заявление о точности продукта и не RT CLOSED.
