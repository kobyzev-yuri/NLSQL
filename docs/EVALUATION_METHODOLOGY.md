# 📊 Методика оценки качества SQL: Precision, Recall, F1-Score

## 🎯 Обзор

Данный документ описывает методику расчета метрик **Precision (P)**, **Recall (R)** и **F1-Score** для оценки качества генерируемых SQL запросов в системе NL→SQL.

## 📈 Определение метрик

### **Precision (Точность)**
**Определение**: Доля релевантных результатов среди всех возвращенных результатов.

**Формула**: `P = TP / (TP + FP)`

**Для SQL**: Доля корректных SQL запросов среди всех сгенерированных запросов.

### **Recall (Полнота)**
**Определение**: Доля найденных релевантных результатов от общего количества релевантных результатов.

**Формула**: `R = TP / (TP + FN)`

**Для SQL**: Доля корректных SQL запросов, которые система смогла сгенерировать, от общего количества возможных корректных запросов.

### **F1-Score (Гармоническое среднее)**
**Определение**: Гармоническое среднее между Precision и Recall.

**Формула**: `F1 = 2 * (P * R) / (P + R)`

**Для SQL**: Балансированная оценка качества генерации SQL.

## 🏗️ Архитектура оценки

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Входной       │    │   Генерация     │    │   Оценка        │
│   вопрос        │───▶│   SQL           │───▶│   качества      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Сравнение с    │
                    │   эталонными     │
                    │   SQL запросами  │
                    └─────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Расчет P,R,F1 │
                    │   метрик        │
                    └─────────────────┘
```

## 🔍 Методика расчета

### 1. **Подготовка данных**

#### Эталонные SQL запросы (Ground Truth)
```json
{
  "question": "Покажи всех пользователей",
  "reference_sql": "SELECT id, login, email, department FROM equsers WHERE deleted = FALSE",
  "expected_tables": ["equsers"],
  "expected_columns": ["id", "login", "email", "department"],
  "expected_conditions": ["deleted = FALSE"]
}
```

#### Сгенерированные SQL запросы
```json
{
  "question": "Покажи всех пользователей", 
  "generated_sql": "SELECT * FROM equsers",
  "generated_tables": ["equsers"],
  "generated_columns": ["*"],
  "generated_conditions": []
}
```

### 2. **Анализ компонентов SQL**

#### **Таблицы (Tables)**
- **TP (True Positive)**: Правильно использованные таблицы
- **FP (False Positive)**: Неправильно использованные таблицы
- **FN (False Negative)**: Пропущенные таблицы

#### **Колонки (Columns)**
- **TP**: Правильно выбранные колонки
- **FP**: Неправильно выбранные колонки  
- **FN**: Пропущенные колонки

#### **Условия (Conditions)**
- **TP**: Правильно добавленные условия
- **FP**: Неправильно добавленные условия
- **FN**: Пропущенные условия

#### **JOIN операции**
- **TP**: Правильно выполненные JOIN
- **FP**: Неправильные JOIN
- **FN**: Пропущенные JOIN

### 3. **Алгоритм расчета**

```python
def calculate_sql_metrics(reference_sql, generated_sql):
    """
    Расчет P, R, F1 для SQL запроса
    """
    
    # 1. Парсинг SQL запросов
    ref_components = parse_sql_components(reference_sql)
    gen_components = parse_sql_components(generated_sql)
    
    # 2. Расчет метрик для каждого компонента
    tables_metrics = calculate_component_metrics(
        ref_components['tables'], 
        gen_components['tables']
    )
    
    columns_metrics = calculate_component_metrics(
        ref_components['columns'], 
        gen_components['columns']
    )
    
    conditions_metrics = calculate_component_metrics(
        ref_components['conditions'], 
        gen_components['conditions']
    )
    
    joins_metrics = calculate_component_metrics(
        ref_components['joins'], 
        gen_components['joins']
    )
    
    # 3. Взвешенное среднее
    weights = {
        'tables': 0.3,      # 30% - важность таблиц
        'columns': 0.25,    # 25% - важность колонок
        'conditions': 0.25, # 25% - важность условий
        'joins': 0.2        # 20% - важность JOIN
    }
    
    # 4. Итоговые метрики
    precision = (
        tables_metrics['precision'] * weights['tables'] +
        columns_metrics['precision'] * weights['columns'] +
        conditions_metrics['precision'] * weights['conditions'] +
        joins_metrics['precision'] * weights['joins']
    )
    
    recall = (
        tables_metrics['recall'] * weights['tables'] +
        columns_metrics['recall'] * weights['columns'] +
        conditions_metrics['recall'] * weights['conditions'] +
        joins_metrics['recall'] * weights['joins']
    )
    
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    return {
        'precision': precision,
        'recall': recall,
        'f1_score': f1_score,
        'component_metrics': {
            'tables': tables_metrics,
            'columns': columns_metrics,
            'conditions': conditions_metrics,
            'joins': joins_metrics
        }
    }
