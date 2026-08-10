# Как проверить и воспроизвести

## Быстрая сверка без запуска

| Что проверить | Где | Ожидаемый признак |
| --- | --- | --- |
| Прогон завершился | `evidence/slice-summary.json` | есть сводка и хэши входов |
| Чтение фрагмента сработало | `evidence/vlm-report.json` | `status = roundtrip_ok`, есть `reads[].observations` |
| Найдено значение | `evidence/vlm-report.json` | `raw_value` содержит `150 mm` |
| Ушёл фрагмент, не лист целиком | `evidence/crops/00-content.png` | `regions_read = 1`, `egress_crop = true` |
| Штамп не ушёл в модель | `evidence/vlm-report.json` | `stamp_regions_excluded >= 1` |
| Ограничения заявлены | `evidence/*LIMITATIONS.json` | без запрещённых обещаний; `model` без id папки |

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

Сверить, что свежие артефакты совпадают по смыслу с `evidence/`
(время и хэши могут отличаться).

## Красные флаги

- В отчётах появились обещания «точность выше 90%».
- Модель называется лицом, принимающим итог.
- В `crops/` есть роли вне `content` или `egress_crop` отсутствует.
- В `LIMITATIONS` виден реальный id облачной папки.
- В пакете встречаются секреты.
