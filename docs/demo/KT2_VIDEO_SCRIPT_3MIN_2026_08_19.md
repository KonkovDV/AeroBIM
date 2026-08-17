<!-- claims-lint: allow-file reason="Withdrawn KT#2 video notice; forbidden phrases as non-claims; NO_GO explicit" -->
---
title: "КТ#2 — видео не записываем и не прилагаем"
date: "2026-08-15"
last_updated: "2026-08-17"
claim_boundary: "Video withdrawn. Live CLI is the demo. Checkpoint NO_GO. Not a recorded mp4."
---

# Видео к КТ#2 не записываем

Ролик 2–3 мин **не снимаем и в форму приёма не прикладываем.** Показ — живой CLI на клоне:

```powershell
cd backend
python -m aerobim.tools.run_demo_ifc_acceptance_gate
```

Это учебный комплект, `summary.passed=false` ожидаем, Checkpoint **`NO_GO`**. Снимок HTML демонстрацией не является.

**Не открывать** `docs/evidence/kt2-handoff-2026-08-11/wall-guid/report.html` и `vertical-slice/report.html` как overlay. Live demo — только CLI.

mp4 в git нет и не появится. Поле «видео» карточки программы оставляем пустым; не подменяем его скриптом и не рисуем записанный показ.

Мы на стадии доработки. Одна команда показывает находку с доказательствами на учебном комплекте. Валидация эффективности и внедрение ещё не начались. `NO_GO` сохраняется, пока нет корпуса Самолёта, двух разметчиков, подписанного профиля приёмки и подтверждения импорта в СОД.