```

### 4. **Детальный расчет компонентов**

```python
def calculate_component_metrics(reference_set, generated_set):
    """
    Расчет метрик для компонента SQL
    """
    
    # True Positives: пересечение множеств
    tp = len(reference_set.intersection(generated_set))
    
    # False Positives: элементы в generated, но не в reference
    fp = len(generated_set - reference_set)
    
    # False Negatives: элементы в reference, но не в generated
    fn = len(reference_set - generated_set)
    
    # Расчет метрик
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    return {
        'precision': precision,
        'recall': recall,
        'f1_score': f1_score,
        'tp': tp,
        'fp': fp,
        'fn': fn
    }
```

## 📊 Примеры расчета

### Пример 1: Простой запрос

**Вопрос**: "Покажи всех пользователей"

**Эталонный SQL**: 
```sql
SELECT id, login, email, department FROM equsers WHERE deleted = FALSE
```

**Сгенерированный SQL**: 
```sql
SELECT * FROM equsers
```

**Анализ компонентов**:

| Компонент | Эталон | Сгенерированный | TP | FP | FN |
|-----------|--------|-----------------|----|----|----| 
| Таблицы | {equsers} | {equsers} | 1 | 0 | 0 |
| Колонки | {id, login, email, department} | {*} | 0 | 1 | 4 |
| Условия | {deleted = FALSE} | {} | 0 | 0 | 1 |

**Расчет метрик**:
- **Tables**: P=1.0, R=1.0, F1=1.0
- **Columns**: P=0.0, R=0.0, F1=0.0  
- **Conditions**: P=0.0, R=0.0, F1=0.0

**Итоговые метрики**:
- **Precision**: 1.0×0.3 + 0.0×0.25 + 0.0×0.25 + 0.0×0.2 = **0.3**
- **Recall**: 1.0×0.3 + 0.0×0.25 + 0.0×0.25 + 0.0×0.2 = **0.3**
- **F1-Score**: 2×(0.3×0.3)/(0.3+0.3) = **0.3**

### Пример 2: Сложный запрос

**Вопрос**: "Платежи по отделам"

**Эталонный SQL**:
```sql
SELECT d.name, SUM(p.amount) as total_amount 
FROM tbl_incoming_payments p 
INNER JOIN equsers u ON p.user_id = u.id 
INNER JOIN eq_departments d ON u.department = d.id 
WHERE p.payment_date >= CURRENT_DATE - INTERVAL '1 year' 
GROUP BY d.name 
ORDER BY total_amount DESC
```

**Сгенерированный SQL**:
```sql
SELECT d.name, SUM(p.amount) 
FROM tbl_incoming_payments p 
JOIN equsers u ON p.user_id = u.id 
JOIN eq_departments d ON u.department = d.id 
GROUP BY d.name
```

**Анализ компонентов**:

| Компонент | Эталон | Сгенерированный | TP | FP | FN |
|-----------|--------|-----------------|----|----|----|
| Таблицы | {tbl_incoming_payments, equsers, eq_departments} | {tbl_incoming_payments, equsers, eq_departments} | 3 | 0 | 0 |
| Колонки | {d.name, SUM(p.amount)} | {d.name, SUM(p.amount)} | 2 | 0 | 0 |
| Условия | {payment_date >= CURRENT_DATE - INTERVAL '1 year'} | {} | 0 | 0 | 1 |
| JOIN | {INNER JOIN equsers, INNER JOIN eq_departments} | {JOIN equsers, JOIN eq_departments} | 2 | 0 | 0 |

**Расчет метрик**:
- **Tables**: P=1.0, R=1.0, F1=1.0
- **Columns**: P=1.0, R=1.0, F1=1.0
- **Conditions**: P=0.0, R=0.0, F1=0.0
- **JOIN**: P=1.0, R=1.0, F1=1.0

**Итоговые метрики**:
- **Precision**: 1.0×0.3 + 1.0×0.25 + 0.0×0.25 + 1.0×0.2 = **0.75**
- **Recall**: 1.0×0.3 + 1.0×0.25 + 0.0×0.25 + 1.0×0.2 = **0.75**
- **F1-Score**: 2×(0.75×0.75)/(0.75+0.75) = **0.75**

## 🎯 Интерпретация результатов

### **Отличные результаты (F1 > 0.9)**
- SQL запросы практически идентичны эталонным
- Все компоненты правильно сгенерированы
- Минимальные различия в синтаксисе

### **Хорошие результаты (0.7 < F1 ≤ 0.9)**
- Основные компоненты правильно сгенерированы
- Небольшие различия в деталях
- Возможны незначительные оптимизации

### **Удовлетворительные результаты (0.5 < F1 ≤ 0.7)**
- Базовая структура правильная
- Некоторые компоненты пропущены или неправильны
- Требуется доработка

### **Плохие результаты (F1 ≤ 0.5)**
- Значительные ошибки в структуре
- Много пропущенных или неправильных компонентов
- Требуется серьезная доработка

## 🔧 Реализация в коде

### Класс SQLMetricsCalculator

```python
class SQLMetricsCalculator:
    """Калькулятор метрик качества SQL"""
    
    def __init__(self, weights=None):
        self.weights = weights or {
            'tables': 0.3,
            'columns': 0.25, 
            'conditions': 0.25,
            'joins': 0.2
        }
    
    def calculate_metrics(self, reference_sql, generated_sql):
        """Основной метод расчета метрик"""
        # Парсинг SQL компонентов
        ref_components = self._parse_sql_components(reference_sql)
        gen_components = self._parse_sql_components(generated_sql)
        
        # Расчет метрик для каждого компонента
        component_metrics = {}
        for component in ['tables', 'columns', 'conditions', 'joins']:
            component_metrics[component] = self._calculate_component_metrics(
                ref_components[component],
                gen_components[component]
            )
        
        # Взвешенное среднее
        precision = sum(
            component_metrics[comp]['precision'] * self.weights[comp]
            for comp in self.weights
        )
        
        recall = sum(
            component_metrics[comp]['recall'] * self.weights[comp]
            for comp in self.weights
        )
        
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        return {
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score,
            'component_metrics': component_metrics
        }
    
    def _parse_sql_components(self, sql):
        """Парсинг SQL запроса на компоненты"""
        # Реализация парсинга SQL
        pass
    
    def _calculate_component_metrics(self, reference_set, generated_set):
        """Расчет метрик для компонента"""
        tp = len(reference_set.intersection(generated_set))
        fp = len(generated_set - reference_set)
        fn = len(reference_set - generated_set)
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        return {
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score,
            'tp': tp,
            'fp': fp,
            'fn': fn
        }
```

## 📈 Мониторинг и улучшение

### Ключевые метрики для отслеживания:
- **Средний F1-Score** по всем запросам
- **Precision по типам запросов** (простые, сложные, с JOIN)
- **Recall по компонентам** (таблицы, колонки, условия)
- **Тренд улучшения** метрик во времени

### Рекомендации по улучшению:
1. **Анализ ошибок** - какие компоненты чаще всего неправильны
2. **Дополнительное обучение** на проблемных случаях
3. **Настройка весов** компонентов под специфику задач
4. **A/B тестирование** разных подходов к генерации

## 🎯 Заключение

Методика оценки P, R, F1-Score для SQL запросов позволяет:

- **Количественно оценить** качество генерации SQL
- **Выявить проблемные области** в генерации
- **Отслеживать прогресс** улучшения модели
- **Сравнивать** разные подходы и модели

**Результат**: Объективная и воспроизводимая оценка качества генерируемых SQL запросов! 📊
