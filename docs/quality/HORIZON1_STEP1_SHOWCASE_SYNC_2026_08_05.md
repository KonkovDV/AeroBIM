# Horizon 1 / Step 1 — синхронизация витрины (2026-08-05)

**Горизонт:** 1 (до КТ#2, 20.08).  
**Статус шага:** выполнен со стороны репозитория; резерв `.local` вне рабочего диска — **у владельца**.

## Чеклист 1.4

| Пункт | Статус | Основание |
|---|---|---|
| Exp B (КР/АР/ВК) + baseline PDF + ENGINEERING_STATUS + PRESS registry | на `origin/main` до этого шага | `698998d` и предшествующие |
| Публичный `qa-defense` без имён конкурентов задачи | на `origin/main` | Red Team Friday pack |
| `.local/` не в git | 0 tracked | `git ls-files .local` |
| Резерв `.local` на том же томе `C:` | есть копия | `C:\plans\_aerobim_local_backup_2026-08-05` (~4813 files) — **не** защита от отказа диска |
| CI: README ↔ baseline (LOC/tests) | уже в CI | `--check-readme --check-complete` |
| CI: множество имён env EN↔RU↔Configuration↔baseline | добавлено | `documented_env_vars` + маркеры `AEROBIM_DOCUMENTED_ENV` |
| `CRITICAL_BLOCKERS` — `СТАТУС: ЗАКРЫТО` у закрытых секций | уже | remediation banners |
| `docs/docs.md` | v1.2, 05.08.2026 | календарь КТ#2/#3/финал; «Новатор» 2026 закрыт |
| README порядок: пример → работает → где → NO_GO RU → глубина | сделано | `README.ru.md` / `README.md` |

## ТРЕБУЕТСЯ ОТ ВЛАДЕЛЬЦА

1. Скопировать `.local/` на **USB / другой диск / частный репозиторий** (копия на `C:\plans\_aerobim_local_backup_*` недостаточна при отказе диска C:).
2. Не публиковать `.local` (воронка, Segment E имена, внутренний qa-defense с конкурентами).
3. После пятницы — операторский intro для Segment E (только через аккаунт-менеджера).
