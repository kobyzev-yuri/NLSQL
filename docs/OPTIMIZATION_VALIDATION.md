# ✅ Валидация оптимизации SQL

## 🎯 Проблема

При добавлении оптимизированного SQL может быть ошибка:
- Пользователь может случайно добавить **неоптимизированный** SQL как "оптимизированный"
- Может быть добавлен SQL, который **хуже** базового по производительности
- Нет проверки, что оптимизированный SQL **действительно лучше**

## ✅ Решение

Добавлена **автоматическая валидация** при добавлении оптимизированного SQL:
- Сравниваются **три метрики** из EXPLAIN планов: `cost`, `width`, `rows`
- Валидация проходит если **хотя бы одна метрика лучше** (cost меньше, width меньше, или rows меньше)
- Если оптимизированный SQL не лучше по всем метрикам → предупреждение и пометка в metadata
- Сохраняются все метрики сравнения для прозрачности

## 📋 Как работает валидация

### Шаг 1: Генерация EXPLAIN планов

При добавлении оптимизированного SQL с `sql_basic`:
1. Генерируется EXPLAIN план для базового SQL
2. Генерируется EXPLAIN план для оптимизированного SQL

### Шаг 2: Извлечение метрик

Из планов извлекаются три метрики:
```python
# Пример плана:
Seq Scan on equsers  (cost=0.00..59.24 rows=1117 width=55)
                      ^^^^^^^^^^^^^^^^^^ ^^^^^^ ^^^^^^
                      cost_max          rows  width

# Извлекаем:
cost = 59.24   # Максимальный cost (верхняя граница)
rows = 1117    # Ожидаемое количество строк
width = 55     # Средний размер строки в байтах
```

### Шаг 3: Сравнение и валидация

Проверяются **все три метрики**, валидация проходит если **хотя бы одна лучше**:

```python
# Базовый SQL
basic_cost = 306.28
basic_width = 17438
basic_rows = 1

# Оптимизированный SQL
optimized_cost = 306.30  # НЕ лучше (немного больше из-за ORDER BY)
optimized_width = 554    # ЛУЧШЕ (96.8% уменьшение!)
optimized_rows = 1       # Без изменений

# Проверка: хотя бы одна метрика лучше
is_better = False
better_criteria = []

if optimized_cost < basic_cost:
    is_better = True
    better_criteria.append('cost')  # Не выполнится

if optimized_width < basic_width:
    is_better = True
    better_criteria.append('width')  # ✅ Выполнится!

if optimized_rows < basic_rows:
    is_better = True
    better_criteria.append('rows')  # Не выполнится

# Результат: is_better = True, better_criteria = ['width']
# ✅ Валидация пройдена: оптимизированный SQL лучше (width улучшение: 96.8%)
```

**Логика валидации:**
- ✅ **Валидация проходит** если хотя бы одна метрика лучше
- ⚠️ **Валидация не проходит** только если ВСЕ метрики хуже или равны

### Шаг 4: Сохранение результатов

В `metadata` сохраняются все метрики:
```json
{
  "cost_basic": 306.28,
  "cost_optimized": 306.30,
  "cost_improvement_percent": -0.01,  // Может быть отрицательным!
  "width_basic": 17438,
  "width_optimized": 554,
  "width_improvement_percent": 96.82,  // Значительное улучшение!
  "rows_basic": 1,
  "rows_optimized": 1,
  "rows_improvement_percent": 0.0,
  "optimization_validated": true,  // true если хотя бы одна метрика лучше
  "optimization_warning": null     // null если валидация прошла, иначе текст предупреждения
}
```

## 🔍 Примеры использования

### Пример 1: Успешная валидация

```python
await vanna.add_question_sql(
    question="Покажи активных пользователей",
    sql="SELECT id, login, email FROM equsers WHERE deleted = FALSE",
    sql_basic="SELECT * FROM equsers",
    improvement="Меньше данных, быстрее выполнение",
    is_optimized=True
)
```

**Результат:**
```
✅ Валидация пройдена: оптимизированный SQL лучше 
   (улучшения: cost: 50.9%, width: 0.0%, rows: 0.0%, лучшие критерии: cost)
```

**Metadata:**
```json
{
  "optimization_validated": true,
  "cost_basic": 120.50,
  "cost_optimized": 59.24,
  "cost_improvement_percent": 50.9,
  "width_basic": 55,
  "width_optimized": 55,
  "width_improvement_percent": 0.0,
  "rows_basic": 1117,
  "rows_optimized": 1117,
  "rows_improvement_percent": 0.0
}
```

### Пример 1.1: Улучшение width (реальный случай)

**Вопрос:** "Поручения за последний месяц"

**Базовый SQL:**
```sql
SELECT * FROM tbl_principal_assignment 
WHERE creationdatetime >= CURRENT_DATE - INTERVAL '1 month' AND deleted = false
```

**Оптимизированный SQL:**
```sql
SELECT reg_number, total_sum, creationdatetime, name, principal_name
FROM tbl_principal_assignment 
WHERE creationdatetime >= CURRENT_DATE - INTERVAL '1 month' AND deleted = false
ORDER BY creationdatetime DESC
```

**Результат валидации:**
```
✅ Валидация пройдена: оптимизированный SQL лучше 
   (улучшения: cost: -0.01%, width: 96.82%, rows: 0.0%, лучшие критерии: width)
```

**EXPLAIN планы:**
- Базовый: `Seq Scan (cost=0.00..306.28 rows=1 width=17438)`
- Оптимизированный: `Sort (cost=306.29..306.30 rows=1 width=554)`

