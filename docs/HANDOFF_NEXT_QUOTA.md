# HANDOFF — следующая квота (AeroBIM)

**Для:** другой аккаунт / следующий исполнитель  
**Дата среза:** 2026-10-15 (МСК)  
**main tip:** `d7a0290` — docs CI badge  
**Factcheck:** `/workspace/AeroBIM-audit/FACTCHECK_RERUN_2026-10-15_2108.md` (агент AeroBIM)  
**Жёстко:** `customer_go=false` **forever** until real customer corpus + dual raters. Checkpoint GO ≠ customer_go. RT тома OPEN остаются OPEN.

## Блокер merge-цепочки

### [#141](https://github.com/KonkovDV/AeroBIM/pull/141) `fix/p0-honesty-baseline-auth-k2a` @ `ee4b313` → **HOLD**

- Ruff снят; lint/test/plans green.
- **Блокер:** `pytest-readme-extras` — 2 IDS-кейса (`get_attribute_category` на IfcWall): **case_0017**, **case_0101**.
- Pin ifcopenshell 0.8.5 = main, но extras на main был green — разобрать регрессию ветки vs pin/fixtures.
- После фикса → новый SHA → factcheck AeroBIM → merge **только** при GO+full green.
- Desk: AB-P0-01/02/04/05 PASS по коду; AB-P0-03 PARTIAL (pptx/pdf с 01.10 не обновлялись — желательно follow-up).

**Не мержить #142–#145 до зелёного #141.**

## Открытые PR после #141

| PR | Ветка | Действие |
|---|---|---|
| [#142](https://github.com/KonkovDV/AeroBIM/pull/142) | `fix/p1-k2a-honesty` | Rebase на #141; App.test под CVD chips; merge после GO |
| [#143](https://github.com/KonkovDV/AeroBIM/pull/143) | `feat/k2a-p1-03-reliability-report` | desk-OK; `publishable=false` по умолчанию — сохранить |
| [#144](https://github.com/KonkovDV/AeroBIM/pull/144) | `feat/k2a-p1-04-stamp-dual-read` | DESK-PARTIAL — dual-read → ABSTAIN |
| [#145](https://github.com/KonkovDV/AeroBIM/pull/145) | `feat/k2a-p1-02-auto-next` | DESK-PARTIAL — j/k + «очередь пуста» |

## Остаток P1 (после #142) — сжато

Полный текст: локально `BRIEF_P1_REMAINING_AFTER_142.md` / `BRIEF_P1_ACCEPTANCE.md` у агента AeroBIM.

| ID | Статус | Минимум |
|---|---|---|
| AB-P1-01 | OPEN | corpus/dual raters — org; код: PrecisionClaim запрещён, `customer_go=false` |
| AB-P1-02 | OPEN | approval object RT-002c или явный NOT_VERIFIED / только public IDS |
| AB-P1-03 | OPEN | MEP: NOT_VERIFIED или полная проверка; неполный scope → NOT_VERIFIED |
| AB-P1-04 | OPEN | OIDC BFF ready **или** lab-only + запрет SSO-ready claims |
| AB-P1-05/06 | в #142 | mypy --strict SSOT; orphan-SHA doc — после green |
| K2A-P0-02b | OPEN? | abstain + reason_code; нельзя expert-confirm без reason |
| K2A-P1-01 | #142 + leftover | chips/a11y; не только цвет |
| K2A-P1-02 | #145 | auto-next / очередь пуста |
| K2A-P1-03 | #143 | reliability JSON, publishable=false без customer |
| K2A-P1-04 | #144 | stamp dual-read disagreement → ABSTAIN |
| K2A-P1-05 | PARTIAL | poison→DEAD_LETTER виден в API+UI (не дублировать store) |
| K2A-P1-06 | OPEN | audit history на карточке |

**Не заявлять** без кода: idempotency BCF, dedup, Wilson-EM, customer corpus, MEP verified, SSO-ready.

## Порядок

1. Fix IDS extras на #141 → factcheck → merge.  
2. #142 rebase+test → merge.  
3. #143 → #145 (или по BRIEF order: P0-02b → P1-01 leftover → P1-02 → P1-06 → P1-05 → P1-03 → P1-04).  
4. AB-P1-02/03/04 продуктовые OPEN.  
5. AB-P1-01 организационный.

## Не делать

- Ставить `customer_go=true` без реального корпуса.  
- Тяжёлые dependabot (#130 ifcopenshell 0.9 и др.) до стабилизации #141.  
- Merge поверх красного #141.

## CI note (этот docs PR #146)

`docs-links` падает на **pre-existing** `check_live_evidence_freshness`: `*-latest.json` от 2026-10-01 (~14d, max 7d) — не из‑за текста HANDOFF. Пока evidence не обновлён, docs-only PR не станет green. **Не** ставить `customer_go=true`. Следующий аккаунт: либо `make evidence`/регенерация latest JSON (отдельный PR), либо merge handoff осознанно поверх известного долга после фикса #141.
