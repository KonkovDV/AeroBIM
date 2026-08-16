<!-- claims-lint: allow-file reason="Demo rehearsal script; forbidden phrases as non-claims; NO_GO first" -->
---
title: "КТ#2 — репетиция демо 30–40 мин"
date: "2026-08-12"
last_updated: "2026-08-16"
claim_boundary: "Rehearsal script. Fixture GO. Checkpoint NO_GO. Live Acceptance Gate first; overlay is P1 sequence."
---

# Demo rehearsal (30–40 min) — 20.08

**PII (0–1 мин, первым):** Штамп с листа в облако не отправляем.

**Формула (1–3 мин, дословно):** Мы на стадии доработки. Одна команда показывает live CLI с fail-closed доказательным finding на fixture. Валидация эффективности и внедрение ещё не начались. `NO_GO` сохраняется до корпуса Самолёта, двух разметчиков, signed scope и CDE-подтверждения.

**Framing сужения (одна фраза):** ядро вердикта — IFC/IDS; чертежи — тот же конвейер, следующая итерация; смешивать до профиля приёмки — врать о покрытии.

**Открывать:** свежий `artifacts/ifc-acceptance-gate-demo/report.html` и `acceptance-gate.json` после Gate CLI. Overlay — только если осталось время (`artifacts/vertical-slice-demo/`).  
**Не открывать:** `docs/evidence/kt2-handoff-2026-08-11/wall-guid/report.html` и snapshot `…/vertical-slice/report.html`.  
**Не просить:** раунд / SAFE / Checkpoint GO. Ask = слот + размеченный комплект.  
**Время:** [`KT2_FIXTURE_TIMING_2026_08_16.md`](KT2_FIXTURE_TIMING_2026_08_16.md) — порядок величины, не SLA.

Перед встречей:

```powershell
$ProgressPreference = 'SilentlyContinue'
cd backend
# предпочтительно: .venv-3.12\Scripts\python.exe
python -m aerobim.tools.run_demo_ifc_acceptance_gate
# P1, если осталось время:
# python -m aerobim.tools.run_demo_vertical_slice
python -m aerobim.tools.verify_kt2_handoff --write-status ../docs/evidence/kt2-handoff-2026-08-11/VERIFY.json
```

Ожидание: CLI **exit 0** (генерация, не customer PASS); Gate `checkpoint_verdict=NO_GO`, `passed=false`.

## Minute plan

| Min | Open | Say |
| --- | --- | --- |
| 0–1 | README | PII-строка. Не ждать вопроса про штамп. |
| 1–3 | README Checkpoint **NO_GO** | Формула + framing сужения. Не «система сломана», не «не осилили чертежи». |
| 3–8 | [`KT2_JURY_FAQ_2026_08_12.md`](KT2_JURY_FAQ_2026_08_12.md) | Wave A ≠ CLOSED blockers. Локальный pytest ≠ CI pin README. |
| 8–12 | `VERIFY.json` + `STATUS.json` | L1 gate зелёный **и** вердикт NO_GO. |
| 12–22 | **live** `acceptance-gate.json` + `report.html` | outcome/passed по ADR-001; findings GUID/правило/evidence; `outcome_scope=full_package`. Не двери/окна. IFC = IfcOpenShell fixture, не Renga. |
| 22–26 | [`KT2_FIXTURE_TIMING_2026_08_16.md`](KT2_FIXTURE_TIMING_2026_08_16.md) | Порядок секунды на fixture. Не ≤30 мин ТЗ. |
| 26–30 | `findings.bcfzip` + capability table | Структурный ZIP / file ingest. Импорт в СОД — NOT_VERIFIED. |
| 30–34 | IDS fail-closed | МОГЭ = IFC4. Другая `FILE_SCHEMA` (в т.ч. IFC4X3) не проходит молча. |
| 34–38 | Tangl / 10D; overlay только если время | Tangl = модель. Мы = комплект. Overlay = P1 того же конвейера. |
| 38–40 | Ask | [`../partners/SAMOLET_KT2_ASK_2026_08_15.md`](../partners/SAMOLET_KT2_ASK_2026_08_15.md). Не инвест-раунд. Юрлица нет. |

## Запрещено на репетиции

точность >90%; SLA Самолёта; MEP delivered; native DWG; Wave A закрыла RT-001/002/003; CDE import готов; Checkpoint GO; «демо = Renga»; «полностью проверено, потому что 2167».
