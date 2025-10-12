#!/usr/bin/env python3
"""
Быстрый тест новых моделей: sqlcoder и phi3
"""

import sys
import time
from pathlib import Path

# Добавляем путь к модулям
sys.path.append(str(Path(__file__).parent / "src"))

def quick_test_new_models():
    """Быстрый тест новых моделей"""
    
    print("🚀 Быстрый тест новых моделей")
    print("=" * 40)
    
    # Новые модели для тестирования
    new_models = [
        "sqlcoder:latest",
        "phi3:latest",
    ]
    
    # Простой вопрос для тестирования
    question = "Покажи всех пользователей"
    
    for model_name in new_models:
        print(f"\n🧠 Тестирование {model_name}...")
        print("-" * 30)
        
        try:
            from src.vanna.vanna_pgvector_native import DocStructureVannaNative
            
            config = {
                'model': model_name,
                'database_url': 'postgresql://postgres:1234@localhost:5432/test_docstructure',
                'api_key': 'ollama',
                'base_url': 'http://localhost:11434/v1'
            }
            
            print(f"📤 Инициализация...")
            start_time = time.time()
            vanna = DocStructureVannaNative(config)
            init_time = time.time()
            print(f"✅ Инициализирован за {init_time - start_time:.2f} сек")
            
            print(f"❓ Вопрос: {question}")
            print("📤 Генерация SQL...")
            start_time = time.time()
            sql = vanna.generate_sql(question)
            end_time = time.time()
            
            print(f"✅ SQL сгенерирован за {end_time - start_time:.2f} сек")
            print(f"💡 SQL: {sql}")
            
            # Быстрая оценка качества
            if "equsers" in sql.lower():
                print("✅ Отлично: правильная таблица equsers")
                quality = "Отлично"
            elif "users" in sql.lower():
                print("⚠️ Средне: таблица users (возможно неправильно)")
                quality = "Средне"
            else:
                print("❌ Плохо: неправильные таблицы")
                quality = "Плохо"
            
            print(f"📊 {model_name}: {quality}, {end_time - start_time:.2f} сек")
            
        except Exception as e:
            print(f"❌ Ошибка с {model_name}: {e}")
    
    print(f"\n🏆 Быстрый тест завершен!")

if __name__ == "__main__":
    quick_test_new_models()
