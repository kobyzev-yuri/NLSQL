#!/usr/bin/env python3
"""
Проверка отсутствующих таблиц в базе данных
"""

import sys
import os
import json
import pandas as pd
from pathlib import Path

# Добавляем путь к модулям
sys.path.append('src')
sys.path.append('.')

from src.vanna.vanna_pgvector_native import DocStructureVannaNative

def check_tables_in_database():
    """Проверяет какие таблицы есть в базе данных"""
    try:
        vanna = DocStructureVannaNative()
        
        # Получаем список всех таблиц в базе
        tables_query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
        ORDER BY table_name
        """
        
        df = vanna.run_sql(tables_query)
        existing_tables = df['table_name'].tolist()
        
        print("📋 Таблицы в базе данных:")
        for table in existing_tables:
            print(f"   ✅ {table}")
        
        return existing_tables
        
    except Exception as e:
        print(f"❌ Ошибка подключения к базе данных: {e}")
        return []

def check_tables_in_doc_structure():
    """Проверяет какие таблицы упоминаются в DocStructureSchema"""
    try:
        schema_data = {}
        
        # Загружаем EQDocTypes.json
        with open('DocStructureSchema/EQDocTypes.json', 'r', encoding='utf-8') as f:
            doc_types = json.load(f)
        
        # Извлекаем таблицы из DocStructureSchema
        schema_tables = set()
        for doc_type in doc_types:
            tablename = doc_type.get('tablename')
            if tablename:
                schema_tables.add(tablename)
        
        print("\n📋 Таблицы в DocStructureSchema:")
        for table in sorted(schema_tables):
            print(f"   📄 {table}")
        
        return list(schema_tables)
        
    except Exception as e:
        print(f"❌ Ошибка загрузки DocStructureSchema: {e}")
        return []

def find_missing_tables():
    """Находит отсутствующие таблицы"""
    print("🔍 Анализ отсутствующих таблиц")
    print("=" * 50)
    
    # Получаем таблицы из базы данных
    db_tables = check_tables_in_database()
    
    # Получаем таблицы из DocStructureSchema
    schema_tables = check_tables_in_doc_structure()
    
    if not db_tables or not schema_tables:
        print("❌ Не удалось получить данные")
        return
    
    # Находим отсутствующие таблицы
    missing_tables = []
    for table in schema_tables:
        if table not in db_tables:
            missing_tables.append(table)
    
    print(f"\n❌ Отсутствующие таблицы ({len(missing_tables)}):")
    for table in missing_tables:
        print(f"   🔴 {table}")
    
    # Находим лишние таблицы в базе
    extra_tables = []
    for table in db_tables:
        if table not in schema_tables:
            extra_tables.append(table)
    
    print(f"\n➕ Дополнительные таблицы в базе ({len(extra_tables)}):")
    for table in extra_tables:
        print(f"   🟢 {table}")
    
    # Анализируем конкретные таблицы из запроса
    requested_tables = [
        "tbl_countries",
        "tbl_swift", 
        "tbl_bik",
        "tbl_currencies",
        "tbl_contract_types",
        "tbl_assignment_types",
        "tbl_payment_statuses"
    ]
    
    print(f"\n🎯 Анализ запрошенных таблиц:")
    for table in requested_tables:
        if table in db_tables:
            print(f"   ✅ {table} - ЕСТЬ в базе")
        elif table in schema_tables:
            print(f"   📄 {table} - ЕСТЬ в DocStructureSchema, НЕТ в базе")
        else:
            print(f"   ❌ {table} - НЕТ ни в базе, ни в схеме")
    
    return missing_tables, extra_tables

def generate_ddl_requests(missing_tables):
    """Генерирует запросы DDL для отсутствующих таблиц"""
    if not missing_tables:
        print("\n✅ Все таблицы присутствуют в базе данных")
        return
    
    print(f"\n📝 Запросы DDL для отсутствующих таблиц:")
    print("=" * 50)
    
    for table in missing_tables:
        print(f"\n-- DDL для таблицы {table}")
        print(f"CREATE TABLE {table} (")
        print(f"    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),")
        print(f"    name VARCHAR(255) NOT NULL,")
        print(f"    description TEXT,")
        print(f"    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,")
        print(f"    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,")
        print(f"    deleted BOOLEAN DEFAULT FALSE")
        print(f");")
        print(f"")
        print(f"-- Индексы для таблицы {table}")
        print(f"CREATE INDEX idx_{table}_name ON {table}(name);")
        print(f"CREATE INDEX idx_{table}_deleted ON {table}(deleted);")
        print(f"")

def main():
    """Основная функция"""
    print("🔍 Проверка отсутствующих таблиц")
    print("=" * 50)
    
    missing_tables, extra_tables = find_missing_tables()
    
    if missing_tables:
        generate_ddl_requests(missing_tables)
        
        print(f"\n📋 Резюме:")
        print(f"   Всего таблиц в DocStructureSchema: {len(schema_tables) if 'schema_tables' in locals() else 0}")
        print(f"   Всего таблиц в базе данных: {len(db_tables) if 'db_tables' in locals() else 0}")
        print(f"   Отсутствующих таблиц: {len(missing_tables)}")
        print(f"   Дополнительных таблиц: {len(extra_tables)}")
    else:
        print("\n✅ Все таблицы из DocStructureSchema присутствуют в базе данных")

if __name__ == "__main__":
    main()
