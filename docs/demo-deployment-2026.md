# Demo Deployment Guide (2026)

> **Claim level:** Engineering runbook. Not a pilot result, not a customer sign-off claim.
> `customer_go` remains **false**. `AEROBIM_SIGNOFF_PROFILE=customer_pilot_demo` is an
> honest-scope contour: clash/MEP stay `SKIPPED`, never faked. FAILED engines still block
> `summary.passed`. LLM egress is denied. This is `Checkpoint GO` (`regulatory_measurement_mvp`),
> not customer acceptance.

---

## Быстрый старт (авто-выбор)

```bash
# Linux / macOS
./deploy/demo/setup-demo.sh

# Windows CMD / Explorer
deploy\demo\setup-demo.bat

# PowerShell
.\deploy\demo\setup-demo.ps1
```

Скрипт автоматически определяет лучший режим: Docker → UI → CLI.

---

## Дерево выбора режима

| Режим | Что нужно | Что показывает | Команда |
|---|---|---|---|
| **A — CLI жюри** | Python 3.12 | Терминал: находки, BCF | `setup-demo.sh cli` |
| **B — UI оболочка** | Python 3.12 + Node 20+ | Браузер: 3D, лист, HITL | `setup-demo.sh ui` |
| **C — Docker API** | Docker ≥ 24 | API + samples | `setup-demo.sh docker` |
| **C+ — Docker+UI** | Docker + Node 20+ | Браузер полный стек | `setup-demo.sh docker-full` |
| **D — Air-gap** | Docker + бандл | API offline | `setup-demo.sh airgap` |

---

## Режим A: CLI жюри

