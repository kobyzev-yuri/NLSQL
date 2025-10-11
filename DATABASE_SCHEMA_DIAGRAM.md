# Диаграмма структуры PostgreSQL базы данных DocStructureSchema

## 🏗️ Архитектура системы

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              СИСТЕМА УПРАВЛЕНИЯ                                 │
│                              ДОКУМЕНТАМИ И ПОЛЬЗОВАТЕЛЯМИ                      │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 👥 Система пользователей и ролей

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   equsers       │    │   eqgroups      │    │   eqroles       │
│   (пользователи)│    │   (группы)      │    │   (роли)        │
│                 │    │                 │    │                 │
│ • id (UUID)     │    │ • id (UUID)     │    │ • id (UUID)     │
│ • login         │    │ • groupname     │    │ • rolename      │
│ • email         │    │ • description   │    │ • description   │
│ • department    │    │ • ownerid       │    │ • ownerid       │
│ • accessgranted│    │                 │    │                 │
│ • pass          │    │                 │    │                 │
│ • refresh_token │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │ eq_departments  │
                    │ (отделы)        │
                    │                 │
                    │ • id (UUID)     │
                    │ • departmentname│
                    │ • parentid      │
                    │ • description   │
                    └─────────────────┘
```

## 📄 Система документооборота

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   eqdoctypes    │    │ eqdocstructure   │    │   eqview        │
│   (типы док-ов) │    │ (структура)     │    │ (представления) │
│                 │    │                 │    │                 │
│ • id (UUID)     │    │ • id (UUID)     │    │ • id (UUID)     │
│ • doctype       │    │ • doctypeid      │    │ • viewname      │
│ • category      │    │ • fieldname      │    │ • parentid      │
│ • tablename     │    │ • fieldtype      │    │ • description   │
│ • docurl        │    │ • required       │    │ • access        │
│ • ismanaged     │    │ • readonly       │    │ • conditions    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │ eqviewfields    │
                    │ (поля представл.)│
                    │                 │
                    │ • id (UUID)     │
                    │ • viewid        │
                    │ • fieldname     │
                    │ • fieldtype     │
                    │ • sortorder     │
                    └─────────────────┘
```

## 💼 Бизнес-данные

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ tbl_business_   │    │ tbl_principal_  │    │ tbl_incoming_  │
│ unit            │    │ assignment      │    │ payments        │
│ (профили клиен.) │    │ (поручения)     │    │ (входящие плат.)│
│                 │    │                 │    │                 │
│ • id (UUID)     │    │ • id (UUID)     │    │ • id (UUID)     │
│ • business_unit │    │ • assignment_   │    │ • payment_      │
│   _name         │    │   number        │    │   number        │
│ • inn           │    │ • assignment_   │    │ • payment_date  │
│ • kpp           │    │   date          │    │ • amount        │
│ • ogrn          │    │ • amount        │    │ • currency_id    │
│ • legal_address │    │ • currency_id   │    │ • business_unit │
│ • actual_address│    │ • status_id     │    │   _id           │
│ • phone         │    │ • business_unit │    │ • assignment_id │
│ • email         │    │   _id           │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │ tbl_currencies  │
                    │ (валюты)        │
                    │                 │
                    │ • id (UUID)     │
                    │ • currency_code │
                    │ • currency_name │
                    │ • is_active     │
                    └─────────────────┘
```

## 🏦 Справочники

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ tbl_countries   │    │ tbl_swift       │    │ tbl_bik         │
│ (страны)        │    │ (SWIFT коды)    │    │ (БИК коды)      │
│                 │    │                 │    │                 │
│ • id (UUID)     │    │ • id (UUID)     │    │ • id (UUID)     │
│ • country_code  │    │ • swift_code    │    │ • bik_code      │
│ • country_name  │    │ • bank_name     │    │ • bank_name     │
│ • is_active     │    │ • country_id    │    │ • city          │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🔗 Основные связи

### **1. Пользователи и роли**
```
equsers.department → eq_departments.id
equsers.id ←→ eqgroups (многие ко многим)
equsers.id ←→ eqroles (многие ко многим)
```

### **2. Документооборот**
```
eqdocstructure.doctypeid → eqdoctypes.id
eqviewfields.viewid → eqview.id
eqview.parentid → eqview.id (самоссылка)
```

### **3. Бизнес-процессы**
```
tbl_principal_assignment.business_unit_id → tbl_business_unit.id
tbl_incoming_payments.business_unit_id → tbl_business_unit.id
tbl_incoming_payments.assignment_id → tbl_principal_assignment.id
tbl_principal_assignment.currency_id → tbl_currencies.id
tbl_incoming_payments.currency_id → tbl_currencies.id
```

### **4. Справочники**
```
tbl_swift.country_id → tbl_countries.id
```

## 📊 Примеры типичных запросов

### **Пользователи и роли**
```sql
-- Все пользователи с их отделами
SELECT u.login, u.email, d.departmentname
FROM equsers u
LEFT JOIN eq_departments d ON u.department = d.id;

-- Пользователи по ролям
SELECT u.login, r.rolename
FROM equsers u
JOIN user_roles ur ON u.id = ur.user_id
JOIN eqroles r ON ur.role_id = r.id;
```

### **Документооборот**
```sql
-- Структура документа
SELECT ds.fieldname, ds.fieldnamedisplay, ds.fieldtype
FROM eqdocstructure ds
JOIN eqdoctypes dt ON ds.doctypeid = dt.id
WHERE dt.doctype = 'Поручение Принципала';

-- Представления пользователя
SELECT v.viewname, v.description
FROM eqview v
WHERE v.access = 'O' OR v.ownerid = 'user_id';
```

### **Бизнес-данные**
```sql
-- Поручения с клиентами
SELECT pa.assignment_number, pa.assignment_date, pa.amount, bu.business_unit_name
FROM tbl_principal_assignment pa
JOIN tbl_business_unit bu ON pa.business_unit_id = bu.id
WHERE pa.assignment_date >= CURRENT_DATE - INTERVAL '30 days';

-- Платежи по клиентам
SELECT bu.business_unit_name, SUM(ip.amount) as total_payments
FROM tbl_incoming_payments ip
JOIN tbl_business_unit bu ON ip.business_unit_id = bu.id
GROUP BY bu.id, bu.business_unit_name
ORDER BY total_payments DESC;
```

## 🎯 Ключевые особенности для NL→SQL

### **1. Ролевая модель**
- Каждый пользователь принадлежит отделу
- Пользователи могут иметь несколько ролей
- Роли определяют доступ к данным

### **2. Гибкая структура документов**
- Настраиваемые типы документов
- Динамическая структура полей
- Представления для отображения

### **3. Бизнес-процессы**
- Управление клиентами
- Обработка поручений
- Учет платежей
- Справочники

### **4. Безопасность**
- Row Level Security (RLS)
- Ролевая модель
- Аудит действий

## 🚀 Рекомендации для NL→SQL системы

### **1. Каталог схем**
- Создать описания таблиц на русском языке
- Добавить синонимы для технических названий
- Подготовить примеры запросов

### **2. Ролевые ограничения**
- Определить доступные таблицы для каждой роли
- Настроить RLS политики
- Учесть иерархию отделов

### **3. Контекстные подсказки**
- Бизнес-логика системы
- Типичные сценарии использования
- Ограничения и правила

### **4. Валидация**
- Проверка прав доступа
- Валидация SQL
- Защита от инъекций
- Ограничение ресурсов

