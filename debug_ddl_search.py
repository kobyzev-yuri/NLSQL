#!/usr/bin/env python3
"""
Скрипт для отладки DDL поиска и анализа семантического поиска
"""

import asyncio
import asyncpg
import os
import logging
from typing import List, Dict, Any
from openai import OpenAI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DDLSearchDebugger:
    """Отладчик DDL поиска"""
    
    def __init__(self):
        self.database_url = "postgresql://postgres:1234@localhost:5432/test_docstructure"
        self.openai_client = OpenAI(
            api_key=os.getenv("PROXYAPI_KEY"),
            base_url="https://api.proxyapi.ru/openai/v1"
        )
    
    async def analyze_ddl_content(self):
        """Анализ содержимого DDL в векторной БД"""
        print("🔍 Анализ DDL содержимого...")
        
        conn = await asyncpg.connect(self.database_url)
        
        # Получаем все DDL записи
        ddl_records = await conn.fetch("""
            SELECT content, embedding IS NOT NULL as has_embedding
            FROM vanna_vectors 
            WHERE content_type = 'ddl'
            ORDER BY id
        """)
        
        print(f"📊 Найдено {len(ddl_records)} DDL записей")
        
        for i, record in enumerate(ddl_records, 1):
            content = record['content']
            has_embedding = record['has_embedding']
            print(f"\n--- DDL запись {i} (эмбеддинг: {'✅' if has_embedding else '❌'}) ---")
            print(content[:200] + "..." if len(content) > 200 else content)
        
        await conn.close()
        return ddl_records
    
    async def test_semantic_search(self, question: str):
        """Тестирование семантического поиска"""
        print(f"\n🔍 Тестирование семантического поиска для: '{question}'")
        
        # Генерируем эмбеддинг для вопроса
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-ada-002",
                input=question
            )
            question_embedding = response.data[0].embedding
            print(f"✅ Эмбеддинг вопроса сгенерирован: {len(question_embedding)} измерений")
        except Exception as e:
            print(f"❌ Ошибка генерации эмбеддинга: {e}")
            return []
        
        # Подключаемся к БД
        conn = await asyncpg.connect(self.database_url)
        
        # Конвертируем эмбеддинг в строку для pgvector
        embedding_str = '[' + ','.join(map(str, question_embedding)) + ']'
        
        # Семантический поиск
        query = """
            SELECT content, embedding <-> $1::vector as distance
            FROM vanna_vectors 
            WHERE content_type = 'ddl' AND embedding IS NOT NULL
            ORDER BY embedding <-> $1::vector
            LIMIT 5
        """
        
        results = await conn.fetch(query, embedding_str)
        await conn.close()
        
        print(f"📊 Найдено {len(results)} релевантных DDL записей:")
        for i, result in enumerate(results, 1):
            distance = result['distance']
            content = result['content']
            print(f"\n--- Результат {i} (расстояние: {distance:.4f}) ---")
            print(content[:300] + "..." if len(content) > 300 else content)
        
        return results
    
    async def check_missing_tables(self):
        """Проверка отсутствующих таблиц платежей"""
        print("\n🔍 Проверка отсутствующих таблиц платежей...")
        
        conn = await asyncpg.connect(self.database_url)
        
        # Получаем все таблицы из information_schema
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        
        table_names = [row['table_name'] for row in tables]
        print(f"📊 Найдено {len(table_names)} таблиц в БД:")
        for table in table_names:
            print(f"  - {table}")
        
        # Проверяем какие таблицы есть в DDL
        ddl_content = await conn.fetch("SELECT content FROM vanna_vectors WHERE content_type = 'ddl'")
        ddl_text = "\n".join([row['content'] for row in ddl_content])
        
        missing_tables = []
        for table in table_names:
            if table not in ddl_text:
                missing_tables.append(table)
        
        print(f"\n❌ Отсутствуют в DDL ({len(missing_tables)} таблиц):")
        for table in missing_tables:
            print(f"  - {table}")
        
        await conn.close()
        return missing_tables
    
    async def generate_ddl_for_missing_tables(self, missing_tables: List[str]):
        """Генерация DDL для отсутствующих таблиц"""
        print(f"\n🔧 Генерация DDL для {len(missing_tables)} отсутствующих таблиц...")
        
        conn = await asyncpg.connect(self.database_url)
        
        ddl_statements = []
        for table in missing_tables:
            try:
                # Получаем структуру таблицы
                columns = await conn.fetch("""
                    SELECT 
                        column_name, 
                        data_type, 
                        is_nullable,
                        column_default,
                        character_maximum_length
                    FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                    AND table_name = $1
                    ORDER BY ordinal_position
                """, table)
                
                # Получаем первичные ключи
                pk_columns = await conn.fetch("""
                    SELECT kcu.column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu 
                        ON tc.constraint_name = kcu.constraint_name
                    WHERE tc.table_schema = 'public' 
                    AND tc.table_name = $1
                    AND tc.constraint_type = 'PRIMARY KEY'
                """, table)
                
                # Получаем внешние ключи
                fk_constraints = await conn.fetch("""
                    SELECT 
                        kcu.column_name,
                        ccu.table_name AS foreign_table_name,
                        ccu.column_name AS foreign_column_name
                    FROM information_schema.table_constraints AS tc
                    JOIN information_schema.key_column_usage AS kcu
                        ON tc.constraint_name = kcu.constraint_name
                    JOIN information_schema.constraint_column_usage AS ccu
                        ON ccu.constraint_name = tc.constraint_name
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND tc.table_schema = 'public'
                    AND tc.table_name = $1
                """, table)
                
                # Генерируем DDL
                ddl_parts = [f"CREATE TABLE public.{table} ("]
                
                for col in columns:
                    col_def = f"    {col['column_name']} {col['data_type']}"
                    if col['character_maximum_length']:
                        col_def += f"({col['character_maximum_length']})"
                    if col['is_nullable'] == 'NO':
                        col_def += " NOT NULL"
                    if col['column_default']:
                        col_def += f" DEFAULT {col['column_default']}"
                    ddl_parts.append(col_def)
                
                # Добавляем первичные ключи
                if pk_columns:
                    pk_cols = [col['column_name'] for col in pk_columns]
                    ddl_parts.append(f"    PRIMARY KEY ({', '.join(pk_cols)})")
                
                ddl_parts.append(");")
                
                ddl_statement = "\n".join(ddl_parts)
                ddl_statements.append(ddl_statement)
                
                print(f"✅ DDL для {table} сгенерирован")
                
            except Exception as e:
                print(f"❌ Ошибка генерации DDL для {table}: {e}")
        
        await conn.close()
        return ddl_statements

async def main():
    """Основная функция отладки"""
    debugger = DDLSearchDebugger()
    
    print("🚀 Запуск отладки DDL поиска...")
    
    # 1. Анализ содержимого DDL
    ddl_records = await debugger.analyze_ddl_content()
    
    # 2. Проверка отсутствующих таблиц
    missing_tables = await debugger.check_missing_tables()
    
    # 3. Генерация DDL для отсутствующих таблиц
    if missing_tables:
        ddl_statements = await debugger.generate_ddl_for_missing_tables(missing_tables)
        
        # Сохраняем DDL в файл
        with open('missing_tables_ddl.sql', 'w', encoding='utf-8') as f:
            f.write("-- DDL для отсутствующих таблиц\n\n")
            for ddl in ddl_statements:
                f.write(ddl + "\n\n")
        
        print(f"\n💾 DDL сохранен в missing_tables_ddl.sql")
    
    # 4. Тестирование семантического поиска
    test_questions = [
        "Платежи за месяц по клиентам",
        "Покажи все платежи",
        "Статистика по платежам",
        "Пользователи системы"
    ]
    
    for question in test_questions:
        await debugger.test_semantic_search(question)
        print("\n" + "="*50)

if __name__ == "__main__":
    asyncio.run(main())
