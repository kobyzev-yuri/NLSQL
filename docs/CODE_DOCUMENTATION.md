# JavaDoc-стиль документация NL→SQL системы

## 📋 Обзор системы

**NL→SQL Assistant** - система для преобразования естественного языка в SQL запросы с поддержкой ролевых ограничений и векторной базы знаний (pgvector).

### Архитектура системы
```
Пользователь → Web Interface → Query Service → Vanna AI → Mock API → PostgreSQL
```

---

## 🏗️ Основные компоненты

### 1. **Web Interface Layer**

#### `src/simple_web_interface.py`
```python
/**
 * Упрощенный веб-интерфейс для NL→SQL системы
 * 
 * @author NL→SQL Team
 * @version 2.0.0
 * @since 2024-10-15
 * 
 * Основные функции:
 * - Генерация SQL из естественного языка
 * - Выполнение SQL с ролевыми ограничениями
 * - Отображение результатов в веб-интерфейсе
 * 
 * @see QueryService для логики генерации SQL
 * @see MockCustomerAPI для выполнения запросов
 */
class SimpleWebInterface:
    """
    FastAPI приложение для веб-интерфейса NL→SQL системы
    
    Endpoints:
    - GET / - Главная страница с интерфейсом
    - POST /generate-sql - Генерация SQL
    - POST /execute-sql - Выполнение SQL
    - GET /health - Проверка состояния
    """
```

**Ключевые методы:**
- `generate_sql()` - Генерация SQL через QueryService
- `execute_sql()` - Выполнение SQL через Mock API
- `fix_sql_for_mock_api()` - Исправление SQL для совместимости

---

### 2. **Query Service Layer**

#### `src/services/query_service.py`
```python
/**
 * Сервис для генерации SQL запросов
 * 
 * @author NL→SQL Team
 * @version 1.0.0
 * 
 * Основные функции:
 * - Интеграция с Vanna AI для генерации SQL
 * - Управление контекстом и базой знаний
 * - Обработка различных типов запросов
 * 
 * @see VannaAI для генерации SQL
 * @see VectorDB для семантического поиска
 */
class QueryService:
    """
    Основной сервис для генерации SQL запросов
    
    Поддерживаемые модели:
    - GPT-4o (через ProxyAPI)
    - Ollama (локальные модели)
    - Vanna AI (векторный поиск)
    """
```

**Ключевые методы:**
- `generate_sql()` - Основная генерация SQL
- `get_context()` - Получение контекста для запроса
- `normalize_sql()` - Нормализация SQL

---

### 3. **Vanna AI Integration**

#### `src/vanna/optimized_dual_pipeline.py`
```python
/**
 * Оптимизированный двойной пайплайн для Vanna AI
 * 
 * @author NL→SQL Team
 * @version 1.0.0
 * 
 * Архитектура:
 * - Семантический поиск по векторной БД
 * - Генерация SQL через LLM
 * - Валидация и оптимизация результатов
 * 
 * @see DocStructureVannaNative для нативной интеграции
 * @see VectorDBConfigs для конфигурации БД
 */
class OptimizedDualPipeline:
    """
    Двойной пайплайн: семантический поиск + генерация SQL
    
    Компоненты:
    1. Vector Search - поиск релевантной информации
    2. SQL Generation - генерация SQL через LLM
    3. Validation - проверка и исправление SQL
    """
```

#### `src/vanna/vanna_pgvector_native.py`
```python
/**
 * Нативная интеграция Vanna AI с pgvector
 * 
 * @author NL→SQL Team
 * @version 1.0.0
 * 
 * Особенности:
 * - Прямая работа с PostgreSQL + pgvector
 * - Семантический поиск по эмбеддингам
 * - Поддержка различных моделей эмбеддингов
 * 
 * @see DocStructureVectorDB для работы с БД
 * @see OpenAI_Chat для генерации SQL
 */
class DocStructureVannaNative:
    """
    Нативная реализация Vanna AI с pgvector
    
    Поддерживаемые модели:
    - text-embedding-ada-002 (OpenAI)
    - sentence-transformers (локальные)
    - Custom embeddings
    """
```

---

### 4. **Mock API Layer**

#### `src/mock_customer_api.py`
```python
/**
 * Mock API заказчика для отладки NL→SQL системы
 * 
 * @author NL→SQL Team
 * @version 1.0.0
 * 
 * Функции:
 * - Имитация API заказчика
 * - Применение ролевых ограничений
 * - Выполнение SQL с ограничениями
 * - Возврат результатов в формате заказчика
 * 
 * @see SQLExecuteRequest для структуры запросов
 * @see RoleRestrictions для применения ограничений
 */
class MockCustomerAPI:
    """
    Mock API для тестирования и отладки
    
    Endpoints:
    - POST /api/sql/execute - Выполнение SQL
    - POST /api/plan/execute - Выполнение плана
    - GET /health - Проверка состояния
    """
```

