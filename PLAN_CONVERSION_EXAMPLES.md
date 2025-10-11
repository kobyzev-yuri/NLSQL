# Конвертация плана PostgreSQL в JSON

## 🎯 Использование EXPLAIN (FORMAT JSON)

Для получения плана в JSON формате используется команда:
```sql
EXPLAIN (FORMAT JSON) SELECT * FROM your_table WHERE your_column = 'value';
```

## 📋 Примеры конвертации

### 1. Простой SELECT
**Текстовый план:**
```
 Seq Scan on tenk1  (cost=0.00..470.00 rows=7000 width=244)
   Filter: (unique1 < 7000)
```

**JSON план:**
```sql
EXPLAIN (FORMAT JSON) SELECT * FROM tenk1 WHERE unique1 < 7000;
```

**Результат:**
```json
[
  {
    "Plan": {
      "Node Type": "Seq Scan",
      "Relation Name": "tenk1",
      "Alias": "tenk1",
      "Startup Cost": 0.00,
      "Total Cost": 470.00,
      "Plan Rows": 7000,
      "Plan Width": 244,
      "Filter": "(unique1 < 7000)"
    }
  }
]
```

### 2. JOIN запрос
**Текстовый план:**
```
 Hash Join  (cost=25.00..50.00 rows=1000 width=488)
   Hash Cond: (orders.customer_id = customers.id)
   ->  Seq Scan on orders  (cost=0.00..25.00 rows=1000 width=244)
   ->  Hash  (cost=25.00..25.00 rows=1000 width=244)
         ->  Seq Scan on customers  (cost=0.00..25.00 rows=1000 width=244)
```

**JSON план:**
```sql
EXPLAIN (FORMAT JSON) 
SELECT o.*, c.name 
FROM orders o 
JOIN customers c ON o.customer_id = c.id;
```

**Результат:**
```json
[
  {
    "Plan": {
      "Node Type": "Hash Join",
      "Startup Cost": 25.00,
      "Total Cost": 50.00,
      "Plan Rows": 1000,
      "Plan Width": 488,
      "Hash Cond": "(orders.customer_id = customers.id)",
      "Plans": [
        {
          "Node Type": "Seq Scan",
          "Relation Name": "orders",
          "Alias": "orders",
          "Startup Cost": 0.00,
          "Total Cost": 25.00,
          "Plan Rows": 1000,
          "Plan Width": 244
        },
        {
          "Node Type": "Hash",
          "Startup Cost": 0.00,
          "Total Cost": 25.00,
          "Plan Rows": 1000,
          "Plan Width": 244,
          "Plans": [
            {
              "Node Type": "Seq Scan",
              "Relation Name": "customers",
              "Alias": "customers",
              "Startup Cost": 0.00,
              "Total Cost": 25.00,
              "Plan Rows": 1000,
              "Plan Width": 244
            }
          ]
        }
      ]
    }
  }
]
```

### 3. Сортировка и группировка
**Текстовый план:**
```
 Sort  (cost=25.00..27.50 rows=1000 width=244)
   Sort Key: order_date DESC
   ->  Seq Scan on orders  (cost=0.00..25.00 rows=1000 width=244)
```

**JSON план:**
```sql
EXPLAIN (FORMAT JSON) 
SELECT * FROM orders 
ORDER BY order_date DESC;
```

**Результат:**
```json
[
  {
    "Plan": {
      "Node Type": "Sort",
      "Startup Cost": 25.00,
      "Total Cost": 27.50,
      "Plan Rows": 1000,
      "Plan Width": 244,
      "Sort Key": ["order_date DESC"],
      "Plans": [
        {
          "Node Type": "Seq Scan",
          "Relation Name": "orders",
          "Alias": "orders",
          "Startup Cost": 0.00,
          "Total Cost": 25.00,
          "Plan Rows": 1000,
          "Plan Width": 244
        }
      ]
    }
  }
]
```

## 🔄 Поток данных в нашем проекте

### 1. LLM генерирует план
**Вход:** "Покажи заказы за последние 3 дня"  
**Выход:** План в JSON формате (как результат EXPLAIN FORMAT JSON)

### 2. Передача в Core Platform
```json
{
  "query_plan": [
    {
      "Plan": {
        "Node Type": "Seq Scan",
        "Relation Name": "orders",
        "Filter": "(order_date >= '2025-01-01'::date)"
      }
    }
  ],
  "user_context": {
    "user_id": "123",
    "role": "manager",
    "branch_id": "456"
  }
}
```

### 3. Core Platform обрабатывает
- Парсит план
- Добавляет ролевые ограничения
- Генерирует SQL
- Выполняет запрос

## 💡 Примеры для тестирования LLM

### Простые запросы:
```sql
-- 1. Простой SELECT
EXPLAIN (FORMAT JSON) SELECT * FROM orders;

-- 2. SELECT с условием
EXPLAIN (FORMAT JSON) SELECT * FROM orders WHERE status = 'completed';

-- 3. SELECT с сортировкой
EXPLAIN (FORMAT JSON) SELECT * FROM orders ORDER BY order_date DESC;

-- 4. SELECT с лимитом
EXPLAIN (FORMAT JSON) SELECT * FROM orders LIMIT 10;
```

### Сложные запросы:
```sql
-- 5. JOIN
EXPLAIN (FORMAT JSON) 
SELECT o.*, c.name 
FROM orders o 
JOIN customers c ON o.customer_id = c.id;

-- 6. GROUP BY
EXPLAIN (FORMAT JSON) 
SELECT customer_id, COUNT(*) 
FROM orders 
GROUP BY customer_id;

-- 7. Подзапрос
EXPLAIN (FORMAT JSON) 
SELECT * FROM orders 
WHERE customer_id IN (
  SELECT id FROM customers WHERE city = 'Moscow'
);
```

## 🎯 Задачи для LLM

### 1. Генерация плана
LLM должен генерировать план в том же формате, что и `EXPLAIN (FORMAT JSON)`.

### 2. Промпт для LLM
```
Сгенерируй план PostgreSQL для запроса: "{user_query}"

Схема базы данных:
{table_schema}

Верни план в формате JSON, точно как результат команды:
EXPLAIN (FORMAT JSON) {sql_query}

Пример формата:
[
  {
    "Plan": {
      "Node Type": "Seq Scan",
      "Relation Name": "table_name",
      "Startup Cost": 0.00,
      "Total Cost": 25.00,
      "Plan Rows": 1000,
      "Plan Width": 244
    }
  }
]
```

## ❓ Вопросы для уточнения

1. **Как тестировать генерацию планов** LLM?
2. **Какие примеры запросов** использовать для тестирования?
3. **Как валидировать** корректность сгенерированных планов?
4. **Есть ли ограничения** на сложность планов?



