#!/usr/bin/env bash

set -euo pipefail

APP_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
HOST="127.0.0.1"
PORT="9999"
APP_URL="http://${HOST}:${PORT}"
PID_FILE="${APP_DIR}/.content-manager.pid"
LOG_FILE="${APP_DIR}/content-manager.log"

if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  echo "Python executable not found: ${PYTHON_BIN}" >&2
  exit 1
fi

if ! command -v curl >/dev/null 2>&1; then
  echo "curl is required to check whether the application is live." >&2
  exit 1
fi

is_live() {
  curl --silent --show-error --fail --max-time 2 "${APP_URL}/" >/dev/null 2>&1
}

is_app_pid() {
  local pid="$1"
  local command_line
  local working_directory

  kill -0 "${pid}" 2>/dev/null || return 1
  command_line="$(ps -p "${pid}" -o args= 2>/dev/null || true)"
  working_directory="$(readlink -f "/proc/${pid}/cwd" 2>/dev/null || true)"
  [[ "${command_line}" == *"${APP_DIR}/app.py"* ]] || {
    [[ "${working_directory}" == "${APP_DIR}" && "${command_line}" == *"app.py"* ]]
  }
}

stop_server() {
  local pids=()
  local pid

  if [[ -f "${PID_FILE}" ]]; then
    pid="$(<"${PID_FILE}")"
    if [[ "${pid}" =~ ^[0-9]+$ ]] && is_app_pid "${pid}"; then
      pids+=("${pid}")
    fi
  fi

  if ((${#pids[@]} == 0)); then
    while read -r pid; do
      [[ -n "${pid}" ]] && is_app_pid "${pid}" && pids+=("${pid}")
    done < <(pgrep -f "app.py" || true)
  fi

  for pid in "${pids[@]}"; do
    kill "${pid}" 2>/dev/null || true
  done

  for _ in {1..20}; do
    local running=0
    for pid in "${pids[@]}"; do
      if kill -0 "${pid}" 2>/dev/null; then
        running=1
        break
      fi
    done
    ((running == 0)) && break
    sleep 0.25
  done

  for pid in "${pids[@]}"; do
    if kill -0 "${pid}" 2>/dev/null; then
      kill -KILL "${pid}" 2>/dev/null || true
    fi
  done

  rm -f "${PID_FILE}"
}

case "${1:-}" in
  "") ;;
  --restart)
    stop_server
    ;;
  *)
    echo "Usage: $0 [--restart]" >&2
    exit 2
    ;;
esac

if is_live; then
  echo "Application running at: ${APP_URL}"
  exit 0
fi

cd "${APP_DIR}"
nohup "${PYTHON_BIN}" "${APP_DIR}/app.py" >>"${LOG_FILE}" 2>&1 &
server_pid=$!
echo "${server_pid}" >"${PID_FILE}"

for _ in {1..30}; do
  if is_live; then
    echo "Application running at: ${APP_URL}"
    exit 0
  fi
  if ! kill -0 "${server_pid}" 2>/dev/null; then
    echo "Application failed to start. Check ${LOG_FILE}" >&2
    rm -f "${PID_FILE}"
    exit 1
  fi
  sleep 1
done

echo "Application did not become live within 30 seconds. Check ${LOG_FILE}" >&2
exit 1
