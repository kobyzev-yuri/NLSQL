# 🎓 Руководство по обучению RAG (основной документ)

Этот документ — центральное руководство по обучению RAG в системе NL→SQL: подготовка данных (DDL/документация/Q&A), генерация эмбеддингов, проверка качества и связи с верификационными и отчётными документами.

## 📋 Обзор

Векторная база знаний (`vanna_vectors`) хранит три типа контента:
- **DDL** - схемы таблиц
- **Documentation** - документация и бизнес-логика
- **Question_SQL** - Q/A пары (вопрос → SQL)

## 🚀 Варианты обучения

### 1. Базовое обучение (DDL + Документация + Q/A)

**Цель:** Обучить модель понимать схему БД и генерировать рабочий SQL.

**Шаги:**

1. **Добавление DDL:**
   ```python
   from src.vanna.vanna_pgvector_native import DocStructureVannaNative
   
   vanna = DocStructureVannaNative()
   vanna.add_ddl("CREATE TABLE equsers (id SERIAL PRIMARY KEY, ...);")
   ```

2. **Добавление документации:**
   ```python
   vanna.add_documentation(
       "Система управления документами DocStructureSchema содержит 12 основных таблиц..."
   )
   ```

3. **Добавление Q/A пар:**
   ```python
   vanna.add_question_sql(
       question="Покажи всех пользователей",
       sql="SELECT id, login, email FROM equsers WHERE deleted = FALSE"
   )
   ```

4. **Генерация эмбеддингов:**
   ```bash
   python -m src.tools.generate_embeddings_hf \
     --dsn "$DATABASE_URL" \
     --model "$HF_MODEL_NAME"
   ```

Рекомендуемая модель эмбеддингов: `intfloat/multilingual-e5-base` (768d). Убедитесь, что столбец `embedding` имеет размерность 768 (см. `docs/VECTOR_DB.md`).

**Формат Q/A пар (JSON):**
```json
[
    {
        "question": "Покажи всех пользователей",
        "sql": "SELECT id, login, email FROM equsers WHERE deleted = FALSE"
    }
]
```

### 2. Обучение на оптимизированных SQL

**Цель:** Обучить модель генерировать не просто рабочий, а **эффективный SQL** с учетом производительности.

**Шаги:**

1. **Подготовка файла `optimized_sql_examples.json`:**
   ```json
   [
       {
           "question": "Покажи всех пользователей",
           "sql_basic": "SELECT * FROM equsers",
           "sql_optimized": "SELECT id, login, email FROM equsers WHERE deleted = FALSE",
           "improvement": "50% меньше данных, быстрее выполнение"
       }
   ]
   ```

2. **Добавление оптимизированных Q/A:**
   ```python
   vanna.add_question_sql(
       question="Покажи всех пользователей",
       sql="SELECT id, login, email FROM equsers WHERE deleted = FALSE",  # оптимизированный
       sql_basic="SELECT * FROM equsers",  # базовый для сравнения
       improvement="50% меньше данных, быстрее выполнение",
       is_optimized=True
   )
   ```

3. **Генерация эмбеддингов:**
   ```bash
   python -m src.tools.generate_embeddings_hf \
     --dsn "$DATABASE_URL" \
     --model "$HF_MODEL_NAME"
   ```

**Хранение в векторной базе:**
- Оптимизированные SQL хранятся как обычные Q/A пары (`content_type='question_sql'`)
- В `metadata` сохраняется:
  - `is_optimized: true`
  - `sql_basic` - базовый SQL
  - `sql_optimized` - оптимизированный SQL
  - `improvement` - описание улучшения

**Использование:**
- При семантическом поиске оптимизированные SQL находятся как обычные Q/A
- Модель видит оптимизированные примеры в контексте и учится генерировать эффективный SQL

### 3. Массовое добавление через интерфейс

