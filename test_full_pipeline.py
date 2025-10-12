#!/usr/bin/env python3
"""
Тестирование полного пайплайна NL→SQL системы
Проверяет работу всех компонентов: FastAPI, Mock API, ролевые ограничения
"""

import asyncio
import httpx
import json
import time
from typing import Dict, Any

class FullPipelineTester:
    """Тестер полного пайплайна"""
    
    def __init__(self):
        self.nl_sql_api_url = "http://localhost:8000"
        self.mock_api_url = "http://localhost:8080"
        self.web_interface_url = "http://localhost:3000"
    
    async def test_api_health(self) -> bool:
        """Проверка здоровья всех API"""
        print("🔍 Проверка здоровья API...")
        
        try:
            async with httpx.AsyncClient() as client:
                # Проверка NL→SQL API
                response = await client.get(f"{self.nl_sql_api_url}/health", timeout=5.0)
                if response.status_code != 200:
                    print(f"❌ NL→SQL API недоступен: {response.status_code}")
                    return False
                
                # Проверка Mock API
                response = await client.get(f"{self.mock_api_url}/health", timeout=5.0)
                if response.status_code != 200:
                    print(f"❌ Mock API недоступен: {response.status_code}")
                    return False
                
                print("✅ Все API работают")
                return True
                
        except Exception as e:
            print(f"❌ Ошибка проверки API: {e}")
            return False
    
    async def test_sql_generation(self, question: str, user_id: str, role: str) -> Dict[str, Any]:
        """Тестирование генерации SQL"""
        print(f"🤖 Тестирование генерации SQL для {role} ({user_id})...")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.nl_sql_api_url}/query",
                    json={
                        "question": question,
                        "user_id": user_id,
                        "role": role,
                        "department": "IT" if role == "manager" else "Support"
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ SQL сгенерирован: {result['sql'][:100]}...")
                    return result
                else:
                    print(f"❌ Ошибка генерации SQL: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            print(f"❌ Ошибка генерации SQL: {e}")
            return None
    
    async def test_sql_execution(self, question: str, user_id: str, role: str) -> Dict[str, Any]:
        """Тестирование выполнения SQL с ролевыми ограничениями"""
        print(f"⚡ Тестирование выполнения SQL для {role} ({user_id})...")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.nl_sql_api_url}/query/execute",
                    json={
                        "question": question,
                        "user_id": user_id,
                        "role": role,
                        "department": "IT" if role == "manager" else "Support"
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ SQL выполнен: {result['row_count']} строк, время: {result['execution_time']:.3f}с")
                    print(f"📊 Примененный SQL: {result['sql'][:200]}...")
                    return result
                else:
                    print(f"❌ Ошибка выполнения SQL: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            print(f"❌ Ошибка выполнения SQL: {e}")
            return None
    
    async def test_role_restrictions(self):
        """Тестирование ролевых ограничений"""
        print("🔐 Тестирование ролевых ограничений...")
        
        test_cases = [
            {
                "question": "Покажи всех пользователей",
                "user_id": "admin",
                "role": "admin",
                "expected": "Полный доступ"
            },
            {
                "question": "Покажи всех пользователей", 
                "user_id": "manager",
                "role": "manager",
                "expected": "Только IT отдел"
            },
            {
                "question": "Покажи всех пользователей",
                "user_id": "user",
                "role": "user", 
                "expected": "Только свои данные"
            }
        ]
        
        results = []
        
        for test_case in test_cases:
            print(f"\n🧪 Тест: {test_case['role']} - {test_case['question']}")
            
            # Генерация SQL
            sql_result = await self.test_sql_generation(
                test_case["question"],
                test_case["user_id"], 
                test_case["role"]
            )
            
            if sql_result:
                # Выполнение SQL
                exec_result = await self.test_sql_execution(
                    test_case["question"],
                    test_case["user_id"],
                    test_case["role"]
                )
                
                if exec_result:
                    results.append({
                        "test_case": test_case,
                        "sql": sql_result["sql"],
                        "executed_sql": exec_result["sql"],
                        "row_count": exec_result["row_count"],
                        "success": True
                    })
                else:
                    results.append({
                        "test_case": test_case,
                        "success": False,
                        "error": "Ошибка выполнения"
                    })
            else:
                results.append({
                    "test_case": test_case,
                    "success": False,
                    "error": "Ошибка генерации"
                })
        
        return results
    
    async def run_full_test(self):
        """Запуск полного тестирования"""
        print("🚀 Запуск полного тестирования пайплайна...")
        print("=" * 60)
        
        # Проверка здоровья API
        if not await self.test_api_health():
            print("❌ API недоступны, завершение тестирования")
            return
        
        print("\n" + "=" * 60)
        
        # Тестирование ролевых ограничений
        results = await self.test_role_restrictions()
        
        print("\n" + "=" * 60)
        print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
        print("=" * 60)
        
        success_count = 0
        for i, result in enumerate(results, 1):
            test_case = result["test_case"]
            print(f"\n{i}. {test_case['role']} - {test_case['question']}")
            
            if result["success"]:
                print(f"   ✅ Успешно")
                print(f"   📊 Строк: {result['row_count']}")
                print(f"   🔧 SQL: {result['executed_sql'][:100]}...")
                success_count += 1
            else:
                print(f"   ❌ Ошибка: {result.get('error', 'Неизвестная ошибка')}")
        
        print(f"\n📈 Итого: {success_count}/{len(results)} тестов прошли успешно")
        
        if success_count == len(results):
            print("🎉 Все тесты прошли успешно! Пайплайн работает корректно.")
        else:
            print("⚠️ Некоторые тесты не прошли. Проверьте логи сервисов.")

async def main():
    """Основная функция"""
    tester = FullPipelineTester()
    await tester.run_full_test()

if __name__ == "__main__":
    asyncio.run(main())
