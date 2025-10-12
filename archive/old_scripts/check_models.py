#!/usr/bin/env python3
"""
Проверка доступности моделей Ollama
"""

import requests
import json

def check_ollama_models():
    """Проверка доступных моделей в Ollama"""
    print("🔍 Проверка доступных моделей Ollama...")
    
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            print(f"✅ Найдено {len(models)} моделей:")
            
            for model in models:
                name = model.get('name', 'Unknown')
                size = model.get('size', 0)
                size_gb = size / (1024**3) if size > 0 else 0
                print(f"   📦 {name} ({size_gb:.1f} GB)")
            
            # Проверяем интересующие нас модели
            target_models = ['sqlcoder:latest', 'phi3:latest', 'qwen2.5:1.5b', 'llama3:latest']
            available_targets = [m['name'] for m in models]
            
            print(f"\n🎯 Целевые модели:")
            for target in target_models:
                if target in available_targets:
                    print(f"   ✅ {target} - доступна")
                else:
                    print(f"   ❌ {target} - недоступна")
            
            return models
        else:
            print(f"❌ Ошибка API: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"❌ Ошибка подключения к Ollama: {e}")
        return []

def test_model_availability():
    """Тест доступности моделей"""
    print("🧪 Тестирование доступности моделей...")
    
    models = check_ollama_models()
    if not models:
        return
    
    # Тестируем простой запрос для каждой модели
    test_prompt = "Hello"
    
    for model in models[:3]:  # Тестируем только первые 3 модели
        model_name = model.get('name', 'Unknown')
        print(f"\n🧠 Тестируем {model_name}...")
        
        try:
            data = {
                "model": model_name,
                "prompt": test_prompt,
                "stream": False
            }
            
            response = requests.post("http://localhost:11434/api/generate", 
                                  json=data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', '')[:50]
                print(f"   ✅ Работает: {response_text}...")
            else:
                print(f"   ❌ Ошибка: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")

if __name__ == "__main__":
    check_ollama_models()
    test_model_availability()
