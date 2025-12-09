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

# Check if ngrok is installed
check_ngrok() {
  if ! command -v ngrok &> /dev/null; then
    echo "⚠️  ngrok не установлен"
    echo "   Установите: sudo snap install ngrok"
    echo "   Или: wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz"
    return 1
  fi
  return 0
}

# Check if Ollama is installed
check_ollama() {
  if ! command -v ollama &> /dev/null; then
    echo "⚠️  Ollama не установлен"
    echo "   Установите: curl -fsSL https://ollama.com/install.sh | sh"
    return 1
  fi
  return 0
}

# Check if Ollama is running
is_ollama_running() {
  curl -s http://localhost:11434/api/tags >/dev/null 2>&1
}

# Start Ollama service
start_ollama() {
  local pidf="$PID_DIR/ollama.pid"
  local log_file="$LOG_DIR/ollama.log"
  
  # Check if already running
  if is_ollama_running; then
    echo "[skip] Ollama already running"
    return 0
  fi
  
  # Check if Ollama is installed
  if ! check_ollama; then
    echo "[skip] Ollama not installed, skipping"
    return 1
  fi
  
  # Clean up stale PID file
  [ -f "$pidf" ] && rm -f "$pidf"
  
  echo "[start] Ollama service"
  nohup ollama serve > "$log_file" 2>&1 &
  local ollama_pid=$!
  echo $ollama_pid > "$pidf"
  sleep 3
  
  # Verify startup
  if is_ollama_running; then
    echo "[ok]   Ollama started (pid $ollama_pid)"
    return 0
  else
    echo "[fail] Ollama failed to start, check $log_file"
    rm -f "$pidf"
    return 1
  fi
}

# Stop Ollama service
stop_ollama() {
  local pidf="$PID_DIR/ollama.pid"
  if [ -f "$pidf" ]; then
    local pid
    pid=$(cat "$pidf")
    if kill -0 "$pid" 2>/dev/null; then
      echo "[stop] Ollama (pid $pid)"
      kill "$pid" || true
      sleep 1 || true
    fi
    rm -f "$pidf"
  else
    # Try to find and kill ollama process
    local ollama_pids=$(pgrep -f "ollama serve" 2>/dev/null || true)
    if [ -n "$ollama_pids" ]; then
      echo "[stop] Ollama (found processes: $ollama_pids)"
      echo "$ollama_pids" | xargs kill 2>/dev/null || true
    else
      echo "[skip] Ollama not running"
    fi
  fi
}

# Check LLM provider and start Ollama if needed
check_and_start_llm_provider() {
  # Reload config to get latest LLM_PROVIDER
  if [[ -f "$REPO_DIR/config.env" ]]; then
    source "$REPO_DIR/config.env"
  fi
  
  local provider="${LLM_PROVIDER:-openai}"
  provider=$(echo "$provider" | tr '[:upper:]' '[:lower:]')
  
  echo "🔍 LLM Provider: $provider"
  
  if [ "$provider" = "ollama" ]; then
    echo "🤖 Ollama провайдер выбран, проверяю Ollama..."
    if ! is_ollama_running; then
      echo "   Ollama не запущен, запускаю..."
      start_ollama
    else
      echo "   ✅ Ollama уже запущен"
    fi
  else
    echo "🤖 OpenAI/GPT-4 провайдер выбран (Ollama не требуется)"
  fi
  echo ""
}

# Start ngrok tunnels for both web UIs (using single ngrok process with config)
start_ngrok_tunnels() {
  local pidf="$PID_DIR/ngrok.pid"
  local log_file="$LOG_DIR/ngrok.log"
  local config_file="$PID_DIR/ngrok_config.yml"
  
  # Check if already running
  if [ -f "$pidf" ] && kill -0 "$(cat "$pidf")" 2>/dev/null; then
    echo "[skip] ngrok already running (pid $(cat "$pidf"))"
    return 0
  fi
  
  # Clean up stale PID file
  [ -f "$pidf" ] && rm -f "$pidf"
  
  # Try to read authtoken from default ngrok config locations
  local authtoken=""
  local ngrok_config_locations=(
    "$HOME/.ngrok2/ngrok.yml"
    "$HOME/.config/ngrok/ngrok.yml"
    "$HOME/.ngrok/ngrok.yml"
  )
  
  for config_loc in "${ngrok_config_locations[@]}"; do
    if [ -f "$config_loc" ]; then
      authtoken=$(grep -i "^[[:space:]]*authtoken:" "$config_loc" 2>/dev/null | sed 's/^[[:space:]]*authtoken:[[:space:]]*//' | head -1)
      if [ -n "$authtoken" ]; then
        break
      fi
    fi
  done
  
  # Create ngrok config file with two tunnels
  if [ -n "$authtoken" ]; then
    cat > "$config_file" <<EOF
version: "2"
authtoken: $authtoken
tunnels:
  simple_ui:
    addr: 3000
    proto: http
  streamlit:
    addr: 8501
    proto: http
EOF
  else
    # Try without authtoken (might be set via env var or default config)
    cat > "$config_file" <<EOF
version: "2"
tunnels:
  simple_ui:
    addr: 3000
    proto: http
  streamlit:
    addr: 8501
    proto: http
EOF
  fi
  
  echo "[start] ngrok tunnels for ports 3000 and 8501"
  ngrok start --all --config "$config_file" > "$log_file" 2>&1 &
  local ngrok_pid=$!
  echo $ngrok_pid > "$pidf"
  sleep 4
  
  # Verify startup
  if [ -f "$pidf" ] && kill -0 "$ngrok_pid" 2>/dev/null; then
    echo "[ok]   ngrok started (pid $ngrok_pid)"
    return 0
  else
    echo "[fail] ngrok failed to start, check $log_file"
    rm -f "$pidf" "$config_file"
    return 1
  fi
}

