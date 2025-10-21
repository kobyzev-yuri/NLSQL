# API Reference - NL→SQL System

## 📋 Обзор API

Система NL→SQL предоставляет REST API для генерации и выполнения SQL запросов из естественного языка.

---

## 🌐 Simple Web Interface API

**Base URL**: `http://localhost:3000`

### Endpoints

#### `GET /`
**Описание**: Главная страница с веб-интерфейсом  
**Response**: HTML страница с интерфейсом

```html
<!DOCTYPE html>
<html lang="ru">
<head>
    <title>NL→SQL Простой Интерфейс</title>
</head>
<body>
    <!-- Веб-интерфейс для ввода вопросов -->
</body>
</html>
```

#### `POST /generate-sql`
**Описание**: Генерация SQL из естественного языка  
**Content-Type**: `application/x-www-form-urlencoded`

**Parameters**:
- `question` (string, required) - Вопрос на русском языке
- `role` (string, optional) - Роль пользователя (admin/manager/user)
- `department` (string, optional) - Отдел пользователя

**Response**:
```json
{
    "success": true,
    "sql": "SELECT * FROM equsers WHERE deleted = FALSE",
    "plan": {
        "tables": ["equsers"],
        "columns": ["*"],
        "conditions": ["deleted = FALSE"]
    },
    "sql_template": "SELECT * FROM equsers",
    "final_sql": "SELECT * FROM equsers WHERE deleted = FALSE",
    "restrictions": ["deleted = FALSE"],
    "explanation": "SQL сгенерирован QueryService с KB",
    "agent_type": "QueryService с KB"
}
```

#### `POST /execute-sql`
**Описание**: Выполнение SQL запроса  
**Content-Type**: `application/x-www-form-urlencoded`

**Parameters**:
- `question` (string, required) - Вопрос на русском языке
- `role` (string, optional) - Роль пользователя
- `department` (string, optional) - Отдел пользователя

**Response**:
```json
{
    "success": true,
    "sql_template": "SELECT * FROM equsers",
    "sql_corrected": "SELECT * FROM equsers WHERE deleted = FALSE",
    "sql_with_roles": "SELECT * FROM equsers WHERE deleted = FALSE AND owner_id = '...'",
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
    "restrictions": ["deleted = FALSE", "owner_id = '...'"],
    "explanation": "SQL выполнен успешно. Найдено 1 записей.",
    "agent_type": "QueryService с KB + Mock API"
}
```

#### `GET /health`
**Описание**: Проверка состояния системы  
**Response**:
```json
{
    "status": "healthy",
    "agent": "Vanna AI + ProxyAPI + pgvector"
}
```

---

## 🔧 Mock Customer API

**Base URL**: `http://localhost:8080`

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

## 🔍 Query Service API

### Класс `QueryService`

#### `generate_sql(question: str, context: dict) -> str`
**Описание**: Генерация SQL из естественного языка  
**Parameters**:
- `question` (str) - Вопрос на русском языке
- `context` (dict) - Контекст запроса

**Returns**: SQL запрос (str)

**Example**:
```python
service = QueryService()
sql = await service.generate_sql("покажи пользователей", {})
# Returns: "SELECT * FROM equsers WHERE deleted = FALSE"
```

#### `get_context(question: str) -> str`
**Описание**: Получение контекста для запроса  
**Parameters**:
- `question` (str) - Вопрос на русском языке

**Returns**: Контекст для генерации SQL (str)

---

## 🧠 Vanna AI Integration

### Класс `DocStructureVannaNative`

#### `generate_sql(question: str) -> str`
**Описание**: Генерация SQL через Vanna AI  
**Parameters**:
- `question` (str) - Вопрос на русском языке

**Returns**: SQL запрос (str)

#### `get_related_ddl(question: str) -> List[str]`
**Описание**: Получение релевантных DDL скриптов  
**Parameters**:
- `question` (str) - Вопрос на русском языке

**Returns**: Список DDL скриптов (List[str])

#### `get_related_documentation(question: str) -> List[str]`
**Описание**: Получение релевантной документации  
**Parameters**:
- `question` (str) - Вопрос на русском языке

**Returns**: Список документации (List[str])

---

## 🔧 Utility Functions

### `src/utils/plan_sql_converter.py`

#### `sql_to_plan(sql: str) -> dict`
**Описание**: Конвертация SQL в план запроса  
**Parameters**:
- `sql` (str) - SQL запрос

**Returns**: План запроса (dict)

**Example**:
```python
plan = sql_to_plan("SELECT * FROM equsers WHERE deleted = FALSE")
# Returns: {
#     "tables": ["equsers"],
#     "columns": ["*"],
#     "conditions": ["deleted = FALSE"]
# }
```

#### `plan_to_sql(plan: dict) -> str`
**Описание**: Конвертация плана в SQL  
**Parameters**:
- `plan` (dict) - План запроса

**Returns**: SQL запрос (str)

### `src/tools/generate_embeddings.py`

#### `EmbeddingGenerator.generate_embeddings(batch_size: int, dry_run: bool)`
**Описание**: Генерация эмбеддингов для существующих записей  
**Parameters**:
- `batch_size` (int) - Размер батча для обработки
- `dry_run` (bool) - Только показать что будет сделано

**Example**:
```python
generator = EmbeddingGenerator(dsn, api_key)
await generator.generate_embeddings(batch_size=100, dry_run=False)
```

---

## 📊 Error Handling

### HTTP Status Codes

- `200` - Успешный запрос
- `400` - Неверные параметры запроса
- `500` - Внутренняя ошибка сервера

### Error Response Format

```json
{
    "success": false,
    "error": "Описание ошибки",
    "details": "Дополнительные детали (опционально)"
}
```

### Common Errors

#### `QueryService не инициализирован`
**Причина**: Проблемы с инициализацией QueryService  
**Решение**: Проверить конфигурацию и подключение к БД

#### `Mock API недоступен`
**Причина**: Mock API не запущен или недоступен  
**Решение**: Запустить Mock API на порту 8080

#### `Не удалось сгенерировать SQL`
**Причина**: Проблемы с LLM или контекстом  
**Решение**: Проверить API ключи и конфигурацию

---

## 🚀 Quick Start Examples

### Python Client Example

```python
import httpx

# Генерация SQL
async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:3000/generate-sql",
        data={
            "question": "покажи пользователей",
            "role": "admin",
            "department": "IT"
        }
    )
    result = response.json()
    print(f"Generated SQL: {result['sql']}")

# Выполнение SQL
async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:3000/execute-sql",
        data={
            "question": "покажи пользователей",
            "role": "admin",
            "department": "IT"
        }
    )
    result = response.json()
    print(f"Results: {result['data']}")
```

### cURL Examples

```bash
# Генерация SQL
curl -X POST http://localhost:3000/generate-sql \
  -d "question=покажи пользователей&role=admin&department=IT"

# Выполнение SQL
curl -X POST http://localhost:3000/execute-sql \
  -d "question=покажи пользователей&role=admin&department=IT"

# Проверка здоровья
curl http://localhost:3000/health
```

---

**Версия API**: 2.0.0  
**Дата обновления**: 2024-10-15





