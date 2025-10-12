#!/usr/bin/env python3
"""
Тест Qwen2.5:1.5b (обычная версия, не coder)
"""

import sys
import time
from pathlib import Path

# Добавляем путь к модулям
sys.path.append(str(Path(__file__).parent / "src"))

def test_qwen25():
    """Тест Qwen2.5:1.5b"""
    
    print("🚀 Тест Qwen2.5:1.5b (обычная версия)")
    print("=" * 50)
    
    try:
        from src.vanna.vanna_pgvector_native import DocStructureVannaNative
        
        config = {
            'model': 'qwen2.5:1.5b',  # Обычная версия, не coder
            'database_url': 'postgresql://postgres:1234@localhost:5432/test_docstructure',
            'api_key': 'ollama',
            'base_url': 'http://localhost:11434/v1'
        }
        
        print("📤 Инициализируем Vanna AI...")
        start_time = time.time()
        vanna = DocStructureVannaNative(config)
        init_time = time.time()
        print(f"✅ Vanna AI инициализирован за {init_time - start_time:.2f} сек")
        
        # Простой вопрос
        question = "Покажи всех пользователей"
        print(f"\n❓ Вопрос: {question}")
        
        print("📤 Генерируем SQL...")
        start_time = time.time()
        sql = vanna.generate_sql(question)
        end_time = time.time()
        print(f"✅ SQL сгенерирован за {end_time - start_time:.2f} сек")
        print(f"💡 SQL: {sql}")
        
        # Проверяем качество SQL
        if "equsers" in sql.lower():
            print("✅ SQL содержит правильную таблицу equsers")
        elif "users" in sql.lower():
            print("⚠️ SQL содержит таблицу users (возможно неправильно)")
        else:
            print("❌ SQL не содержит ожидаемых таблиц")
            
        # Тестируем еще один вопрос
        print(f"\n❓ Вопрос 2: Список отделов")
        start_time = time.time()
        sql2 = vanna.generate_sql("Список отделов")
        end_time = time.time()
        print(f"✅ SQL сгенерирован за {end_time - start_time:.2f} сек")
        print(f"💡 SQL: {sql2}")
        
        if "eq_departments" in sql2.lower():
            print("✅ SQL содержит правильную таблицу eq_departments")
        else:
            print("❌ SQL не содержит таблицу eq_departments")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_qwen25()
