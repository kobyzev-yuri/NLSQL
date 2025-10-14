#!/usr/bin/env python3
"""
Отладка семантического поиска
"""

import sys
import os
import asyncio
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.vanna.vanna_semantic_fixed import create_semantic_vanna_client
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def debug_semantic_search():
    """Отладка семантического поиска"""
    try:
        # Создаем клиент
        vanna = create_semantic_vanna_client()
        
        question = "Покажи поручения за последний месяц"
        print(f"🔍 Вопрос: {question}")
        print("=" * 50)
        
        # Получаем DDL
        ddl_list = await vanna.get_related_ddl(question)
        print(f"📋 DDL ({len(ddl_list)} записей):")
        for i, ddl in enumerate(ddl_list):
            print(f"  {i+1}. {ddl[:200]}...")
        
        # Получаем документацию
        docs_list = await vanna.get_related_documentation(question)
        print(f"\n📄 Документация ({len(docs_list)} записей):")
        for i, doc in enumerate(docs_list):
            print(f"  {i+1}. {doc[:200]}...")
        
        # Получаем Q/A пары
        qa_list = await vanna.get_similar_question_sql(question)
        print(f"\n❓ Q/A пары ({len(qa_list)} записей):")
        for i, qa in enumerate(qa_list):
            print(f"  {i+1}. {qa[:200]}...")
        
    except Exception as e:
        logger.error(f"❌ Ошибка отладки: {e}")

if __name__ == "__main__":
    asyncio.run(debug_semantic_search())
