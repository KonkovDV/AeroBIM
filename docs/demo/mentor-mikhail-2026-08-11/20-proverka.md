# Как проверить и воспроизвести

## Быстрая сверка без запуска

| Что проверить | Где | Ожидаемый признак |
| --- | --- | --- |
| Прогон завершился | `evidence/slice-summary.json` | есть сводка и хэши входов |
| Чтение фрагмента сработало | `evidence/vlm-result.json` | `status = ok`, найдено `150 mm` |
| Ушёл фрагмент, не лист целиком | `evidence/crops/00-content.png` | один регион; `regions_read = 1` |
| Штамп не ушёл в модель | `evidence/vlm-result.json` | `stamp_regions_excluded = 4` |
| Ограничения заявлены | `evidence/*LIMITATIONS.json` | без запрещённых обещаний |

## Воспроизведение из репозитория

Из каталога `backend/`:

```powershell
$env:PYTHONIOENCODING = "utf-8"
python -m aerobim.tools.run_vertical_slice `
  --manifest ../samples/demo/vertical-slice-2026-08-11/manifest.json `
  --output ../artifacts/vertical-slice-2026-08-11

python -m aerobim.tools.run_mentor_vlm_demo `
  --pdf ../samples/demo/vertical-slice-2026-08-11/techlab-a101-wall-thickness.pdf `
  --output ../artifacts/mentor-vlm-2026-08-11
```

Проверить, что свежие артефакты совпадают по смыслу с копиями в `evidence/`
(время и хэши могут отличаться — это нормально для повторного прогона).

## Красные флаги при проверке

- В отчётах появились обещания «точность выше 90%».
- Модель называется лицом, принимающим итог.
- Говорится о целом листе вместо фрагмента без оговорок.
- В пакете встречаются секреты или идентификаторы, которых не должно быть.
