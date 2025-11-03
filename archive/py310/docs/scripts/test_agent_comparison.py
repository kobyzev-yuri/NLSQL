#!/usr/bin/env python3
"""
Скрипт для тестирования и сравнения результатов агента
до и после автоматического обучения на схеме БД
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Any
import json

# Добавляем путь к проекту
sys.path.append(str(Path(__file__).parent))

from src.vanna.vanna_pgvector_native import DocStructureVannaNative

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AgentTester:
    """Класс для тестирования агента"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.vanna = DocStructureVannaNative(config=config)
        
    def test_questions(self) -> Dict[str, Any]:
        """Тестирование набора вопросов"""
        test_questions = [
            "Покажи всех пользователей",
            "Список отделов",
            "Все клиенты",
            "Пользователи по отделам",
            "Поручения с клиентами",
            "Платежи по клиентам",
            "Количество пользователей по отделам",
            "Поручения за последний месяц",
            "Сумма платежей по месяцам",
            "Покажи таблицы в базе данных",
            "Какие поля есть в таблице equsers?",
            "Связи между таблицами",
            "Статистика по пользователям",
            "Активные пользователи",
            "Недавние поручения"
        ]
        
        results = {}
        
        for question in test_questions:
            try:
                logger.info(f"🔍 Тестирование: {question}")
                
                # Генерируем SQL
                sql = self.vanna.generate_sql(question)
                
                results[question] = {
                    "sql": sql,
                    "success": sql is not None and sql.strip() != "",
                    "error": None
                }
                
                if results[question]["success"]:
                    logger.info(f"✅ SQL сгенерирован: {sql[:100]}...")
                else:
                    logger.warning(f"⚠️ SQL не сгенерирован для: {question}")
                    
            except Exception as e:
                logger.error(f"❌ Ошибка для вопроса '{question}': {e}")
                results[question] = {
                    "sql": None,
                    "success": False,
                    "error": str(e)
                }
        
        return results
    
    def analyze_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Анализ результатов тестирования"""
        total_questions = len(results)
        successful = sum(1 for r in results.values() if r["success"])
        failed = total_questions - successful
        
        success_rate = (successful / total_questions) * 100 if total_questions > 0 else 0
        
        # Анализ типов вопросов
        simple_questions = ["Покажи всех пользователей", "Список отделов", "Все клиенты"]
        complex_questions = ["Пользователи по отделам", "Поручения с клиентами", "Платежи по клиентам"]
        schema_questions = ["Покажи таблицы в базе данных", "Какие поля есть в таблице equsers?", "Связи между таблицами"]
        
        simple_success = sum(1 for q in simple_questions if results.get(q, {}).get("success", False))
        complex_success = sum(1 for q in complex_questions if results.get(q, {}).get("success", False))
        schema_success = sum(1 for q in schema_questions if results.get(q, {}).get("success", False))
        
        analysis = {
            "total_questions": total_questions,
            "successful": successful,
            "failed": failed,
            "success_rate": success_rate,
            "simple_questions": {
                "total": len(simple_questions),
                "successful": simple_success,
                "success_rate": (simple_success / len(simple_questions)) * 100 if simple_questions else 0
            },
            "complex_questions": {
                "total": len(complex_questions),
                "successful": complex_success,
                "success_rate": (complex_success / len(complex_questions)) * 100 if complex_questions else 0
            },
            "schema_questions": {
                "total": len(schema_questions),
                "successful": schema_success,
                "success_rate": (schema_success / len(schema_questions)) * 100 if schema_questions else 0
            }
        }
        
        return analysis
    
    def save_results(self, results: Dict[str, Any], analysis: Dict[str, Any], filename: str):
        """Сохранение результатов в файл"""
        output = {
            "timestamp": str(Path(__file__).stat().st_mtime),
            "analysis": analysis,
            "detailed_results": results
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        logger.info(f"📊 Результаты сохранены в {filename}")

def main():
    """Главная функция тестирования"""
    # Загружаем конфигурацию
    config_file = Path("config.json")
    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
    else:
        config = {
            "vanna_model": "gpt-4o",
            "vector_db": "pgvector",
            "training_data_dir": "training_data",
            "api_key": "your-api-key",
            "base_url": "https://api.proxyapi.ru/openai/v1",
            "model": "gpt-4o"
        }
    
    # Создаем тестер
    tester = AgentTester(config)
    
    # Запускаем тестирование
    logger.info("🧪 Начало тестирования агента...")
    results = tester.test_questions()
    
    # Анализируем результаты
    analysis = tester.analyze_results(results)
    
    # Выводим результаты
    logger.info("📊 Результаты тестирования:")
    logger.info(f"Всего вопросов: {analysis['total_questions']}")
    logger.info(f"Успешных: {analysis['successful']}")
    logger.info(f"Неудачных: {analysis['failed']}")
    logger.info(f"Процент успеха: {analysis['success_rate']:.1f}%")
    
    logger.info("📈 Детальный анализ:")
    logger.info(f"Простые вопросы: {analysis['simple_questions']['success_rate']:.1f}%")
    logger.info(f"Сложные вопросы: {analysis['complex_questions']['success_rate']:.1f}%")
    logger.info(f"Вопросы по схеме: {analysis['schema_questions']['success_rate']:.1f}%")
    
    # Сохраняем результаты
    tester.save_results(results, analysis, "test_results_after_schema_training.json")
    
    logger.info("✅ Тестирование завершено!")

if __name__ == "__main__":
    main()
