#!/usr/bin/env python3
"""
Тест новых моделей: sqlcoder:latest и phi3
"""

import sys
import time
from pathlib import Path

# Добавляем путь к модулям
sys.path.append(str(Path(__file__).parent / "src"))

def test_new_models():
    """Тест новых моделей"""
    
    print("🚀 Тест новых моделей: sqlcoder:latest и phi3")
    print("=" * 60)
    
    # Список моделей для тестирования
    models_to_test = [
        "sqlcoder:latest",
        "phi3:latest",  # или другое имя phi3 модели
    ]
    
    question = "Покажи всех пользователей"
    
    for model_name in models_to_test:
        print(f"\n🧠 Тестирование {model_name}...")
        print("-" * 40)
        
        try:
            from src.vanna.vanna_pgvector_native import DocStructureVannaNative
            
            config = {
                'model': model_name,
                'database_url': 'postgresql://postgres:1234@localhost:5432/test_docstructure',
                'api_key': 'ollama',
                'base_url': 'http://localhost:11434/v1'
            }
            
            print(f"📤 Инициализируем {model_name}...")
            start_time = time.time()
            vanna = DocStructureVannaNative(config)
            init_time = time.time()
            print(f"✅ {model_name} инициализирован за {init_time - start_time:.2f} сек")
            
            print(f"❓ Вопрос: {question}")
            print("📤 Генерируем SQL...")
            start_time = time.time()
            sql = vanna.generate_sql(question)
            end_time = time.time()
            print(f"✅ SQL сгенерирован за {end_time - start_time:.2f} сек")
            print(f"💡 SQL: {sql}")
            
            # Проверяем качество SQL
            if "equsers" in sql.lower():
                print("✅ SQL содержит правильную таблицу equsers")
                quality = "Отлично"
            elif "users" in sql.lower():
                print("⚠️ SQL содержит таблицу users (возможно неправильно)")
                quality = "Средне"
            else:
                print("❌ SQL не содержит ожидаемых таблиц")
                quality = "Плохо"
            
            # Тестируем второй вопрос
            print(f"\n❓ Вопрос 2: Список отделов")
            start_time = time.time()
            sql2 = vanna.generate_sql("Список отделов")
            end_time = time.time()
            print(f"✅ SQL сгенерирован за {end_time - start_time:.2f} сек")
            print(f"💡 SQL: {sql2}")
            
            if "eq_departments" in sql2.lower():
                print("✅ SQL содержит правильную таблицу eq_departments")
                quality2 = "Отлично"
            elif "department" in sql2.lower():
                print("⚠️ SQL содержит department (возможно неправильно)")
                quality2 = "Средне"
            else:
                print("❌ SQL не содержит таблицу eq_departments")
                quality2 = "Плохо"
            
            print(f"\n📊 Результат {model_name}:")
            print(f"   Качество SQL: {quality} / {quality2}")
            print(f"   Скорость: {end_time - start_time:.2f} сек")
            
        except Exception as e:
            print(f"❌ Ошибка с {model_name}: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n🏆 Тестирование завершено!")

if __name__ == "__main__":
    test_new_models()
