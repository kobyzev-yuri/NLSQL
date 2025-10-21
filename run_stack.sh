#!/usr/bin/env bash
set -euo pipefail

# Simple process manager for NL→SQL stack
# Services:
#  - Core API           : 8000 (src/api/main.py)
#  - Mock Customer API  : 8080 (src/mock_customer_api.py)
#  - Simple Web (UI)    : 3000 (src/simple_web_interface.py)
#  - Streamlit UI       : 8501 (src/streamlit_app.py)

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$REPO_DIR/logs"
PID_DIR="$REPO_DIR/.pids"
PYTHONPATH="$REPO_DIR"

mkdir -p "$LOG_DIR" "$PID_DIR"

export PYTHONPATH

svc_start() {
  local name="$1" cmd="$2" port="$3"
  local out="$LOG_DIR/${name}_${port}.out" err="$LOG_DIR/${name}_${port}.err" pidf="$PID_DIR/${name}_${port}.pid"
  if [ -f "$pidf" ] && kill -0 "$(cat "$pidf")" 2>/dev/null; then
    echo "[skip] $name already running on :$port (pid $(cat "$pidf"))"
    return 0
  fi
  echo "[start] $name on :$port"
  nohup bash -lc "$cmd" > "$out" 2> "$err" &
  echo $! > "$pidf"
  sleep 0.5
}

svc_stop() {
  local name="$1" port="$2"
  local pidf="$PID_DIR/${name}_${port}.pid"
  if [ -f "$pidf" ]; then
    local pid
    pid=$(cat "$pidf")
    if kill -0 "$pid" 2>/dev/null; then
      echo "[stop] $name (pid $pid)"
      kill "$pid" || true
      sleep 0.5 || true
    fi
    rm -f "$pidf"
  else
    echo "[skip] $name not running"
  fi
}

svc_status() {
  local name="$1" port="$2"
  local pidf="$PID_DIR/${name}_${port}.pid"
  if [ -f "$pidf" ] && kill -0 "$(cat "$pidf")" 2>/dev/null; then
    echo "[up]   $name on :$port (pid $(cat "$pidf"))"
  else
    echo "[down] $name on :$port"
  fi
}

start_all() {
  svc_start core_api "uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload" 8000
  svc_start mock_api "uvicorn src.mock_customer_api:mock_app --host 0.0.0.0 --port 8080 --reload" 8080
  svc_start simple_ui "uvicorn src.simple_web_interface:app --host 0.0.0.0 --port 3000 --reload" 3000
  svc_start streamlit "streamlit run src/streamlit_app.py --server.port 8501 --server.address 0.0.0.0" 8501
}

stop_all() {
  svc_stop streamlit 8501
  svc_stop simple_ui 3000
  svc_stop mock_api 8080
  svc_stop core_api 8000
}

status_all() {
  svc_status core_api 8000
  svc_status mock_api 8080
  svc_status simple_ui 3000
  svc_status streamlit 8501
}

logs_tail() {
  local name="$1" port="$2" lines="${3:-200}"
  local out="$LOG_DIR/${name}_${port}.out" err="$LOG_DIR/${name}_${port}.err"
  echo "===== $name :$port stdout (last $lines) ====="; tail -n "$lines" "$out" 2>/dev/null || true
  echo "===== $name :$port stderr (last $lines) ====="; tail -n "$lines" "$err" 2>/dev/null || true
}

case "${1:-}" in
  start)
    start_all ;;
  stop)
    stop_all ;;
  restart)
    stop_all; start_all ;;
  status)
    status_all ;;
  logs)
    logs_tail core_api 8000 200
    logs_tail mock_api 8080 200
    logs_tail simple_ui 3000 200
    logs_tail streamlit 8501 200 ;;
  *)
    cat <<USAGE
Usage: $(basename "$0") <start|stop|restart|status|logs>
  start    start all services in background (logs in $LOG_DIR)
  stop     stop all services
  restart  restart all services
  status   show status of services
  logs     tail last lines of service logs

ENV expected (examples):
  PROXYAPI_KEY / OPENAI_API_KEY / OPENAI_BASE_URL
  OLLAMA_BASE_URL / OLLAMA_MODEL
  CUSTOMER_DB_DSN=postgresql://postgres:1234@localhost:5432/test_docstructure
USAGE
    ;;
esac


