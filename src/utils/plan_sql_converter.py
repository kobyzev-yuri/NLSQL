"""
Утилиты для конвертации между планами запросов и SQL
"""

import json
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class PlanField:
    """Поле в плане запроса"""
    name: str
    alias: Optional[str] = None
    function: Optional[str] = None  # COUNT, SUM, AVG, etc.
    
    def to_sql(self) -> str:
        """Преобразует поле в SQL"""
        if self.function:
            if self.alias:
                return f"{self.function}({self.name}) AS {self.alias}"
            else:
                return f"{self.function}({self.name})"
        elif self.alias and self.alias != self.name:
            return f"{self.name} AS {self.alias}"
        else:
            return self.name


@dataclass
class PlanCondition:
    """Условие в плане запроса"""
    field: str
    operator: str
    value: Any
    
    def to_sql(self) -> str:
        """Преобразует условие в SQL"""
        if isinstance(self.value, str) and self.operator in ['LIKE', 'ILIKE']:
            return f"{self.field} {self.operator} '{self.value}'"
        elif isinstance(self.value, str):
            return f"{self.field} {self.operator} '{self.value}'"
        else:
            return f"{self.field} {self.operator} {self.value}"


@dataclass
class PlanJoin:
    """Связь в плане запроса"""
    table: str
    on: str
    type: str = "JOIN"
    
    def to_sql(self) -> str:
        """Преобразует связь в SQL"""
        return f"{self.type} {self.table} ON {self.on}"


class PlanToSQLConverter:
    """Конвертер из плана в SQL"""
    
    def __init__(self):
        self.table_aliases = {}
    
    def convert(self, plan: Dict[str, Any]) -> str:
        """Конвертирует план в SQL запрос"""
        try:
            # Основные компоненты
            tables = plan.get('tables', [])
            fields = plan.get('fields', ['*'])
            conditions = plan.get('conditions', [])
            joins = plan.get('joins', [])
            group_by = plan.get('group_by', [])
            order_by = plan.get('order_by', [])
            limit = plan.get('limit')
            
            # Генерируем SQL
            sql_parts = []
            
            # SELECT clause
            select_clause = self._build_select_clause(fields)
            sql_parts.append(f"SELECT {select_clause}")
            
            # FROM clause
            from_clause = self._build_from_clause(tables)
            sql_parts.append(f"FROM {from_clause}")
            
            # JOIN clauses
            for join in joins:
                join_clause = self._build_join_clause(join)
                sql_parts.append(join_clause)
            
            # WHERE clause
            if conditions:
                where_clause = self._build_where_clause(conditions)
                sql_parts.append(f"WHERE {where_clause}")
            
            # GROUP BY clause
            if group_by:
                group_clean = [g.rstrip(';').strip() for g in group_by]
                group_clause = ", ".join(group_clean)
                sql_parts.append(f"GROUP BY {group_clause}")
            
            # ORDER BY clause
            if order_by:
                order_clean = [o.rstrip(';').strip() for o in order_by]
                order_clause = ", ".join(order_clean)
                sql_parts.append(f"ORDER BY {order_clause}")
            
            # LIMIT clause
            if limit:
                sql_parts.append(f"LIMIT {limit}")
            
            return " ".join(sql_parts)
            
        except Exception as e:
            raise ValueError(f"Ошибка конвертации плана в SQL: {e}")
    
    def _build_select_clause(self, fields: List[str]) -> str:
        """Строит SELECT clause"""
        if not fields or fields == ['*']:
            return "*"
        return ", ".join(fields)
    
    def _build_from_clause(self, tables: List[str]) -> str:
        """Строит FROM clause"""
        if not tables:
            raise ValueError("Не указаны таблицы")
        
        # Создаем алиасы для таблиц
        main_table = tables[0]
        self.table_aliases = {main_table: self._get_table_alias(main_table)}
        
        return main_table
    
    def _build_join_clause(self, join: Dict[str, str]) -> str:
        """Строит JOIN clause"""
        table = join['table']
        on_condition = join['on']
        join_type = join.get('type', 'JOIN')
        
        # Добавляем алиас для таблицы
        alias = self._get_table_alias(table)
        self.table_aliases[table] = alias
        
        return f"{join_type} {table} {alias} ON {on_condition}"
    
    def _build_where_clause(self, conditions: List[Dict[str, Any]]) -> str:
        """Строит WHERE clause"""
        if not conditions:
            return ""
        
        where_parts = []
        for condition in conditions:
            field = condition['field']
            operator = condition['operator']
            value = condition['value']
            
            # Обрабатываем специальные случаи
            if isinstance(value, str) and operator in ['LIKE', 'ILIKE']:
                where_parts.append(f"{field} {operator} '{value}'")
            elif isinstance(value, str):
                # if value looks like a SQL function/expression (e.g., DATE_TRUNC('year', CURRENT_DATE))
                is_expression = bool(re.match(r"^[A-Za-z_][A-Za-z0-9_]*\s*\(", value)) or '::' in value
                cleaned = value.strip().rstrip(';')
                if is_expression:
                    where_parts.append(f"{field} {operator} {cleaned}")
                else:
                    where_parts.append(f"{field} {operator} '{cleaned}'")
            else:
                where_parts.append(f"{field} {operator} {value}")
        
        return " AND ".join(where_parts)
    
    def _get_table_alias(self, table: str) -> str:
        """Генерирует алиас для таблицы"""
        # Простая логика создания алиасов
        if table.startswith('tbl_'):
            return table.replace('tbl_', 't')[0:3]
        elif table.startswith('eq'):
            return table[0:2]
        else:
            return table[0:3]


