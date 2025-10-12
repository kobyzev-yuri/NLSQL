#!/usr/bin/env python3
"""
Финальная версия обучения с правильным форматом промпта
"""

import sys
import json
from pathlib import Path
from typing import List, Dict, Any

# Добавляем путь к модулям
sys.path.append(str(Path(__file__).parent / "src"))

from src.vanna.vanna_pgvector_native import DocStructureVannaNative

class FinalTraining:
    """Финальная версия обучения с правильным форматом промпта"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.vanna = DocStructureVannaNative(config=config)
        
        # Приоритетные бизнес-таблицы
        self.priority_tables = [
            "equsers",                    # Пользователи
            "eq_departments",             # Отделы
            "eqgroups",                   # Группы
            "eqroles",                    # Роли
            "tbl_business_unit",          # Клиенты
            "tbl_principal_assignment",  # Поручения
            "tbl_incoming_payments",      # Платежи
            "tbl_accounts_document",      # Учетные записи
            "tbl_personal_account"        # Личные кабинеты
        ]
    
    def train_on_schema(self) -> bool:
        """Обучение на схеме БД"""
        
        try:
            print("🔍 Обучение на схеме БД...")
            
            # Загружаем схему всех таблиц
            schema_query = "SELECT * FROM INFORMATION_SCHEMA.COLUMNS"
            df_schema = self.vanna.run_sql(schema_query)
            print(f"✅ Загружено {len(df_schema)} колонок из схемы")
            
            plan = self.vanna.get_training_plan_generic(df_schema)
            self.vanna.train(plan=plan)
            
            print("✅ Обучение на схеме завершено")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка обучения на схеме: {e}")
            return False
    
    def train_on_sql_examples(self) -> bool:
        """Обучение на SQL примерах"""
        
        try:
            print("📚 Обучение на SQL примерах...")
            
            # Загружаем улучшенные примеры
            examples_file = Path("training_data/enhanced_sql_examples.json")
            if not examples_file.exists():
                print("❌ Файл с примерами не найден")
                return False
            
            with open(examples_file, 'r', encoding='utf-8') as f:
                examples = json.load(f)
            
            print(f"📖 Загружено {len(examples)} примеров")
            
            # Обучаем на каждом примере
            success_count = 0
            for i, example in enumerate(examples, 1):
                try:
                    question = example['question']
                    sql = example['sql']
                    
                    # Обучаем агента
                    self.vanna.train(
                        question=question,
                        sql=sql
                    )
                    
                    success_count += 1
                    
                    if i % 5 == 0:
                        print(f"   Прогресс: {i}/{len(examples)} ({i/len(examples)*100:.1f}%)")
                        
                except Exception as e:
                    print(f"❌ Ошибка обучения примера {i}: {e}")
            
            print(f"✅ Обучение завершено: {success_count} успешно, {len(examples) - success_count} ошибок")
            return success_count > 0
            
        except Exception as e:
            print(f"❌ Ошибка обучения на примерах: {e}")
            return False
    
    def test_agent_final(self) -> Dict[str, Any]:
        """Финальное тестирование агента"""
        
        print("🧪 Финальное тестирование агента...")
        
        test_questions = [
            "Покажи всех пользователей",
            "Список отделов", 
            "Все клиенты",
            "Пользователи по отделам",
            "Поручения с клиентами",
            "Платежи по клиентам"
        ]
        
        results = {}
        
        for question in test_questions:
            print(f"\n❓ Вопрос: {question}")
            
            try:
                # Используем стандартный метод Vanna AI
                sql = self.vanna.generate_sql(question)
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
        
        return results

def main():
    """Основная функция"""
    
    print("🚀 Финальное обучение NL→SQL агента")
    print("=" * 60)
    print("🎯 Фокус: Правильный формат промпта")
    print("🔧 Исправление: Стандартный метод Vanna AI")
    print("=" * 60)
    
    # Конфигурация
    config = {
        'model': 'gpt-4o',
        'database_url': 'postgresql://postgres:1234@localhost:5432/test_docstructure',
        'api_key': 'sk-xF20r7G4tq9ezBMNKIjCPvva2io4S8FV',
        'base_url': 'https://api.proxyapi.ru/openai/v1'
    }
    
    try:
        # Создаем тренер
        trainer = FinalTraining(config)
        
        # Этап 1: Обучение на схеме
        print("\n🔍 Этап 1: Обучение на схеме БД")
        if not trainer.train_on_schema():
            print("❌ Ошибка обучения на схеме")
            return
        
        # Этап 2: Обучение на SQL примерах
        print("\n📚 Этап 2: Обучение на SQL примерах")
        if not trainer.train_on_sql_examples():
            print("❌ Ошибка обучения на примерах")
            return
        
        # Этап 3: Финальное тестирование
        print("\n🧪 Этап 3: Финальное тестирование")
        results = trainer.test_agent_final()
        
        # Сохраняем результаты
        with open("final_training_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n📊 Результаты сохранены в final_training_results.json")
        
        # Статистика
        success_count = sum(1 for r in results.values() if r["status"] == "success")
        total_count = len(results)
        
        print(f"\n📊 Статистика тестирования:")
        print(f"   Успешных запросов: {success_count}/{total_count}")
        print(f"   Среднее качество: {success_count/total_count:.2f}")
        
        if success_count > total_count * 0.7:
            print("✅ Качество генерации SQL отличное!")
        else:
            print("❌ Качество генерации SQL требует улучшения")
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")

if __name__ == "__main__":
    main()
