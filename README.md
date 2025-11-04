# NL→SQL система с GPT-4o и RAG

Система преобразования естественного языка в SQL запросы для PostgreSQL с использованием GPT-4o, семантического поиска (RAG) и ролевых ограничений.

**Версия:** 2.0  
**Дата:** 4 ноября 2025

---

## Быстрый старт

```bash
# 1. Запуск всех сервисов
cd /mnt/ai/cnn/sql4A
./start_all_services.sh

# 2. Откройте в браузере (локально)
# localhost:3000   # Simple UI (основной интерфейс)
# localhost:8501   # Streamlit UI
# localhost:8503   # Vector KB (обучение)
```

---

## Интерфейсы системы

| Порт | Интерфейс | Назначение | URL |
|------|-----------|------------|-----|
| **3000** | Simple UI | Веб-интерфейс с детализацией | `http://localhost:3000` |
| **8501** | Streamlit UI | Пользовательский интерфейс | `http://localhost:8501` |
| **8503** | **Vector KB** | **Обучение RAG и тестирование** | `http://localhost:8503` |
| 8000 | Core API | REST API (генерация SQL) | `http://localhost:8000/docs` |
| 8081 | Mock API | Ролевые ограничения | `http://localhost:8081/health` |
Примечание: указанные URL работают только локально после запуска сервисов.

---

## Возможности

### 1. **Генерация SQL из естественного языка**
```
Вопрос: "Покажи всех пользователей"
↓ GPT-4o + RAG
SQL: SELECT * FROM equsers WHERE deleted = false
```

### 2. **Ролевые ограничения безопасности**
- 👑 **admin** - полный доступ
- 👨‍💼 **manager** - данные своего отдела
- 👤 **user** - только свои данные

### 3. **RAG (Retrieval Augmented Generation)**
- Семантический поиск по векторной базе
- Использование обучающих примеров (DDL, документация, Q/A)
- Top-K retrieval

### 4. **Интерфейс обучения Vector KB**
- Тестирование семантического поиска
- Добавление Q/A пар
- Обучение на примерах DDL/SQL
- Метрики качества (Top-1, Top-3, MRR)

---

## Архитектура

```
User Interface (3000/8501/8503)
         ↓
    Core API (8000)
    • QueryService
    • RAG Search
    • GPT-4o
         ↓
    Mock API (8081)
    • Role restrictions
    • SQL execution
         ↓
    PostgreSQL
    • Data tables
    • Vector DB (vanna_vectors)
```

Подробнее: `docs/SYSTEM_OVERVIEW.md`

---

## Документация

### Основные документы

- **[SYSTEM_OVERVIEW.md](docs/SYSTEM_OVERVIEW.md)** - Обзор системы
- **[ROLE_RESTRICTIONS_GUIDE.md](docs/ROLE_RESTRICTIONS_GUIDE.md)** - Настройка ролевых ограничений
- **[VECTOR_KB_INTERFACE_GUIDE.md](docs/VECTOR_KB_INTERFACE_GUIDE.md)** - Работа с интерфейсом обучения
- **[SERVICES_STARTUP_GUIDE.md](docs/SERVICES_STARTUP_GUIDE.md)** - Запуск и управление

### Дополнительные

- **[TRAINING_GUIDE.md](docs/TRAINING_GUIDE.md)** - Обучение RAG (основной документ)
- **[API_REFERENCE.md](docs/API_REFERENCE.md)** - Справочник API
- **[VECTOR_DB.md](docs/VECTOR_DB.md)** - Структура и индексы pgvector

---

## Управление системой

### Все сервисы

```bash
./start_all_services.sh    # Запуск всех
./run_stack.sh status       # Статус
./run_stack.sh restart      # Перезапуск
./run_stack.sh stop         # Остановка
./run_stack.sh logs         # Логи
```

### Отдельные сервисы

```bash
./run_stack.sh start core_api    # Запуск Core API
./run_stack.sh stop mock_api     # Остановка Mock API
./start_vector_kb.sh             # Запуск Vector KB
```

### Проверка здоровья

```bash
curl http://localhost:8000/health
curl http://localhost:8081/health
curl http://localhost:3000
```

---

## Конфигурация

**Файл:** `config.env`

```bash
# LLM модель
OPENAI_API_KEY=sk-...              # Ключ ProxyAPI или OpenAI
OPENAI_BASE_URL=https://api.proxyapi.ru/openai/v1
OPENAI_MODEL=gpt-4o

# База данных
DATABASE_URL=postgresql://postgres:1234@localhost:5432/test_docstructure

# Векторная база
VECTOR_TABLE=vanna_vectors
TRAINING_DATA_DIR=training_data
```

---

## Примеры использования

### 1. Генерация SQL через Simple UI

