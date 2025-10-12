#!/usr/bin/env python3
"""
Скрипт для запуска улучшенного обучения KB агента
Использует двухмодельный пайплайн и улучшенную логику контекста
"""

import os
import sys
import json
import logging
from pathlib import Path

# Добавляем путь к модулям
sys.path.append(str(Path(__file__).parent))

from src.vanna.enhanced_kb_agent import EnhancedKBAgent

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_training_data() -> dict:
    """Загрузка данных для обучения"""
    training_data = {
        'examples': [],
        'documentation': []
    }
    
    # Загружаем улучшенные примеры
    examples_file = Path("training_data/enhanced_sql_examples.json")
    if examples_file.exists():
        try:
            with open(examples_file, 'r', encoding='utf-8') as f:
                examples_data = json.load(f)
                training_data['examples'] = examples_data.get('examples', [])
            logger.info(f"✅ Загружено {len(training_data['examples'])} примеров")
        except Exception as e:
            logger.warning(f"⚠️ Ошибка загрузки примеров: {e}")
    
    # Загружаем документацию
    docs_file = Path("training_data/documentation.txt")
    if docs_file.exists():
        try:
            with open(docs_file, 'r', encoding='utf-8') as f:
                training_data['documentation'] = f.read()
            logger.info("✅ Загружена документация")
        except Exception as e:
            logger.warning(f"⚠️ Ошибка загрузки документации: {e}")
    
    return training_data

def test_agent(agent: EnhancedKBAgent) -> dict:
    """Тестирование агента"""
    test_questions = [
        "Покажи всех пользователей",
        "Список отделов", 
        "Все клиенты",
        "Пользователи по отделам",
        "Платежи за последний месяц"
    ]
    
    results = {}
    
    logger.info("🧪 Начало тестирования агента...")
    
    for question in test_questions:
        logger.info(f"❓ Тестирование: '{question}'")
        
        try:
            result = agent.generate_sql(question)
            results[question] = result
            
            if result['success']:
                logger.info(f"✅ Успех: {result['sql'][:50]}...")
            else:
                logger.error(f"❌ Ошибка: {result.get('error', 'Неизвестная ошибка')}")
                
        except Exception as e:
            logger.error(f"❌ Критическая ошибка: {e}")
            results[question] = {
                'success': False,
                'error': str(e)
            }
    
    return results

def main():
    """Основная функция"""
    logger.info("🚀 Запуск улучшенного обучения KB агента")
    logger.info("=" * 60)
    
    try:
        # 1. Создаем агента
        logger.info("🤖 Создание KB агента...")
        agent = EnhancedKBAgent()
        
        # 2. Проверяем здоровье
        logger.info("🏥 Проверка здоровья агента...")
        health = agent.health_check()
        logger.info(f"Здоровье: {health}")
        
        if not health.get('overall', False):
            logger.warning("⚠️ Агент не готов к работе")
            return
        
        # 3. Загружаем данные для обучения
        logger.info("📚 Загрузка данных для обучения...")
        training_data = load_training_data()
        
        # 4. Обучаем агента
        logger.info("🎓 Начало обучения...")
        training_success = agent.train_agent(training_data)
        
        if not training_success:
            logger.error("❌ Обучение не удалось")
            return
        
        logger.info("✅ Обучение завершено успешно")
        
        # 5. Тестируем агента
        logger.info("🧪 Тестирование агента...")
        test_results = test_agent(agent)
        
        # 6. Сохраняем результаты
        results_file = "enhanced_kb_training_results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump({
                'training_success': training_success,
                'test_results': test_results,
                'health': health,
                'statistics': agent.get_statistics()
            }, f, ensure_ascii=False, indent=2)
        
        logger.info(f"📊 Результаты сохранены в {results_file}")
        
        # 7. Статистика
        success_count = sum(1 for r in test_results.values() if r.get('success', False))
        total_count = len(test_results)
        
        logger.info(f"\n📊 Статистика тестирования:")
        logger.info(f"   Успешных запросов: {success_count}/{total_count}")
        logger.info(f"   Качество: {success_count/total_count:.2f}")
        
        if success_count >= total_count * 0.8:
            logger.info("🎉 Агент работает отлично!")
        elif success_count >= total_count * 0.6:
            logger.info("✅ Агент работает хорошо")
        else:
            logger.warning("⚠️ Агент требует доработки")
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        raise

if __name__ == "__main__":
    main()
