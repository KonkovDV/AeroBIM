---
title: "AeroBIM — World Practices & Literature Refresh (2026-07-28)"
status: active
version: "1.0.0"
last_updated: "2026-07-28"
claim_boundary: "Literature validates the existing design. No new product claims. Checkpoint NO_GO until RT-001/002/003."
tags: [aerobim, research, literature, advisory, honesty]
---

# World Practices & Literature Refresh (2026-07-28)

Свежий обзор мировых практик и публикаций 2025–2026 по областям, критичным для
AeroBIM. **Вывод: литература подтверждает уже принятые инженерные решения** —
advisory-контур + детерминированная валидация + HITL, layered-defense против
инъекций, verbalized confidence как display-only. **Новых продуктовых claim'ов
не вводится**; Checkpoint остаётся **`NO_GO`** (RT-001/002/003).

> Цитирование — по заголовку/автору/году/венью и выводам из аннотаций
> (веб-поиск 2026-07-28); это не построчная проверка полных текстов.

## 1. Indirect / multimodal prompt injection

| Источник (2025–2026) | Вывод | Соответствие AeroBIM |
|---|---|---|
| Zhan et al., **NAACL 2025 Findings** — «Adaptive Attacks Break Defenses Against Indirect Prompt Injection» | Одиночные фильтры пробиваются адаптивными атаками | **Layered defense**, не один фильтр: output-as-data + strict schema fail-closed + caps + игнор value модели + advisory-never-verdict |
| Google Security 2025 (layered defense, Gemini 2.5); Microsoft MSRC 2025 | Промышленный консенсус — многослойная защита + мониторинг | + **новая observability**: `control_fields_ignored` — surfacing попыток инъекции для мониторинга (OWASP LLM 2025) |
| Gulyamov et al., **MDPI Information 17(1):54, 2026** (обзор 45 источников) | Быстрый рост от прямых к мультимодальным атакам | image-injection капы + containment уже внедрены |
| Geng et al., 2026 (ScienceDirect) | Мультимодальные PI достигают >90% успеха | Вердикт вне досягаемости контура по построению (ADR-001) |

**Изменение кода этого рефреша:** `ground_vlm_region_observations` теперь не только
**игнорирует** authority/verdict-ключи в ответе модели (verdict/passed/severity/
approval/compliance/…), но и **surfaces их имена** в `VlmRegionReadResult.
control_fields_ignored` — чтобы попытка over-reach/инъекции была **видима**
мониторингу (детектировать, а не только блокировать). Значения по-прежнему не
применяются; вердикт не затрагивается; OFF==ON сохраняется.

## 2. LLM для автоматической проверки соответствия (ACC) в BIM

| Источник | Вывод | Соответствие AeroBIM |
|---|---|---|
| Iversen et al., **Automation in Construction, 2026** (DSR-артефакт ACC на LLM) | LLM полезен как ассистент ACC при формализации правил | LLM = **advisory-драфтинг** (IDS-assist stub), не автономный вердикт |
| Madireddy et al., **MDPI Electronics 14(11):2146, 2025** | LLM-driven code compliance в BIM снижает ручной труд | Детерминированный движок владеет вердиктом (ADR-001); LLM не флипает `summary.passed` |
| Fuchs et al., **EC3 2026** (mediaTUM) — LLM-агенты генерируют переиспользуемые checking-функции | Итеративно write → refine → **validate** | Наш путь: черновик → **детерминированная валидация** → HITL |
| de Mendonça et al., **W78 2024** — ACC через **IDS** | Нейтральный IDS как основа ACC | IDS 1.0 — первичный детерминированный контур; IDS-assist только advisory |

## 3. Калибровка/верность verbalized confidence

| Источник | Вывод | Соответствие AeroBIM |
|---|---|---|
| «Are LLM Decisions Faithful to Verbal Confidence?» **arXiv 2601.07767, 2026** | Решения модели **не верны** её же вербальной уверенности | `confidence` — только display/ranking |
| Seo et al., **ACL 2026** (2026.acl-long.1098) | Ответ и уверенность **внутренне декуплированы** | `confidence_calibrated=False` по умолчанию → **каждый кандидат HITL** |
| ConfTuner, **NeurIPS 2025**; Wang et al. (OpenReview) | Калибровку надо обучать/пост-обрабатывать отдельно | Порог применяется **только** при явно калиброванном источнике |

## 4. VLM по инженерным/строительным чертежам

| Источник | Вывод | Соответствие AeroBIM |
|---|---|---|
| Picard et al., **Springer AI Review, 2025** (10.1007/s10462-025-11290-y) | VLM на инженерных задачах — ограничены, неравномерны | VLM — **advisory + HITL**, без «читает как инженер» |
| **DrawingVQA**, arXiv 2607.15418, 2026 (реальные «Issued for Construction» чертежи) | Реальные конструкторские чертежи — трудный бенчмарк для VLM | Значения нормализует **наш** детерминированный нормализатор, не модель |
| «Vision Foundation Models for Engineering Document…» (ResearchSquare rs-9528170) | Symbol/GD&T/BOM — активная, незрелая область | Детекторные priors честно помечены; без YOLO-весов в проде |
| Taormina et al., **Cambridge Prisms: Water, 2026** (18 VLM zero-shot, дефекты) | Zero-shot VLM-дефекты — вариативны | Дефект-«чтение» остаётся кандидатом под ревью |

## 5. Честные границы

- Литература **валидирует** дизайн — она **не добавляет** возможностей и не снимает
  внешних блокеров. `>90%` / DWG / MEP-delivered / CDE-ready остаются запрещёнными
  до данных заказчика (Claims Lock).
- Единственное изменение кода — **observability** инъекций (`control_fields_ignored`);
  это defense-in-depth-сигнал, а не новая гарантия предотвращения.
- Инварианты целы: вердикт — только детерминированный движок; **advisory OFF==ON**;
  fail-closed. **Checkpoint = NO_GO** (RT-001/002/003 — внешние).

## Sync

- Claim boundary: [`../pilot-claim-boundary-2026.md`](../pilot-claim-boundary-2026.md)
- Kimi K3 study: [`KIMI_K3_INTEGRATION_STUDY_2026_07_27.md`](KIMI_K3_INTEGRATION_STUDY_2026_07_27.md)
- Architecture SSOT: [`TARGET_HYBRID_ARCHITECTURE_TZ_2026.md`](TARGET_HYBRID_ARCHITECTURE_TZ_2026.md)
- Claims Lock: [`../../audit/reports/CLAIMS_LOCK_2026_07_17.md`](../../audit/reports/CLAIMS_LOCK_2026_07_17.md)
