# API Reference (для разработчиков)

## 📋 Обзор

Система NL→SQL предоставляет REST API (FastAPI) и Python API для генерации и выполнения SQL по текстовому запросу.

---

## 🌐 Core REST API (FastAPI)

Base URL: `http://localhost:8000`

### Эндпоинты

#### `GET /`
Возвращает статус работы API и версию.

#### `GET /health`
Сводный статус компонентов (`api`, `vanna`, `customer_api`).

#### `POST /test-search`
Тест семантического поиска в векторной БД.
Body: `{ question, search_type?: semantic|ddl|documentation|examples, limit?: number }`

#### `POST /query`
Генерация SQL.
Body: `{ question, user_id?, role?, department?, context? }`
Returns: `{ sql, question, user_id }`

#### `POST /query/execute`
Генерация и немедленное выполнение SQL через Customer API.
Returns: `{ data, columns, row_count, execution_time, sql }`

#### `POST /training/example`
Добавление примера для обучения: `{ question, sql, user_id?, verified? }` → `{ success, example_id }`

#### `GET /training/status`
Статус обучения: `{ status, training_examples, last_training, model_version }`

---

## 🔧 Mock Customer API

**Base URL**: `http://localhost:8081`

### Endpoints

#### `GET /`
**Описание**: Корневой эндпоинт  
**Response**:
```json
{
    "message": "Mock Customer API работает",
    "version": "1.0.0",
    "description": "Mock API заказчика для отладки NL→SQL системы"
}
```

#### `POST /api/sql/execute`
**Описание**: Выполнение SQL с ролевыми ограничениями  
**Content-Type**: `application/json`

**Request Body**:
```json
{
    "sql_template": "SELECT * FROM equsers",
    "user_context": {
        "login": "admin",
        "role": "admin",
        "department": "IT"
    },
    "request_id": "unique_request_id"
}
```

**Response**:
```json
{
    "success": true,
    "sql_with_roles": "SELECT * FROM equsers WHERE deleted = FALSE",
    "data": [
        {
            "id": "uuid",
            "login": "user1",
            "email": "user1@example.com"
        }
    ],
    "columns": ["id", "login", "email"],
    "row_count": 1,
    "execution_time": 0.123,
    "restrictions_applied": ["deleted = FALSE"]
}
```

#### `POST /api/plan/execute`
**Описание**: Выполнение плана запроса  
**Content-Type**: `application/json`

**Request Body**:
```json
{
    "plan": {
        "tables": ["equsers"],
        "columns": ["*"],
        "conditions": ["deleted = FALSE"]
    },
    "user_context": {
        "login": "admin",
        "role": "admin",
        "department": "IT"
    },
    "request_id": "unique_request_id"
}
```

**Response**:
```json
{
    "success": true,
    "final_sql": "SELECT * FROM equsers WHERE deleted = FALSE",
    "data": [...],
    "columns": [...],
    "row_count": 1,
    "execution_time": 0.123,
    "restrictions_applied": ["deleted = FALSE"]
}
```

#### `GET /health`
**Описание**: Проверка состояния Mock API  
**Response**:
```json
{
    "status": "healthy",
    "timestamp": "2024-10-15T13:42:24.003335",
    "components": {
        "database": "connected",
        "permissions": "loaded"
    }
}
```

---

## 🔍 Query Service (Python API)

### `QueryService`
- `generate_sql(question: str, user_context: Dict[str, Any]) -> str`
- `add_training_example(question: str, sql: str, user_id: str, verified: bool=False)`
- `get_training_status() -> Dict[str, Any]`
- `test_vector_search(question: str, search_type: str = "semantic", limit: int = 5) -> List[Dict]`
- `is_ready() -> bool`

Зависимости: `SimpleOpenAISQL` (прямой GPT-4o), `create_semantic_vanna_client()` (семантический RAG).

---

## 🧠 Vanna / Пайплайны

**Библиотека:** [vanna-ai](https://github.com/vanna-ai/vanna) — система генерации SQL из естественного языка с RAG.

**Наши реализации на базе Vanna:**

- `src/vanna/vanna_pgvector_native.DocStructureVannaNative` — нативная интеграция VannaBase + PostgreSQL + ProxyAPI/OpenAI. Методы: `run_sql`, `get_training_plan_generic`, `train`, `generate_sql`.
- `src/vanna/optimized_dual_pipeline.OptimizedDualPipeline` — мультимодельная генерация (gpt4/sqlcoder/ollama) и тренировка. Методы: `generate_sql`, `train_on_schema`, `train_on_examples`, `get_usage_stats`, `health_check`.
- `src/vanna/enhanced_kb_agent.EnhancedKBAgent` — KB-агент поверх пайплайна. Методы: `train_agent`, `generate_sql`, `get_context_info`, `health_check`, `get_statistics`.
- Утилиты генерации: `src/vanna/simple_openai_sql.SimpleOpenAISQL` (OpenAI/ProxyAPI), `src/vanna/ollama_native_sql.OllamaNativeSQL` (нативный Ollama API).
- Семантический клиент: `src/vanna/vanna_semantic_fixed.create_semantic_vanna_client()` — `get_related_ddl`, `get_related_documentation`, `get_similar_question_sql`.

---

## 📊 Ошибки
- HTTP 4xx/5xx с сообщением об ошибке; глобальный обработчик возвращает JSON с полем `error`.

---

## 🚀 Примеры

### Python (FastAPI)
```python
import httpx

# Генерация SQL
async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/query",
        json={
            "question": "Покажи всех пользователей",
            "user_id": "test",
            "role": "admin",
            "department": "IT"
        }
    )
    result = response.json()
    print(f"Generated SQL: {result['sql']}")

# Выполнение SQL
async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/query/execute",
        json={
            "question": "Покажи всех пользователей",
            "user_id": "test",
            "role": "admin",
            "department": "IT"
        }
    )
    result = response.json()
    print(f"Rows: {result['row_count']}")
```

### cURL
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question":"Покажи всех пользователей","user_id":"test","role":"admin","department":"IT"}'

curl -X POST http://localhost:8000/query/execute \
  -H "Content-Type: application/json" \
  -d '{"question":"Покажи всех пользователей","user_id":"test","role":"admin","department":"IT"}'

curl http://localhost:8000/health
```

---

Версия: 2.1  
Дата: 2025-11-03










