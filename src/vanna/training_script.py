#!/usr/bin/env python3
"""
Скрипт обучения Vanna AI агента
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Any
import json

# Добавляем путь к проекту
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.vanna.vanna_pgvector_native import DocStructureVannaNative

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class VannaTrainer:
    """Класс для обучения Vanna AI агента"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.vanna = DocStructureVannaNative(config=config)
        self.training_data_dir = Path(config.get("training_data_dir", "training_data"))
        
    def train_on_ddl(self) -> bool:
        """Обучение на DDL statements"""
        try:
            ddl_file = self.training_data_dir / "ddl_statements.sql"
            if not ddl_file.exists():
                logger.error(f"❌ Файл DDL не найден: {ddl_file}")
                return False
                
            with open(ddl_file, 'r', encoding='utf-8') as f:
                ddl_content = f.read()
                
            # Для DDL используем прямое добавление через vanna
            # (API /training/example предназначен для Q/A пар)
            if hasattr(self.vanna, 'add_ddl'):
                self.vanna.add_ddl(ddl_content)
            else:
                self.vanna.train(ddl=ddl_content)
            
            logger.info("✅ Обучение на DDL завершено")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка обучения на DDL: {e}")
            return False
    
    def train_on_documentation(self) -> bool:
        """Обучение на документации (использует прямое добавление через vanna)"""
        try:
            doc_file = self.training_data_dir / "documentation.txt"
            if not doc_file.exists():
                logger.error(f"❌ Файл документации не найден: {doc_file}")
                return False
                
            with open(doc_file, 'r', encoding='utf-8') as f:
                doc_content = f.read()
                
            # Для документации используем прямое добавление через vanna
            # (API /training/example предназначен для Q/A пар)
            if hasattr(self.vanna, 'add_documentation'):
                self.vanna.add_documentation(doc_content)
            else:
                self.vanna.train(documentation=doc_content)
            
            logger.info("✅ Обучение на документации завершено")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка обучения на документации: {e}")
            return False
    
    def train_on_sql_examples(self) -> bool:
        """Обучение на SQL примерах через унифицированный API клиент"""
        try:
            examples_file = self.training_data_dir / "sql_examples.json"
            if not examples_file.exists():
                logger.error(f"❌ Файл SQL примеров не найден: {examples_file}")
                return False
            
            # Используем унифицированный клиент через API
            from src.tools.kb_training_client import KBTrainingClient
            
            client = KBTrainingClient()
            if not client.check_api_connection():
                logger.warning("⚠️ Core API недоступен, используем прямое добавление через vanna")
                # Fallback: прямое добавление через vanna (старый способ)
                with open(examples_file, 'r', encoding='utf-8') as f:
                    examples = json.load(f)
                
                for example in examples:
                    question = example.get("question")
                    sql = example.get("sql")
                    if question and sql:
                        self.vanna.train(question=question, sql=sql)
                
                logger.info("✅ Обучение на SQL примерах завершено (через прямое добавление)")
                return True
            
            # Используем API клиент
            stats = client.add_from_json_file(
                json_file=examples_file,
                user_id="training_script",
                verbose=False
            )
            
            if stats['failed'] == 0:
                logger.info(f"✅ Обучение на SQL примерах завершено: {stats['success']}/{stats['total']} добавлено")
                return True
            else:
                logger.warning(f"⚠️ Обучение завершено с ошибками: {stats['success']}/{stats['total']} успешно, {stats['failed']} ошибок")
                return stats['success'] > 0
            
        except Exception as e:
            logger.error(f"❌ Ошибка обучения на SQL примерах: {e}")
            return False
    
    def train_on_metadata(self) -> bool:
        """Обучение на метаданных"""
        try:
            metadata_file = self.training_data_dir / "metadata.json"
            if not metadata_file.exists():
                logger.error(f"❌ Файл метаданных не найден: {metadata_file}")
                return False
                
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                
            # Обучаем на метаданных
            # Создаем общее описание базы данных
            db_description = f"База данных: {metadata.get('database', 'Unknown')}\n"
            db_description += f"Всего таблиц: {metadata.get('total_tables', 0)}\n"
            db_description += f"Основные таблицы: {', '.join(metadata.get('main_tables', []))}\n"
            db_description += f"Бизнес-домены: {', '.join(metadata.get('business_domains', []))}\n"
            
            # Добавляем в векторную БД
            self.vanna.add_documentation(db_description)
                
            logger.info("✅ Обучение на метаданных завершено")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка обучения на метаданных: {e}")
            return False
    
    def train_on_database_schema(self) -> bool:
        """Автоматическое обучение на схеме базы данных через INFORMATION_SCHEMA"""
        try:
            logger.info("🔍 Получение схемы базы данных из INFORMATION_SCHEMA...")
            
            # Получаем схему базы данных
            schema_query = """
            SELECT 
                table_name,
                column_name,
                data_type,
                is_nullable,
                column_default,
                character_maximum_length
            FROM information_schema.columns 
            WHERE table_schema = 'public'
            ORDER BY table_name, ordinal_position
            """
            
            # Выполняем запрос к базе данных
            df_schema = self.vanna.run_sql(schema_query)
            
            if df_schema is None or df_schema.empty:
                logger.warning("⚠️ Схема базы данных пуста или недоступна")
                return False
            
            logger.info(f"📊 Найдено {len(df_schema)} колонок в схеме")
            
            # Создаем план обучения на основе схемы
            plan = self.vanna.get_training_plan_generic(df_schema)
            
            if plan is None or not plan:
                logger.warning("⚠️ Не удалось создать план обучения на основе схемы")
                return False
            
            logger.info(f"📋 Создан план обучения с {len(plan)} элементами")
            
            # Обучаем на плане
            self.vanna.train(plan=plan)
            
            logger.info("✅ Обучение на схеме базы данных завершено")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка обучения на схеме базы данных: {e}")
            return False
    
    def train_full(self) -> bool:
        """Полное обучение агента"""
        try:
            logger.info("🎓 Начало полного обучения агента...")
            
            # Обучаем на всех типах данных
            success = True
            success &= self.train_on_ddl()
            success &= self.train_on_documentation()
            success &= self.train_on_sql_examples()
            success &= self.train_on_metadata()
            
            # Автоматическое обучение на схеме базы данных
            logger.info("🔍 Добавляем автоматическое обучение на схеме базы данных...")
            schema_success = self.train_on_database_schema()
            if schema_success:
                logger.info("✅ Автоматическое обучение на схеме завершено")
            else:
                logger.warning("⚠️ Автоматическое обучение на схеме не удалось (возможно, БД недоступна)")
            
            if success:
                logger.info("✅ Полное обучение завершено успешно!")
            else:
                logger.error("❌ Обучение завершилось с ошибками")
                
            return success
            
        except Exception as e:
            logger.error(f"❌ Критическая ошибка обучения: {e}")
            return False

def main():
    """Главная функция обучения"""
    # Загружаем конфигурацию из файла
    config_file = Path("config.json")
    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
    else:
        # Конфигурация по умолчанию
        config = {
            "vanna_model": "gpt-4o",
            "vector_db": "pgvector",
            "training_data_dir": "training_data",
            "api_key": "your-api-key",
            "base_url": "https://api.proxyapi.ru/openai/v1",
            "model": "gpt-4o"
        }
    
    # Создаем тренер
    trainer = VannaTrainer(config)
    
    # Запускаем обучение
    success = trainer.train_full()
    
    if success:
        print("🎉 Обучение завершено успешно!")
        print("🤖 Агент готов к работе!")
    else:
        print("❌ Обучение завершилось с ошибками")
        sys.exit(1)

if __name__ == "__main__":
    main()
