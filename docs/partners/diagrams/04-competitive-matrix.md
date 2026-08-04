# 4. Конкурентные оси (сжатая матрица)

Полная таблица: [`../COMPETITIVE_MATRIX_2026_08.md`](../COMPETITIVE_MATRIX_2026_08.md).

```mermaid
quadrantChart
    title Где гипотеза AeroBIM отличима
    x-axis Низкая зрелость экосистемы --> Высокая зрелость экосистемы
    y-axis Слабая ответственность за вердикт --> Доказуемая ответственность
    quadrant-1 Зрелые model checkers
    quadrant-2 Целевая зона AeroBIM
    quadrant-3 Типичный «ИИ проверяет»
    quadrant-4 Issue trackers
    Solibri: [0.85, 0.35]
    Navisworks: [0.9, 0.3]
    BIMcollab: [0.55, 0.4]
    AeroBIM: [0.25, 0.85]
```

Честные уступки: зрелость model checking и доля рынка — у зарубежных продуктов выше. Отличие AeroBIM — связка cross-doc + provenance + fail-closed + OFF==ON.
