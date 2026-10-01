<!-- claims-lint: allow-file reason="Validation layers: bSI file vs IDS vs engine; compatibility is not replacement; NO_GO" -->
---
title: "Validation layers — bSI file vs IDS vs engine"
date: "2026-08-28"
last_updated: "2026-08-28"
status: active
version: "1.0.0"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_boundary: >
  One-page responsibility split. Compatibility with the bSI Validation
  Service is not replacement and not certification. Checkpoint GO; customer_go false.
---

# Слои проверки: файл, требования, инженерное содержание

**Совместимость не замена.** **Совместимость не сертификация.** AeroBIM не
заменяет [bSI Validation Service](https://technical.buildingsmart.org/services/validation-service/)
и не является сертификацией buildingSMART.

## Три слоя

| Слой | Кто | Что решает | Что не решает |
|------|-----|------------|----------------|
| Файл / схема IFC | bSI Validation Service (или локальный schema pre-gate) | STEP-синтаксис, схема EXPRESS, нормативные правила IFC | Проектные, национальные, организационные правила |
| Information requirements | IDS 1.0 (финал 2024-06-01), у нас IfcTester | Назначенные свойства/сущности по контракту информации | Инженерную сверку по существу нормы/СТО |
| Engineering content | AeroBIM (детерминированный движок + advisory) | Сверка комплекта: IDS + свойства + листы + тексты + шаблонные нормы | Вердикт эксперта; `summary.passed` от LLM (ADR-001) |

Цитата мандата bSI (technical page, «What is not being checked?»): the IFC
Validation Service **does not check project-specific, national-specific, organization-specific**
rules or constraints. Case-specific validation is
where the mandate of the bSI Validation Service ends — and where other
solutions like IDS can help.

IDS — Information Delivery Specification: контракт информации, не замена
нормоконтроля. Движок AeroBIM читает IDS и пакеты правил; это не «лучше рынка»
и не замена зарубежного schema-валидатора.

## Ворота находки (аналог, не точность)

Группировка schema / quality / regulatory в отчёте — аналогия стадий
[CORENET X Model Checker](https://info.corenet.gov.sg/overview/corenet-x-submission-portal/model-checker)
(IFC Schema Check → Quality Check → Regulatory Compliance Check). Счётчики
ворот — не точность продукта и не 90%. Детерминированные строки — предикаты
движка. Вероятностные — `origin=advisory` и не пишут `summary.passed`.

## Запрещено

- AeroBIM replaces the bSI Validation Service
- заменяем валидатор buildingSMART
- точность >90%
- Checkpoint GO
- production-ready

Checkpoint **GO**; customer_go false.
