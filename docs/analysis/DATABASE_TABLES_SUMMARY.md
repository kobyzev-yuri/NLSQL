# Краткий обзор таблиц PostgreSQL базы данных DocStructureSchema

## 📋 Основные таблицы системы

### 👥 **Система пользователей и ролей**

| Таблица | Назначение | Ключевые поля |
|---------|------------|---------------|
| `equsers` | Пользователи системы | `login`, `email`, `department`, `accessgranted` |
| `eqgroups` | Группы пользователей | `groupname`, `description`, `ownerid` |
| `eqroles` | Роли системы | `rolename`, `description`, `ownerid` |
| `eq_departments` | Отделы организации | `departmentname`, `parentid`, `description` |

### 📄 **Документооборот**

| Таблица | Назначение | Ключевые поля |
|---------|------------|---------------|
| `eqdoctypes` | Типы документов | `doctype`, `category`, `tablename`, `docurl` |
| `eqdocstructure` | Структура полей документов | `doctypeid`, `fieldname`, `fieldtype`, `required` |
| `eqview` | Представления данных | `viewname`, `parentid`, `access`, `conditions` |
| `eqviewfields` | Поля представлений | `viewid`, `fieldname`, `fieldtype`, `sortorder` |

### 💼 **Бизнес-данные**

| Таблица | Назначение | Ключевые поля |
|---------|------------|---------------|
| `tbl_business_unit` | Профили клиентов | `business_unit_name`, `inn`, `kpp`, `ogrn` |
| `tbl_principal_assignment` | Поручения принципала | `assignment_number`, `assignment_date`, `amount` |
| `tbl_incoming_payments` | Входящие платежи | `payment_number`, `payment_date`, `amount` |

### 🏦 **Справочники**

| Таблица | Назначение | Ключевые поля |
|---------|------------|---------------|
| `tbl_currencies` | Валюты | `currency_code`, `currency_name`, `is_active` |
| `tbl_countries` | Страны | `country_code`, `country_name`, `is_active` |
| `tbl_swift` | SWIFT коды банков | `swift_code`, `bank_name`, `country_id` |
| `tbl_bik` | БИК коды банков | `bik_code`, `bank_name`, `city` |

## 🔗 **Основные связи**

### **Пользователи → Отделы**
```
equsers.department → eq_departments.id
```

### **Документы → Типы документов**
```
eqdocstructure.doctypeid → eqdoctypes.id
```

### **Бизнес-процессы**
```
tbl_principal_assignment.business_unit_id → tbl_business_unit.id
tbl_incoming_payments.business_unit_id → tbl_business_unit.id
tbl_incoming_payments.assignment_id → tbl_principal_assignment.id
```

## 📊 **Примеры запросов для NL→SQL**

### **Простые запросы:**
- "Покажи всех пользователей" → `SELECT * FROM equsers`
- "Список отделов" → `SELECT * FROM eq_departments`
- "Все клиенты" → `SELECT * FROM tbl_business_unit`
- "Валюты" → `SELECT * FROM tbl_currencies`

### **Сложные запросы:**
- "Поручения за последний месяц" → 
  ```sql
  SELECT pa.*, bu.business_unit_name 
  FROM tbl_principal_assignment pa
  JOIN tbl_business_unit bu ON pa.business_unit_id = bu.id
  WHERE pa.assignment_date >= CURRENT_DATE - INTERVAL '1 month'
  ```

- "Сумма платежей по клиентам" →
  ```sql
  SELECT bu.business_unit_name, SUM(ip.amount) as total_amount
  FROM tbl_incoming_payments ip
  JOIN tbl_business_unit bu ON ip.business_unit_id = bu.id
  GROUP BY bu.id, bu.business_unit_name
  ```

## 🎯 **Ключевые особенности для NL→SQL**

### **1. Ролевая модель**
- Пользователи принадлежат отделам
- Роли определяют доступ к данным
- Иерархия отделов

### **2. Документооборот**
- Гибкие типы документов
- Настраиваемая структура полей
- Представления для отображения

### **3. Бизнес-процессы**
- Управление клиентами
- Обработка поручений
- Учет платежей

### **4. Безопасность**
- Row Level Security (RLS)
- Ролевая модель
- Аудит действий

## 🚀 **Рекомендации для NL→SQL системы**

### **1. Каталог схем**
- Описания таблиц на русском языке
- Синонимы для технических названий
- Примеры запросов

### **2. Ролевые ограничения**
- Доступные таблицы для каждой роли
- RLS политики
- Иерархия отделов

### **3. Контекстные подсказки**
- Бизнес-логика системы
- Типичные сценарии
- Ограничения и правила

### **4. Валидация**
- Проверка прав доступа
- Валидация SQL
- Защита от инъекций
- Ограничение ресурсов

