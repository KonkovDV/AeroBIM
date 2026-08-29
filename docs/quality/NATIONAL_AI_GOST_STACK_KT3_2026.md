<!-- claims-lint: allow-file reason="National AI GOST stack mapping; not 42001 certification; NO_GO" -->
---
title: "National AI GOST stack for KT#3 — mapping, not certification"
date: "2026-08-29"
last_updated: "2026-08-29"
status: active
version: "1.1.0"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_boundary: >
  Pointers to in-force GOST R AI standards and how existing AeroBIM honesty
  maps. Not a certified AI management system. Not a product-accuracy claim.
  Checkpoint NO_GO.
---

# Национальный стек ИИ (ТК 164) — карта, не сертификат

**Совместимость не сертификация.** Текст стандартов не копируется.

| Обозначение | Карточка / приказ | Зачем комиссии (К2) | Чего это не значит |
|---|---|---|---|
| ГОСТ Р 71476-2024 (ИСО/МЭК 22989:2022) | приказ 28.10.2024 № **1550-ст**, введение **01.01.2025** ([ГАРАНТ](https://base.garant.ru/411037370/); карточка UUID фонда не скачана) | Термины: система ИИ ≠ вердикт эксперта | Мы «стандартизовали отрасль» |
| ГОСТ Р ИСО/МЭК 42001-2024 | [protect.gost.ru](https://protect.gost.ru/gost/details/3cb023c3-e628-45ad-b233-65e3d175eb10): **1549-ст**, 28.10.2024, введение 01.01.2025 | Система менеджмента ИИ: HITL, пересмотр, роли | Сертифицированная СМИИ / знак обращения |
| ГОСТ Р 72514-2026 (ИСО/МЭК 42005:2025) | карточка фонда **64-ст** / 30.01.2026 | Оценка воздействия | Декларация соответствия |
| ГОСТ Р 72515-2026 (ИСО/МЭК 12792:2025) | карточка фонда **65-ст** / 30.01.2026 | Таксономия прозрачности: ограничения, данные | Сертификат прозрачности |
| ГОСТ Р 71752-2024 | [protect.gost.ru](https://protect.gost.ru/gost/details/b3926061-79c5-4b06-8047-cca58156902e): **1548-ст**, 28.10.2024, введение 01.01.2025 | Содержание ТЗ на ИИ: потребности, контроль, приёмка | Наше ТЗ заменяет ТЗ партнёра |
| ГОСТ Р 71539-2024 (ИСО/МЭК 5338:2023) | [protect.gost.ru](https://protect.gost.ru/gost/details/31be4384-1429-42e4-8f94-8fe339d2276f): **1539-ст**, 28.10.2024, введение 01.01.2025 | Жизненный цикл: контроль и совершенствование | Полный lifecycle-сертификат |

Уже стоящие контуры: ADR-001 (LLM не пишет `summary.passed`); самооценка 72514;
карта 72515; протокол измерения; BOM поставки.

IfcOpenShell / IfcTester — тот же класс IDS, что питает официальный контур
buildingSMART; AeroBIM **не** заменяет [bSI Validation Service](https://technical.buildingsmart.org/services/validation-service/).
См. [`VALIDATION_LAYERS_BSI_IDS_ENGINE_2026.md`](VALIDATION_LAYERS_BSI_IDS_ENGINE_2026.md).

УГТ (готовность): [`TRL_GOST_R_58048_SELF_ASSESS_2026.md`](TRL_GOST_R_58048_SELF_ASSESS_2026.md)
(ГОСТ Р 58048-2017, приказ **2128-ст**). Самооценка **4**, не 5.

Рядом, **не** ГОСТ Р: ПНСТ 841-2023 (приказ **61-пнст**) — карта на протокол
измерения, не оценка соответствия SQuaRE.
[`PNST_841_AI_QUALITY_EVAL_2026.md`](PNST_841_AI_QUALITY_EVAL_2026.md).
