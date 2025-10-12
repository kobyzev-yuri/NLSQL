#!/usr/bin/env python3
"""
Дебаг тест Qwen моделей с подробным логированием
"""

import sys
import time
from pathlib import Path

# Добавляем путь к модулям
sys.path.append(str(Path(__file__).parent / "src"))

def debug_test_qwen():
    """Дебаг тест Qwen моделей"""
    
    print("🚀 Дебаг тест Qwen моделей")
    print("=" * 40)
    
    # Проверяем подключение к Ollama
    print("\n1. Проверяем подключение к Ollama...")
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        print(f"✅ Ollama доступен: {response.status_code}")
        models = response.json().get('models', [])
        print(f"📋 Доступные модели: {[m['name'] for m in models]}")
    except Exception as e:
        print(f"❌ Ollama недоступен: {e}")
        return
    
    # Тестируем простой запрос к Ollama
    print("\n2. Тестируем простой запрос к Ollama...")
    try:
        import requests
        data = {
            "model": "qwen3:8b",
            "prompt": "Hello",
            "stream": False
        }
        print("📤 Отправляем запрос...")
        start_time = time.time()
        response = requests.post("http://localhost:11434/api/generate", 
                                json=data, timeout=30)
        end_time = time.time()
        print(f"✅ Ответ получен за {end_time - start_time:.2f} сек: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"💬 Ответ модели: {result.get('response', 'Нет ответа')[:100]}...")
        else:
            print(f"❌ Ошибка: {response.text}")
    except Exception as e:
        print(f"❌ Ошибка запроса к Ollama: {e}")
        return
    
    # Тестируем Vanna AI
    print("\n3. Тестируем Vanna AI...")
    try:
        from src.vanna.vanna_pgvector_native import DocStructureVannaNative
        
        config = {
            'model': 'qwen3:8b',
            'database_url': 'postgresql://postgres:1234@localhost:5432/test_docstructure',
            'api_key': 'ollama',
            'base_url': 'http://localhost:11434/v1'
        }
        
        print("📤 Инициализируем Vanna AI...")
        start_time = time.time()
        vanna = DocStructureVannaNative(config)
        init_time = time.time()
        print(f"✅ Vanna AI инициализирован за {init_time - start_time:.2f} сек")
        
        print("📤 Генерируем SQL...")
        start_time = time.time()
        sql = vanna.generate_sql("Покажи всех пользователей")
        end_time = time.time()
        print(f"✅ SQL сгенерирован за {end_time - start_time:.2f} сек: {sql}")
        
    except Exception as e:
        print(f"❌ Ошибка Vanna AI: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_test_qwen()
