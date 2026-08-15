<!-- claims-lint: allow-file reason="Demo rehearsal script; forbidden phrases as non-claims; NO_GO first" -->
---
title: "КТ#2 — репетиция демо 30–40 мин"
date: "2026-08-12"
last_updated: "2026-08-15"
claim_boundary: "Rehearsal script. Fixture GO. Checkpoint NO_GO. Live CLI slice, not wall-guid HTML."
---

# Demo rehearsal (30–40 min) — 20.08

**Формула (0–3 мин, дословно):** Мы на стадии доработки. Одна команда показывает live CLI с fail-closed доказательным finding на fixture. Валидация эффективности и внедрение ещё не начались. `NO_GO` сохраняется до корпуса Самолёта, двух разметчиков, signed scope и CDE-подтверждения.

**Открывать:** свежий `artifacts/vertical-slice-demo/report.html` после CLI.  
**Не открывать:** `docs/evidence/kt2-handoff-2026-08-11/wall-guid/report.html` и snapshot `…/vertical-slice/report.html` (нет `#kt2-overlay`).  
**Не просить:** раунд / SAFE / Checkpoint GO. Ask = слот + размеченный комплект.

Перед встречей:

```powershell
$ProgressPreference = 'SilentlyContinue'
cd backend
# предпочтительно: .venv-3.12\Scripts\python.exe
python -m aerobim.tools.run_demo_vertical_slice
python -m aerobim.tools.verify_kt2_handoff --write-status ../docs/evidence/kt2-handoff-2026-08-11/VERIFY.json
```

Ожидание: CLI **exit 0** (генерация, не customer PASS); handoff `checkpoint_verdict=NO_GO`.

## Minute plan

| Min | Open | Say |
| --- | --- | --- |
| 0–3 | README Checkpoint **NO_GO** | Формула выше. Не «система сломана». |
| 3–8 | [`KT2_JURY_FAQ_2026_08_12.md`](KT2_JURY_FAQ_2026_08_12.md) | Wave A ≠ CLOSED blockers. Локальный pytest ≠ CI pin README. |
| 8–12 | `VERIFY.json` + `STATUS.json` | L1 gate зелёный **и** вердикт NO_GO. |
| 12–22 | **live** `artifacts/vertical-slice-demo/report.html` → `#kt2-overlay` | Одна находка: лист, текст 150 mm / WALL-01, finding_id / source_id / evidence_refs, `summary.passed=false`. Не двери/окна. IFC = IfcOpenShell fixture, не Renga. |
| 22–26 | `overlay-problem-zone.png` рядом | Детерминированная рамка, не CV. |
| 26–30 | `findings.bcfzip` + capability table | Структурный ZIP / file ingest. Импорт в СОД — NOT_VERIFIED. |
| 30–34 | IDS fail-closed | МОГЭ = IFC4. Другая `FILE_SCHEMA` (в т.ч. IFC4X3) не проходит молча. |
| 34–38 | Tangl / 10D | Tangl = модель. Мы = комплект. 10D не заменяем. |
| 38–40 | Ask | Комплект + dual raters + слот. Не инвест-раунд. Юрлица нет. |

## Запрещено на репетиции

точность >90%; SLA Самолёта; MEP delivered; native DWG; Wave A закрыла RT-001/002/003; CDE import готов; Checkpoint GO; «демо = Renga»; «полностью проверено, потому что 2167».
