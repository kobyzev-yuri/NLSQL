# База знаний NL→SQL системы

## 📚 Обзор базы знаний

База знаний содержит структурированную информацию о системе NL→SQL, включая архитектуру, API, компоненты и примеры использования.

---

## 🏗️ Архитектурные компоненты

### 1. **Web Interface Layer**
```
┌─────────────────────────────────────┐
│        Web Interface Layer          │
├─────────────────────────────────────┤
│ • Simple Web Interface (FastAPI)   │
│ • Streamlit UI (опционально)       │
│ • Web Interface (устаревший)        │
└─────────────────────────────────────┘
```

**Ключевые файлы**:
- `src/simple_web_interface.py` - Основной веб-интерфейс
- `src/streamlit_app.py` - Streamlit интерфейс
- `src/web_interface.py` - Устаревший интерфейс

**Основные функции**:
- Прием запросов от пользователей
- Отображение результатов
- Управление сессиями

### 2. **Service Layer**
```
┌─────────────────────────────────────┐
│          Service Layer              │
├─────────────────────────────────────┤
│ • Query Service                     │
│ • Customer API Service              │
│ • Mock Customer API                 │
└─────────────────────────────────────┘
```

**Ключевые файлы**:
- `src/services/query_service.py` - Основной сервис генерации SQL
- `src/services/customer_api_service.py` - Сервис для работы с API заказчика
- `src/mock_customer_api.py` - Mock API для тестирования

**Основные функции**:
- Генерация SQL из естественного языка
- Применение ролевых ограничений
- Выполнение SQL запросов

### 3. **Vanna AI Integration Layer**
```
┌─────────────────────────────────────┐
│      Vanna AI Integration           │
├─────────────────────────────────────┤
│ • Native Vanna AI                   │
│ • Optimized Dual Pipeline           │
│ • Vector Database Integration       │
└─────────────────────────────────────┘
```

**Ключевые файлы**:
- `src/vanna/vanna_pgvector_native.py` - Нативная интеграция с pgvector
- `src/vanna/optimized_dual_pipeline.py` - Оптимизированный пайплайн
- `src/vanna/vector_db_configs.py` - Конфигурация векторных БД

**Основные функции**:
- Семантический поиск по векторной БД
- Генерация SQL через LLM
- Управление базой знаний

### 4. **Utility Layer**
```
┌─────────────────────────────────────┐
│         Utility Layer              │
├─────────────────────────────────────┤
│ • Plan-SQL Converter               │
│ • Embedding Generator              │
│ • Training Tools                    │
└─────────────────────────────────────┘
```

**Ключевые файлы**:
- `src/utils/plan_sql_converter.py` - Конвертер между SQL и планами
- `src/tools/generate_embeddings.py` - Генератор эмбеддингов
- `src/tools/ingest_kb.py` - Импорт базы знаний

---

## 🔧 API Endpoints

### Simple Web Interface (порт 3000)

| Endpoint | Method | Описание |
|----------|--------|----------|
| `/` | GET | Главная страница с интерфейсом |
| `/generate-sql` | POST | Генерация SQL из естественного языка |
| `/execute-sql` | POST | Выполнение SQL запроса |
| `/health` | GET | Проверка состояния системы |

### Mock Customer API (порт 8080)

| Endpoint | Method | Описание |
|----------|--------|----------|
| `/` | GET | Корневой эндпоинт |
| `/api/sql/execute` | POST | Выполнение SQL с ролевыми ограничениями |
| `/api/plan/execute` | POST | Выполнение плана запроса |
| `/health` | GET | Проверка состояния Mock API |

---

## 🧠 База знаний (Knowledge Base)

### Структура таблицы `vanna_vectors`

```sql
CREATE TABLE vanna_vectors (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    content_type VARCHAR(50) NOT NULL,
    metadata JSONB,
    embedding VECTOR(1536),  -- pgvector
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Типы контента

| Тип | Описание | Примеры |
|-----|----------|---------|
| `documentation` | Документация схемы БД | Описания таблиц, колонок |
| `question_sql` | Пары вопрос-ответ | "покажи пользователей" → SQL |
| `ddl` | DDL скрипты | CREATE TABLE, ALTER TABLE |
| `examples` | Примеры SQL | Шаблоны запросов |

### Модели эмбеддингов

| Модель | Размерность | Использование |
|--------|-------------|---------------|
| `text-embedding-ada-002` | 1536 | Основная модель |
| `text-embedding-3-small` | 1536 | Альтернативная |
| `sentence-transformers` | 384-768 | Локальные модели |

---

## 🔍 Семантический поиск

### Алгоритм поиска

1. **Нормализация запроса**
   ```python
   normalized_question = normalize_text(question)
   ```

2. **Генерация эмбеддинга**
   ```python
   query_embedding = generate_embedding(normalized_question)
   ```

3. **Векторный поиск**
   ```sql
   SELECT content, content_type, metadata
   FROM vanna_vectors
   WHERE content_type = 'documentation'
   ORDER BY embedding <-> query_embedding
   LIMIT 5
   ```

4. **Ранжирование результатов**
   ```python
   results = rank_by_relevance(search_results, question)
   ```

### Гибридный поиск

```python
def hybrid_search(question: str) -> List[str]:
    # Семантический поиск
    semantic_results = semantic_search(question)
    
    # Лексический поиск
    lexical_results = lexical_search(question)
    
    # Комбинирование результатов
    combined_results = combine_search_results(
        semantic_results, lexical_results
    )
    
    return combined_results
