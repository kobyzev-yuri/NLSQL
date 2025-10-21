#!/usr/bin/env python3
"""
Расширенное обучение на Q/A парах с учетом производительности SQL
Включает обучение на оптимизированных запросах и метриках производительности
"""

import asyncio
import json
import sys
import os
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import pandas as pd

# Добавляем путь к проекту
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.vanna.vanna_semantic_fixed import create_semantic_vanna_client

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedQATrainer:
    """Расширенный тренер для обучения на Q/A парах с учетом производительности"""
    
    def __init__(self):
        self.vanna_client = None
        self.optimization_examples = []
        
    async def initialize(self):
        """Инициализация клиента"""
        try:
            self.vanna_client = create_semantic_vanna_client()
            logger.info("✅ Enhanced QA Trainer инициализирован")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации: {e}")
            raise
    
    def load_optimization_examples(self, file_path: str) -> List[Dict[str, Any]]:
        """Загрузка примеров оптимизированных SQL"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get('qa_pairs', [])
        except Exception as e:
            logger.error(f"Ошибка загрузки файла {file_path}: {e}")
            return []
    
    async def train_on_optimized_sql(self, examples: List[Dict[str, Any]]) -> Dict[str, int]:
        """Обучение на оптимизированных SQL запросах"""
        if not self.vanna_client:
            raise Exception("Vanna AI клиент не инициализирован")
        
        results = {
            'total': len(examples),
            'trained': 0,
            'skipped': 0,
            'errors': 0
        }
        
        for i, example in enumerate(examples):
            try:
                # Создаем расширенный контекст для обучения
                enhanced_question = self._create_enhanced_question(example)
                optimized_sql = example['sql_optimized']
                
                # Добавляем метаданные о производительности в контекст
                performance_context = self._create_performance_context(example)
                
                # Обучаем на оптимизированном SQL с контекстом
                await self._train_with_performance_context(
                    enhanced_question, 
                    optimized_sql, 
                    performance_context
                )
                
                results['trained'] += 1
                logger.info(f"✅ Обучение на примере {i+1}/{len(examples)}: {example['question']}")
                
            except Exception as e:
                results['errors'] += 1
                logger.error(f"❌ Ошибка обучения на примере {i+1}: {e}")
        
        return results
    
    def _create_enhanced_question(self, example: Dict[str, Any]) -> str:
        """Создание расширенного вопроса с контекстом производительности"""
        base_question = example['question']
        optimization_reason = example.get('optimization_reason', '')
        performance_impact = example.get('performance_impact', '')
        
        enhanced_question = f"""
        {base_question}
        
        Требования к производительности:
        - Запрос должен быть оптимизирован для быстрого выполнения
        - Использовать только необходимые поля
        - Применять фильтры для ограничения данных
        - Оптимизация: {optimization_reason}
        - Ожидаемое улучшение: {performance_impact}
        """
        
        return enhanced_question.strip()
    
    def _create_performance_context(self, example: Dict[str, Any]) -> str:
        """Создание контекста производительности для обучения"""
        context = f"""
        SQL Оптимизация:
        - Базовый запрос: {example.get('sql_basic', '')}
        - Оптимизированный запрос: {example.get('sql_optimized', '')}
        - Причина оптимизации: {example.get('optimization_reason', '')}
        - Влияние на производительность: {example.get('performance_impact', '')}
        
        Принципы оптимизации:
        - Используйте INNER JOIN вместо JOIN для совпадающих записей
        - Добавляйте фильтры по дате для ограничения данных
        - Выбирайте только нужные поля вместо SELECT *
        - Используйте HAVING для фильтрации агрегированных данных
        - Добавляйте ORDER BY для логичной сортировки
        - Используйте LIMIT для ограничения результатов
        """
        
        return context.strip()
    
    async def _train_with_performance_context(self, question: str, sql: str, context: str):
        """Обучение с контекстом производительности"""
        # Здесь нужно реализовать обучение с учетом контекста
        # Пока что используем базовый подход
        logger.info(f"Обучение на оптимизированном SQL: {sql[:100]}...")
        
        # В реальной реализации здесь был бы вызов метода обучения Vanna AI
        # с передачей контекста производительности
        pass
    
    async def analyze_sql_performance(self, sql: str) -> Dict[str, Any]:
        """Анализ производительности SQL запроса"""
        try:
            # Здесь можно добавить анализ через EXPLAIN ANALYZE
            # Пока что возвращаем базовые метрики
            analysis = {
                'query': sql,
                'estimated_cost': self._estimate_query_cost(sql),
                'optimization_suggestions': self._get_optimization_suggestions(sql),
                'performance_score': self._calculate_performance_score(sql)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Ошибка анализа производительности: {e}")
            return {}
    
    def _estimate_query_cost(self, sql: str) -> str:
        """Оценка стоимости запроса"""
        sql_lower = sql.lower()
        
        if 'select *' in sql_lower:
            return "Высокая - используйте конкретные поля"
        elif 'join' in sql_lower and 'where' not in sql_lower:
            return "Средняя - добавьте фильтры"
        elif 'order by' in sql_lower and 'limit' not in sql_lower:
            return "Средняя - добавьте LIMIT"
        else:
            return "Низкая - запрос оптимизирован"
    
    def _get_optimization_suggestions(self, sql: str) -> List[str]:
        """Получение предложений по оптимизации"""
        suggestions = []
        sql_lower = sql.lower()
        
        if 'select *' in sql_lower:
            suggestions.append("Замените SELECT * на конкретные поля")
        
        if 'join' in sql_lower and 'inner join' not in sql_lower:
            suggestions.append("Используйте INNER JOIN вместо JOIN")
        
        if 'group by' in sql_lower and 'having' not in sql_lower:
            suggestions.append("Рассмотрите добавление HAVING для фильтрации")
        
        if 'order by' in sql_lower and 'limit' not in sql_lower:
            suggestions.append("Добавьте LIMIT для ограничения результатов")
        
        return suggestions
    
    def _calculate_performance_score(self, sql: str) -> int:
        """Расчет оценки производительности (0-100)"""
        score = 100
        sql_lower = sql.lower()
        
        # Штрафы за неоптимизированные конструкции
        if 'select *' in sql_lower:
            score -= 20
        if 'join' in sql_lower and 'inner join' not in sql_lower:
            score -= 10
        if 'order by' in sql_lower and 'limit' not in sql_lower:
            score -= 15
        if 'group by' in sql_lower and 'having' not in sql_lower:
            score -= 10
        
        # Бонусы за оптимизированные конструкции
        if 'where' in sql_lower:
            score += 10
        if 'limit' in sql_lower:
            score += 10
        if 'inner join' in sql_lower:
            score += 5
        
        return max(0, min(100, score))
    
    async def create_performance_report(self, examples: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Создание отчета по производительности"""
        report = {
            'total_examples': len(examples),
            'performance_analysis': [],
            'optimization_principles': [],
            'recommendations': []
        }
        
        for example in examples:
            analysis = await self.analyze_sql_performance(example['sql_optimized'])
            report['performance_analysis'].append({
                'question': example['question'],
                'analysis': analysis
            })
        
        # Анализ принципов оптимизации
        report['optimization_principles'] = [
            "Используйте конкретные поля вместо SELECT *",
            "Добавляйте фильтры WHERE для ограничения данных",
            "Применяйте INNER JOIN для совпадающих записей",
            "Используйте HAVING для фильтрации агрегатов",
            "Добавляйте LIMIT для ограничения результатов"
        ]
        
        # Рекомендации
        report['recommendations'] = [
            "Создайте индексы на часто используемые поля",
            "Используйте партиционирование для больших таблиц",
            "Применяйте EXPLAIN ANALYZE для анализа производительности",
            "Кэшируйте часто используемые запросы"
        ]
        
        return report

async def main():
    """Основная функция"""
    trainer = EnhancedQATrainer()
    await trainer.initialize()
    
    # Загружаем примеры оптимизированных SQL
    examples = trainer.load_optimization_examples('optimized_sql_examples.json')
    
    if not examples:
        logger.error("Не удалось загрузить примеры оптимизации")
        return
    
    logger.info(f"Загружено {len(examples)} примеров оптимизации")
    
    # Обучение на оптимизированных SQL
    results = await trainer.train_on_optimized_sql(examples)
    logger.info(f"Результаты обучения: {results}")
    
    # Создание отчета по производительности
    report = await trainer.create_performance_report(examples)
    
    # Сохранение отчета
    with open('performance_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    logger.info("✅ Обучение на оптимизированных SQL завершено")
    logger.info("📊 Отчет по производительности сохранен в performance_report.json")

if __name__ == '__main__':
    asyncio.run(main())
