# Опции EXPLAIN для генерации планов

## 🎯 Комбинации опций EXPLAIN

### Базовые форматы:
```sql
EXPLAIN (FORMAT JSON) SELECT * FROM your_table WHERE your_column = 'value';
EXPLAIN (FORMAT XML) SELECT * FROM your_table WHERE your_column = 'value';
EXPLAIN (FORMAT YAML) SELECT * FROM your_table WHERE your_column = 'value';
```

### Расширенные опции:
- **ANALYZE** - выполняет запрос и показывает фактические данные
- **VERBOSE** - показывает дополнительную информацию
- **COSTS** - показывает оценки стоимости (по умолчанию)
- **BUFFERS** - показывает статистику буферов
- **TIMING** - показывает время выполнения
- **SUMMARY** - показывает общую статистику

## 📋 Примеры комбинаций

### 1. Детальный JSON план с анализом
```sql
EXPLAIN (ANALYZE, FORMAT JSON) SELECT * FROM orders WHERE order_date >= '2025-01-01';
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
      "Filter": "(order_date >= '2025-01-01'::date)",
      "Actual Startup Time": 0.123,
      "Actual Total Time": 5.456,
      "Actual Rows": 850,
      "Actual Loops": 1,
      "Planning Time": 0.234,
      "Execution Time": 5.690
    }
  }
]
```

### 2. XML план с буферами
```sql
EXPLAIN (ANALYZE, BUFFERS, FORMAT XML) SELECT * FROM orders WHERE order_date >= '2025-01-01';
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
      <Actual-Startup-Time>0.123</Actual-Startup-Time>
      <Actual-Total-Time>5.456</Actual-Total-Time>
      <Actual-Rows>850</Actual-Rows>
      <Actual-Loops>1</Actual-Loops>
      <Buffers>
        <Shared-Hit>5</Shared-Hit>
        <Shared-Read>10</Shared-Read>
        <Shared-Dirtied>0</Shared-Dirtied>
        <Shared-Written>0</Shared-Written>
        <Local-Hit>0</Local-Hit>
        <Local-Read>0</Local-Read>
        <Local-Dirtied>0</Local-Dirtied>
        <Local-Written>0</Local-Written>
        <Temp-Read>0</Temp-Read>
        <Temp-Written>0</Temp-Written>
      </Buffers>
      <Planning-Time>0.234</Planning-Time>
      <Execution-Time>5.690</Execution-Time>
    </Plan>
  </Query>
</explain>
```

### 3. Подробный план с вербозностью
```sql
EXPLAIN (ANALYZE, VERBOSE, FORMAT JSON) 
SELECT o.*, c.name 
FROM orders o 
JOIN customers c ON o.customer_id = c.id;
```

## 🔄 Поток данных в нашем проекте

### 1. LLM генерирует план
**Вход:** "Покажи заказы за последние 3 дня"  
**Выход:** План в JSON/XML формате

### 2. Передача в Core Platform
```json
{
  "query_plan": [
    {
      "Plan": {
        "Node Type": "Seq Scan",
        "Relation Name": "orders",
        "Startup Cost": 0.00,
        "Total Cost": 25.00,
        "Plan Rows": 1000,
        "Plan Width": 244,
        "Filter": "(order_date >= '2025-01-01'::date)"
      }
    }
  ],
  "user_context": {
    "user_id": "123",
    "role": "manager",
    "branch_id": "456"
  },
  "plan_options": {
    "format": "JSON",
    "analyze": false,
    "verbose": false
  }
}
```

### 3. Core Platform обрабатывает
- Парсит план
- Добавляет ролевые ограничения
- Генерирует SQL
- Выполняет запрос

## 💡 Рекомендации для LLM

### 1. Базовый план (для разработки)
```sql
EXPLAIN (FORMAT JSON) SELECT * FROM orders WHERE order_date >= '2025-01-01';
```

### 2. Детальный план (для продакшена)
```sql
EXPLAIN (ANALYZE, VERBOSE, FORMAT JSON) SELECT * FROM orders WHERE order_date >= '2025-01-01';
```

### 3. План с буферами (для оптимизации)
```sql
EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) SELECT * FROM orders WHERE order_date >= '2025-01-01';
```

## 🎯 Промпт для LLM

```
Сгенерируй план PostgreSQL для запроса: "{user_query}"

Схема базы данных:
{table_schema}

Верни план в формате JSON, точно как результат команды:
EXPLAIN (FORMAT JSON) {sql_query}

Структура плана должна включать:
- Node Type (тип операции)
- Relation Name (имя таблицы)
- Startup Cost (стоимость запуска)
- Total Cost (общая стоимость)
- Plan Rows (оценка количества строк)
- Plan Width (ширина строки)
- Filter (условия фильтрации)
- Plans (дочерние планы для JOIN)

Пример формата:
[
  {
    "Plan": {
      "Node Type": "Seq Scan",
      "Relation Name": "orders",
      "Startup Cost": 0.00,
      "Total Cost": 25.00,
      "Plan Rows": 1000,
      "Plan Width": 244,
      "Filter": "(order_date >= '2025-01-01'::date)"
    }
  }
]
```

## ❓ Вопросы для уточнения

1. **Какой уровень детализации** нужен для планов?
2. **Нужны ли фактические данные** (ANALYZE) или только оценки?
3. **Какой формат предпочтительнее** - JSON или XML?
4. **Есть ли ограничения** на размер плана?
5. **Как валидировать** корректность сгенерированных планов?



