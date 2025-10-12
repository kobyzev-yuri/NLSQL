#!/usr/bin/env python3
"""
Быстрое сравнение Qwen3:8b и Qwen2.5-coder:1.5b для NL→SQL агента
"""

import sys
import json
from pathlib import Path

# Добавляем путь к модулям
sys.path.append(str(Path(__file__).parent / "src"))

from src.vanna.vanna_pgvector_native import DocStructureVannaNative

class QwenFixedContextVanna(DocStructureVannaNative):
    """
    Vanna AI с исправленной логикой получения контекста для Qwen моделей
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
            
            # Создаем промпт для Qwen моделей
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

def test_qwen_models():
    """Быстрое сравнение Qwen3:8b и Qwen2.5-coder:1.5b"""
    
    print("🚀 Быстрое сравнение Qwen моделей")
    print("=" * 50)
    
    # Тестовые вопросы (упрощенные)
    test_questions = [
        "Покажи всех пользователей",
        "Список отделов"
    ]
    
    # Конфигурация для Qwen3:8b
    qwen3_config = {
        'model': 'qwen3:8b',
        'database_url': 'postgresql://postgres:1234@localhost:5432/test_docstructure',
        'api_key': 'ollama',
        'base_url': 'http://localhost:11434/v1'
    }
    
    # Конфигурация для Qwen2.5-coder:1.5b
    qwen25_coder_config = {
        'model': 'qwen2.5-coder:1.5b',
        'database_url': 'postgresql://postgres:1234@localhost:5432/test_docstructure',
        'api_key': 'ollama',
        'base_url': 'http://localhost:11434/v1'
    }
    
    results = {
        'qwen3': {},
        'qwen25_coder': {}
    }
    
    try:
        # Тестируем Qwen3:8b
        print("\n🧠 Тестирование Qwen3:8b...")
        
        qwen3_vanna = QwenFixedContextVanna(qwen3_config)
        
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
        
        # Тестируем Qwen2.5-coder:1.5b
        print("\n💻 Тестирование Qwen2.5-coder:1.5b...")
        
        qwen25_coder_vanna = QwenFixedContextVanna(qwen25_coder_config)
        
        for question in test_questions:
            print(f"\n❓ Qwen2.5-coder: {question}")
            try:
                sql = qwen25_coder_vanna.generate_sql(question)
                results['qwen25_coder'][question] = {
                    'sql': sql,
                    'status': 'success'
                }
                print(f"💡 SQL: {sql}")
            except Exception as e:
                results['qwen25_coder'][question] = {
                    'sql': f"Ошибка: {e}",
                    'status': 'error'
                }
                print(f"❌ Ошибка: {e}")
        
        # Сохраняем результаты
        with open("qwen_models_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n📊 Результаты сохранены в qwen_models_results.json")
        
        # Статистика
        qwen3_success = sum(1 for r in results['qwen3'].values() if r["status"] == "success")
        qwen25_coder_success = sum(1 for r in results['qwen25_coder'].values() if r["status"] == "success")
        total = len(test_questions)
        
        print(f"\n📊 Статистика сравнения:")
        print(f"   Qwen3:8b:        {qwen3_success}/{total} ({qwen3_success/total:.2f})")
        print(f"   Qwen2.5-coder:   {qwen25_coder_success}/{total} ({qwen25_coder_success/total:.2f})")
        
        # Анализ качества
        print(f"\n🔍 Анализ качества:")
        for question in test_questions:
            qwen3_result = results['qwen3'][question]
            qwen25_coder_result = results['qwen25_coder'][question]
            
            print(f"\n❓ {question}")
            print(f"   Qwen3:8b:      {qwen3_result['status']} - {qwen3_result['sql'][:100]}...")
            print(f"   Qwen2.5-coder: {qwen25_coder_result['status']} - {qwen25_coder_result['sql'][:100]}...")
        
        # Рейтинг моделей
        print(f"\n🏆 Рейтинг Qwen моделей:")
        models = [
            ("Qwen3:8b", qwen3_success),
            ("Qwen2.5-coder:1.5b", qwen25_coder_success)
        ]
        models.sort(key=lambda x: x[1], reverse=True)
        
        for i, (model, score) in enumerate(models, 1):
            print(f"   {i}. {model}: {score}/{total} ({score/total:.2f})")
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")

if __name__ == "__main__":
    test_qwen_models()
