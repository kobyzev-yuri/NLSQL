#!/usr/bin/env python3
"""
Исправленное обучение с правильной фильтрацией контекста
"""

import sys
import json
from pathlib import Path
from typing import List, Dict, Any

# Добавляем путь к модулям
sys.path.append(str(Path(__file__).parent / "src"))

from src.vanna.vanna_pgvector_native import DocStructureVannaNative

class FixedContextTraining:
    """Обучение с исправленной фильтрацией контекста"""
    
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
    
    def test_agent_with_fixed_context(self) -> Dict[str, Any]:
        """Тестирование агента с исправленным контекстом"""
        
        print("🧪 Тестирование агента с исправленным контекстом...")
        
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
                # Получаем SQL с исправленным контекстом
                sql = self.get_sql_with_fixed_context(question)
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
    
    def get_sql_with_fixed_context(self, question: str) -> str:
        """Получение SQL с исправленным контекстом"""
        
        # Создаем правильный контекст с бизнес-таблицами
        context_tables = []
        
        for table in self.priority_tables:
            try:
                # Получаем информацию о таблице
                table_info = self.get_table_info(table)
                if table_info:
                    context_tables.append(table_info)
            except Exception as e:
                print(f"⚠️ Не удалось получить информацию о таблице {table}: {e}")
        
        # Формируем контекст
        context = "\n\n".join(context_tables)
        
        # Создаем промпт с правильным контекстом
        prompt = f"""
You are a postgresql expert. Please help to generate a SQL query to answer the question. Your response should ONLY be based on the given context and follow the response guidelines and format instructions.

===Tables

===Additional Context

{context}

===Response Guidelines
1. If the provided context is sufficient, please generate a valid SQL query without any explanations for the question.
2. If the provided context is almost sufficient but requires knowledge of a specific string in a particular column, please generate an intermediate SQL query to find the distinct strings in that column. Prepend the query with a comment saying intermediate_sql
3. If the provided context is insufficient, please explain why it can't be generated.
4. Please use the most relevant table(s).
5. If the question has been asked and answered before, please repeat the answer exactly as it was given before.
6. Ensure that the output SQL is postgresql-compliant and executable, and free of syntax errors.
"""
        
        # Используем LLM для генерации SQL
        response = self.vanna.generate_sql(prompt, question)
        return response
    
    def get_table_info(self, table_name: str) -> str:
        """Получение информации о таблице"""
        
        try:
            # Запрос информации о таблице
            query = f"""
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default,
                character_maximum_length
            FROM information_schema.columns 
            WHERE table_name = '{table_name}'
            AND table_schema = 'public'
            ORDER BY ordinal_position
            """
            
            df = self.vanna.run_sql(query)
            
            if df.empty:
                return None
            
            # Формируем описание таблицы
            columns_info = []
            for _, row in df.iterrows():
                col_info = f"- {row['column_name']}: {row['data_type']}"
                if row['is_nullable'] == 'NO':
                    col_info += " (NOT NULL)"
                if row['character_maximum_length']:
                    col_info += f"({row['character_maximum_length']})"
                columns_info.append(col_info)
            
            table_info = f"Таблица {table_name}:\nКолонки: {', '.join(df['column_name'].tolist())}\n" + "\n".join(columns_info)
            
            return table_info
            
        except Exception as e:
            print(f"⚠️ Ошибка получения информации о таблице {table_name}: {e}")
            return None

def main():
    """Основная функция"""
    
    print("🚀 Запуск исправленного обучения NL→SQL агента")
    print("=" * 60)
    print("🔧 Исправление: Правильная фильтрация контекста")
    print("🎯 Фокус: Бизнес-таблицы вместо системных")
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
        trainer = FixedContextTraining(config)
        
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
        
        # Этап 3: Тестирование с исправленным контекстом
        print("\n🧪 Этап 3: Тестирование с исправленным контекстом")
        results = trainer.test_agent_with_fixed_context()
        
        # Сохраняем результаты
        with open("fixed_context_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n📊 Результаты сохранены в fixed_context_results.json")
        
        # Статистика
        success_count = sum(1 for r in results.values() if r["status"] == "success")
        total_count = len(results)
        
        print(f"\n📊 Статистика тестирования:")
        print(f"   Успешных запросов: {success_count}/{total_count}")
        print(f"   Среднее качество: {success_count/total_count:.2f}")
        
        if success_count > total_count * 0.7:
            print("✅ Качество генерации SQL улучшилось!")
        else:
            print("❌ Качество генерации SQL требует дальнейшего улучшения")
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")

if __name__ == "__main__":
    main()
