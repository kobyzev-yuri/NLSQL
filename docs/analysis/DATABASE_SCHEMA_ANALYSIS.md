# Анализ структуры PostgreSQL базы данных DocStructureSchema

## 📊 Обзор системы

На основе изучения файлов схемы в папке `DocStructureSchema/`, база данных представляет собой комплексную систему управления документами и пользователями с развитой ролевой моделью.

## 🏗️ Основные компоненты системы

### 1. **Система пользователей и ролей**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   equsers       │    │   eqgroups      │    │   eqroles       │
│   (пользователи)│    │   (группы)      │    │   (роли)        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │ eq_departments  │
                    │ (отделы)        │
                    └─────────────────┘
```

### 2. **Система документов**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   eqdoctypes    │    │ eqdocstructure  │    │   eqview        │
│   (типы док-ов) │    │ (структура)     │    │ (представления) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │ eqviewfields    │
                    │ (поля представл.)│
                    └─────────────────┘
```

### 3. **Бизнес-данные**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ tbl_business_   │    │ tbl_principal_  │    │ tbl_incoming_  │
│ unit            │    │ assignment      │    │ payments        │
│ (профили клиен.) │    │ (поручения)     │    │ (входящие плат.)│
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📋 Детальная структура таблиц

### **Системные таблицы**

#### 1. **equsers** - Пользователи системы
```sql
-- Основные поля:
- id (UUID) - уникальный идентификатор
- login (VARCHAR) - логин пользователя  
- email (VARCHAR) - электронная почта
- surname, firstname, patronymic - ФИО
- department (UUID) - ссылка на отдел
- accessgranted (BOOLEAN) - доступ разрешен
- build_in_account (BOOLEAN) - встроенная учетная запись
- pass (VARCHAR) - хеш пароля
- refresh_token - токен обновления
- validity (DATE) - срок действия
```

#### 2. **eqgroups** - Группы пользователей
```sql
-- Основные поля:
- id (UUID) - уникальный идентификатор
- groupname (VARCHAR) - название группы
- description (TEXT) - описание группы
- ownerid (UUID) - владелец группы
```

#### 3. **eqroles** - Роли системы
```sql
-- Основные поля:
- id (UUID) - уникальный идентификатор  
- rolename (VARCHAR) - название роли
- description (TEXT) - описание роли
- ownerid (UUID) - владелец роли
```

#### 4. **eq_departments** - Отделы
```sql
-- Основные поля:
- id (UUID) - уникальный идентификатор
- departmentname (VARCHAR) - название отдела
- parentid (UUID) - родительский отдел
- description (TEXT) - описание отдела
```

### **Документооборот**

#### 5. **eqdoctypes** - Типы документов
```sql
-- Основные поля:
- id (UUID) - уникальный идентификатор
- doctype (VARCHAR) - тип документа
- category (VARCHAR) - категория
- tablename (VARCHAR) - связанная таблица
- docurl (VARCHAR) - URL документа
- ismanaged (BOOLEAN) - управляемый тип
```

#### 6. **eqdocstructure** - Структура документов
```sql
-- Основные поля:
- id (UUID) - уникальный идентификатор
- doctypeid (UUID) - ссылка на тип документа
- fieldname (VARCHAR) - имя поля
- fieldnamedisplay (VARCHAR) - отображаемое имя
- fieldtype (INTEGER) - тип поля
- required (BOOLEAN) - обязательное поле
- readonly (BOOLEAN) - только для чтения
- tablename (VARCHAR) - связанная таблица
```

#### 7. **eqview** - Представления данных
```sql
-- Основные поля:
- id (UUID) - уникальный идентификатор
- viewname (VARCHAR) - имя представления
- parentid (UUID) - родительское представление
- description (TEXT) - описание
- access (VARCHAR) - уровень доступа
- conditions (TEXT) - условия фильтрации
```

### **Бизнес-данные**

#### 8. **tbl_business_unit** - Профили клиентов
```sql
-- Основные поля:
- id (UUID) - уникальный идентификатор
- business_unit_name (VARCHAR) - название организации
- inn (VARCHAR) - ИНН
- kpp (VARCHAR) - КПП
- ogrn (VARCHAR) - ОГРН
- legal_address (TEXT) - юридический адрес
- actual_address (TEXT) - фактический адрес
- phone (VARCHAR) - телефон
- email (VARCHAR) - электронная почта
```

