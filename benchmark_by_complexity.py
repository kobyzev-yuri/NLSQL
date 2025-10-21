#!/usr/bin/env python3
"""
Бенчмарк SQL по сложности на реальных данных из векторки
Использует Q/A пары из training_data/sql_examples.json
"""

import json
import os
from typing import List, Dict, Any, Tuple
from sql_metrics_calculator import SQLMetricsCalculator

class ComplexityBenchmark:
    """Бенчмарк по сложности SQL запросов"""
    
    def __init__(self, project_root: str = "/mnt/ai/cnn/sql4A"):
        self.project_root = project_root
        self.sql_examples_path = os.path.join(project_root, "training_data", "sql_examples.json")
        self.calculator = SQLMetricsCalculator()
        
    def load_real_qa_pairs(self) -> List[Dict[str, str]]:
        """Загружает реальные Q/A пары из векторки"""
        if not os.path.exists(self.sql_examples_path):
            raise FileNotFoundError(f"Файл {self.sql_examples_path} не найден")
        
        with open(self.sql_examples_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def classify_by_complexity(self, qa_pairs: List[Dict[str, str]]) -> Dict[str, List[Dict[str, str]]]:
        """Классифицирует Q/A пары по сложности"""
        
        complexity_groups = {
            "Простые": [],      # Простые SELECT без JOIN
            "Средние": [],      # С JOIN, но без агрегации
            "Сложные": []       # С агрегацией, GROUP BY, сложной логикой
        }
        
        for qa in qa_pairs:
            sql = qa['sql'].upper()
            
            # Анализ сложности
            has_join = 'JOIN' in sql
            has_aggregation = any(func in sql for func in ['COUNT', 'SUM', 'AVG', 'MAX', 'MIN'])
            has_group_by = 'GROUP BY' in sql
            has_order_by = 'ORDER BY' in sql
            has_where = 'WHERE' in sql
            
            # Классификация
            if has_aggregation or has_group_by:
                complexity_groups["Сложные"].append(qa)
            elif has_join:
                complexity_groups["Средние"].append(qa)
            else:
                complexity_groups["Простые"].append(qa)
        
        return complexity_groups
    
    def simulate_generated_sql(self, reference_sql: str, complexity: str) -> str:
        """Симулирует сгенерированный SQL с типичными ошибками для каждой сложности"""
        
        if complexity == "Простые":
            # Типичные ошибки простых запросов
            generated = reference_sql
            # Убираем WHERE условия
            if 'WHERE' in generated:
                generated = generated.split('WHERE')[0].strip()
            # Упрощаем SELECT
            if 'SELECT' in generated and '*' not in generated:
                select_part = generated.split('FROM')[0]
                if 'SELECT' in select_part:
                    generated = generated.replace(select_part, 'SELECT *')
        
        elif complexity == "Средние":
            # Типичные ошибки средних запросов
            generated = reference_sql
            # Упрощаем JOIN
            generated = generated.replace('LEFT JOIN', 'JOIN')
            generated = generated.replace('INNER JOIN', 'JOIN')
            # Убираем некоторые условия
            if 'WHERE' in generated:
                generated = generated.replace('WHERE u.deleted = false', '')
                generated = generated.replace('WHERE deleted = false', '')
        
        elif complexity == "Сложные":
            # Типичные ошибки сложных запросов
            generated = reference_sql
            # Убираем ORDER BY
            if 'ORDER BY' in generated:
                generated = generated.split('ORDER BY')[0].strip()
            # Упрощаем агрегацию
            if 'SUM(' in generated:
                generated = generated.replace('SUM(ip.amount)', 'ip.amount')
            if 'COUNT(' in generated:
                generated = generated.replace('COUNT(u.id)', 'u.id')
            # Убираем GROUP BY
            if 'GROUP BY' in generated:
                generated = generated.split('GROUP BY')[0].strip()
        
        return generated.strip()
    
    def evaluate_complexity_group(self, group_name: str, qa_pairs: List[Dict[str, str]]) -> Dict[str, Any]:
        """Оценивает группу запросов по сложности"""
        
        print(f"\n🔍 Оценка группы: {group_name}")
        print(f"Количество запросов: {len(qa_pairs)}")
        
        if not qa_pairs:
            return {
                'group': group_name,
                'count': 0,
                'precision': 0.0,
                'recall': 0.0,
                'details': []
            }
        
        total_precision = 0.0
        total_recall = 0.0
        details = []
        
        for i, qa in enumerate(qa_pairs):
            question = qa['question']
            reference_sql = qa['sql']
            generated_sql = self.simulate_generated_sql(reference_sql, group_name)
            
            print(f"\n  {i+1}. {question}")
            print(f"     Эталонный: {reference_sql[:100]}...")
            print(f"     Сгенерированный: {generated_sql[:100]}...")
            
            try:
                metrics = self.calculator.calculate_metrics(reference_sql, generated_sql)
                
                precision = metrics['precision']
                recall = metrics['recall']
                
                total_precision += precision
                total_recall += recall
                
                details.append({
                    'question': question,
                    'reference_sql': reference_sql,
                    'generated_sql': generated_sql,
                    'precision': precision,
                    'recall': recall
                })
                
                print(f"     Precision: {precision:.3f}, Recall: {recall:.3f}")
                
            except Exception as e:
                print(f"     ❌ Ошибка: {e}")
                continue
        
        # Средние метрики
        avg_precision = total_precision / len(details) if details else 0.0
        avg_recall = total_recall / len(details) if details else 0.0
        
        print(f"\n📊 Итоги для {group_name}:")
        print(f"  Средняя Precision: {avg_precision:.3f}")
        print(f"  Средняя Recall: {avg_recall:.3f}")
        
        return {
            'group': group_name,
            'count': len(details),
            'precision': avg_precision,
            'recall': avg_recall,
            'details': details
        }
    
    def run_benchmark(self) -> Dict[str, Any]:
        """Запускает полный бенчмарк по сложности"""
        
        print("🎯 Бенчмарк SQL по сложности")
        print("=" * 50)
        
        # Загружаем реальные данные
        print("📂 Загрузка Q/A пар из векторки...")
        qa_pairs = self.load_real_qa_pairs()
        print(f"Найдено {len(qa_pairs)} Q/A пар")
        
        # Классифицируем по сложности
        print("\n🔍 Классификация по сложности...")
        complexity_groups = self.classify_by_complexity(qa_pairs)
        
        for group_name, pairs in complexity_groups.items():
            print(f"  {group_name}: {len(pairs)} запросов")
        
        # Оцениваем каждую группу
        results = {}
        
        for group_name, qa_pairs in complexity_groups.items():
            group_results = self.evaluate_complexity_group(group_name, qa_pairs)
            results[group_name] = group_results
        
        # Итоговые результаты
        print("\n" + "=" * 50)
        print("📊 ИТОГОВЫЕ РЕЗУЛЬТАТЫ БЕНЧМАРКА")
        print("=" * 50)
        
        for group_name, result in results.items():
            print(f"\n{group_name}:")
            print(f"  Запросов: {result['count']}")
            print(f"  Precision: {result['precision']:.3f}")
            print(f"  Recall: {result['recall']:.3f}")
        
        return {
            'complexity_groups': results,
            'total_qa_pairs': len(qa_pairs),
            'summary': {
                'simple_count': results.get('Простые', {}).get('count', 0),
                'medium_count': results.get('Средние', {}).get('count', 0),
                'complex_count': results.get('Сложные', {}).get('count', 0)
            }
        }
    
    def save_results(self, results: Dict[str, Any], filename: str = "complexity_benchmark_results.json"):
        """Сохраняет результаты бенчмарка"""
        output_path = os.path.join(self.project_root, filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Результаты сохранены в {output_path}")

def main():
    """Основная функция бенчмарка"""
    benchmark = ComplexityBenchmark()
    
    try:
        results = benchmark.run_benchmark()
        benchmark.save_results(results)
        
        print("\n✅ Бенчмарк завершен успешно!")
        
    except Exception as e:
        print(f"\n❌ Ошибка бенчмарка: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
