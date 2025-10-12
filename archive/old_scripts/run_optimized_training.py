#!/usr/bin/env python3
"""
Скрипт для запуска оптимизированного обучения
Использует улучшенный двухмодельный пайплайн с приоритизацией таблиц
"""

import os
import sys
import json
import logging
from pathlib import Path

# Добавляем путь к модулям
sys.path.append(str(Path(__file__).parent))

from src.vanna.optimized_dual_pipeline import OptimizedDualPipeline

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

def test_pipeline(pipeline: OptimizedDualPipeline) -> dict:
    """Тестирование пайплайна"""
    test_questions = [
        "Покажи всех пользователей",
        "Список отделов", 
        "Все клиенты",
        "Пользователи по отделам",
        "Платежи за последний месяц"
    ]
    
    results = {}
    
    logger.info("🧪 Начало тестирования оптимизированного пайплайна...")
    
    for question in test_questions:
        logger.info(f"❓ Тестирование: '{question}'")
        
        try:
            result = pipeline.generate_sql(question)
            results[question] = result
            
            if result['success']:
                logger.info(f"✅ Успех: {result['sql'][:50]}...")
                logger.info(f"   Модель: {result['model']}, Время: {result['time']:.2f} сек")
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
    logger.info("🚀 Запуск оптимизированного обучения")
    logger.info("=" * 60)
    
    try:
        # 1. Создаем оптимизированный пайплайн
        logger.info("🤖 Создание оптимизированного пайплайна...")
        pipeline = OptimizedDualPipeline()
        
        # 2. Проверяем здоровье
        logger.info("🏥 Проверка здоровья пайплайна...")
        health = pipeline.health_check()
        logger.info(f"Здоровье: {health}")
        
        if not any(health.values()):
            logger.error("❌ Ни одна модель не доступна")
            return
        
        # 3. Загружаем данные для обучения
        logger.info("📚 Загрузка данных для обучения...")
        training_data = load_training_data()
        
        # 4. Обучаем на схеме БД
        logger.info("🎓 Обучение на схеме БД...")
        schema_success = pipeline.train_on_schema()
        
        if not schema_success:
            logger.warning("⚠️ Обучение на схеме не удалось")
        else:
            logger.info("✅ Обучение на схеме завершено")
        
        # 5. Обучаем на примерах
        if training_data['examples']:
            logger.info("🎓 Обучение на примерах...")
            examples_success = pipeline.train_on_examples(training_data['examples'])
            
            if examples_success:
                logger.info("✅ Обучение на примерах завершено")
            else:
                logger.warning("⚠️ Обучение на примерах не удалось")
        
        # 6. Тестируем пайплайн
        logger.info("🧪 Тестирование пайплайна...")
        test_results = test_pipeline(pipeline)
        
        # 7. Сохраняем результаты
        results_file = "optimized_training_results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump({
                'schema_training_success': schema_success,
                'examples_training_success': training_data['examples'] and examples_success,
                'test_results': test_results,
                'health': health,
                'statistics': pipeline.get_usage_stats()
            }, f, ensure_ascii=False, indent=2)
        
        logger.info(f"📊 Результаты сохранены в {results_file}")
        
        # 8. Статистика
        success_count = sum(1 for r in test_results.values() if r.get('success', False))
        total_count = len(test_results)
        
        logger.info(f"\n📊 Статистика тестирования:")
        logger.info(f"   Успешных запросов: {success_count}/{total_count}")
        logger.info(f"   Качество: {success_count/total_count:.2f}")
        
        # Анализ по моделям
        model_usage = {}
        for result in test_results.values():
            if result.get('success') and 'model' in result:
                model = result['model']
                if model not in model_usage:
                    model_usage[model] = {'calls': 0, 'success': 0}
                model_usage[model]['calls'] += 1
                model_usage[model]['success'] += 1
        
        logger.info(f"\n📊 Использование моделей:")
        for model, stats in model_usage.items():
            logger.info(f"   {model}: {stats['success']}/{stats['calls']} ({stats['success']/stats['calls']:.2f})")
        
        if success_count >= total_count * 0.8:
            logger.info("🎉 Оптимизированный пайплайн работает отлично!")
        elif success_count >= total_count * 0.6:
            logger.info("✅ Оптимизированный пайплайн работает хорошо")
        else:
            logger.warning("⚠️ Оптимизированный пайплайн требует доработки")
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        raise

if __name__ == "__main__":
    main()
