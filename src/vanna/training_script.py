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
                
            # Обучаем на DDL
            self.vanna.train(ddl=ddl_content)
            logger.info("✅ Обучение на DDL завершено")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка обучения на DDL: {e}")
            return False
    
    def train_on_documentation(self) -> bool:
        """Обучение на документации"""
        try:
            doc_file = self.training_data_dir / "documentation.txt"
            if not doc_file.exists():
                logger.error(f"❌ Файл документации не найден: {doc_file}")
                return False
                
            with open(doc_file, 'r', encoding='utf-8') as f:
                doc_content = f.read()
                
            # Обучаем на документации
            self.vanna.train(documentation=doc_content)
            logger.info("✅ Обучение на документации завершено")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка обучения на документации: {e}")
            return False
    
    def train_on_sql_examples(self) -> bool:
        """Обучение на SQL примерах"""
        try:
            examples_file = self.training_data_dir / "sql_examples.json"
            if not examples_file.exists():
                logger.error(f"❌ Файл SQL примеров не найден: {examples_file}")
                return False
                
            with open(examples_file, 'r', encoding='utf-8') as f:
                examples = json.load(f)
                
            # Обучаем на каждом примере
            for example in examples:
                question = example.get("question")
                sql = example.get("sql")
                if question and sql:
                    self.vanna.train(question=question, sql=sql)
                    
            logger.info("✅ Обучение на SQL примерах завершено")
            return True
            
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
    # Конфигурация
    config = {
        "vanna_model": "ollama/llama3.1:8b",
        "vector_db": "chromadb",
        "training_data_dir": "training_data"
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
