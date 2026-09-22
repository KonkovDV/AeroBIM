#!/usr/bin/env bash
# =============================================================================
# AeroBIM — Universal Demo Setup Script (Linux / macOS)
# =============================================================================
#
# Использование:
#   ./deploy/demo/setup-demo.sh               # авто-выбор режима
#   ./deploy/demo/setup-demo.sh cli           # Режим A: CLI жюри (Python only)
#   ./deploy/demo/setup-demo.sh ui            # Режим B: UI оболочка (Python + Node)
#   ./deploy/demo/setup-demo.sh docker        # Режим C: Docker (API без сборки)
#   ./deploy/demo/setup-demo.sh docker-full   # Режим C+: Docker API + Vite UI
#   ./deploy/demo/setup-demo.sh airgap        # Режим D: air-gap (tar-бандл Docker)
#
# Требования по режимам:
#   cli         — Python 3.12, git clone
#   ui          — Python 3.12, Node 20+, git clone
#   docker      — Docker (Engine ≥ 24) + Docker Compose plugin
#   docker-full — Docker + Node 20+ (Vite запускается на хосте)
#   airgap      — Docker + бандл artifacts/offline-bundle/
# =============================================================================
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

RED='\033[0;31m'; YEL='\033[1;33m'; GRN='\033[0;32m'; CYN='\033[0;36m'; RST='\033[0m'
info()  { echo -e "${CYN}[AeroBIM]${RST} $*"; }
ok()    { echo -e "${GRN}[  OK  ]${RST} $*"; }
warn()  { echo -e "${YEL}[ WARN ]${RST} $*"; }
die()   { echo -e "${RED}[ FAIL ]${RST} $*" >&2; exit 1; }

# -----------------------------------------------------------------------
# Определение режима
# -----------------------------------------------------------------------
MODE="${1:-auto}"

if [[ "$MODE" == "auto" ]]; then
  info "Auto-detecting best demo mode..."
  if command -v docker &>/dev/null && docker info &>/dev/null 2>&1; then
    MODE="docker"
    info "Docker found → using Mode C (docker)"
  elif command -v python3.12 &>/dev/null; then
    if command -v node &>/dev/null; then
      MODE="ui"
      info "Python 3.12 + Node found → using Mode B (ui)"
    else
      MODE="cli"
      info "Python 3.12 found (no Node) → using Mode A (cli)"
    fi
  else
    die "No Docker, no python3.12 found. Install Docker or Python 3.12."
  fi
fi

# -----------------------------------------------------------------------
# Режим A: CLI жюри (только Python 3.12)
# -----------------------------------------------------------------------
if [[ "$MODE" == "cli" ]]; then
  info "Mode A: CLI jury demo (Python 3.12, no Node, no Docker)"
  command -v python3.12 &>/dev/null || die "python3.12 not found. Install CPython 3.12."
  exec "$REPO_ROOT/run-jury.sh"
fi

# -----------------------------------------------------------------------
# Режим B: UI оболочка (Python 3.12 + Node 20+)
# -----------------------------------------------------------------------
if [[ "$MODE" == "ui" ]]; then
  info "Mode B: Review shell demo (Python 3.12 + Node 20+)"
  command -v python3.12 &>/dev/null || die "python3.12 not found. Install CPython 3.12."
  command -v node &>/dev/null      || die "node not found. Install Node 20+."
  NODE_VER=$(node --version | sed 's/v//' | cut -d. -f1)
  [[ "$NODE_VER" -ge 20 ]] || die "Node $NODE_VER found, need 20+. Update Node."

  # Создаём venv, если нет
  if [[ ! -x backend/.venv/bin/python ]]; then
    info "Creating backend/.venv with python3.12 ..."
    python3.12 -m venv backend/.venv
  fi

  # Проверяем версию Python
  if ! backend/.venv/bin/python -c "import sys; raise SystemExit(0 if sys.version_info[:2]==(3,12) else 1)"; then
    die "backend/.venv is not Python 3.12. Delete backend/.venv and re-run."
  fi

  # Устанавливаем зависимости
  info "Installing Python dependencies..."
  export PIP_DISABLE_PIP_VERSION_CHECK=1
  backend/.venv/bin/python -m pip install -q -U pip
  backend/.venv/bin/python -m pip install -q -e "backend/.[dev,raster]"

  # Загрузка env из .env.demo
  if [[ -f .env.demo.local ]]; then
    info "Loading .env.demo.local ..."
    set -a; source .env.demo.local; set +a
  elif [[ -f .env.demo ]]; then
    info "Loading .env.demo ..."
    set -a; source .env.demo; set +a
  fi
  export AEROBIM_ALLOW_ANONYMOUS_DEV=true
  export AEROBIM_SIGNOFF_PROFILE=${AEROBIM_SIGNOFF_PROFILE:-customer_pilot_demo}

  ok "Starting review shell..."
  info "API → http://127.0.0.1:8080   UI → http://127.0.0.1:5173"
  exec backend/.venv/bin/python -m aerobim.tools.run_review_stand
