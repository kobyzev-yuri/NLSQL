# 🏷️ Маркировка оптимизированных SQL в векторной базе

## 📋 Обзор

Оптимизированные SQL помечаются **явной маркировкой в `content`** и **метаданными в `metadata``. Это позволяет агенту (LLM) сразу видеть оптимизированные примеры в RAG контексте.

## 🎯 Два уровня маркировки

### 1. **Явная маркировка в `content`** (для агента)

При добавлении оптимизированного SQL в `content` автоматически добавляется маркировка:

```
[OPTIMIZED SQL: улучшение производительности]
Q: Покажи активных пользователей
A: SELECT id, login, email FROM equsers WHERE deleted = FALSE
[BASIC SQL (for comparison)]: SELECT * FROM equsers
```

**Формат:**
- `[OPTIMIZED SQL]` - базовая маркировка
- `[OPTIMIZED SQL: описание улучшения]` - с описанием улучшения
- `[BASIC SQL (for comparison)]: базовый SQL` - для сравнения

**Преимущества:**
- ✅ Агент (LLM) **сразу видит** маркировку при чтении контекста
- ✅ Не нужно парсить JSON metadata
- ✅ Явно указывает на приоритет оптимизированных примеров

### 2. **Метаданные в `metadata`** (основной источник)

```json
{
  "type": "question_sql",
  "question": "Покажи активных пользователей",
  "sql": "SELECT id, login, email FROM equsers WHERE deleted = FALSE",
  "is_optimized": true,
  "sql_basic": "SELECT * FROM equsers",
  "sql_optimized": "SELECT id, login, email FROM equsers WHERE deleted = FALSE",
  "improvement": "Меньше данных, быстрее выполнение",
  "explain_plan": "QUERY PLAN\n...",
  "explain_plan_basic": "QUERY PLAN\n..."
}
```

**Поля:**
- `is_optimized: true` - флаг оптимизации
- `sql_basic` - базовый SQL для сравнения
- `sql_optimized` - оптимизированный SQL
- `improvement` - описание улучшения
- `explain_plan` - план выполнения оптимизированного SQL
- `explain_plan_basic` - план выполнения базового SQL

## 🔍 Как это работает

### При добавлении SQL (`add_question_sql`)

```python
await vanna.add_question_sql(
    question="Покажи активных пользователей",
    sql="SELECT id, login, email FROM equsers WHERE deleted = FALSE",
    sql_basic="SELECT * FROM equsers",
    improvement="Меньше данных, быстрее выполнение",
    is_optimized=True
)
```

**Результат в БД:**

```sql
-- content (с явной маркировкой):
[OPTIMIZED SQL: Меньше данных, быстрее выполнение]
Q: Покажи активных пользователей
A: SELECT id, login, email FROM equsers WHERE deleted = FALSE
[BASIC SQL (for comparison)]: SELECT * FROM equsers

-- metadata (JSON):
{
  "is_optimized": true,
  "sql_basic": "SELECT * FROM equsers",
  "improvement": "Меньше данных, быстрее выполнение",
  "explain_plan": "...",
  "explain_plan_basic": "..."
}
```

### При поиске (`get_similar_question_sql_with_metadata`)

Метод распознает маркировку из **обоих источников**:

1. **Проверяет `metadata.is_optimized`** (основной источник)
2. **Проверяет `content` на наличие `[OPTIMIZED SQL]`** (явная маркировка)
3. **Извлекает `improvement` из content**, если нет в metadata

**Сортировка:** Оптимизированные SQL получают приоритет (даже при большем семантическом расстоянии).

### При формировании RAG контекста (`_get_rag_context`)

Оптимизированные SQL помещаются в отдельную секцию:

```
===OPTIMIZED SQL EXAMPLES (PREFERRED - Use these patterns for efficiency):
[OPTIMIZED SQL: Меньше данных, быстрее выполнение]
Q: Покажи активных пользователей
A: SELECT id, login, email FROM equsers WHERE deleted = FALSE
[BASIC SQL (for comparison)]: SELECT * FROM equsers
EXPLAIN PLAN:
QUERY PLAN
...

===ADDITIONAL SQL EXAMPLES (reference):
Q: Покажи всех пользователей
A: SELECT * FROM equsers
...
```

## ✅ Преимущества подхода

1. **Явная видимость для агента:**
   - Маркировка `[OPTIMIZED SQL]` сразу видна в контексте
   - Агент не нужно парсить JSON для понимания приоритета

2. **Двойная проверка:**
   - `metadata.is_optimized` - основной источник
   - `content` маркировка - резервный источник
   - Гарантирует распознавание даже при ошибках в metadata

3. **Приоритизация:**
   - Оптимизированные SQL всегда в топе результатов
   - Секция "OPTIMIZED SQL EXAMPLES" в контексте
   - Системные инструкции в промпте

4. **Сравнение:**
   - Базовый SQL доступен для сравнения
   - EXPLAIN планы показывают разницу в производительности

## 🔧 Проверка маркировки

### SQL запрос

```sql
-- Проверка маркировки в content
SELECT 
    id,
    CASE 
        WHEN content LIKE '%[OPTIMIZED SQL]%' THEN '✅ Маркировано'
        ELSE '❌ Не маркировано'
    END as content_marker,
    CASE 
        WHEN metadata->>'is_optimized' = 'true' THEN '✅ В metadata'
        ELSE '❌ Нет в metadata'
    END as metadata_marker,
    LEFT(content, 100) as content_preview
FROM vanna_vectors
WHERE content_type = 'question_sql'
ORDER BY id DESC
LIMIT 10;
```

### Python скрипт

```python
import asyncio
from src.vanna.vanna_semantic_fixed import create_semantic_vanna_client

async def check_marking():
    vanna = create_semantic_vanna_client()
    
    results = await vanna.get_similar_question_sql_with_metadata(
        "Покажи активных пользователей",
        limit=5
    )
    
    for r in results:
        print(f"Optimized: {r['is_optimized']}, Content: {r['content'][:100]}")

asyncio.run(check_marking())
```

## 📚 Связанные документы

- [TRAINING_GUIDE.md](TRAINING_GUIDE.md) - Полное руководство по обучению
- [SQL_OPTIMIZATION_TRAINING_GUIDE.md](SQL_OPTIMIZATION_TRAINING_GUIDE.md) - Обучение на оптимизированных SQL
- [EXPLAIN_PLAN_INTEGRATION.md](EXPLAIN_PLAN_INTEGRATION.md) - Интеграция EXPLAIN планов



