#!/usr/bin/env bash
# =============================================================================
# AeroBIM -- Demo Validation / Smoke Test (Linux / macOS)
# Проверяет ключевые эндпойнты запущенного демо.
# =============================================================================
# Использование:
#   ./deploy/demo/validate-demo.sh
#   ./deploy/demo/validate-demo.sh http://192.168.1.100:8080   # по LAN
# =============================================================================
set -euo pipefail

BASE_URL="${1:-http://127.0.0.1:8080}"
RED='\033[0;31m'; GRN='\033[0;32m'; CYN='\033[0;36m'; RST='\033[0m'
info()  { echo -e "${CYN}[validate]${RST} $*"; }
pass()  { echo -e "${GRN}[ PASS ]${RST} $*"; }
fail()  { echo -e "${RED}[ FAIL ]${RST} $*"; FAILURES=$((FAILURES+1)); }

FAILURES=0

check() {
  local label="$1" url="$2" expected_code="${3:-200}"
  local code
  code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 "$url" 2>/dev/null || echo 000)
  if [[ "$code" == "$expected_code" ]]; then
    pass "$label ($code)"
  else
    fail "$label — expected HTTP $expected_code, got $code  [$url]"
  fi
}

check_json() {
  local label="$1" url="$2" field="$3"
  local body
  body=$(curl -sf --max-time 5 "$url" 2>/dev/null || echo '{}')
  if echo "$body" | python3 -c "import sys,json; d=json.load(sys.stdin); raise SystemExit(0 if '$field' in str(d) else 1)" 2>/dev/null; then
    pass "$label (field '$field' present)"
  else
    fail "$label — field '$field' missing  [$url]"
  fi
}

info "Smoke-testing AeroBIM demo at $BASE_URL"
echo

# 1. Health
check "/health" "$BASE_URL/health" 200

# 2. Capabilities
check "/v1/system/capabilities" "$BASE_URL/v1/system/capabilities" 200
check_json "capabilities.env" "$BASE_URL/v1/system/capabilities" "env"
check_json "capabilities.signoff_profile" "$BASE_URL/v1/system/capabilities" "signoff_profile"

# 3. Auth gate (without token, anonymous dev)
check "/v1/auth/bff (501 expected without SSO)" "$BASE_URL/v1/auth/bff" 501

# 4. Reports list
check "/v1/reports" "$BASE_URL/v1/reports" 200

echo
if [[ $FAILURES -eq 0 ]]; then
  echo -e "${GRN}All checks passed. Demo API is healthy.${RST}"
  exit 0
else
  echo -e "${RED}$FAILURES check(s) FAILED. See messages above.${RST}"
  exit 1
fi
