---
title: "AeroBIM — что чинить после HD-аудита"
status: active
version: "1.1.0"
last_updated: "2026-08-16"
claim_boundary: "Engineering backlog only. Checkpoint NO_GO until RT-001/002/003."
---

# План доработки (16.08)

NO_GO не снимаем. Самолёту по-прежнему нужны корпус ПД, подписанный профиль и живой MEP-clash — это не закрывается кодом.

## Сделано в этой волне

Швы, из-за которых система выглядела бы дураком на внешнем разборе: 429 без заголовков, IDS/`status` по умолчанию «прошла», clash, который глотал кривые записи, вечный кэш IFC, JWKS без refetch, DI без lock, квота после записи на диск, XFF со всех подряд, cookie BFF как principal.

Добивка сегодня:

- квота: hold-файл на reserve; через час брошенный hold откатывается;
- JWKS: неизвестный `kid` не дёргает IdP чаще чем раз в 30 с;
- XFF: в бакет попадает только валидный IP;
- IDS: проход спеки только при `status is True` (строка `"failed"` больше не выглядит как успех);
- clash без GUID — ошибка движка, не пустой вердикт.

## Не трогаем кодом

RT-001 / RT-002 / RT-003. Postgres DDL в рантайме — нормально для пилота, перед продом вынести в миграции. Redis и in-process лимитеры считают окна по-разному — так и написано. BFF-сессии в памяти, пока phase 3 не INCLUDE.

## Git

HD close-out: `4b410c9` on `origin/main`. This remaining-work note is not the dataset contour. Dataset hunt / PNST CLI / IFC-Bench 27/1026 / Ishigaki processability land in a separate commit.
