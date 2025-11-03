"""
Улучшенный пайплайн обучения Vanna AI агента
Использует данные от заказчика и улучшенную стратегию обучения
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Добавляем путь к модулям
sys.path.append(str(Path(__file__).parent.parent))

from vanna.vanna_pgvector_native import DocStructureVannaNative


class EnhancedTrainingPipeline:
    """Улучшенный пайплайн обучения с использованием данных заказчика"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.vanna = DocStructureVannaNative(
            config=config,
            model=config.get('model', 'ollama/llama3.1:8b')
        )
        
        # Приоритетные бизнес-таблицы (из анализа DocStructureSchema)
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
        
        # Исключаем технические таблицы
        self.excluded_tables = [
            "tbl_subd_admin",
            "tbl_subd_admin_log",
            "tbl_regex_patterns",
            "tbl_integration_files",
            "tbl_integration_log",
            "tbl_javascript_exception_handler",
            "tbl_notification",
            "tbl_activity_log"
        ]
    
    def extract_business_context_from_schema(self) -> Dict[str, Any]:
        """Извлекает бизнес-контекст из DocStructureSchema"""
        
        schema_path = Path(os.getenv("DOCSTRUCTURE_DIR", "data/DocStructureSchema"))
        business_context = {
            "system_purpose": "Система управления поручениями и платежами",
            "main_entities": {
                "users": "Пользователи системы (сотрудники)",
                "clients": "Клиенты/бизнес-единицы",
                "assignments": "Поручения клиентам",
                "payments": "Платежи от клиентов"
            },
            "business_flows": [
                "Создание поручения → Назначение клиенту → Выполнение → Платеж",
                "Регистрация клиента → Создание личного кабинета → Работа с поручениями"
            ],
            "priority_tables": self.priority_tables,
            "excluded_tables": self.excluded_tables
        }
        
        return business_context
    
    def train_on_filtered_schema(self) -> bool:
        """Обучение только на приоритетных таблицах"""
        
        try:
            print("🔍 Обучение на фильтрованной схеме...")
            
            # Создаем фильтрованный запрос схемы
            tables_list = "', '".join(self.priority_tables)
            schema_query = f"""
            SELECT 
                table_name,
                column_name,
                data_type,
                is_nullable,
                column_default,
                character_maximum_length
            FROM information_schema.columns 
            WHERE table_schema = 'public'
            AND table_name IN ('{tables_list}')
            ORDER BY table_name, ordinal_position
            """
            
            print(f"📊 Обучаем на {len(self.priority_tables)} приоритетных таблицах")
            print(f"🚫 Исключаем {len(self.excluded_tables)} технических таблиц")
            
            df_schema = self.vanna.run_sql(schema_query)
            plan = self.vanna.get_training_plan_generic(df_schema)
            self.vanna.train(plan=plan)
            
            print("✅ Обучение на схеме завершено")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка обучения на схеме: {e}")
            return False
    
    def train_on_enhanced_examples(self) -> bool:
        """Обучение на улучшенных SQL примерах"""
        
        try:
            print("📚 Обучение на улучшенных примерах...")
            
            # Загружаем улучшенные примеры
            examples_file = Path("training_data/enhanced_sql_examples.json")
            if not examples_file.exists():
                print(f"❌ Файл {examples_file} не найден")
                return False
            
            with open(examples_file, 'r', encoding='utf-8') as f:
                examples = json.load(f)
            
            print(f"📖 Загружено {len(examples)} улучшенных примеров")
            
            # Группируем примеры по сложности
            complexity_groups = {}
            for example in examples:
                complexity = example.get('complexity', 1)
                if complexity not in complexity_groups:
                    complexity_groups[complexity] = []
                complexity_groups[complexity].append(example)
            
            # Обучаем по уровням сложности
            for complexity in sorted(complexity_groups.keys()):
                group_examples = complexity_groups[complexity]
                print(f"🎯 Обучение на уровне сложности {complexity} ({len(group_examples)} примеров)")
                
                for example in group_examples:
                    try:
                        self.vanna.train(
                            question=example['question'],
                            sql=example['sql']
                        )
                    except Exception as e:
                        print(f"⚠️ Ошибка обучения примера: {example['question'][:50]}... - {e}")
            
            print("✅ Обучение на примерах завершено")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка обучения на примерах: {e}")
            return False
    
    def train_on_business_context(self) -> bool:
        """Обучение на бизнес-контексте"""
        
        try:
            print("🏢 Обучение на бизнес-контексте...")
            
            # Создаем контекстные примеры на основе бизнес-процессов
            business_processes = [
                {
                    "process": "Управление поручениями",
                    "examples": [
                        "Создать новое поручение клиенту",
                        "Показать все поручения в работе",
                        "Найти поручения по конкретному клиенту",
                        "Статистика выполнения поручений"
                    ]
                },
                {
                    "process": "Работа с платежами",
                    "examples": [
                        "Показать все платежи за месяц",
                        "Найти платежи конкретного клиента",
                        "Сумма платежей по клиентам",
                        "Платежи по периодам"
                    ]
                },
                {
                    "process": "Управление пользователями",
                    "examples": [
                        "Показать всех пользователей",
                        "Пользователи по отделам",
                        "Пользователи с ролями",
                        "Статистика по пользователям"
                    ]
                }
            ]
            
            # Обучаем на контекстных примерах
            for process in business_processes:
                print(f"📋 Обучаем на процессе: {process['process']}")
                
                for example in process['examples']:
                    try:
                        # Создаем SQL для контекстного примера
                        context_sql = self._generate_context_sql(example, process['process'])
                        if context_sql:
                            self.vanna.train(
                                question=example,
                                sql=context_sql
                            )
                    except Exception as e:
                        print(f"⚠️ Ошибка контекстного обучения: {example} - {e}")
            
            print("✅ Обучение на бизнес-контексте завершено")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка обучения на бизнес-контексте: {e}")
            return False
    
    def _generate_context_sql(self, question: str, process: str) -> str:
        """Генерирует SQL для контекстного примера"""
        
        # Простая логика сопоставления вопросов с SQL
        if "пользователей" in question.lower():
            return "SELECT id, login, email, surname, firstname FROM equsers WHERE deleted = false"
        elif "поручения" in question.lower():
            return "SELECT assignment_number, assignment_date, amount FROM tbl_principal_assignment WHERE deleted = false"
        elif "платежи" in question.lower():
            return "SELECT payment_number, payment_date, amount FROM tbl_incoming_payments WHERE deleted = false"
        elif "отделам" in question.lower():
            return "SELECT u.login, u.email, d.departmentname FROM equsers u LEFT JOIN eq_departments d ON u.department = d.id WHERE u.deleted = false"
        else:
            return None
    
    def train_on_tz_examples(self) -> bool:
        """Обучение на примерах из ТЗ"""
        
        try:
            print("📋 Обучение на примерах из ТЗ...")
            
            # Примеры из ТЗ (адаптированные под нашу схему)
            tz_examples = [
                {
                    "question": "Покажи заказы старше 3 дней из категории А больше 1 млн рублей",
                    "sql": """
                    SELECT pa.assignment_number, pa.assignment_date, pa.amount, 
                           bu.business_unit_name, bu.category
                    FROM tbl_principal_assignment pa
                    JOIN tbl_business_unit bu ON pa.business_unit_id = bu.id
                    WHERE pa.assignment_date < CURRENT_DATE - INTERVAL '3 days'
                    AND bu.category = 'A'
                    AND pa.amount > 1000000
                    AND pa.deleted = false
                    ORDER BY pa.amount DESC
                    """
                },
                {
                    "question": "Из чего сделан продукт #876?",
                    "sql": """
                    SELECT product_name, material, description
                    FROM tbl_products 
                    WHERE id = 876
                    """
                },
                {
                    "question": "Когда будет совещание по маркетингу?",
                    "sql": """
                    SELECT meeting_date, meeting_time, description
                    FROM tbl_meetings 
                    WHERE topic ILIKE '%маркетинг%'
                    AND meeting_date >= CURRENT_DATE
                    ORDER BY meeting_date ASC
                    LIMIT 1
                    """
                }
            ]
            
            for example in tz_examples:
                try:
                    self.vanna.train(
                        question=example['question'],
                        sql=example['sql']
                    )
                except Exception as e:
                    print(f"⚠️ Ошибка обучения примера из ТЗ: {example['question']} - {e}")
            
            print("✅ Обучение на примерах из ТЗ завершено")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка обучения на примерах из ТЗ: {e}")
            return False
    
    def run_enhanced_training(self) -> bool:
        """Запуск улучшенного обучения"""
        
        print("🚀 Запуск улучшенного обучения Vanna AI агента")
        print("=" * 60)
        
        # 1. Анализ и приоритизация
        print("📊 Этап 1: Анализ и приоритизация данных")
        business_context = self.extract_business_context_from_schema()
        print(f"✅ Приоритетных таблиц: {len(business_context['priority_tables'])}")
        print(f"✅ Исключенных таблиц: {len(business_context['excluded_tables'])}")
        
        # 2. Фильтрованное обучение на схеме
        print("\n🔍 Этап 2: Фильтрованное обучение на схеме")
        if not self.train_on_filtered_schema():
            return False
        
        # 3. Обучение на улучшенных примерах
        print("\n📚 Этап 3: Обучение на улучшенных примерах")
        if not self.train_on_enhanced_examples():
            return False
        
        # 4. Обучение на бизнес-контексте
        print("\n🏢 Этап 4: Обучение на бизнес-контексте")
        if not self.train_on_business_context():
            return False
        
        # 5. Обучение на примерах из ТЗ
        print("\n📋 Этап 5: Обучение на примерах из ТЗ")
        if not self.train_on_tz_examples():
            return False
        
        print("\n🎉 Улучшенное обучение завершено успешно!")
        return True
    
    def test_enhanced_agent(self, test_questions: List[str]) -> Dict[str, Any]:
        """Тестирование улучшенного агента"""
        
        print("🧪 Тестирование улучшенного агента")
        print("=" * 40)
        
        results = {}
        
        for question in test_questions:
            try:
                print(f"❓ Вопрос: {question}")
                sql = self.vanna.generate_sql(question)
                print(f"💡 SQL: {sql}")
                results[question] = {
                    "sql": sql,
                    "status": "success"
                }
            except Exception as e:
                print(f"❌ Ошибка: {e}")
                results[question] = {
                    "sql": None,
                    "status": "error",
                    "error": str(e)
                }
            print("-" * 40)
        
        return results


def main():
    """Основная функция"""
    
    # Конфигурация
    config = {
        'model': 'ollama/llama3.1:8b',
        'database_url': 'postgresql://postgres:1234@localhost:5432/test_docstructure'
    }
    
    # Создаем пайплайн
    pipeline = EnhancedTrainingPipeline(config)
    
    # Запускаем улучшенное обучение
    if pipeline.run_enhanced_training():
        print("\n🎯 Обучение завершено успешно!")
        
        # Тестируем агента
        test_questions = [
            "Покажи всех пользователей",
            "Сколько клиентов в каждом регионе?",
            "Поручения за последний месяц",
            "Топ-10 клиентов по сумме поручений"
        ]
        
        results = pipeline.test_enhanced_agent(test_questions)
        
        # Сохраняем результаты
        with open('enhanced_training_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print("📊 Результаты сохранены в enhanced_training_results.json")
    else:
        print("❌ Обучение завершилось с ошибками")
        sys.exit(1)


if __name__ == "__main__":
    main()
