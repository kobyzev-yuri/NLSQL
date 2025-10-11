#!/bin/bash
"""
Быстрый запуск обучения Vanna AI агента
"""

echo "🚀 Запуск быстрого обучения Vanna AI агента..."

# Проверяем зависимости
echo "🔍 Проверка зависимостей..."
python -c "import vanna, ollama, chromadb" 2>/dev/null || {
    echo "❌ Не все зависимости установлены. Устанавливаем..."
    pip install -r requirements.txt
}

# Проверяем Ollama
echo "🔍 Проверка Ollama..."
ollama list | grep -q "llama3.1:8b" || {
    echo "❌ Модель llama3.1:8b не найдена. Загружаем..."
    ollama pull llama3.1:8b
}

# Проверяем PostgreSQL
echo "🔍 Проверка PostgreSQL..."
psql -h localhost -U postgres -d test_docstructure -c "SELECT 1;" >/dev/null 2>&1 || {
    echo "❌ PostgreSQL недоступен. Проверьте подключение."
    exit 1
}

# Создаем директорию для данных
echo "📁 Создание директории для данных..."
mkdir -p training_data

# Запускаем обучение
echo "🤖 Запуск обучения..."
python train_vanna_agent.py

echo "✅ Обучение завершено!"
