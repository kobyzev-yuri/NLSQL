# 🎓 Обучение Knowledge Base с нуля: Пошаговая инструкция для разработчика БД

## 📋 О чем этот документ

Этот документ — **практическое руководство** для разработчика базы данных, который хочет обучить Knowledge Base (KB) для своей схемы БД с нуля, используя `vector_kb_interface.py` и связанные инструменты.

**Для кого:** Разработчик БД, который:
- Знает свою схему БД "от и до"
- Понимает бизнес-логику и связи между таблицами
- Хочет добавить "мозги" в виде KB для генерации SQL на естественном языке

**Что вы получите:** Полностью обученную KB, которая понимает вашу схему БД и может генерировать SQL запросы на основе вопросов пользователей.

---

## 🎯 Общая стратегия обучения

KB обучается на **трех типах данных**:

1. **DDL (Data Definition Language)** — схемы таблиц, колонок, индексов
2. **Documentation** — бизнес-логика, описание таблиц, правила работы с данными
3. **Q/A пары (Question/SQL)** — примеры вопросов и соответствующих SQL запросов

**Принцип:** Чем больше качественных данных вы добавите, тем лучше будет работать KB.

---

## 🛠️ Работа без интерфейса: CLI скрипты

**Важно:** Все операции обучения можно выполнить **без интерфейса**, используя CLI скрипты. Это особенно удобно для автоматизации и массовой загрузки данных.

### Основные скрипты

#### 1. Унифицированный клиент для обучения (`kb_training_client.py`)

**Назначение:** Единый инструмент для всех операций обучения через API.

**Использование:**

```bash
# Массовое добавление Q/A пар из JSON файла
python -m src.tools.kb_training_client \
    --file training_data/sql_examples.json \
    --api-url http://localhost:8000

# Тихий режим (без подробного вывода)
python -m src.tools.kb_training_client \
    --file qa_pairs.json \
    --quiet

# С указанием пользователя
python -m src.tools.kb_training_client \
    --file examples.json \
    --user-id "db_guru"
```

**Формат JSON файла:**
```json
[
    {
        "question": "Покажи всех пользователей",
        "sql": "SELECT id, login FROM equsers WHERE deleted = FALSE",
        "sql_basic": "SELECT * FROM equsers",
        "improvement": "50% меньше данных",
        "domain": "users",
        "tags": ["users", "basic"]
    }
]
```

#### 2. Загрузка документации из DocStructureSchema (`load_docstructure_schema.py`)

**Назначение:** Автоматическая загрузка документации из JSON файлов схемы.

```bash
# Загрузка документации из data/DocStructureSchema/
python src/tools/load_docstructure_schema.py
```

**Что делает:**
- Анализирует `EQDocTypes.json`, `EQCategories.json`, `EQDocStates.json`
- Создает структурированную документацию
- Загружает через API в KB

#### 3. Извлечение SQL и DDL (`extract_sql_from_docstructure.py`)

**Назначение:** Извлечение Q/A примеров из представлений и DDL из SQL дампа.

```bash
# Извлечение Q/A из представлений и DDL из SQL файла
python src/tools/extract_sql_from_docstructure.py
```

**Что делает:**
- Извлекает SQL из `EQView.json` (представления)
- Извлекает DDL из `TradecoTemplateTestDB.sql`
- Загружает в KB через API

#### 4. Генерация эмбеддингов (`generate_embeddings_hf.py`)

**Назначение:** Генерация векторных представлений для всех записей в KB.

```bash
# Базовая генерация
python -m src.tools.generate_embeddings_hf \
    --dsn "$DATABASE_URL" \
    --model "$HF_MODEL_NAME"

# С пересозданием всех эмбеддингов
python -m src.tools.generate_embeddings_hf \
    --dsn "$DATABASE_URL" \
    --model "intfloat/multilingual-e5-base" \
    --rebuild \
    --batch-size 200
```

#### 5. Проверка эмбеддингов (`check_embeddings.py`)

**Назначение:** Проверка состояния эмбеддингов в KB.

```bash
python -m src.tools.check_embeddings --database-url "$DATABASE_URL"
```

### Полный процесс обучения через CLI (без интерфейса)

```bash
# 1. Запустите Core API
./run_stack.sh start core_api

# 2. Загрузите документацию
python src/tools/load_docstructure_schema.py

# 3. Извлеките SQL и DDL
python src/tools/extract_sql_from_docstructure.py

# 4. Добавьте дополнительные Q/A пары (если нужно)
python -m src.tools.kb_training_client --file my_qa_pairs.json

# 5. Сгенерируйте эмбеддинги
python -m src.tools.generate_embeddings_hf \
    --dsn "$DATABASE_URL" \
    --model "$HF_MODEL_NAME"

# 6. Проверьте результат
python -m src.tools.check_embeddings --database-url "$DATABASE_URL"
```

**Преимущества CLI подхода:**
- ✅ Автоматизация через скрипты
- ✅ Массовая загрузка данных
- ✅ Интеграция в CI/CD
- ✅ Работа в headless окружении

---

## 📦 Шаг 0: Подготовка окружения

### 0.1. Проверка зависимостей

```bash
# Убедитесь, что все сервисы установлены
cd /mnt/ai/cnn/sql4A  # или ваш путь к проекту

# Проверьте Python окружение
python --version  # Должен быть Python 3.10+

# Проверьте зависимости
pip list | grep -E "streamlit|requests|asyncpg|sentence-transformers"
```

