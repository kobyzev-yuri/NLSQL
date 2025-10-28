# Руководство по настройке ролевых ограничений

## Обзор

Ролевые ограничения применяются в Mock Customer API (`src/mock_customer_api.py`) в функции `apply_role_restrictions()`.

## Текущая конфигурация

### 🔴 Роль: `user` (Пользователь)

**Принцип:** Пользователь видит только СВОИ данные

| Таблица | Ограничение | Описание |
|---------|-------------|----------|
| `equsers` | `login = '{login}'` | Только свой профиль |
| `tbl_principal_assignment` | `creationdatetime >= CURRENT_DATE - INTERVAL '1 month'` | Поручения за последний месяц |
| `tbl_business_unit` | `business_unit_name IS NOT NULL` | Только активные клиенты |
| `tbl_incoming_payments` | `payment_date >= CURRENT_DATE - INTERVAL '1 month'` | Платежи за последний месяц |

### 🟡 Роль: `manager` (Менеджер)

**Принцип:** Менеджер видит данные СВОЕГО отдела

| Таблица | Ограничение | Описание |
|---------|-------------|----------|
| `equsers` | `department = (SELECT id FROM eq_departments WHERE name = '{department}')` | Сотрудники своего отдела |
| `eq_departments` | `name = '{department}'` | Только свой отдел |
| `tbl_principal_assignment` | `creationdatetime >= CURRENT_DATE - INTERVAL '3 months'` | Поручения за последние 3 месяца |
| `tbl_business_unit` | Нет ограничений | Все клиенты |
| `tbl_incoming_payments` | `payment_date >= CURRENT_DATE - INTERVAL '6 months'` | Платежи за последние 6 месяцев |

### 🟢 Роль: `admin` (Администратор)

**Принцип:** Полный доступ БЕЗ ограничений

- Видит ВСЕ данные
- Видит ВСЕ таблицы
- Видит ВСЕ временные диапазоны

## Как добавить/изменить ограничения

### 1. Откройте файл
```bash
nano /mnt/ai/cnn/sql4A/src/mock_customer_api.py
```

### 2. Найдите функцию `apply_role_restrictions`
```python
def apply_role_restrictions(sql: str, login: str, role: str, department: str) -> str:
```

### 3. Примеры изменений

#### Пример 1: Добавить ограничение для новой таблицы

```python
elif role == "user":
    # ... существующие условия ...
    elif "from your_new_table" in sql_lower:
        sql = append_condition(sql, f"created_by = '{login}'")
```

#### Пример 2: Изменить временной диапазон

```python
# Было: 1 месяц
sql = append_condition(sql, f"creationdatetime >= CURRENT_DATE - INTERVAL '1 month'")

# Стало: 2 недели
sql = append_condition(sql, f"creationdatetime >= CURRENT_DATE - INTERVAL '2 weeks'")
```

#### Пример 3: Добавить ограничения для admin

```python
elif role == "admin":
    # Администратор видит данные всех, но только за последний год
    if "from tbl_principal_assignment" in sql_lower:
        sql = append_condition(sql, f"creationdatetime >= CURRENT_DATE - INTERVAL '1 year'")
```

#### Пример 4: Сложное условие с несколькими полями

```python
elif role == "manager":
    if "from tbl_principal_assignment" in sql_lower:
        # Менеджер видит поручения своего отдела И активные
        sql = append_condition(sql, f"department_id = (SELECT id FROM eq_departments WHERE name = '{department}')")
        sql = append_condition(sql, f"status = 'active'")
```

#### Пример 5: Ограничение по типу данных

```python
elif role == "user":
    if "from tbl_incoming_payments" in sql_lower:
        # Пользователь видит только свои платежи
        sql = append_condition(sql, f"payer_login = '{login}'")
        # И только подтвержденные
        sql = append_condition(sql, f"status = 'confirmed'")
```

### 4. Перезапустите Mock API

```bash
cd /mnt/ai/cnn/sql4A
./run_stack.sh restart mock_api
```

## Структура `append_condition`

Функция `append_condition` автоматически:
- Определяет есть ли уже `WHERE` в SQL
- Если есть → добавляет `AND условие`
- Если нет → добавляет `WHERE условие`

```python
def append_condition(base_sql: str, condition: str) -> str:
    if " where " in base_sql.lower():
        return f"{base_sql} AND {condition}"
    else:
        return f"{base_sql} WHERE {condition}"
```

## Доступные поля для ограничений

### Контекстные переменные:
- `login` - логин пользователя (например: "ivanov")
- `role` - роль (user/manager/admin)
- `department` - название отдела (например: "IT Department")

### SQL функции PostgreSQL:
- `CURRENT_DATE` - текущая дата
- `INTERVAL '1 month'` - временной интервал
- `IS NULL` / `IS NOT NULL` - проверка на NULL
- Подзапросы: `(SELECT ...)`

## Тестирование ограничений

### 1. Тест через Streamlit (порт 8501)
- Выберите роль в выпадающем списке
- Введите вопрос
- Проверьте "🔒 Финальный SQL (с ограничениями)"

### 2. Тест через Simple UI (порт 3000)
- Откройте http://localhost:3000
- Введите вопрос
- Проверьте "🔐 SQL с ролевыми ограничениями"

### 3. Тест через API напрямую

```bash
curl -X POST http://localhost:8081/api/sql/execute \
  -H "Content-Type: application/json" \
  -d '{
    "sql_template": "SELECT * FROM equsers",
    "user_context": {
      "login": "test_user",
      "role": "user",
      "department": "IT"
    },
    "request_id": "test"
  }' | jq .
```

## Логирование

Включено логирование всех применяемых ограничений:
```python
logger.info(f"Применение ограничений для роли: {role}, login: {login}")
```

Смотрите логи:
```bash
tail -f /mnt/ai/cnn/sql4A/logs/mock_api_8081.err
```

## Безопасность

⚠️ **ВАЖНО:**
1. Все ограничения применяются на уровне SQL (не на уровне приложения)
2. Mock API блокирует опасные операции: DROP, DELETE, TRUNCATE, ALTER, CREATE
3. Разрешены только SELECT запросы
4. SQL injection защита через параметризованные запросы

## Дополнительная кастомизация

Для сложной бизнес-логики заказчик может:

1. **Добавить новую роль:**
```python
elif role == "auditor":
    # Аудитор видит все, но только для чтения
    if "from tbl_incoming_payments" in sql_lower:
        sql = append_condition(sql, f"payment_date >= CURRENT_DATE - INTERVAL '3 years'")
```

2. **Использовать справочники из БД:**
```python
# Получить department_id из БД
async with db_pool.acquire() as conn:
    dept_id = await conn.fetchval(
        "SELECT id FROM eq_departments WHERE name = $1", 
        department
    )
sql = append_condition(sql, f"department = {dept_id}")
```

3. **Комбинировать условия:**
```python
if role == "manager" and department == "Finance":
    # Финансовые менеджеры имеют особые права
    sql = append_condition(sql, f"amount > 0")
```

## Контакты для вопросов

При необходимости изменения логики ограничений:
1. Обратитесь к разработчику системы
2. Предоставьте бизнес-требования
3. Протестируйте изменения на тестовой среде

