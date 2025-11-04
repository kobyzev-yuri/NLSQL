#!/bin/bash
# 🚀 Скрипт для запуска всех сервисов NL→SQL системы
# Автор: AI Assistant
# Дата: $(date +%Y-%m-%d)

set -euo pipefail

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции для цветного вывода
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Переменные
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$REPO_DIR/logs"
PID_DIR="$REPO_DIR/.pids"
PYTHONPATH="$REPO_DIR"

# Создание директорий
mkdir -p "$LOG_DIR" "$PID_DIR"

# Экспорт переменных
export PYTHONPATH

log_info "🚀 Запуск всех сервисов NL→SQL системы"
log_info "📁 Рабочая директория: $REPO_DIR"

# Проверка виртуального окружения
if [[ "${CONDA_DEFAULT_ENV:-}" != "py310" ]]; then
    log_warning "Активация виртуального окружения py310..."
    if command -v conda >/dev/null 2>&1; then
        eval "$(conda shell.bash hook)"
        conda activate py310 || true
    fi
fi

# Проверка конфигурации
if [[ ! -f "$REPO_DIR/config.env" ]]; then
    log_error "Файл config.env не найден!"
    exit 1
fi

log_info "📋 Загрузка конфигурации..."
source "$REPO_DIR/config.env"

# Функция запуска сервиса
start_service() {
    local name="$1"
    local cmd="$2"
    local port="$3"
    local out="$LOG_DIR/${name}_${port}.out"
    local err="$LOG_DIR/${name}_${port}.err"
    local pidf="$PID_DIR/${name}_${port}.pid"
    
    # Проверка, не запущен ли уже сервис
    if [[ -f "$pidf" ]] && kill -0 "$(cat "$pidf")" 2>/dev/null; then
        log_warning "$name уже запущен на порту :$port (pid $(cat "$pidf"))"
        return 0
    fi
    
    log_info "Запуск $name на порту :$port..."
    nohup bash -lc "$cmd" > "$out" 2> "$err" &
    echo $! > "$pidf"
    sleep 1
    
    # Проверка успешного запуска
    if kill -0 "$(cat "$pidf")" 2>/dev/null; then
        log_success "$name запущен на порту :$port (pid $(cat "$pidf"))"
    else
        log_error "Не удалось запустить $name"
        return 1
    fi
}

# Остановка существующих сервисов
log_info "🛑 Остановка существующих сервисов..."
pkill -f "uvicorn.*8000" 2>/dev/null || true
pkill -f "uvicorn.*8081" 2>/dev/null || true
pkill -f "uvicorn.*3000" 2>/dev/null || true
pkill -f "streamlit.*8501" 2>/dev/null || true
sleep 2

# Запуск сервисов
log_info "🚀 Запуск сервисов..."

# 1. Core API (8000)
start_service "core_api" \
    "cd $REPO_DIR && eval \"\$(conda shell.bash hook)\" && conda activate py310 && source config.env && PYTHONPATH=\$(pwd) uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload" \
    8000

# 2. Mock API (8081) - исправленный порт
start_service "mock_api" \
    "cd $REPO_DIR && eval \"\$(conda shell.bash hook)\" && conda activate py310 && source config.env && PYTHONPATH=\$(pwd) uvicorn src.mock_customer_api:mock_app --host 0.0.0.0 --port 8081 --reload" \
    8081

# 3. Simple UI (3000)
start_service "simple_ui" \
    "cd $REPO_DIR && eval \"\$(conda shell.bash hook)\" && conda activate py310 && source config.env && PYTHONPATH=\$(pwd) uvicorn src.simple_web_interface:app --host 0.0.0.0 --port 3000 --reload" \
    3000

# 4. Streamlit UI (8501) - правильный файл
start_service "streamlit" \
    "cd $REPO_DIR && eval \"\$(conda shell.bash hook)\" && conda activate py310 && source config.env && PYTHONPATH=\$(pwd) streamlit run src/streamlit_main.py --server.port 8501 --server.address 0.0.0.0" \
    8501

# Ожидание запуска
log_info "⏳ Ожидание запуска сервисов..."
sleep 5

# Проверка статуса
log_info "🔍 Проверка статуса сервисов..."

check_service() {
    local name="$1"
    local port="$2"
    local url="$3"
    
    if curl -s "$url" > /dev/null 2>&1; then
        log_success "$name доступен на $url"
        return 0
    else
        log_error "$name недоступен на $url"
        return 1
    fi
}

# Проверка всех сервисов
check_service "Core API" 8000 "http://localhost:8000/docs"
check_service "Mock API" 8081 "http://localhost:8081/health"
check_service "Simple UI" 3000 "http://localhost:3000"
check_service "Streamlit UI" 8501 "http://localhost:8501"

# Итоговый статус
echo ""
log_success "🎉 Все сервисы запущены!"
echo ""
echo "📋 Доступные интерфейсы:"
echo "  • Core API:      http://localhost:8000/docs"
echo "  • Mock API:      http://localhost:8081/health"
echo "  • Simple UI:     http://localhost:3000"
echo "  • Streamlit UI:  http://localhost:8501"
echo ""
echo "🔧 Управление сервисами:"
echo "  • Статус:        ./run_stack.sh status"
echo "  • Остановка:     ./run_stack.sh stop"
echo "  • Перезапуск:    ./run_stack.sh restart"
echo "  • Логи:          ./run_stack.sh logs"
echo ""
log_info "📁 Логи сервисов: $LOG_DIR"
log_info "📁 PID файлы: $PID_DIR"
