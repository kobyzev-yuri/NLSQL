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
Добавление примера Q/A пары для обучения векторной базы знаний.

**Рекомендуется использовать:** `KBTrainingClient` из `src/tools/kb_training_client.py` для единообразного доступа к этому эндпоинту.

**Параметры запроса:**
- `question` (str, обязательный) - вопрос на естественном языке
- `sql` (str, обязательный) - SQL запрос (или оптимизированный SQL)
- `user_id` (str, обязательный) - идентификатор пользователя
- `verified` (bool, опционально) - верифицирован ли пример
- `sql_basic` (str, опционально) - базовый SQL для сравнения (при оптимизации)
- `sql_optimized` (str, опционально) - оптимизированный SQL
- `improvement` (str, опционально) - описание улучшения производительности
- `domain` (str, опционально) - домен запроса (payments, users, assignments, reports)
- `tags` (List[str], опционально) - теги для категоризации

**Ответ:**
- `success` (bool) - успешность операции
- `example_id` (str) - идентификатор добавленного примера
- `explain_plan` (dict, опционально) - EXPLAIN план для SQL
- `explain_plan_basic` (dict, опционально) - EXPLAIN план для базового SQL
- `optimization_validated` (bool, опционально) - результат валидации оптимизации
- `cost_improvement_percent` (float, опционально) - процент улучшения стоимости запроса
- `optimization_warning` (str, опционально) - предупреждение о валидации

**Особенности:**
- Автоматически генерирует EXPLAIN планы для оптимизированных SQL
- Валидирует оптимизацию через сравнение планов выполнения
- Сохраняет в векторную базу `vanna_vectors` с типом `content_type='question_sql'`

**Пример использования через KBTrainingClient:**
```python
from src.tools.kb_training_client import KBTrainingClient

client = KBTrainingClient(api_base_url="http://localhost:8000")
result = client.add_training_example(
    question="Покажи всех пользователей",
    sql="SELECT id, login, email FROM equsers WHERE deleted = FALSE",
    sql_basic="SELECT * FROM equsers",
    improvement="50% меньше данных",
    user_id="my_script"
)
```

**См. также:** [KB_TRAINING_UNIFICATION.md](KB_TRAINING_UNIFICATION.md), [TRAINING_GUIDE.md](TRAINING_GUIDE.md)

#### `POST /training/ddl`
Добавление DDL statements для обучения векторной базы знаний.

**Рекомендуется использовать:** `KBTrainingClient.add_ddl_statements()` или `KBTrainingClient.add_ddl()` из `src/tools/kb_training_client.py`.

**Параметры запроса:**
- `ddl_statements` (List[Dict], обязательный) - список DDL statements:
  - `ddl` (str, обязательный) - DDL оператор (CREATE TABLE ...)
  - `table_name` (str, обязательный) - имя таблицы
  - `source` (str, обязательный) - источник DDL (information_schema, manual, migration, etc.)
  - `version` (str, опционально) - версия схемы
  - `metadata` (Dict, опционально) - дополнительные метаданные
- `user_id` (str, обязательный) - идентификатор пользователя/скрипта

**Ответ:**
- `success` (bool) - успешность операции
- `added` (int) - количество добавленных записей
- `updated` (int) - количество обновленных записей
- `failed` (int) - количество неудачных операций
- `errors` (List[str]) - список ошибок

**Особенности:**
- Транзакционность: все операции выполняются в транзакции с откатом при ошибках
- Уникальность: по `table_name` (одна таблица = одна запись)
- Логирование изменений: при обновлении существующей записи логируются детали изменений
- Автоматическая генерация эмбеддингов: выполняется в рамках транзакции

**Пример использования:**
```python
from src.tools.kb_training_client import KBTrainingClient

client = KBTrainingClient(api_base_url="http://localhost:8000")
result = client.add_ddl(
    ddl="CREATE TABLE equsers (id SERIAL PRIMARY KEY, login VARCHAR(50));",
    table_name="equsers",
    source="information_schema",
    version="2024-11-26"
)
```

#### `POST /training/documentation`
Добавление документации для обучения векторной базы знаний.

**Рекомендуется использовать:** `KBTrainingClient.add_documentation()` или `KBTrainingClient.add_doc()` из `src/tools/kb_training_client.py`.

**Параметры запроса:**
- `documents` (List[Dict], обязательный) - список документов:
  - `content` (str, обязательный) - текст документации
  - `title` (str, обязательный) - название документа
  - `source` (str, опционально) - источник документации
  - `domain` (str, опционально) - домен (users, payments, assignments, etc.)
  - `tags` (List[str], опционально) - список тегов для категоризации
  - `metadata` (Dict, опционально) - дополнительные метаданные
