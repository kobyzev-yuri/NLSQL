#!/usr/bin/env python3
"""
Простой тест агента с правильным контекстом
"""

import os
import sys
import logging
from pathlib import Path

# Добавляем путь к модулям
sys.path.append(str(Path(__file__).parent))

from src.vanna.vanna_pgvector_native import DocStructureVannaNative

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_simple_agent():
    """Простой тест агента"""
    
    # Конфигурация для GPT-4o
    gpt4_config = {
        "database_url": "postgresql://postgres:1234@localhost:5432/test_docstructure",
        "vector_table": "vanna_vectors",
        "api_key": os.getenv("PROXYAPI_KEY") or os.getenv("PROXYAPI_API_KEY") or os.getenv("OPENAI_API_KEY"),
        "model": "gpt-4o",
        "base_url": "https://api.proxyapi.ru/openai/v1",
        "temperature": 0.2
    }
    
    try:
        # Инициализируем агента
        logger.info("🔧 Инициализация агента...")
        agent = DocStructureVannaNative(gpt4_config)
        logger.info("✅ Агент инициализирован")
        
        # Тестируем простой запрос
        question = "Покажи всех пользователей"
        logger.info(f"❓ Тестирование: '{question}'")
        
        # Генерируем SQL
        sql = agent.generate_sql(question)
        logger.info(f"📝 Сгенерированный SQL: {sql}")
        
        # Проверяем результат
        if sql and not sql.startswith("The provided context is insufficient"):
            logger.info("✅ Агент работает корректно")
            return True
        else:
            logger.warning("⚠️ Агент не может сгенерировать SQL")
            return False
            
    except Exception as e:
        logger.error(f"❌ Ошибка тестирования: {e}")
        return False

if __name__ == "__main__":
    success = test_simple_agent()
    if success:
        print("✅ Тест пройден успешно")
    else:
        print("❌ Тест не пройден")
        sys.exit(1)
