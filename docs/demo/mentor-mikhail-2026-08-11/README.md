# Доказательства работы — AeroBIM

**Кому:** Михаил, IT-ментор  
**Дата:** 11.08.2026  
**Назначение:** проверить факты работы, а не прочитать обещания.

## Что здесь проверяется

| № | Утверждение | Чем подтверждается |
| --- | --- | --- |
| 1 | Есть сквозной прогон от документов до замечания | [evidence/slice-summary.json](evidence/slice-summary.json), [evidence/report.json](evidence/report.json) |
| 2 | Замечание привязано к месту и несёт след источника | [evidence/report.html](evidence/report.html) (просмотр), [evidence/slice-LIMITATIONS.json](evidence/slice-LIMITATIONS.json) |
| 3 | Система прочитала фрагмент чертежа через Yandex Cloud | [evidence/crops/00-content.png](evidence/crops/00-content.png), [evidence/vlm-result.json](evidence/vlm-result.json) |
| 4 | Границы заявлены явно и не подменяют факт | [evidence/vlm-LIMITATIONS.json](evidence/vlm-LIMITATIONS.json), [evidence/slice-LIMITATIONS.json](evidence/slice-LIMITATIONS.json) |
| 5 | Модель не ставит итог вместо эксперта | [10-fakty.md](10-fakty.md), пункт «Решение» |

## Как проверить за 3 минуты

1. Открыть [20-proverka.md](20-proverka.md) и сверить ключевые поля с `evidence/*.json`.  
2. Посмотреть [evidence/crops/00-content.png](evidence/crops/00-content.png) и значение **150 mm** в [evidence/vlm-result.json](evidence/vlm-result.json).  
3. Убедиться, что в ограничениях нет заявлений «точность 90%+», «итог ставит модель», «полностью готовое зрение».

## Полный перечень

- [00-index.md](00-index.md) — карта пакета  
- [10-fakty.md](10-fakty.md) — только факты и границы  
- [20-proverka.md](20-proverka.md) — как воспроизвести и что сверить  
- [evidence/](evidence/) — артефакты прогонов

Секретные ключи сюда не входят; идентификатор облачной папки в имени модели скрыт.