**Ключевые методы:**
- `execute_sql()` - Выполнение SQL с ролями
- `apply_role_restrictions()` - Применение ограничений
- `simulate_sql_execution()` - Имитация выполнения

---

### 5. **Utility Layer**

#### `src/utils/plan_sql_converter.py`
```python
/**
 * Конвертер между SQL и планами запросов
 * 
 * @author NL→SQL Team
 * @version 1.0.0
 * 
 * Функции:
 * - SQL → План (для передачи в Core Platform)
 * - План → SQL (для валидации)
 * - Нормализация и оптимизация
 * 
 * @see PlanStructure для структуры планов
 * @see SQLNormalizer для нормализации SQL
 */
class PlanSQLConverter:
    """
    Конвертер между SQL и планами запросов
    
    Поддерживаемые форматы:
    - PostgreSQL SQL
    - JSON планы
    - Структурированные планы
    """
```

#### `src/tools/generate_embeddings.py`
```python
/**
 * Генератор эмбеддингов для векторной БД
 * 
 * @author NL→SQL Team
 * @version 1.0.0
 * 
 * Функции:
 * - Генерация эмбеддингов для существующих записей
 * - Поддержка различных моделей эмбеддингов
 * - Батчевая обработка для производительности
 * 
 * @see EmbeddingGenerator для основной логики
 * @see OpenAI для генерации эмбеддингов
 */
class EmbeddingGenerator:
    """
    Генератор эмбеддингов для vanna_vectors
    
    Поддерживаемые модели:
    - text-embedding-ada-002 (OpenAI)
    - text-embedding-3-small (OpenAI)
    - sentence-transformers (локальные)
    """
```

---

## 🔧 Конфигурация системы

### Environment Variables
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

### Port Configuration
- **Simple Web Interface**: 3000
- **Mock Customer API**: 8080
- **Core API**: 8000
- **Streamlit UI**: 8501

---

## 📊 База знаний

### Структура данных
```
vanna_vectors:
├── id (SERIAL PRIMARY KEY)
├── content (TEXT) - Содержимое для поиска
├── content_type (VARCHAR) - Тип контента
├── metadata (JSONB) - Метаданные
├── embedding (VECTOR(1536)) - Вектор эмбеддинга
└── created_at (TIMESTAMP)
```

### Типы контента
- `documentation` - Документация схемы БД
- `question_sql` - Пары вопрос-ответ
- `ddl` - DDL скрипты
- `examples` - Примеры SQL

---

## 🚀 Запуск системы

### Основные сервисы
```bash
# 1. Simple Web Interface
uvicorn src.simple_web_interface:app --host 0.0.0.0 --port 3000

# 2. Mock Customer API
uvicorn src.mock_customer_api:mock_app --host 0.0.0.0 --port 8080

# 3. Core API (опционально)
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

### Скрипты для разработки
```bash
# Генерация эмбеддингов
python src/tools/generate_embeddings.py --dsn "postgresql://..." --api-key "sk-..."

# Тестирование моделей
python compare_ollama_models.py

# Отладка семантического поиска
python debug_semantic_search.py
```

---

## 📈 Метрики и мониторинг

### Ключевые метрики
- **SQL Quality**: % корректных SQL запросов
- **Response Time**: Среднее время генерации
- **Context Relevance**: % релевантной информации
- **Table Accuracy**: % использования реальных таблиц

### Логирование
- RAG logs: `logs/rag_*.log`
- SQL generation: `logs/sql_generation.log`
- Performance: `logs/performance.log`

---

## 🔍 Отладка и тестирование

### Тестовые команды
```bash
# Проверка здоровья сервисов
curl http://localhost:3000/health
curl http://localhost:8080/health

# Тестирование генерации SQL
curl -X POST http://localhost:3000/generate-sql \
  -d "question=покажи пользователей&role=admin&department=IT"

# Тестирование выполнения SQL
curl -X POST http://localhost:3000/execute-sql \
  -d "question=покажи пользователей&role=admin&department=IT"
```

### Отладочные скрипты
- `debug_semantic_search.py` - Отладка семантического поиска
- `test_semantic_rag.py` - Тестирование RAG системы
- `compare_ollama_models.py` - Сравнение моделей

---

## 📚 Дополнительные ресурсы

### Документация
- [Архитектура системы](docs/SYSTEM_ARCHITECTURE.md)
- [Методология обучения](docs/TRAINING_METHODOLOGY.md)
- [Поток данных SQL](docs/SQL_DATA_FLOW.md)

### Конфигурационные файлы
- `config.env` - Переменные окружения
- `docs/scripts/config.json` - Конфигурация системы
- `src/vanna/vector_db_configs.py` - Конфигурация векторных БД

---

**Версия документации**: 1.0.0  
**Дата обновления**: 2024-10-15  
**Автор**: NL→SQL Team


