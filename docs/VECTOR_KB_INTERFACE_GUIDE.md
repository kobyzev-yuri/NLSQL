# Vector KB Interface Guide

## Обзор

**Vector KB Interface** - это Streamlit интерфейс для тестирования и дообучения векторной базы знаний. Интерфейс использует FastAPI для всех операций с векторкой, обеспечивая единообразный подход к работе с данными.

## Архитектура

```
┌─────────────────┐    HTTP API    ┌─────────────────┐    ┌─────────────────┐
│  Streamlit UI   │ ──────────────▶│   Core API      │ ──▶│  Vector DB      │
│  (Port 8503)    │                │  (Port 8000)    │    │  (PostgreSQL +  │
│                 │                │                 │    │   pgvector)     │
└─────────────────┘                └─────────────────┘    └─────────────────┘
```

## Запуск

### 1. Запуск всех сервисов
```bash
cd NLSQL
./start_all_services.sh
```

### 2. Запуск Vector KB Interface
```bash
cd NLSQL
./start_vector_kb.sh  # если 8503 занят, скрипт использует 8504
```

### 3. Доступ к интерфейсу
- **Vector KB Interface**: `http://localhost:8503` (или :8504)
- **Core API Docs**: `http://localhost:8000/docs`

## Функциональность

### 🔍 Тестирование поиска

**Цель**: Тестирование качества семантического поиска в векторной базе данных.

**Типы поиска**:
- `semantic` - Семантический поиск по всем типам контента
- `ddl` - Поиск по DDL схемам таблиц
- `documentation` - Поиск по документации
- `examples` - Поиск по Q/A примерам

**Использование**:
1. Выберите тип поиска
2. Введите тестовый запрос
3. Нажмите "🔍 Тестировать поиск"
4. Просмотрите результаты

**API вызовы**:
```bash
curl -X POST http://localhost:8000/semantic-search \
  -H "Content-Type: application/json" \
  -d '{"query":"Покажи всех пользователей","limit":5}'
```

### 📝 Добавление Q/A пар

**Цель**: Добавление новых вопросов и ответов для обучения модели.

**Поддерживаемые форматы**:
- Ручное добавление через интерфейс
- Массовое добавление через JSON файл

**Пример Q/A пары**:
```json
{
    "question": "Покажи всех пользователей системы",
    "sql": "SELECT * FROM equsers WHERE deleted = FALSE"
}
```

Загрузка через интерфейс или REST API (`POST /training/example`).

### 🎓 Обучение

**Цель**: Обучение модели на новых данных (DDL, документация, Q/A пары).

**Типы обучения**:
- **DDL обучение**: Схемы таблиц и связей
- **Документация**: Бизнес-логика и правила
- **Q/A пары**: Примеры вопросов и SQL

**Генерация эмбеддингов**:
```bash
python -m src.tools.generate_embeddings_hf \
  --dsn "$DATABASE_URL" \
  --model "$HF_MODEL_NAME"
```

### 🚀 Оптимизация SQL

**Цель**: Обучение модели генерировать эффективный SQL с учетом производительности.

**Принципы оптимизации**:
- Выбор конкретных полей вместо `SELECT *`
- Добавление фильтров `WHERE`
- Использование `INNER JOIN` для совпадающих записей
- Применение `HAVING` для фильтрации агрегированных данных
- Добавление `ORDER BY` для логичной сортировки

**Примеры оптимизации**:
```sql
-- Базовый SQL
SELECT * FROM equsers

-- Оптимизированный SQL
SELECT id, login, email, department 
FROM equsers 
WHERE deleted = FALSE
```

### 📊 Аналитика качества

**Метрики в интерфейсе**: Top‑1, Top‑3, MRR для retrieval.

### ⚙️ Настройки

**Параметры поиска**:
- Порог схожести (0.0 - 1.0)
- Максимальная длина контекста
- Размер батча для эмбеддингов

**Модель эмбеддингов по умолчанию**:
- `intfloat/multilingual-e5-base` (768d)

## API Endpoints

### FastAPI Endpoints

| Endpoint | Method | Описание |
|----------|--------|----------|
| `/health` | GET | Проверка здоровья системы |
| `/semantic-search` | POST | Семантический поиск по KB |
| `/query` | POST | Генерация SQL |

### Примеры API вызовов

```bash
curl http://localhost:8000/health
curl -X POST http://localhost:8000/semantic-search -H "Content-Type: application/json" -d '{"query":"Покажи всех пользователей","limit":5}'
curl -X POST http://localhost:8000/query -H "Content-Type: application/json" -d '{"question":"Покажи всех пользователей","role":"user","department":"IT"}'
```

## Структура файлов

```
NLSQL/
├── src/vector_kb_interface.py      # Streamlit интерфейс
├── src/tools/generate_embeddings_hf.py
├── docs/VECTOR_DB.md
└── docs/VECTOR_KB_INTERFACE_GUIDE.md
```

## Troubleshooting

### Проблема: Core API недоступен
**Решение**: Убедитесь, что сервис запущен на порту 8000
```bash
./start_all_services.sh
```

### Проблема: Ошибка подключения к векторке
**Решение**: Проверьте подключение к PostgreSQL и наличие pgvector
```bash
# Проверка подключения к БД
psql -h localhost -U postgres -d test_docstructure -c "SELECT version();"
```

### Проблема: Пустые результаты поиска
**Решение**: Убедитесь, что векторка содержит данные
```bash
# Проверка данных в векторке
python qa_management_script.py --action test --input training_data/sql_examples.json
```

## Разработка

### Добавление новых функций

1. **Добавление нового API endpoint**:
   - Обновите `src/api/main.py`
   - Добавьте метод в `QueryService`
   - Обновите интерфейс в `vector_kb_interface.py`

2. **Добавление новых метрик**:
   - Обновите `benchmark_by_complexity.py`
   - Добавьте расчет метрик в `sql_metrics_calculator.py`
   - Обновите отображение в интерфейсе

3. **Добавление новых типов поиска**:
   - Обновите `QueryService.test_vector_search()`
   - Добавьте новый тип в интерфейс
   - Обновите примеры запросов

## Связанные документы

- [TRAINING_GUIDE.md](../docs/TRAINING_GUIDE.md) - Руководство по обучению
- [VECTOR_DB.md](../docs/VECTOR_DB.md) - Структура и индексация векторной таблицы
- [SERVICES_STARTUP_GUIDE.md](../docs/SERVICES_STARTUP_GUIDE.md) - Руководство по сервисам

## Контакты

- **Документация**: `docs/`
- **Логи**: `logs/`
