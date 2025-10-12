# Улучшенная стратегия обучения NL→SQL агента

## 📊 **Анализ текущей ситуации**

### ✅ **Что у нас есть от заказчика:**

1. **DocStructureSchema/** - Полная схема базы данных в JSON/XML
   - `EQDocTypes.json` - Типы документов и таблицы
   - `EQUsers.json` - Пользователи и роли
   - `EQCategories.json` - Категории документов
   - И другие метаданные

2. **TradecoTemplateTestDB.sql** - Дамп базы данных
   - Реальные данные для тестирования
   - Структура таблиц и связей

3. **ТЗ.md** - Техническое задание с примерами
   - Конкретные примеры запросов
   - Требования к архитектуре
   - Бизнес-логика

### ❌ **Проблемы текущего обучения:**

1. **Неэффективное использование данных** - не все данные от заказчика используются
2. **Слабая связь с бизнес-логикой** - агент не понимает контекст
3. **Недостаточная фильтрация** - обучается на технических таблицах
4. **Отсутствие приоритизации** - все таблицы равнозначны

## 🎯 **Улучшенная стратегия обучения**

### **Этап 1: Анализ и приоритизация данных**

#### **1.1 Извлечение бизнес-таблиц из DocStructureSchema**
```python
def extract_business_tables_from_schema():
    """Извлекает приоритетные бизнес-таблицы из схемы заказчика"""
    
    # Приоритетные таблицы (из анализа EQDocTypes.json)
    priority_tables = [
        "equsers",           # Пользователи
        "eq_departments",    # Отделы  
        "eqgroups",          # Группы
        "eqroles",           # Роли
        "tbl_business_unit", # Клиенты
        "tbl_principal_assignment", # Поручения
        "tbl_incoming_payments",    # Платежи
        "tbl_accounts_document",    # Учетные записи
        "tbl_personal_account"      # Личные кабинеты
    ]
    
    # Исключаем технические таблицы
    excluded_tables = [
        "tbl_subd_admin",
        "tbl_subd_admin_log", 
        "tbl_regex_patterns",
        "tbl_integration_files",
        "tbl_integration_log",
        "tbl_javascript_exception_handler",
        "tbl_notification",
        "tbl_activity_log"
    ]
    
    return priority_tables, excluded_tables
```

#### **1.2 Создание бизнес-контекста**
```python
def create_business_context():
    """Создает контекст бизнес-процессов на основе DocStructureSchema"""
    
    business_context = {
        "system_purpose": "Система управления поручениями и платежами",
        "main_entities": {
            "users": "Пользователи системы (сотрудники)",
            "clients": "Клиенты/бизнес-единицы", 
            "assignments": "Поручения клиентам",
            "payments": "Платежи от клиентов"
        },
        "business_flows": [
            "Создание поручения → Назначение клиенту → Выполнение → Платеж",
            "Регистрация клиента → Создание личного кабинета → Работа с поручениями"
        ]
    }
    
    return business_context
```

### **Этап 2: Улучшенная подготовка данных**

#### **2.1 Фильтрованное обучение на схеме**
```python
def train_on_filtered_schema(self):
    """Обучение только на приоритетных таблицах"""
    
    # Получаем приоритетные таблицы
    priority_tables, excluded_tables = extract_business_tables_from_schema()
    
    # Создаем фильтрованный запрос схемы
    schema_query = f"""
    SELECT 
        table_name,
        column_name,
        data_type,
        is_nullable,
        column_default,
        character_maximum_length
    FROM information_schema.columns 
    WHERE table_schema = 'public'
    AND table_name IN ({','.join([f"'{t}'" for t in priority_tables])})
    ORDER BY table_name, ordinal_position
    """
    
    df_schema = self.vanna.run_sql(schema_query)
    plan = self.vanna.get_training_plan_generic(df_schema)
    self.vanna.train(plan=plan)
    
    return True
```

#### **2.2 Обогащение SQL примеров контекстом**
```python
def enhance_sql_examples_with_context():
    """Обогащает SQL примеры бизнес-контекстом"""
    
    enhanced_examples = []
    
    # Базовые примеры с контекстом
    examples = [
        {
            "question": "Покажи всех пользователей системы",
            "sql": "SELECT id, login, email, surname, firstname FROM equsers WHERE deleted = false",
            "context": "Управление пользователями системы",
            "business_entity": "users",
            "complexity": 1
        },
        {
            "question": "Какие отделы есть в компании?",
            "sql": "SELECT id, departmentname, parentid FROM eq_departments WHERE deleted = false",
            "context": "Организационная структура",
            "business_entity": "departments", 
            "complexity": 1
        },
        {
            "question": "Покажи всех клиентов с их контактами",
            "sql": "SELECT id, business_unit_name, inn, phone, email FROM tbl_business_unit WHERE deleted = false",
            "context": "Управление клиентской базой",
            "business_entity": "clients",
            "complexity": 1
        }
    ]
    
    return enhanced_examples
```

### **Этап 3: Многоуровневое обучение**

#### **3.1 Обучение по уровням сложности**
```python
def train_by_complexity_levels():
    """Обучение по уровням сложности"""
    
    levels = {
        "level_1_basic": [
            "Покажи всех пользователей",
            "Список отделов", 
            "Все клиенты"
        ],
        "level_2_joins": [
            "Пользователи по отделам",
            "Поручения с клиентами",
            "Платежи по клиентам"
        ],
        "level_3_aggregation": [
            "Статистика по клиентам",
            "Сумма платежей по месяцам",
            "Количество поручений по статусам"
        ],
        "level_4_complex": [
            "Поручения старше 3 дней от клиентов категории А больше 1 млн рублей",
            "Топ-10 клиентов по сумме платежей за последний квартал",
            "Пользователи с ролями и их отделы"
        ]
    }
    
    return levels
```

#### **3.2 Обучение на примерах из ТЗ**
```python
def train_on_tz_examples():
    """Обучение на примерах из технического задания"""
    
    tz_examples = [
        {
            "question": "Покажи заказы старше 3 дней из категории А больше 1 млн рублей",
            "sql": """
            SELECT pa.assignment_number, pa.assignment_date, pa.amount, 
                   bu.business_unit_name, bu.category
            FROM tbl_principal_assignment pa
            JOIN tbl_business_unit bu ON pa.business_unit_id = bu.id
            WHERE pa.assignment_date < CURRENT_DATE - INTERVAL '3 days'
            AND bu.category = 'A'
            AND pa.amount > 1000000
            ORDER BY pa.amount DESC
            """,
            "context": "Сложный аналитический запрос с множественными условиями",
            "business_entity": "assignments",
            "complexity": 4
        },
        {
            "question": "Из чего сделан продукт #876?",
            "sql": """
            SELECT product_name, material, description
            FROM tbl_products 
            WHERE id = 876
            """,
            "context": "Поиск информации о конкретном продукте",
            "business_entity": "products",
            "complexity": 2
        }
    ]
    
    return tz_examples
```

### **Этап 4: Контекстное обучение**

#### **4.1 Обучение на бизнес-процессах**
```python
def train_on_business_processes():
    """Обучение на реальных бизнес-процессах"""
    
    business_processes = [
        {
            "process": "Управление поручениями",
            "examples": [
                "Создать новое поручение клиенту",
                "Показать все поручения в работе",
                "Найти поручения по конкретному клиенту",
                "Статистика выполнения поручений"
            ]
        },
        {
            "process": "Работа с платежами", 
            "examples": [
                "Показать все платежи за месяц",
                "Найти платежи конкретного клиента",
                "Сумма платежей по клиентам",
                "Платежи по периодам"
            ]
        },
        {
            "process": "Управление пользователями",
            "examples": [
                "Показать всех пользователей",
                "Пользователи по отделам",
                "Пользователи с ролями",
                "Статистика по пользователям"
            ]
        }
    ]
    
    return business_processes
```

## 🚀 **Реализация улучшенного обучения**

### **Скрипт улучшенного обучения:**
```python
def enhanced_training_pipeline():
    """Улучшенный пайплайн обучения"""
    
    # 1. Анализ и приоритизация
    priority_tables, excluded_tables = extract_business_tables_from_schema()
    business_context = create_business_context()
    
    # 2. Фильтрованное обучение на схеме
    train_on_filtered_schema(priority_tables)
    
    # 3. Обогащенные SQL примеры
    enhanced_examples = enhance_sql_examples_with_context()
    train_on_examples(enhanced_examples)
    
    # 4. Обучение по уровням сложности
    complexity_levels = train_by_complexity_levels()
    for level, examples in complexity_levels.items():
        train_on_examples(examples)
    
    # 5. Обучение на примерах из ТЗ
    tz_examples = train_on_tz_examples()
    train_on_examples(tz_examples)
    
    # 6. Контекстное обучение
    business_processes = train_on_business_processes()
    train_on_business_context(business_processes)
    
    return True
```

## 📊 **Ожидаемые улучшения**

### **1. Качество генерации SQL:**
- ✅ **Лучшее понимание контекста** - агент знает бизнес-логику
- ✅ **Приоритизация таблиц** - фокус на важных таблицах
- ✅ **Фильтрация шума** - исключение технических таблиц

### **2. Релевантность запросов:**
- ✅ **Бизнес-ориентированность** - запросы соответствуют реальным потребностям
- ✅ **Контекстная осведомленность** - понимание связей между сущностями
- ✅ **Практичность** - примеры из реального ТЗ

### **3. Производительность:**
- ✅ **Быстрее обучение** - меньше данных для обработки
- ✅ **Лучше качество** - фокус на важном
- ✅ **Эффективнее использование** - все данные заказчика

## 🎯 **Следующие шаги**

1. **Реализовать улучшенный скрипт обучения**
2. **Протестировать на текущих данных**
3. **Сравнить с предыдущим обучением**
4. **Оптимизировать на основе результатов**

---
**Дата создания**: 2025-01-11  
**Версия**: 1.0  
**Статус**: Готово к реализации  
**Следующий этап**: Реализация скрипта обучения
