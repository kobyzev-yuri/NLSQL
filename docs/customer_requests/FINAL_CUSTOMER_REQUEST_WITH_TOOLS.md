# ФИНАЛЬНЫЙ запрос к заказчику: Планы запросов + Инструменты

## 🎯 **Основная идея (по ТЗ)**

**LLM генерирует ПЛАН запроса (JSON/XML), а не SQL напрямую.**
**Core Platform собирает SQL из плана, добавляя ролевые ограничения.**

## 🔥 **Критически важно:**

### A. **Примеры планов запросов** (нужно 30-40 примеров):

```markdown
ЗАПРОС: Предоставьте примеры планов запросов в формате JSON:

Пример 1 (сложный запрос с условиями):
Вопрос: "Покажи поручения старше 3 дней от клиентов категории А больше 1 млн рублей"
План: {
  "tables": ["tbl_principal_assignment", "tbl_business_unit"],
  "fields": ["pa.assignment_number", "pa.assignment_date", "pa.amount", "bu.business_unit_name"],
  "joins": [{"table": "tbl_business_unit", "on": "pa.business_unit_id = bu.id", "type": "JOIN"}],
  "conditions": [
    {"field": "pa.assignment_date", "operator": "<", "value": "CURRENT_DATE - INTERVAL '3 days'"},
    {"field": "bu.category", "operator": "=", "value": "A"},
    {"field": "pa.amount", "operator": ">", "value": "1000000"}
  ],
  "group_by": ["bu.business_unit_name"],
  "order_by": ["pa.amount DESC"]
}

Пример 2 (поиск по ID):
Вопрос: "Какие документы у клиента #876?"
План: {
  "tables": ["tbl_business_unit", "tbl_principal_assignment"],
  "fields": ["pa.assignment_number", "pa.assignment_date", "pa.amount", "pa.status"],
  "joins": [{"table": "tbl_principal_assignment", "on": "bu.id = pa.business_unit_id", "type": "LEFT JOIN"}],
  "conditions": [{"field": "bu.id", "operator": "=", "value": "876"}],
  "order_by": ["pa.assignment_date DESC"]
}

Пример 3 (временной запрос):
Вопрос: "Когда последний платеж от клиента ООО Ромашка?"
План: {
  "tables": ["tbl_incoming_payments", "tbl_business_unit"],
  "fields": ["ip.payment_date", "ip.amount", "bu.business_unit_name"],
  "joins": [{"table": "tbl_business_unit", "on": "ip.business_unit_id = bu.id", "type": "JOIN"}],
  "conditions": [{"field": "bu.business_unit_name", "operator": "ILIKE", "value": "%ООО Ромашка%"}],
  "order_by": ["ip.payment_date DESC"],
  "limit": 1
}

Пример 4 (аналитический запрос):
Вопрос: "Сколько клиентов в каждом регионе?"
План: {
  "tables": ["tbl_business_unit"],
  "fields": ["region", "COUNT(*) as client_count"],
  "group_by": ["region"],
  "order_by": ["client_count DESC"]
}
```

## 🛠️ **Инструменты для работы с планами**

### **1. CLI инструмент для конвертации:**

```bash
# Конвертация плана в SQL (для проверки)
python src/utils/plan_sql_cli.py plan-to-sql my_plan.json

# Конвертация SQL в план (для создания примеров)
python src/utils/plan_sql_cli.py sql-to-plan "SELECT * FROM users WHERE id = 1"

# Валидация плана (проверка корректности)
python src/utils/plan_sql_cli.py validate my_plan.json

# Пакетная конвертация
python src/utils/plan_sql_cli.py batch-convert ./plans ./sql_output
```

### **2. Программное использование:**

```python
from src.utils.plan_sql_converter import plan_to_sql, sql_to_plan

# План в SQL
plan = {
    "tables": ["tbl_business_unit"],
    "fields": ["business_unit_name", "inn"],
    "conditions": [{"field": "region", "operator": "=", "value": "Москва"}]
}

sql = plan_to_sql(plan)
print(sql)  # SELECT business_unit_name, inn FROM tbl_business_unit WHERE region = 'Москва'

# SQL в план
sql_query = "SELECT * FROM users WHERE id = 1"
plan = sql_to_plan(sql_query)
print(plan)  # {"tables": ["users"], "fields": ["*"], "conditions": [...]}
```

## 📋 **Структура планов** (критично):

### **Обязательные поля:**
- `tables` - список таблиц
- `fields` - список полей

### **Опциональные поля:**
- `conditions` - условия WHERE
- `joins` - связи между таблицами
- `group_by` - группировка
- `order_by` - сортировка
- `limit` - ограничение количества

