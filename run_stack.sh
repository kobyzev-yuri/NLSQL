#!/usr/bin/env bash
set -euo pipefail

# Unified process manager for NL→SQL stack
# Supports different startup modes:
#  - web: Core API + Mock API + Web UIs (Simple UI + Streamlit)
#  - vector-kb: Core API + Mock API + Vector KB Interface
#  - core: Only Core API + Mock API (base services)

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$REPO_DIR/logs"
PID_DIR="$REPO_DIR/.pids"
PYTHONPATH="$REPO_DIR"
CONDA_ENV_NAME="${CONDA_ENV_NAME:-py310}"

mkdir -p "$LOG_DIR" "$PID_DIR"
export PYTHONPATH

# Load config if exists
if [[ -f "$REPO_DIR/config.env" ]]; then
    source "$REPO_DIR/config.env"
fi

# Build command with conda activation if needed
build_cmd() {
    local cmd="$1"
    if command -v conda >/dev/null 2>&1; then
        echo "cd $REPO_DIR && eval \"\$(conda shell.bash hook)\" && conda activate $CONDA_ENV_NAME && source config.env 2>/dev/null || true && PYTHONPATH=\$(pwd) $cmd"
    else
        echo "cd $REPO_DIR && source config.env 2>/dev/null || true && PYTHONPATH=\$(pwd) $cmd"
    fi
}

svc_start() {
  local name="$1" cmd="$2" port="$3"
  local out="$LOG_DIR/${name}_${port}.out" err="$LOG_DIR/${name}_${port}.err" pidf="$PID_DIR/${name}_${port}.pid"
  
  # Check if already running
  if [ -f "$pidf" ] && kill -0 "$(cat "$pidf")" 2>/dev/null; then
    echo "[skip] $name already running on :$port (pid $(cat "$pidf"))"
    return 0
  fi
  
  # Clean up stale PID file
  [ -f "$pidf" ] && rm -f "$pidf"
  
  echo "[start] $name on :$port"
  local full_cmd=$(build_cmd "$cmd")
  nohup bash -lc "$full_cmd" > "$out" 2> "$err" &
  echo $! > "$pidf"
  sleep 1
  
  # Verify startup
  if [ -f "$pidf" ] && kill -0 "$(cat "$pidf")" 2>/dev/null; then
    echo "[ok]   $name started (pid $(cat "$pidf"))"
  else
    echo "[fail] $name failed to start, check $err"
    return 1
  fi
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
    return 0
  else
    echo "[down] $name on :$port"
    return 1
  fi
}

# Start core services (Core API + Mock API)
start_core() {
  echo "=== Starting core services ==="
  svc_start core_api "uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload" 8000
  svc_start mock_api "uvicorn src.mock_customer_api:mock_app --host 0.0.0.0 --port 8081 --reload" 8081
}

# Start web UIs (Simple UI + Streamlit)
start_web_uis() {
  echo "=== Starting web UIs ==="
  svc_start simple_ui "uvicorn src.simple_web_interface:app --host 0.0.0.0 --port 3000 --reload" 3000
  svc_start streamlit "streamlit run src/streamlit_main.py --server.port 8501 --server.address 0.0.0.0" 8501
}

# Start Vector KB Interface
start_vector_kb() {
  echo "=== Starting Vector KB Interface ==="
  local vkb_port=8503
  # Check if port is available
  if lsof -i :8503 >/dev/null 2>&1 || netstat -tln 2>/dev/null | grep -q ":8503 " || ss -tln 2>/dev/null | grep -q ":8503 "; then
    vkb_port=8504
    echo "[info] Port 8503 busy, using 8504"
  fi
  
  svc_start vector_kb "streamlit run src/vector_kb_interface.py --server.port ${vkb_port} --server.address 0.0.0.0 --server.headless true --browser.gatherUsageStats false" "$vkb_port"
}

# Start all services (web mode)
start_web() {
  echo "🚀 Starting web mode: Core services + Web UIs"
  start_core
  start_web_uis
  echo ""
  echo "✅ Web mode started!"
  echo "   • Core API:      http://localhost:8000/docs"
  echo "   • Mock API:      http://localhost:8081/health"
  echo "   • Simple UI:     http://localhost:3000"
  echo "   • Streamlit UI:  http://localhost:8501"
}

