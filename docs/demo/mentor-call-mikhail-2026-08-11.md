# Mentor call — Михаил (IT), 11.08.2026

**Цель звонка:** показать, что AeroBIM **читает чертёж** двумя честными путями —
(1) детерминированный text-layer vertical slice, (2) **crop региона → Yandex Qwen VLM → JSON**.
Verdict (`summary.passed`) **не** решает VLM.

**Стек VLM:** Yandex AI Studio · `qwen3.6-35b-a3b` · OpenAI-compat · `Api-Key` + `x-folder-id`.  
**Имена в коде:** advisory contour = `vlm_*` / `AEROBIM_VLM_*` (устаревший алиас `AEROBIM_KIMI_*`).

---

## Перед звонком (5 мин)

```powershell
cd C:\plans\AeroBIM\backend
$env:PYTHONIOENCODING = "utf-8"

# 1) Детерминированный срез (обязательно)
python -m aerobim.tools.run_vertical_slice `
  --manifest ../samples/demo/vertical-slice-2026-08-11/manifest.json `
  --output ../artifacts/vertical-slice-2026-08-11

# 2) VLM mentor demo (live Yandex; нужен backend/.env)
python -m aerobim.tools.run_mentor_vlm_demo `
  --pdf ../samples/demo/vertical-slice-2026-08-11/techlab-a101-wall-thickness.pdf `
  --output ../artifacts/mentor-vlm-2026-08-11

# Offline rehearsal без ключа/сети:
python -m aerobim.tools.run_mentor_vlm_demo --dry-crop-only `
  --output ../artifacts/mentor-vlm-2026-08-11
```

**Live smoke (2026-08-10, этот стенд):** `status=roundtrip_ok`, Yandex `qwen3.6-35b-a3b`,
1 region crop → ≥1 observation, `hitl_required` возможен, `degraded=true` (advisory).
Показать `reads[].observations[].raw_value` и PNG в `crops/`.

Ожидание live: `report.json` → `"status": "roundtrip_ok"`, папка `crops/*.png`, `LIMITATIONS.json`.

Если live упал — показывать vertical slice + crops + схему `candidate_class` + этот LIMITATIONS. **Не выдумывать успех VLM.**

---

## Скрипт 7 минут

| Время | Что говорить / показывать | Доказательство |
| --- | --- | --- |
| 0:00–0:45 | «Один PDF, два контура: правила и advisory vision» | PDF + `manifest.json` |
| 0:45–2:15 | Vertical slice: text-layer → `WALL-01 thickness 150 mm` → finding | `artifacts/.../report.html` |
| 2:15–3:00 | Claim boundary: не CV product, не >90%, не DWG | `LIMITATIONS.json` среза |
| 3:00–4:30 | **VLM:** layout → crop региона (не весь лист) → Yandex | `crops/*.png` + `mentor-vlm.../report.json` |
| 4:30–5:30 | Structured observations / `candidate_class`; HITL если надо | `reads[].observations` |
| 5:30–6:20 | **ADR-001:** VLM advisory; `summary.passed` только детерминизм; OFF==ON | одна фраза + slice `passed_unchanged` |
| 6:20–7:00 | Roadmap P0–P4 baselines; завтрашний next: labeled corpus | `docs/plans/cv-roadmap-2026-08.md` |

---

## Фразы «да / нет»

**Да:**
- «Yandex Cloud подключён, модель с Base64-изображениями, live open-bench уже мерили.»
- «В модель уходит **crop региона**, штамп исключён.»
- «VLM даёт кандидаты; эксперт и детерминированный движок решают.»

**Нет / не говорить:**
- «У нас product computer vision / LayoutLM в проде.»
- «Точность >90%.»
- «VLM ставит PASS/FAIL.»
- «Читаем native DWG.»
- «Отправляем весь лист.»

---

## Если Михаил спросит «а это реально читает?»

1. Показать PNG crop (`crops/`).
2. Показать `reads` в `report.json` (raw_value / kind / confidence).
3. Сказать: «Это advisory observation на open fixture; customer corpus и trained detector — следующий этап (roadmap).»

---

## Артефакты на диск

| Путь | Зачем |
| --- | --- |
| `artifacts/vertical-slice-2026-08-11/` | детерминированный demo |
| `artifacts/mentor-vlm-2026-08-11/report.json` | live VLM roundtrip |
| `artifacts/mentor-vlm-2026-08-11/crops/` | визуал для экрана |
| `artifacts/mentor-vlm-2026-08-11/LIMITATIONS.json` | claim boundary |
| `docs/demo/mentor-call-mikhail-2026-08-11.md` | этот runbook |

---

## Техническая шпаргалка (30 сек)

```
PDF → HeuristicLayoutRegionDetector
   → RegionReadPlan (stamp out, text_layer skip unless forced)
   → PdfiumRegionCropper (PNG)
   → VlmAdvisoryClient → Yandex /v1/chat/completions (image_url data:)
   → observations JSON → grounding → candidates
   ✗ never → summary.passed
```