### **Поддерживаемые операторы:**
- `=`, `!=`, `<`, `>`, `<=`, `>=`
- `LIKE`, `ILIKE`
- `IN`, `NOT IN`
- `BETWEEN`
- `IS NULL`, `IS NOT NULL`

### **Типы JOIN:**
- `JOIN`, `LEFT JOIN`, `RIGHT JOIN`, `FULL JOIN`

### **Функции агрегации:**
- `COUNT`, `SUM`, `AVG`, `MIN`, `MAX`
- `GROUP_CONCAT`, `STRING_AGG`

## 📊 **Целевые категории и количество**

| Категория | Нужно добавить | Примеры |
|-----------|----------------|---------|
| **Сложные запросы** | 5-7 | Множественные условия, группировка, сортировка |
| **Поиск по ID** | 3-5 | Поиск по конкретному клиенту, пользователю, документу |
| **Временные запросы** | 3-5 | Последние события, периоды, временные диапазоны |
| **Аналитические** | 5-7 | Статистика, тренды, сравнения, топы |
| **Пользователи** | 4-6 | Пользователи по отделам, ролям, группам |
| **Клиенты** | 4-6 | Список клиентов, поиск по ИНН, статистика |
| **Поручения** | 4-6 | Поручения по периодам, статусам, клиентам |
| **Платежи** | 4-6 | Платежи по периодам, клиентам, суммам |
| **Справочники** | 3-5 | Валюты, страны, типы документов |
| **ИТОГО** | **30-40** | **Покрытие всех основных сценариев** |

## 🎯 **Требования к качеству**

### ✅ **Хорошие примеры:**
- **Сложные запросы**: "Покажи поручения старше 3 дней от клиентов категории А больше 1 млн рублей"
- **Поиск по ID**: "Какие документы у клиента #876?"
- **Временные запросы**: "Когда последний платеж от клиента ООО Ромашка?", "Платежи за последний месяц"
- **Аналитические**: "Сколько клиентов в каждом регионе?"
- **Практичные планы**: Реальные бизнес-сценарии
- **Разная сложность**: От простых SELECT до сложных JOIN с агрегацией
- **Полные планы**: Все необходимые поля заполнены

### ❌ **Избегать:**
- **Слишком общие**: "Покажи все данные"
- **Неполные планы**: Отсутствуют обязательные поля
- **Нерелевантные**: Запросы, которые не нужны пользователям
- **Дублирующие**: Похожие планы с незначительными различиями

## 📝 **Формат предоставления**

### **Структура каждого примера:**
```json
{
  "question": "Естественный вопрос на русском языке",
  "plan": {
    "tables": ["table1", "table2"],
    "fields": ["field1", "field2", "COUNT(*) as count"],
    "conditions": [{"field": "field1", "operator": "=", "value": "value1"}],
    "joins": [{"table": "table2", "on": "table1.id = table2.table1_id", "type": "LEFT JOIN"}],
    "group_by": ["field1"],
    "order_by": ["field2 DESC"],
    "limit": 100
  },
  "category": "Категория (например: 'Клиенты', 'Аналитика', 'Пользователи')",
  "complexity": "Уровень сложности (1-5)",
  "description": "Краткое описание что делает запрос"
}
```

### **Пример правильного формата:**
```json
{
  "question": "Покажи всех пользователей с их отделами",
  "plan": {
    "tables": ["equsers", "eq_departments"],
    "fields": ["u.login", "u.email", "d.departmentname"],
    "joins": [{"table": "eq_departments", "on": "u.department = d.id", "type": "LEFT JOIN"}],
    "conditions": [{"field": "u.deleted", "operator": "=", "value": "false"}],
    "order_by": ["d.departmentname", "u.login"]
  },
  "category": "Пользователи",
  "complexity": 3,
  "description": "Список пользователей с их организационной принадлежностью"
}
```

## 🚀 **Следующие шаги**

1. **Заказчик получает** этот документ + инструменты
2. **Заказчик создает** 30-40 примеров планов запросов
3. **Заказчик валидирует** каждый план с помощью CLI
4. **Заказчик проверяет SQL** на корректность
5. **Заказчик отправляет** готовые примеры
6. **Мы обучаем LLM** генерировать планы вместо SQL
7. **Core Platform** собирает SQL из планов с ролевыми ограничениями
8. **Тестируем** качество генерации планов

## 📞 **Контакты для вопросов**

Если у вас есть вопросы по формату планов, инструментам или содержанию, пожалуйста, обращайтесь за разъяснениями.

---
**Дата создания**: 2025-01-11  
**Версия**: 5.0 (ФИНАЛЬНАЯ с инструментами)  
**Статус**: Ожидает ответа заказчика  
**Срок**: Желательно в течение недели
