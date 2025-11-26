# 🎓 Руководство по обучению RAG (основной документ)

Этот документ — центральное руководство по обучению RAG в системе NL→SQL: подготовка данных (DDL/документация/Q&A), генерация эмбеддингов, проверка качества и связи с верификационными и отчётными документами.

> **Признательность:** Идеология базового обучения RAG (DDL + Documentation + Q/A пары) основана на подходе библиотеки [vanna-ai](https://github.com/vanna-ai/vanna). Методология контекстного поиска релевантных примеров описана в их исследовании: [AI SQL Accuracy: Testing different LLMs + context strategies](https://github.com/vanna-ai/vanna/blob/v2/papers/ai-sql-accuracy-2023-08-17.md). См. также [их документацию](https://vanna.ai/docs). Наша система расширяет этот подход добавлением оптимизированных SQL с EXPLAIN планами для улучшения производительности генерируемых запросов.

## 📋 Обзор

Векторная база знаний (`vanna_vectors`) хранит три типа контента:
- **DDL** - схемы таблиц
- **Documentation** - документация и бизнес-логика
- **Question_SQL** - Q/A пары (вопрос → SQL)

> **💡 Workflow:** Основная цель - **автоматическое обучение KB** на материалах заказчика (дампах БД, документации, SQL примерах) через скрипты и API. Интерфейс используется для **корректировки уже созданной KB**. См. [AUTOMATIC_TRAINING_GUIDE.md](AUTOMATIC_TRAINING_GUIDE.md) для деталей автоматического обучения.

## 🚀 Варианты обучения

> **⚠️ Важно:** Для добавления Q/A пар рекомендуется использовать унифицированный клиент `KBTrainingClient`, который обеспечивает единообразие между интерфейсом и CLI скриптами, автоматическую генерацию EXPLAIN планов и валидацию оптимизации. См. [KB_TRAINING_UNIFICATION.md](KB_TRAINING_UNIFICATION.md) для деталей.

> **📋 Workflow:** Основная цель скриптов обучения и API - **автоматическое обучение KB на материалах заказчика** (дампах БД, документации, SQL примерах). Интерфейс используется для **корректировки уже созданной KB** после ее автоматического создания.

### 1. Автоматическое обучение из дампов БД и других источников

**Цель:** Автоматически обучить KB на материалах заказчика без ручного вмешательства.

**Типичный сценарий:**
1. Заказчик предоставляет дамп БД, документацию, примеры SQL запросов
2. Скрипты автоматически извлекают DDL из дампа или INFORMATION_SCHEMA
3. Скрипты автоматически добавляют DDL, документацию и Q/A пары через API
4. Генерируются эмбеддинги
5. KB готова к использованию

**Интерфейс используется для:**
- Просмотра и проверки автоматически созданной KB
- Корректировки и добавления недостающих примеров
- Оптимизации SQL запросов

### 2. Базовое обучение (DDL + Документация + Q/A)

**Цель:** Обучить модель понимать схему БД и генерировать рабочий SQL.

**Шаги:**

1. **Добавление DDL:**
   > **Примечание:** Для DDL пока нет API эндпоинта, используется прямое добавление через `vanna`.
   ```python
   from src.vanna.vanna_pgvector_native import DocStructureVannaNative
   
   vanna = DocStructureVannaNative()
   vanna.add_ddl("CREATE TABLE equsers (id SERIAL PRIMARY KEY, ...);")
   ```

2. **Добавление документации:**
   > **Примечание:** Для документации пока нет API эндпоинта, используется прямое добавление через `vanna`.
   ```python
   vanna.add_documentation(
       "Система управления документами DocStructureSchema содержит 12 основных таблиц..."
   )
   ```

3. **Добавление Q/A пар (рекомендуемый способ - через унифицированный клиент):**
   
   **✅ Предпочтительный способ (через API):**
   ```python
   from src.tools.kb_training_client import KBTrainingClient
   
   client = KBTrainingClient(api_base_url="http://localhost:8000")
   client.add_training_example(
       question="Покажи всех пользователей",
       sql="SELECT id, login, email FROM equsers WHERE deleted = FALSE"
   )
   ```
   
   Или массовое добавление из JSON файла:
   ```bash
   python -m src.tools.kb_training_client --file training_data/sql_examples.json
   ```
   
   **⚠️ Legacy способ (прямое добавление через vanna):**
   ```python
   from src.vanna.vanna_pgvector_native import DocStructureVannaNative
   
   vanna = DocStructureVannaNative()
   vanna.add_question_sql(
       question="Покажи всех пользователей",
       sql="SELECT id, login, email FROM equsers WHERE deleted = FALSE"
   )
   ```
   > **Примечание:** Используйте этот способ только если Core API недоступен. Унифицированный клиент автоматически использует fallback на прямое добавление при недоступности API.

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

2. **Добавление оптимизированных Q/A (рекомендуемый способ - через унифицированный клиент):**
   
   **✅ Предпочтительный способ (через API с автоматической генерацией EXPLAIN планов):**
   ```python
   from src.tools.kb_training_client import KBTrainingClient
   
   client = KBTrainingClient(api_base_url="http://localhost:8000")
   client.add_training_example(
       question="Покажи всех пользователей",
       sql="SELECT id, login, email FROM equsers WHERE deleted = FALSE",  # оптимизированный
       sql_basic="SELECT * FROM equsers",  # базовый для сравнения
       improvement="50% меньше данных, быстрее выполнение"
   )
   ```
   > **Преимущества:** Автоматическая генерация EXPLAIN планов, валидация оптимизации через сравнение планов выполнения.
   
   **⚠️ Legacy способ (прямое добавление через vanna):**
   ```python
   from src.vanna.vanna_pgvector_native import DocStructureVannaNative
   
   vanna = DocStructureVannaNative()
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

### 3. Массовое добавление через интерфейс или CLI

> **✅ Рекомендуется:** Использовать унифицированный клиент `KBTrainingClient` для всех операций с Q/A парами. См. [KB_TRAINING_UNIFICATION.md](KB_TRAINING_UNIFICATION.md) для деталей архитектуры.

**Через Vector KB Interface (http://localhost:8503):**

1. **Вкладка "Добавление новых Q/A пар":**
   - Ручное добавление: введите `question` и `sql` → использует API `/training/example`
   - Массовое добавление: загрузите JSON файл → использует `KBTrainingClient` через API

2. **Вкладка "Оптимизация SQL":**
   - Добавьте пару SQL/SQL optimized → использует API `/training/example`
   - Скачайте `optimized_sql_examples.json`

**Через CLI скрипт (унифицированный клиент):**

```bash
# Массовое добавление из JSON файла через API
python -m src.tools.kb_training_client --file training_data/sql_examples.json

# С указанием API URL
python -m src.tools.kb_training_client --file qa_pairs.json --api-url http://localhost:8000

# Тихий режим (без подробного вывода)
python -m src.tools.kb_training_client --file examples.json --quiet
```

**Через Python API:**

```python
from src.tools.kb_training_client import KBTrainingClient
from pathlib import Path

client = KBTrainingClient(api_base_url="http://localhost:8000")

# Массовое добавление из файла
stats = client.add_from_json_file(
    json_file=Path("training_data/sql_examples.json"),
    user_id="my_script"
)

print(f"Добавлено: {stats['success']}/{stats['total']}")
```

**Важно:** Все операции обучения Q/A пар используют единый API (`/training/example`), что обеспечивает:
- Единообразие логики добавления (интерфейс и скрипты используют один код)
- Автоматическую генерацию EXPLAIN планов для оптимизированных SQL
- Валидацию оптимизации через сравнение планов выполнения
- Централизованную логику и удобство отладки

**Быстрый гайд:** [QUICK_ADD_OPTIMIZED_SQL.md](QUICK_ADD_OPTIMIZED_SQL.md)

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

**Быстрый тест:** [QUICK_TEST.md](QUICK_TEST.md)

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

- [QUICK_ADD_OPTIMIZED_SQL.md](https://github.com/kobyzev-yuri/NLSQL/blob/main/docs/QUICK_ADD_OPTIMIZED_SQL.md) — быстрое добавление оптимизированного SQL
- [QUICK_TEST.md](https://github.com/kobyzev-yuri/NLSQL/blob/main/docs/QUICK_TEST.md) — быстрый тест EXPLAIN планов
- [TEST_EXPLAIN_PLAN.md](https://github.com/kobyzev-yuri/NLSQL/blob/main/docs/TEST_EXPLAIN_PLAN.md) — тестирование EXPLAIN планов
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


