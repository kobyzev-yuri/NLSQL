# Структура потока данных SQL

## Архитектура передачи SQL данных

```
┌──────────────┐
│  Vanna AI    │  Генерирует SQL из NL
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────────────┐
│  FastAPI (simple_web_interface.py)       │
│  1. Получает SQL от Vanna AI              │
│  2. Исправляет синтаксис для PostgreSQL   │
│  3. Передает в Mock API                   │
└──────┬───────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│  Mock API (mock_customer_api.py)         │
│  1. Получает SQL                          │
│  2. Применяет ролевые ограничения         │
│  3. Выполняет SQL                         │
│  4. Возвращает результаты                 │
└──────┬───────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│  UI (Streamlit / simple_web_interface)   │
│  Отображает все этапы SQL                 │
└──────────────────────────────────────────┘
```

## Структура данных в ответе API

### От Mock API к FastAPI

```json
{
  "success": true,
  "sql_template": "SELECT * FROM ... WHERE ...",  // Оригинальный SQL (который получил Mock API)
  "sql_with_roles": "SELECT * FROM ... WHERE ... AND owner_id = '...'",  // SQL с ролями
  "final_sql": "SELECT * FROM ... WHERE ... AND owner_id = '...'",  // Для совместимости
  "data": [...],
  "columns": [...],
  "row_count": 10,
  "execution_time": 0.15,
  "user_context": {...},
  "restrictions_applied": [...]
}
```

### От FastAPI к UI

```json
{
  "success": true,
  "sql_template": "SELECT * FROM ...",  // Оригинальный SQL от Vanna AI (до исправлений)
  "sql_corrected": "SELECT * FROM ...",  // Исправленный SQL (передается в Mock API)
  "sql_with_roles": "SELECT * FROM ... AND owner_id = '...'",  // SQL с ролями
  "sql": "SELECT * FROM ... AND owner_id = '...'",  // Для совместимости
  "final_sql": "SELECT * FROM ... AND owner_id = '...'",  // Для совместимости
  "data": [...],
  "columns": [...],
  "row_count": 10,
  "execution_time": 0.15,
  "restrictions": [...],
  "explanation": "...",
  "agent_type": "QueryService с KB + Mock API"
}
```

## Этапы обработки SQL

### 1. Генерация SQL (Vanna AI)

**Пример:**
```sql
SELECT *
FROM tbl_principal_assignment
WHERE creationdatetime >= NOW() - INTERVAL "1 month";
```

**Проблемы:**
- Двойные кавычки вместо одинарных
- Алиасы таблиц
- JOIN вместо LEFT JOIN

### 2. Исправление SQL (FastAPI)

**Исправления:**
```python
# Исправляем синтаксис PostgreSQL
sql = sql.replace('"7 days"', "'7 days'")
sql = sql.replace('"1 month"', "'1 month'")

# Убираем алиасы таблиц
sql = sql.replace('ti.', '')
sql = sql.replace('pa.', '')

# Заменяем JOIN на LEFT JOIN
sql = re.sub(r'JOIN\s+(eq_)?departments', r'LEFT JOIN \1departments', sql)
```

**Результат:**
```sql
SELECT *
FROM tbl_principal_assignment
WHERE creationdatetime >= NOW() - INTERVAL '1 month';
```

### 3. Применение ролей (Mock API)

**Роли:**
- **admin**: Полный доступ
- **manager**: Доступ к данным своего отдела
- **user**: Доступ только к своим данным

**Пример для роли `user`:**
```sql
SELECT *
FROM tbl_principal_assignment
WHERE creationdatetime >= NOW() - INTERVAL '1 month'
  AND owner_id = '1acae6e0-7808-4f87-9829-8b7fc0b4f98f';
```

## Отображение в UI

### simple_web_interface (HTML)

```html
<h4>📋 SQL Шаблон (оригинальный от Vanna AI):</h4>
<pre>${data.sql_template}</pre>

<h4>🔧 SQL Исправленный (передается в Mock API):</h4>
<pre>${data.sql_corrected}</pre>

<h4>🔐 SQL с ролевыми ограничениями:</h4>
<pre>${data.sql_with_roles}</pre>
```

### Streamlit

```python
st.markdown("### 📋 SQL Шаблон (оригинальный от Vanna AI)")
st.code(result.get('sql_template', ''), language='sql')

st.markdown("### 🔧 SQL Исправленный (передается в Mock API)")
st.code(result.get('sql_corrected', ''), language='sql')

st.markdown("### 🔐 SQL с ролевыми ограничениями")
st.code(result.get('sql_with_roles', ''), language='sql')
```

## Преимущества такой структуры

1. **Прозрачность**: Видны все этапы обработки SQL
2. **Отладка**: Легко найти проблемы на каждом этапе
3. **Обучение**: Понятно, как работает система
4. **Безопасность**: Видно, какие ограничения применены

## Непротиворечивость

- `sql_template` всегда содержит оригинальный SQL от Vanna AI
- `sql_corrected` всегда содержит исправленный SQL (передается в Mock API)
- `sql_with_roles` всегда содержит финальный SQL с ролями (выполняется в БД)
- Каждый компонент формируется в своем слое и передается дальше без изменений










