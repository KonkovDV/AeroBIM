<!-- claims-lint: allow-file reason="3-min human video script; forbidden phrases as non-claims; NO_GO explicit" -->
---
title: "КТ#2 — скрипт видео 3 мин (человек, 19.08)"
date: "2026-08-15"
last_updated: "2026-08-16"
claim_boundary: "Script for a human. Fixture demo. Checkpoint NO_GO. Not CV. Not CDE-ready. Not Renga export."
---

# Скрипт видео 3 минуты (19.08, человек)

**PII (первым, до формулы):** Штамп с листа в облако не отправляем. Облачный VLM видит только вырезанный фрагмент после клипа title-block.

**Что продаём (клин):** IFC Acceptance Gate — IFC + IDS/rule pack → finding с GUID/правилом/evidence → HTML/JSON/BCF. Overlay PDF — **следующая итерация того же конвейера доказательств**, не откат и не продукт этой записи.

**Формула (сразу после PII, дословно):** Мы на стадии доработки. Не заменяем 10D, Tangl и эксперта: независимая проверка приёмки IFC-пакета. Одна команда показывает находку с доказательствами на учебном комплекте. Валидация эффективности и внедрение ещё не начались. `NO_GO` сохраняется, пока нет корпуса Самолёта, двух разметчиков, подписанного профиля приёмки и подтверждения импорта в СОД.

**Не снимает ИИ.** Перед записью на чистой машине:

```powershell
cd backend
python -m aerobim.tools.run_demo_ifc_acceptance_gate
```

Открыть **свежий** `artifacts/ifc-acceptance-gate-demo/report.html` и `acceptance-gate.json`.  
Не открывать snapshot HTML из `docs/evidence/kt2-handoff-2026-08-11/` (`wall-guid/report.html` и `vertical-slice/report.html`). Live demo — только CLI.

Сценарий: IDS/атрибут стены (FireRating) на fixture IFC. Не «ИИ понял чертёж». Overlay — отдельная команда `run_demo_vertical_slice`, не обязательна на этой записи.

## Тайминг

| Сек | Экран | Текст (дословно) |
| ---: | --- | --- |
| 0–12 | README Checkpoint `NO_GO` | PII-строка выше, затем формула (дословно). |
| 12–50 | терминал, Acceptance Gate | «Ядро вердикта — IFC + IDS. Одна команда, fail-loud: HTML, JSON, acceptance-gate.json, BCF ZIP. Чертежи — тот же конвейер, следующая итерация; смешивать до профиля приёмки — врать о покрытии.» |
| 50–110 | `acceptance-gate.json` + `report.html` | «outcome, passed=false по ADR-001, capabilities, finding: GUID, правило, expected/observed, evidence_refs. Вердикт не PASS. Fixture demo.» |
| 110–140 | finding в HTML | «Требование → объект → доказательство. Эксперт оставляет решение.» |
| 140–165 | `findings.bcfzip` | «Структурный BCF ZIP. Импорт в СОД не проверяли. Не CDE-ready.» |
| 165–175 | IDS / схема | «Официальные IDS МОГЭ — IFC4. Чужая схема не проходит молча. Демо-IFC — IfcOpenShell, не Renga и не Самолёт.» |
| 175–180 | стоп | «10D хранит документы. Мы проверяем пригодность пакета. Tangl не заменяем. GO не рисуем. Порядок времени на fixture — лист KT2_FIXTURE_TIMING, не SLA.» |

## Запрещено в кадре и в голосе

точность >90%; SLA Самолёта; экономия ≥20%; native DWG; MEP delivered; интеграция с Tangl/10D; «закрыли АГР Москвы»; «демо = Renga»; двери/окна.

## После записи

Файл: `artifacts/demo/kt2-demo.mp4` (локально; в git не класть, если >лимита).  
Скриншот загрузки в ЛК — человек, 19–20.08. Операторский список файлов ЛК не публикуется в git.
