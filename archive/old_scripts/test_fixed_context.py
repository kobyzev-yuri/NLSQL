#!/usr/bin/env python3
"""
Тестирование исправленной логики получения контекста
"""

import sys
import json
from pathlib import Path

# Добавляем путь к модулям
sys.path.append(str(Path(__file__).parent / "src"))

from src.vanna.vanna_fixed_context import DocStructureVannaFixed

def test_fixed_context():
    """Тестирование исправленной логики получения контекста"""
    
    print("🚀 Тестирование исправленной логики получения контекста")
    print("=" * 60)
    
    # Конфигурация
    config = {
        'model': 'gpt-4o',
        'database_url': 'postgresql://postgres:1234@localhost:5432/test_docstructure',
        'api_key': 'sk-xF20r7G4tq9ezBMNKIjCPvva2io4S8FV',
        'base_url': 'https://api.proxyapi.ru/openai/v1'
    }
    
    try:
        # Создаем исправленный клиент
        vanna = DocStructureVannaFixed(config)
        
        # Тестируем получение контекста
        print("\n🔍 Тестирование получения контекста...")
        
        test_question = "Покажи всех пользователей"
        
        # Получаем связанные DDL
        ddl_list = vanna.get_related_ddl(test_question)
        print(f"✅ Получено {len(ddl_list)} DDL для приоритетных таблиц")
        
        # Показываем первые несколько DDL
        for i, ddl in enumerate(ddl_list[:3], 1):
            print(f"\n📋 DDL {i}:")
            print(ddl[:200] + "..." if len(ddl) > 200 else ddl)
        
        # Тестируем генерацию SQL
        print(f"\n🧪 Тестирование генерации SQL для: '{test_question}'")
        
        try:
            sql = vanna.generate_sql(test_question)
            print(f"💡 SQL: {sql}")
            
            # Проверяем, содержит ли SQL бизнес-таблицы
            business_tables = ["equsers", "tbl_business_unit", "eq_departments"]
            found_tables = [table for table in business_tables if table in sql.lower()]
            
            if found_tables:
                print(f"✅ SQL содержит бизнес-таблицы: {found_tables}")
            else:
                print("❌ SQL не содержит бизнес-таблицы")
                
        except Exception as e:
            print(f"❌ Ошибка генерации SQL: {e}")
        
        # Тестируем несколько вопросов
        test_questions = [
            "Покажи всех пользователей",
            "Список отделов",
            "Все клиенты",
            "Пользователи по отделам"
        ]
        
        results = {}
        
        for question in test_questions:
            print(f"\n❓ Вопрос: {question}")
            
            try:
                sql = vanna.generate_sql(question)
                results[question] = {
                    "sql": sql,
                    "status": "success"
                }
                print(f"💡 SQL: {sql}")
                
            except Exception as e:
                results[question] = {
                    "sql": f"Ошибка: {e}",
                    "status": "error"
                }
                print(f"❌ Ошибка: {e}")
        
        # Сохраняем результаты
        with open("fixed_context_test_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n📊 Результаты сохранены в fixed_context_test_results.json")
        
        # Статистика
        success_count = sum(1 for r in results.values() if r["status"] == "success")
        total_count = len(results)
        
        print(f"\n📊 Статистика тестирования:")
        print(f"   Успешных запросов: {success_count}/{total_count}")
        print(f"   Среднее качество: {success_count/total_count:.2f}")
        
        if success_count > total_count * 0.7:
            print("✅ Исправленная логика работает отлично!")
        else:
            print("❌ Исправленная логика требует дальнейшей доработки")
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")

if __name__ == "__main__":
    test_fixed_context()
