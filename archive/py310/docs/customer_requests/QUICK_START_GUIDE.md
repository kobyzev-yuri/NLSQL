# Быстрый старт: Инструменты для работы с планами

## 🚀 **Быстрая настройка**

### **1. Установка зависимостей:**
```bash
# Убедитесь, что Python 3.7+ установлен
python --version

# Установите зависимости (если нужно)
pip install -r requirements.txt
```

### **2. Тестирование инструментов:**
```bash
# Запустите тесты
python test_converter.py

# Проверьте CLI
python src/utils/plan_sql_cli.py --help
```

## 🛠️ **Основные команды**

### **Валидация плана:**
```bash
python src/utils/plan_sql_cli.py validate my_plan.json
```
**Результат:** ✅ План валиден + SQL запрос

### **Конвертация плана в SQL:**
```bash
python src/utils/plan_sql_cli.py plan-to-sql my_plan.json
```
**Результат:** SQL запрос + файл `my_plan_converted.sql`

### **Конвертация SQL в план:**
```bash
python src/utils/plan_sql_cli.py sql-to-plan "SELECT * FROM users WHERE id = 1"
```
**Результат:** JSON план + файл `converted_plan.json`

### **Пакетная обработка:**
```bash
python src/utils/plan_sql_cli.py batch-convert ./plans ./sql_output
```
**Результат:** Все JSON файлы конвертированы в SQL

## 📋 **Примеры файлов**

### **Простой план:**
```json
{
  "question": "Покажи всех клиентов из Москвы",
  "plan": {
    "tables": ["tbl_business_unit"],
    "fields": ["business_unit_name", "inn", "region"],
    "conditions": [
      {"field": "region", "operator": "=", "value": "Москва"}
    ],
    "order_by": ["business_unit_name"]
  },
  "category": "Клиенты",
  "complexity": 2,
  "description": "Поиск клиентов по региону"
}
```

### **Сложный план:**
```json
{
  "question": "Покажи поручения старше 3 дней от клиентов категории А больше 1 млн рублей",
  "plan": {
    "tables": ["tbl_principal_assignment", "tbl_business_unit"],
    "fields": ["pa.assignment_number", "pa.assignment_date", "pa.amount", "bu.business_unit_name"],
    "joins": [
      {"table": "tbl_business_unit", "on": "pa.business_unit_id = bu.id", "type": "JOIN"}
    ],
    "conditions": [
      {"field": "pa.assignment_date", "operator": "<", "value": "CURRENT_DATE - INTERVAL '3 days'"},
      {"field": "bu.category", "operator": "=", "value": "A"},
      {"field": "pa.amount", "operator": ">", "value": "1000000"}
    ],
    "group_by": ["bu.business_unit_name"],
    "order_by": ["pa.amount DESC"]
  },
  "category": "Сложные запросы",
  "complexity": 4,
  "description": "Сложный запрос с множественными условиями"
}
```

## 🔧 **Программное использование**

### **В Python коде:**
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

## 📁 **Организация файлов**

### **Рекомендуемая структура:**
```
customer_plans/
├── simple_queries/
│   ├── clients_by_region.json
│   └── users_by_department.json
├── complex_queries/
│   ├── assignments_with_conditions.json
│   └── payments_analytics.json
└── analytical_queries/
    ├── statistics_by_month.json
    └── top_clients.json
```

### **Пакетная обработка:**
```bash
# Конвертируйте все планы в SQL
python src/utils/plan_sql_cli.py batch-convert customer_plans/ sql_output/

# Результат: все JSON файлы станут SQL файлами
```

## 🎯 **Рекомендации**

### **1. Создание примеров:**
1. **Начните с простых запросов** (SELECT без JOIN)
2. **Добавьте условия** (WHERE)
3. **Добавьте связи** (JOIN)
4. **Добавьте группировку** (GROUP BY)
5. **Добавьте сортировку** (ORDER BY)

### **2. Проверка качества:**
1. **Валидируйте каждый план** перед отправкой
2. **Проверяйте SQL** на корректность
3. **Тестируйте на реальных данных**
4. **Убедитесь в полноте** всех полей

### **3. Отладка:**
```bash
# Если план не валиден
python src/utils/plan_sql_cli.py validate problematic_plan.json

# Если SQL некорректен
python src/utils/plan_sql_cli.py plan-to-sql problematic_plan.json
```

## 🚨 **Частые ошибки**

### **1. Отсутствуют обязательные поля:**
```json
// ❌ Неправильно
{
  "question": "Покажи клиентов",
  "plan": {
    "fields": ["business_unit_name"]
    // Отсутствует "tables"
  }
}

// ✅ Правильно
{
  "question": "Покажи клиентов",
  "plan": {
    "tables": ["tbl_business_unit"],
    "fields": ["business_unit_name"]
  }
}
```

### **2. Неправильный формат условий:**
```json
// ❌ Неправильно
{
  "conditions": ["region = 'Москва'"]
}

// ✅ Правильно
{
  "conditions": [
    {"field": "region", "operator": "=", "value": "Москва"}
  ]
}
```

### **3. Неправильный формат JOIN:**
```json
// ❌ Неправильно
{
  "joins": ["JOIN tbl_business_unit ON pa.business_unit_id = bu.id"]
}

// ✅ Правильно
{
  "joins": [
    {"table": "tbl_business_unit", "on": "pa.business_unit_id = bu.id", "type": "JOIN"}
  ]
}
```

## 📞 **Поддержка**

Если у вас возникли проблемы:
1. **Проверьте формат JSON** - должен быть валидным
2. **Запустите валидацию** - `python src/utils/plan_sql_cli.py validate your_plan.json`
3. **Проверьте обязательные поля** - `tables` и `fields`
4. **Обратитесь за помощью** - опишите проблему

---
**Дата создания**: 2025-01-11  
**Версия**: 1.0  
**Статус**: Готово к использованию  
**Следующий этап**: Создание примеров заказчиком
