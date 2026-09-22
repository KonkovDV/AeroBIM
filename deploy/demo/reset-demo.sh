#!/usr/bin/env bash
# =============================================================================
# AeroBIM -- Demo Reset Script (Linux / macOS)
# Сбрасывает отчёты для чистого старта между демо-сессиями.
# =============================================================================
# Использование:
#   ./deploy/demo/reset-demo.sh           # сброс venv-режима (var/reports)
#   ./deploy/demo/reset-demo.sh docker    # сброс Docker-режима (volume)
#   ./deploy/demo/reset-demo.sh all       # сброс всего (venv + docker)
# =============================================================================
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

RED='\033[0;31m'; YEL='\033[1;33m'; GRN='\033[0;32m'; CYN='\033[0;36m'; RST='\033[0m'
info() { echo -e "${CYN}[AeroBIM reset]${RST} $*"; }
ok()   { echo -e "${GRN}[  OK  ]${RST} $*"; }
die()  { echo -e "${RED}[ FAIL ]${RST} $*" >&2; exit 1; }

MODE="${1:-venv}"

reset_venv() {
  info "Resetting venv-mode reports (backend/var/reports)..."
  TARGET="$REPO_ROOT/backend/var/reports"
  if [[ -d "$TARGET" ]]; then
    rm -rf "${TARGET:?}"/*
    ok "Cleared: $TARGET"
  else
    info "Nothing to clear (dir not found)."
  fi
}

reset_docker() {
  info "Resetting Docker-mode reports (volume aerobim_demo_reports)..."
  command -v docker &>/dev/null || die "docker not found."
  # Останавливаем stack, удаляем volume, стартуем снова
  if docker compose -f docker-compose.demo.yml ps --quiet 2>/dev/null | grep -q .; then
    info "Stopping demo stack..."
    docker compose -f docker-compose.demo.yml down
  fi
  if docker volume ls --format '{{.Name}}' | grep -q 'aerobim_demo_reports'; then
    docker volume rm aerobim_demo_reports
    ok "Volume aerobim_demo_reports removed."
  else
    info "Volume aerobim_demo_reports not found — nothing to remove."
  fi
}

case "$MODE" in
  venv)   reset_venv ;;
  docker) reset_docker ;;
  all)    reset_venv; reset_docker ;;
  *) die "Unknown mode '$MODE'. Use: venv docker all" ;;
esac

ok "Demo reset complete. Run setup-demo.sh to start a fresh demo."
