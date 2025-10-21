#!/usr/bin/env python3
"""
Калькулятор метрик качества SQL: Precision, Recall, F1-Score
Правильная реализация с диапазоном значений 0.0 - 1.0
"""

import re
import logging
from typing import Dict, List, Set, Any, Tuple
from dataclasses import dataclass
import sys
import os

# Добавляем путь к существующему SQL парсеру
sys.path.append(os.path.join(os.path.dirname(__file__), 'src', 'utils'))
from plan_sql_converter import SQLToPlanConverter

logger = logging.getLogger(__name__)

@dataclass
class SQLComponents:
    """Компоненты SQL запроса"""
    tables: Set[str]
    columns: Set[str] 
    conditions: Set[str]
    joins: Set[str]
    order_by: Set[str]
    group_by: Set[str]

class SQLMetricsCalculator:
    """Калькулятор метрик качества SQL"""
    
    def __init__(self, weights: Dict[str, float] = None):
        """
        Инициализация калькулятора
        
        Args:
            weights: Веса компонентов для расчета итоговых метрик
        """
        self.weights = weights or {
            'tables': 0.25,      # 25% - важность таблиц
            'columns': 0.20,    # 20% - важность колонок
            'conditions': 0.20, # 20% - важность условий
            'joins': 0.15,      # 15% - важность JOIN
            'order_by': 0.10,   # 10% - важность сортировки
            'group_by': 0.10    # 10% - важность группировки
        }
        
        # Проверяем, что веса в сумме дают 1.0
        total_weight = sum(self.weights.values())
        if abs(total_weight - 1.0) > 0.01:
            logger.warning(f"Сумма весов = {total_weight}, должна быть 1.0")
    
    def calculate_metrics(self, reference_sql: str, generated_sql: str) -> Dict[str, Any]:
        """
        Расчет метрик качества SQL
        
        Args:
            reference_sql: Эталонный SQL запрос
            generated_sql: Сгенерированный SQL запрос
            
        Returns:
            Словарь с метриками: precision, recall, f1_score, component_metrics
        """
        try:
            # Парсинг SQL компонентов
            ref_components = self._parse_sql_components(reference_sql)
            gen_components = self._parse_sql_components(generated_sql)
            
            # Расчет метрик для каждого компонента
            component_metrics = {}
            for component_name in self.weights.keys():
                ref_set = getattr(ref_components, component_name)
                gen_set = getattr(gen_components, component_name)
                
                component_metrics[component_name] = self._calculate_component_metrics(
                    ref_set, gen_set
                )
            
            # Взвешенное среднее для итоговых метрик
            precision = sum(
                component_metrics[comp]['precision'] * self.weights[comp]
                for comp in self.weights
            )
            
            recall = sum(
                component_metrics[comp]['recall'] * self.weights[comp]
                for comp in self.weights
            )
            
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
                'f1_score': f1_score,
                'component_metrics': component_metrics,
                'reference_components': ref_components,
                'generated_components': gen_components
            }
            
        except Exception as e:
            logger.error(f"Ошибка расчета метрик: {e}")
            return {
                'precision': 0.0,
                'recall': 0.0,
                'f1_score': 0.0,
                'error': str(e)
            }
    
    def _parse_sql_components(self, sql: str) -> SQLComponents:
        """Парсинг SQL запроса на компоненты используя существующий парсер"""
        if not sql or not sql.strip():
            return SQLComponents(set(), set(), set(), set(), set(), set())
        
        try:
            # Используем существующий SQL парсер
            converter = SQLToPlanConverter()
            plan = converter.convert(sql)
            
            # Извлекаем компоненты из плана
            tables = set(plan.get('tables', []))
            
            # Колонки из полей
            columns = set(plan.get('fields', []))
            
            # Условия из WHERE
            conditions = set()
            for condition in plan.get('conditions', []):
                if isinstance(condition, dict):
                    field = condition.get('field', '')
                    operator = condition.get('operator', '')
                    value = condition.get('value', '')
                    conditions.add(f"{field} {operator} {value}")
                else:
                    conditions.add(str(condition))
            
            # JOIN операции (пока не поддерживаются в существующем парсере)
            joins = set()
            
            # ORDER BY
            order_by = set(plan.get('order_by', []))
            
            # GROUP BY
            group_by = set(plan.get('group_by', []))
            
            return SQLComponents(
                tables=tables,
                columns=columns,
                conditions=conditions,
                joins=joins,
                order_by=order_by,
                group_by=group_by
            )
            
        except Exception as e:
            logger.warning(f"Ошибка парсинга SQL: {e}, используем fallback")
            # Fallback к простому парсингу
            return self._parse_sql_components_fallback(sql)
    
    def _parse_sql_components_fallback(self, sql: str) -> SQLComponents:
        """Fallback парсинг SQL запроса на компоненты"""
        if not sql or not sql.strip():
            return SQLComponents(set(), set(), set(), set(), set(), set())
        
        sql_upper = sql.upper().strip()
        
        # Извлечение таблиц
        tables = self._extract_tables(sql_upper)
        
        # Извлечение колонок
        columns = self._extract_columns(sql_upper)
        
        # Извлечение условий
        conditions = self._extract_conditions(sql_upper)
        
        # Извлечение JOIN
        joins = self._extract_joins(sql_upper)
        
        # Извлечение ORDER BY
        order_by = self._extract_order_by(sql_upper)
        
        # Извлечение GROUP BY
        group_by = self._extract_group_by(sql_upper)
        
        return SQLComponents(
            tables=tables,
            columns=columns,
            conditions=conditions,
            joins=joins,
            order_by=order_by,
            group_by=group_by
        )
    
    def _extract_tables(self, sql: str) -> Set[str]:
        """Извлечение таблиц из SQL"""
        tables = set()
        
        # FROM clause
        from_match = re.search(r'FROM\s+(\w+)', sql)
        if from_match:
            tables.add(from_match.group(1))
        
        # JOIN clauses
        join_matches = re.findall(r'JOIN\s+(\w+)', sql)
        tables.update(join_matches)
        
        return tables
    
    def _extract_columns(self, sql: str) -> Set[str]:
        """Извлечение колонок из SQL"""
        columns = set()
        
        # SELECT clause
        select_match = re.search(r'SELECT\s+(.*?)\s+FROM', sql, re.DOTALL)
        if select_match:
            select_clause = select_match.group(1)
            # Разбиваем по запятым и очищаем
            for col in select_clause.split(','):
                col = col.strip()
                if col and col != '*':
                    # Убираем алиасы (AS ...)
                    col = re.sub(r'\s+AS\s+\w+', '', col)
                    columns.add(col)
        
        return columns
    
    def _extract_conditions(self, sql: str) -> Set[str]:
        """Извлечение условий WHERE из SQL"""
        conditions = set()
        
        # WHERE clause
        where_match = re.search(r'WHERE\s+(.*?)(?:\s+GROUP\s+BY|\s+ORDER\s+BY|\s+HAVING|$)', sql, re.DOTALL)
        if where_match:
            where_clause = where_match.group(1).strip()
            # Разбиваем по AND/OR
            for condition in re.split(r'\s+(?:AND|OR)\s+', where_clause):
                condition = condition.strip()
                if condition:
                    conditions.add(condition)
        
        return conditions
    
    def _extract_joins(self, sql: str) -> Set[str]:
        """Извлечение JOIN операций из SQL"""
        joins = set()
        
        # Более простой и надежный подход
        # Ищем все JOIN с ON условиями
        join_pattern = r'(INNER\s+JOIN|LEFT\s+JOIN|RIGHT\s+JOIN|FULL\s+JOIN|JOIN)\s+\w+\s+ON\s+[^;]+'
        
        matches = re.findall(join_pattern, sql, re.IGNORECASE)
        for match in matches:
            # Очищаем и нормализуем JOIN
            join_clean = re.sub(r'\s+', ' ', match.strip())
            joins.add(join_clean)
        
        # Дополнительно ищем простые JOIN без INNER/LEFT
        simple_join_pattern = r'JOIN\s+\w+\s+ON\s+[^;]+'
        simple_matches = re.findall(simple_join_pattern, sql, re.IGNORECASE)
        for match in simple_matches:
            join_clean = re.sub(r'\s+', ' ', match.strip())
            joins.add(join_clean)
        
        return joins
    
    def _extract_order_by(self, sql: str) -> Set[str]:
        """Извлечение ORDER BY из SQL"""
        order_by = set()
        
        # Более точный поиск ORDER BY
        order_match = re.search(r'ORDER\s+BY\s+([^;]+?)(?:\s+GROUP\s+BY|\s+HAVING|$)', sql, re.IGNORECASE | re.DOTALL)
        if order_match:
            order_clause = order_match.group(1).strip()
            # Разбиваем по запятым и очищаем
            for col in order_clause.split(','):
                col = col.strip()
                if col:
                    # Убираем ASC/DESC и лишние пробелы
                    col = re.sub(r'\s+(ASC|DESC)\s*$', '', col, flags=re.IGNORECASE)
                    col = re.sub(r'\s+', ' ', col.strip())
                    if col:
                        order_by.add(col)
        
        return order_by
    
    def _extract_group_by(self, sql: str) -> Set[str]:
        """Извлечение GROUP BY из SQL"""
        group_by = set()
        
        # Более точный поиск GROUP BY
        group_match = re.search(r'GROUP\s+BY\s+([^;]+?)(?:\s+ORDER\s+BY|\s+HAVING|$)', sql, re.IGNORECASE | re.DOTALL)
        if group_match:
            group_clause = group_match.group(1).strip()
            # Разбиваем по запятым и очищаем
            for col in group_clause.split(','):
                col = col.strip()
                if col:
                    # Убираем лишние пробелы
                    col = re.sub(r'\s+', ' ', col.strip())
                    if col:
                        group_by.add(col)
        
        return group_by
    
    def _calculate_component_metrics(self, reference_set: Set[str], generated_set: Set[str]) -> Dict[str, float]:
        """Расчет метрик для компонента SQL"""
        
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
            'f1_score': f1_score,
            'tp': tp,
            'fp': fp,
            'fn': fn,
            'reference_count': len(reference_set),
            'generated_count': len(generated_set)
        }
    
    def interpret_metrics(self, metrics: Dict[str, Any]) -> str:
        """Интерпретация метрик качества"""
        f1 = metrics.get('f1_score', 0.0)
        precision = metrics.get('precision', 0.0)
        recall = metrics.get('recall', 0.0)
        
        if f1 >= 0.9:
            quality = "Отличное качество"
        elif f1 >= 0.7:
            quality = "Хорошее качество"
        elif f1 >= 0.5:
            quality = "Удовлетворительное качество"
        else:
            quality = "Плохое качество"
        
        return f"""
        📊 Результаты оценки качества SQL:
        
        **Общие метрики:**
        - Precision: {precision:.2f} ({precision*100:.1f}%)
        - Recall: {recall:.2f} ({recall*100:.1f}%)
        - F1-Score: {f1:.2f} ({f1*100:.1f}%)
        
        **Оценка качества: {quality}**
        
        **Интерпретация:**
        - Precision показывает долю корректных SQL среди всех сгенерированных
        - Recall показывает долю найденных корректных SQL от общего количества возможных
        - F1-Score - балансированная оценка качества
        """

