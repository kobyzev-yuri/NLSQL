# 📊 Метрики качества: что считаем сейчас и что позже

## 🎯 Правильная интерпретация метрик

На данном этапе мы не используем P/R/F1 из-за отсутствия корректного определения FP/FN в задачах генерации SQL (разные SQL могут быть эквивалентны по результату). Вместо этого фокусируемся на метриках, опирающихся на эквивалентность результата.

## 📊 Примеры правильных значений

### **Пример 1: Отличное качество**
```python
precision = 0.95  # 95% точности
recall = 0.90     # 90% полноты
f1_score = 0.92   # 92% качества
```

### **Пример 2: Хорошее качество**
```python
precision = 0.85  # 85% точности
recall = 0.80    # 80% полноты
f1_score = 0.82  # 82% качества
```

### **Пример 3: Удовлетворительное качество**
```python
precision = 0.70  # 70% точности
recall = 0.65    # 65% полноты
f1_score = 0.67  # 67% качества
```

### **Пример 4: Плохое качество**
```python
precision = 0.30  # 30% точности
recall = 0.25    # 25% полноты
f1_score = 0.27  # 27% качества
```

## ✅ Что считаем сейчас

### Accuracy (эквивалентность результата)
SQL считается корректным, если:
1) валиден синтаксически;
2) возвращает тот же датасет, что и эталонный SQL для того же вопроса (execution equivalence);
3) опционально — план выполнения эквивалентен (plan equivalence) для исключения «читов».

Расчёт:
```
Accuracy = Correct_SQL / Total_SQL
```

Где Correct_SQL — количество запросов, прошедших проверки 1–2 (и 3 — если включена).

### Component Match (диагностика, не KPI)
Сравнение компонентов (таблицы, колонки, условия, JOIN) для объяснимости ошибок. Это вспомогательная метрика.

### **Неправильная реализация (НЕ ДЕЛАЙТЕ ТАК)**
```python
# ❌ НЕПРАВИЛЬНО: значения могут быть больше 1
precision = tp / (tp + fp)  # Может быть > 1 если fp < 0
recall = tp / (tp + fn)    # Может быть > 1 если fn < 0
f1_score = 2 * (precision * recall) / (precision + recall)  # Может быть > 1
```

## 🎯 Практические примеры для SQL

### **Пример 1: Простой запрос**
```sql
-- Эталонный SQL
SELECT id, login FROM equsers WHERE deleted = FALSE

-- Сгенерированный SQL  
SELECT id, login FROM equsers WHERE deleted = FALSE
```

**Анализ компонентов:**
- **Таблицы**: TP=1, FP=0, FN=0 → P=1.0, R=1.0, F1=1.0
- **Колонки**: TP=2, FP=0, FN=0 → P=1.0, R=1.0, F1=1.0
- **Условия**: TP=1, FP=0, FN=0 → P=1.0, R=1.0, F1=1.0

**Итоговые метрики:**
- **Precision**: 1.0 (100% точности)
- **Recall**: 1.0 (100% полноты)
- **F1-Score**: 1.0 (100% качества)

### **Пример 2: Запрос с ошибками**
```sql
-- Эталонный SQL
SELECT u.id, u.login, d.name 
FROM equsers u 
JOIN eq_departments d ON u.department = d.id 
WHERE u.deleted = FALSE

-- Сгенерированный SQL
SELECT u.id, u.login 
FROM equsers u 
WHERE u.deleted = FALSE
```

**Анализ компонентов:**
- **Таблицы**: TP=1, FP=0, FN=1 → P=1.0, R=0.5, F1=0.67
- **Колонки**: TP=2, FP=0, FN=1 → P=1.0, R=0.67, F1=0.8
- **Условия**: TP=1, FP=0, FN=0 → P=1.0, R=1.0, F1=1.0
- **JOIN**: TP=0, FP=0, FN=1 → P=0.0, R=0.0, F1=0.0

**Итоговые метрики (взвешенное среднее):**
- **Precision**: 1.0×0.25 + 1.0×0.20 + 1.0×0.20 + 0.0×0.15 = **0.65**
- **Recall**: 0.5×0.25 + 0.67×0.20 + 1.0×0.20 + 0.0×0.15 = **0.58**
- **F1-Score**: 2×(0.65×0.58)/(0.65+0.58) = **0.61**

## 📈 Мониторинг метрик

### **Ключевые принципы:**
1. **Все метрики в диапазоне 0.0 - 1.0**
2. **Процентное представление**: метрика × 100%
3. **Сравнение с эталоном**: эталонные SQL запросы
4. **Компонентный анализ**: таблицы, колонки, условия, JOIN

### **Рекомендации по улучшению:**
- **Precision < 0.7**: Улучшить точность генерации
- **Recall < 0.7**: Улучшить полноту генерации
- **F1-Score < 0.7**: Общее улучшение качества

## 🔄 Эквивалентность SQL запросов

### **Проблема: разные SQL → одинаковый результат**

**Критически важная тонкость:** Разные SQL-запросы могут возвращать **идентичный датасет**, при этом отличаясь синтаксически.

