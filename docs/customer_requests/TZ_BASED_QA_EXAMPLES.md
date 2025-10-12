# Q/A пары на основе примеров из ТЗ

## 📋 Анализ примеров из ТЗ

### ✅ **Примеры из ТЗ очень адекватны:**

1. **"Покажи заказы старше 3 дней из категории А больше 1 млн рублей"**
   - Сложный запрос с множественными условиями
   - Группировка и сортировка
   - Реальный бизнес-сценарий

2. **"Из чего сделан продукт #876?"**
   - Поиск по конкретному ID
   - Получение детальной информации
   - Простой, но практичный запрос

3. **"Когда будет совещание по маркетингу?"**
   - Временные запросы
   - Планирование и события
   - Контекстная информация

## 🎯 Адаптированные Q/A пары для нашей системы

### 1. **Сложные запросы с условиями** (на основе примера 1):

```json
{
  "question": "Покажи поручения старше 3 дней от клиентов категории А больше 1 млн рублей",
  "plan": {
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
  },
  "category": "Поручения",
  "complexity": 4,
  "description": "Сложный запрос с множественными условиями, группировкой и сортировкой"
}
```

```json
{
  "question": "Покажи платежи за последний месяц от клиентов с ИНН больше 1 млн рублей",
  "plan": {
    "tables": ["tbl_incoming_payments", "tbl_business_unit"],
    "fields": ["ip.payment_date", "ip.amount", "bu.business_unit_name", "bu.inn"],
    "joins": [{"table": "tbl_business_unit", "on": "ip.business_unit_id = bu.id", "type": "JOIN"}],
    "conditions": [
      {"field": "ip.payment_date", "operator": ">=", "value": "CURRENT_DATE - INTERVAL '1 month'"},
      {"field": "ip.amount", "operator": ">", "value": "1000000"}
    ],
    "order_by": ["ip.amount DESC"]
  },
  "category": "Платежи",
  "complexity": 3,
  "description": "Платежи за период с условием по сумме"
}
```

### 2. **Поиск по конкретному ID** (на основе примера 2):

```json
{
  "question": "Какие документы у клиента #876?",
  "plan": {
    "tables": ["tbl_business_unit", "tbl_principal_assignment"],
    "fields": ["pa.assignment_number", "pa.assignment_date", "pa.amount", "pa.status"],
    "joins": [{"table": "tbl_principal_assignment", "on": "bu.id = pa.business_unit_id", "type": "LEFT JOIN"}],
    "conditions": [{"field": "bu.id", "operator": "=", "value": "876"}],
    "order_by": ["pa.assignment_date DESC"]
  },
  "category": "Клиенты",
  "complexity": 2,
  "description": "Поиск документов конкретного клиента"
}
```

```json
{
  "question": "Какие поручения у клиента с ИНН 1234567890?",
  "plan": {
    "tables": ["tbl_business_unit", "tbl_principal_assignment"],
    "fields": ["pa.assignment_number", "pa.assignment_date", "pa.amount", "bu.business_unit_name"],
    "joins": [{"table": "tbl_principal_assignment", "on": "bu.id = pa.business_unit_id", "type": "LEFT JOIN"}],
    "conditions": [{"field": "bu.inn", "operator": "=", "value": "1234567890"}],
    "order_by": ["pa.assignment_date DESC"]
  },
  "category": "Клиенты",
  "complexity": 2,
  "description": "Поиск поручений клиента по ИНН"
}
```

### 3. **Временные запросы** (на основе примера 3):

```json
{
  "question": "Когда последний платеж от клиента ООО Ромашка?",
  "plan": {
    "tables": ["tbl_incoming_payments", "tbl_business_unit"],
    "fields": ["ip.payment_date", "ip.amount", "bu.business_unit_name"],
    "joins": [{"table": "tbl_business_unit", "on": "ip.business_unit_id = bu.id", "type": "JOIN"}],
    "conditions": [{"field": "bu.business_unit_name", "operator": "ILIKE", "value": "%ООО Ромашка%"}],
    "order_by": ["ip.payment_date DESC"],
    "limit": 1
  },
  "category": "Платежи",
  "complexity": 2,
  "description": "Поиск последнего платежа конкретного клиента"
}
```

