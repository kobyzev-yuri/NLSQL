#!/usr/bin/env python3
"""
Улучшенный скрипт обучения агента с фильтрацией по бизнес-таблицам
"""

import sys
import os
import json
import pandas as pd
from pathlib import Path

# Добавляем путь к модулям
sys.path.append('src')

from vanna.vanna_pgvector_native import DocStructureVannaNative

# Whitelist бизнес-таблиц для обучения агента
BUSINESS_TABLES_WHITELIST = [
    # Пользователи и права
    "equsers",
    "eq_departments", 
    "eqgroups",
    "eqroles",
    
    # Бизнес-данные
    "tbl_business_unit",
    "tbl_principal_assignment", 
    "tbl_incoming_payments",
    "tbl_accounts_document",
    "tbl_personal_account",
    
    # Справочники
    "tbl_currencies",
    "tbl_countries",
    "tbl_swift",
    "tbl_bik",
    "tbl_contract_types",
    "tbl_assignment_types",
    "tbl_payment_statuses"
]

class FilteredVannaTrainer:
    def __init__(self):
        self.vanna = DocStructureVannaNative()
        self.training_stats = {
            'ddl_items': 0,
            'documentation_items': 0,
            'sql_examples': 0,
            'schema_items': 0,
            'filtered_tables': 0
        }
    
    def train_on_ddl(self):
        """Обучение на DDL с фильтрацией по бизнес-таблицам"""
        try:
            print("📋 Обучение на DDL с фильтрацией...")
            
            with open('training_data/ddl_statements.sql', 'r', encoding='utf-8') as f:
                ddl_content = f.read()
            
            # Фильтруем DDL по бизнес-таблицам
            filtered_ddl = self._filter_ddl_by_business_tables(ddl_content)
            
            if filtered_ddl:
                self.vanna.add_ddl(filtered_ddl)
                self.training_stats['ddl_items'] = 1
                print(f"✅ DDL обучение завершено (отфильтровано)")
            else:
                print("⚠️ Не найдено DDL для бизнес-таблиц")
                
        except Exception as e:
            print(f"❌ Ошибка обучения на DDL: {e}")
    
    def train_on_documentation(self):
        """Обучение на документации"""
        try:
            print("📚 Обучение на документации...")
            
            with open('training_data/documentation.txt', 'r', encoding='utf-8') as f:
                doc_content = f.read()
            
            self.vanna.add_documentation(doc_content)
            self.training_stats['documentation_items'] = 1
            print("✅ Обучение на документации завершено")
            
        except Exception as e:
            print(f"❌ Ошибка обучения на документации: {e}")
    
    def train_on_sql_examples(self):
        """Обучение на SQL примерах"""
        try:
            print("💾 Обучение на SQL примерах...")
            
            with open('training_data/sql_examples.json', 'r', encoding='utf-8') as f:
                examples = json.load(f)
            
            for example in examples:
                self.vanna.add_question_sql(example['question'], example['sql'])
            
            self.training_stats['sql_examples'] = len(examples)
            print(f"✅ Обучение на {len(examples)} SQL примерах завершено")
            
        except Exception as e:
            print(f"❌ Ошибка обучения на SQL примерах: {e}")
    
    def train_on_generated_qa(self):
        """Обучение на сгенерированных Q/A парах"""
        try:
            print("🤖 Обучение на сгенерированных Q/A парах...")
            
            with open('generated_qa_pairs.json', 'r', encoding='utf-8') as f:
                qa_pairs = json.load(f)
            
            for qa in qa_pairs:
                self.vanna.add_question_sql(qa['question'], qa['sql'])
            
            print(f"✅ Обучение на {len(qa_pairs)} сгенерированных Q/A парах завершено")
            
        except Exception as e:
            print(f"❌ Ошибка обучения на сгенерированных Q/A: {e}")
    
    def train_on_metadata(self):
        """Обучение на метаданных"""
        try:
            print("📊 Обучение на метаданных...")
            
            with open('training_data/metadata.json', 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # Добавляем описание базы данных
            db_description = f"""
            База данных: {metadata.get('database_name', 'DocStructureSchema')}
            Описание: {metadata.get('description', 'Система управления документами и бизнес-процессами')}
            Основные таблицы: {', '.join(BUSINESS_TABLES_WHITELIST)}
            """
            
            self.vanna.add_documentation(db_description)
            self.training_stats['documentation_items'] += 1
            print("✅ Обучение на метаданных завершено")
            
        except Exception as e:
            print(f"❌ Ошибка обучения на метаданных: {e}")
    
    def train_on_database_schema_filtered(self):
        """Обучение на схеме БД с фильтрацией по бизнес-таблицам"""
        try:
            print("🗄️ Обучение на схеме БД (только бизнес-таблицы)...")
            
            # Получаем схему БД
            schema_query = """
            SELECT 
                table_name,
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns 
            WHERE table_schema = 'public'
            AND table_name IN ({})
            ORDER BY table_name, ordinal_position
            """.format(','.join([f"'{table}'" for table in BUSINESS_TABLES_WHITELIST]))
            
            df = self.vanna.run_sql(schema_query)
            
            if df.empty:
                print("⚠️ Не найдено бизнес-таблиц в схеме БД")
                return
            
            # Создаем план обучения
            plan = self.vanna.get_training_plan_generic(df)
            
            # Фильтруем план по бизнес-таблицам
            filtered_plan = []
            for item in plan:
                if any(table in item.get('content', '') for table in BUSINESS_TABLES_WHITELIST):
                    filtered_plan.append(item)
                else:
                    self.training_stats['filtered_tables'] += 1
            
            if filtered_plan:
                # Обучаем на отфильтрованном плане
                self.vanna.train(plan=filtered_plan)
                self.training_stats['schema_items'] = len(filtered_plan)
                print(f"✅ Обучение на схеме завершено: {len(filtered_plan)} элементов")
                print(f"📊 Отфильтровано {self.training_stats['filtered_tables']} технических таблиц")
            else:
                print("⚠️ Не найдено бизнес-таблиц для обучения")
                
        except Exception as e:
            print(f"❌ Ошибка обучения на схеме БД: {e}")
    
    def _filter_ddl_by_business_tables(self, ddl_content: str) -> str:
        """Фильтрует DDL по бизнес-таблицам"""
        lines = ddl_content.split('\n')
        filtered_lines = []
        current_table = None
        
        for line in lines:
            # Проверяем, начинается ли новая таблица
            if line.strip().upper().startswith('CREATE TABLE'):
                # Извлекаем имя таблицы
                parts = line.split()
                if len(parts) >= 3:
                    table_name = parts[2].strip('`"\'')
                    current_table = table_name
            
            # Если это бизнес-таблица, добавляем строку
            if current_table in BUSINESS_TABLES_WHITELIST:
                filtered_lines.append(line)
            elif line.strip() == '' or line.strip().startswith('--'):
                # Добавляем пустые строки и комментарии
                filtered_lines.append(line)
            elif line.strip() == ');' and current_table in BUSINESS_TABLES_WHITELIST:
                # Завершение таблицы
                filtered_lines.append(line)
                current_table = None
        
        return '\n'.join(filtered_lines)
    
    def train_full(self):
        """Полное обучение агента"""
        print("🚀 Начало полного обучения агента с фильтрацией")
        print("=" * 60)
        
        # 1. Обучение на DDL
        self.train_on_ddl()
        
        # 2. Обучение на документации
        self.train_on_documentation()
        
        # 3. Обучение на SQL примерах
        self.train_on_sql_examples()
        
        # 4. Обучение на сгенерированных Q/A парах
        self.train_on_generated_qa()
        
        # 5. Обучение на метаданных
        self.train_on_metadata()
        
        # 6. Обучение на схеме БД (только бизнес-таблицы)
        self.train_on_database_schema_filtered()
        
        # Выводим статистику
        print("\n📊 Статистика обучения:")
        print(f"   DDL элементов: {self.training_stats['ddl_items']}")
        print(f"   Документации: {self.training_stats['documentation_items']}")
        print(f"   SQL примеров: {self.training_stats['sql_examples']}")
        print(f"   Схемы БД: {self.training_stats['schema_items']}")
        print(f"   Отфильтровано технических таблиц: {self.training_stats['filtered_tables']}")
        
        print("\n✅ Обучение завершено!")
        print("🎯 Агент обучен только на бизнес-таблицах")
        print("📋 Используемые таблицы:", ', '.join(BUSINESS_TABLES_WHITELIST))

def main():
    """Основная функция"""
    trainer = FilteredVannaTrainer()
    trainer.train_full()

if __name__ == "__main__":
    main()
