#!/usr/bin/env python3
"""
Быстрый тест Qwen моделей - только один простой вопрос
"""

import sys
from pathlib import Path

# Добавляем путь к модулям
sys.path.append(str(Path(__file__).parent / "src"))

from src.vanna.vanna_pgvector_native import DocStructureVannaNative

def quick_test_qwen():
    """Быстрый тест Qwen моделей"""
    
    print("🚀 Быстрый тест Qwen моделей")
    print("=" * 40)
    
    # Простой вопрос
    question = "Покажи всех пользователей"
    
    # Тестируем Qwen3:8b
    print("\n🧠 Тестирование Qwen3:8b...")
    qwen3_config = {
        'model': 'qwen3:8b',
        'database_url': 'postgresql://postgres:1234@localhost:5432/test_docstructure',
        'api_key': 'ollama',
        'base_url': 'http://localhost:11434/v1'
    }
    
    try:
        qwen3_vanna = DocStructureVannaNative(qwen3_config)
        sql = qwen3_vanna.generate_sql(question)
        print(f"✅ Qwen3:8b - {sql}")
    except Exception as e:
        print(f"❌ Qwen3:8b - Ошибка: {e}")
    
    # Тестируем Qwen2.5-coder:1.5b
    print("\n💻 Тестирование Qwen2.5-coder:1.5b...")
    qwen25_coder_config = {
        'model': 'qwen2.5-coder:1.5b',
        'database_url': 'postgresql://postgres:1234@localhost:5432/test_docstructure',
        'api_key': 'ollama',
        'base_url': 'http://localhost:11434/v1'
    }
    
    try:
        qwen25_coder_vanna = DocStructureVannaNative(qwen25_coder_config)
        sql = qwen25_coder_vanna.generate_sql(question)
        print(f"✅ Qwen2.5-coder:1.5b - {sql}")
    except Exception as e:
        print(f"❌ Qwen2.5-coder:1.5b - Ошибка: {e}")

if __name__ == "__main__":
    quick_test_qwen()