def main():
    """Пример использования калькулятора метрик"""
    
    # Примеры SQL запросов с реальными JOIN, ORDER BY, GROUP BY
    reference_sql = """
    SELECT u.id, u.login, d.name as department_name, COUNT(p.id) as payment_count
    FROM equsers u 
    INNER JOIN eq_departments d ON u.department = d.id 
    LEFT JOIN tbl_incoming_payments p ON u.id = p.user_id
    WHERE u.deleted = FALSE 
    GROUP BY u.id, u.login, d.name
    ORDER BY u.login ASC, payment_count DESC
    """
    
    generated_sql = """
    SELECT u.id, u.login, d.name, COUNT(p.id) as payment_count
    FROM equsers u 
    JOIN eq_departments d ON u.department = d.id 
    LEFT JOIN tbl_incoming_payments p ON u.id = p.user_id
    WHERE u.deleted = FALSE 
    GROUP BY u.id, u.login, d.name
    ORDER BY u.login, payment_count
    """
    
    # Создание калькулятора
    calculator = SQLMetricsCalculator()
    
    # Расчет метрик
    metrics = calculator.calculate_metrics(reference_sql, generated_sql)
    
    # Вывод результатов
    print("🔍 Анализ качества SQL:")
    print(f"Precision: {metrics['precision']:.3f}")
    print(f"Recall: {metrics['recall']:.3f}")
    print(f"F1-Score: {metrics['f1_score']:.3f}")
    
    # Интерпретация
    print(calculator.interpret_metrics(metrics))
    
    # Детальный анализ компонентов
    print("\n📋 Детальный анализ компонентов:")
    for component, comp_metrics in metrics['component_metrics'].items():
        print(f"{component}: P={comp_metrics['precision']:.3f}, R={comp_metrics['recall']:.3f}, F1={comp_metrics['f1_score']:.3f}")

if __name__ == '__main__':
    main()
