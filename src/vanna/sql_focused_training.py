"""
Фокус на обучении SQL с последующим конвертированием в план
Упрощенный подход без усложнения датасета
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

# Добавляем путь к модулям
sys.path.append(str(Path(__file__).parent.parent))

from .vanna_pgvector_native import DocStructureVannaNative


class SQLFocusedTraining:
    """Обучение агента на SQL с фокусом на качество генерации"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.vanna = DocStructureVannaNative(config=config)
        
        # Приоритетные таблицы для обучения
        self.priority_tables = [
            "equsers",                    # Пользователи
            "eq_departments",            # Отделы
            "eqgroups",                  # Группы
            "eqroles",                   # Роли
            "tbl_business_unit",         # Клиенты
            "tbl_principal_assignment", # Поручения
            "tbl_incoming_payments",     # Платежи
            "tbl_accounts_document",     # Учетные записи
            "tbl_personal_account"       # Личные кабинеты
        ]
    
    def train_on_filtered_schema(self) -> bool:
        """Обучение на схеме БД (правильный способ)"""
        
        try:
            print("🔍 Обучение на схеме БД...")
            
            # Правильный способ - все колонки из INFORMATION_SCHEMA.COLUMNS
            schema_query = "SELECT * FROM INFORMATION_SCHEMA.COLUMNS"
            
            print("📊 Загружаем схему всех таблиц...")
            
            df_schema = self.vanna.run_sql(schema_query)
            print(f"✅ Загружено {len(df_schema)} колонок из схемы")
            
            plan = self.vanna.get_training_plan_generic(df_schema)
            self.vanna.train(plan=plan)
            
            print("✅ Обучение на схеме завершено")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка обучения на схеме: {e}")
            return False
    
    def train_on_enhanced_sql_examples(self) -> bool:
        """Обучение на улучшенных SQL примерах"""
        
        try:
            print("📚 Обучение на улучшенных SQL примерах...")
            
            # Загружаем улучшенные примеры
            examples_file = Path("training_data/enhanced_sql_examples.json")
            if not examples_file.exists():
                print(f"❌ Файл {examples_file} не найден")
                return False
            
            with open(examples_file, 'r', encoding='utf-8') as f:
                examples = json.load(f)
            
            print(f"📖 Загружено {len(examples)} улучшенных примеров")
            
            # Статистика по категориям
            categories = {}
            complexities = {}
            
            for example in examples:
                category = example.get('category', 'Неизвестно')
                complexity = example.get('complexity', 1)
                
                categories[category] = categories.get(category, 0) + 1
                complexities[complexity] = complexities.get(complexity, 0) + 1
            
            print("📊 Статистика примеров:")
            print(f"   Категории: {dict(categories)}")
            print(f"   Сложность: {dict(complexities)}")
            
            # Обучаем на всех примерах
            success_count = 0
            error_count = 0
            
            for i, example in enumerate(examples, 1):
                try:
                    self.vanna.train(
                        question=example['question'],
                        sql=example['sql']
                    )
                    success_count += 1
                    
                    if i % 5 == 0:  # Прогресс каждые 5 примеров
                        print(f"   Прогресс: {i}/{len(examples)} ({i/len(examples)*100:.1f}%)")
                        
                except Exception as e:
                    error_count += 1
                    print(f"⚠️ Ошибка примера {i}: {example['question'][:50]}... - {e}")
            
            print(f"✅ Обучение завершено: {success_count} успешно, {error_count} ошибок")
            return success_count > 0
            
        except Exception as e:
            print(f"❌ Ошибка обучения на примерах: {e}")
            return False
    
    def train_on_business_context(self) -> bool:
        """Обучение на бизнес-контексте (дополнительные примеры)"""
        
        try:
            print("🏢 Обучение на бизнес-контексте...")
            
            # Дополнительные контекстные примеры
            context_examples = [
                {
                    "question": "Покажи активных пользователей системы",
                    "sql": "SELECT id, login, email, surname, firstname FROM equsers WHERE deleted = false AND active = true"
                },
                {
                    "question": "Найди клиентов из Москвы",
                    "sql": "SELECT business_unit_name, inn, phone, email FROM tbl_business_unit WHERE region = 'Москва' AND deleted = false"
                },
                {
                    "question": "Покажи поручения в работе",
                    "sql": "SELECT assignment_number, assignment_date, amount, status FROM tbl_principal_assignment WHERE status = 'В работе' AND deleted = false"
                },
                {
                    "question": "Платежи за сегодня",
                    "sql": "SELECT payment_number, payment_date, amount FROM tbl_incoming_payments WHERE payment_date = CURRENT_DATE AND deleted = false"
                }
            ]
            
            for example in context_examples:
                try:
                    self.vanna.train(
                        question=example['question'],
                        sql=example['sql']
                    )
                except Exception as e:
                    print(f"⚠️ Ошибка контекстного примера: {example['question']} - {e}")
            
            print("✅ Обучение на бизнес-контексте завершено")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка обучения на бизнес-контексте: {e}")
            return False
    
    def run_sql_training(self) -> bool:
        """Запуск обучения с фокусом на SQL"""
        
        print("🚀 Запуск обучения с фокусом на SQL")
        print("=" * 50)
        
        # 1. Обучение на фильтрованной схеме
        print("🔍 Этап 1: Обучение на схеме БД")
        if not self.train_on_filtered_schema():
            print("⚠️ Продолжаем без схемы...")
        
        # 2. Обучение на улучшенных SQL примерах
        print("\n📚 Этап 2: Обучение на SQL примерах")
        if not self.train_on_enhanced_sql_examples():
            return False
        
        # 3. Дополнительное обучение на контексте
        print("\n🏢 Этап 3: Обучение на бизнес-контексте")
        if not self.train_on_business_context():
            print("⚠️ Продолжаем без контекста...")
        
        print("\n🎉 Обучение завершено успешно!")
        return True
    
    def test_sql_generation(self, test_questions: List[str]) -> Dict[str, Any]:
        """Тестирование генерации SQL"""
        
        print("🧪 Тестирование генерации SQL")
        print("=" * 40)
        
        results = {}
        
        for question in test_questions:
            try:
                print(f"❓ Вопрос: {question}")
                sql = self.vanna.generate_sql(question)
                print(f"💡 SQL: {sql}")
                
                # Проверяем качество SQL
                quality_score = self._evaluate_sql_quality(sql, question)
                
                results[question] = {
                    "sql": sql,
                    "quality_score": quality_score,
                    "status": "success"
                }
                
            except Exception as e:
                print(f"❌ Ошибка: {e}")
                results[question] = {
                    "sql": None,
                    "quality_score": 0,
                    "status": "error",
                    "error": str(e)
                }
            
            print("-" * 40)
        
        return results
    
    def _evaluate_sql_quality(self, sql: str, question: str) -> float:
        """Оценивает качество сгенерированного SQL"""
        
        score = 0.0
        
        # Базовые проверки
        if sql and sql.strip():
            score += 0.3
            
        if sql.upper().startswith('SELECT'):
            score += 0.2
            
        if 'WHERE' in sql.upper():
            score += 0.2
            
        if 'JOIN' in sql.upper():
            score += 0.2
            
        if 'GROUP BY' in sql.upper() or 'ORDER BY' in sql.upper():
            score += 0.1
            
        return min(score, 1.0)
    
    def save_training_results(self, results: Dict[str, Any], filename: str = "sql_training_results.json"):
        """Сохраняет результаты обучения"""
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"📊 Результаты сохранены в {filename}")
        except Exception as e:
            print(f"❌ Ошибка сохранения результатов: {e}")


