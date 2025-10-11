# Формат плана PostgreSQL для LLM

## 🎯 Формат плана = Стандартный PostgreSQL EXPLAIN

LLM должен генерировать план в стандартном формате PostgreSQL EXPLAIN.

## 📋 Доступные форматы в PostgreSQL

### 1. JSON формат (рекомендуемый для API)
```sql
EXPLAIN (FORMAT JSON) SELECT * FROM orders WHERE order_date >= '2025-01-01';
```

**Результат:**
```json
[
  {
    "Plan": {
      "Node Type": "Seq Scan",
      "Relation Name": "orders",
      "Alias": "orders",
      "Startup Cost": 0.00,
      "Total Cost": 25.00,
      "Plan Rows": 1000,
      "Plan Width": 244,
      "Filter": "(order_date >= '2025-01-01'::date)"
    }
  }
]
```

### 2. XML формат
```sql
EXPLAIN (FORMAT XML) SELECT * FROM orders WHERE order_date >= '2025-01-01';
```

**Результат:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<explain xmlns="http://www.postgresql.org/2009/explain">
  <Query>
    <Plan>
      <Node-Type>Seq Scan</Node-Type>
      <Relation-Name>orders</Relation-Name>
      <Alias>orders</Alias>
      <Startup-Cost>0.00</Startup-Cost>
      <Total-Cost>25.00</Total-Cost>
      <Plan-Rows>1000</Plan-Rows>
      <Plan-Width>244</Plan-Width>
      <Filter>(order_date &gt;= '2025-01-01'::date)</Filter>
    </Plan>
  </Query>
</explain>
```

### 3. YAML формат
```sql
EXPLAIN (FORMAT YAML) SELECT * FROM orders WHERE order_date >= '2025-01-01';
```

## 🔄 Поток данных с PostgreSQL форматом

```
Пользователь → API → LLM → PostgreSQL Plan (JSON/XML) → Core Platform → SQL → PostgreSQL → Результат
```

### Детализация:
1. **LLM генерирует план** в стандартном PostgreSQL формате
2. **Core Platform получает план** и добавляет ролевые ограничения
3. **Core Platform генерирует SQL** из плана
4. **PostgreSQL выполняет SQL** и возвращает результат

## 📊 Примеры планов для разных запросов

### Простой SELECT:
```json
[
  {
    "Plan": {
      "Node Type": "Seq Scan",
      "Relation Name": "orders",
      "Alias": "orders",
      "Startup Cost": 0.00,
      "Total Cost": 25.00,
      "Plan Rows": 1000,
      "Plan Width": 244
    }
  }
]
```

### SELECT с условием:
```json
[
  {
    "Plan": {
      "Node Type": "Seq Scan",
      "Relation Name": "orders",
      "Alias": "orders",
      "Startup Cost": 0.00,
      "Total Cost": 25.00,
      "Plan Rows": 100,
      "Plan Width": 244,
      "Filter": "(order_date >= '2025-01-01'::date)"
    }
  }
]
```

### JOIN запрос:
```json
[
  {
    "Plan": {
      "Node Type": "Hash Join",
      "Startup Cost": 0.00,
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

## 🤔 Вопросы для уточнения

### 1. Какой формат предпочтительнее?
**❓ ВОПРОС:** LLM должен генерировать план в каком формате?
- JSON (удобно для API)
- XML (стандартный)
- YAML (читаемый)

### 2. Как Core Platform обрабатывает план?
**❓ ВОПРОС:** Core Platform:
- Парсит PostgreSQL план и добавляет ролевые ограничения?
- Генерирует SQL из плана?
- Выполняет SQL или возвращает готовый SQL?

### 3. Ролевые ограничения в плане
**❓ ВОПРОС:** Как Core Platform добавляет ролевые ограничения?
- Модифицирует существующий план?
- Создает новый план с ограничениями?
- Добавляет фильтры в план?

## 💡 Предполагаемая работа LLM

### Входные данные для LLM:
- Естественный язык: "Покажи заказы за последние 3 дня"
- Схема базы данных (каталог схем)
- Контекст пользователя (роль, права)

### Выходные данные LLM:
- План в стандартном PostgreSQL формате (JSON/XML)
- Готовый для передачи в Core Platform

### Пример промпта для LLM:
```
Сгенерируй план PostgreSQL для запроса: "Покажи заказы за последние 3 дня"

Схема базы данных:
- Таблица: orders (id, customer_id, order_date, amount)
- Таблица: customers (id, name, email)

Верни план в формате JSON как EXPLAIN (FORMAT JSON) в PostgreSQL.
```

## 🎯 Следующие шаги

1. **Выбрать формат плана** - JSON/XML/YAML
2. **Создать промпт для LLM** - генерация PostgreSQL плана
3. **Протестировать генерацию** - простые запросы
4. **Интегрировать с Core Platform** - передача плана

## ❓ Критические вопросы для заказчика

1. **Какой формат плана предпочтительнее?** (JSON/XML/YAML)
2. **Как Core Platform обрабатывает план?** (парсинг, модификация, генерация SQL)
3. **Есть ли примеры планов** которые должна генерировать система?
4. **Как тестировать генерацию планов** LLM?



