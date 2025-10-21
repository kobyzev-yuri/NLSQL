# Vector KB Interface Guide

## Обзор

**Vector KB Interface** - это Streamlit интерфейс для тестирования и дообучения векторной базы знаний. Интерфейс использует FastAPI для всех операций с векторкой, обеспечивая единообразный подход к работе с данными.

## Архитектура

```
┌─────────────────┐    HTTP API    ┌─────────────────┐    ┌─────────────────┐
│  Streamlit UI   │ ──────────────▶│   FastAPI       │ ──▶│  Vector DB      │
│  (Port 8503)    │                │  (Port 3000)    │    │  (PostgreSQL +  │
│                 │                │                 │    │   pgvector)     │
└─────────────────┘                └─────────────────┘    └─────────────────┘
```

## Запуск

### 1. Запуск FastAPI сервиса
```bash
cd /mnt/ai/cnn/sql4A
python src/simple_web_interface.py
```

### 2. Запуск Vector KB Interface
```bash
cd /mnt/ai/cnn/sql4A
streamlit run vector_kb_interface.py --server.port 8503
```

### 3. Доступ к интерфейсу
- **Vector KB Interface**: http://localhost:8503
- **FastAPI Docs**: http://localhost:3000/docs

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
```python
# Тестирование поиска
POST /test-search
{
    "question": "Покажи всех пользователей",
    "search_type": "semantic",
    "limit": 5
}
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

**CLI команды**:
```bash
# Создание шаблона
python qa_management_script.py --action template --output qa_template.json

# Добавление Q/A пар
python qa_management_script.py --action add --input qa_pairs.json --validate
```

### 🎓 Обучение

**Цель**: Обучение модели на новых данных (DDL, документация, Q/A пары).

**Типы обучения**:
- **DDL обучение**: Схемы таблиц и связей
- **Документация**: Бизнес-логика и правила
- **Q/A пары**: Примеры вопросов и SQL

**CLI команды**:
```bash
# Генерация эмбеддингов
python qa_management_script.py --action embeddings

# Обучение на оптимизированных SQL
python qa_management_script.py --action optimize --input optimized_sql_examples.json
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

**Метрики**:
- **Precision (P)**: Доля корректных SQL запросов
- **Recall (R)**: Доля найденных корректных SQL
- **F1-Score**: Гармоническое среднее P и R

**Бенчмарк по сложности**:
- **Простые запросы**: SELECT без JOIN (3 запроса)
- **Средние запросы**: С JOIN, без агрегации (4 запроса)
- **Сложные запросы**: С агрегацией, GROUP BY (3 запроса)

**Запуск бенчмарка**:
```bash
python benchmark_by_complexity.py
```

### ⚙️ Настройки

**Параметры поиска**:
- Порог схожести (0.0 - 1.0)
- Максимальная длина контекста
- Размер батча для эмбеддингов

**Модели эмбеддингов**:
- `all-MiniLM-L6-v2` - Быстрая, компактная (22MB)
- `all-mpnet-base-v2` - Высокое качество (420MB)
- `paraphrase-multilingual-MiniLM-L12-v2` - Многоязычная (118MB)

## API Endpoints

### FastAPI Endpoints

| Endpoint | Method | Описание |
|----------|--------|----------|
| `/health` | GET | Проверка здоровья системы |
| `/test-search` | POST | Тестирование поиска в векторке |
| `/generate-sql` | POST | Генерация SQL запроса |
| `/query` | POST | Полный цикл генерации SQL |

### Примеры API вызовов

```python
import requests

# Проверка здоровья
response = requests.get("http://localhost:3000/health")

# Тестирование поиска
response = requests.post(
    "http://localhost:3000/test-search",
    json={
        "question": "Покажи всех пользователей",
        "search_type": "semantic",
        "limit": 5
    }
)

# Генерация SQL
response = requests.post(
    "http://localhost:3000/generate-sql",
    data={"question": "Покажи всех пользователей"}
)
```

## Структура файлов

```
/mnt/ai/cnn/sql4A/
├── vector_kb_interface.py          # Основной интерфейс
├── vector_db_tester.py             # CLI тестер векторки
├── benchmark_by_complexity.py      # Бенчмарк по сложности
├── qa_management_script.py         # CLI управление Q/A
├── enhanced_qa_training.py        # Обучение на оптимизированных SQL
├── optimized_sql_examples.json     # Примеры оптимизированных SQL
├── complexity_benchmark_results.json # Результаты бенчмарка
└── docs/
    └── VECTOR_KB_INTERFACE_GUIDE.md # Эта документация
```

## Troubleshooting

### Проблема: FastAPI недоступен
**Решение**: Убедитесь, что сервис запущен на порту 3000
```bash
python src/simple_web_interface.py
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

- [VANNA_TRAINING_GUIDE.md](../docs/VANNA_TRAINING_GUIDE.md) - Руководство по обучению
- [RAG_IMPROVEMENT_CHECKLIST.md](../RAG_IMPROVEMENT_CHECKLIST.md) - Чеклист улучшений RAG
- [VECTOR_KB_IMPROVEMENT_PLAN.md](../VECTOR_KB_IMPROVEMENT_PLAN.md) - План улучшения векторки
- [SERVICES_STARTUP_GUIDE.md](../docs/SERVICES_STARTUP_GUIDE.md) - Руководство по сервисам

## Контакты

- **GitHub**: [kobyzev-yuri/NLSQL](https://github.com/kobyzev-yuri/NLSQL)
- **Документация**: `/mnt/ai/cnn/sql4A/docs/`
- **Логи**: `/mnt/ai/cnn/sql4A/logs/`