### 0.2. Настройка config.env

Откройте `config.env` и проверьте настройки:

```bash
# База данных (ваша БД)
DATABASE_URL=postgresql://postgres:1234@localhost:5432/your_database

# Векторная таблица (создается автоматически)
VECTOR_TABLE=vanna_vectors

# Модель для эмбеддингов (рекомендуется)
HF_MODEL_NAME=intfloat/multilingual-e5-base

# Директория с документацией (если есть)
DOCSTRUCTURE_DIR=data/DocStructureSchema
```

### 0.3. Запуск сервисов

```bash
# Запустите Core API (обязательно!)
./run_stack.sh start core_api

# Проверьте, что API работает
curl http://localhost:8000/health
# Должен вернуть: {"status": "healthy", ...}

# Запустите Vector KB Interface (опционально, для визуальной работы)
./run_stack.sh start-vector-kb
# Или через основной скрипт:
# ./run_stack.sh start-web
```

**Важно:** Core API должен быть запущен для всех операций обучения через API.

---

## 📊 Шаг 1: Загрузка DDL (схемы таблиц)

**Цель:** Научить KB понимать структуру вашей базы данных.

### 1.1. Подготовка DDL данных

У вас есть несколько вариантов получения DDL:

#### Вариант A: Из SQL дампа (если есть)

Если у вас есть SQL дамп базы данных:

```bash
# Пример: у нас есть TradecoTemplateTestDB.sql
# Скрипт автоматически извлечет CREATE TABLE statements

python src/tools/extract_sql_from_docstructure.py
```

**Что делает скрипт:**
- Ищет все `CREATE TABLE` statements в SQL файле
- Извлекает имя таблицы и полный DDL
- Загружает в KB через API

**Результат:**
```
📖 Извлечение DDL из SQL файла...
  - Найдено DDL statements: 192
💾 Загрузка 192 DDL statements...
  ✅ Добавлено: 192
```

#### Вариант B: Из INFORMATION_SCHEMA (рекомендуется для живой БД)

Если у вас есть доступ к живой базе данных, создайте скрипт для извлечения DDL:

```python
# Пример скрипта extract_ddl_from_db.py
import psycopg
import sys
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv(Path(__file__).parent.parent / "config.env")

def get_ddl_for_table(conn, table_name: str) -> str:
    """Получить DDL для таблицы"""
    cur = conn.cursor()
    
    # Получаем CREATE TABLE statement
    cur.execute(f"""
        SELECT 'CREATE TABLE ' || schemaname || '.' || tablename || ' (' || 
               string_agg(column_name || ' ' || data_type || 
               CASE WHEN character_maximum_length IS NOT NULL 
                    THEN '(' || character_maximum_length || ')' 
                    ELSE '' END, ', ') || ');' as ddl
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = %s
        GROUP BY schemaname, tablename
    """, (table_name,))
    
    result = cur.fetchone()
    return result[0] if result else None

# Использование
database_url = os.getenv("DATABASE_URL")
conn = psycopg.connect(database_url)

# Список ваших таблиц
tables = ['equsers', 'eq_departments', 'tbl_principal_assignment', ...]

for table in tables:
    ddl = get_ddl_for_table(conn, table)
    if ddl:
        # Добавить в KB через API (см. шаг 1.2)
        pass
```

#### Вариант C: Ручное добавление через интерфейс

1. Откройте Vector KB Interface: `http://localhost:8503`
2. Перейдите на вкладку **"🎓 Обучение"**
3. В разделе **"Обучение на DDL"**:
   - Выберите таблицу из списка (если уже есть в БД)
   - Или введите DDL вручную в текстовое поле
4. Нажмите **"📖 Обучить на DDL"**

**Пример DDL для ручного ввода:**
```sql
CREATE TABLE equsers (
    id SERIAL PRIMARY KEY,
    login VARCHAR(50) NOT NULL,
    email VARCHAR(100),
    firstname VARCHAR(100),
    lastname VARCHAR(100),
    departmentid INTEGER,
    deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE eq_departments (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(20),
    deleted BOOLEAN DEFAULT FALSE
);
```

### 1.2. Загрузка DDL через API (программно)

Если вы хотите автоматизировать процесс:

**Через Python скрипт:**
```python
from src.tools.kb_training_client import KBTrainingClient

client = KBTrainingClient(api_base_url="http://localhost:8000")

# Подготовьте список DDL statements
ddl_statements = [
    {
        'ddl': 'CREATE TABLE equsers (...);',
        'table_name': 'equsers',
        'source': 'information_schema',
        'version': '1.0',
        'metadata': {'domain': 'users'}
    },
    # ... другие таблицы
]

# Загрузите через API
result = client.add_ddl_statements(
    ddl_statements=ddl_statements,
    user_id="db_guru"
)

print(f"Добавлено: {result['added']}, Обновлено: {result['updated']}")
```

**Через готовый скрипт (если есть SQL дамп):**
```bash
# Автоматическое извлечение DDL из SQL файла
python src/tools/extract_sql_from_docstructure.py

# Скрипт автоматически:
# 1. Найдет все CREATE TABLE statements
# 2. Извлечет имена таблиц
# 3. Загрузит через API в KB
```

### 1.3. Проверка загруженных DDL

