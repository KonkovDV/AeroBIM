# Sprint 2.1 claims boundary

**Date:** 2026-07-31  
**HEAD at authoring:** see `audit/sprint-2-1-start-state.json`  
**Checkpoint:** `NO_GO` (RT-001/002/003 open)

## Allowed

- Проведён инженерный baseline на public/synthetic package.
- Результаты воспроизводимы на заявленном commit и manifest.
- Система фиксирует deterministic findings и capability statuses.
- LLM используется только как advisory layer.
- Сравнение моделей проводится на synthetic/public сценариях (mock/contract в CI).

## Forbidden

- точность продукта выше 90%
- подтверждено на реальных проектах Самолёта
- SLA ≤30 минут для любого комплекта
- полная проверка проектной документации
- проверка корректности расчётов
- готовая интеграция с CDE
- LLM понимает чертёж как инженер
- облачный API безопасен для customer data
- заказчики заинтересованы, если контакта не было

## Status labels for Sprint metrics

| Label | Meaning |
|---|---|
| fixture/synthetic | measured on declared pack |
| not customer | must not be sold as customer SLA |
| blocked | needs external customer/license/API |
| PDF_GENERATION_BLOCKED | no PDF toolchain in this run |
