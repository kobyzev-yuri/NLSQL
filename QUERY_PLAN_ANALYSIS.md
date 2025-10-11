# Анализ плана запроса PostgreSQL

## 🎯 Понял! План = Query Plan из PostgreSQL

Согласно [документации PostgreSQL](https://www.postgresql.org/docs/current/using-explain.html), план запроса - это структурированное описание того, как PostgreSQL будет выполнять SQL запрос.

## 📋 Что такое план запроса в PostgreSQL

### Структура плана:
```
┌─────────────────────────────────────────────────────────┐
│                    ПЛАН ЗАПРОСА                         │
│  ┌─────────────────┐  ┌─────────────────┐              │
│  │   Узлы плана    │  │   Операции      │              │
│  │   (Plan Nodes)  │  │   (Operations)  │              │
│  └─────────────────┘  └─────────────────┘              │
│  ┌─────────────────┐  ┌─────────────────┐              │
│  │   Стоимость     │  │   Оценки        │              │
│  │   (Cost)        │  │   (Estimates)   │              │
│  └─────────────────┘  └─────────────────┘              │
└─────────────────────────────────────────────────────────┘
```

### Пример плана из документации:
```sql
EXPLAIN SELECT * FROM tenk1 WHERE unique1 < 100;
```

**Результат:**
```
                                  QUERY PLAN
-------------------------------------------------------------------------------
 Bitmap Heap Scan on tenk1  (cost=5.06..224.98 rows=100 width=244)
   Recheck Cond: (unique1 < 100)
   ->  Bitmap Index Scan on tenk1_unique1  (cost=0.00..5.04 rows=100 width=0)
         Index Cond: (unique1 < 100)
```

## 🔄 Поток данных в нашем проекте

### Теперь понятно из ТЗ:
```
Пользователь → API → LLM → План запроса → Core Platform → SQL → PostgreSQL → Результат
```

### Детализация:
1. **LLM генерирует план запроса** (структурированное описание операций)
2. **Core Platform получает план** и добавляет ролевые ограничения
3. **Core Platform генерирует SQL** из плана
4. **PostgreSQL выполняет SQL** и возвращает результат

## 📊 Форматы плана в PostgreSQL

### 1. Текстовый формат (по умолчанию):
```
 Seq Scan on tenk1  (cost=0.00..445.00 rows=10000 width=244)
```

### 2. JSON формат:
```sql
EXPLAIN (FORMAT JSON) SELECT * FROM tenk1;
```

### 3. XML формат:
```sql
EXPLAIN (FORMAT XML) SELECT * FROM tenk1;
```

## 🤔 Вопросы для уточнения

### 1. Какой формат плана генерирует LLM?
**❓ ВОПРОС:** LLM должен генерировать план в каком формате?
- JSON (как в PostgreSQL EXPLAIN FORMAT JSON)?
- XML (как в PostgreSQL EXPLAIN FORMAT XML)?
- Собственный формат?

### 2. Что содержит план от LLM?
**❓ ВОПРОС:** План должен содержать:
- Структуру операций (Scan, Join, Sort)?
- Таблицы и поля?
- Условия фильтрации?
- Оценки стоимости?

### 3. Как Core Platform обрабатывает план?
**❓ ВОПРОС:** Core Platform:
- Парсит план и добавляет ролевые ограничения?
- Генерирует SQL из плана?
- Выполняет SQL или возвращает готовый SQL?

## 💡 Предположения

### Возможная структура плана от LLM:
```json
{
  "plan": {
    "type": "SELECT",
    "tables": ["orders", "customers"],
    "columns": ["order_id", "customer_name", "order_date"],
    "conditions": [
      {
        "column": "order_date",
        "operator": ">=",
        "value": "2025-01-01"
      }
    ],
    "joins": [
      {
        "type": "INNER",
        "table1": "orders",
        "table2": "customers",
        "condition": "orders.customer_id = customers.id"
      }
    ],
    "grouping": null,
    "sorting": [
      {
        "column": "order_date",
        "direction": "DESC"
      }
    ]
  }
}
```

### Core Platform добавляет:
```json
{
  "role_restrictions": {
    "user_role": "manager",
    "branch_id": 123,
    "allowed_tables": ["orders", "customers"],
    "row_level_security": {
      "orders": "branch_id = 123",
      "customers": "branch_id = 123"
    }
  }
}
```

## 🎯 Следующие шаги

1. **Уточнить формат плана** - JSON/XML/собственный?
2. **Определить структуру плана** - что должно содержать?
3. **Понять API Core Platform** - как передается план?
4. **Создать прототип** генерации плана LLM

## ❓ Критические вопросы для заказчика

1. **В каком формате LLM должен генерировать план?** (JSON/XML/собственный)
2. **Что должно содержать в плане?** (таблицы, поля, условия, операции)
3. **Какой API у Core Platform** для обработки планов?
4. **Есть ли примеры планов** которые должна генерировать система?
5. **Как Core Platform добавляет ролевые ограничения** в план?



