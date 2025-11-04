#!/bin/bash
# Запуск Core API на порту 8000

cd "$(dirname "$0")"

# Активация виртуального окружения
# Активируем conda окружение py310 без абсолютных путей
if command -v conda >/dev/null 2>&1; then
    eval "$(conda shell.bash hook)"
    conda activate py310
fi

# Загрузка переменных окружения
if [ -f config.env ]; then
    export $(grep -v '^#' config.env | xargs)
fi

# Установка PYTHONPATH
export PYTHONPATH="$(pwd)"

# Создание директорий для логов
mkdir -p logs

# Запуск Core API
echo "🚀 Запуск Core API на порту 8000..."
echo "📝 Логи: logs/core_api_8000.out и logs/core_api_8000.err"
echo ""
echo "Для остановки: Ctrl+C или pkill -f 'uvicorn.*8000'"
echo ""

cd "$(dirname "$0")"
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload


