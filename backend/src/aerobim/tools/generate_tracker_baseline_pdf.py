"""Generate baseline-2026-08.pdf (Cyrillic) for tracker chat."""
from __future__ import annotations

from pathlib import Path

import pymupdf

REPO = Path(__file__).resolve().parents[4]
OUT_PRIMARY = REPO / "docs" / "evidence" / "baseline-2026-08.pdf"
OUT_ALIAS = REPO / "docs" / "evidence" / "tracker-baseline-2026-08-07.pdf"

PAGES: list[list[str]] = [
    [
        "AeroBIM — baseline-2026-08 (трек-встреча / КТ#2)",
        "Checkpoint: NO_GO. Не точность продукта. Не >90%. Не customer SLA.",
        "",
        "1. Атрибуция 0,43 (первым)",
        "Измеряли НЕ модель AeroBIM, а сквозной конвейер:",
        "зонная нарезка → извлечение → сборка ответа",
        "на открытой модели через РФ-облако (Qwen / Yandex Studio).",
        "macro_extended = 0,4325 — в диапазоне фронтирных моделей AECV,",
        "работающих напрямую. Не превосходство над GPT/Gemini.",
        "Для заказчика без внешнего облака: конвейер не теряет качество",
        "на модели, доступной в закрытом контуре. open_bench_only.",
        "",
        "Таблица авторов (чужие чертежи): Gemini 0,51 · GPT-5.2 0,49 ·",
        "наш конвейер 0,43 · Claude 0,42 · GLM-4.6V 0,39.",
        "Тот же скорер: |Δ| к Table 1 ≤ 0,02.",
        "",
        "L2 Fixture SLA p95 ≈ 0,53 с — НЕ показатель реального комплекта.",
        "L3 Synthetic P=0,75 R=1,0 (n=6) — synthetic_only.",
        "Стоимость: ~111 ₽ (Wilson n≈111). «~11 ₽/100» — НЕ публиковать.",
    ],
    [
        "2. Критерии оценивания ТЗ → что измерено → чем → чего не хватает",
        "",
        "Коллизии/несоответствия >90% | протокол+harness | WP-07 | корпус RT-001",
        "Расчёт нагрузок | сверка чисел | cross-doc | не решатель",
        "Замечания RU/EN | шаблоны+advisory | TemplateRemark | не замена эксперта",
        "Стабильность | pytest+pin+hash | CI | —",
        "≤30 мин | fixture p95 | measure_package_sla | customer pack+machine",
        "MEP | NOT_VERIFIED | gap + Exp B ВК 13п.п. | федеративная модель RT-003",
        "Нормы | fail-closed loader | + Exp B КР 17п.п. | approved pack RT-002",
        "Native DWG | fail-closed | — | решение владельца",
        "",
        "3. Что значит «точность >90%» (методика, не цифра)",
        "Раздельные P и R; классы ошибок со своими целями;",
        "отдельный recall по критическим; Wilson CI + n;",
        "двойная слепая разметка; учёт FN; отложенная выборка;",
        "воспроизводимость (commit, hash, оборудование).",
        "Агрегат 90% вытягивается лёгкими классами — без разбивки не принимать.",
        "",
        "4. Exp B покрытие (не точность) — Киров ≠ Мордовия",
        "Киров КР n=24: из коробки 0%; условно 42% = 17п.п. norm + 25п.п. комплект",
        "Мордовия АР n=12: 17% из коробки (хрупко: ~8,3п.п./строка)",
        "Мордовия ВК n=16: 25% из коробки; условно 50%; вне обл. 13%;",
        "  RT-003 федеративная модель = 13п.п.",
        "Тренд 0→17→25%. Смета: RT-001 протокол · RT-002=17 · RT-003=13.",
        "",
        "MD: docs/evidence/baseline-2026-08.md",
        "Exp B: docs/evidence/EXPERIMENT_B_TYPICAL_REMARKS_KR_COVERAGE_2026_08.md",
    ],
]


def main() -> None:
    font_candidates = [
        Path(r"C:\Windows\Fonts\arial.ttf"),
        Path(r"C:\Windows\Fonts\segoeui.ttf"),
        Path(r"C:\Windows\Fonts\tahoma.ttf"),
    ]
    fontfile = next((p for p in font_candidates if p.exists()), None)
    if fontfile is None:
        raise SystemExit("No Cyrillic TTF found")

    doc = pymupdf.open()
    font = pymupdf.Font(fontfile=str(fontfile))
    for lines in PAGES:
        page = doc.new_page(width=595, height=842)
        tw = pymupdf.TextWriter(page.rect)
        y = 48.0
        for line in lines:
            tw.append((36, y), line, font=font, fontsize=9.5)
            y += 13.0
        tw.write_text(page)

    OUT_PRIMARY.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT_PRIMARY)
    doc.save(OUT_ALIAS)
    doc.close()
    print(f"wrote {OUT_PRIMARY} and alias {OUT_ALIAS.name} bytes={OUT_PRIMARY.stat().st_size}")


if __name__ == "__main__":
    main()
