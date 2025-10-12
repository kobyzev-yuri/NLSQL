#!/usr/bin/env python3
"""
Тестирование исправления логики получения контекста
"""

import sys
import json
from pathlib import Path

# Добавляем путь к модулям
sys.path.append(str(Path(__file__).parent / "src"))

from src.vanna.vanna_pgvector_native import DocStructureVannaNative

class FixedContextVanna(DocStructureVannaNative):
    """
    Vanna AI с исправленной логикой получения контекста
    """
    
    def __init__(self, config):
        super().__init__(config)
        
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
    
    def get_related_ddl(self, question: str, **kwargs):
        """
        Исправленный метод получения DDL с приоритетом бизнес-таблиц
        """
        try:
            ddl_list = []
            
            for table in self.priority_tables:
                try:
                    # Получаем DDL для таблицы
                    ddl_query = f"""
                    SELECT 
                        table_name,
                        column_name,
                        data_type,
                        is_nullable,
                        column_default,
                        character_maximum_length
                    FROM information_schema.columns 
                    WHERE table_name = '{table}'
                    AND table_schema = 'public'
                    ORDER BY ordinal_position
                    """
                    
                    df = self.run_sql(ddl_query)
                    
                    if not df.empty:
                        # Формируем DDL для таблицы
                        table_ddl = f"Таблица {table}:\n"
                        table_ddl += f"Колонки: {', '.join(df['column_name'].tolist())}\n"
                        
                        for _, row in df.iterrows():
                            col_name = row['column_name']
                            data_type = row['data_type']
                            is_nullable = row['is_nullable']
                            
                            col_info = f"- {col_name}: {data_type}"
                            if is_nullable == 'NO':
                                col_info += " (NOT NULL)"
                            if row['character_maximum_length']:
                                col_info += f"({row['character_maximum_length']})"
                            table_ddl += col_info + "\n"
                        
                        ddl_list.append(table_ddl)
                        
                except Exception as e:
                    print(f"⚠️ Не удалось получить DDL для таблицы {table}: {e}")
                    continue
            
            print(f"✅ Получено {len(ddl_list)} DDL для приоритетных таблиц")
            return ddl_list
            
        except Exception as e:
            print(f"❌ Ошибка получения DDL: {e}")
            return []
    
    def generate_sql(self, question: str) -> str:
        """
        Исправленная генерация SQL с правильным контекстом
        """
        try:
            # Получаем связанные данные с исправленной логикой
            ddl_list = self.get_related_ddl(question)
            docs_list = self.get_related_documentation(question)
            qa_list = self.get_similar_question_sql(question)
            
            # Формируем контекст
            context_parts = []
            
            if ddl_list:
                context_parts.append("\n".join(ddl_list))
            
            if docs_list:
                context_parts.append("\n".join(docs_list))
            
            if qa_list:
                context_parts.append("\n".join(qa_list))
            
            context = "\n\n".join(context_parts)
            
            # Создаем промпт
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
            
            # Используем правильный метод Vanna AI для генерации SQL
            return super().generate_sql(question)
            
        except Exception as e:
            print(f"❌ Ошибка генерации SQL: {e}")
            raise

def test_fixed_context():
    """Тестирование исправленной логики получения контекста"""
    
    print("🚀 Тестирование исправленной логики получения контекста")
    print("=" * 60)
    
    # Конфигурация для Ollama Llama 3.1
    config = {
        'model': 'llama3.1:8b',
        'database_url': 'postgresql://postgres:1234@localhost:5432/test_docstructure',
        'api_key': 'ollama',  # Не используется для Ollama
        'base_url': 'http://localhost:11434'  # Локальный Ollama
    }
    
    try:
        # Создаем исправленный клиент
        vanna = FixedContextVanna(config)
        
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
