#!/bin/bash
# 🚀 Скрипт для запуска Vector KB Interface (Streamlit)
# Используется для тестирования и дообучения векторной базы знаний

set -euo pipefail

# Цвета для вывода
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHONPATH="$REPO_DIR"

# Экспорт переменных
export PYTHONPATH

log_info "🚀 Запуск Vector KB Interface"
log_info "📁 Рабочая директория: $REPO_DIR"

# Проверка виртуального окружения
CONDA_ENV_NAME="${CONDA_ENV_NAME:-py310}"
if [[ "${CONDA_DEFAULT_ENV:-}" != "$CONDA_ENV_NAME" ]]; then
    log_warning "Активация виртуального окружения $CONDA_ENV_NAME..."
    if command -v conda >/dev/null 2>&1; then
        eval "$(conda shell.bash hook)"
        conda activate "$CONDA_ENV_NAME" || true
    fi
fi

# Проверка конфигурации
if [[ ! -f "$REPO_DIR/config.env" ]]; then
    log_warning "Файл config.env не найден! Используются значения по умолчанию."
else
    log_info "📋 Загрузка конфигурации..."
    source "$REPO_DIR/config.env"
fi

# Проверка, запущен ли Core API
log_info "🔍 Проверка Core API на порту 8000..."
if curl -s http://localhost:8000/status > /dev/null 2>&1; then
    log_success "Core API доступен"
else
    log_warning "Core API не запущен. Запустите: ./start_all_services.sh"
    log_info "Продолжаем запуск интерфейса..."
fi

# Проверка свободного порта
VKB_PORT=8503
if lsof -i :8503 >/dev/null 2>&1 || netstat -tln 2>/dev/null | grep -q ":8503 " || ss -tln 2>/dev/null | grep -q ":8503 "; then
    VKB_PORT=8504
    log_warning "Порт 8503 занят, используем 8504"
fi

# Запуск Streamlit
log_info "🚀 Запуск Streamlit интерфейса..."
log_info "📝 Интерфейс будет доступен по адресу: http://localhost:${VKB_PORT}"

cd "$REPO_DIR"
if command -v conda >/dev/null 2>&1; then
    eval "$(conda shell.bash hook)"
    conda activate "$CONDA_ENV_NAME" || true
fi
source config.env 2>/dev/null || true
PYTHONPATH="$(pwd)" streamlit run src/vector_kb_interface.py \
    --server.port ${VKB_PORT} \
    --server.address 0.0.0.0 \
    --server.headless true \
    --browser.gatherUsageStats false
