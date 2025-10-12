#!/usr/bin/env python3
"""
Продвинутое сравнение всех моделей с детальным анализом
"""

import sys
import time
import json
from pathlib import Path
from datetime import datetime

# Добавляем путь к модулям
sys.path.append(str(Path(__file__).parent / "src"))

class ModelTester:
    """Класс для тестирования различных LLM моделей"""
    
    def __init__(self):
        self.results = {}
        self.test_questions = [
            "Покажи всех пользователей",
            "Список отделов",
            "Все клиенты",
            "Пользователи по отделам"
        ]
        
    def test_model(self, model_name, config):
        """Тестирование одной модели"""
        print(f"\n🧠 Тестирование {model_name}...")
        print("=" * 50)
        
        model_results = {
            'model': model_name,
            'config': config,
            'questions': {},
            'total_time': 0,
            'success_rate': 0,
            'quality_score': 0
        }
        
        try:
            from src.vanna.vanna_pgvector_native import DocStructureVannaNative
            
            # Инициализация
            print(f"📤 Инициализируем {model_name}...")
            start_time = time.time()
            vanna = DocStructureVannaNative(config)
            init_time = time.time()
            print(f"✅ Инициализирован за {init_time - start_time:.2f} сек")
            
            success_count = 0
            total_quality = 0
            
            for i, question in enumerate(self.test_questions, 1):
                print(f"\n❓ Вопрос {i}: {question}")
                
                try:
                    start_time = time.time()
                    sql = vanna.generate_sql(question)
                    end_time = time.time()
                    
                    response_time = end_time - start_time
                    model_results['total_time'] += response_time
                    
                    print(f"✅ SQL сгенерирован за {response_time:.2f} сек")
                    print(f"💡 SQL: {sql}")
                    
                    # Анализ качества SQL
                    quality = self.analyze_sql_quality(question, sql)
                    total_quality += quality
                    
                    model_results['questions'][question] = {
                        'sql': sql,
                        'time': response_time,
                        'quality': quality,
                        'status': 'success'
                    }
                    
                    success_count += 1
                    print(f"📊 Качество: {quality}/10")
                    
                except Exception as e:
                    print(f"❌ Ошибка: {e}")
                    model_results['questions'][question] = {
                        'sql': f"Ошибка: {e}",
                        'time': 0,
                        'quality': 0,
                        'status': 'error'
                    }
            
            # Подсчет метрик
            model_results['success_rate'] = success_count / len(self.test_questions)
            model_results['quality_score'] = total_quality / len(self.test_questions) if success_count > 0 else 0
            model_results['avg_time'] = model_results['total_time'] / len(self.test_questions)
            
            print(f"\n📊 Результаты {model_name}:")
            print(f"   Успешность: {model_results['success_rate']:.2f}")
            print(f"   Качество: {model_results['quality_score']:.2f}/10")
            print(f"   Среднее время: {model_results['avg_time']:.2f} сек")
            
            return model_results
            
        except Exception as e:
            print(f"❌ Критическая ошибка с {model_name}: {e}")
            return {
                'model': model_name,
                'error': str(e),
                'success_rate': 0,
                'quality_score': 0,
                'avg_time': 0
            }
    
    def analyze_sql_quality(self, question, sql):
        """Анализ качества SQL запроса"""
        quality = 0
        
        # Проверяем наличие правильных таблиц
        if "пользовател" in question.lower():
            if "equsers" in sql.lower():
                quality += 4
            elif "users" in sql.lower():
                quality += 2
        
        elif "отдел" in question.lower():
            if "eq_departments" in sql.lower():
                quality += 4
            elif "department" in sql.lower():
                quality += 2
        
        elif "клиент" in question.lower():
            if "tbl_business_unit" in sql.lower():
                quality += 4
            elif "client" in sql.lower() or "customer" in sql.lower():
                quality += 2
        
        # Проверяем синтаксис SQL
        if sql.strip().upper().startswith('SELECT'):
            quality += 2
        
        # Проверяем наличие WHERE для фильтрации
        if 'WHERE' in sql.upper() and 'deleted' in sql.lower():
            quality += 2
        
        # Проверяем JOIN для сложных запросов
        if "по отделам" in question.lower() and 'JOIN' in sql.upper():
            quality += 2
        
        return min(quality, 10)  # Максимум 10 баллов
    
    def run_comparison(self):
        """Запуск сравнения всех моделей"""
        print("🚀 Продвинутое сравнение LLM моделей")
        print("=" * 60)
        print(f"📅 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Конфигурации моделей
        models_config = {
            'GPT-4o': {
                'model': 'gpt-4o',
                'database_url': 'postgresql://postgres:1234@localhost:5432/test_docstructure',
                'api_key': 'sk-xF20r7G4tq9ezBMNKIjCPvva2io4S8FV',
                'base_url': 'https://api.proxyapi.ru/openai/v1'
            },
            'Ollama Llama 3': {
                'model': 'llama3:latest',
                'database_url': 'postgresql://postgres:1234@localhost:5432/test_docstructure',
                'api_key': 'ollama',
                'base_url': 'http://localhost:11434/v1'
            },
            'Qwen2.5:1.5b': {
                'model': 'qwen2.5:1.5b',
                'database_url': 'postgresql://postgres:1234@localhost:5432/test_docstructure',
                'api_key': 'ollama',
                'base_url': 'http://localhost:11434/v1'
            },
            'SQLCoder:latest': {
                'model': 'sqlcoder:latest',
                'database_url': 'postgresql://postgres:1234@localhost:5432/test_docstructure',
                'api_key': 'ollama',
                'base_url': 'http://localhost:11434/v1'
            },
            'Phi3:latest': {
                'model': 'phi3:latest',
                'database_url': 'postgresql://postgres:1234@localhost:5432/test_docstructure',
                'api_key': 'ollama',
                'base_url': 'http://localhost:11434/v1'
            }
        }
        
        # Тестируем каждую модель
        for model_name, config in models_config.items():
            try:
                result = self.test_model(model_name, config)
                self.results[model_name] = result
            except Exception as e:
                print(f"❌ Пропускаем {model_name}: {e}")
                continue
        
        # Сохраняем результаты
        self.save_results()
        
        # Выводим итоговый рейтинг
        self.print_ranking()
    
    def save_results(self):
        """Сохранение результатов в файл"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"model_comparison_results_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        print(f"\n📊 Результаты сохранены в {filename}")
    
    def print_ranking(self):
        """Вывод итогового рейтинга"""
        print(f"\n🏆 ИТОГОВЫЙ РЕЙТИНГ МОДЕЛЕЙ")
        print("=" * 60)
        
        # Сортируем модели по качеству
        ranking = []
        for model_name, result in self.results.items():
            if 'error' not in result:
                score = result['quality_score'] * result['success_rate']
                ranking.append((model_name, score, result))
        
        ranking.sort(key=lambda x: x[1], reverse=True)
        
        for i, (model_name, score, result) in enumerate(ranking, 1):
            print(f"{i}. {model_name}")
            print(f"   Качество: {result['quality_score']:.2f}/10")
            print(f"   Успешность: {result['success_rate']:.2f}")
            print(f"   Среднее время: {result['avg_time']:.2f} сек")
            print(f"   Общий балл: {score:.2f}")
            print()

def main():
    """Главная функция"""
    tester = ModelTester()
    tester.run_comparison()

if __name__ == "__main__":
    main()
