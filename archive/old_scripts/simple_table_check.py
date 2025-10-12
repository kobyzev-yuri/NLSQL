#!/usr/bin/env python3
"""
Простая проверка таблиц через Vanna AI
"""

import sys
sys.path.append('src')

from src.vanna.vanna_pgvector_native import DocStructureVannaNative

def check_tables_simple():
    """Простая проверка таблиц"""
    
    config = {
        'model': 'gpt-4o',
        'database_url': 'postgresql://postgres:1234@localhost:5432/test_docstructure',
        'api_key': 'sk-xF20r7G4tq9ezBMNKIjCPvva2io4S8FV',
        'base_url': 'https://api.proxyapi.ru/openai/v1'
    }
    
    try:
        vanna = DocStructureVannaNative(config=config)
        
        print("🔍 Проверяем таблицы в базе данных...")
        
        # Простой запрос для проверки таблиц
        tables_query = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
        
        print("📊 Выполняем запрос...")
        df = vanna.run_sql(tables_query)
        
        print(f"✅ Найдено таблиц: {len(df)}")
        print("📋 Список таблиц:")
        
        for table in df['table_name']:
            print(f"   - {table}")
        
        # Проверяем приоритетные таблицы
        priority_tables = [
            "equsers", "eq_departments", "eqgroups", "eqroles",
            "tbl_business_unit", "tbl_principal_assignment", 
            "tbl_incoming_payments", "tbl_accounts_document", "tbl_personal_account"
        ]
        
        print(f"\n🎯 Проверяем приоритетные таблицы:")
        found_count = 0
        
        for table in priority_tables:
            if table in df['table_name'].values:
                print(f"   ✅ {table}")
                found_count += 1
            else:
                print(f"   ❌ {table}")
        
        print(f"\n📊 Результат: {found_count}/{len(priority_tables)} приоритетных таблиц найдено")
        
        if found_count < len(priority_tables):
            print("💡 Проблема: не все приоритетные таблицы найдены в базе данных")
            print("🔧 Возможные решения:")
            print("   1. Загрузить дамп базы данных")
            print("   2. Проверить правильность названий таблиц")
            print("   3. Обновить список приоритетных таблиц")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    check_tables_simple()
