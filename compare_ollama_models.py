#!/usr/bin/env python3
"""
Сравнительное тестирование всех моделей Ollama для генерации SQL
"""

import sys
import os
import asyncio
import time
import json
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.services.query_service import QueryService
import logging

# Настройка логирования
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Модели для тестирования (исключая llava)
MODELS_TO_TEST = [
    "mistral:7b",
    "sqlcoder:latest", 
    "phi3:latest",
    "llama3:latest",
    "qwen2.5-coder:1.5b",
    "qwen2.5:1.5b",
    "qwen3:8b"
]

# Стандартные тестовые вопросы
TEST_QUESTIONS = [
    "Покажи всех пользователей",
    "Список пользователей по отделам",
    "Покажи поручения за последний месяц",
    "Платежи по клиентам",
    "Статистика по отделам"
]

class ModelTester:
    def __init__(self):
        self.results = {}
        
    async def test_model(self, model_name, question):
        """Тестирование одной модели на одном вопросе"""
        try:
            # Устанавливаем переменную окружения для модели
            os.environ['OLLAMA_MODEL'] = model_name
            
            # Создаем новый сервис для каждой модели
            query_service = QueryService()
            
            start_time = time.time()
            sql = await query_service.generate_sql(question, {})
            end_time = time.time()
            
            duration = end_time - start_time
            
            # Анализ качества SQL
            quality_score = self.analyze_sql_quality(sql)
            
            return {
                'sql': sql,
                'duration': duration,
                'quality_score': quality_score,
                'success': quality_score > 0
            }
            
        except Exception as e:
            return {
                'sql': f"ERROR: {str(e)}",
                'duration': 0,
                'quality_score': 0,
                'success': False
            }
    
    def analyze_sql_quality(self, sql):
        """Анализ качества SQL запроса"""
        if not sql or not sql.strip():
            return 0
            
        sql_lower = sql.lower().strip()
        
        # Базовые проверки
        if not sql_lower.startswith('select'):
            return 0
            
        # Штрафы за ошибки
        penalty = 0
        
        # Проверка на несуществующие таблицы
        if 'eqorders' in sql_lower or 'eqpayments' in sql_lower:
            penalty += 1
            
        # Проверка на простые запросы
        if sql_lower == 'select * from equsers;':
            return 3  # Базовый запрос
            
        # Бонусы за сложность
        bonus = 0
        if 'join' in sql_lower:
            bonus += 1
        if 'group by' in sql_lower:
            bonus += 1
        if 'where' in sql_lower:
            bonus += 1
        if 'count(' in sql_lower or 'sum(' in sql_lower:
            bonus += 1
            
        return max(0, 5 - penalty + bonus)
    
    async def run_comparison(self):
        """Запуск сравнительного тестирования"""
        print("🤖 Сравнительное тестирование моделей Ollama")
        print("=" * 80)
        print(f"Модели: {', '.join(MODELS_TO_TEST)}")
        print(f"Вопросы: {len(TEST_QUESTIONS)}")
        print("=" * 80)
        
        for model in MODELS_TO_TEST:
            print(f"\n🔍 Тестируем модель: {model}")
            print("-" * 50)
            
            model_results = {
                'model': model,
                'questions': {},
                'summary': {
                    'total_questions': len(TEST_QUESTIONS),
                    'successful_questions': 0,
                    'average_duration': 0,
                    'average_quality': 0,
                    'total_duration': 0
                }
            }
            
            total_duration = 0
            successful_count = 0
            total_quality = 0
            
            for i, question in enumerate(TEST_QUESTIONS, 1):
                print(f"  {i}. {question}")
                
                result = await self.test_model(model, question)
                model_results['questions'][question] = result
                
                total_duration += result['duration']
                if result['success']:
                    successful_count += 1
                total_quality += result['quality_score']
                
                print(f"     ✅ SQL: {result['sql'][:100]}...")
                print(f"     ⏱️  Время: {result['duration']:.1f}с")
                print(f"     📊 Качество: {result['quality_score']}/5")
            
            # Подсчет итогов
            model_results['summary']['successful_questions'] = successful_count
            model_results['summary']['average_duration'] = total_duration / len(TEST_QUESTIONS)
            model_results['summary']['average_quality'] = total_quality / len(TEST_QUESTIONS)
            model_results['summary']['total_duration'] = total_duration
            
            self.results[model] = model_results
            
            print(f"\n📊 Итоги для {model}:")
            print(f"   Успешных: {successful_count}/{len(TEST_QUESTIONS)} ({successful_count/len(TEST_QUESTIONS)*100:.1f}%)")
            print(f"   Среднее время: {model_results['summary']['average_duration']:.1f}с")
            print(f"   Среднее качество: {model_results['summary']['average_quality']:.1f}/5")
            print(f"   Общее время: {total_duration:.1f}с")
        
        # Генерация отчета
        self.generate_report()
    
    def generate_report(self):
        """Генерация сравнительного отчета"""
        print("\n" + "="*80)
        print("📊 СРАВНИТЕЛЬНЫЙ ОТЧЕТ МОДЕЛЕЙ OLLAMA")
        print("="*80)
        
        # Сортировка по качеству
        sorted_models = sorted(
            self.results.items(), 
            key=lambda x: x[1]['summary']['average_quality'], 
            reverse=True
        )
        
        print("\n🏆 РЕЙТИНГ ПО КАЧЕСТВУ:")
        print("-" * 50)
        for i, (model, results) in enumerate(sorted_models, 1):
            summary = results['summary']
            print(f"{i}. {model}")
            print(f"   Качество: {summary['average_quality']:.1f}/5")
            print(f"   Успешность: {summary['successful_questions']}/{summary['total_questions']} ({summary['successful_questions']/summary['total_questions']*100:.1f}%)")
            print(f"   Время: {summary['average_duration']:.1f}с")
            print()
        
        # Сортировка по скорости
        sorted_by_speed = sorted(
            self.results.items(), 
            key=lambda x: x[1]['summary']['average_duration']
        )
        
        print("⚡ РЕЙТИНГ ПО СКОРОСТИ:")
        print("-" * 50)
        for i, (model, results) in enumerate(sorted_by_speed, 1):
            summary = results['summary']
            print(f"{i}. {model}: {summary['average_duration']:.1f}с")
        
        # Детальная таблица
        print("\n📋 ДЕТАЛЬНАЯ ТАБЛИЦА:")
        print("-" * 80)
        print(f"{'Модель':<20} {'Качество':<10} {'Успешность':<12} {'Время':<8} {'Общее время':<12}")
        print("-" * 80)
        
        for model, results in sorted_models:
            summary = results['summary']
            success_rate = f"{summary['successful_questions']}/{summary['total_questions']} ({summary['successful_questions']/summary['total_questions']*100:.1f}%)"
            print(f"{model:<20} {summary['average_quality']:<10.1f} {success_rate:<12} {summary['average_duration']:<8.1f}с {summary['total_duration']:<12.1f}с")
        
        # Сохранение результатов
        with open('ollama_models_comparison.json', 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Результаты сохранены в: ollama_models_comparison.json")
        
        # Рекомендации
        print("\n🎯 РЕКОМЕНДАЦИИ:")
        print("-" * 50)
        best_quality = sorted_models[0]
        fastest = sorted_by_speed[0]
        
        print(f"🏆 Лучшее качество: {best_quality[0]} ({best_quality[1]['summary']['average_quality']:.1f}/5)")
        print(f"⚡ Самая быстрая: {fastest[0]} ({fastest[1]['summary']['average_duration']:.1f}с)")
        
        # Находим баланс качества и скорости
        balanced_models = []
        for model, results in self.results.items():
            quality = results['summary']['average_quality']
            speed = results['summary']['average_duration']
            # Балл = качество / время (чем больше, тем лучше)
            score = quality / speed if speed > 0 else 0
            balanced_models.append((model, score, quality, speed))
        
        balanced_models.sort(key=lambda x: x[1], reverse=True)
        best_balanced = balanced_models[0]
        
        print(f"⚖️  Лучший баланс: {best_balanced[0]} (качество: {best_balanced[2]:.1f}, время: {best_balanced[3]:.1f}с)")

async def main():
    """Основная функция"""
    tester = ModelTester()
    await tester.run_comparison()

if __name__ == "__main__":
    asyncio.run(main())




