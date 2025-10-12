#!/usr/bin/env python3
"""
CLI инструмент для конвертации между планами и SQL
Использование:
    python plan_sql_cli.py plan-to-sql plan.json
    python plan_sql_cli.py sql-to-plan "SELECT * FROM users"
    python plan_sql_cli.py validate plan.json
"""

import json
import sys
import argparse
from pathlib import Path
from plan_sql_converter import plan_to_sql, sql_to_plan


def plan_to_sql_cli(plan_file: str):
    """Конвертирует план в SQL"""
    try:
        with open(plan_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Извлекаем план (может быть в поле 'plan' или быть корневым объектом)
        if 'plan' in data:
            plan = data['plan']
        else:
            plan = data
        
        sql = plan_to_sql(plan)
        print("SQL запрос:")
        print(sql)
        
        # Сохраняем в файл
        output_file = plan_file.replace('.json', '_converted.sql')
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(sql)
        print(f"\nSQL сохранен в: {output_file}")
        
    except Exception as e:
        print(f"Ошибка: {e}")
        sys.exit(1)


def sql_to_plan_cli(sql_query: str):
    """Конвертирует SQL в план"""
    try:
        plan = sql_to_plan(sql_query)
        print("План запроса:")
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        
        # Сохраняем в файл
        output_file = "converted_plan.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(plan, f, ensure_ascii=False, indent=2)
        print(f"\nПлан сохранен в: {output_file}")
        
    except Exception as e:
        print(f"Ошибка: {e}")
        sys.exit(1)


def validate_plan_cli(plan_file: str):
    """Валидирует план запроса"""
    try:
        with open(plan_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Извлекаем план (может быть в поле 'plan' или быть корневым объектом)
        if 'plan' in data:
            plan = data['plan']
        else:
            plan = data
        
        # Проверяем обязательные поля
        required_fields = ['tables', 'fields']
        missing_fields = [field for field in required_fields if field not in plan]
        
        if missing_fields:
            print(f"❌ Отсутствуют обязательные поля: {missing_fields}")
            return False
        
        # Проверяем типы полей
        if not isinstance(plan['tables'], list) or not plan['tables']:
            print("❌ Поле 'tables' должно быть непустым списком")
            return False
        
        if not isinstance(plan['fields'], list) or not plan['fields']:
            print("❌ Поле 'fields' должно быть непустым списком")
            return False
        
        # Проверяем опциональные поля
        optional_fields = ['conditions', 'joins', 'group_by', 'order_by', 'limit']
        for field in optional_fields:
            if field in plan:
                if field == 'conditions' and not isinstance(plan[field], list):
                    print(f"❌ Поле '{field}' должно быть списком")
                    return False
                elif field == 'joins' and not isinstance(plan[field], list):
                    print(f"❌ Поле '{field}' должно быть списком")
                    return False
                elif field == 'group_by' and not isinstance(plan[field], list):
                    print(f"❌ Поле '{field}' должно быть списком")
                    return False
                elif field == 'order_by' and not isinstance(plan[field], list):
                    print(f"❌ Поле '{field}' должно быть списком")
                    return False
                elif field == 'limit' and not isinstance(plan[field], int):
                    print(f"❌ Поле '{field}' должно быть числом")
                    return False
        
        print("✅ План валиден")
        
        # Пробуем конвертировать в SQL
        try:
            sql = plan_to_sql(plan)
            print("✅ План успешно конвертируется в SQL")
            print(f"SQL: {sql}")
        except Exception as e:
            print(f"❌ Ошибка конвертации в SQL: {e}")
            return False
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Ошибка JSON: {e}")
        return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


def batch_convert_cli(input_dir: str, output_dir: str):
    """Пакетная конвертация планов в SQL"""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    if not input_path.exists():
        print(f"❌ Директория {input_dir} не существует")
        sys.exit(1)
    
    output_path.mkdir(exist_ok=True)
    
    json_files = list(input_path.glob("*.json"))
    if not json_files:
        print(f"❌ В директории {input_dir} нет JSON файлов")
        sys.exit(1)
    
    success_count = 0
    error_count = 0
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                plan = json.load(f)
            
            sql = plan_to_sql(plan)
            
            # Сохраняем SQL
            sql_file = output_path / f"{json_file.stem}.sql"
            with open(sql_file, 'w', encoding='utf-8') as f:
                f.write(sql)
            
            print(f"✅ {json_file.name} -> {sql_file.name}")
            success_count += 1
            
        except Exception as e:
            print(f"❌ {json_file.name}: {e}")
            error_count += 1
    
    print(f"\n📊 Результат: {success_count} успешно, {error_count} ошибок")


def main():
    parser = argparse.ArgumentParser(
        description="CLI инструмент для конвертации между планами и SQL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python plan_sql_cli.py plan-to-sql plan.json
  python plan_sql_cli.py sql-to-plan "SELECT * FROM users WHERE id = 1"
  python plan_sql_cli.py validate plan.json
  python plan_sql_cli.py batch-convert ./plans ./sql_output
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Доступные команды')
    
    # plan-to-sql
    plan_to_sql_parser = subparsers.add_parser('plan-to-sql', help='Конвертировать план в SQL')
    plan_to_sql_parser.add_argument('plan_file', help='Файл с планом (JSON)')
    
    # sql-to-plan
    sql_to_plan_parser = subparsers.add_parser('sql-to-plan', help='Конвертировать SQL в план')
    sql_to_plan_parser.add_argument('sql_query', help='SQL запрос')
    
    # validate
    validate_parser = subparsers.add_parser('validate', help='Валидировать план')
    validate_parser.add_argument('plan_file', help='Файл с планом (JSON)')
    
    # batch-convert
    batch_parser = subparsers.add_parser('batch-convert', help='Пакетная конвертация')
    batch_parser.add_argument('input_dir', help='Директория с планами')
    batch_parser.add_argument('output_dir', help='Директория для SQL файлов')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if args.command == 'plan-to-sql':
        plan_to_sql_cli(args.plan_file)
    elif args.command == 'sql-to-plan':
        sql_to_plan_cli(args.sql_query)
    elif args.command == 'validate':
        validate_plan_cli(args.plan_file)
    elif args.command == 'batch-convert':
        batch_convert_cli(args.input_dir, args.output_dir)


if __name__ == "__main__":
    main()
