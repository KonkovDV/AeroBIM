# Доказательства работы — AeroBIM

**Кому:** Михаил, IT-ментор  
**Дата:** 11.08.2026  
**Назначение:** проверить факты работы, а не прочитать обещания.

| № | Утверждение | Чем подтверждается |
| --- | --- | --- |
| 1 | Есть сквозной прогон от документов до замечания | [evidence/slice-summary.json](evidence/slice-summary.json), [evidence/report.json](evidence/report.json) |
| 2 | Замечание привязано к месту и несёт след источника | [evidence/report.html](evidence/report.html), [evidence/slice-LIMITATIONS.json](evidence/slice-LIMITATIONS.json) |
| 3 | Система прочитала фрагмент чертежа через Yandex Cloud | [evidence/crops/00-content.png](evidence/crops/00-content.png), [evidence/vlm-report.json](evidence/vlm-report.json) |
| 4 | В модель ушёл именно этот фрагмент (после защиты зон) | `crops[].egress_crop=true`, `bbox_xyxy[0]=0.1`, `crop_sha256` совпадает с чтением |
| 5 | Границы заявлены явно | [evidence/vlm-LIMITATIONS.json](evidence/vlm-LIMITATIONS.json), [evidence/slice-LIMITATIONS.json](evidence/slice-LIMITATIONS.json) |
| 6 | Модель не ставит итог вместо эксперта | [10-fakty.md](10-fakty.md) |

## Как проверить за 3 минуты

1. [20-proverka.md](20-proverka.md) — сверить поля с `evidence/*.json`.  
2. Открыть фрагмент и найти **150 mm** в `vlm-report.json`.  
3. Убедиться: `status=roundtrip_ok`, id папки скрыт, нет обещаний «точность 90%+».

## Файлы

- [00-index.md](00-index.md)  
- [10-fakty.md](10-fakty.md)  
- [20-proverka.md](20-proverka.md)  
- [evidence/](evidence/)  

Секреты сюда не входят.