```

---

## 🎯 Ролевые ограничения

### Роли пользователей

| Роль | Доступ | Ограничения |
|------|--------|-------------|
| `admin` | Полный доступ | Нет ограничений |
| `manager` | Данные отдела | `department = 'user_department'` |
| `user` | Собственные данные | `owner_id = 'user_id'` |

### Применение ограничений

```python
def apply_role_restrictions(sql: str, role: str, department: str) -> str:
    if role == "user":
        sql += " AND owner_id = 'user_id'"
    elif role == "manager":
        sql += " AND department = 'user_department'"
    # admin не имеет ограничений
    
    return sql
```

---

## 🚀 Запуск и конфигурация

### Переменные окружения

```bash
# API Keys
OPENAI_API_KEY=sk-...
PROXYAPI_KEY=sk-...
CUSTOMER_DB_DSN=postgresql://...

# Model Configuration
OLLAMA_MODEL=llama3:latest
OLLAMA_BASE_URL=http://localhost:11434

# Database
DATABASE_URL=postgresql://postgres:1234@localhost:5432/test_docstructure
```

### Порты сервисов

| Сервис | Порт | Описание |
|--------|------|----------|
| Simple Web Interface | 3000 | Основной веб-интерфейс |
| Mock Customer API | 8080 | Mock API для тестирования |
| Core API | 8000 | Основной API (опционально) |
| Streamlit UI | 8501 | Streamlit интерфейс |

### Команды запуска

```bash
# Simple Web Interface
uvicorn src.simple_web_interface:app --host 0.0.0.0 --port 3000

# Mock Customer API
uvicorn src.mock_customer_api:mock_app --host 0.0.0.0 --port 8080

# Core API (опционально)
uvicorn src.api.main:app --host 0.0.0.0 --port 8000

# Streamlit UI
streamlit run src/streamlit_app.py --server.port 8501
```

---

## 📊 Мониторинг и метрики

### Ключевые метрики

| Метрика | Описание | Целевое значение |
|---------|----------|-------------------|
| SQL Quality | % корректных SQL запросов | > 80% |
| Response Time | Среднее время генерации | < 5 сек |
| Context Relevance | % релевантной информации | > 70% |
| Table Accuracy | % использования реальных таблиц | > 90% |

### Логирование

```python
# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/rag_system.log'),
        logging.StreamHandler()
    ]
)
```

### Файлы логов

- `logs/rag_*.log` - Логи RAG системы
- `logs/sql_generation.log` - Логи генерации SQL
- `logs/performance.log` - Логи производительности

---

## 🔧 Отладка и тестирование

### Тестовые скрипты

| Скрипт | Описание | Использование |
|--------|----------|----------------|
| `debug_semantic_search.py` | Отладка семантического поиска | `python debug_semantic_search.py` |
| `test_semantic_rag.py` | Тестирование RAG системы | `python test_semantic_rag.py` |
| `compare_ollama_models.py` | Сравнение моделей | `python compare_ollama_models.py` |

### Проверка здоровья

```bash
# Проверка Simple Web Interface
curl http://localhost:3000/health

# Проверка Mock Customer API
curl http://localhost:8080/health

# Проверка Core API
curl http://localhost:8000/health
```

### Тестовые запросы

```bash
# Генерация SQL
curl -X POST http://localhost:3000/generate-sql \
  -d "question=покажи пользователей&role=admin&department=IT"

# Выполнение SQL
curl -X POST http://localhost:3000/execute-sql \
  -d "question=покажи пользователей&role=admin&department=IT"
```

---

## 📚 Дополнительные ресурсы

### Документация

- [Архитектура системы](SYSTEM_ARCHITECTURE.md)
- [API Reference](API_REFERENCE.md)
- [Код документация](CODE_DOCUMENTATION.md)
- [Методология обучения](TRAINING_METHODOLOGY.md)

### Конфигурационные файлы

- `config.env` - Переменные окружения
- `docs/scripts/config.json` - Конфигурация системы
- `src/vanna/vector_db_configs.py` - Конфигурация векторных БД

### Примеры использования

- `examples/` - Примеры использования API
- `tests/` - Тестовые скрипты
- `scripts/` - Утилиты для разработки

---

**Версия базы знаний**: 1.0.0  
**Дата обновления**: 2024-10-15  
**Автор**: NL→SQL Team


