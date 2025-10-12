#!/bin/bash
"""
Скрипт для установки pgvector расширения PostgreSQL
"""

echo "🔧 Установка pgvector для PostgreSQL..."

# Проверяем версию PostgreSQL
echo "📊 Проверка версии PostgreSQL..."
psql --version

# Проверяем, установлен ли pgvector
echo "🔍 Проверка установки pgvector..."
psql -h localhost -U postgres -d test_docstructure -c "SELECT * FROM pg_extension WHERE extname = 'vector';" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ pgvector уже установлен!"
    exit 0
fi

# Устанавливаем зависимости
echo "📦 Установка зависимостей..."
sudo apt-get update
sudo apt-get install -y postgresql-server-dev-14 build-essential

# Клонируем и собираем pgvector
echo "🔨 Сборка pgvector..."
cd /tmp
git clone https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install

# Создаем расширение в базе данных
echo "🗄️ Создание расширения в базе данных..."
psql -h localhost -U postgres -d test_docstructure -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Проверяем установку
echo "✅ Проверка установки..."
psql -h localhost -U postgres -d test_docstructure -c "SELECT * FROM pg_extension WHERE extname = 'vector';"

if [ $? -eq 0 ]; then
    echo "🎉 pgvector успешно установлен!"
    echo "📋 Доступные функции:"
    psql -h localhost -U postgres -d test_docstructure -c "SELECT proname FROM pg_proc WHERE proname LIKE '%vector%';"
else
    echo "❌ Ошибка установки pgvector"
    exit 1
fi

echo "🚀 Готово! Теперь можно использовать pgvector в Vanna AI"
