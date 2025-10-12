#!/usr/bin/env python3
"""
Сравнение GPT-4o, Ollama Llama 3 и Qwen3:8b для NL→SQL агента
"""

import sys
import json
from pathlib import Path

# Добавляем путь к модулям
sys.path.append(str(Path(__file__).parent / "src"))

from src.vanna.vanna_pgvector_native import DocStructureVannaNative

class Qwen3FixedContextVanna(DocStructureVannaNative):
    """
    Vanna AI с исправленной логикой получения контекста для Qwen3:8b
    """
    
    def __init__(self, config):
        # Настройки для Qwen3
        config['model'] = 'qwen3:8b'
        config['base_url'] = 'http://localhost:11434/v1'  # Ollama API
        config['api_key'] = 'ollama'
        
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
            
            # Создаем промпт для Qwen3
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

def test_qwen3_comparison():
    """Сравнение GPT-4o, Ollama Llama 3 и Qwen3:8b"""
    
    print("🚀 Сравнение GPT-4o, Ollama Llama 3 и Qwen3:8b")
    print("=" * 70)
    
    # Тестовые вопросы
    test_questions = [
        "Покажи всех пользователей",
        "Список отделов", 
        "Все клиенты",
        "Пользователи по отделам"
    ]
    
    # Конфигурация для GPT-4o
    gpt4_config = {
        'model': 'gpt-4o',
        'database_url': 'postgresql://postgres:1234@localhost:5432/test_docstructure',
        'api_key': 'sk-xF20r7G4tq9ezBMNKIjCPvva2io4S8FV',
        'base_url': 'https://api.proxyapi.ru/openai/v1'
    }
    
    # Конфигурация для Ollama Llama 3
    ollama_config = {
        'model': 'llama3:latest',
        'database_url': 'postgresql://postgres:1234@localhost:5432/test_docstructure',
        'api_key': 'ollama',
        'base_url': 'http://localhost:11434/v1'
    }
    
    # Конфигурация для Qwen3:8b
    qwen3_config = {
        'model': 'qwen3:8b',
        'database_url': 'postgresql://postgres:1234@localhost:5432/test_docstructure',
        'api_key': 'ollama',
        'base_url': 'http://localhost:11434/v1'
    }
    
    results = {
        'gpt4o': {},
        'ollama': {},
        'qwen3': {}
    }
    
    try:
        # Тестируем GPT-4o
        print("\n🤖 Тестирование GPT-4o...")
        from test_context_fix import FixedContextVanna
        
        gpt4_vanna = FixedContextVanna(gpt4_config)
        
        for question in test_questions:
            print(f"\n❓ GPT-4o: {question}")
            try:
                sql = gpt4_vanna.generate_sql(question)
                results['gpt4o'][question] = {
                    'sql': sql,
                    'status': 'success'
                }
                print(f"💡 SQL: {sql}")
            except Exception as e:
                results['gpt4o'][question] = {
                    'sql': f"Ошибка: {e}",
                    'status': 'error'
                }
                print(f"❌ Ошибка: {e}")
        
        # Тестируем Ollama Llama 3
        print("\n🦙 Тестирование Ollama Llama 3...")
        from test_ollama_comparison import OllamaFixedContextVanna
        
        ollama_vanna = OllamaFixedContextVanna(ollama_config)
        
        for question in test_questions:
            print(f"\n❓ Ollama: {question}")
            try:
                sql = ollama_vanna.generate_sql(question)
                results['ollama'][question] = {
                    'sql': sql,
                    'status': 'success'
                }
                print(f"💡 SQL: {sql}")
            except Exception as e:
                results['ollama'][question] = {
                    'sql': f"Ошибка: {e}",
                    'status': 'error'
                }
                print(f"❌ Ошибка: {e}")
        
        # Тестируем Qwen3:8b
        print("\n🧠 Тестирование Qwen3:8b...")
        
        qwen3_vanna = Qwen3FixedContextVanna(qwen3_config)
        
        for question in test_questions:
            print(f"\n❓ Qwen3: {question}")
            try:
                sql = qwen3_vanna.generate_sql(question)
                results['qwen3'][question] = {
                    'sql': sql,
                    'status': 'success'
                }
                print(f"💡 SQL: {sql}")
            except Exception as e:
                results['qwen3'][question] = {
                    'sql': f"Ошибка: {e}",
                    'status': 'error'
                }
                print(f"❌ Ошибка: {e}")
        
        # Сохраняем результаты
        with open("qwen3_comparison_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n📊 Результаты сохранены в qwen3_comparison_results.json")
        
        # Статистика
        gpt4_success = sum(1 for r in results['gpt4o'].values() if r["status"] == "success")
        ollama_success = sum(1 for r in results['ollama'].values() if r["status"] == "success")
        qwen3_success = sum(1 for r in results['qwen3'].values() if r["status"] == "success")
        total = len(test_questions)
        
        print(f"\n📊 Статистика сравнения:")
        print(f"   GPT-4o: {gpt4_success}/{total} ({gpt4_success/total:.2f})")
        print(f"   Ollama: {ollama_success}/{total} ({ollama_success/total:.2f})")
        print(f"   Qwen3:  {qwen3_success}/{total} ({qwen3_success/total:.2f})")
        
        # Анализ качества
        print(f"\n🔍 Анализ качества:")
        for question in test_questions:
            gpt4_result = results['gpt4o'][question]
            ollama_result = results['ollama'][question]
            qwen3_result = results['qwen3'][question]
            
            print(f"\n❓ {question}")
            print(f"   GPT-4o: {gpt4_result['status']} - {gpt4_result['sql'][:100]}...")
            print(f"   Ollama: {ollama_result['status']} - {ollama_result['sql'][:100]}...")
            print(f"   Qwen3:  {qwen3_result['status']} - {qwen3_result['sql'][:100]}...")
        
        # Рейтинг моделей
        print(f"\n🏆 Рейтинг моделей:")
        models = [
            ("GPT-4o", gpt4_success),
            ("Ollama Llama 3", ollama_success),
            ("Qwen3:8b", qwen3_success)
        ]
        models.sort(key=lambda x: x[1], reverse=True)
        
        for i, (model, score) in enumerate(models, 1):
            print(f"   {i}. {model}: {score}/{total} ({score/total:.2f})")
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")

if __name__ == "__main__":
    test_qwen3_comparison()