```bash
# Через SQL
psql "$DATABASE_URL" -c "
SELECT 
    content_type,
    COUNT(*) as total,
    COUNT(CASE WHEN embedding IS NOT NULL THEN 1 END) as with_embeddings
FROM vanna_vectors 
WHERE content_type = 'ddl'
GROUP BY content_type;
"

# Должно показать:
# content_type | total | with_embeddings
# -------------+-------+----------------
# ddl          |   192 |             192
```

**Ожидаемый результат:** Все ваши таблицы должны быть в KB как DDL statements.

---

## 📝 Шаг 2: Добавление документации

**Цель:** Научить KB понимать бизнес-логику и назначение таблиц.

### 2.1. Подготовка документации

Документация должна описывать:
- **Назначение таблиц** — для чего используется каждая таблица
- **Бизнес-логику** — правила работы с данными
- **Связи между таблицами** — как таблицы связаны между собой
- **Особенности** — важные нюансы (например, soft delete через `deleted = FALSE`)

#### Пример документации для таблицы `equsers`:

```markdown
## Таблица: equsers

### Назначение
Таблица пользователей системы. Хранит информацию о всех пользователях, включая логины, email, имена и принадлежность к отделам.

### Бизнес-логика
- Пользователи не удаляются физически, используется soft delete через флаг `deleted`
- При выборке пользователей ВСЕГДА нужно фильтровать `WHERE deleted = FALSE`
- Поле `departmentid` связывает пользователя с отделом через таблицу `eq_departments`
- Логин должен быть уникальным

### Связи
- `departmentid` → `eq_departments.id` (многие к одному)
- Используется в `tbl_principal_assignment` для связи поручений с пользователями

### Важные поля
- `id` - уникальный идентификатор пользователя
- `login` - логин для входа в систему (уникальный)
- `email` - email пользователя
- `deleted` - флаг удаления (FALSE = активный пользователь)
```

### 2.2. Загрузка документации

#### Вариант A: Автоматическая загрузка из DocStructureSchema (если есть)

Если у вас есть JSON файлы с описанием схемы (как в нашем проекте):

```bash
python src/tools/load_docstructure_schema.py
```

**Что делает скрипт:**
- Анализирует JSON файлы (`EQDocTypes.json`, `EQCategories.json`, `EQDocStates.json`)
- Извлекает информацию о таблицах, категориях, состояниях
- Создает структурированную документацию
- Загружает в KB через API

**Результат:**
```
📖 Загрузка JSON файлов...
  - EQDocTypes: 81 записей
  - EQCategories: 25 записей
  - EQDocStates: 97 записей
📝 Формирование документации...
  - Создано документов: 77
💾 Загрузка в векторную базу...
  ✅ Добавлено: 77
```

#### Вариант B: Ручное добавление через интерфейс

1. Откройте Vector KB Interface: `http://localhost:8503`
2. Перейдите на вкладку **"🎓 Обучение"**
3. В разделе **"Обучение на документации"**:
   - Введите документацию в текстовое поле
   - Укажите заголовок (например, "Таблица equsers")
   - Нажмите **"📖 Обучить на документации"**

**Примечание:** Через интерфейс пока нет прямого API для документации, используйте вариант C.

#### Вариант C: Загрузка через API (программно)

**Через Python скрипт:**
```python
from src.tools.kb_training_client import KBTrainingClient

client = KBTrainingClient(api_base_url="http://localhost:8000")

# Подготовьте список документов
documents = [
    {
        'content': '''
## Таблица: equsers

### Назначение
Таблица пользователей системы...

### Бизнес-логика
- Пользователи не удаляются физически...
        ''',
        'title': 'Таблица equsers - документация',
        'source': 'manual',
        'domain': 'users',
        'tags': ['users', 'authentication'],
        'metadata': {
            'table': 'equsers',
            'type': 'table_documentation'
        }
    },
    # ... другие документы
]

# Загрузите через API
result = client.add_documentation(
    documents=documents,
    user_id="db_guru"
)

print(f"Добавлено: {result['added']}, Обновлено: {result['updated']}")
```

**Через готовый скрипт (если есть DocStructureSchema JSON файлы):**
```bash
# Автоматическая загрузка документации из JSON файлов
python src/tools/load_docstructure_schema.py

# Скрипт автоматически:
# 1. Анализирует EQDocTypes.json, EQCategories.json, EQDocStates.json
# 2. Создает структурированную документацию
# 3. Загружает через API в KB
```

### 2.3. Структура документации

**Рекомендуемая структура для каждой таблицы:**

```markdown
## Таблица: [table_name]

### Назначение
[Краткое описание назначения таблицы]

### Бизнес-логика
- [Правило 1]
- [Правило 2]
- [Правило 3]

### Связи
- [Поле] → [Таблица.Поле] (тип связи)

### Важные поля
- [поле] - [описание]
- [поле] - [описание]

### Примеры использования
[Примеры типичных запросов к таблице]
```

### 2.4. Проверка загруженной документации

```bash
psql "$DATABASE_URL" -c "
SELECT 
    COUNT(*) as total_docs,
    COUNT(DISTINCT metadata->>'table') as tables_documented
FROM vanna_vectors 
WHERE content_type = 'documentation';
"
```

---

## 💬 Шаг 3: Добавление Q/A пар (вопросы и SQL)

**Цель:** Научить KB генерировать правильные SQL запросы на основе вопросов пользователей.

### 3.1. Подготовка Q/A пар