1. Откройте `http://localhost:3000`
2. Выберите роль (admin/manager/user)
3. Введите вопрос: "Покажи всех пользователей"
4. Смотрите результат:
   - 📋 SQL Шаблон (оригинальный от GPT-4o)
   - 🔐 SQL с ролевыми ограничениями
   - 🧭 План запроса
   - 📊 Результаты выполнения

### 2. Обучение векторной базы

1. Откройте `http://localhost:8503` (если порт занят, скрипт использует 8504)
2. Вкладка "🔍 Тестирование поиска"
   - Введите вопрос
   - Просмотрите найденные примеры
3. Вкладка "➕ Добавление Q/A пар"
   - Добавьте новый вопрос и SQL
   - Система автоматически создаст эмбеддинг
4. Вкладка "📊 Метрики"
   - Посмотрите качество retrieval
   - Top-1, Top-3 accuracy
   - MRR (Mean Reciprocal Rank)

### 3. API запросы

```bash
# Генерация SQL
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Покажи всех пользователей",
    "user_id": "test",
    "role": "admin",
    "department": "IT"
  }'

# Семантический поиск
curl -X POST http://localhost:8000/semantic-search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "покажи пользователей",
    "limit": 5
  }'
```

---

## Ролевые ограничения

### Примеры ограничений

**Вопрос:** "Покажи всех пользователей"

```sql
-- admin
SELECT * FROM equsers WHERE deleted = false

-- manager (отдел IT)
SELECT * FROM equsers WHERE deleted = false 
AND department = (SELECT id FROM eq_departments WHERE name = 'IT')

-- user
SELECT * FROM equsers WHERE deleted = false 
AND login = 'test_user'
```

Настройка: `src/mock_customer_api.py` → функция `apply_role_restrictions()`

**Документация:** `docs/ROLE_RESTRICTIONS_GUIDE.md`

---

## Структура проекта

```
sql4A/
├── src/
│   ├── api/main.py                   # Core API
│   ├── services/query_service.py     # Генерация SQL + RAG
│   ├── vanna/                        # LLM обертки
│   ├── simple_web_interface.py       # Simple UI
│   ├── streamlit_main.py             # Streamlit UI
│   └── mock_customer_api.py          # Mock API
├── vector_kb_interface.py            # Vector KB Interface
├── docs/                             # Документация
├── training_data/                    # Обучающие данные
├── logs/                             # Логи
├── config.env                        # Конфигурация
├── start_all_services.sh             # Запуск всех
├── run_stack.sh                      # Управление
└── start_vector_kb.sh                # Запуск Vector KB
```

---

## Процесс генерации SQL

```
1. User Input
   "Покажи всех пользователей"
   
2. Core API (QueryService)
   ├─ Определение домена: "users"
   ├─ Получение DDL: equsers, eq_departments
   ├─ RAG поиск: похожие вопросы
   └─ Построение промпта с контекстом
   
3. GPT-4o via ProxyAPI
   Генерация SQL с учетом контекста
   
4. Mock API
   Применение ролевых ограничений
   
5. PostgreSQL
   Выполнение SQL
   
6. Result
   ✅ SQL + План + Результаты
```

---

## Технологии

- **Backend:** Python 3.10, FastAPI, Streamlit
- **LLM:** GPT-4o (ProxyAPI.ru), Ollama (опционально)
- **Database:** PostgreSQL 14+
- **Vector DB:** pgvector
- **Embeddings:** intfloat/multilingual-e5-base (768d)

---

## Метрики качества

Просмотр через Vector KB Interface (`http://localhost:8503`):

- **Top-1 Accuracy** - точность первого результата
- **Top-3 Accuracy** - точность топ-3 результатов
- **MRR** (Mean Reciprocal Rank) - средняя позиция релевантного результата

---

## Отладка

### Логи

```bash
tail -f logs/core_api_8000.err       # Core API
tail -f logs/mock_api_8081.err       # Mock API
tail -f logs/simple_ui_3000.err      # Simple UI
tail -f logs/streamlit_8501.err      # Streamlit
tail -f logs/vector_kb_8503.err      # Vector KB
```

### Проверка статуса

```bash
./run_stack.sh status
ps aux | grep "uvicorn\|streamlit"
```

### Типичные проблемы

1. **Порт занят**
   ```bash
   pkill -f "uvicorn.*8000"
   ```

2. **API ключ не работает**
   - Проверьте `config.env`
   - Тест: `curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.proxyapi.ru/openai/v1/models`

3. **База данных недоступна**
   - Проверьте PostgreSQL: `psql -U postgres -d test_docstructure -c "SELECT 1"`

---

<!-- Удалено: Roadmap. README отражает только текущий функционал. -->

---

## Поддержка

1. **Документация:** `docs/SYSTEM_OVERVIEW.md`
2. **Логи:** `logs/`
3. **Статус:** `./run_stack.sh status`

---

## Лицензия

Внутренний проект

---

**Дата последнего обновления:** 4 ноября 2025
