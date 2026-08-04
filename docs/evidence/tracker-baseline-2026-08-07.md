---
title: "Baseline к трек-встрече 07.08.2026"
date: 2026-08-04
claim_level: mixed_engineering_open_bench_synthetic
claim_boundary: >-
  Не точность продукта на корпусе заказчика. Не закрывает RT-001/002/003.
  Не публиковать «>90%» и «SLA ≤30 мин на комплекте заказчика».
---

# Baseline AeroBIM — трек-встреча 07.08.2026

**Формат:** документ для трекера (PDF-близнец рядом)  
**Checkpoint:** **NO_GO**  
**HEAD на момент сборки пакета:** локальное дерево после `385c4b9` + незакоммиченные К1–К6

## 1. Что измеряли (три разных уровня — не смешивать)

| Уровень | Что это | Цифра | Граница |
|---|---|---|---|
| **L1 Open-bench** | AECV-Bench object counting, чужой корпус и протокол (arXiv:2601.04819) | **macro_extended = 0,4325** | `claim_level=open_bench_only`; ≠ продукт |
| **L2 Fixture SLA** | `measure_package_sla` на демо-пакете | p95 ≈ **0,0089 мин ≈ 0,53 с** | fixture only; ≠ customer SLA |
| **L3 Synthetic detection** | посаженные дефекты, Sprint 2 | P=**0,75** / R=**1,0** (n=6) | `synthetic_only`; n ниже планировщика |

Evidence:
- AECV: `docs/evidence/aecv-bench-eval-latest.json`
- SLA fixture: `docs/evidence/samolet-sla-fixture-p95-2026-08-04.json`
- Synthetic: `docs/evidence/sprint2-synthetic-baseline-2026-08-04.json`

### 1.1 AECV — контекст таблицы авторов (пятиполевая метрика)

| Модель | Mean |
|---:|---:|
| Gemini 3 Pro (paper) | 0,51 |
| GPT-5.2 | 0,49 |
| **AeroBIM pipeline + Qwen 3.6-35b (Yandex Studio)** | **0,4325** |
| Claude Opus 4.5 | 0,42 |
| GLM-4.6V (лучшая открытая в paper) | 0,39 |

Скорер сходится с Table 1 авторов в допуске \|Δ\|≤0,02.  

**Чей это результат (обязательная оговорка):** измеряли не «модель AeroBIM», а **сквозной конвейер** (зонная нарезка → извлечение → сборка ответа) на **открытой** модели через российское облако. Цифра в одном диапазоне с фронтирными коммерческими моделями, работающими напрямую. Содержание для заказчика без внешнего облака: конвейер **не теряет** качество на модели, доступной в закрытом контуре. Не «мы лучше GPT». Не точность нормоконтроля. `claim_level=open_bench_only`.

Код/модель: `qwen3.6-35b-a3b`, 117/120 планов (3 vendor HTTP 400 исключены).
### 1.2 Стоимость (только измеренное)

| Статья | Оценка | Источник |
|---|---|---|
| Wilson-выборка n≈111 (half-width ≤0,08) | порядка **~111 ₽** токенов | grant / deep-analysis notes |
| «~11 ₽ за комплект из 100 замечаний» | **не подтверждено evidence-файлом** | **ТРЕБУЕТСЯ ОТ ВЛАДЕЛЬЦА** — не публиковать |

## 2. Построчное соотнесение с критериями оценивания ТЗ задачи №7

Статусы: `измерено (граница)` | `инструмент есть, цифра нет` | `не заявлено / gap` | `блокировано данными заказчика`

| Критерий ТЗ (смысл) | Что умеем показать сейчас | Статус | Evidence / код |
|---|---|---|---|
| Коллизии, точность >90% | Протокол + harness; на customer-корпусе **не измерено** | блокировано данными | WP-07 / PrecisionClaim; RT-001 |
| Несоответствия, точность >90% | То же | блокировано данными | RT-001 |
| Ошибки расчёта нагрузок | Сверка чисел / provenance; не решатель | не заявлено как solver | cross-doc |
| Замечания RU/EN | Шаблоны + advisory LLM | инструмент есть | TemplateRemarkGenerator |
| Стабильность / воспроизводимость | pytest + pin модели + hash пакета | измерено (инженерно) | CI / evidence JSON |
| Масштабирование | Jobs; fixture малы | частичное | — |
| UI / удобство эксперта | Review shell + coverage map | инструмент есть | frontend CoverageMapPanel |
| ≤30 мин на комплект | Fixture p95 ≪ 30 мин; customer **не измерен** | измерено (fixture only) | measure_package_sla schema 1.4.0 |
| Снижение когнитивной нагрузки | HITL KPI-протокол | не измерено на пилоте | — |
| MEP / пересечения систем | Системный MEP-clash не в контуре | gap (RT-003) | MEP-CLASH-001 |
| Нормы / утверждённый пакет | Loader fail-closed без approval | блокировано (RT-002) | NormRulePackLoader |
| DWG native | Fail-closed, не заявляется | gap | — |

**Вывод для трекера:** цифры «>90%» и «≤30 мин на комплекте Самолёта» остаются **целями пилота**. Мы принесли **методику**, которой эти цифры можно проверить у всех пяти команд (см. К1).

## 3. Код и воспроизведение

```text
# AECV evidence (уже записан)
docs/evidence/aecv-bench-eval-latest.json

# Fixture SLA
python -m aerobim.tools.measure_package_sla --help

# Synthetic Sprint 2 baseline
python -m aerobim.tools.run_sprint2_synthetic_baseline
```

## 4. Честные ограничения

1. Нет корпуса заказчика с двойной разметкой → нет publishable precision.  
2. Нет подписанного norm-pack → RT-002.  
3. Нет федеративной MEP-модели заказчика → RT-003.  
4. Outreach = 0 до заполнения оператором.  
5. Коммерческий SSOT: **28** организаций в `.local/commercial-ops/commercial-pipeline.csv` (не в GH; цель трекера 30+ ещё OPEN).

## 5. Следующий шаг после встречи

Предложить Самолёту принять `PROTOCOL_QUALITY_ACCEPTANCE_TASK07` как **общий** критерий приёмки задачи №7.

Red Team wave-2: [`../quality/RED_TEAM_WAVE2_TRACKER_COMMERCIAL_2026_08_04.md`](../quality/RED_TEAM_WAVE2_TRACKER_COMMERCIAL_2026_08_04.md).