**Принцип:** Для каждой важной таблицы и типичного запроса создайте Q/A пару.

#### Примеры Q/A пар для таблицы `equsers`:

```json
[
    {
        "question": "Покажи всех пользователей системы",
        "sql": "SELECT id, login, email, firstname, lastname FROM equsers WHERE deleted = FALSE"
    },
    {
        "question": "Список активных пользователей",
        "sql": "SELECT id, login, email FROM equsers WHERE deleted = FALSE ORDER BY login"
    },
    {
        "question": "Пользователи из определенного отдела",
        "sql": "SELECT u.id, u.login, u.email, d.name as department FROM equsers u JOIN eq_departments d ON u.departmentid = d.id WHERE u.deleted = FALSE AND d.name = 'Отдел продаж'"
    }
]
```

#### Примеры Q/A пар для сложных запросов:

```json
[
    {
        "question": "Поручения за последний месяц",
        "sql": "SELECT pa.id, pa.assignment_number, pa.amount, bu.business_unit_name, pa.creationdatetime FROM tbl_principal_assignment pa JOIN tbl_business_unit bu ON pa.business_unit_id = bu.id WHERE pa.creationdatetime >= CURRENT_DATE - INTERVAL '1 month' AND pa.deleted = FALSE"
    },
    {
        "question": "Сумма платежей по месяцам",
        "sql": "SELECT DATE_TRUNC('month', payment_date) as month, SUM(amount) as total_amount FROM tbl_incoming_payments WHERE deleted = FALSE GROUP BY DATE_TRUNC('month', payment_date) ORDER BY month DESC"
    },
    {
        "question": "Топ-10 клиентов по сумме платежей",
        "sql": "SELECT bu.business_unit_name, SUM(p.amount) as total_payments FROM tbl_incoming_payments p JOIN tbl_business_unit bu ON p.business_unit_id = bu.id WHERE p.deleted = FALSE GROUP BY bu.id, bu.business_unit_name ORDER BY total_payments DESC LIMIT 10"
    }
]
```

**Рекомендации:**
- ✅ Используйте конкретные названия колонок вместо `SELECT *`
- ✅ Всегда добавляйте фильтр `WHERE deleted = FALSE` для таблиц с soft delete
- ✅ Включайте JOIN'ы для связанных таблиц
- ✅ Добавляйте `ORDER BY` для логичной сортировки
- ✅ Используйте алиасы таблиц для читаемости

### 3.2. Загрузка Q/A пар

#### Вариант A: Через Vector KB Interface (визуально)

1. Откройте Vector KB Interface: `http://localhost:8503`
2. Перейдите на вкладку **"📝 Добавление Q/A"**
3. **Ручное добавление:**
   - Введите вопрос (например, "Покажи всех пользователей")
   - Введите SQL (например, `SELECT id, login FROM equsers WHERE deleted = FALSE`)
   - Нажмите **"➕ Добавить Q/A пару"**
4. **Массовое добавление:**
   - Подготовьте JSON файл с Q/A парами (формат см. выше)
   - Нажмите **"📤 Загрузить JSON файл"**
   - Выберите файл и загрузите

#### Вариант B: Через CLI скрипт (массово)

```bash
# Подготовьте файл qa_pairs.json
cat > qa_pairs.json << 'EOF'
[
    {
        "question": "Покажи всех пользователей системы",
        "sql": "SELECT id, login, email FROM equsers WHERE deleted = FALSE"
    },
    {
        "question": "Поручения за последний месяц",
        "sql": "SELECT * FROM tbl_principal_assignment WHERE creationdatetime >= CURRENT_DATE - INTERVAL '1 month'"
    }
]
EOF

# Загрузите через унифицированный клиент
python -m src.tools.kb_training_client \
    --file qa_pairs.json \
    --api-url http://localhost:8000
```

#### Вариант C: Через Python API

**Программно (один пример):**
```python
from src.tools.kb_training_client import KBTrainingClient

client = KBTrainingClient(api_base_url="http://localhost:8000")

# Добавьте одну Q/A пару
result = client.add_training_example(
    question="Покажи всех пользователей системы",
    sql="SELECT id, login, email FROM equsers WHERE deleted = FALSE",
    user_id="db_guru"
)

print(f"Добавлено: {result.get('example_id')}")
```

**Массовое добавление из файла (CLI):**
```bash
# Подготовьте файл qa_pairs.json
cat > qa_pairs.json << 'EOF'
[
    {
        "question": "Покажи всех пользователей",
        "sql": "SELECT id, login FROM equsers WHERE deleted = FALSE"
    },
    {
        "question": "Поручения за последний месяц",
        "sql": "SELECT * FROM tbl_principal_assignment WHERE creationdatetime >= CURRENT_DATE - INTERVAL '1 month'"
    }
]
EOF

# Загрузите через CLI скрипт
python -m src.tools.kb_training_client --file qa_pairs.json
```

**Или программно:**
```python
from src.tools.kb_training_client import KBTrainingClient
from pathlib import Path

client = KBTrainingClient(api_base_url="http://localhost:8000")

# Массовое добавление из файла
stats = client.add_from_json_file(
    json_file=Path("qa_pairs.json"),
    user_id="db_guru"
)

print(f"Успешно: {stats['success']}/{stats['total']}")
```

### 3.3. Добавление оптимизированных SQL (опционально, но рекомендуется)

