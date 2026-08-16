<!-- claims-lint: allow-file reason="3-min human video script; forbidden phrases as non-claims; NO_GO explicit" -->
---
title: "КТ#2 — скрипт видео 3 мин (человек, 19.08)"
date: "2026-08-15"
claim_boundary: "Script for a human. Fixture demo. Checkpoint NO_GO. Not CV. Not CDE-ready. Not Renga export."
---

# Скрипт видео 3 минуты (19.08, человек)

**Что продаём (клин):** IFC Acceptance Gate — IFC + IDS/rule pack → finding с GUID/правилом/evidence → HTML/JSON/BCF. Overlay PDF — P1, не продукт.

**Формула (0–20 с, дословно):** Мы на стадии доработки. Не заменяем 10D, Tangl и эксперта: независимый acceptance gate для IFC-пакета. Одна команда показывает live CLI с fail-closed доказательным finding на fixture. Валидация эффективности и внедрение ещё не начались. `NO_GO` сохраняется до корпуса Самолёта, двух разметчиков, signed scope и CDE-подтверждения.

**Не снимает ИИ.** Перед записью на чистой машине:

```powershell
cd backend
python -m aerobim.tools.run_demo_ifc_acceptance_gate
```

Открыть **свежий** `artifacts/ifc-acceptance-gate-demo/report.html` и `acceptance-gate.json`.  
Не открывать snapshot `docs/evidence/kt2-handoff-2026-08-11/vertical-slice/report.html`.

Сценарий: IDS/атрибут стены (FireRating) на fixture IFC. Не «ИИ понял чертёж». Overlay — отдельная команда `run_demo_vertical_slice`, не обязательна на этой записи.

## Тайминг

| Сек | Экран | Текст (дословно) |
| ---: | --- | --- |
| 0–20 | README Checkpoint `NO_GO` | Формула выше (дословно). |
| 20–50 | терминал, Acceptance Gate | «Одна команда: IFC + IDS. Fail-loud. Пишет HTML, JSON, acceptance-gate.json и BCF ZIP. Overlay не нужен.» |
| 50–110 | `acceptance-gate.json` + `report.html` | «outcome, passed=false по ADR-001, capabilities, finding: GUID, правило, expected/observed, evidence_refs. Вердикт не PASS. Fixture demo.» |
| 110–140 | finding в HTML | «Требование → объект → доказательство. Эксперт оставляет решение.» |
| 140–165 | `findings.bcfzip` | «Структурный BCF ZIP. Импорт в СОД не проверяли. Не CDE-ready.» |
| 165–175 | IDS / схема | «Официальные IDS МОГЭ — IFC4. Чужая схема не проходит молча. Демо-IFC — IfcOpenShell, не Renga и не Самолёт.» |
| 175–180 | стоп | «10D хранит документы. Мы проверяем пригодность пакета. Tangl не заменяем. GO не рисуем.» |

## Запрещено в кадре и в голосе

точность >90%; SLA Самолёта; экономия ≥20%; native DWG; MEP delivered; интеграция с Tangl/10D; «закрыли АГР Москвы»; «демо = Renga»; двери/окна.

## После записи

Файл: `artifacts/demo/kt2-demo.mp4` (локально; в git не класть, если >лимита).  
Скриншот загрузки в ЛК — человек, 19–20.08. Список файлов ЛК: [`../pilot/KT2_UPLOAD_PACK_2026_08_14.md`](../pilot/KT2_UPLOAD_PACK_2026_08_14.md).