**Анализ:**
- Cost: 306.30 vs 306.28 (-0.01%) - небольшое ухудшение из-за ORDER BY
- Width: 554 vs 17438 (+96.82%) - **значительное улучшение!**
- Валидация прошла, т.к. width намного лучше

### Пример 2: Неудачная валидация

```python
await vanna.add_question_sql(
    question="Покажи всех пользователей",
    sql="SELECT * FROM equsers JOIN ...",  # Хуже из-за JOIN
    sql_basic="SELECT * FROM equsers",     # Проще и быстрее
    is_optimized=True
)
```

**Результат:**
```
⚠️ ВНИМАНИЕ: Оптимизированный SQL НЕ лучше базового!
   Базовый: cost=59.24, width=55, rows=1117
   Оптимизированный: cost=120.50, width=55, rows=1117
   Рекомендуется проверить правильность оптимизации.
```

**Metadata:**
```json
{
  "optimization_validated": false,
  "cost_basic": 59.24,
  "cost_optimized": 120.50,
  "cost_improvement_percent": -103.4,
  "width_basic": 55,
  "width_optimized": 55,
  "width_improvement_percent": 0.0,
  "rows_basic": 1117,
  "rows_optimized": 1117,
  "rows_improvement_percent": 0.0,
  "optimization_warning": "⚠️ ВНИМАНИЕ: Оптимизированный SQL НЕ лучше базового!..."
}
```

## 📊 API Response

При добавлении через API возвращается:

```json
{
  "success": true,
  "example_id": "12497",
  "explain_plan": "Sort (cost=306.29..306.30 rows=1 width=554)...",
  "explain_plan_basic": "Seq Scan (cost=0.00..306.28 rows=1 width=17438)...",
  "optimization_validated": true,
  "cost_basic": 306.28,
  "cost_optimized": 306.30,
  "cost_improvement_percent": -0.01,
  "width_basic": 17438,
  "width_optimized": 554,
  "width_improvement_percent": 96.82,
  "rows_basic": 1,
  "rows_optimized": 1,
  "rows_improvement_percent": 0.0,
  "optimization_warning": null
}
```

Если валидация не пройдена:
```json
{
  "optimization_validated": false,
  "cost_basic": 59.24,
  "cost_optimized": 120.50,
  "cost_improvement_percent": -103.4,
  "width_basic": 55,
  "width_optimized": 55,
  "width_improvement_percent": 0.0,
  "rows_basic": 1117,
  "rows_optimized": 1117,
  "rows_improvement_percent": 0.0,
  "optimization_warning": "⚠️ ВНИМАНИЕ: Оптимизированный SQL НЕ лучше базового!..."
}
```

## 🔧 Проверка валидации в БД

```sql
-- Найти все оптимизированные SQL с результатами валидации
SELECT 
    id,
    metadata->>'question' as question,
    metadata->>'optimization_validated' as validated,
    (metadata->>'cost_basic')::numeric as cost_basic,
    (metadata->>'cost_optimized')::numeric as cost_optimized,
    (metadata->>'cost_improvement_percent')::numeric as cost_improvement,
    (metadata->>'width_basic')::numeric as width_basic,
    (metadata->>'width_optimized')::numeric as width_optimized,
    (metadata->>'width_improvement_percent')::numeric as width_improvement,
    (metadata->>'rows_basic')::numeric as rows_basic,
    (metadata->>'rows_optimized')::numeric as rows_optimized,
    (metadata->>'rows_improvement_percent')::numeric as rows_improvement,
    CASE 
        WHEN metadata->>'optimization_validated' = 'true' THEN '✅ Валидировано'
        WHEN metadata->>'optimization_validated' = 'false' THEN '⚠️ Не прошло'
        ELSE '❓ Не проверено'
    END as status
FROM vanna_vectors
WHERE content_type = 'question_sql'
  AND metadata->>'is_optimized' = 'true'
ORDER BY id DESC
LIMIT 10;
```

## ⚠️ Важные замечания

1. **Валидация не блокирует добавление:**
   - SQL добавляется даже если не прошел валидацию
   - Но помечается `optimization_validated: false`
   - Предупреждение логируется и сохраняется в metadata

2. **Метрики не всегда точные:**
   - PostgreSQL cost - это оценка, не реальное время выполнения
   - Width показывает размер данных, но не учитывает сжатие
   - Rows - это оценка количества строк
   - Но для сравнения относительной производительности это полезно

3. **Валидация по нескольким критериям:**
   - Валидация проходит если **хотя бы одна метрика лучше**
   - Это позволяет учитывать случаи, когда:
     - Cost немного увеличился (из-за ORDER BY), но width значительно уменьшился
     - Width уменьшился (SELECT конкретных колонок вместо SELECT *)
     - Rows уменьшились (более эффективный фильтр)
   - **Пример:** Width улучшение на 96.8% компенсирует увеличение cost на 0.01%

4. **Рекомендация:**
   - Всегда проверяйте результаты валидации
   - Если `optimization_validated: false` - пересмотрите оптимизацию
   - Смотрите на все метрики: `cost_improvement_percent`, `width_improvement_percent`, `rows_improvement_percent`
   - Width улучшение часто более важно чем cost для запросов с большим объемом данных

## 📚 Связанные документы

- [EXPLAIN_PLAN_INTEGRATION.md](EXPLAIN_PLAN_INTEGRATION.md) - Интеграция EXPLAIN планов
- [OPTIMIZED_SQL_MARKING.md](OPTIMIZED_SQL_MARKING.md) - Маркировка оптимизированных SQL
- [SQL_OPTIMIZATION_TRAINING_GUIDE.md](SQL_OPTIMIZATION_TRAINING_GUIDE.md) - Обучение на оптимизированных SQL

