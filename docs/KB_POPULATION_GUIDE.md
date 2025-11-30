# Руководство по пополнению Knowledge Base

## Обзор

Этот документ описывает процесс пополнения векторной базы знаний (KB) данными из различных источников, включая структурированные схемы DocStructureSchema, DDL statements и SQL примеры.

## Скрипты загрузки и индексации KB

### 1. Загрузка документации из DocStructureSchema

**Скрипт:** `src/tools/load_docstructure_schema.py`

**Назначение:** Парсит JSON/XML файлы из `data/DocStructureSchema/` и преобразует их в структурированную документацию для KB.

**Что загружает:**
- Общий обзор системы DocStructureSchema
- Бизнес-логика и связи между таблицами
- Документация по таблицам (из `EQDocTypes.json`)
- Описания категорий (из `EQCategories.json`)
- Описания состояний документов (из `EQDocStates.json`)

**Использование:**
```bash
export $(cat config.env | grep -v '^#' | xargs)
python src/tools/load_docstructure_schema.py
```

**Результат:**
- Загружает ~77 документов с типом `documentation`
- Источник: `DocStructureSchema`
- Автоматически использует `KBTrainingClient` с fallback на прямое добавление

---

### 2. Извлечение SQL запросов и DDL из DocStructureSchema

**Скрипт:** `src/tools/extract_sql_from_docstructure.py`

**Назначение:** Извлекает SQL запросы из представлений и DDL statements из SQL файлов.

**Что загружает:**
- Q/A примеры из `EQView.json` (SQL запросы из представлений)
- DDL statements из `TradecoTemplateDBAndDocStructure/TradecoTemplateTestDB.sql`

**Использование:**
```bash
export $(cat config.env | grep -v '^#' | xargs)
python src/tools/extract_sql_from_docstructure.py
```

**Результат:**
- Загружает ~5-10 Q/A примеров с типом `question_sql`
- Загружает ~192 DDL statements с типом `ddl`
- Источник: `DocStructureSchema`

---

### 3. Генерация эмбеддингов

**Скрипт:** `src/tools/generate_embeddings_hf.py`

**Назначение:** Генерирует векторные представления (эмбеддинги) для всех записей в KB без эмбеддингов.

**Использование:**
```bash
export $(cat config.env | grep -v '^#' | xargs)
python -m src.tools.generate_embeddings_hf \
  --dsn "$DATABASE_URL" \
  --model "$HF_MODEL_NAME"
```

**Параметры:**
- `--dsn`: Connection string для PostgreSQL
- `--model`: Модель для генерации эмбеддингов (например, `intfloat/multilingual-e5-base`)
- `--rebuild`: Пересоздать все эмбеддинги (опционально)
- `--batch-size`: Размер батча (по умолчанию 200)

**Результат:**
- Генерирует эмбеддинги для всех записей без них
- Использует GPU если доступно (CUDA)
- Размерность эмбеддингов: 768 (для `multilingual-e5-base`)

---

### 4. Базовое обучение (legacy)

**Скрипт:** `src/vanna/training_script.py`

**Назначение:** Базовый скрипт обучения из файлов `training_data/`.

**Что загружает:**
- DDL из `training_data/ddl_statements.sql`
- Документацию из `training_data/documentation.txt`
- Q/A примеры из `training_data/sql_examples.json`

**Использование:**
```bash
python src/vanna/training_script.py
```

**Примечание:** Рекомендуется использовать специализированные скрипты выше для автоматической загрузки из DocStructureSchema.

---

## Полный процесс пополнения KB

### Шаг 1: Загрузка документации из DocStructureSchema

```bash
# Убедитесь, что Core API запущен
./run_stack.sh start core_api

# Загрузите документацию
export $(cat config.env | grep -v '^#' | xargs)
python src/tools/load_docstructure_schema.py
```

**Ожидаемый результат:**
```
✅ Подключение к API установлено
📖 Загрузка JSON файлов...
  - EQDocTypes: 81 записей
  - EQCategories: 25 записей
  - EQDocStates: 97 записей
📝 Формирование документации...
  - Создано документов: 77
💾 Загрузка в векторную базу...
  ✅ Добавлено: 77
```