class SQLToPlanConverter:
    """Конвертер из SQL в план"""
    
    def convert(self, sql: str) -> Dict[str, Any]:
        """Конвертирует SQL в план запроса"""
        try:
            # Парсим SQL (упрощенная версия)
            sql_clean = sql.strip().upper()
            
            # Извлекаем компоненты
            select_match = re.search(r'SELECT\s+(.*?)\s+FROM', sql_clean, re.IGNORECASE)
            from_match = re.search(r'FROM\s+([\w\.]+)', sql_clean, re.IGNORECASE)
            where_match = re.search(r'WHERE\s+(.*?)(?:\s+GROUP\s+BY|\s+ORDER\s+BY|\s+LIMIT|$)', sql_clean, re.IGNORECASE)
            group_by_match = re.search(r'GROUP\s+BY\s+(.*?)(?:\s+ORDER\s+BY|\s+LIMIT|$)', sql_clean, re.IGNORECASE)
            order_by_match = re.search(r'ORDER\s+BY\s+(.*?)(?:\s+LIMIT|$)', sql_clean, re.IGNORECASE)
            limit_match = re.search(r'LIMIT\s+(\d+)', sql_clean, re.IGNORECASE)
            
            # Строим план
            plan = {}
            
            # Tables
            if from_match:
                plan['tables'] = [from_match.group(1)]
            
            # Fields
            if select_match:
                fields_str = select_match.group(1)
                plan['fields'] = [field.strip() for field in fields_str.split(',')]
            
            # Conditions
            if where_match:
                conditions_str = where_match.group(1)
                plan['conditions'] = self._parse_conditions(conditions_str)
            
            # Group by
            if group_by_match:
                group_by_str = group_by_match.group(1)
                plan['group_by'] = [field.strip() for field in group_by_str.split(',')]
            
            # Order by
            if order_by_match:
                order_by_str = order_by_match.group(1)
                plan['order_by'] = [field.strip() for field in order_by_str.split(',')]
            
            # Limit
            if limit_match:
                plan['limit'] = int(limit_match.group(1))
            
            return plan
            
        except Exception as e:
            raise ValueError(f"Ошибка конвертации SQL в план: {e}")
    
    def _parse_conditions(self, conditions_str: str) -> List[Dict[str, Any]]:
        """Парсит условия WHERE"""
        conditions = []
        
        # Простая логика разбора условий
        # В реальной реализации нужен более сложный парсер
        parts = re.split(r'\s+AND\s+', conditions_str, flags=re.IGNORECASE)
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
            # поддержка операторов: >=, <=, <>, !=, =, >, < (двухсимвольные первыми)
            m = re.match(r'([\w\.\(\)]+)\s*(<>|!=|>=|<=|=|>|<)\s*(.+)', part)
            if m:
                field, op, value = m.group(1), m.group(2), m.group(3)
                conditions.append({
                    'field': field.strip(),
                    'operator': op,
                    'value': value.strip().strip("'\"")
                })
        
        return conditions


def plan_to_sql(plan: Dict[str, Any]) -> str:
    """Конвертирует план в SQL"""
    converter = PlanToSQLConverter()
    return converter.convert(plan)


def sql_to_plan(sql: str) -> Dict[str, Any]:
    """Конвертирует SQL в план"""
    converter = SQLToPlanConverter()
    return converter.convert(sql)


# Примеры использования
if __name__ == "__main__":
    # Пример плана
    example_plan = {
        "tables": ["tbl_business_unit"],
        "fields": ["business_unit_name", "inn", "region"],
        "conditions": [
            {"field": "region", "operator": "=", "value": "Москва"}
        ],
        "order_by": ["business_unit_name"]
    }
    
    # Конвертация в SQL
    sql = plan_to_sql(example_plan)
    print("SQL:", sql)
    
    # Конвертация обратно в план
    plan = sql_to_plan(sql)
    print("План:", json.dumps(plan, ensure_ascii=False, indent=2))