#### **Пример 1: Порядок условий**
```sql
-- Вариант 1 (эталон)
SELECT * FROM users WHERE deleted = false AND department = 'IT';

-- Вариант 2 (сгенерированный)
SELECT * FROM users WHERE department = 'IT' AND deleted = false;

-- ✅ Результат: ИДЕНТИЧНЫЙ датасет
```

#### **Пример 2: Явное перечисление колонок vs SELECT ***
```sql
-- Вариант 1
SELECT * FROM users WHERE id = 1;

-- Вариант 2
SELECT id, login, email, department FROM users WHERE id = 1;

-- ✅ Результат: ИДЕНТИЧНЫЙ датасет (если в таблице только эти 4 колонки)
```

#### **Пример 3: Разные способы JOIN**
```sql
-- Вариант 1
SELECT u.* FROM users u 
INNER JOIN departments d ON u.dept_id = d.id 
WHERE d.name = 'IT';

-- Вариант 2
SELECT u.* FROM users u 
WHERE u.dept_id IN (SELECT id FROM departments WHERE name = 'IT');

-- ✅ Результат: ИДЕНТИЧНЫЙ датасет
```

### Принцип EXPLAIN/планов

Для корректной оценки качества SQL используется **эквивалентность по плану выполнения**:

#### **1️⃣ Execution Equivalence (Эквивалентность результата)**
```python
# Оба SQL должны вернуть одинаковый датасет
result1 = execute_sql(sql_reference)
result2 = execute_sql(sql_generated)

# Сравнение: одинаковые строки, колонки, значения
is_equivalent = (result1 == result2)
```

#### **2️⃣ Plan Equivalence (Эквивалентность плана)**
```python
# PostgreSQL EXPLAIN показывает план выполнения
plan1 = execute_sql(f"EXPLAIN {sql_reference}")
plan2 = execute_sql(f"EXPLAIN {sql_generated}")

# Сравнение ключевых аспектов плана:
# - Используемые индексы
# - Тип сканирования (Sequential, Index, Bitmap)
# - Порядок JOIN
# - Стоимость запроса (cost)
is_plan_equivalent = compare_explain_plans(plan1, plan2)
```

#### **Пример EXPLAIN PLAN**
```sql
-- SQL 1
EXPLAIN SELECT * FROM users WHERE department = 'IT' AND deleted = false;
---
Seq Scan on users  (cost=0.00..35.50 rows=10 width=120)
  Filter: ((department = 'IT'::text) AND (deleted = false))

-- SQL 2  
EXPLAIN SELECT * FROM users WHERE deleted = false AND department = 'IT';
---
Seq Scan on users  (cost=0.00..35.50 rows=10 width=120)
  Filter: ((deleted = false) AND (department = 'IT'::text))

✅ План ИДЕНТИЧЕН → SQL эквивалентны
```

### Итоги
- Accuracy — основная метрика качества.
- Component Match — только для разбора ошибок.

### **Практическое применение**

#### **В системе NLSQL**
```python
def evaluate_sql_quality(reference_sql, generated_sql):
    """
    Оценка качества сгенерированного SQL
    
    Returns:
        {
            'syntax_valid': bool,           # Синтаксис корректен
            'execution_equiv': bool,        # Результаты идентичны
            'plan_equiv': bool,             # Планы эквивалентны
            'component_match': float,       # 0.0 - 1.0
            'accuracy': bool                # Общая оценка
        }
    """
    # 1. Проверка синтаксиса
    syntax_valid = validate_syntax(generated_sql)
    
    # 2. Сравнение результатов
    ref_result = execute(reference_sql)
    gen_result = execute(generated_sql)
    execution_equiv = (ref_result == gen_result)
    
    # 3. Сравнение планов
    ref_plan = get_explain_plan(reference_sql)
    gen_plan = get_explain_plan(generated_sql)
    plan_equiv = compare_plans(ref_plan, gen_plan)
    
    # 4. Анализ компонентов
    component_match = analyze_components(reference_sql, generated_sql)
    
    # 5. Итоговая оценка
    accuracy = syntax_valid and execution_equiv and plan_equiv
    
    return {
        'syntax_valid': syntax_valid,
        'execution_equiv': execution_equiv,
        'plan_equiv': plan_equiv,
        'component_match': component_match,
        'accuracy': accuracy
    }
```

## 🔬 Что отложено на потом (методология)

### Качество RAG (retrieval)
- Top-1/Top-k hit-rate: попал ли релевантный фрагмент контекста в топ-k
- MRR/NDCG: ранжирование релевантных документов
- Порог релевантности: ручная разметка/эвристики (требуется методология и датасет)

### Сравнение моделей (benchmark)
- Единый набор вопросов + эталонный SQL (или эталонный датасет)
- Accuracy per model, затем тесты значимости
- Взвешивание доменов (users/payments/assignments)

Эти блоки потребуют аккуратной разметки и будут описаны отдельно.

## 🎯 Вывод
- Сейчас считаем понятную метрику: Accuracy по эквивалентности результата (и опционально планов).
- P/R/F1 — не применяем из‑за неопределимости FP/FN для генерации SQL.
- Методологии для RAG/benchmark моделей — зафиксируем отдельно после подготовки датасета и правил разметки.
