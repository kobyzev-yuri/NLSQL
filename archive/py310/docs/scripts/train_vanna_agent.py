#!/usr/bin/env python3
"""
Скрипт для запуска полного пайплайна обучения Vanna AI агента
"""

import os
import sys
import logging
from pathlib import Path
import argparse

# Добавляем путь к проекту
sys.path.append(str(Path(__file__).parent))

from src.vanna.training_pipeline import VannaTrainingPipeline

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(description="Обучение Vanna AI агента")
    parser.add_argument("--config", type=str, default="config.json", help="Файл конфигурации")
    parser.add_argument("--step", type=str, choices=["prepare", "train", "test", "all"], 
                       default="all", help="Этап пайплайна")
    parser.add_argument("--model", type=str, default="ollama/llama3.1:8b", help="Модель Vanna")
    parser.add_argument("--vector-db", type=str, default="chromadb", help="Векторная БД")
    
    args = parser.parse_args()
    
    # Конфигурация по умолчанию
    config = {
        "database_url": "postgresql://postgres:1234@localhost:5432/test_docstructure",
        "vanna_model": args.model,
        "vector_db": args.vector_db,
        "training_data_dir": "training_data",
        "test_questions": [
            "Покажи всех пользователей",
            "Сколько клиентов в системе?",
            "Покажи поручения за последний месяц",
            "Статистика по отделам",
            "Покажи платежи за сегодня"
        ]
    }
    
    # Загружаем конфигурацию из файла, если существует
    config_file = Path(args.config)
    if config_file.exists():
        try:
            import json
            with open(config_file, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
                config.update(file_config)
        except Exception as e:
            logger.warning(f"⚠️ Ошибка загрузки конфигурации: {e}")
    
    # Создаем пайплайн
    pipeline = VannaTrainingPipeline(config)
    
    # Запускаем нужный этап
    if args.step == "prepare":
        logger.info("📊 Запуск этапа подготовки данных...")
        success = pipeline.prepare_training_data()
    elif args.step == "train":
        logger.info("🤖 Запуск этапа обучения...")
        success = pipeline.train_agent()
    elif args.step == "test":
        logger.info("🧪 Запуск этапа тестирования...")
        success = pipeline.test_agent()
    else:  # all
        logger.info("🚀 Запуск полного пайплайна...")
        success = pipeline.run_full_pipeline()
    
    if success:
        print("🎉 Пайплайн завершен успешно!")
        print("🤖 Агент готов к работе!")
    else:
        print("❌ Пайплайн завершился с ошибками")
        sys.exit(1)

if __name__ == "__main__":
    main()
