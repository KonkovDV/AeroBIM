# Пакет для Михаила — AeroBIM (11.08.2026)

**Одна ссылка на эту папку:**  
https://github.com/KonkovDV/AeroBIM/tree/main/docs/demo/mentor-mikhail-2026-08-11

Здесь всё нужное к созвону: краткий отчёт, текст письма, как показать за 7 минут и доказательства прогона.

## С чего начать

| Файл | Зачем |
| --- | --- |
| [01-otchet.md](01-otchet.md) | Краткий отчёт простыми словами |
| [02-pismo.md](02-pismo.md) | Текст «как от меня» |
| [03-kak-pokazat.md](03-kak-pokazat.md) | Сценарий показа на 7 минут |
| [evidence/](evidence/) | Результат прогона и картинка фрагмента |

## Суть в трёх предложениях

1. Есть честный сквозной показ: чертёж → проверка → замечание с привязкой к месту.  
2. Через Yandex Cloud система прочитала фрагмент чертежа и нашла толщину **150 мм**.  
3. Итог принимает не модель, а правила и человек; границы заявлены явно.

## Доказательства (уже в папке)

- Фрагмент листа: [evidence/crops/00-content.png](evidence/crops/00-content.png)
- Что вернула модель: [evidence/vlm-result.json](evidence/vlm-result.json) → значение `150 mm`
- Ограничения: [evidence/vlm-LIMITATIONS.json](evidence/vlm-LIMITATIONS.json), [evidence/slice-LIMITATIONS.json](evidence/slice-LIMITATIONS.json)
- Сводка детерминированного среза: [evidence/slice-summary.json](evidence/slice-summary.json)

## Повторный прогон (если нужно обновить артефакты)

Из каталога `backend/`:

```powershell
$env:PYTHONIOENCODING = "utf-8"
python -m aerobim.tools.run_vertical_slice --manifest ../samples/demo/vertical-slice-2026-08-11/manifest.json --output ../artifacts/vertical-slice-2026-08-11
python -m aerobim.tools.run_mentor_vlm_demo --pdf ../samples/demo/vertical-slice-2026-08-11/techlab-a101-wall-thickness.pdf --output ../artifacts/mentor-vlm-2026-08-11
```

Ключи и секреты в эту папку **не** кладём.
