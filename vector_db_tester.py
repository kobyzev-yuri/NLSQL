#!/usr/bin/env python3
"""
Тестирование векторной базы данных через FastAPI
Использует реальные эндпоинты для тестирования семантического поиска
"""

import requests
import json
import time
from typing import List, Dict, Any, Optional

class VectorDBTester:
    """Тестер векторной базы данных через FastAPI"""
    
    def __init__(self, api_base_url: str = "http://localhost:3000"):
        self.api_base_url = api_base_url
        self.session = requests.Session()
        self.session.timeout = 30
    
    def test_api_health(self) -> bool:
        """Проверка доступности API"""
        try:
            response = self.session.get(f"{self.api_base_url}/health")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ API доступен: {data.get('status', 'unknown')}")
                return True
            else:
                print(f"❌ API недоступен: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Ошибка подключения к API: {e}")
            return False
    
    def test_semantic_search(self, question: str, search_type: str = "semantic") -> Dict[str, Any]:
        """Тестирование семантического поиска"""
        try:
            # Используем эндпоинт для тестирования поиска
            response = self.session.post(
                f"{self.api_base_url}/test-search",
                json={
                    "question": question,
                    "search_type": search_type,
                    "limit": 5
                }
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}", "details": response.text}
                
        except Exception as e:
            return {"error": str(e)}
    
    def test_sql_generation(self, question: str) -> Dict[str, Any]:
        """Тестирование генерации SQL"""
        try:
            response = self.session.post(
                f"{self.api_base_url}/generate-sql",
                data={"question": question}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}", "details": response.text}
                
        except Exception as e:
            return {"error": str(e)}
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Комплексное тестирование векторки"""
        print("🔍 Комплексное тестирование векторной базы данных")
        print("=" * 60)
        
        # Проверка доступности API
        if not self.test_api_health():
            return {"error": "API недоступен"}
        
        # Тестовые вопросы
        test_questions = [
            "Покажи всех пользователей",
            "Список отделов", 
            "Платежи по клиентам",
            "Пользователи с ролями",
            "Статистика по поручениям"
        ]
        
        results = {
            "api_health": True,
            "test_questions": [],
            "summary": {
                "total_tests": len(test_questions),
                "successful_tests": 0,
                "failed_tests": 0
            }
        }
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n📝 Тест {i}/{len(test_questions)}: {question}")
            
            # Тестируем семантический поиск
            search_result = self.test_semantic_search(question)
            
            # Тестируем генерацию SQL
            sql_result = self.test_sql_generation(question)
            
            test_result = {
                "question": question,
                "search_result": search_result,
                "sql_result": sql_result,
                "success": "error" not in search_result and "error" not in sql_result
            }
            
            if test_result["success"]:
                results["summary"]["successful_tests"] += 1
                print(f"  ✅ Успешно")
            else:
                results["summary"]["failed_tests"] += 1
                print(f"  ❌ Ошибка")
            
            results["test_questions"].append(test_result)
            
            # Небольшая пауза между запросами
            time.sleep(1)
        
        # Итоговая статистика
        print(f"\n📊 Итоги тестирования:")
        print(f"  Всего тестов: {results['summary']['total_tests']}")
        print(f"  Успешных: {results['summary']['successful_tests']}")
        print(f"  Неудачных: {results['summary']['failed_tests']}")
        
        success_rate = (results['summary']['successful_tests'] / results['summary']['total_tests']) * 100
        print(f"  Процент успеха: {success_rate:.1f}%")
        
        return results
    
    def test_specific_question(self, question: str) -> Dict[str, Any]:
        """Тестирование конкретного вопроса"""
        print(f"🔍 Тестирование вопроса: {question}")
        print("=" * 50)
        
        # Проверка API
        if not self.test_api_health():
            return {"error": "API недоступен"}
        
        # Семантический поиск
        print("\n1. Семантический поиск:")
        search_result = self.test_semantic_search(question)
        if "error" in search_result:
            print(f"   ❌ Ошибка: {search_result['error']}")
        else:
            print(f"   ✅ Найдено результатов: {len(search_result.get('results', []))}")
            for i, result in enumerate(search_result.get('results', [])[:3], 1):
                preview = result.get('content', '')[:100] + "..." if len(result.get('content', '')) > 100 else result.get('content', '')
                print(f"     {i}. {preview}")
        
        # Генерация SQL
        print("\n2. Генерация SQL:")
        sql_result = self.test_sql_generation(question)
        if "error" in sql_result:
            print(f"   ❌ Ошибка: {sql_result['error']}")
        else:
            sql = sql_result.get('sql', '')
            print(f"   ✅ SQL: {sql[:200]}{'...' if len(sql) > 200 else ''}")
        
        return {
            "question": question,
            "search_result": search_result,
            "sql_result": sql_result
        }

def main():
    """Основная функция тестирования"""
    print("🎯 Тестирование векторной базы данных")
    print("=" * 50)
    
    # Создаем тестер
    tester = VectorDBTester()
    
    # Выбор режима тестирования
    print("Выберите режим тестирования:")
    print("1. Комплексное тестирование")
    print("2. Тестирование конкретного вопроса")
    
    choice = input("\nВведите номер (1 или 2): ").strip()
    
    if choice == "1":
        # Комплексное тестирование
        results = tester.run_comprehensive_test()
        
        # Сохраняем результаты
        with open("vector_db_test_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Результаты сохранены в vector_db_test_results.json")
        
    elif choice == "2":
        # Тестирование конкретного вопроса
        question = input("Введите вопрос для тестирования: ").strip()
        if question:
            results = tester.test_specific_question(question)
            
            # Сохраняем результаты
            with open("vector_db_single_test.json", "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            print(f"\n💾 Результаты сохранены в vector_db_single_test.json")
        else:
            print("❌ Вопрос не введен")
    
    else:
        print("❌ Неверный выбор")

if __name__ == "__main__":
    main()
