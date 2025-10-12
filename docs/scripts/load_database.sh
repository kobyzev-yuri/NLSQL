#!/bin/bash

# Скрипт для загрузки дампа PostgreSQL базы данных DocStructureSchema
# Автор: AI Assistant
# Дата: $(date)

set -e  # Остановка при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для вывода сообщений
print_message() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Конфигурация
DB_NAME="test_docstructure"
DB_USER="postgres"
DB_HOST="localhost"
DB_PORT="5432"
SQL_FILE="TradecoTemplateTestDB.sql"

print_message "Скрипт загрузки дампа PostgreSQL базы данных DocStructureSchema"
print_message "================================================================"

# Проверка наличия SQL файла
if [ ! -f "$SQL_FILE" ]; then
    print_error "Файл $SQL_FILE не найден!"
    print_message "Убедитесь, что файл находится в текущей директории"
    exit 1
fi

print_success "Файл $SQL_FILE найден"

# Проверка подключения к PostgreSQL
print_message "Проверка подключения к PostgreSQL..."
if ! psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "SELECT 1;" > /dev/null 2>&1; then
    print_error "Не удается подключиться к PostgreSQL!"
    print_message "Проверьте:"
    print_message "1. PostgreSQL запущен"
    print_message "2. Пользователь $DB_USER существует"
    print_message "3. Пароль правильный"
    print_message "4. Хост и порт корректные"
    exit 1
fi

print_success "Подключение к PostgreSQL успешно"

# Создание базы данных (если не существует)
print_message "Создание базы данных $DB_NAME..."
if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "CREATE DATABASE $DB_NAME;" 2>/dev/null; then
    print_success "База данных $DB_NAME создана"
else
    print_warning "База данных $DB_NAME уже существует или ошибка создания"
fi

# Загрузка дампа
print_message "Загрузка дампа в базу данных $DB_NAME..."
print_message "Это может занять некоторое время..."

# Проверка формата файла
if file "$SQL_FILE" | grep -q "PostgreSQL custom database dump"; then
    print_message "Обнаружен PostgreSQL custom-format dump"
    print_message "Используем pg_restore для загрузки..."
    
    if pg_restore -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" --verbose --clean --if-exists "$SQL_FILE"; then
        print_success "Дамп успешно загружен в базу данных $DB_NAME"
    else
        print_error "Ошибка загрузки через pg_restore!"
        print_message "Попробуйте загрузить вручную:"
        print_message "pg_restore -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME --clean --if-exists $SQL_FILE"
        exit 1
    fi
else
    print_message "Обнаружен SQL файл, используем psql для загрузки..."
    if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$SQL_FILE"; then
        print_success "Дамп успешно загружен через psql"
    else
        print_error "Ошибка загрузки дампа!"
        print_message "Проверьте формат файла и права доступа"
        exit 1
    fi
fi

# Проверка загруженных таблиц
print_message "Проверка загруженных таблиц..."
TABLE_COUNT=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null | tr -d ' ')

if [ "$TABLE_COUNT" -gt 0 ]; then
    print_success "Загружено $TABLE_COUNT таблиц"
    
    # Список основных таблиц
    print_message "Основные таблицы:"
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name IN ('equsers', 'eqdoctypes', 'eqdocstructure', 'tbl_business_unit', 'tbl_principal_assignment', 'tbl_incoming_payments')
    ORDER BY table_name;
    " 2>/dev/null || print_warning "Не удалось получить список таблиц"
else
    print_warning "Таблицы не найдены или ошибка подключения"
fi

# Информация о подключении
print_message "================================================================"
print_success "Загрузка завершена!"
print_message "Для подключения к базе данных используйте:"
print_message "psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME"
print_message ""
print_message "Или через переменные окружения:"
print_message "export PGHOST=$DB_HOST"
print_message "export PGPORT=$DB_PORT"
print_message "export PGUSER=$DB_USER"
print_message "export PGDATABASE=$DB_NAME"
print_message "psql"
print_message "================================================================"

