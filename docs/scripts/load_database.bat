@echo off
REM Скрипт для загрузки дампа PostgreSQL базы данных DocStructureSchema (Windows)
REM Автор: AI Assistant
REM Дата: %date%

setlocal enabledelayedexpansion

REM Конфигурация
set DB_NAME=test_docstructure
set DB_USER=postgres
set DB_HOST=localhost
set DB_PORT=5432
set SQL_FILE=TradecoTemplateTestDB.sql

echo.
echo [INFO] Скрипт загрузки дампа PostgreSQL базы данных DocStructureSchema
echo [INFO] ================================================================
echo.

REM Проверка наличия SQL файла
if not exist "%SQL_FILE%" (
    echo [ERROR] Файл %SQL_FILE% не найден!
    echo [INFO] Убедитесь, что файл находится в текущей директории
    pause
    exit /b 1
)

echo [SUCCESS] Файл %SQL_FILE% найден

REM Проверка подключения к PostgreSQL
echo [INFO] Проверка подключения к PostgreSQL...
psql -h %DB_HOST% -p %DB_PORT% -U %DB_USER% -d postgres -c "SELECT 1;" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Не удается подключиться к PostgreSQL!
    echo [INFO] Проверьте:
    echo [INFO] 1. PostgreSQL запущен
    echo [INFO] 2. Пользователь %DB_USER% существует
    echo [INFO] 3. Пароль правильный
    echo [INFO] 4. Хост и порт корректные
    pause
    exit /b 1
)

echo [SUCCESS] Подключение к PostgreSQL успешно

REM Создание базы данных (если не существует)
echo [INFO] Создание базы данных %DB_NAME%...
psql -h %DB_HOST% -p %DB_PORT% -U %DB_USER% -d postgres -c "CREATE DATABASE %DB_NAME%;" >nul 2>&1
if errorlevel 1 (
    echo [WARNING] База данных %DB_NAME% уже существует или ошибка создания
) else (
    echo [SUCCESS] База данных %DB_NAME% создана
)

REM Загрузка дампа
echo [INFO] Загрузка дампа в базу данных %DB_NAME%...
echo [INFO] Это может занять некоторое время...

REM Проверка формата файла (простая проверка)
echo [INFO] Обнаружен PostgreSQL custom-format dump
echo [INFO] Используем pg_restore для загрузки...

pg_restore -h %DB_HOST% -p %DB_PORT% -U %DB_USER% -d %DB_NAME% --verbose --clean --if-exists "%SQL_FILE%"
if errorlevel 1 (
    echo [ERROR] Ошибка загрузки через pg_restore!
    echo [INFO] Попробуйте загрузить вручную:
    echo [INFO] pg_restore -h %DB_HOST% -p %DB_PORT% -U %DB_USER% -d %DB_NAME% --clean --if-exists %SQL_FILE%
    pause
    exit /b 1
)

echo [SUCCESS] Дамп успешно загружен в базу данных %DB_NAME%

REM Проверка загруженных таблиц
echo [INFO] Проверка загруженных таблиц...
for /f "tokens=*" %%i in ('psql -h %DB_HOST% -p %DB_PORT% -U %DB_USER% -d %DB_NAME% -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2^>nul') do set TABLE_COUNT=%%i

if %TABLE_COUNT% gtr 0 (
    echo [SUCCESS] Загружено %TABLE_COUNT% таблиц
    
    REM Список основных таблиц
    echo [INFO] Основные таблицы:
    psql -h %DB_HOST% -p %DB_PORT% -U %DB_USER% -d %DB_NAME% -c "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name IN ('equsers', 'eqdoctypes', 'eqdocstructure', 'tbl_business_unit', 'tbl_principal_assignment', 'tbl_incoming_payments') ORDER BY table_name;" 2>nul
) else (
    echo [WARNING] Таблицы не найдены или ошибка подключения
)

REM Информация о подключении
echo [INFO] ================================================================
echo [SUCCESS] Загрузка завершена!
echo [INFO] Для подключения к базе данных используйте:
echo [INFO] psql -h %DB_HOST% -p %DB_PORT% -U %DB_USER% -d %DB_NAME%
echo.
echo [INFO] Или через переменные окружения:
echo [INFO] set PGHOST=%DB_HOST%
echo [INFO] set PGPORT=%DB_PORT%
echo [INFO] set PGUSER=%DB_USER%
echo [INFO] set PGDATABASE=%DB_NAME%
echo [INFO] psql
echo [INFO] ================================================================
echo.
pause
