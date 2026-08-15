<!-- claims-lint: allow-file reason="Historical 11.08 demo script; >90% and native DWG listed as forbidden, not claimed" -->
# Vertical slice — демонстрация 11.08.2026

**Baseline зафиксирован:** HEAD `fc88d50b9313bde31bdee08ca38791a59fd48133` (Signed-off-by / GPG `G`).

## Выбранный сценарий (Вариант B, честный)

Один комплект, один запуск, один PDF с векторным текстовым слоем (без OCR-claim), извлечение `WALL-01 thickness 150 mm`, сопоставление с правилом/IFC-путём через существующий контур `AnalyzeProjectPackageUseCase`, формирование finding с `problem_zone` и provenance, экспорт JSON/HTML.

- **Вход:** `samples/demo/vertical-slice-2026-08-11/manifest.json` + `techlab-a101-wall-thickness.pdf` (генерируется скриптом) + существующие `samples/ifc/walls-multi-entity.ifc`, правила, IDS, ТЗ, расчёт.
- **Запуск:**  
  `python -m aerobim.tools.run_vertical_slice --manifest samples/demo/vertical-slice-2026-08-11/manifest.json --output artifacts/vertical-slice-2026-08-11`  
  (из `backend/`: `--manifest ../samples/... --output ../artifacts/...`)
- **Артефакты:** `report.json`, `report.html` (секция `#kt2-overlay` со ссылкой на sibling PNG), `overlay-problem-zone.png`, `slice-summary.json`, `LIMITATIONS.json` (входные SHA256, статус карты покрытия, воспроизводимый ключ finding, claim boundary, evidence envelope). Детерминированный bbox, не CV.

## Что честно заявлено

- PDF использует **text-layer extraction** (вектор), не trained CV.
- OCR — это baseline-эвристика, **не** инженерное понимание чертежа.
- `REQUIRES_EXPERT` выражается через coverage/operator status (`expert_required`, `not_checked`, `insufficient_data`, `no_findings`, `findings`), а не новым доменным claim.
- Исходные файлы не изменяются (read-only), SHA256 фиксируются.
- Детерминированный `summary.passed` не меняется advisory-контуром.
- **Evidence envelope:** каждая извлечённая аннотация несёт `method`, `method_version`, `source_sha256`, `page`, `region_bbox`, `quality_flags` (`heuristic_baseline`, `cv_verified=false`), `evidence_hash`.

## Ограничения (таблица)

| Пункт | Сейчас | Не заявляется |
| --- | --- | --- |
| Тип входа | Vector PDF (текстовый слой) | Сканированный PDF без текстового слоя, DWG native |
| Регионы | Heuristic coordinates from text blocks / annotations | Trained detector / stamp layout CV |
| Точность | Fixture-only, deterministic rules | >90% customer accuracy |
| Эксперт | Остаётся финальным решением | Автоматический sign-off |
| BCF 2.1 | Структурный smoke на существующем пути | Готовая CDE-интеграция |
| Metrics | extraction coverage, counts | customer accuracy, nDCG без ground truth |

## 7-минутный runbook

| Время | Действие | Проверка |
| --- | --- | --- |
| 0:00–0:40 | Показать `manifest.json` и PDF, открыть входы, назвать SHA256 | Входы и хеши видны в `slice-summary.json` |
| 0:40–1:30 | Запустить одну команду | CLI печатает сводку и `report_id` |
| 1:30–2:30 | Открыть `report.html` → страница/область/качество (annotation, coverage) | `drawing_annotations` = 1, `operator_status` заполнен |
| 2:30–3:30 | Показать извлечённое значение `WALL-01 thickness 150 mm` + источник (IFC/правила) | Аннотация и проблемная зона есть |
| 3:30–4:30 | Показать finding / coverage / honest статус | `summary.passed=false`, статусы не «no errors» |
| 4:30–5:30 | Открыть JSON → `problem_zone` с координатами, `evidence_refs`, `finding_id` | Привязка к sheet/page/координатам |
| 5:30–6:20 | Экспорт JSON/HTML/BCF через существующие API (по желанию `run_demo_path`) | Артефакты записаны |
| 6:20–7:00 | Показать таблицу ограничений и claim boundary | Нет «CV реализовано», «DWG», «>90%» |

## Быстрые проверки перед показом

```powershell
cd backend
python -m aerobim.tools.run_vertical_slice `
  --manifest ../samples/demo/vertical-slice-2026-08-11/manifest.json `
  --output ../artifacts/vertical-slice-2026-08-11
python -c "import json; p=Path('../artifacts/vertical-slice-2026-08-11/slice-summary.json'); d=json.loads(p.read_text(encoding='utf-8')); print(d['report_id'], d['summary'], d['operator_status_counts'], d['metrics'])"
```

## VLM-путь для звонка с ментором (crop → Yandex)

Отдельный runbook: [`mentor-call-mikhail-2026-08-11.md`](mentor-call-mikhail-2026-08-11.md).

```powershell
python -m aerobim.tools.run_mentor_vlm_demo `
  --pdf ../samples/demo/vertical-slice-2026-08-11/techlab-a101-wall-thickness.pdf `
  --output ../artifacts/mentor-vlm-2026-08-11
```

Advisory only: crop региона → Yandex Qwen → observations; **не** меняет `summary.passed`.


- Скан-PDF / RapidOCR путь с явным `OCR extraction, not engineering understanding`.
- Расширение coverage UI до явных 4 состояний на уровне интерфейса.
- BCF 2.1 — оставить structural smoke, не называть CDE-интеграцией.
- Нативный DWG и MEP system-aware clash — отдельные, отложенные контуры.
