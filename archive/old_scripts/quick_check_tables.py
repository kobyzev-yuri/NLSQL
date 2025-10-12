#!/usr/bin/env python3
"""
Быстрая проверка таблиц без Vanna AI
"""

import psycopg2
import sys

def quick_check_tables():
    """Быстрая проверка таблиц в базе данных"""
    
    try:
        # Подключаемся к базе данных
        conn = psycopg2.connect(
            host="localhost",
            database="test_docstructure", 
            user="postgres",
            password="1234"
        )
        
        cursor = conn.cursor()
        
        # Проверяем все таблицы
        print("🔍 Проверяем все таблицы в базе данных...")
        
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        
        all_tables = [row[0] for row in cursor.fetchall()]
        print(f"📊 Всего таблиц в базе: {len(all_tables)}")
        
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
            if table in all_tables:
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
            
        # Проверяем содержимое одной из таблиц
        if existing_priority:
            test_table = existing_priority[0]
            print(f"\n🔍 Проверяем содержимое таблицы {test_table}...")
            
            cursor.execute(f"SELECT COUNT(*) FROM {test_table}")
            count = cursor.fetchone()[0]
            print(f"   Записей в {test_table}: {count}")
            
            if count > 0:
                cursor.execute(f"SELECT * FROM {test_table} LIMIT 3")
                rows = cursor.fetchall()
                print(f"   Примеры записей:")
                for i, row in enumerate(rows, 1):
                    print(f"     {i}. {row}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка подключения к базе данных: {e}")
        print("💡 Проверьте:")
        print("   - Запущен ли PostgreSQL")
        print("   - Правильные ли параметры подключения")
        print("   - Загружен ли дамп базы данных")

if __name__ == "__main__":
    quick_check_tables()
