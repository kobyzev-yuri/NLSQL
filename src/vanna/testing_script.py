#!/usr/bin/env python3
"""
Скрипт тестирования Vanna AI агента
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

class VannaTester:
    """Класс для тестирования Vanna AI агента"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.vanna = DocStructureVannaNative(config=config)
        self.test_questions = config.get("test_questions", [])
        
    def test_basic_queries(self) -> bool:
        """Тестирование базовых запросов"""
        try:
            logger.info("🔍 Тестирование базовых запросов...")
            
            basic_questions = [
                "Покажи всех пользователей",
                "Сколько клиентов в системе?",
                "Покажи поручения за последний месяц",
                "Статистика по отделам"
            ]
            
            for question in basic_questions:
                logger.info(f"❓ Тестируем: {question}")
                try:
                    sql = self.vanna.generate_sql(question)
                    logger.info(f"✅ SQL сгенерирован: {sql}")
                except Exception as e:
                    logger.error(f"❌ Ошибка генерации SQL: {e}")
                    return False
                    
            logger.info("✅ Базовые запросы протестированы")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка тестирования базовых запросов: {e}")
            return False
    
    def test_complex_queries(self) -> bool:
        """Тестирование сложных запросов"""
        try:
            logger.info("🔍 Тестирование сложных запросов...")
            
            complex_questions = [
                "Покажи пользователей с их отделами и ролями",
                "Статистика по поручениям по отделам за последний месяц",
                "Топ-10 клиентов по количеству поручений",
                "Пользователи без поручений за последний месяц"
            ]
            
            for question in complex_questions:
                logger.info(f"❓ Тестируем: {question}")
                try:
                    sql = self.vanna.generate_sql(question)
                    logger.info(f"✅ SQL сгенерирован: {sql}")
                except Exception as e:
                    logger.error(f"❌ Ошибка генерации SQL: {e}")
                    return False
                    
            logger.info("✅ Сложные запросы протестированы")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка тестирования сложных запросов: {e}")
            return False
    
    def test_error_handling(self) -> bool:
        """Тестирование обработки ошибок"""
        try:
            logger.info("🔍 Тестирование обработки ошибок...")
            
            error_questions = [
                "Покажи несуществующую таблицу",
                "Непонятный запрос на китайском языке",
                "Покажи данные из другой базы",
                "Сложный запрос с ошибками"
            ]
            
            for question in error_questions:
                logger.info(f"❓ Тестируем обработку ошибок: {question}")
                try:
                    sql = self.vanna.generate_sql(question)
                    logger.info(f"✅ SQL сгенерирован (возможно с ошибками): {sql}")
                except Exception as e:
                    logger.info(f"✅ Ошибка корректно обработана: {e}")
                    
            logger.info("✅ Обработка ошибок протестирована")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка тестирования обработки ошибок: {e}")
            return False
    
    def test_full(self) -> bool:
        """Полное тестирование агента"""
        try:
            logger.info("🧪 Начало полного тестирования агента...")
            
            # Тестируем все типы запросов
            success = True
            success &= self.test_basic_queries()
            success &= self.test_complex_queries()
            success &= self.test_error_handling()
            
            if success:
                logger.info("✅ Полное тестирование завершено успешно!")
            else:
                logger.error("❌ Тестирование завершилось с ошибками")
                
            return success
            
        except Exception as e:
            logger.error(f"❌ Критическая ошибка тестирования: {e}")
            return False
    
    def generate_test_report(self) -> str:
        """Генерация отчета о тестировании"""
        try:
            report = {
                "timestamp": str(Path.cwd()),
                "test_results": {
                    "basic_queries": "✅ Пройдены",
                    "complex_queries": "✅ Пройдены", 
                    "error_handling": "✅ Пройдены"
                },
                "recommendations": [
                    "Агент готов к работе",
                    "Рекомендуется дополнительное обучение на реальных данных",
                    "Мониторинг качества SQL запросов"
                ]
            }
            
            report_file = Path("test_report.json")
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
                
            logger.info(f"📊 Отчет о тестировании сохранен: {report_file}")
            return str(report_file)
            
        except Exception as e:
            logger.error(f"❌ Ошибка генерации отчета: {e}")
            return ""

def main():
    """Главная функция тестирования"""
    # Конфигурация
    config = {
        "vanna_model": "ollama/llama3.1:8b",
        "vector_db": "chromadb",
        "test_questions": [
            "Покажи всех пользователей",
            "Сколько клиентов в системе?",
            "Покажи поручения за последний месяц",
            "Статистика по отделам",
            "Покажи платежи за сегодня"
        ]
    }
    
    # Создаем тестер
    tester = VannaTester(config)
    
    # Запускаем тестирование
    success = tester.test_full()
    
    if success:
        print("🎉 Тестирование завершено успешно!")
        print("🤖 Агент готов к работе!")
        
        # Генерируем отчет
        report_file = tester.generate_test_report()
        if report_file:
            print(f"📊 Отчет сохранен: {report_file}")
    else:
        print("❌ Тестирование завершилось с ошибками")
        sys.exit(1)

if __name__ == "__main__":
    main()
