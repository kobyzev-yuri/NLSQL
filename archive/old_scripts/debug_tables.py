#!/usr/bin/env python3
"""
Отладка таблиц в базе данных
"""

import sys
sys.path.append('src')

from src.vanna.vanna_pgvector_native import DocStructureVannaNative

def check_tables():
    """Проверяем какие таблицы есть в базе"""
    
    config = {
        'model': 'llama3.1:8b',
        'database_url': 'postgresql://postgres:1234@localhost:5432/test_docstructure',
        'api_key': 'ollama',
        'base_url': 'http://localhost:11434/v1'
    }
    
    vanna = DocStructureVannaNative(config=config)
    
    # Проверяем все таблицы
    print("🔍 Проверяем все таблицы в базе данных...")
    
    try:
        # Запрос всех таблиц
        all_tables_query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name
        """
        
        df = vanna.run_sql(all_tables_query)
        print(f"📊 Всего таблиц в базе: {len(df)}")
        print("📋 Список таблиц:")
        for table in df['table_name']:
            print(f"   - {table}")
        
        # Проверяем приоритетные таблицы
        print("\n🎯 Проверяем приоритетные таблицы...")
        priority_tables = [
            "equsers", "eq_departments", "eqgroups", "eqroles",
            "tbl_business_unit", "tbl_principal_assignment", 
            "tbl_incoming_payments", "tbl_accounts_document", "tbl_personal_account"
        ]
        
        existing_priority = []
        missing_priority = []
        
        for table in priority_tables:
            if table in df['table_name'].values:
                existing_priority.append(table)
                print(f"   ✅ {table}")
            else:
                missing_priority.append(table)
                print(f"   ❌ {table}")
        
        print(f"\n📊 Статистика:")
        print(f"   Существующих приоритетных таблиц: {len(existing_priority)}/{len(priority_tables)}")
        print(f"   Отсутствующих: {len(missing_priority)}")
        
        if missing_priority:
            print(f"\n❌ Отсутствующие таблицы: {missing_priority}")
            print("💡 Возможно, нужно загрузить дамп базы данных")
        else:
            print("\n✅ Все приоритетные таблицы найдены!")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    check_tables()
