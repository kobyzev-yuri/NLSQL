#!/usr/bin/env python3
"""
Аудит покрытия знаний в RAG системе
"""

import asyncio
import asyncpg
import os
import logging
import json
from typing import List, Dict, Any, Set
from collections import defaultdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KnowledgeCoverageAuditor:
    """Аудитор покрытия знаний"""
    
    def __init__(self):
        self.database_url = "postgresql://postgres:1234@localhost:5432/test_docstructure"
    
    async def audit_vector_db_coverage(self):
        """Аудит покрытия векторной БД"""
        print("🔍 Аудит покрытия векторной БД...")
        
        conn = await asyncpg.connect(self.database_url)
        
        # Статистика по типам контента
        content_stats = await conn.fetch("""
            SELECT content_type, COUNT(*) as count, 
                   COUNT(CASE WHEN embedding IS NOT NULL THEN 1 END) as with_embedding
            FROM vanna_vectors 
            GROUP BY content_type 
            ORDER BY count DESC
        """)
        
        print("\n📊 Статистика по типам контента:")
        for stat in content_stats:
            print(f"  {stat['content_type']}: {stat['count']} записей ({stat['with_embedding']} с эмбеддингами)")
        
        # Анализ DDL покрытия
        ddl_content = await conn.fetch("SELECT content FROM vanna_vectors WHERE content_type = 'ddl'")
        ddl_text = "\n".join([row['content'] for row in ddl_content])
        
        # Получаем все таблицы из БД
        db_tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        
        db_table_names = {row['table_name'] for row in db_tables}
        
        # Проверяем покрытие DDL
        covered_tables = set()
        for table_name in db_table_names:
            if table_name in ddl_text:
                covered_tables.add(table_name)
        
        missing_tables = db_table_names - covered_tables
        
        print(f"\n📊 Покрытие DDL:")
        print(f"  Всего таблиц в БД: {len(db_table_names)}")
        print(f"  Покрыто DDL: {len(covered_tables)} ({len(covered_tables)/len(db_table_names)*100:.1f}%)")
        print(f"  Отсутствует в DDL: {len(missing_tables)}")
        
        # Фокусируемся на платежных таблицах
        payment_tables = {t for t in db_table_names if 'payment' in t.lower() or 'tbl_' in t.lower()}
        payment_covered = payment_tables & covered_tables
        payment_missing = payment_tables - covered_tables
        
        print(f"\n💰 Покрытие платежных таблиц:")
        print(f"  Платежные таблицы в БД: {len(payment_tables)}")
        print(f"  Покрыто DDL: {len(payment_covered)}")
        print(f"  Отсутствует в DDL: {len(payment_missing)}")
        
        if payment_missing:
            print(f"  Отсутствующие платежные таблицы:")
            for table in sorted(payment_missing):
                print(f"    - {table}")
        
        await conn.close()
        
        return {
            'content_stats': [dict(stat) for stat in content_stats],
            'total_tables': len(db_table_names),
            'covered_tables': len(covered_tables),
            'missing_tables': list(missing_tables),
            'payment_tables': list(payment_tables),
            'payment_covered': len(payment_covered),
            'payment_missing': list(payment_missing)
        }
    
    async def audit_docstructure_schema(self):
        """Аудит DocStructureSchema (JSON/XML от заказчика)"""
        print("\n🔍 Аудит DocStructureSchema...")
        
        # Проверяем наличие файлов DocStructureSchema
        docstructure_files = []
        docstructure_dir = "/mnt/ai/cnn/sql4A/DocStructureSchema"
        
        if os.path.exists(docstructure_dir):
            for file in os.listdir(docstructure_dir):
                if file.endswith(('.json', '.xml')):
                    docstructure_files.append(file)
        
        print(f"📁 Найдено файлов DocStructureSchema: {len(docstructure_files)}")
        for file in sorted(docstructure_files):
            print(f"  - {file}")
        
        # Анализируем содержимое JSON файлов
        json_tables = set()
        json_fields = set()
        
        for file in docstructure_files:
            if file.endswith('.json'):
                file_path = os.path.join(docstructure_dir, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Извлекаем таблицы и поля
                    if isinstance(data, dict):
                        for key, value in data.items():
                            if isinstance(value, dict):
                                if 'table' in key.lower() or 'table' in str(value).lower():
                                    json_tables.add(key)
                                if 'field' in key.lower() or 'field' in str(value).lower():
                                    json_fields.add(key)
                    
                    # Ищем упоминания таблиц в содержимом
                    content = str(data).lower()
                    if 'tbl_' in content:
                        # Простой поиск упоминаний таблиц
                        import re
                        table_matches = re.findall(r'tbl_\w+', content)
                        json_tables.update(table_matches)
                
                except Exception as e:
                    print(f"  ❌ Ошибка чтения {file}: {e}")
        
        print(f"\n📊 Анализ DocStructureSchema:")
        print(f"  Найдено таблиц: {len(json_tables)}")
        print(f"  Найдено полей: {len(json_fields)}")
        
        if json_tables:
            print(f"  Таблицы в DocStructureSchema:")
            for table in sorted(json_tables):
                print(f"    - {table}")
        
        return {
            'files': docstructure_files,
            'tables': list(json_tables),
            'fields': list(json_fields)
        }
    
    async def audit_qa_coverage(self):
        """Аудит покрытия Q/A пар"""
        print("\n🔍 Аудит покрытия Q/A пар...")
        
        conn = await asyncpg.connect(self.database_url)
        
        # Анализ Q/A пар
        qa_stats = await conn.fetch("""
            SELECT 
                COUNT(*) as total_qa,
                COUNT(CASE WHEN content ILIKE '%payment%' THEN 1 END) as payment_qa,
                COUNT(CASE WHEN content ILIKE '%tbl_%' THEN 1 END) as table_qa,
                COUNT(CASE WHEN content ILIKE '%SELECT%' THEN 1 END) as sql_qa
            FROM vanna_vectors 
            WHERE content_type = 'question_sql'
        """)
        
        if qa_stats:
            stat = qa_stats[0]
            print(f"📊 Статистика Q/A пар:")
            print(f"  Всего Q/A: {stat['total_qa']}")
            print(f"  С упоминанием 'payment': {stat['payment_qa']}")
            print(f"  С упоминанием 'tbl_': {stat['table_qa']}")
            print(f"  С SQL запросами: {stat['sql_qa']}")
        
        # Примеры Q/A пар
        sample_qa = await conn.fetch("""
            SELECT content 
            FROM vanna_vectors 
            WHERE content_type = 'question_sql'
            ORDER BY id
            LIMIT 3
        """)
        
        print(f"\n📝 Примеры Q/A пар:")
        for i, qa in enumerate(sample_qa, 1):
            content = qa['content']
            preview = content[:200] + "..." if len(content) > 200 else content
            print(f"  {i}. {preview}")
        
        await conn.close()
        
        return dict(qa_stats[0]) if qa_stats else {}
    
    async def audit_documentation_coverage(self):
        """Аудит покрытия документации"""
        print("\n🔍 Аудит покрытия документации...")
        
        conn = await asyncpg.connect(self.database_url)
        
        # Анализ документации
        doc_stats = await conn.fetch("""
            SELECT 
                COUNT(*) as total_docs,
                COUNT(CASE WHEN content ILIKE '%payment%' THEN 1 END) as payment_docs,
                COUNT(CASE WHEN content ILIKE '%tbl_%' THEN 1 END) as table_docs,
                COUNT(CASE WHEN content ILIKE '%CREATE TABLE%' THEN 1 END) as ddl_docs
            FROM vanna_vectors 
            WHERE content_type = 'documentation'
        """)
        
        if doc_stats:
            stat = doc_stats[0]
            print(f"📊 Статистика документации:")
            print(f"  Всего документов: {stat['total_docs']}")
            print(f"  С упоминанием 'payment': {stat['payment_docs']}")
            print(f"  С упоминанием 'tbl_': {stat['table_docs']}")
            print(f"  С DDL: {stat['ddl_docs']}")
        
        # Примеры документации
        sample_docs = await conn.fetch("""
            SELECT content 
            FROM vanna_vectors 
            WHERE content_type = 'documentation'
            AND content ILIKE '%payment%'
            ORDER BY id
            LIMIT 3
        """)
        
        print(f"\n📝 Примеры документации по платежам:")
        for i, doc in enumerate(sample_docs, 1):
            content = doc['content']
            preview = content[:200] + "..." if len(content) > 200 else content
            print(f"  {i}. {preview}")
        
        await conn.close()
        
        return dict(doc_stats[0]) if doc_stats else {}
    
    async def generate_coverage_report(self):
        """Генерация отчета о покрытии"""
        print("\n📋 Генерация отчета о покрытии...")
        
        # Собираем все данные
        vector_stats = await self.audit_vector_db_coverage()
        docstructure_stats = await self.audit_docstructure_schema()
        qa_stats = await self.audit_qa_coverage()
        doc_stats = await self.audit_documentation_coverage()
        
        # Анализ достаточности
        print("\n🎯 Анализ достаточности знаний:")
        
        # 1. Достаточно ли DocStructureSchema?
        docstructure_tables = set(docstructure_stats['tables'])
        db_tables = set(vector_stats['missing_tables'] + [t for t in vector_stats['payment_tables'] if t in vector_stats['missing_tables']])
        
        docstructure_coverage = len(docstructure_tables & db_tables) / len(db_tables) if db_tables else 0
        
        print(f"  📁 DocStructureSchema покрытие: {docstructure_coverage:.1%}")
        if docstructure_coverage < 0.5:
            print("    ❌ DocStructureSchema недостаточно - нужны DDL из БД")
        else:
            print("    ✅ DocStructureSchema достаточно")
        
        # 2. Достаточно ли Q/A пар?
        qa_coverage = qa_stats.get('payment_qa', 0) / max(qa_stats.get('total_qa', 1), 1)
        print(f"  ❓ Q/A покрытие платежей: {qa_coverage:.1%}")
        if qa_coverage < 0.1:
            print("    ❌ Q/A недостаточно - нужны примеры по платежам")
        else:
            print("    ✅ Q/A достаточно")
        
        # 3. Достаточно ли документации?
        doc_coverage = doc_stats.get('payment_docs', 0) / max(doc_stats.get('total_docs', 1), 1)
        print(f"  📚 Документация по платежам: {doc_coverage:.1%}")
        if doc_coverage < 0.1:
            print("    ❌ Документации недостаточно")
        else:
            print("    ✅ Документации достаточно")
        
        # Рекомендации
        print(f"\n💡 Рекомендации:")
        
        if docstructure_coverage < 0.5:
            print("  1. 🔧 Добавить DDL из живой БД для недостающих таблиц")
        
        if qa_coverage < 0.1:
            print("  2. 📝 Добавить Q/A примеры по платежам")
        
        if doc_coverage < 0.1:
            print("  3. 📚 Расширить документацию по платежам")
        
        if vector_stats['payment_missing']:
            print(f"  4. 🎯 Приоритет: добавить DDL для {vector_stats['payment_missing']}")
        
        return {
            'vector_stats': vector_stats,
            'docstructure_stats': docstructure_stats,
            'qa_stats': qa_stats,
            'doc_stats': doc_stats,
            'recommendations': {
                'docstructure_sufficient': docstructure_coverage >= 0.5,
                'qa_sufficient': qa_coverage >= 0.1,
                'doc_sufficient': doc_coverage >= 0.1
            }
        }

async def main():
    """Основная функция аудита"""
    auditor = KnowledgeCoverageAuditor()
    
    print("🚀 Запуск аудита покрытия знаний...")
    
    report = await auditor.generate_coverage_report()
    
    print("\n✅ Аудит завершен!")
    print(f"📊 Отчет сохранен в памяти, готов к анализу")

if __name__ == "__main__":
    asyncio.run(main())