**Через Vector KB Interface (http://localhost:8503):**

1. **Вкладка "Добавление новых Q/A пар":**
   - Ручное добавление: введите `question` и `sql`
   - Массовое добавление: загрузите JSON файл

2. **Вкладка "Оптимизация SQL":**
   - Добавьте пару SQL/SQL optimized
   - Скачайте `optimized_sql_examples.json`
   - Используйте для скрипта `optimize`

**Формат для массового добавления:**
```json
[
    {
        "question": "Покажи всех пользователей",
        "sql": "SELECT id, login, email FROM equsers WHERE deleted = FALSE",
        "sql_basic": "SELECT * FROM equsers",  // опционально
        "improvement": "50% меньше данных"      // опционально
    }
]
```

## 📊 Форматы данных

### Формат 1: Обычные Q/A пары (для базового обучения)
```json
{
    "question": "Покажи всех пользователей",
    "sql": "SELECT id, login, email FROM equsers WHERE deleted = FALSE"
}
```

### Формат 2: Оптимизированные SQL (для обучения на оптимизации)
```json
{
    "question": "Покажи всех пользователей",
    "sql_basic": "SELECT * FROM equsers",
    "sql_optimized": "SELECT id, login, email FROM equsers WHERE deleted = FALSE",
    "improvement": "50% меньше данных, быстрее выполнение"
}
```

**Важно:** При добавлении через `add_question_sql()`:
- Если есть `sql_optimized`, он используется как основной `sql`
- `sql_basic` сохраняется в `metadata` для сравнения
- Флаг `is_optimized` устанавливается автоматически

## 🔧 Инструменты

### 1. Генерация эмбеддингов
```bash
python -m src.tools.generate_embeddings_hf \
  --dsn "$DATABASE_URL" \
  --model "$HF_MODEL_NAME" \
  [--rebuild] [--alter] [--batch-size 200]
```

**Флаги:**
- `--rebuild` - полная перестройка всех эмбеддингов
- `--alter` - автоматическое изменение размерности столбца (384 → 768)
- `--batch-size` - размер батча для обработки

### 2. Проверка эмбеддингов
```bash
python -m src.tools.check_embeddings --database-url "$DATABASE_URL"
```

### 3. Тестирование KB
```bash
python -m src.tools.kb_benchmark \
  --paraphrases 0 --retriever-only \
  --topk 25 --max-questions 50 \
  --output docs/RETRIEVAL_BENCHMARKS.md \
  --report reports/kb_benchmark_report.json
```

Альтернативно, быстрая проверка через API:
```bash
curl -X POST http://localhost:8000/semantic-search \
  -H "Content-Type: application/json" \
  -d '{"query":"Покажи всех пользователей","limit":5}' | jq .
```

## 📝 Рекомендации

1. **Начните с базового обучения:**
   - Добавьте DDL всех таблиц
   - Добавьте документацию по бизнес-логике
   - Добавьте базовые Q/A пары

2. **Затем добавьте оптимизированные SQL:**
   - Для часто используемых запросов
   - Для медленных запросов
   - Для запросов с большим объемом данных

3. **Регулярно тестируйте качество:**
   - Используйте `kb_benchmark.py` для оценки точности
   - Анализируйте отчеты и дообучайте на проблемных случаях

4. **Генерируйте эмбеддинги после каждого обучения:**
   - После добавления новых данных
   - После изменения модели эмбеддингов
   - После миграции размерности

## 🔍 Где хранятся оптимизированные SQL?

**Ответ:** В той же таблице `vanna_vectors` с `content_type='question_sql'`, как и обычные Q/A пары.

**Отличие:** В `metadata` содержится дополнительная информация:
```json
{
    "type": "question_sql",
    "question": "Покажи всех пользователей",
    "sql": "SELECT id, login, email FROM equsers WHERE deleted = FALSE",
    "is_optimized": true,
    "sql_basic": "SELECT * FROM equsers",
    "sql_optimized": "SELECT id, login, email FROM equsers WHERE deleted = FALSE",
    "improvement": "50% меньше данных, быстрее выполнение"
}
```

**При поиске:**
- Семантический поиск находит оптимизированные SQL как обычные Q/A
- Модель видит оптимизированные примеры в контексте
- Модель учится генерировать эффективный SQL, видя примеры оптимизации

## ✅ Проверка обучения (примеры)

На основе отчётов от 2025‑11‑04 (см. `docs/RETRIEVAL_BENCHMARKS.md`, `reports/kb_benchmark_report.json`):

- Запрос: «Покажи всех пользователей» → Top‑1: `question_sql` (метод: seen), Accuracy набора: 1.000 (50/50)
- Запрос: «Поручения за последний месяц» → Top‑1: `question_sql` (seen)
- Запрос: «Сумма платежей по месяцам» → Top‑1: `question_sql` (seen)

Быстрая команда для повторной проверки:
```bash
curl -X POST http://localhost:8000/semantic-search \
  -H "Content-Type: application/json" \
  -d '{"query":"Сумма платежей по месяцам","limit":5}' | jq .
```

## 📚 Связанные документы

- [VECTOR_DB.md](https://github.com/kobyzev-yuri/NLSQL/blob/main/docs/VECTOR_DB.md) — структура/индексация векторной таблицы (pgvector, 768d)
- [SQL_OPTIMIZATION_TRAINING_GUIDE.md](https://github.com/kobyzev-yuri/NLSQL/blob/main/docs/SQL_OPTIMIZATION_TRAINING_GUIDE.md) — детали обучения на оптимизированных SQL
- [OPTIMIZED_SQL_MARKING.md](https://github.com/kobyzev-yuri/NLSQL/blob/main/docs/OPTIMIZED_SQL_MARKING.md) — маркировка оптимизированных примеров
- [EXPLAIN_PLAN_INTEGRATION.md](https://github.com/kobyzev-yuri/NLSQL/blob/main/docs/EXPLAIN_PLAN_INTEGRATION.md) — интеграция EXPLAIN планов в контекст RAG
- [EXPLAIN_PLAN_OPTIMIZATION.md](https://github.com/kobyzev-yuri/NLSQL/blob/main/docs/EXPLAIN_PLAN_OPTIMIZATION.md) — использование планов при оптимизации
- [EXPLAIN_PLAN_USAGE_ANALYSIS.md](https://github.com/kobyzev-yuri/NLSQL/blob/main/docs/EXPLAIN_PLAN_USAGE_ANALYSIS.md) — анализ применения планов
- [KB_TESTING_GUIDE.md](https://github.com/kobyzev-yuri/NLSQL/blob/main/docs/KB_TESTING_GUIDE.md) — методика тестирования KB
- [RETRIEVAL_BENCHMARKS.md](https://github.com/kobyzev-yuri/NLSQL/blob/main/docs/RETRIEVAL_BENCHMARKS.md) — сверка Top‑1/Top‑3/MRR и Accuracy
- [RAG_QUALITY_REPORT.md](https://github.com/kobyzev-yuri/NLSQL/blob/main/docs/RAG_QUALITY_REPORT.md) — отчёт по качеству ретривера
- [TEST_RESULTS.md](https://github.com/kobyzev-yuri/NLSQL/blob/main/docs/TEST_RESULTS.md) — результаты экспериментов (EXPLAIN, оптимизация)
- [EVALUATION_METHODOLOGY.md](https://github.com/kobyzev-yuri/NLSQL/blob/main/docs/EVALUATION_METHODOLOGY.md) — методика оценки качества SQL
- [METRICS_EXPLANATION.md](https://github.com/kobyzev-yuri/NLSQL/blob/main/docs/METRICS_EXPLANATION.md) — справочник по метрикам
- [SERVICES_STARTUP_GUIDE.md](https://github.com/kobyzev-yuri/NLSQL/blob/main/docs/SERVICES_STARTUP_GUIDE.md) — запуск/порты/проверки
- [VECTOR_KB_INTERFACE_GUIDE.md](https://github.com/kobyzev-yuri/NLSQL/blob/main/docs/VECTOR_KB_INTERFACE_GUIDE.md) — работа с интерфейсом