Для обучения KB генерировать **эффективные** SQL запросы:

```python
from src.tools.kb_training_client import KBTrainingClient

client = KBTrainingClient(api_base_url="http://localhost:8000")

# Добавьте оптимизированную Q/A пару
result = client.add_training_example(
    question="Покажи всех пользователей системы",
    sql="SELECT id, login, email FROM equsers WHERE deleted = FALSE",  # оптимизированный
    sql_basic="SELECT * FROM equsers",  # базовый (неоптимизированный)
    improvement="50% меньше данных, быстрее выполнение за счет фильтрации deleted",
    user_id="db_guru"
)

# Система автоматически:
# 1. Сгенерирует EXPLAIN план для обоих SQL
# 2. Сравнит планы и валидирует оптимизацию
# 3. Сохранит планы в metadata
```

**Преимущества:**
- KB учится генерировать не просто рабочий, а **эффективный** SQL
- Автоматическая валидация оптимизации через EXPLAIN планы
- Модель видит примеры оптимизации и учится применять их

### 3.4. Проверка загруженных Q/A пар

```bash
psql "$DATABASE_URL" -c "
SELECT 
    COUNT(*) as total_qa,
    COUNT(CASE WHEN metadata->>'is_optimized' = 'true' THEN 1 END) as optimized_qa
FROM vanna_vectors 
WHERE content_type = 'question_sql';
"
```

---

## 🔄 Шаг 4: Генерация эмбеддингов

**Цель:** Преобразовать все текстовые данные (DDL, документация, Q/A) в векторные представления для семантического поиска.

### 4.1. Запуск генерации эмбеддингов

```bash
# Базовый запуск
python -m src.tools.generate_embeddings_hf \
    --dsn "$DATABASE_URL" \
    --model "$HF_MODEL_NAME"

# С дополнительными параметрами
python -m src.tools.generate_embeddings_hf \
    --dsn "$DATABASE_URL" \
    --model "intfloat/multilingual-e5-base" \
    --batch-size 200 \
    --rebuild  # если нужно пересоздать все эмбеддинги
```

**Что делает скрипт:**
- Находит все записи в `vanna_vectors` без эмбеддингов
- Генерирует векторные представления используя модель эмбеддингов
- Сохраняет эмбеддинги в столбец `embedding` (тип `vector(768)`)

**Параметры:**
- `--dsn` - connection string к PostgreSQL
- `--model` - модель для эмбеддингов (рекомендуется `intfloat/multilingual-e5-base`)
- `--rebuild` - пересоздать все эмбеддинги (даже если уже есть)
- `--alter` - автоматически изменить размерность столбца (например, 384 → 768)
- `--batch-size` - размер батча для обработки (по умолчанию 200)

### 4.2. Ожидаемый результат

```
INFO - Records to (re)embed: 269
INFO - Using model: intfloat/multilingual-e5-base
INFO - Embedding dimension: 768
INFO - Processing batch 1/2 (200 records)...
INFO - Processing batch 2/2 (69 records)...
INFO - Processed 269/269
INFO - Completed: processed 269 records
```

### 4.3. Проверка эмбеддингов

```bash
psql "$DATABASE_URL" -c "
SELECT 
    content_type,
    COUNT(*) as total,
    COUNT(CASE WHEN embedding IS NOT NULL THEN 1 END) as with_embeddings,
    ROUND(100.0 * COUNT(CASE WHEN embedding IS NOT NULL THEN 1 END) / COUNT(*), 2) as coverage_percent
FROM vanna_vectors 
GROUP BY content_type
ORDER BY content_type;
"

# Должно показать 100% coverage для всех типов:
# content_type    | total | with_embeddings | coverage_percent
# ----------------+-------+-----------------+------------------
# ddl             |   192 |             192 |           100.00
# documentation   |    77 |              77 |           100.00
# question_sql    |    50 |              50 |           100.00
```

**Важно:** Если `coverage_percent < 100%`, запустите генерацию эмбеддингов еще раз.

### 4.4. Пересоздание индексов (если нужно)

После генерации эмбеддингов убедитесь, что индексы созданы:

```sql
-- Проверка существующих индексов
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'vanna_vectors' AND indexname LIKE '%embedding%';

-- Создание индекса для семантического поиска (если нет)
CREATE INDEX IF NOT EXISTS vanna_vectors_embedding_ivf
ON vanna_vectors USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Для больших таблиц (100K+ записей) используйте больше lists:
-- WITH (lists = 200);
```

---

## ✅ Шаг 5: Проверка качества KB

**Цель:** Убедиться, что KB правильно работает и находит релевантные данные.

### 5.1. Тестирование через Vector KB Interface

1. Откройте Vector KB Interface: `http://localhost:8503`
2. Перейдите на вкладку **"🔍 Тестирование поиска"**
3. Введите тестовый запрос (например, "Покажи всех пользователей")
4. Выберите тип поиска:
   - `semantic` - поиск по всем типам контента
   - `ddl` - поиск по схемам таблиц
   - `documentation` - поиск по документации
   - `examples` - поиск по Q/A примерам
5. Нажмите **"🔍 Тестировать поиск"**

**Ожидаемый результат:**
- Должны появиться релевантные результаты
- Для запроса "Покажи всех пользователей" должны найтись:
  - Q/A примеры с похожими вопросами
  - DDL таблицы `equsers`
  - Документация о пользователях

### 5.2. Тестирование через API

