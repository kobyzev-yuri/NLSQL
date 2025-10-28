# 📊 Объяснение метрик качества SQL: P, R, F1

## ❓ Почему метрики не могут быть больше 1?

### **Математические ограничения**

Метрики **Precision**, **Recall** и **F1-Score** имеют строгие математические ограничения:

- **Диапазон значений**: `0.0 ≤ метрика ≤ 1.0`
- **Единица измерения**: Доля или процент (0% - 100%)

### **Формулы метрик**

```python
# Precision (Точность)
P = TP / (TP + FP)
# TP = True Positives (правильные результаты)
# FP = False Positives (неправильные результаты)

# Recall (Полнота)  
R = TP / (TP + FN)
# FN = False Negatives (пропущенные результаты)

# F1-Score (Гармоническое среднее)
F1 = 2 × (P × R) / (P + R)
```

### **Почему значения ограничены 0-1?**

1. **TP, FP, FN** - это количества (неотрицательные числа)
2. **TP ≤ (TP + FP)** - всегда, так как TP входит в сумму
3. **TP ≤ (TP + FN)** - всегда, так как TP входит в сумму
4. **P = TP / (TP + FP) ≤ 1** - дробь не может быть больше 1
5. **R = TP / (TP + FN) ≤ 1** - дробь не может быть больше 1
6. **F1 ≤ min(P, R) ≤ 1** - гармоническое среднее не превышает минимум

## 🎯 Правильная интерпретация метрик

### **Precision (Точность)**
- **0.0**: Все результаты неправильные (0% точности)
- **0.5**: Половина результатов правильные (50% точности)
- **1.0**: Все результаты правильные (100% точности)

### **Recall (Полнота)**
- **0.0**: Ничего не найдено (0% полноты)
- **0.5**: Найдена половина возможных результатов (50% полноты)
- **1.0**: Найдены все возможные результаты (100% полноты)

### **F1-Score (Баланс)**
- **0.0**: Плохое качество (0% качества)
- **0.5**: Удовлетворительное качество (50% качества)
- **0.7**: Хорошее качество (70% качества)
- **0.9**: Отличное качество (90% качества)
- **1.0**: Идеальное качество (100% качества)

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

## 🔧 Реализация в коде

### **Правильная реализация**
```python
def calculate_metrics(reference_set, generated_set):
    """Правильный расчет метрик с ограничением 0-1"""
    
    # True Positives: пересечение множеств
    tp = len(reference_set.intersection(generated_set))
    
    # False Positives: элементы в generated, но не в reference
    fp = len(generated_set - reference_set)
    
    # False Negatives: элементы в reference, но не в generated
    fn = len(reference_set - generated_set)
    
    # Расчет метрик с проверкой деления на ноль
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    
    # F1-Score с проверкой деления на ноль
    if (precision + recall) > 0:
        f1_score = 2 * (precision * recall) / (precision + recall)
    else:
        f1_score = 0.0
    
    # Ограничиваем значения диапазоном [0.0, 1.0]
    precision = max(0.0, min(1.0, precision))
    recall = max(0.0, min(1.0, recall))
    f1_score = max(0.0, min(1.0, f1_score))
    
    return {
        'precision': precision,
        'recall': recall,
        'f1_score': f1_score
    }
```

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

### **Решение: EXPLAIN PLAN для эквивалентности**

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

### **Метрики с учетом эквивалентности**

#### **Accuracy (Точность генерации)**
```python
# SQL считается правильным, если:
# 1. Синтаксически корректен
# 2. Возвращает правильный датасет (Execution Equivalence)
# 3. Имеет эквивалентный план выполнения (Plan Equivalence)

Accuracy = Correct_SQL / Total_SQL

# Correct_SQL - запросы, прошедшие все 3 проверки
```

#### **Component Match (Совпадение компонентов)**
```python
# Для детального анализа:
# - Tables: правильные таблицы
# - Columns: правильные колонки
# - Conditions: правильные условия WHERE
# - Joins: правильные JOIN

Component_Match = (Tables_Match + Columns_Match + 
                   Conditions_Match + Joins_Match) / 4
```

#### **Execution Equivalence (Эквивалентность выполнения)**
```python
# Основная метрика для бизнес-логики:
# SQL возвращает правильные данные?

Exec_Equiv = SQL_Same_Result / Total_SQL
```

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

### **Текущие метрики в системе**

Система NLSQL использует:

1. **Accuracy (Точность генерации)**
   - SQL синтаксически корректен ✓
   - SQL возвращает правильные данные ✓
   - SQL имеет эквивалентный план ✓

2. **Component Match (Совпадение компонентов)**
   - Таблицы, колонки, условия, JOIN
   - Детальный анализ ошибок

3. **Execution Equivalence (Эквивалентность выполнения)**
   - **Основная метрика для бизнеса**
   - Проверка через EXPLAIN PLAN
   - Сравнение результатов выполнения

## 🎯 Заключение

**Метрики для SQL запросов с учетом эквивалентности:**
- ✅ **Accuracy**: Синтаксис + Результат + План (0.0 - 1.0)
- ✅ **Component Match**: Детальный анализ компонентов (0.0 - 1.0)
- ✅ **Execution Equivalence**: Основная метрика для бизнеса
- ✅ **EXPLAIN PLAN**: Проверка эквивалентности планов выполнения

**Ключевая тонкость:** Разные SQL могут быть эквивалентны по результату и плану выполнения, даже если синтаксически отличаются. Это учитывается при оценке качества через EXPLAIN PLAN.

**Результат**: Правильная и точная оценка качества генерируемых SQL запросов с учетом их функциональной эквивалентности! 📊
