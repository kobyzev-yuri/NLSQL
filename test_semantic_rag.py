#!/usr/bin/env python3
"""
Тестирование семантического RAG
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.vanna.vanna_semantic_fixed import create_semantic_vanna_client
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_semantic_rag():
    """Тестирование семантического RAG"""
    try:
        # Создаем клиент с семантическим поиском
        vanna = create_semantic_vanna_client()
        
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
                # Генерируем SQL с семантическим поиском
                sql = vanna.generate_sql(question)
                print(f"✅ SQL: {sql}")
                
            except Exception as e:
                print(f"❌ Ошибка: {e}")
        
        print("\n🎉 Тестирование завершено!")
        
    except Exception as e:
        logger.error(f"❌ Ошибка тестирования: {e}")

if __name__ == "__main__":
    test_semantic_rag()
