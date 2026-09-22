# AeroBIM — Universal Demo Deployment

> **Честный скоп.** Режим `customer_pilot_demo`: clash/MEP = SKIPPED (не подделывает, не фальсифицирует).
> FAILED-движки блокируют `summary.passed`. LLM-исходящий запрещён.

## Дерево выбора режима

```
У заказчика есть Docker?
├── ДА  →  Режим C: docker        (setup-demo.sh docker)
└── НЕТ
    ├── Есть Python 3.12 + Node 20+?  →  Режим B: ui  (setup-demo.sh ui)
    └── Есть только Python 3.12?     →  Режим A: cli (setup-demo.sh cli)

Закрытая сеть (аир-гэп)?
└── Docker + бандл  →  Режим D: airgap (setup-demo.sh airgap)
```

---

## Режим A — CLI жюри (Python 3.12 only, без Node, без Docker)

**Требуется:** Python 3.12, git.

```bash
# Linux / macOS
./deploy/demo/setup-demo.sh cli
# или напрямую:
./run-jury.sh
```

```bat
rem Windows
deploy\demo\setup-demo.bat cli
rem или напрямую:
run-jury.bat
```

Вывод: CLI-протокол фиксации KT#3 (`summary.passed=false` ожидаемо).

---

## Режим B — UI оболочка (Python 3.12 + Node 20+)

**Требуется:** Python 3.12, Node ≥ 20, git.

```bash
./deploy/demo/setup-demo.sh ui
```

```bat
deploy\demo\setup-demo.bat ui
rem PowerShell:
.\deploy\demo\setup-demo.ps1 -Mode ui
```

Фронтенд: `http://127.0.0.1:5173` · API: `http://127.0.0.1:8080`

---

## Режим C — Docker (API, анонимный доступ)

**Требуется:** Docker Engine ≥ 24 + Compose plugin.

```bash
./deploy/demo/setup-demo.sh docker
# С UI (Node 20+ на хосте):
./deploy/demo/setup-demo.sh docker-full
```

```bat
deploy\demo\setup-demo.bat docker
.\deploy\demo\setup-demo.ps1 -Mode docker-full
```

Вручную:
```bash
docker compose -f docker-compose.demo.yml up --build -d
# проверка:
curl http://127.0.0.1:8080/health
# остановка:
docker compose -f docker-compose.demo.yml down
# полный сброс отчётов:
docker compose -f docker-compose.demo.yml down -v
```

---

## Режим D — Air-gap / закрытый контур (Docker без pip)

**Требуется:** Docker. Бандл собран заранее онлайн.

```bash
# 1. Онлайн (один раз): сборка бандла
cd backend
python -m aerobim.tools.offline_bundle build
python -m aerobim.tools.offline_bundle verify

# 2. Перенос artifacts/offline-bundle/ на хост заказчика
# 3. Установка (air-gap, без интернета):
./deploy/demo/setup-demo.sh airgap
# Windows: .\deploy\demo\setup-demo.ps1 -Mode airgap
```

Подробно: [`docs/offline-deployment-2026.md`](../../docs/offline-deployment-2026.md)

---

## Сброс репортов между сессиями

```bash
# Linux / macOS
./deploy/demo/reset-demo.sh             # venv-режим
./deploy/demo/reset-demo.sh docker      # Docker volume
./deploy/demo/reset-demo.sh all         # всё
```

```bat
rem Windows
deploy\demo\reset-demo.bat docker
```

---

## Смок-тест API

```bash
./deploy/demo/validate-demo.sh
# LAN: ./deploy/demo/validate-demo.sh http://192.168.1.100:8080
```

```bat
deploy\demo\validate-demo.bat
```

---

## Настройки демо

| Переменная | Значение по умолчанию | Описание |
|---|---|---|
| `AEROBIM_SIGNOFF_PROFILE` | `customer_pilot_demo` | `moscow_agr_2026` — для акцента на АГР |
| `AEROBIM_ALLOW_ANONYMOUS_DEV` | `true` | отключить + задать `AEROBIM_API_BEARER_TOKEN` |
| `AEROBIM_REMARK_LOCALE` | `ru` | `en` — для замечаний на английском |
| `AEROBIM_CORS_ORIGINS` | `http://localhost:5173,...` | Добавь IP, если демо по LAN |
| `AEROBIM_HOST` | `127.0.0.1` | `0.0.0.0` — если демо по LAN |

Копируйте `.env.demo` → `.env.demo.local` и правьте переменные. Файл `.env.demo.local` в `.gitignore`.

---

## Честность показа в демо

- `summary.passed=false` на учебном комплекте — **ожидаемо** (посажены дефекты)
- SKIPPED в capabilities — честный out-of-scope (не подделъвает)
- `customer_go = false` — пилот ещё не завершён
- LLM не пишет `summary.passed` никогда

---

Подробное руководство со всеми сценариями, troubleshooting и LAN-конфигурацией:
[`docs/demo-deployment-2026.md`](../../docs/demo-deployment-2026.md)
