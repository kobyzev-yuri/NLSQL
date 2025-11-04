# 🧪 Тестирование интеграции EXPLAIN планов

## 📋 Изменения в коде

### 1. `src/vanna/vanna_semantic_fixed.py`

**Добавлено:**
- Метод `_get_explain_plan(sql)` - генерация EXPLAIN плана для SQL
- Обновлен `add_question_sql()` - автоматическая генерация планов при добавлении
- Обновлен `get_similar_question_sql_with_metadata()` - извлечение планов из metadata

**Изменения:**
```python
# Автоматическая генерация EXPLAIN плана
async def _get_explain_plan(self, sql: str) -> Optional[str]:
    """Генерация EXPLAIN плана для SQL запроса"""
    conn = await asyncpg.connect(self.database_url)
    explain_sql = f"EXPLAIN (FORMAT TEXT) {sql}"
    result = await conn.fetch(explain_sql)
    plan = '\n'.join([row['QUERY PLAN'] for row in result])
    return plan

# При добавлении SQL автоматически генерируется план
async def add_question_sql(self, question: str, sql: str, **kwargs):
    explain_plan = await self._get_explain_plan(sql)  # Автоматическая генерация
    metadata['explain_plan'] = explain_plan  # Сохранение в metadata
```

### 2. `src/services/query_service.py`

**Добавлено:**
- Извлечение EXPLAIN планов из metadata в `_get_rag_context()`
- Форматирование контекста с планами для оптимизированных SQL
- Инструкции по анализу планов в системном промпте

**Изменения:**
```python
# Извлечение планов из metadata
explain_plan = metadata.get('explain_plan')

# Форматирование с планом
if explain_plan:
    formatted_parts.append(f"EXPLAIN PLAN:\n{explain_plan}")

# Системные инструкции
system_instructions = """...
2. Analyze EXPLAIN PLANs in examples to understand performance characteristics:
   - Lower cost (e.g., cost=0.00..35.50) = faster execution
   - Index Scan/Index Only Scan = better than Sequential Scan
..."""
```

### 3. `src/vanna/simple_openai_sql.py`

**Обновлено:**
- Системный промпт с инструкциями по оптимизации и анализу планов

**Изменения:**
```python
system_prompt = f"""You are a PostgreSQL expert. Generate ONLY valid, OPTIMIZED SQL code.

PERFORMANCE OPTIMIZATION RULES (PRIORITY):
1. Use specific column names instead of SELECT *
2. Add WHERE filters to reduce data volume
3. Use INNER JOIN instead of LEFT JOIN when possible
..."""
```

## 🧪 Как протестировать

### Вариант 1: Автоматическое тестирование

Запустите тестовый скрипт:

```bash
cd NLSQL
python -m src.tools.test_explain_plan_integration
```

**Тесты проверяют:**
1. ✅ Генерацию EXPLAIN плана
2. ✅ Добавление Q/A пары с автоматической генерацией плана
3. ✅ Получение Q/A пар с метаданными (включая планы)
4. ✅ Формирование RAG контекста с планами
5. ✅ Формирование промпта с инструкциями по планам

### Вариант 2: Ручное тестирование

#### Шаг 1: Добавление оптимизированного SQL с планом

```python
from src.vanna.vanna_semantic_fixed import create_semantic_vanna_client
import asyncio

async def test():
    vanna = create_semantic_vanna_client()
    
    # Добавляем оптимизированный SQL
    example_id = await vanna.add_question_sql(
        question="Покажи всех активных пользователей",
        sql="SELECT id, login, email FROM equsers WHERE deleted = FALSE",
        sql_basic="SELECT * FROM equsers",
        improvement="50% меньше данных, быстрее выполнение",
        is_optimized=True
    )
    
    print(f"✅ Добавлено с ID: {example_id}")

asyncio.run(test())
```

**Проверка:**
- План должен быть автоматически сгенерирован
- План должен быть сохранен в `metadata.explain_plan`
- Для базового SQL должен быть сохранен `metadata.explain_plan_basic`

#### Шаг 2: Проверка сохраненных планов

```python
import asyncpg
import json

async def check():
    conn = await asyncpg.connect("postgresql://postgres:1234@localhost:5432/test_docstructure")
    
    result = await conn.fetchrow(
        "SELECT metadata FROM vanna_vectors WHERE id = $1",
        12345  # ID из предыдущего шага
    )
    
    metadata = json.loads(result['metadata']) if isinstance(result['metadata'], str) else result['metadata']
    
    print(f"explain_plan: {'✅' if metadata.get('explain_plan') else '❌'}")
    print(f"explain_plan_basic: {'✅' if metadata.get('explain_plan_basic') else '❌'}")
    
    if metadata.get('explain_plan'):
        print("\nПлан оптимизированного SQL:")
        print(metadata['explain_plan'])

asyncio.run(check())
```

#### Шаг 3: Проверка RAG контекста

