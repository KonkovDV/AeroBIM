"""Generate tracker baseline PDF (Cyrillic) for 2026-08-07 meeting."""
from __future__ import annotations

from pathlib import Path

import pymupdf

# tools → aerobim → src → backend → repo
REPO = Path(__file__).resolve().parents[4]
OUT = REPO / "docs" / "evidence" / "tracker-baseline-2026-08-07.pdf"

PAGES: list[list[str]] = [
    [
        "AeroBIM — Baseline к трек-встрече 07.08.2026",
        "Checkpoint: NO_GO (RT-001/002/003 открыты). Не точность продукта.",
        "",
        "1. Три уровня измерений (не смешивать)",
        "L1 AECV-Bench (чужой протокол): macro_extended = 0.4325",
        "   модель: qwen3.6-35b-a3b / Yandex AI Studio; 117/120 планов",
        "   рядом: Gemini 0.51 · GPT-5.2 0.49 · Claude Opus 4.5 0.42 · GLM 0.39",
        "   claim_level=open_bench_only; ≠ продуктовая точность; ≠ RT-001",
        "L2 Fixture SLA (measure_package_sla): p95 ≈ 0.53 с",
        "   ≠ SLA ≤30 мин на комплекте заказчика",
        "L3 Synthetic detection Sprint2: P=0.75 R=1.0 (n=6 planted)",
        "   synthetic_only; n ниже планировщика half-width 0.08",
        "",
        "Стоимость: ~111 руб на Wilson n≈111 (grant notes).",
        "Цифра «~11 руб / 100 замечаний» — НЕ подтверждена evidence; не публиковать.",
        "",
        "Evidence:",
        "  docs/evidence/aecv-bench-eval-latest.json",
        "  docs/evidence/samolet-sla-fixture-p95-2026-08-04.json",
        "  docs/evidence/sprint2-synthetic-baseline-2026-08-04.json",
    ],
    [
        "2. Построчное соотнесение с критериями ТЗ задачи №7",
        "",
        "Критерий ТЗ                  | Сейчас                         | Статус",
        "Коллизии >90%                | протокол+harness; нет корпуса   | блокировано RT-001",
        "Несоответствия >90%          | то же                           | блокировано RT-001",
        "Ошибки расчёта нагрузок      | сверка чисел; не решатель       | не заявлено как solver",
        "Замечания RU/EN              | шаблоны + advisory LLM          | инструмент есть",
        "Стабильность                 | pytest + pin модели + hash      | измерено (инженерно)",
        "UI / эксперт                 | review shell + карта покрытия   | инструмент есть",
        "≤30 мин на комплект          | fixture p95 << 30 мин           | fixture only",
        "Когнитивная нагрузка         | HITL KPI-протокол               | не измерено на пилоте",
        "MEP / пересечения систем     | не в рабочем контуре            | gap RT-003",
        "Утверждённый норм-пакет      | loader fail-closed без approval | блокировано RT-002",
        "Native DWG                   | fail-closed                     | gap",
        "",
        "Вывод: «>90%» и «≤30 мин у Самолёта» — цели пилота.",
        "Предлагаем общий протокол измерения для всех 5 команд (К1).",
        "",
        "3. Коммерческий трек (честно)",
        "Список организаций: 28 SSOT (.local/commercial-ops/; не в GH)",
        "Исходящие контакты / ответы / демо: 0 / 0 / 0",
        "ТРЕБУЕТСЯ ОТ ВЛАДЕЛЬЦА: outreach оператором до пятницы.",
        "",
        "Полный MD: docs/evidence/tracker-baseline-2026-08-07.md",
        "Пакет: docs/quality/TRACKER_MEETING_PACK_2026_08_07.md",
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
        y = 52.0
        for line in lines:
            tw.append((40, y), line, font=font, fontsize=10)
            y += 14.0
        tw.write_text(page)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT)
    doc.close()
    print(f"wrote {OUT} bytes={OUT.stat().st_size} font={fontfile}")


if __name__ == "__main__":
    main()
