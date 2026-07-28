---
title: "AeroBIM Hybrid AI — Research Review (2026-07-28)"
status: active
version: "1.0.0"
last_updated: "2026-07-28"
claim_boundary: "Applicability review. Preprints are not standards. No product claims. Checkpoint NO_GO."
tags: [aerobim, hybrid-ai, research, routing, privacy]
---

# Hybrid AI — обзор мировых подходов и применимость

Companion к `HYBRID_AI_ARCHITECTURE_2026_07_28.md`. **Честная оговорка:** препринт ≠
промышленный стандарт; эксперимент на синтетике ≠ доказательство защищённости
AeroBIM. Ниже разделены **проверенные стандарты** и **концепт-подходы из брифа**,
чьи первоисточники нужно верифицировать перед цитированием в акт/публикацию.

## 1. Проверяемые стандарты (можно ссылаться)

| Источник | Тип | Что переносим в AeroBIM |
|---|---|---|
| **NIST AI RMF** (Govern/Map/Measure/Manage) | стандарт | структура управления рисками контура; Map=классификация, Measure=harness, Manage=fail-closed policy |
| **NIST Generative AI Profile** | стандарт | профиль рисков генеративных моделей → egress/маскирование/HITL |
| **OWASP Top-10 for LLM Apps (2025)** | стандарт-обзор | LLM01 (prompt injection), LLM02 (data leakage), LLM07 (мониторинг) → уже отражено в grounding/schema-guard/observability |
| **OWASP риски агентных систем/утечки** | обзор | «модель не выбирает инструменты/маршрут»; server-tools off |
| Zhan et al., NAACL 2025 Findings (adaptive attacks) | публикация (веб-подтв.) | layered defense; детектировать инъекции, не только блокировать |

## 2. Концепт-подходы из брифа (первоисточник верифицировать; НЕ цитировать как доказанное)

Для каждого — задача → применимость к AeroBIM → что НЕЛЬЗЯ переносить без доказательства.

| Подход | Идея (по брифу) | Применимость к AeroBIM | Ограничение |
|---|---|---|---|
| ComplianceGate | classifier-gated multi-tier routing для регулируемых отраслей | прямой аналог нашего class×route policy engine (Wave 2) | классификатор нельзя делать LLM-only; fail-closed обязателен |
| PRISM | privacy-aware routing cloud↔edge | вход для Model Router (P2) | не переносить метрики приватности без наших тестов re-id |
| SplitAgent | приватный локальный + облачный reasoning-агент | локальный guardrail + advisory-only внешний | агент не владеет вердиктом |
| Privacy-R1 | privacy-aware collaboration моделей | HITL + маскирование | не «анонимность гарантирована» |
| TrustedARI | доверенная инфра маршрутизации + проверка провайдера | provider allowlist + audit провайдера (P2) | требует реального attestation — не заявлять |
| STREAM | локально/HPC/облако многоуровневое исполнение | профили маршрутов (P2) | не для CONFIDENTIAL наружу |
| PPRoute | privacy-preserving маршрутизация | вход policy engine | эксперимент ≠ гарантия |
| SS-ZKR | семантическая маршрутизация между зонами доверия | классификация→зона→маршрут | ZK — P3, не начинать до P0 |
| CoTrust | большая+малая модель в доверенной среде | local_vlm + private_vlm | доверенная среда требует TEE (P3) |
| AgenTEE | конфиденциальные агентные задачи на периферии | P3 (TEE) | не начинать до P0 |
| Bifrost | гибрид TEE/FHE | P3 | вычислительно тяжело; не для пилота |

## 3. Применимость к типам данных AeroBIM

- **IFC/чертежи/расчёты (CONFIDENTIAL/RESTRICTED):** только local/private; наружу —
  максимум region-crop/OCR/нормализованный признак после маскирования; целый лист/
  комплект — никогда.
- **PDF/OCR-текст:** локальный OCR предпочтителен; внешний только для PUBLIC/обезличенного.
- **Нормопаки:** утверждённые — RESTRICTED (RT-002); внешний вывод запрещён.
- **Ответ модели:** всегда кандидатное наблюдение, строгая схема, вердикт — движок.

## 4. Итог

Наиболее зрелое для немедленного переноса — **NIST AI RMF-структура + OWASP-контроли
+ classifier-gated fail-closed routing** (ComplianceGate-класс). TEE/FHE/MPC/ZK
(Bifrost/AgenTEE/SS-ZKR) — **P3**, не начинать до подтверждённого P0. Никакой из
подходов **не** снимает RT-001/002/003 и **не** делает публичный API безопасным для
customer data. **Checkpoint = NO_GO.**
