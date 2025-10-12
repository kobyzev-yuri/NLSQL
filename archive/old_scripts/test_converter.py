#!/usr/bin/env python3
"""
Тестовый скрипт для проверки конвертера планов
"""

import json
import sys
from pathlib import Path

# Добавляем путь к модулям
sys.path.append('src')

from src.utils.plan_sql_converter import plan_to_sql, sql_to_plan


def test_plan_to_sql():
    """Тестирует конвертацию плана в SQL"""
    print("🧪 Тестирование: План → SQL")
    
    # Простой план
    simple_plan = {
        "tables": ["tbl_business_unit"],
        "fields": ["business_unit_name", "inn", "region"],
        "conditions": [
            {"field": "region", "operator": "=", "value": "Москва"}
        ],
        "order_by": ["business_unit_name"]
    }
    
    try:
        sql = plan_to_sql(simple_plan)
        print(f"✅ Простой план: {sql}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False
    
    # Сложный план с JOIN
    complex_plan = {
        "tables": ["tbl_principal_assignment", "tbl_business_unit"],
        "fields": ["pa.assignment_number", "pa.assignment_date", "pa.amount"],
        "joins": [
            {"table": "tbl_business_unit", "on": "pa.business_unit_id = bu.id", "type": "JOIN"}
        ],
        "conditions": [
            {"field": "pa.amount", "operator": ">", "value": "1000000"}
        ],
        "order_by": ["pa.amount DESC"]
    }
    
    try:
        sql = plan_to_sql(complex_plan)
        print(f"✅ Сложный план: {sql}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False
    
    return True


def test_sql_to_plan():
    """Тестирует конвертацию SQL в план"""
    print("\n🧪 Тестирование: SQL → План")
    
    # Простой SQL
    simple_sql = "SELECT business_unit_name, inn FROM tbl_business_unit WHERE region = 'Москва'"
    
    try:
        plan = sql_to_plan(simple_sql)
        print(f"✅ Простой SQL: {json.dumps(plan, ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False
    
    return True


def test_roundtrip():
    """Тестирует полный цикл: План → SQL → План"""
    print("\n🧪 Тестирование: План → SQL → План")
    
    original_plan = {
        "tables": ["tbl_business_unit"],
        "fields": ["business_unit_name", "inn"],
        "conditions": [
            {"field": "region", "operator": "=", "value": "Москва"}
        ]
    }
    
    try:
        # План → SQL
        sql = plan_to_sql(original_plan)
        print(f"SQL: {sql}")
        
        # SQL → План
        converted_plan = sql_to_plan(sql)
        print(f"План: {json.dumps(converted_plan, ensure_ascii=False, indent=2)}")
        
        print("✅ Цикл конвертации успешен")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


def create_example_files():
    """Создает примеры файлов для тестирования"""
    print("\n📁 Создание примеров файлов")
    
    # Создаем директорию для примеров
    examples_dir = Path("examples")
    examples_dir.mkdir(exist_ok=True)
    
    # Пример 1: Простой запрос
    simple_plan = {
        "question": "Покажи всех клиентов из Москвы",
        "plan": {
            "tables": ["tbl_business_unit"],
            "fields": ["business_unit_name", "inn", "region"],
            "conditions": [
                {"field": "region", "operator": "=", "value": "Москва"}
            ],
            "order_by": ["business_unit_name"]
        },
        "category": "Клиенты",
        "complexity": 2,
        "description": "Поиск клиентов по региону"
    }
    
    with open(examples_dir / "simple_plan.json", "w", encoding="utf-8") as f:
        json.dump(simple_plan, f, ensure_ascii=False, indent=2)
    
    # Пример 2: Сложный запрос
    complex_plan = {
        "question": "Покажи поручения старше 3 дней от клиентов категории А больше 1 млн рублей",
        "plan": {
            "tables": ["tbl_principal_assignment", "tbl_business_unit"],
            "fields": ["pa.assignment_number", "pa.assignment_date", "pa.amount", "bu.business_unit_name"],
            "joins": [
                {"table": "tbl_business_unit", "on": "pa.business_unit_id = bu.id", "type": "JOIN"}
            ],
            "conditions": [
                {"field": "pa.assignment_date", "operator": "<", "value": "CURRENT_DATE - INTERVAL '3 days'"},
                {"field": "bu.category", "operator": "=", "value": "A"},
                {"field": "pa.amount", "operator": ">", "value": "1000000"}
            ],
            "group_by": ["bu.business_unit_name"],
            "order_by": ["pa.amount DESC"]
        },
        "category": "Сложные запросы",
        "complexity": 4,
        "description": "Сложный запрос с множественными условиями"
    }
    
    with open(examples_dir / "complex_plan.json", "w", encoding="utf-8") as f:
        json.dump(complex_plan, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Созданы примеры в директории: {examples_dir}")
    print("   - simple_plan.json")
    print("   - complex_plan.json")


def main():
    """Основная функция тестирования"""
    print("🚀 Тестирование конвертера планов запросов")
    print("=" * 50)
    
    # Тестируем все функции
    tests = [
        test_plan_to_sql,
        test_sql_to_plan,
        test_roundtrip
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 Результат: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 Все тесты пройдены успешно!")
        
        # Создаем примеры файлов
        create_example_files()
        
        print("\n🔧 Примеры использования CLI:")
        print("python src/utils/plan_sql_cli.py plan-to-sql examples/simple_plan.json")
        print("python src/utils/plan_sql_cli.py validate examples/simple_plan.json")
        print("python src/utils/plan_sql_cli.py sql-to-plan \"SELECT * FROM users\"")
        
    else:
        print("❌ Некоторые тесты не пройдены")
        sys.exit(1)


if __name__ == "__main__":
    main()
