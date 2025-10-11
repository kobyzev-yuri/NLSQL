# NL→SQL система с интеграцией Vanna AI

## 🎯 Описание проекта

Система для генерации SQL запросов на естественном языке с использованием Vanna AI и FastAPI. Позволяет пользователям задавать вопросы на русском языке и получать соответствующие SQL запросы для базы данных DocStructureSchema.

## 🏗️ Архитектура

```
Пользователь → FastAPI → Vanna AI → SQL шаблон → API заказчика → PostgreSQL → Результат
```

### Основные компоненты:
- **FastAPI сервер** - REST API для обработки запросов
- **Vanna AI** - RAG модель для генерации SQL
- **ChromaDB** - векторная база данных
- **PostgreSQL** - основная база данных DocStructureSchema
- **API заказчика** - обработка ролевых ограничений

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Настройка конфигурации

```bash
cp config.env.example .env
# Отредактируйте .env файл с вашими настройками
```

### 3. Запуск сервера

```bash
python -m src.api.main
```

### 4. Проверка работы

```bash
curl http://localhost:8000/health
```

## 📋 API Эндпоинты

### Основные эндпоинты:

- `GET /` - Информация о сервисе
- `GET /health` - Проверка здоровья системы
- `POST /query` - Генерация SQL запроса
- `POST /query/execute` - Генерация и выполнение SQL
- `POST /training/example` - Добавление примера обучения
- `GET /training/status` - Статус обучения модели

### Примеры запросов:

#### Генерация SQL:
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Покажи всех пользователей",
    "user_id": "123",
    "role": "admin"
  }'
```

#### Выполнение запроса:
```bash
curl -X POST "http://localhost:8000/query/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Сколько клиентов в системе?",
    "user_id": "123",
    "role": "manager"
  }'
```

## 🔧 Конфигурация

### Переменные окружения:

- `OPENAI_API_KEY` - API ключ OpenAI
- `DATABASE_URL` - URL подключения к PostgreSQL
- `CUSTOMER_API_URL` - URL API заказчика
- `VANNA_CHROMA_DB_PATH` - Путь к векторной базе данных

### База данных:

Система работает с PostgreSQL базой данных DocStructureSchema, содержащей:
- 200 таблиц
- 1,124 пользователя
- 502 клиента
- 1,959 поручений
- 1,665 платежей

## 🧠 Обучение модели

### Автоматическое обучение:
Система автоматически обучается на:
- DDL структуре базы данных
- Документации на русском языке
- Примерах SQL запросов

### Ручное обучение:
```python
# Добавление примера обучения
await query_service.add_training_example(
    question="Покажи всех пользователей",
    sql="SELECT * FROM equsers",
    user_id="123"
)
```

## 🔒 Безопасность

- Ролевая модель доступа
- Row Level Security (RLS) в PostgreSQL
- Валидация SQL запросов
- Ограничения по отделам и ролям

## 📊 Мониторинг

### Проверка здоровья:
```bash
curl http://localhost:8000/health
```

### Логи:
```bash
tail -f logs/app.log
```

## 🧪 Тестирование

```bash
# Запуск тестов
pytest tests/

# Запуск с покрытием
pytest --cov=src tests/
```

## 📚 Документация

- [Архитектура системы](ARCHITECTURE_VANNA_INTEGRATION.md)
- [Анализ базы данных](DATABASE_SCHEMA_ANALYSIS.md)
- [Отчет о загрузке](DATABASE_LOAD_REPORT.md)

## 🤝 Разработка

### Структура проекта:
```
sql4A/
├── src/
│   ├── api/           # FastAPI эндпоинты
│   ├── models/        # Pydantic модели
│   ├── services/      # Бизнес-логика
│   └── vanna/         # Vanna AI интеграция
├── docs/              # Документация
├── tests/             # Тесты
└── requirements.txt   # Зависимости
```

### Установка для разработки:
```bash
pip install -r requirements.txt
pre-commit install
```

## 📄 Лицензия

MIT License

## 🔗 Ссылки

- [Vanna AI](https://github.com/vanna-ai/vanna)
- [FastAPI](https://fastapi.tiangolo.com/)
- [PostgreSQL](https://www.postgresql.org/)
- [ChromaDB](https://www.trychroma.com/)