# Start vector KB mode
start_vector_kb_mode() {
  echo "🚀 Starting vector KB mode: Core services + Vector KB Interface"
  start_core
  start_vector_kb
  echo ""
  echo "✅ Vector KB mode started!"
  echo "   • Core API:         http://localhost:8000/docs"
  echo "   • Mock API:         http://localhost:8081/health"
  echo "   • Vector KB UI:     http://localhost:8503 (or 8504)"
}

# Start all (web mode by default for backward compatibility)
start_all() {
  start_web
}

# Stop services
stop_core() {
  svc_stop mock_api 8081
  svc_stop core_api 8000
}

stop_web_uis() {
  svc_stop streamlit 8501
  svc_stop simple_ui 3000
}

stop_vector_kb() {
  svc_stop vector_kb 8503
  svc_stop vector_kb 8504  # Also check 8504
}

stop_all() {
  echo "🛑 Stopping all services..."
  stop_vector_kb
  stop_web_uis
  stop_core
}

# Status
status_core() {
  svc_status core_api 8000
  svc_status mock_api 8081
}

status_web_uis() {
  svc_status simple_ui 3000
  svc_status streamlit 8501
}

status_vector_kb() {
  svc_status vector_kb 8503
  svc_status vector_kb 8504
}

status_all() {
  echo "=== Core Services ==="
  status_core
  echo ""
  echo "=== Web UIs ==="
  status_web_uis
  echo ""
  echo "=== Vector KB Interface ==="
  status_vector_kb
}

logs_tail() {
  local name="$1" port="$2" lines="${3:-200}"
  local out="$LOG_DIR/${name}_${port}.out" err="$LOG_DIR/${name}_${port}.err"
  echo "===== $name :$port stdout (last $lines) ====="; tail -n "$lines" "$out" 2>/dev/null || true
  echo "===== $name :$port stderr (last $lines) ====="; tail -n "$lines" "$err" 2>/dev/null || true
}

logs_all() {
  logs_tail core_api 8000 200
  logs_tail mock_api 8081 200
  logs_tail simple_ui 3000 200
  logs_tail streamlit 8501 200
  logs_tail vector_kb 8503 200
  logs_tail vector_kb 8504 200
}

# Main command dispatcher
case "${1:-}" in
  start)
    start_all ;;
  start-web)
    start_web ;;
  start-vector-kb|start-vkb)
    start_vector_kb_mode ;;
  start-core)
    start_core ;;
  stop)
    stop_all ;;
  stop-web)
    stop_web_uis ;;
  stop-vector-kb|stop-vkb)
    stop_vector_kb ;;
  stop-core)
    stop_core ;;
  restart)
    stop_all; start_all ;;
  restart-web)
    stop_web_uis; start_web ;;
  restart-vector-kb|restart-vkb)
    stop_vector_kb; start_vector_kb_mode ;;
  status)
    status_all ;;
  logs)
    logs_all ;;
  *)
    cat <<USAGE
Usage: $(basename "$0") <command> [mode]

Commands:
  start              Start all services (web mode - backward compatible)
  start-web          Start core services + web UIs (Simple UI + Streamlit)
  start-vector-kb    Start core services + Vector KB Interface
  start-core         Start only core services (Core API + Mock API)
  
  stop               Stop all services
  stop-web           Stop web UIs only
  stop-vector-kb     Stop Vector KB Interface only
  stop-core          Stop core services only
  
  restart            Restart all services
  restart-web        Restart web UIs
  restart-vector-kb  Restart Vector KB Interface
  
  status             Show status of all services
  logs               Show logs of all services

Examples:
  ./run_stack.sh start-web          # Start web interfaces
  ./run_stack.sh start-vector-kb    # Start vector KB training interface
  ./run_stack.sh status             # Check what's running
  ./run_stack.sh stop-web           # Stop only web UIs

Services:
  Core API           : 8000 (src/api/main.py)
  Mock Customer API  : 8081 (src/mock_customer_api.py)
  Simple Web (UI)    : 3000 (src/simple_web_interface.py)
  Streamlit UI       : 8501 (src/streamlit_main.py)
  Vector KB Interface: 8503/8504 (src/vector_kb_interface.py)

ENV expected (from config.env):
  OPENAI_API_KEY / OPENAI_BASE_URL
  OLLAMA_BASE_URL / OLLAMA_MODEL
  DATABASE_URL=postgresql://postgres:1234@localhost:5432/test_docstructure
USAGE
    exit 1
    ;;
esac
