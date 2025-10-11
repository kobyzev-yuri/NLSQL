#!/usr/bin/env python3
"""
Пайплайн обучения Vanna AI агента для DocStructureSchema
Этапы:
1. Подготовка данных для обучения
2. Обучение агента
3. Тестирование
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Any
import json

# Добавляем путь к проекту
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.vanna.training_data_preparation import VannaTrainingDataPreparator
from src.vanna.vanna_client import DocStructureVanna
from src.vanna.training_script import VannaTrainer
from src.vanna.testing_script import VannaTester

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class VannaTrainingPipeline:
    """Пайплайн обучения Vanna AI агента"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.data_preparator = VannaTrainingDataPreparator()
        self.trainer = VannaTrainer(config)
        self.tester = VannaTester(config)
        
    def run_full_pipeline(self) -> bool:
        """Запуск полного пайплайна обучения"""
        try:
            logger.info("🚀 Запуск пайплайна обучения Vanna AI")
            
            # Этап 1: Подготовка данных
            logger.info("📊 Этап 1: Подготовка данных для обучения")
            if not self.prepare_training_data():
                logger.error("❌ Ошибка на этапе подготовки данных")
                return False
                
            # Этап 2: Обучение агента
            logger.info("🤖 Этап 2: Обучение агента")
            if not self.train_agent():
                logger.error("❌ Ошибка на этапе обучения")
                return False
                
            # Этап 3: Тестирование
            logger.info("🧪 Этап 3: Тестирование агента")
            if not self.test_agent():
                logger.error("❌ Ошибка на этапе тестирования")
                return False
                
            logger.info("✅ Пайплайн обучения завершен успешно!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Критическая ошибка в пайплайне: {e}")
            return False
    
    def prepare_training_data(self) -> bool:
        """Этап 1: Подготовка данных для обучения"""
        try:
            logger.info("📋 Подготовка данных для обучения...")
            
            # Создаем директорию для данных
            training_data_dir = Path(self.config.get("training_data_dir", "training_data"))
            training_data_dir.mkdir(exist_ok=True)
            
            # Подготавливаем и сохраняем данные
            self.data_preparator.save_training_data(str(training_data_dir))
            
            logger.info("✅ Данные для обучения подготовлены")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка подготовки данных: {e}")
            return False
    
    def train_agent(self) -> bool:
        """Этап 2: Обучение агента"""
        try:
            logger.info("🎓 Начало обучения агента...")
            
            # Обучаем на DDL
            logger.info("📋 Обучение на DDL statements...")
            self.trainer.train_on_ddl()
            
            # Обучаем на документации
            logger.info("📚 Обучение на документации...")
            self.trainer.train_on_documentation()
            
            # Обучаем на SQL примерах
            logger.info("💡 Обучение на SQL примерах...")
            self.trainer.train_on_sql_examples()
            
            # Обучаем на метаданных
            logger.info("🔍 Обучение на метаданных...")
            self.trainer.train_on_metadata()
            
            logger.info("✅ Агент обучен")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка обучения: {e}")
            return False
    
    def test_agent(self) -> bool:
        """Этап 3: Тестирование агента"""
        try:
            logger.info("🧪 Начало тестирования агента...")
            
            # Тестируем базовые запросы
            logger.info("🔍 Тестирование базовых запросов...")
            self.tester.test_basic_queries()
            
            # Тестируем сложные запросы
            logger.info("🔍 Тестирование сложных запросов...")
            self.tester.test_complex_queries()
            
            # Тестируем обработку ошибок
            logger.info("🔍 Тестирование обработки ошибок...")
            self.tester.test_error_handling()
            
            logger.info("✅ Тестирование завершено")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка тестирования: {e}")
            return False

def main():
    """Главная функция пайплайна"""
    # Конфигурация
    config = {
        "database_url": "postgresql://postgres:1234@localhost:5432/test_docstructure",
        "vanna_model": "ollama/llama3.1:8b",
        "vector_db": "chromadb",
        "training_data_dir": "training_data",
        "test_questions": [
            "Покажи всех пользователей",
            "Сколько клиентов в системе?",
            "Покажи поручения за последний месяц",
            "Статистика по отделам",
            "Покажи платежи за сегодня"
        ]
    }
    
    # Создаем пайплайн
    pipeline = VannaTrainingPipeline(config)
    
    # Запускаем полный пайплайн
    success = pipeline.run_full_pipeline()
    
    if success:
        print("🎉 Пайплайн обучения завершен успешно!")
        print("🤖 Агент готов к работе!")
    else:
        print("❌ Пайплайн обучения завершился с ошибками")
        sys.exit(1)

if __name__ == "__main__":
    main()