```bash
# Тест семантического поиска
curl -X POST http://localhost:8000/test-search \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Покажи всех пользователей",
    "search_type": "semantic",
    "limit": 5
  }' | jq .

# Тест генерации SQL
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Покажи всех пользователей",
    "user_id": "test",
    "role": "admin"
  }' | jq .
```

### 5.3. Проверка статистики KB

```bash
psql "$DATABASE_URL" -c "
SELECT 
    content_type,
    COUNT(*) as total,
    COUNT(CASE WHEN embedding IS NOT NULL THEN 1 END) as with_embeddings,
    MIN(created_at) as first_added,
    MAX(created_at) as last_added
FROM vanna_vectors 
GROUP BY content_type
ORDER BY content_type;
"
```

### 5.4. Анализ качества через интерфейс

1. Откройте Vector KB Interface: `http://localhost:8503`
2. Перейдите на вкладку **"📊 Аналитика"**
3. Просмотрите:
   - Статистику по типам контента
   - Графики распределения данных
   - Метрики качества поиска

---

## 🎯 Шаг 6: Итеративное улучшение

**Цель:** Постоянно улучшать качество KB на основе реального использования.

### 6.1. Анализ проблемных запросов

Когда пользователи задают вопросы, которые KB не может правильно обработать:

1. **Зафиксируйте проблемный вопрос**
2. **Создайте правильный SQL ответ**
3. **Добавьте как Q/A пару в KB**

```python
from src.tools.kb_training_client import KBTrainingClient

client = KBTrainingClient(api_base_url="http://localhost:8000")

# Добавьте проблемный случай
client.add_training_example(
    question="[Проблемный вопрос пользователя]",
    sql="[Правильный SQL запрос]",
    user_id="db_guru"
)

# Пересоздайте эмбеддинги
# python -m src.tools.generate_embeddings_hf --dsn "$DATABASE_URL" --model "$HF_MODEL_NAME"
```

### 6.2. Добавление недостающей документации

Если KB не понимает определенные аспекты БД:

1. **Определите, чего не хватает** (документация, DDL, примеры)
2. **Добавьте недостающие данные**
3. **Пересоздайте эмбеддинги**

### 6.3. Оптимизация SQL

Для часто используемых запросов:

1. **Создайте оптимизированную версию SQL**
2. **Добавьте как оптимизированную Q/A пару**
3. **KB научится генерировать эффективные запросы**

---

## 🚀 Быстрый старт: Полный процесс через CLI (без интерфейса)

Если вы предпочитаете работать через командную строку, вот полный процесс:

```bash
# 1. Запустите Core API
./run_stack.sh start core_api

# 2. Проверьте подключение
curl http://localhost:8000/health

# 3. Загрузите документацию (если есть DocStructureSchema)
python src/tools/load_docstructure_schema.py

# 4. Извлеките DDL и Q/A из SQL дампа (если есть)
python src/tools/extract_sql_from_docstructure.py

# 5. Добавьте дополнительные Q/A пары (подготовьте qa_pairs.json)
python -m src.tools.kb_training_client --file qa_pairs.json

# 6. Сгенерируйте эмбеддинги
python -m src.tools.generate_embeddings_hf \
    --dsn "$DATABASE_URL" \
    --model "$HF_MODEL_NAME"

# 7. Проверьте результат
python -m src.tools.check_embeddings --database-url "$DATABASE_URL"

# 8. Протестируйте через API
curl -X POST http://localhost:8000/test-search \
  -H "Content-Type: application/json" \
  -d '{"question": "Покажи всех пользователей", "search_type": "semantic", "limit": 5}'
```

**Время выполнения:** ~10-30 минут в зависимости от объема данных.

---

## 📋 Чеклист обучения KB с нуля

Используйте этот чеклист для проверки полноты обучения:

- [ ] **Шаг 0: Подготовка**
  - [ ] Core API запущен и доступен
  - [ ] `config.env` настроен правильно
  - [ ] База данных доступна

- [ ] **Шаг 1: DDL**
  - [ ] Все основные таблицы добавлены как DDL
  - [ ] Проверено количество: `SELECT COUNT(*) FROM vanna_vectors WHERE content_type = 'ddl'`

- [ ] **Шаг 2: Документация**
  - [ ] Добавлена документация по всем важным таблицам
  - [ ] Описана бизнес-логика
  - [ ] Описаны связи между таблицами

- [ ] **Шаг 3: Q/A пары**
  - [ ] Добавлены базовые Q/A пары для каждой таблицы
  - [ ] Добавлены сложные Q/A пары с JOIN'ами
  - [ ] Добавлены оптимизированные SQL (опционально)

- [ ] **Шаг 4: Эмбеддинги**
  - [ ] Запущена генерация эмбеддингов
  - [ ] Проверено покрытие: 100% записей имеют эмбеддинги
  - [ ] Созданы индексы для поиска

- [ ] **Шаг 5: Проверка**
  - [ ] Протестирован поиск через интерфейс
  - [ ] Протестирована генерация SQL
  - [ ] Проверена статистика KB

- [ ] **Шаг 6: Улучшение**
  - [ ] Настроен процесс добавления проблемных случаев
  - [ ] Регулярно обновляется KB на основе использования

---

## 🎓 Примеры из нашей схемы БД

### Пример 1: Таблица `equsers`