fi

# -----------------------------------------------------------------------
# Режим C: Docker (API)
# -----------------------------------------------------------------------
if [[ "$MODE" == "docker" ]]; then
  info "Mode C: Docker demo (API only, anonymous access)"
  command -v docker &>/dev/null || die "docker not found. Install Docker Desktop or Docker Engine."
  docker info &>/dev/null 2>&1  || die "Docker daemon not running. Start Docker Desktop."
  _dc_cmd=()
  if docker compose version &>/dev/null 2>&1; then
    _dc_cmd=(docker compose)
  elif docker-compose --version &>/dev/null 2>&1; then
    _dc_cmd=(docker-compose)
  else
    die "Docker Compose plugin not found. Install Docker Desktop or compose plugin."
  fi

  info "Building and starting demo backend..."
  "${_dc_cmd[@]}" -f docker-compose.demo.yml up --build -d

  info "Waiting for health check..."
  for i in $(seq 1 30); do
    if curl -sf http://127.0.0.1:8080/health &>/dev/null; then
      ok "API ready: http://127.0.0.1:8080"
      ok "Health:    http://127.0.0.1:8080/health"
      ok "Caps:      http://127.0.0.1:8080/v1/system/capabilities"
      info "API is on 127.0.0.1 only. The anonymous demo API is not published to the LAN."
      info "To stop: docker compose -f docker-compose.demo.yml down"
      info "To reset reports: docker compose -f docker-compose.demo.yml down -v"
      exit 0
    fi
    sleep 2
  done
  die "Health check timed out. Run: docker compose -f docker-compose.demo.yml logs"
fi

# -----------------------------------------------------------------------
# Режим C+: Docker API + Vite UI
# -----------------------------------------------------------------------
if [[ "$MODE" == "docker-full" ]]; then
  info "Mode C+: Docker API + Vite UI on host"
  command -v node &>/dev/null || die "node not found. Install Node 20+ for frontend."
  NODE_VER=$(node --version | sed 's/v//' | cut -d. -f1)
  [[ "$NODE_VER" -ge 20 ]] || die "Node $NODE_VER found, need 20+."

  # Сначала запускаем backend через Docker
  "$0" docker

  cleanup() {
    info "Stopping Vite and the demo container..."
    if [[ -n "${VITE_PID:-}" ]] && kill -0 "$VITE_PID" 2>/dev/null; then
      kill "$VITE_PID" 2>/dev/null || true
      wait "$VITE_PID" 2>/dev/null || true
    fi
    docker compose -f "$REPO_ROOT/docker-compose.demo.yml" down
  }
  trap cleanup INT TERM EXIT

  info "Installing frontend dependencies from the lockfile..."
  cd "$REPO_ROOT/frontend"
  [[ -f package-lock.json ]] || die "frontend/package-lock.json is missing."
  npm ci
  info "Starting Vite frontend... UI → http://127.0.0.1:5173"
  VITE_API_BASE_URL=http://127.0.0.1:8080 npm run dev &
  VITE_PID=$!
  ok "Frontend started (PID $VITE_PID). Ctrl+C stops Vite and the demo container."
  ok "UI  → http://127.0.0.1:5173"
  ok "API → http://127.0.0.1:8080"
  wait "$VITE_PID"
  exit 0
fi

# -----------------------------------------------------------------------
# Режим D: Air-gap (offline bundle)
# -----------------------------------------------------------------------
if [[ "$MODE" == "airgap" ]]; then
  info "Mode D: offline image track. This is not customer_pilot_demo."
  warn "install_offline.sh starts the closed-contour image. It does not set AEROBIM_SIGNOFF_PROFILE=customer_pilot_demo."
  warn "Clash/MEP honesty of the demo profile applies to modes cli, ui, and docker only."
  BUNDLE_DIR="$REPO_ROOT/artifacts/offline-bundle"
  [[ -d "$BUNDLE_DIR" ]] || die "Bundle not found at $BUNDLE_DIR. Run first (online): cd backend && python -m aerobim.tools.offline_bundle build"
  command -v docker &>/dev/null || die "docker not found."
  if [[ -f "$BUNDLE_DIR/install_offline.sh" ]]; then
    info "Running offline installer..."
    cd "$BUNDLE_DIR"
    bash install_offline.sh
  else
    die "install_offline.sh not found in $BUNDLE_DIR. Rebuild the bundle."
  fi
  exit 0
fi

die "Unknown mode '$MODE'. Valid: auto cli ui docker docker-full airgap"
