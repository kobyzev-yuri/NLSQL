#!/usr/bin/env python3
"""
Запуск улучшенного обучения NL→SQL агента
Фокус на SQL с последующим конвертированием в план
"""

import sys
from pathlib import Path

# Добавляем путь к модулям
sys.path.append('src')

from src.vanna.sql_focused_training import SQLFocusedTraining


def main():
    """Запуск улучшенного обучения"""
    
    print("🚀 Запуск улучшенного обучения NL→SQL агента")
    print("=" * 60)
    print("📋 Стратегия: Обучение на SQL + конвертер в план")
    print("🎯 Фокус: Качество генерации SQL")
    print("=" * 60)
    
    # Конфигурация
    config = {
        'model': 'gpt-4o',
        'database_url': 'postgresql://postgres:1234@localhost:5432/test_docstructure',
        'api_key': 'sk-xF20r7G4tq9ezBMNKIjCPvva2io4S8FV',
        'base_url': 'https://api.proxyapi.ru/openai/v1'
    }
    
    try:
        # Создаем тренер
        trainer = SQLFocusedTraining(config)
        
        # Запускаем обучение
        if trainer.run_sql_training():
            print("\n🎉 Обучение завершено успешно!")
            
            # Тестируем агента
            print("\n🧪 Тестирование агента...")
            
            test_questions = [
                "Покажи всех пользователей",
                "Список отделов",
                "Все клиенты",
                "Пользователи по отделам",
                "Поручения с клиентами",
                "Платежи по клиентам",
                "Сколько клиентов в каждом регионе?",
                "Поручения за последний месяц",
                "Топ-10 клиентов по сумме поручений",
                "Пользователи отдела Продажи",
                "Платежи больше 1 млн рублей",
                "Поручения старше 3 дней от клиентов категории А больше 1 млн рублей"
            ]
            
            results = trainer.test_sql_generation(test_questions)
            
            # Сохраняем результаты
            trainer.save_training_results(results, "enhanced_sql_training_results.json")
            
            # Выводим статистику
            success_count = sum(1 for r in results.values() if r['status'] == 'success')
            avg_quality = sum(r['quality_score'] for r in results.values()) / len(results)
            
            print(f"\n📊 Статистика тестирования:")
            print(f"   Успешных запросов: {success_count}/{len(results)}")
            print(f"   Среднее качество: {avg_quality:.2f}")
            
            # Рекомендации
            if avg_quality > 0.7:
                print("✅ Качество генерации SQL хорошее!")
                print("🎯 Можно переходить к интеграции с конвертером планов")
            elif avg_quality > 0.5:
                print("⚠️ Качество генерации SQL удовлетворительное")
                print("💡 Рекомендуется добавить больше примеров обучения")
            else:
                print("❌ Качество генерации SQL требует улучшения")
                print("🔧 Рекомендуется пересмотреть стратегию обучения")
            
        else:
            print("❌ Обучение завершилось с ошибками")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