### Требования
- Python 3.12 (из [python.org](https://www.python.org/), не Microsoft Store)
- git clone

### Windows
```bat
git clone https://github.com/KonkovDV/AeroBIM.git
cd AeroBIM
run-jury.bat
```

### Linux / macOS
```bash
git clone https://github.com/KonkovDV/AeroBIM.git
cd AeroBIM
./run-jury.sh
```

### Ожидаемый результат
`summary.passed=false` — норма. Учебный комплект содержит посаженные дефекты.

### Troubleshooting A
| Проблема | Решение |
|---|---|
| `py -3.12 not found` | Скачайте CPython 3.12 с python.org, не из Microsoft Store |
| `IfcOpenShell import error` (Windows) | Установите Microsoft VC++ 2015-2022 x64 Redistributable |
| `No module named aerobim` | Запускайте из корня, не из `backend/`. Используйте `run-jury.bat`, не `python -m aerobim` системный python |
| Предупреждения в pip | Не стопают запуск. Ошибка exit 2 станавливает |
| Кириллица в пути (Windows) | Положите клон в `C:\AeroBIM` |
| Диагностика | `.\check-launch.bat` (Windows) / `./check-launch.sh` (Linux/macOS) |

---

## Режим B: UI оболочка

### Требования
- Python 3.12
- Node 20+, npm
- venv уже создан (run-jury.bat/sh должен быть запущен хотя бы один раз)

### Windows
```bat
rem Шаг 1: создаём venv
run-jury.bat

rem Шаг 2: запуск UI оболочки (PowerShell: .\start.bat, Explorer: двойной щелчок start.bat)
start.bat
```

### Linux / macOS
```bash
# Шаг 1 (venv)
./run-jury.sh
# Шаг 2
./start.sh
```

### Или одной командой
```bash
./deploy/demo/setup-demo.sh ui
```

API: `http://127.0.0.1:8080` · UI: `http://127.0.0.1:5173`

### Troubleshooting B
| Проблема | Решение |
|---|---|
| `backend/.venv not found` | Сначала запустите `run-jury.bat/sh` |
| Порт 8080 занят | Остановите предыдущий `start.bat` / `aerobim-backend` Docker и запустите снова |
| `npm` не найден | Установите [Node.js 20 LTS](https://nodejs.org/) |
| CORS-ошибки | `AEROBIM_CORS_ORIGINS` должен включать адрес Vite |

---

## Режим C: Docker

### Требования
- Docker Engine ≥ 24 или Docker Desktop
- Docker Compose plugin (v2: `docker compose`)

### Одной командой
```bash
./deploy/demo/setup-demo.sh docker
```

### Вручную
```bash
# Сборка и запуск
# (--build можно опустить после первого запуска)
docker compose -f docker-compose.demo.yml up --build -d

# Проверка
curl http://127.0.0.1:8080/health
curl http://127.0.0.1:8080/v1/system/capabilities

# Логи
docker compose -f docker-compose.demo.yml logs -f

# Остановка
docker compose -f docker-compose.demo.yml down

# Полный сброс (удаление отчётов)
docker compose -f docker-compose.demo.yml down -v
```

### Добавление UI (Vite на хосте)
```bash
./deploy/demo/setup-demo.sh docker-full
# или вручную:
cd frontend && npm install && VITE_API_BASE_URL=http://127.0.0.1:8080 npm run dev
```

### Windows
```bat
deploy\demo\setup-demo.bat docker
rem PowerShell:
.\deploy\demo\setup-demo.ps1 -Mode docker
.\deploy\demo\setup-demo.ps1 -Mode docker-full
```

### Troubleshooting C
| Проблема | Решение |
|---|---|
| `Cannot connect to Docker daemon` | Запустите Docker Desktop |
| `port is already allocated` | `docker compose -f docker-compose.demo.yml down` и повторите |
| `volume is in use` | `docker compose -f docker-compose.demo.yml down -v` |
| `permission denied /data/reports` | `docker compose -f docker-compose.demo.yml down -v` (удаляет volume) |
| `docker-compose: command not found` | Используйте `docker compose` (v2 plugin) |

---

## Режим C-LAN: демо по сети для нескольких участников

Измените в `docker-compose.demo.yml` или через `.env.demo.local`:

```bash
# Создайте .env.demo.local (he в git):
cat > .env.demo.local << 'EOF'
AEROBIM_HOST=0.0.0.0
AEROBIM_CORS_ORIGINS=http://192.168.1.100:5173,http://192.168.1.100:8080
AEROBIM_ALLOW_ANONYMOUS_DEV=true
AEROBIM_SIGNOFF_PROFILE=customer_pilot_demo
EOF

# Измените ports в docker-compose.demo.yml:
# ports:
#   - "0.0.0.0:8080:8080"   # <-- вместо 127.0.0.1:8080:8080

docker compose -f docker-compose.demo.yml up --build -d
```

Убедитесь, что firewall открывает порт 8080.

---

## Режим D: Air-gap / закрытый контур

Подробно: [`docs/offline-deployment-2026.md`](offline-deployment-2026.md)

### Подготовка (online, один раз)
```bash
cd backend
python -m aerobim.tools.offline_bundle build
python -m aerobim.tools.offline_bundle verify
python -m aerobim.tools.offline_bundle smoke
```

Бандл: `artifacts/offline-bundle/` (содержит tar, SBOM, `install_offline.sh`, `install_offline.ps1`).

### Установка (air-gap)
```bash
# Linux / macOS
cp -r artifacts/offline-bundle/ /path/to/airgap/host/bundle/
# на закрытом хосте:
bash bundle/install_offline.sh

# Windows
# Перенесите artifacts/offline-bundle/ на USB / SMB
powershell -ExecutionPolicy Bypass -File bundle\install_offline.ps1

# Или через setup-demo:
./deploy/demo/setup-demo.sh airgap
```

### Ограничения air-gap
- Без Docker air-gap не работает (bare-metal wheelhouse OUT_OF_SCOPE)
- LLM/VLM оффлайн — недоступны (запрещено по умолчанию)
- Redis недоступен в single-container air-gap (опциональная очередь не включается)

---

## Сброс демо между сессиями

```bash
# venv-режим (A/B)
./deploy/demo/reset-demo.sh

# Docker-режим (C)
./deploy/demo/reset-demo.sh docker
# или вручную:
docker compose -f docker-compose.demo.yml down -v

# Всё
./deploy/demo/reset-demo.sh all
```

Windows: `deploy\demo\reset-demo.bat [venv|docker|all]`

---

## Смок-тест API

```bash
./deploy/demo/validate-demo.sh
# LAN:
./deploy/demo/validate-demo.sh http://192.168.1.100:8080
```

Windows: `deploy\demo\validate-demo.bat`

Проверяет: `/health`, `/v1/system/capabilities`, `/v1/reports`.

---

## Ключевые переменные демо

| Переменная | Значение демо | Примечание |
|---|---|---|
| `AEROBIM_SIGNOFF_PROFILE` | `customer_pilot_demo` | `moscow_agr_2026` — акцент Москвы |
| `AEROBIM_ENV` | `development` | Не менять на `production` для демо |
| `AEROBIM_ALLOW_ANONYMOUS_DEV` | `true` | Только `development`. Для защищённого демо убрать + `AEROBIM_API_BEARER_TOKEN` |
| `AEROBIM_REMARK_LOCALE` | `ru` | `en` — замечания на английском |
| `AEROBIM_CORS_ORIGINS` | `http://localhost:5173,...` | Добавь IP для LAN |
| `AEROBIM_HOST` | `127.0.0.1` | `0.0.0.0` — для LAN |
| `AEROBIM_PDF_BACKEND` | `pdfium` | Не менять для демо |
| `AEROBIM_LLM_ADVISORY_ENABLED` | `false` | Запрещено на `customer_pilot*` |
| `AEROBIM_STORAGE_DIR` | `var/reports` | Для Docker — `/data/reports` (volume) |

Полная таблица переменных: `README.md` (`AEROBIM_*` section).

---

## Настройка .env.demo.local

```bash
cp .env.demo .env.demo.local
# Отредактируйте .env.demo.local:
# AEROBIM_SIGNOFF_PROFILE=customer_pilot_demo  # или moscow_agr_2026
# AEROBIM_HOST=0.0.0.0                         # для LAN
# AEROBIM_CORS_ORIGINS=http://192.168.1.100:5173
```

`.env.demo.local` — в `.gitignore`, не коммитить.

---

## Честность показа

| Сценарий | Сказать заказчику |
|---|---|
| `summary.passed=false` на учебном комплекте | Цень — программа нашла посаженные дефекты |
| SKIPPED в capabilities | Честный out-of-scope: clash/MEP не подделывает |
| FAILED блокирует `summary.passed` | Детерминированное ядро, LLM не пишет флаг |
| `customer_go = false` | Пилот не завершён |
| Логи BCF | `GET /v1/reports/{id}/export/bcf` / `?version=3` |

---

## Сценарии демо-дня (7 кадров)

Сценарий из `submission/03-presentation/demo_day_slides.md`.

| Кадр | Что запустить | Команда |
|---|---|---|
| 3 | Цифры (0,86 / 10/10 / 1/8) | `python -m aerobim.tools.run_kt3_jury` |
| 4 | Узел 30/40 мм → BCF | То же — `summary.passed=false` | 
| 4+ | IFC acceptance gate | `python -m aerobim.tools.run_demo_ifc_acceptance_gate` |
| 4+ | Vertical slice | `python -m aerobim.tools.run_demo_vertical_slice` |
| UI | 3D-модель + превью листа | Режим B или C+ |

---

## Ограничения demo-режимов

- `customer_pilot_demo` и `moscow_agr_2026` — `development`/`test` only
- Не запускайте `AEROBIM_SIGNOFF_PROFILE=customer_pilot` / `production` на первом клоне
- Анонимный API `AEROBIM_ALLOW_ANONYMOUS_DEV=true` работает только в `ENV=development`
- LLM-исходящий запрещён (`AEROBIM_CUSTOMER_PACK_LLM_EGRESS=deny`)
- `requirements-lock.txt` — Linux/CI lock, на Windows не ставить

---

## Связанные документы

| Документ | Описание |
|---|---|
| [`docs/offline-deployment-2026.md`](offline-deployment-2026.md) | Air-gap Docker (и1 CLOSED) |
| [`deploy/demo/README.md`](../deploy/demo/README.md) | Быстрый гайд / дерево выбора |
| [`backend/.env.example`](../backend/.env.example) | Полная таблица переменных |
| [`README.md`](../README.md) | Try it / Configuration / HTTP API |
| [`frontend/README.md`](../frontend/README.md) | Настройка фронтенда |
| [`docs/pilot-claim-boundary-2026.md`](pilot-claim-boundary-2026.md) | Граница заявлений |
| [`docs/architecture/ADR-001-verdict-ownership-2026.md`](architecture/ADR-001-verdict-ownership-2026.md) | Почему LLM не пишет summary.passed |
