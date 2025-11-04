# 🧪 Быстрый тест: EXPLAIN планы в оптимизированных SQL

## ✅ Да, планы появятся автоматически!

При добавлении оптимизированного SQL через API или интерфейс:
- ✅ План для оптимизированного SQL → `metadata.explain_plan`
- ✅ План для базового SQL → `metadata.explain_plan_basic`
- ✅ Планы включаются в RAG контекст при генерации SQL

## 🚀 Быстрый тест

### Вариант 1: Автоматический тест

```bash
cd NLSQL
python -m src.tools.test_optimized_sql_with_plan
```

**Что проверяет:**
1. ✅ Оптимизированный SQL → планы генерируются
2. ✅ Обычный SQL → планы НЕ генерируются
3. ✅ Планы сохраняются в metadata
4. ✅ Планы попадают в RAG контекст

### Вариант 2: Через интерфейс

1. Запустите Core API:
   ```bash
   ./run_stack.sh start core_api
   ```

2. Запустите Vector KB:
   ```bash
   ./start_vector_kb.sh
   ```

3. Откройте http://localhost:8503

4. Вкладка "🚀 Оптимизация SQL":
   - Вопрос: "Покажи всех пользователей"
   - SQL базовый: `SELECT * FROM equsers`
   - SQL оптимизированный: `SELECT id, login, email FROM equsers WHERE deleted = FALSE`
   - Нажмите "💾 Добавить в векторную базу (с EXPLAIN планом)"

5. **Проверьте результат:**
   - ✅ Должно появиться сообщение "✅ Оптимизированный SQL добавлен"
   - ✅ Должны быть показаны EXPLAIN планы (если API их возвращает)
   - ✅ Планы сохранены в `metadata.explain_plan` и `metadata.explain_plan_basic`

### Вариант 3: Через API напрямую

```bash
curl -X POST http://localhost:8000/training/example \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Покажи всех пользователей",
    "sql": "SELECT id, login, email FROM equsers WHERE deleted = FALSE",
    "user_id": "test",
    "verified": true,
    "sql_basic": "SELECT * FROM equsers",
    "sql_optimized": "SELECT id, login, email FROM equsers WHERE deleted = FALSE",
    "improvement": "50% меньше данных",
    "is_optimized": true
  }'
```

**Ответ должен содержать:**
```json
{
  "success": true,
  "message": "Пример успешно добавлен",
  "example_id": "...",
  "explain_plan": "Seq Scan on equsers  (cost=0.00..35.50 rows=10 width=120)...",
  "explain_plan_basic": "Seq Scan on equsers  (cost=0.00..150.50 rows=100 width=500)..."
}
```

### Вариант 4: Проверка в БД

```sql
-- Проверяем, что планы сохранены
SELECT 
    id,
    metadata->>'is_optimized' as is_optimized,
    CASE 
        WHEN metadata->>'explain_plan' IS NOT NULL THEN '✅ ЕСТЬ'
        ELSE '❌ НЕТ'
    END as explain_plan,
    CASE 
        WHEN metadata->>'explain_plan_basic' IS NOT NULL THEN '✅ ЕСТЬ'
        ELSE '❌ НЕТ'
    END as explain_plan_basic,
    LEFT(metadata->>'explain_plan', 50) as plan_preview
FROM vanna_vectors
WHERE content_type = 'question_sql'
  AND metadata->>'is_optimized' = 'true'
ORDER BY id DESC
LIMIT 5;
```

## 📊 Ожидаемый результат

### ✅ Успешно:
- Планы генерируются **только** для оптимизированных SQL
- Планы сохраняются в `metadata.explain_plan` и `metadata.explain_plan_basic`
- Планы включаются в RAG контекст при генерации SQL
- Обычные Q/A пары добавляются **без** планов (быстро)

### ❌ Проблемы:
- Если планы не генерируются → проверьте подключение к БД
- Если планы не сохраняются → проверьте права на запись в `vanna_vectors`
- Если планы не попадают в контекст → проверьте `get_similar_question_sql_with_metadata`

## 🔍 Проверка в коде

Логика генерации планов (строка 202-204 в `vanna_semantic_fixed.py`):
```python
# Флаг для генерации планов: только для оптимизированных SQL
generate_plan = kwargs.get('generate_explain_plan', False)  # По умолчанию False
if is_optimized:
    generate_plan = True  # Автоматически включается для оптимизированных SQL
```

**Планы генерируются если:**
- ✅ `is_optimized=True` ИЛИ есть `sql_basic` ИЛИ есть `sql_optimized`
- ✅ Явно указано `generate_explain_plan=True`

**Планы НЕ генерируются если:**
- ❌ Обычная Q/A пара без `is_optimized` и `sql_basic`
- ❌ Массовое добавление обычных Q/A пар

## ✅ Готово к тестированию!

Запустите тест и проверьте, что планы появляются в оптимизированных SQL.