```json
{
  "question": "Когда последнее поручение по клиенту X?",
  "plan": {
    "tables": ["tbl_principal_assignment", "tbl_business_unit"],
    "fields": ["pa.assignment_date", "pa.assignment_number", "pa.amount", "bu.business_unit_name"],
    "joins": [{"table": "tbl_business_unit", "on": "pa.business_unit_id = bu.id", "type": "JOIN"}],
    "conditions": [
      {"field": "bu.business_unit_name", "operator": "ILIKE", "value": "%X%"}
    ],
    "order_by": ["pa.assignment_date DESC"],
    "limit": 1
  },
  "category": "Поручения",
  "complexity": 2,
  "description": "Поиск последнего поручения клиента"
}
```

### 4. **Дополнительные примеры на основе ТЗ**:

```json
{
  "question": "Покажи всех пользователей отдела Продажи за последний месяц",
  "plan": {
    "tables": ["equsers", "eq_departments"],
    "fields": ["u.login", "u.email", "u.surname", "u.firstname", "d.departmentname"],
    "joins": [{"table": "eq_departments", "on": "u.department = d.id", "type": "JOIN"}],
    "conditions": [
      {"field": "d.departmentname", "operator": "ILIKE", "value": "%Продажи%"},
      {"field": "u.creationdatetime", "operator": ">=", "value": "CURRENT_DATE - INTERVAL '1 month'"}
    ],
    "order_by": ["u.surname", "u.firstname"]
  },
  "category": "Пользователи",
  "complexity": 3,
  "description": "Пользователи отдела за период"
}
```

```json
{
  "question": "Сколько клиентов в каждом регионе?",
  "plan": {
    "tables": ["tbl_business_unit"],
    "fields": ["region", "COUNT(*) as client_count"],
    "group_by": ["region"],
    "order_by": ["client_count DESC"]
  },
  "category": "Аналитика",
  "complexity": 2,
  "description": "Статистика клиентов по регионам"
}
```

## 📊 Итоговые рекомендации

### ✅ **Примеры из ТЗ отлично подходят:**

1. **Сложные запросы** - показывают реальные бизнес-сценарии
2. **Поиск по ID** - практичные запросы пользователей  
3. **Временные запросы** - важная функциональность
4. **Группировка и сортировка** - аналитические возможности

### 🎯 **Дополнить наш набор:**

- **10-15 Q/A пар** на основе примеров из ТЗ
- **Адаптировать под нашу схему** (поручения вместо заказов)
- **Сохранить сложность** оригинальных примеров
- **Добавить вариации** для разных сценариев

### 📝 **Формат для заказчика:**

```markdown
ЗАПРОС: Предоставьте примеры планов запросов в формате JSON, включая:

1. **Сложные запросы с условиями** (5-7 примеров):
   - "Покажи поручения старше 3 дней от клиентов категории А больше 1 млн рублей"
   - "Платежи за последний месяц от клиентов с ИНН больше 1 млн рублей"
   - "Пользователи отдела Продажи за последний месяц"

2. **Поиск по конкретному ID** (3-5 примеров):
   - "Какие документы у клиента #876?"
   - "Какие поручения у клиента с ИНН 1234567890?"
   - "Пользователь с логином admin"

3. **Временные запросы** (3-5 примеров):
   - "Когда последний платеж от клиента ООО Ромашка?"
   - "Когда следующее поручение по клиенту X?"
   - "Поручения на завтра"

4. **Аналитические запросы** (5-7 примеров):
   - "Сколько клиентов в каждом регионе?"
   - "Топ-10 клиентов по сумме поручений"
   - "Средняя сумма платежа по месяцам"
```

---
**Дата создания**: 2025-01-11  
**Версия**: 1.0  
**Статус**: Готово к интеграции  
**Следующий этап**: Добавление в финальный запрос к заказчику
