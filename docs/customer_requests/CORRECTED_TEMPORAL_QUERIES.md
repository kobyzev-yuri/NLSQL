# Исправление временных запросов

## ❌ **Проблема с примером "следующий платеж":**

### **Почему "следующий платеж" не имеет смысла:**

1. **Платежи - это факты**, которые уже произошли
2. **Нет "планов платежей"** в системе
3. **Пользователи не спрашивают** "когда будет следующий платеж"
4. **Это не бизнес-сценарий** для данной системы

## ✅ **Правильные временные запросы:**

### 1. **Последние события:**
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

### 2. **Периоды:**
```json
{
  "question": "Платежи за последний месяц",
  "plan": {
    "tables": ["tbl_incoming_payments"],
    "fields": ["payment_date", "amount", "payment_number"],
    "conditions": [{"field": "payment_date", "operator": ">=", "value": "CURRENT_DATE - INTERVAL '1 month'"}],
    "order_by": ["payment_date DESC"]
  },
  "category": "Платежи",
  "complexity": 2,
  "description": "Платежи за определенный период"
}
```

### 3. **Временные диапазоны:**
```json
{
  "question": "Поручения с 1 по 31 января 2024 года",
  "plan": {
    "tables": ["tbl_principal_assignment"],
    "fields": ["assignment_number", "assignment_date", "amount", "status"],
    "conditions": [
      {"field": "assignment_date", "operator": ">=", "value": "2024-01-01"},
      {"field": "assignment_date", "operator": "<=", "value": "2024-01-31"}
    ],
    "order_by": ["assignment_date DESC"]
  },
  "category": "Поручения",
  "complexity": 2,
  "description": "Поручения за конкретный период"
}
```

### 4. **Сравнение периодов:**
```json
{
  "question": "Сравни платежи за январь и февраль 2024 года",
  "plan": {
    "tables": ["tbl_incoming_payments"],
    "fields": [
      "CASE WHEN EXTRACT(MONTH FROM payment_date) = 1 THEN 'Январь' ELSE 'Февраль' END as month",
      "COUNT(*) as payment_count",
      "SUM(amount) as total_amount"
    ],
    "conditions": [
      {"field": "payment_date", "operator": ">=", "value": "2024-01-01"},
      {"field": "payment_date", "operator": "<", "value": "2024-03-01"}
    ],
    "group_by": ["EXTRACT(MONTH FROM payment_date)"],
    "order_by": ["month"]
  },
  "category": "Аналитика",
  "complexity": 3,
  "description": "Сравнение показателей по месяцам"
}
```

## 🎯 **Итоговые рекомендации для временных запросов:**

### ✅ **Хорошие примеры:**
- **"Когда последний платеж от клиента X?"** ✅
- **"Платежи за последний месяц"** ✅
- **"Поручения за период с X по Y"** ✅
- **"Сравни показатели за январь и февраль"** ✅

### ❌ **Избегать:**
- **"Когда следующий платеж?"** ❌ (нет планов платежей)
- **"Когда будет следующее поручение?"** ❌ (если нет планирования)
- **"Будущие события"** ❌ (если система не планирует)

### 📊 **Категории временных запросов:**

1. **Последние события** (3-4 примера)
2. **Периоды** (3-4 примера)  
3. **Временные диапазоны** (2-3 примера)
4. **Сравнение периодов** (2-3 примера)

---
**Дата создания**: 2025-01-11  
**Версия**: 1.0  
**Статус**: Исправлено  
**Следующий этап**: Обновление финального запроса к заказчику