**DDL:**
```sql
CREATE TABLE equsers (
    id SERIAL PRIMARY KEY,
    login VARCHAR(50) NOT NULL,
    email VARCHAR(100),
    firstname VARCHAR(100),
    lastname VARCHAR(100),
    departmentid INTEGER,
    deleted BOOLEAN DEFAULT FALSE
);
```

**Документация:**
```markdown
## Таблица: equsers

Таблица пользователей системы. Использует soft delete через флаг `deleted`.
Всегда фильтровать `WHERE deleted = FALSE` при выборке.
```

**Q/A пары:**
```json
[
    {
        "question": "Покажи всех пользователей",
        "sql": "SELECT id, login, email FROM equsers WHERE deleted = FALSE"
    },
    {
        "question": "Активные пользователи из отдела продаж",
        "sql": "SELECT u.id, u.login, d.name FROM equsers u JOIN eq_departments d ON u.departmentid = d.id WHERE u.deleted = FALSE AND d.name = 'Отдел продаж'"
    }
]
```

### Пример 2: Таблица `tbl_principal_assignment`

**DDL:**
```sql
CREATE TABLE tbl_principal_assignment (
    id SERIAL PRIMARY KEY,
    assignment_number VARCHAR(20),
    amount DECIMAL(15,2),
    business_unit_id INTEGER,
    creationdatetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted BOOLEAN DEFAULT FALSE
);
```

**Документация:**
```markdown
## Таблица: tbl_principal_assignment

Таблица поручений. Связана с клиентами через `business_unit_id`.
Использует soft delete. Важно фильтровать по дате создания для временных запросов.
```

**Q/A пары:**
```json
[
    {
        "question": "Поручения за последний месяц",
        "sql": "SELECT pa.id, pa.assignment_number, pa.amount, bu.business_unit_name FROM tbl_principal_assignment pa JOIN tbl_business_unit bu ON pa.business_unit_id = bu.id WHERE pa.creationdatetime >= CURRENT_DATE - INTERVAL '1 month' AND pa.deleted = FALSE"
    }
]
```

---

## 🔧 Устранение проблем

### Проблема: "Результаты не найдены" при поиске

**Причины:**
1. Эмбеддинги не сгенерированы
2. Индексы не созданы
3. Недостаточно данных в KB

**Решение:**
```bash
# 1. Проверьте эмбеддинги
psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM vanna_vectors WHERE embedding IS NULL;"

# 2. Если есть записи без эмбеддингов, сгенерируйте их
python -m src.tools.generate_embeddings_hf --dsn "$DATABASE_URL" --model "$HF_MODEL_NAME"

# 3. Проверьте индексы
psql "$DATABASE_URL" -c "\d vanna_vectors"
```

### Проблема: "API недоступен"

**Решение:**
```bash
# Запустите Core API
./run_stack.sh start core_api

# Проверьте
curl http://localhost:8000/health
```

### Проблема: "Низкое качество генерации SQL"

**Причины:**
1. Недостаточно Q/A примеров
2. Недостаточно документации
3. Неправильные примеры

**Решение:**
1. Добавьте больше Q/A пар для проблемных случаев
2. Улучшите документацию
3. Добавьте оптимизированные SQL примеры

---

## 🖥️ Локальные модели для генерации SQL (для серверов с большими ресурсами)

Если у вас есть сервер с большими ресурсами (больше чем ноутбук), вы можете использовать более мощные локальные модели для генерации SQL.

### Текущие модели в системе

**Поддерживаемые через Ollama:**
- `qwen2.5-coder:1.5b` - легкая модель (986 MB, ~2-3 GB RAM)
- `qwen2.5:1.5b` - альтернатива (986 MB)
- `qwen3:8b` - более мощная (5.2 GB, ~10-12 GB RAM)

### Рекомендуемые модели для серверов с большими ресурсами

#### 1. Qwen 2.5 Coder 30B (Alibaba)

**Характеристики:**
- Размер модели: ~30 GB
- Требования: 32+ GB RAM, GPU с 24+ GB VRAM
- Качество: Очень высокое для генерации кода и SQL
- Скорость: Средняя (зависит от GPU)

**Установка:**
```bash
ollama pull qwen2.5-coder:30b
```

**Настройка в config.env:**
```env
LLM_PROVIDER=ollama
OLLAMA_MODEL=qwen2.5-coder:30b
OLLAMA_TIMEOUT=300  # Увеличьте таймаут для больших моделей
```

#### 2. CodeLlama 34B (Meta)

**Характеристики:**
- Размер модели: ~34 GB
- Требования: 64+ GB RAM, GPU с 32+ GB VRAM
- Качество: Отличное для SQL и кода
- Скорость: Средняя

**Установка:**
```bash
ollama pull codellama:34b
```

**Настройка:**
```env
LLM_PROVIDER=ollama
OLLAMA_MODEL=codellama:34b
OLLAMA_TIMEOUT=300
```

#### 3. DeepSeek Coder 33B

**Характеристики:**
- Размер модели: ~33 GB
- Требования: 64+ GB RAM, GPU с 32+ GB VRAM
- Качество: Очень высокое, специализирована на коде
- Скорость: Средняя-высокая

**Установка:**
```bash
ollama pull deepseek-coder:33b
```

#### 4. Qwen 2.5 72B (для очень мощных серверов)