#### 9. **tbl_principal_assignment** - Поручения принципала
```sql
-- Основные поля:
- id (UUID) - уникальный идентификатор
- assignment_number (VARCHAR) - номер поручения
- assignment_date (DATE) - дата поручения
- amount (DECIMAL) - сумма
- currency_id (UUID) - валюта
- status_id (UUID) - статус
- business_unit_id (UUID) - клиент
```

#### 10. **tbl_incoming_payments** - Входящие платежи
```sql
-- Основные поля:
- id (UUID) - уникальный идентификатор
- payment_number (VARCHAR) - номер платежа
- payment_date (DATE) - дата платежа
- amount (DECIMAL) - сумма
- currency_id (UUID) - валюта
- business_unit_id (UUID) - клиент
- assignment_id (UUID) - связанное поручение
```

### **Справочники**

#### 11. **tbl_currencies** - Валюты
```sql
-- Основные поля:
- id (UUID) - уникальный идентификатор
- currency_code (VARCHAR) - код валюты
- currency_name (VARCHAR) - название валюты
- is_active (BOOLEAN) - активная валюта
```

#### 12. **tbl_countries** - Страны
```sql
-- Основные поля:
- id (UUID) - уникальный идентификатор
- country_code (VARCHAR) - код страны
- country_name (VARCHAR) - название страны
- is_active (BOOLEAN) - активная страна
```

#### 13. **tbl_swift** - SWIFT коды
```sql
-- Основные поля:
- id (UUID) - уникальный идентификатор
- swift_code (VARCHAR) - SWIFT код
- bank_name (VARCHAR) - название банка
- country_id (UUID) - страна
```

## 🔗 Связи между таблицами

### **Основные связи:**

1. **Пользователи → Отделы**
   ```
   equsers.department → eq_departments.id
   ```

2. **Документы → Типы документов**
   ```
   eqdocstructure.doctypeid → eqdoctypes.id
   ```

3. **Поручения → Клиенты**
   ```
   tbl_principal_assignment.business_unit_id → tbl_business_unit.id
   ```

4. **Платежи → Поручения**
   ```
   tbl_incoming_payments.assignment_id → tbl_principal_assignment.id
   ```

5. **Платежи → Клиенты**
   ```
   tbl_incoming_payments.business_unit_id → tbl_business_unit.id
   ```

## 🎯 Ключевые особенности для NL→SQL системы

### **1. Ролевая модель**
- Система имеет развитую ролевую модель с пользователями, группами и ролями
- Каждый пользователь принадлежит отделу
- Права доступа определяются через роли

### **2. Документооборот**
- Гибкая система типов документов
- Настраиваемая структура полей документов
- Представления для отображения данных

### **3. Бизнес-процессы**
- Управление клиентами (бизнес-единицами)
- Обработка поручений принципала
- Учет входящих платежей
- Справочники валют, стран, банков

### **4. Безопасность**
- Row Level Security (RLS) для ограничения доступа
- Ролевая модель для контроля прав
- Аудит действий пользователей

## 📊 Примеры запросов для NL→SQL

### **Простые запросы:**
- "Покажи всех пользователей" → `SELECT * FROM equsers`
- "Список отделов" → `SELECT * FROM eq_departments`
- "Все клиенты" → `SELECT * FROM tbl_business_unit`

### **Сложные запросы:**
- "Покажи поручения за последний месяц" → 
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

## 🚀 Рекомендации для NL→SQL системы

### **1. Каталог схем**
Создать структурированный каталог с описанием:
- Названий таблиц и их назначения
- Полями и их типами
- Связями между таблицами
- Бизнес-логикой и ограничениями

### **2. Ролевые ограничения**
- Определить какие таблицы доступны каждой роли
- Настроить RLS политики для ограничения данных
- Учесть иерархию отделов и подчинения

### **3. Контекстные подсказки**
- Добавить описания таблиц на русском языке
- Создать синонимы для технических названий
- Подготовить примеры типичных запросов

### **4. Валидация запросов**
- Проверка прав доступа к таблицам
- Валидация синтаксиса SQL
- Защита от SQL-инъекций
- Ограничение ресурсоемких запросов