---

### Шаг 2: Извлечение SQL и DDL

```bash
python src/tools/extract_sql_from_docstructure.py
```

**Ожидаемый результат:**
```
📖 Извлечение Q/A примеров из представлений...
  - Извлечено Q/A примеров: 5
📖 Извлечение DDL из SQL файла...
  - Найдено DDL statements: 192
💾 Загрузка 5 Q/A примеров...
  ✅ Успешно: 5
💾 Загрузка 192 DDL statements...
  ✅ Добавлено: 192
```

---

### Шаг 3: Генерация эмбеддингов

```bash
python -m src.tools.generate_embeddings_hf \
  --dsn "$DATABASE_URL" \
  --model "$HF_MODEL_NAME"
```

**Ожидаемый результат:**
```
INFO - Records to (re)embed: 15
INFO - Processed 15/15
INFO - Completed: processed 15 records
```

---

## Структура данных в KB

### Типы контента

1. **DDL** (`content_type = 'ddl'`)
   - CREATE TABLE statements
   - Источники: SQL дампы, INFORMATION_SCHEMA, DocStructureSchema

2. **Documentation** (`content_type = 'documentation'`)
   - Текстовая документация о таблицах, бизнес-логике
   - Источники: DocStructureSchema JSON, текстовые файлы

3. **Question_SQL** (`content_type = 'question_sql'`)
   - Пары вопрос-ответ (естественный язык → SQL)
   - Источники: примеры из представлений, ручные примеры

### Метаданные

Каждая запись содержит JSON метаданные:
```json
{
  "type": "documentation",
  "source": "DocStructureSchema",
  "filename": "EQDocTypes.json",
  "table_name": "equsers",
  "domain": "users"
}
```

---

## Проверка состояния KB

### Статистика по типам контента

```sql
SELECT 
  content_type, 
  COUNT(*) as total,
  COUNT(CASE WHEN embedding IS NOT NULL THEN 1 END) as with_embeddings
FROM vanna_vectors 
GROUP BY content_type;
```

### Статистика по источникам

```sql
SELECT 
  metadata->>'source' as source,
  content_type,
  COUNT(*) 
FROM vanna_vectors 
WHERE metadata->>'source' IS NOT NULL
GROUP BY source, content_type
ORDER BY source, content_type;
```

### Последние добавленные записи

```sql
SELECT 
  content_type,
  COUNT(*) as count,
  MAX(created_at) as last_added
FROM vanna_vectors
GROUP BY content_type
ORDER BY content_type;
```

---

## Восстановление KB из дампа

Если у вас есть дамп векторной таблицы (`vanna_vectors_dump.sql`):

```bash
# Восстановление дампа
psql "$DATABASE_URL" < vanna_vectors_dump.sql

# Проверка восстановления
psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM vanna_vectors;"
```

**Примечание:** После восстановления дампа может потребоваться пересоздание индексов pgvector:

```sql
-- Пересоздание индекса для семантического поиска
CREATE INDEX IF NOT EXISTS vanna_vectors_embedding_idx 
ON vanna_vectors 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

---

## Рекомендации

1. **Регулярное пополнение:** Запускайте скрипты загрузки при обновлении данных в `data/DocStructureSchema/`

2. **Проверка эмбеддингов:** После загрузки новых данных всегда запускайте генерацию эмбеддингов

3. **Резервное копирование:** Регулярно создавайте дампы векторной таблицы для быстрого восстановления

4. **Мониторинг качества:** Используйте бенчмарки для проверки качества KB после пополнения

---

## Связанные документы

- [TRAINING_GUIDE.md](TRAINING_GUIDE.md) - Основное руководство по обучению RAG
- [AUTOMATIC_TRAINING_GUIDE.md](AUTOMATIC_TRAINING_GUIDE.md) - Автоматическое обучение KB
- [VECTOR_DB.md](VECTOR_DB.md) - Структура векторной базы данных
- [LOAD_DOCSTRUCTURE_SCHEMA.md](LOAD_DOCSTRUCTURE_SCHEMA.md) - Детали загрузки DocStructureSchema

