#!/bin/bash

# Скрипт для запуска интерфейса обучения векторной базы знаний

REPO_DIR="/mnt/ai/cnn/sql4A"
PORT=8503

cd "$REPO_DIR" || exit 1

# Активируем conda окружение
source /mnt/ai/src/anaconda3/bin/activate py310

# Загружаем переменные окружения
if [ -f "$REPO_DIR/config.env" ]; then
    source "$REPO_DIR/config.env"
fi

# Проверяем запущен ли уже
if pgrep -f "streamlit.*vector_kb.*$PORT" > /dev/null; then
    echo "⚠️  Vector KB Interface уже запущен на порту $PORT"
    echo "Остановить: pkill -f 'streamlit.*vector_kb.*$PORT'"
    exit 1
fi

# Создаем директорию для логов
mkdir -p logs

echo "🚀 Запуск Vector KB Interface на порту $PORT..."

# Запускаем Streamlit в фоне
nohup streamlit run vector_kb_interface.py \
    --server.port $PORT \
    --server.address 0.0.0.0 \
    > logs/vector_kb_$PORT.out \
    2> logs/vector_kb_$PORT.err &

PID=$!
sleep 3

# Проверяем запустился ли
if ps -p $PID > /dev/null; then
    echo "✅ Vector KB Interface запущен (PID: $PID)"
    echo "📊 URL: http://localhost:$PORT"
    echo "📁 Логи: logs/vector_kb_$PORT.{out,err}"
    echo ""
    echo "Остановить: pkill -f 'streamlit.*vector_kb.*$PORT'"
else
    echo "❌ Ошибка запуска. Проверьте логи:"
    echo "   tail -50 logs/vector_kb_$PORT.err"
    exit 1
fi

