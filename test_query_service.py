#!/usr/bin/env python3
"""
Тестирование обновленного QueryService с семантическим RAG
"""

import sys
import os
import asyncio
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.services.query_service import QueryService
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_query_service():
    """Тестирование QueryService с семантическим RAG"""
    try:
        # Создаем сервис
        query_service = QueryService()
        
        # Тестовые вопросы
        test_questions = [
            "Покажи поручения за последний месяц",
            "Список пользователей по отделам",
            "Платежи по клиентам"
        ]
        
        for question in test_questions:
            print(f"\n🔍 Тестируем: {question}")
            print("=" * 50)
            
            try:
                # Генерируем SQL
                sql = await query_service.generate_sql(question, {})
                print(f"✅ SQL: {sql}")
                
            except Exception as e:
                print(f"❌ Ошибка: {e}")
        
        print("\n🎉 Тестирование QueryService завершено!")
        
    except Exception as e:
        logger.error(f"❌ Ошибка тестирования: {e}")

if __name__ == "__main__":
    asyncio.run(test_query_service())

