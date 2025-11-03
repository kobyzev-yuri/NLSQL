# Полное руководство по обучению и дообучению Vanna AI агента

## Содержание
1. [Обзор процесса обучения](#обзор-процесса-обучения)
2. [Подготовка данных для обучения](#подготовка-данных-для-обучения)
3. [Процесс обучения](#процесс-обучения)
4. [Дообучение агента](#дообучение-агента)
5. [Тестирование и валидация](#тестирование-и-валидация)
6. [Мониторинг и отладка](#мониторинг-и-отладка)
7. [Примеры использования](#примеры-использования)

## Обзор процесса обучения

Vanna AI агент обучается на четырех типах данных:

1. **DDL (Data Definition Language)** - структура базы данных
2. **Документация** - описание бизнес-логики и таблиц
3. **SQL примеры** - пары вопрос-ответ на естественном языке
4. **Схема базы данных** - автоматическое извлечение из INFORMATION_SCHEMA

### Архитектура обучения

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   DDL файлы     │    │  Документация   │    │  SQL примеры    │
│                 │    │                 │    │                 │
│ - CREATE TABLE  │    │ - Описание БД  │    │ - Вопросы       │
│ - ALTER TABLE   │    │ - Бизнес-логика │    │ - SQL запросы   │
│ - INDEXES       │    │ - Связи таблиц  │    │ - Контекст      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │  Vanna AI Agent │
                    │                 │
                    │ - Векторная БД   │
                    │ - LLM (ProxyAPI) │
                    │ - pgvector       │
                    └─────────────────┘
                                 │
                    ┌─────────────────┐
                    │  INFORMATION_   │
                    │  SCHEMA         │
                    │                 │
                    │ - Автоматическое│
                    │   обучение      │
                    └─────────────────┘
```

## Подготовка данных для обучения

### 1. DDL файлы (`training_data/ddl_statements.sql`)

Содержит структуру базы данных:

```sql
-- Пример DDL для обучения
CREATE TABLE equsers (
    id UUID PRIMARY KEY,
    login VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    surname VARCHAR(255),
    firstname VARCHAR(255),
    department UUID REFERENCES eq_departments(id),
    accessgranted BOOLEAN DEFAULT true,
    creationdatetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted BOOLEAN DEFAULT false
);

CREATE TABLE eq_departments (
    id UUID PRIMARY KEY,
    departmentname VARCHAR(255) NOT NULL,
    parentid UUID REFERENCES eq_departments(id),
    description TEXT,
    creationdatetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted BOOLEAN DEFAULT false
);
```

### 2. Документация (`training_data/documentation.txt`)

Описание бизнес-логики и связей:

```
DocStructureSchema - система управления документами и пользователями

ОСНОВНЫЕ ТАБЛИЦЫ:

1. ПОЛЬЗОВАТЕЛИ И РОЛИ:
- equsers: пользователи системы (логин, email, отдел, права доступа)
- eq_departments: отделы организации (название, родительский отдел)
- eqgroups: группы пользователей (название группы, описание)
- eqroles: роли системы (название роли, описание)

2. БИЗНЕС-ДАННЫЕ:
- tbl_business_unit: профили клиентов (название организации, ИНН, КПП, ОГРН)
- tbl_principal_assignment: поручения принципала (номер, дата, сумма, клиент)
- tbl_incoming_payments: входящие платежи (номер, дата, сумма, поручение)

БИЗНЕС-ЛОГИКА:
- Каждый пользователь принадлежит отделу (equsers.department → eq_departments.id)
- Поручения связаны с клиентами (tbl_principal_assignment.business_unit_id → tbl_business_unit.id)
- Платежи связаны с поручениями (tbl_incoming_payments.assignment_id → tbl_principal_assignment.id)
```

### 3. SQL примеры (`training_data/sql_examples.json`)

Пары вопрос-ответ на естественном языке:

```json
[
  {
    "question": "Покажи всех пользователей",
    "sql": "SELECT id, login, email, surname, firstname, department FROM equsers WHERE deleted = false"
  },
  {
    "question": "Список отделов",
    "sql": "SELECT id, departmentname, parentid, description FROM eq_departments WHERE deleted = false"
  },
  {
    "question": "Пользователи по отделам",
    "sql": "SELECT u.login, u.email, u.surname, u.firstname, d.departmentname FROM equsers u LEFT JOIN eq_departments d ON u.department = d.id WHERE u.deleted = false"
  },
  {
    "question": "Количество пользователей по отделам",
    "sql": "SELECT d.departmentname, COUNT(u.id) as user_count FROM eq_departments d LEFT JOIN equsers u ON d.id = u.department AND u.deleted = false WHERE d.deleted = false GROUP BY d.id, d.departmentname ORDER BY user_count DESC"
  },
  {
    "question": "Поручения за последний месяц",
    "sql": "SELECT pa.assignment_number, pa.assignment_date, pa.amount, bu.business_unit_name FROM tbl_principal_assignment pa JOIN tbl_business_unit bu ON pa.business_unit_id = bu.id WHERE pa.assignment_date >= CURRENT_DATE - INTERVAL '1 month' AND pa.deleted = false ORDER BY pa.assignment_date DESC"
  }
]
```

### 4. Метаданные (`training_data/metadata.json`)

Общая информация о базе данных:

```json
{
  "database": "DocStructureSchema",
  "total_tables": 12,
  "main_tables": ["equsers", "eq_departments", "tbl_business_unit", "tbl_principal_assignment"],
  "business_domains": ["Пользователи", "Отделы", "Клиенты", "Поручения", "Платежи"],
  "description": "Система управления документами и пользователями"
}
```

## Процесс обучения

### 1. Первичное обучение

```bash
# Запуск полного обучения
python enhanced_training_script.py
```

**Логи процесса:**

```
2025-01-11 23:30:00 - INFO - 🎓 Начало полного обучения агента...
2025-01-11 23:30:01 - INFO - ✅ Обучение на DDL завершено
2025-01-11 23:30:02 - INFO - ✅ Обучение на документации завершено
2025-01-11 23:30:03 - INFO - ✅ Обучение на SQL примерах завершено
2025-01-11 23:30:04 - INFO - ✅ Обучение на метаданных завершено
2025-01-11 23:30:05 - INFO - 🔍 Добавляем автоматическое обучение на схеме базы данных...
2025-01-11 23:30:06 - INFO - 📊 Найдено 45 колонок в схеме
2025-01-11 23:30:07 - INFO - 📋 Создан план обучения с 12 элементами
2025-01-11 23:30:08 - INFO - ✅ Автоматическое обучение на схеме завершено
2025-01-11 23:30:09 - INFO - ✅ Полное обучение завершено успешно!
```

### 2. Структура обучения

```python
class EnhancedVannaTrainer:
    def train_full(self) -> bool:
        """Полное обучение агента"""
        # 1. DDL обучение
        self.train_on_ddl()
        
        # 2. Документация
        self.train_on_documentation()
        
        # 3. SQL примеры
        self.train_on_sql_examples()
        
        # 4. Метаданные
        self.train_on_metadata()
        
        # 5. Автоматическое обучение на схеме
        self.train_on_database_schema()
```

### 3. Автоматическое обучение на схеме

```python
def train_on_database_schema(self) -> bool:
    """Автоматическое обучение на схеме базы данных"""
    # Получаем схему из INFORMATION_SCHEMA
    schema_query = """
    SELECT 
        table_name,
        column_name,
        data_type,
        is_nullable,
        column_default,
        character_maximum_length
    FROM information_schema.columns 
    WHERE table_schema = 'public'
    ORDER BY table_name, ordinal_position
    """
    
    # Выполняем запрос
    df_schema = self.vanna.run_sql(schema_query)
    
    # Создаем план обучения
    plan = self.vanna.get_training_plan_generic(df_schema)
    
    # Обучаем на плане
    self.vanna.train(plan=plan)
```

## Дообучение агента

### 1. Добавление новых SQL примеров

**Шаг 1:** Обновите файл `training_data/sql_examples.json`:

```json
[
  // ... существующие примеры ...
  {
    "question": "Покажи активных пользователей за последний месяц",
    "sql": "SELECT u.login, u.email, u.surname, u.firstname, d.departmentname FROM equsers u LEFT JOIN eq_departments d ON u.department = d.id WHERE u.deleted = false AND u.creationdatetime >= CURRENT_DATE - INTERVAL '1 month'"
  },
  {
    "question": "Статистика по платежам по месяцам",
    "sql": "SELECT DATE_TRUNC('month', payment_date) as month, COUNT(*) as payment_count, SUM(amount) as total_amount FROM tbl_incoming_payments WHERE deleted = false GROUP BY DATE_TRUNC('month', payment_date) ORDER BY month DESC"
  }
]
```

**Шаг 2:** Запустите дообучение:

```bash
python incremental_training.py --type sql_examples
```

### 2. Обновление документации

**Шаг 1:** Обновите `training_data/documentation.txt`:

```
// ... существующая документация ...

НОВЫЕ ВОЗМОЖНОСТИ:
- Аналитика по пользователям: статистика активности, география
- Отчеты по платежам: группировка по периодам, валютам
- Мониторинг отделов: эффективность, загрузка
```

**Шаг 2:** Запустите дообучение:

```bash
python incremental_training.py --type documentation
```

### 3. Добавление новых таблиц

**Шаг 1:** Обновите DDL в `training_data/ddl_statements.sql`:

```sql
-- ... существующие таблицы ...

CREATE TABLE tbl_analytics (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES equsers(id),
    action_type VARCHAR(100),
    action_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB,
    creationdatetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted BOOLEAN DEFAULT false
);
```

**Шаг 2:** Обновите документацию:

```
// ... существующая документация ...

АНАЛИТИКА:
- tbl_analytics: действия пользователей (тип, дата, метаданные)
- Связь с пользователями: tbl_analytics.user_id → equsers.id
```

**Шаг 3:** Добавьте SQL примеры:

```json
{
  "question": "Активность пользователей за день",
  "sql": "SELECT u.login, COUNT(a.id) as actions_count FROM equsers u LEFT JOIN tbl_analytics a ON u.id = a.user_id WHERE a.action_date >= CURRENT_DATE - INTERVAL '1 day' AND u.deleted = false GROUP BY u.id, u.login ORDER BY actions_count DESC"
}
```

**Шаг 4:** Запустите полное дообучение:

```bash
python incremental_training.py --type full
```

## Тестирование и валидация

### 1. Тестирование агента

```bash
# Запуск тестов
python src/vanna/testing_script.py
```

**Пример тестов:**

```python
def test_agent():
    """Тестирование обученного агента"""
    test_cases = [
        {
            "question": "Покажи всех пользователей",
            "expected_tables": ["equsers"],
            "expected_columns": ["id", "login", "email"]
        },
        {
            "question": "Статистика по отделам",
            "expected_tables": ["eq_departments", "equsers"],
            "expected_columns": ["departmentname", "user_count"]
        }
    ]
    
    for test_case in test_cases:
        result = vanna.generate_sql(test_case["question"])
        assert result is not None
        # Проверяем наличие ожидаемых таблиц и колонок
```

### 2. Валидация SQL

```python
def validate_sql(sql: str) -> bool:
    """Валидация сгенерированного SQL"""
    try:
        # Проверяем синтаксис
        parsed = sqlparse.parse(sql)[0]
        
        # Проверяем наличие основных элементов
        assert "SELECT" in sql.upper()
        assert "FROM" in sql.upper()
        
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка валидации SQL: {e}")
        return False
```

## Мониторинг и отладка

### 1. Логирование процесса обучения

```python
# Настройка детального логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('training.log'),
        logging.StreamHandler()
    ]
)
```

### 2. Мониторинг качества обучения

```python
def monitor_training_quality():
    """Мониторинг качества обучения"""
    # Проверяем количество обученных примеров
    training_data = vanna.get_training_data()
    logger.info(f"📊 Обучено примеров: {len(training_data)}")
    
    # Проверяем разнообразие типов
    types = training_data['content_type'].value_counts()
    logger.info(f"📈 Типы данных: {types.to_dict()}")
    
    # Проверяем последние добавления
    recent = training_data.head(10)
    logger.info(f"🕒 Последние добавления: {recent['content_type'].tolist()}")
```

### 3. Отладка проблем

```python
def debug_training_issues():
    """Отладка проблем обучения"""
    # Проверяем подключение к БД
    try:
        test_sql = "SELECT 1 as test"
        result = vanna.run_sql(test_sql)
        logger.info("✅ Подключение к БД работает")
    except Exception as e:
        logger.error(f"❌ Проблема с БД: {e}")
    
    # Проверяем ProxyAPI
    try:
        test_question = "Тестовый вопрос"
        result = vanna.generate_sql(test_question)
        logger.info("✅ ProxyAPI работает")
    except Exception as e:
        logger.error(f"❌ Проблема с ProxyAPI: {e}")
```

## Примеры использования

### 1. Полное переобучение

```bash
# Очистка старых данных
python clear_training_data.py

# Полное обучение
python enhanced_training_script.py

# Тестирование
python src/vanna/testing_script.py
```

### 2. Инкрементальное дообучение

```bash
# Добавление новых SQL примеров
python incremental_training.py --type sql_examples --file new_examples.json

# Обновление документации
python incremental_training.py --type documentation --file updated_docs.txt

# Добавление новых таблиц
python incremental_training.py --type ddl --file new_tables.sql
```

### 3. Автоматическое дообучение

```bash
# Настройка автоматического дообучения
python setup_auto_retraining.py --schedule daily --monitor_changes

# Мониторинг изменений в БД
python monitor_schema_changes.py --auto_retrain
```

## Заключение

Процесс обучения Vanna AI агента включает:

1. **Подготовку данных** - DDL, документация, SQL примеры, метаданные
2. **Первичное обучение** - полное обучение на всех типах данных
3. **Автоматическое обучение** - на схеме базы данных через INFORMATION_SCHEMA
4. **Дообучение** - инкрементальное добавление новых данных
5. **Тестирование** - валидация качества обучения
6. **Мониторинг** - отслеживание изменений и автоматическое дообучение

Этот подход обеспечивает высокое качество генерации SQL и возможность адаптации к изменениям в базе данных.