**Характеристики:**
- Размер модели: ~72 GB
- Требования: 128+ GB RAM, GPU с 48+ GB VRAM (или несколько GPU)
- Качество: Максимальное
- Скорость: Медленная без GPU

**Установка:**
```bash
ollama pull qwen2.5:72b
```

### Сравнение моделей

| Модель | Размер | RAM | VRAM | Качество SQL | Скорость | Рекомендация |
|--------|--------|-----|------|--------------|----------|--------------|
| **qwen2.5-coder:1.5b** | 986 MB | 2-3 GB | - | Хорошее | Быстрая | Для ноутбуков |
| **qwen3:8b** | 5.2 GB | 10-12 GB | 8 GB | Хорошее | Средняя | Для средних серверов |
| **qwen2.5-coder:30b** | ~30 GB | 32+ GB | 24 GB | Очень высокое | Средняя | **Рекомендуется для серверов** |
| **codellama:34b** | ~34 GB | 64+ GB | 32 GB | Отличное | Средняя | Для мощных серверов |
| **deepseek-coder:33b** | ~33 GB | 64+ GB | 32 GB | Очень высокое | Средняя-высокая | Для серверов с GPU |
| **qwen2.5:72b** | ~72 GB | 128+ GB | 48+ GB | Максимальное | Медленная | Для очень мощных серверов |

### Рекомендации по выбору модели

**Для сервера с 32-64 GB RAM и GPU 24-32 GB:**
```env
OLLAMA_MODEL=qwen2.5-coder:30b  # Лучший баланс качества и ресурсов
```

**Для сервера с 64+ GB RAM и GPU 32+ GB:**
```env
OLLAMA_MODEL=codellama:34b  # Или deepseek-coder:33b
```

**Для сервера с 128+ GB RAM и несколькими GPU:**
```env
OLLAMA_MODEL=qwen2.5:72b  # Максимальное качество
```

### Настройка Ollama для больших моделей

```bash
# Установите Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Настройте переменные окружения для больших моделей
export OLLAMA_NUM_GPU=1  # Количество GPU
export OLLAMA_MAX_LOADED_MODELS=1  # Ограничение одновременных моделей

# Запустите Ollama
ollama serve

# В другом терминале загрузите модель
ollama pull qwen2.5-coder:30b

# Проверьте загрузку
ollama list
```

### Оптимизация производительности

**Для GPU:**
```bash
# Используйте CUDA если доступно
export CUDA_VISIBLE_DEVICES=0  # Укажите GPU

# Проверьте использование GPU
nvidia-smi
```

**Для CPU (без GPU):**
```bash
# Увеличьте количество потоков
export OLLAMA_NUM_THREAD=16  # По количеству ядер CPU

# Используйте quantization для экономии памяти
ollama pull qwen2.5-coder:30b-q4_K_M  # Если доступна quantized версия
```

### Тестирование модели

После установки модели протестируйте её:

```bash
# Тест через Ollama API
curl http://localhost:11434/api/generate -d '{
  "model": "qwen2.5-coder:30b",
  "prompt": "Generate SQL to select all users from equsers table",
  "stream": false
}'

# Тест через систему
# В config.env установите:
# LLM_PROVIDER=ollama
# OLLAMA_MODEL=qwen2.5-coder:30b

# Перезапустите сервисы
./run_stack.sh restart core_api

# Протестируйте генерацию SQL
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Покажи всех пользователей",
    "user_id": "test",
    "role": "admin"
  }'
```

### Мониторинг ресурсов

```bash
# Мониторинг использования памяти
watch -n 1 'free -h && echo "---" && ps aux | grep ollama | head -5'

# Мониторинг GPU (если используется)
watch -n 1 nvidia-smi

# Логи Ollama
tail -f ~/.ollama/logs/server.log
```

---

## 📚 Дополнительные ресурсы

- [TRAINING_GUIDE.md](TRAINING_GUIDE.md) - Основное руководство по обучению RAG
- [TRAINING_GUIDE.md](TRAINING_GUIDE.md) - Основное руководство по обучению RAG
- [VECTOR_KB_INTERFACE_GUIDE.md](VECTOR_KB_INTERFACE_GUIDE.md) - Работа с интерфейсом
- [VECTOR_DB.md](VECTOR_DB.md) - Структура векторной базы данных
- [SQL_OPTIMIZATION_TRAINING_GUIDE.md](SQL_OPTIMIZATION_TRAINING_GUIDE.md) - Обучение на оптимизированных SQL

---

## ✅ Итоговая проверка

После завершения всех шагов проверьте:

```bash
# 1. Статистика KB
psql "$DATABASE_URL" -c "
SELECT 
    content_type,
    COUNT(*) as total,
    COUNT(CASE WHEN embedding IS NOT NULL THEN 1 END) as with_embeddings
FROM vanna_vectors 
GROUP BY content_type;
"

# 2. Тест поиска
curl -X POST http://localhost:8000/test-search \
  -H "Content-Type: application/json" \
  -d '{"question": "Покажи всех пользователей", "search_type": "semantic", "limit": 5}' | jq .

# 3. Тест генерации SQL
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Покажи всех пользователей", "user_id": "test", "role": "admin"}' | jq .
```

**Ожидаемый результат:**
- ✅ Все типы контента имеют эмбеддинги (100% coverage)
- ✅ Поиск возвращает релевантные результаты
- ✅ Генерация SQL работает корректно

---

**Поздравляем! Ваша KB обучена и готова к использованию! 🎉**