def main():
    """Основная функция"""
    
    # Конфигурация
    config = {
        'model': 'ollama/llama3.1:8b',
        'database_url': 'postgresql://postgres:1234@localhost:5432/test_docstructure'
    }
    
    # Создаем тренер
    trainer = SQLFocusedTraining(config)
    
    # Запускаем обучение
    if trainer.run_sql_training():
        print("\n🎯 Обучение завершено успешно!")
        
        # Тестируем агента
        test_questions = [
            "Покажи всех пользователей",
            "Сколько клиентов в каждом регионе?",
            "Поручения за последний месяц",
            "Топ-10 клиентов по сумме поручений",
            "Пользователи отдела Продажи",
            "Платежи больше 1 млн рублей"
        ]
        
        results = trainer.test_sql_generation(test_questions)
        
        # Сохраняем результаты
        trainer.save_training_results(results)
        
        # Выводим статистику
        success_count = sum(1 for r in results.values() if r['status'] == 'success')
        avg_quality = sum(r['quality_score'] for r in results.values()) / len(results)
        
        print(f"\n📊 Статистика тестирования:")
        print(f"   Успешных запросов: {success_count}/{len(results)}")
        print(f"   Среднее качество: {avg_quality:.2f}")
        
    else:
        print("❌ Обучение завершилось с ошибками")
        sys.exit(1)


if __name__ == "__main__":
    main()