- `user_id` (str, обязательный) - идентификатор пользователя/скрипта

**Ответ:**
- `success` (bool) - успешность операции
- `added` (int) - количество добавленных записей
- `updated` (int) - количество обновленных записей
- `failed` (int) - количество неудачных операций
- `errors` (List[str]) - список ошибок

**Особенности:**
- Транзакционность: все операции выполняются в транзакции с откатом при ошибках
- Уникальность: по `title` (один документ = одна запись)
- Логирование изменений: при обновлении существующей записи логируются детали изменений
- Автоматическая генерация эмбеддингов: выполняется в рамках транзакции

**Пример использования:**
```python
from src.tools.kb_training_client import KBTrainingClient

client = KBTrainingClient(api_base_url="http://localhost:8000")
result = client.add_doc(
    content="Use case: получение списка активных пользователей...",
    title="Активные пользователи",
    source="internal_docs",
    domain="users",
    tags=["use_case", "users"]
)
```

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

**Примечание:** Конвертация плана в SQL выполняется через `src/utils/plan_sql_converter.py` (класс `PlanToSQLConverter`). Заказчик может заменить эту реализацию на свою собственную, сохранив интерфейс класса для совместимости.

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
- `add_training_example(question: str, sql: str, user_id: str, verified: bool=False, **kwargs) -> Dict[str, Any]`
  - Поддерживает параметры: `sql_basic`, `sql_optimized`, `improvement`, `domain`, `tags`
  - Автоматически генерирует EXPLAIN планы для оптимизированных SQL
  - Валидирует оптимизацию через сравнение планов выполнения
- `get_training_status() -> Dict[str, Any]`
- `test_vector_search(question: str, search_type: str = "semantic", limit: int = 5) -> List[Dict]`
- `is_ready() -> bool`

Зависимости: `SimpleOpenAISQL` (прямой GPT-4o), `create_semantic_vanna_client()` (семантический RAG).

### `KBTrainingClient` (унифицированный клиент для обучения KB)
**Модуль:** `src/tools/kb_training_client.py`

**Методы:**
- `add_training_example(question: str, sql: str, **kwargs) -> Dict[str, Any]` - добавление одного примера через API
- `add_from_json_file(json_file: Path, user_id: str, verbose: bool = True) -> Dict[str, int]` - массовое добавление из JSON файла
- `add_training_examples_batch(examples: List[Dict], user_id: str, verbose: bool = True) -> Dict[str, int]` - массовое добавление из списка
- `check_api_connection() -> bool` - проверка доступности Core API

**Использование:**
```python
from src.tools.kb_training_client import KBTrainingClient

client = KBTrainingClient(api_base_url="http://localhost:8000")
client.add_training_example(question="...", sql="...")
```

**См. также:** [KB_TRAINING_UNIFICATION.md](KB_TRAINING_UNIFICATION.md)

---

## 🧠 Vanna / Пайплайны

**Библиотека:** [vanna-ai](https://github.com/vanna-ai/vanna) — система генерации SQL из естественного языка с RAG.

**Наши реализации на базе Vanna:**

- `src/vanna/vanna_pgvector_native.DocStructureVannaNative` — нативная интеграция VannaBase + PostgreSQL + ProxyAPI/OpenAI. Методы: `run_sql`, `get_training_plan_generic`, `train`, `generate_sql`, `add_ddl`, `add_documentation`, `add_question_sql` (legacy для DDL/документации, для Q/A пар рекомендуется использовать `KBTrainingClient`).
- `src/vanna/optimized_dual_pipeline.OptimizedDualPipeline` — мультимодельная генерация (gpt4/sqlcoder/ollama) и тренировка. Методы: `generate_sql`, `train_on_schema`, `train_on_examples`, `get_usage_stats`, `health_check`.
- `src/vanna/enhanced_kb_agent.EnhancedKBAgent` — KB-агент поверх пайплайна. Методы: `train_agent`, `generate_sql`, `get_context_info`, `health_check`, `get_statistics`.
- Утилиты генерации: `src/vanna/simple_openai_sql.SimpleOpenAISQL` (OpenAI/ProxyAPI), `src/vanna/ollama_native_sql.OllamaNativeSQL` (нативный Ollama API).
- Семантический клиент: `src/vanna/vanna_semantic_fixed.create_semantic_vanna_client()` — `get_related_ddl`, `get_related_documentation`, `get_similar_question_sql`.
- **Унифицированный клиент обучения:** `src/tools/kb_training_client.KBTrainingClient` — единый интерфейс для обучения Q/A пар через API `/training/example`. См. [KB_TRAINING_UNIFICATION.md](KB_TRAINING_UNIFICATION.md).

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










