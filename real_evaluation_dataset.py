#!/usr/bin/env python3
"""
Реальный датасет для оценки качества SQL
Использует существующие данные из проекта
"""

import json
import os
from typing import List, Dict, Any
from sql_metrics_calculator import SQLMetricsCalculator

class RealEvaluationDataset:
    """Реальный датасет для оценки качества SQL"""
    
    def __init__(self, project_root: str = "/mnt/ai/cnn/sql4A"):
        self.project_root = project_root
        self.training_data_path = os.path.join(project_root, "training_data")
        self.sql_examples_path = os.path.join(self.training_data_path, "sql_examples.json")
        self.enhanced_examples_path = os.path.join(self.training_data_path, "enhanced_sql_examples.json")
        
    def load_real_sql_examples(self) -> List[Dict[str, str]]:
        """Загружает реальные SQL примеры из проекта"""
        examples = []
        
        # Загружаем основные примеры
        if os.path.exists(self.sql_examples_path):
            with open(self.sql_examples_path, 'r', encoding='utf-8') as f:
                examples.extend(json.load(f))
        
        # Загружаем расширенные примеры
        if os.path.exists(self.enhanced_examples_path):
            with open(self.enhanced_examples_path, 'r', encoding='utf-8') as f:
                examples.extend(json.load(f))
        
        return examples
    
    def create_evaluation_pairs(self) -> List[Dict[str, Any]]:
        """Создает пары для оценки: эталонный SQL vs сгенерированный SQL"""
        examples = self.load_real_sql_examples()
        
        evaluation_pairs = []
        
        for example in examples:
            # Эталонный SQL (из данных)
            reference_sql = example.get('sql', '').strip()
            question = example.get('question', '')
            
            if not reference_sql or not question:
                continue
            
            # Создаем "сгенерированный" SQL с небольшими изменениями
            # (симулируем ошибки генерации)
            generated_sql = self._simulate_generated_sql(reference_sql)
            
            evaluation_pairs.append({
                'question': question,
                'reference_sql': reference_sql,
                'generated_sql': generated_sql,
                'source': 'real_training_data'
            })
        
        return evaluation_pairs
    
    def _simulate_generated_sql(self, reference_sql: str) -> str:
        """Симулирует сгенерированный SQL с типичными ошибками"""
        generated = reference_sql
        
        # Типичные ошибки генерации:
        # 1. Убираем некоторые условия
        if 'WHERE' in generated:
            generated = generated.replace('WHERE deleted = false', '')
            generated = generated.replace('WHERE deleted = FALSE', '')
        
        # 2. Упрощаем JOIN
        generated = generated.replace('LEFT JOIN', 'JOIN')
        generated = generated.replace('INNER JOIN', 'JOIN')
        
        # 3. Убираем ORDER BY
        if 'ORDER BY' in generated:
            generated = generated.split('ORDER BY')[0].strip()
        
        # 4. Убираем GROUP BY
        if 'GROUP BY' in generated:
            generated = generated.split('GROUP BY')[0].strip()
        
        # 5. Упрощаем SELECT
        if 'SELECT' in generated and '*' not in generated:
            # Заменяем конкретные поля на *
            select_part = generated.split('FROM')[0]
            if 'SELECT' in select_part:
                generated = generated.replace(select_part, 'SELECT *')
        
        return generated.strip()
    
    def evaluate_real_dataset(self) -> Dict[str, Any]:
        """Оценивает качество на реальном датасете"""
        print("🔍 Загрузка реального датасета...")
        
        evaluation_pairs = self.create_evaluation_pairs()
        
        if not evaluation_pairs:
            return {
                'error': 'Нет данных для оценки',
                'total_pairs': 0
            }
        
        print(f"📊 Найдено {len(evaluation_pairs)} пар для оценки")
        
        # Инициализируем калькулятор метрик
        calculator = SQLMetricsCalculator()
        
        # Оцениваем каждую пару
        results = []
        total_precision = 0
        total_recall = 0
        total_f1 = 0
        
        for i, pair in enumerate(evaluation_pairs):
            print(f"\n📝 Пара {i+1}/{len(evaluation_pairs)}: {pair['question'][:50]}...")
            
            try:
                metrics = calculator.calculate_metrics(
                    pair['reference_sql'], 
                    pair['generated_sql']
                )
                
                results.append({
                    'question': pair['question'],
                    'reference_sql': pair['reference_sql'],
                    'generated_sql': pair['generated_sql'],
                    'metrics': metrics
                })
                
                total_precision += metrics['precision']
                total_recall += metrics['recall']
                total_f1 += metrics['f1_score']
                
                print(f"   Precision: {metrics['precision']:.3f}")
                print(f"   Recall: {metrics['recall']:.3f}")
                print(f"   F1-Score: {metrics['f1_score']:.3f}")
                
            except Exception as e:
                print(f"   ❌ Ошибка: {e}")
                continue
        
        # Средние метрики
        avg_precision = total_precision / len(results) if results else 0
        avg_recall = total_recall / len(results) if results else 0
        avg_f1 = total_f1 / len(results) if results else 0
        
        return {
            'total_pairs': len(evaluation_pairs),
            'evaluated_pairs': len(results),
            'average_precision': avg_precision,
            'average_recall': avg_recall,
            'average_f1_score': avg_f1,
            'results': results
        }
    
    def save_evaluation_results(self, results: Dict[str, Any], filename: str = "real_evaluation_results.json"):
        """Сохраняет результаты оценки"""
        output_path = os.path.join(self.project_root, filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Результаты сохранены в {output_path}")

def main():
    """Основная функция для оценки на реальном датасете"""
    print("🎯 Оценка качества SQL на реальном датасете")
    print("=" * 50)
    
    # Создаем датасет
    dataset = RealEvaluationDataset()
    
    # Оцениваем
    results = dataset.evaluate_real_dataset()
    
    if 'error' in results:
        print(f"❌ {results['error']}")
        return
    
    # Выводим результаты
    print(f"\n📊 Результаты оценки:")
    print(f"Всего пар: {results['total_pairs']}")
    print(f"Оценено пар: {results['evaluated_pairs']}")
    print(f"Средняя Precision: {results['average_precision']:.3f}")
    print(f"Средняя Recall: {results['average_recall']:.3f}")
    print(f"Средний F1-Score: {results['average_f1_score']:.3f}")
    
    # Сохраняем результаты
    dataset.save_evaluation_results(results)
    
    # Интерпретация
    f1 = results['average_f1_score']
    if f1 >= 0.9:
        quality = "Отличное качество"
    elif f1 >= 0.7:
        quality = "Хорошее качество"
    elif f1 >= 0.5:
        quality = "Удовлетворительное качество"
    else:
        quality = "Плохое качество"
    
    print(f"\n🎯 Оценка качества: {quality}")

if __name__ == '__main__':
    main()
