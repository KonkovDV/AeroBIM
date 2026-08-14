<!-- claims-lint: allow-file reason="3-min human video script; forbidden phrases as non-claims; NO_GO explicit" -->
---
title: "КТ#2 — скрипт видео 3 мин (человек, 19.08)"
date: "2026-08-14"
claim_boundary: "Script for a human. Fixture demo. Checkpoint NO_GO. Not CV. Not CDE-ready. Not Renga export."
---

# Скрипт видео 3 минуты (19.08, человек)

**Не снимает ИИ.** Перед записью на чистой машине:

```powershell
cd backend
python -m aerobim.tools.run_demo_vertical_slice
```

Открыть **свежий** `artifacts/vertical-slice-demo/report.html`.  
Не открывать snapshot `docs/evidence/kt2-handoff-2026-08-11/vertical-slice/report.html` — там нет секции `#kt2-overlay` (срез 11.08, до коммита overlay).

Сценарий: штамп / экспликация / толщина стены на **текстовом слое PDF**. Не двери и окна.

## Тайминг

| Сек | Экран | Текст (дословно) |
| ---: | --- | --- |
| 0–20 | README Checkpoint `NO_GO` | «Промежуточная версия на учебном комплекте. Checkpoint у заказчика — NO_GO: нет корпуса РФ-экспертизы и нет подписанного профиля Самолёта.» |
| 20–50 | терминал, команда | «Одна команда из README. Fail-loud. Пишет HTML, JSON, PNG оверлея и BCF ZIP.» |
| 50–100 | `report.html` → `#kt2-overlay` | «Лист, текстовое доказательство, finding_id, source_id, evidence_refs, summary.passed=false. Вердикт не PASS. Рамка детерминированная, это не CV. Fixture demo.» |
| 100–130 | `overlay-problem-zone.png` рядом | «Оверлей — sibling PNG. Не обученный детектор штампа.» |
| 130–155 | `findings.bcfzip` | «Структурный BCF ZIP. Импорт в СОД не проверяли. Не CDE-ready.» |
| 155–175 | IDS / схема | «Официальные IDS МОГЭ — IFC4. Если схема другая, в том числе IFC4X3, не проходит молча. Демо-IFC в репо — IfcOpenShell, не Renga. Публичный Renga 8.7 ПНСТ 909 у нас измерен как IFC4.» |
| 175–180 | стоп | «Tangl проверяет модель, мы — комплект. 10D не заменяем. GO не рисуем.» |

## Запрещено в кадре и в голосе

точность >90%; SLA Самолёта; экономия ≥20%; native DWG; MEP delivered; интеграция с Tangl/10D; «закрыли АГР Москвы»; «демо = Renga»; двери/окна.

## После записи

Файл: `artifacts/demo/kt2-demo.mp4` (локально; в git не класть, если >лимита).  
Скриншот загрузки в ЛК — человек, 19–20.08. Список файлов ЛК: [`../pilot/KT2_UPLOAD_PACK_2026_08_14.md`](../pilot/KT2_UPLOAD_PACK_2026_08_14.md).