# Get ngrok URL for a tunnel by name
get_ngrok_url() {
  local tunnel_name="$1"
  # Use default ngrok web interface port 4040
  local url=$(curl -s "http://localhost:4040/api/tunnels" 2>/dev/null | \
    python3 -c "import sys, json; data=json.load(sys.stdin); \
    tunnels=[t for t in data.get('tunnels', []) if t.get('name') == '$tunnel_name']; \
    print(tunnels[0]['public_url'] if tunnels else '')" 2>/dev/null)
  echo "$url"
}

# Stop ngrok tunnels
stop_ngrok_tunnels() {
  local pidf="$PID_DIR/ngrok.pid"
  local config_file="$PID_DIR/ngrok_config.yml"
  if [ -f "$pidf" ]; then
    local pid
    pid=$(cat "$pidf")
    if kill -0 "$pid" 2>/dev/null; then
      echo "[stop] ngrok (pid $pid)"
      kill "$pid" || true
      sleep 0.5 || true
    fi
    rm -f "$pidf" "$config_file"
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
  
  # Start ngrok tunnels if ngrok is available
  if check_ngrok; then
    echo ""
    echo "🌐 Starting ngrok tunnels..."
    start_ngrok_tunnels
  else
    echo ""
    echo "⚠️  ngrok не установлен, туннели не будут созданы"
  fi
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
  
  # Check LLM provider and start Ollama if needed
  check_and_start_llm_provider
  
  start_core
  start_web_uis
  echo ""
  echo "✅ Web mode started!"
  echo "   • Core API:      http://localhost:8000/docs"
  echo "   • Mock API:      http://localhost:8081/health"
  echo "   • Simple UI:     http://localhost:3000"
  echo "   • Streamlit UI:  http://localhost:8501"
  
  # Show ngrok URLs if available
  if check_ngrok >/dev/null 2>&1; then
    sleep 3  # Give ngrok time to initialize
    local ngrok_url_3000=$(get_ngrok_url "simple_ui" 2>/dev/null)
    local ngrok_url_8501=$(get_ngrok_url "streamlit" 2>/dev/null)
    
    if [ -n "$ngrok_url_3000" ] || [ -n "$ngrok_url_8501" ]; then
      echo ""
      echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      echo "🌐 Ngrok туннели:"
      if [ -n "$ngrok_url_3000" ]; then
        echo "   • Simple UI (ngrok):     $ngrok_url_3000"
      else
        echo "   • Simple UI (ngrok):     ⚠️  Туннель не активен (проверьте логи)"
      fi
      if [ -n "$ngrok_url_8501" ]; then
        echo "   • Streamlit UI (ngrok):   $ngrok_url_8501"
      else
        echo "   • Streamlit UI (ngrok):   ⚠️  Туннель не активен (проверьте логи)"
      fi
      echo ""
      echo "📊 Ngrok веб-интерфейс: http://localhost:4040"
      echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    else
      echo ""
      echo "⚠️  Ngrok туннели запущены, но URL недоступны"
      echo "   Проверьте логи: tail -f logs/ngrok_*.log"
      echo "   Или веб-интерфейсы: http://localhost:4040 и http://localhost:4041"
    fi
  fi
}

# Start vector KB mode
start_vector_kb_mode() {
  echo "🚀 Starting vector KB mode: Core services + Vector KB Interface"
  
  # Check LLM provider and start Ollama if needed
  check_and_start_llm_provider
  
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
  stop_ngrok_tunnels
}

stop_vector_kb() {
  svc_stop vector_kb 8503
  svc_stop vector_kb 8504  # Also check 8504
}

stop_all() {
  echo "🛑 Stopping all services..."
  stop_vector_kb
  stop_web_uis  # This will also stop ngrok tunnels
  stop_core
  
  # Stop Ollama if running (only if LLM_PROVIDER=ollama)
  if [[ -f "$REPO_DIR/config.env" ]]; then
    source "$REPO_DIR/config.env"
    local provider="${LLM_PROVIDER:-openai}"
    provider=$(echo "$provider" | tr '[:upper:]' '[:lower:]')
    if [ "$provider" = "ollama" ]; then
      stop_ollama
    fi
  fi
}

# Status
status_core() {
  svc_status core_api 8000
  svc_status mock_api 8081
}

status_web_uis() {
  svc_status simple_ui 3000
  svc_status streamlit 8501
  local ngrok_pidf="$PID_DIR/ngrok.pid"
  if [ -f "$ngrok_pidf" ] && kill -0 "$(cat "$ngrok_pidf")" 2>/dev/null; then
    echo "[up]   ngrok tunnels (pid $(cat "$ngrok_pidf"))"
  else
    echo "[down] ngrok tunnels"
  fi
}

status_vector_kb() {
  svc_status vector_kb 8503
  svc_status vector_kb 8504
}

status_all() {
  echo "=== LLM Provider ==="
  if [[ -f "$REPO_DIR/config.env" ]]; then
    source "$REPO_DIR/config.env"
    local provider="${LLM_PROVIDER:-openai}"
    provider=$(echo "$provider" | tr '[:upper:]' '[:lower:]')
    echo "Provider: $provider"
    if [ "$provider" = "ollama" ]; then
      if is_ollama_running; then
        echo "[up]   Ollama service"
      else
        echo "[down] Ollama service"
      fi
    else
      echo "[skip] Ollama not required (using OpenAI/GPT-4)"
    fi
  fi
  echo ""
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
