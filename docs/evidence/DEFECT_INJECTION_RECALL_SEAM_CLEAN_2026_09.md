<!-- claims-lint: allow-file reason="Injection recall run; synthetic mutation test; GO; customer_go false" -->
---
title: "Defect-injection recall run — mutation-kill, synthetic-only"
date: "2026-09-22"
last_updated: "2026-09-22"
status: active
version: "1.0.0"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_boundary: >
  Mutation-kill recall on injected synthetics. Output-sensitivity
  proxy, not semantic defect confirmation. Not appointing-party accuracy.
  Not product accuracy. Checkpoint GO (regulatory_measurement_mvp; customer_go false).
---

# Recall на инъекциях — прогон E2 (синтетика, не партнёр)

- Источник: `wall_fire_rating_rei60_seam_clean`.
- Seed: **20260915** · коммит: `4cf35e91adfb307491045e96e89b03b275c5b956`
- Манифест sha256: `8793de98dec2c457614fedf3aecc9b905c21012c83432eab9b4f861f65e357b7`
- Детерминизм (source ≡ CONTROL): **pass**

## Отклонение от плана 2026-08-30

План требовал шовно-чистый пакет с `summary.passed=true`. По команде
дорожной карты 2026-09-03 источник — канальный IFC (дерево владельца;
режим данных не согласован; не публикуется), который
чистым не является; атрибуция — через CONTROL-дифф мультимножеств находок.
Recall на синтетике **не** переносится на комплект заказчика.

## По классам инъекций

| Класс | Инъекция | Новых находок | Исчезнувших | Мутант убит |
|---|---|---|---|---|
| IDS_FIRE_REI45 | да | 1 | 0 | да |
| IDS_FIRE_REI30 | да | 1 | 0 | да |
| IDS_FIRE_REI90 | да | 1 | 0 | да |
| IDS_FIRE_REI15 | да | 1 | 0 | да |
| IDS_FIRE_EI60 | да | 1 | 0 | да |
| IDS_FIRE_REI120 | да | 1 | 0 | да |
| IDS_PSET_UNLINK | да | 1 | 0 | да |
| IDS_CLASS_SWAP | да | 1 | 0 | да |
| IDS_PROP_RENAME | да | 1 | 0 | да |
| IDS_WALL_REMOVED | да | 1 | 0 | да |

## Итог

- Mutation-kill recall: **10/10** (точечно 1.000)
- Wilson 95%: [0.722; 1.000] — публикуется **нижняя** граница 0.722
- База CONTROL: 0 находок до инъекций

Граница: прокси — чувствительность выхода контура, не семантическое
подтверждение дефекта. `claim_level=synthetic_only`. Checkpoint GO (regulatory_measurement_mvp; customer_go false).
RT-001/002/003 остаются OPEN.
