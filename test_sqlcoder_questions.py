#!/usr/bin/env python3
"""
Тестирование sqlcoder:latest на стандартных вопросах
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

async def test_sqlcoder_questions():
    """Тестирование sqlcoder:latest на стандартных вопросах"""
    try:
        # Устанавливаем переменную окружения для sqlcoder
        os.environ['OLLAMA_MODEL'] = 'sqlcoder:latest'
        
        # Создаем сервис
        query_service = QueryService()
        
        # Стандартные тестовые вопросы
        test_questions = [
            "Покажи всех пользователей",
            "Список пользователей по отделам", 
            "Покажи поручения за последний месяц",
            "Платежи по клиентам",
            "Статистика по отделам"
        ]
        
        print("🤖 Тестирование sqlcoder:latest на стандартных вопросах")
        print("=" * 70)
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n🔍 Вопрос {i}: {question}")
            print("-" * 50)
            
            try:
                # Генерируем SQL
                sql = await query_service.generate_sql(question, {})
                print(f"✅ SQL: {sql}")
                
                # Проверяем качество SQL
                if sql and sql.strip():
                    if sql.lower().startswith('select'):
                        print("✅ Качество: Валидный SELECT запрос")
                    elif "не могу" in sql.lower() or "недостаточно" in sql.lower():
                        print("⚠️ Качество: Недостаточно контекста")
                    else:
                        print("❓ Качество: Неопределенное")
                else:
                    print("❌ Качество: Пустой ответ")
                    
            except Exception as e:
                print(f"❌ Ошибка: {e}")
        
        print("\n🎉 Тестирование sqlcoder завершено!")
        
    except Exception as e:
        logger.error(f"❌ Ошибка тестирования: {e}")

if __name__ == "__main__":
    asyncio.run(test_sqlcoder_questions())