```python
from src.services.query_service import QueryService

async def test_context():
    service = QueryService()
    
    context = await service._get_rag_context(
        "Покажи активных пользователей",
        domain="users"
    )
    
    print("RAG контекст:")
    print(context)
    
    # Проверяем наличие планов
    if "EXPLAIN PLAN" in context:
        print("\n✅ Планы найдены в контексте!")
    
    # Проверяем приоритизацию
    if "OPTIMIZED SQL EXAMPLES" in context:
        print("✅ Оптимизированные SQL приоритизированы!")

asyncio.run(test_context())
```

#### Шаг 4: Проверка генерации SQL

```bash
# Запустите Core API
./run_stack.sh start core_api

# Отправьте запрос
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Покажи активных пользователей",
    "user_id": "test",
    "role": "admin",
    "department": "IT"
  }'
```

**Проверка:**
- Сгенерированный SQL должен быть оптимизированным
- SQL должен использовать конкретные колонки вместо `SELECT *`
- SQL должен содержать фильтры `WHERE`

### Вариант 3: Интеграционное тестирование через интерфейс

1. **Запустите Vector KB Interface:**
   ```bash
   ./start_vector_kb.sh
   ```

2. **Откройте http://localhost:8503**

3. **Добавьте оптимизированный SQL:**
   - Вкладка "🚀 Оптимизация SQL"
   - Заполните форму: вопрос, sql_basic, sql_optimized, improvement
   - Нажмите "➕ Добавить пару SQL/SQL optimized"
   - Скачайте `optimized_sql_examples.json`

4. **Проверьте через API:**
   - Добавьте пары через API endpoint `/training/example`
   - Проверьте, что планы сгенерированы автоматически

5. **Протестируйте генерацию:**
   - Вкладка "🔍 Тестирование поиска"
   - Введите вопрос и проверьте, что в контексте есть планы
   - Проверьте, что оптимизированные SQL приоритизированы

## 📊 Ожидаемые результаты

### ✅ Успешное тестирование

1. **EXPLAIN планы генерируются автоматически:**
   ```
   ✅ EXPLAIN план успешно сгенерирован
   Seq Scan on equsers  (cost=0.00..35.50 rows=10 width=120)
     Filter: (deleted = false)
   ```

2. **Планы сохраняются в metadata:**
   ```json
   {
     "explain_plan": "Seq Scan on equsers...",
     "explain_plan_basic": "Seq Scan on equsers..."
   }
   ```

3. **Планы включаются в RAG контекст:**
   ```
   ===OPTIMIZED SQL EXAMPLES (PREFERRED):
   Q: Покажи активных пользователей
   A: SELECT id, login FROM equsers WHERE deleted = FALSE
   EXPLAIN PLAN:
   Seq Scan on equsers  (cost=0.00..35.50 rows=10 width=120)
   ```

4. **Промпт содержит инструкции по планам:**
   ```
   PERFORMANCE PRIORITY RULES:
   2. Analyze EXPLAIN PLANs in examples to understand performance characteristics:
      - Lower cost = faster execution
      - Index Scan = better than Sequential Scan
   ```

5. **Модель генерирует оптимизированный SQL:**
   ```sql
   -- Хорошо:
   SELECT id, login, email FROM equsers WHERE deleted = FALSE
   
   -- Плохо:
   SELECT * FROM equsers
   ```

## 🔍 Отладка

### Если планы не генерируются:

1. **Проверьте подключение к БД:**
   ```python
   import asyncpg
   conn = await asyncpg.connect("postgresql://...")
   result = await conn.fetch("EXPLAIN SELECT 1")
   print(result)
   ```

2. **Проверьте права доступа:**
   ```sql
   -- Убедитесь, что пользователь может выполнять EXPLAIN
   EXPLAIN SELECT 1;
   ```

3. **Проверьте логи:**
   ```bash
   tail -f logs/core_api_8000.out
   ```

### Если планы не включаются в контекст:

1. **Проверьте metadata:**
   ```sql
   SELECT id, metadata->>'explain_plan' as plan
   FROM vanna_vectors
   WHERE content_type = 'question_sql'
   LIMIT 5;
   ```

2. **Проверьте метод `get_similar_question_sql_with_metadata`:**
   ```python
   results = await vanna.get_similar_question_sql_with_metadata("test", limit=5)
   for r in results:
       print(r.get('explain_plan'))
   ```

## 📚 Связанные документы

- [TEST_EXPLAIN_PLAN.md](TEST_EXPLAIN_PLAN.md) - Быстрый тест EXPLAIN планов
- [EXPLAIN_PLAN_INTEGRATION.md](EXPLAIN_PLAN_INTEGRATION.md) - Детали реализации
- [SQL_OPTIMIZATION_TRAINING_GUIDE.md](SQL_OPTIMIZATION_TRAINING_GUIDE.md) - Обучение на оптимизированных SQL
- [TRAINING_GUIDE.md](TRAINING_GUIDE.md) - Полное руководство по обучению


