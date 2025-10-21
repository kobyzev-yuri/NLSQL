#!/usr/bin/env python3
"""
Скрипт для управления Q/A парами и дообучения векторки
Автоматизирует процесс добавления, валидации и обучения на новых данных
"""

import asyncio
import json
import sys
import os
import argparse
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import pandas as pd

# Добавляем путь к проекту
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.vanna.vanna_semantic_fixed import create_semantic_vanna_client
from src.services.query_service import QueryService

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class QAManager:
    """Менеджер для работы с Q/A парами и дообучения векторки"""
    
    def __init__(self):
        self.vanna_client = None
        self.query_service = None
        self.qa_data = []
        
    async def initialize(self):
        """Инициализация клиентов"""
        try:
            self.vanna_client = create_semantic_vanna_client()
            self.query_service = QueryService()
            logger.info("✅ Клиенты инициализированы")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации: {e}")
            raise
    
    def load_qa_from_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Загрузка Q/A пар из файла"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and 'qa_pairs' in data:
                return data['qa_pairs']
            else:
                logger.error("Неверный формат файла")
                return []
                
        except Exception as e:
            logger.error(f"Ошибка загрузки файла {file_path}: {e}")
            return []
    
    def validate_qa_pair(self, qa_pair: Dict[str, Any]) -> bool:
        """Валидация Q/A пары"""
        required_fields = ['question', 'sql']
        
        for field in required_fields:
            if field not in qa_pair or not qa_pair[field]:
                logger.warning(f"Отсутствует поле {field} в Q/A паре")
                return False
        
        # Проверка SQL
        sql = qa_pair['sql'].strip().upper()
        if not sql.startswith('SELECT'):
            logger.warning("SQL должен начинаться с SELECT")
            return False
        
        return True
    
    async def add_qa_pairs(self, qa_pairs: List[Dict[str, Any]], validate: bool = True) -> Dict[str, int]:
        """Добавление Q/A пар в векторку"""
        if not self.vanna_client:
            raise Exception("Vanna AI клиент не инициализирован")
        
        results = {
            'total': len(qa_pairs),
            'added': 0,
            'skipped': 0,
            'errors': 0
        }
        
        for i, qa_pair in enumerate(qa_pairs):
            try:
                if validate and not self.validate_qa_pair(qa_pair):
                    results['skipped'] += 1
                    continue
                
                # Добавляем в векторку
                self.vanna_client.add_question_sql(
                    qa_pair['question'], 
                    qa_pair['sql']
                )
                
                results['added'] += 1
                logger.info(f"✅ Добавлена Q/A пара {i+1}/{len(qa_pairs)}")
                
            except Exception as e:
                results['errors'] += 1
                logger.error(f"❌ Ошибка добавления Q/A пары {i+1}: {e}")
        
        return results
    
    async def test_qa_quality(self, qa_pairs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Тестирование качества Q/A пар"""
        if not self.query_service:
            raise Exception("QueryService не инициализирован")
        
        results = {
            'total_tests': len(qa_pairs),
            'successful': 0,
            'failed': 0,
            'avg_time': 0,
            'details': []
        }
        
        total_time = 0
        
        for i, qa_pair in enumerate(qa_pairs):
            try:
                start_time = time.time()
                
                # Генерируем SQL для вопроса
                generated_sql = await self.query_service.generate_sql(
                    qa_pair['question'], 
                    {}
                )
                
                end_time = time.time()
                test_time = end_time - start_time
                total_time += test_time
                
                # Простая проверка качества (можно улучшить)
                is_successful = self._compare_sql_quality(
                    qa_pair['sql'], 
                    generated_sql
                )
                
                if is_successful:
                    results['successful'] += 1
                else:
                    results['failed'] += 1
                
                results['details'].append({
                    'question': qa_pair['question'],
                    'expected_sql': qa_pair['sql'],
                    'generated_sql': generated_sql,
                    'time': test_time,
                    'success': is_successful
                })
                
                logger.info(f"Тест {i+1}/{len(qa_pairs)}: {'✅' if is_successful else '❌'}")
                
            except Exception as e:
                results['failed'] += 1
                logger.error(f"Ошибка тестирования Q/A пары {i+1}: {e}")
        
        results['avg_time'] = total_time / len(qa_pairs) if qa_pairs else 0
        return results
    
    def _compare_sql_quality(self, expected: str, generated: str) -> bool:
        """Простое сравнение качества SQL (можно улучшить)"""
        # Нормализация SQL
        expected_norm = expected.strip().upper().replace(' ', '')
        generated_norm = generated.strip().upper().replace(' ', '')
        
        # Проверяем основные ключевые слова
        expected_keywords = set(expected_norm.split())
        generated_keywords = set(generated_norm.split())
        
        # Если пересечение ключевых слов больше 70%, считаем успешным
        intersection = expected_keywords.intersection(generated_keywords)
        union = expected_keywords.union(generated_keywords)
        
        similarity = len(intersection) / len(union) if union else 0
        return similarity > 0.7
    
    async def generate_embeddings(self):
        """Генерация эмбеддингов для новых данных"""
        try:
            from src.tools.generate_embeddings_hf import main as generate_embeddings_func
            generate_embeddings_func()
            logger.info("✅ Эмбеддинги сгенерированы")
        except Exception as e:
            logger.error(f"❌ Ошибка генерации эмбеддингов: {e}")
            raise
    
    def export_qa_pairs(self, output_file: str, format: str = 'json'):
        """Экспорт Q/A пар"""
        try:
            if format == 'json':
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(self.qa_data, f, indent=2, ensure_ascii=False)
            elif format == 'csv':
                df = pd.DataFrame(self.qa_data)
                df.to_csv(output_file, index=False, encoding='utf-8')
            
            logger.info(f"✅ Q/A пары экспортированы в {output_file}")
        except Exception as e:
            logger.error(f"❌ Ошибка экспорта: {e}")
    
    def create_qa_template(self, output_file: str):
        """Создание шаблона для Q/A пар"""
        template = {
            "qa_pairs": [
                {
                    "question": "Покажи всех пользователей системы",
                    "sql": "SELECT * FROM equsers WHERE deleted = FALSE",
                    "category": "users",
                    "difficulty": "easy"
                },
                {
                    "question": "Поручения за последний месяц",
                    "sql": "SELECT * FROM tbl_principal_assignment WHERE creationdatetime >= CURRENT_DATE - INTERVAL '1 month'",
                    "category": "assignments", 
                    "difficulty": "medium"
                }
            ],
            "metadata": {
                "created": "2025-01-01",
                "version": "1.0",
                "description": "Q/A пары для обучения векторки"
            }
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(template, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Шаблон создан: {output_file}")

async def main():
    """Основная функция"""
    parser = argparse.ArgumentParser(description="Управление Q/A парами и дообучение векторки")
    parser.add_argument('--action', choices=['add', 'test', 'export', 'template', 'embeddings', 'optimize', 'performance'], 
                       required=True, help="Действие для выполнения")
    parser.add_argument('--input', help="Входной файл с Q/A парами")
    parser.add_argument('--output', help="Выходной файл")
    parser.add_argument('--validate', action='store_true', help="Валидация Q/A пар")
    parser.add_argument('--format', choices=['json', 'csv'], default='json', help="Формат файла")
    
    args = parser.parse_args()
    
    # Инициализация менеджера
    manager = QAManager()
    await manager.initialize()
    
    if args.action == 'add':
        if not args.input:
            logger.error("Не указан входной файл")
            return
        
        qa_pairs = manager.load_qa_from_file(args.input)
        if not qa_pairs:
            logger.error("Не удалось загрузить Q/A пары")
            return
        
        results = await manager.add_qa_pairs(qa_pairs, args.validate)
        logger.info(f"Результаты добавления: {results}")
        
        # Генерируем эмбеддинги
        await manager.generate_embeddings()
        
    elif args.action == 'test':
        if not args.input:
            logger.error("Не указан входной файл")
            return
        
        qa_pairs = manager.load_qa_from_file(args.input)
        if not qa_pairs:
            logger.error("Не удалось загрузить Q/A пары")
            return
        
        results = await manager.test_qa_quality(qa_pairs)
        logger.info(f"Результаты тестирования: {results}")
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
        
    elif args.action == 'export':
        if not args.output:
            logger.error("Не указан выходной файл")
            return
        
        manager.export_qa_pairs(args.output, args.format)
        
    elif args.action == 'template':
        output_file = args.output or 'qa_template.json'
        manager.create_qa_template(output_file)
        
    elif args.action == 'embeddings':
        await manager.generate_embeddings()
        
    elif args.action == 'optimize':
        if not args.input:
            logger.error("Не указан входной файл с оптимизированными примерами")
            return
        
        # Загружаем примеры оптимизации
        from enhanced_qa_training import EnhancedQATrainer
        trainer = EnhancedQATrainer()
        await trainer.initialize()
        
        examples = trainer.load_optimization_examples(args.input)
        if not examples:
            logger.error("Не удалось загрузить примеры оптимизации")
            return
        
        # Обучение на оптимизированных SQL
        results = await trainer.train_on_optimized_sql(examples)
        logger.info(f"Результаты обучения на оптимизации: {results}")
        
        # Создание отчета по производительности
        report = await trainer.create_performance_report(examples)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            logger.info(f"Отчет по производительности сохранен: {args.output}")
        
    elif args.action == 'performance':
        if not args.input:
            logger.error("Не указан входной файл")
            return
        
        # Анализ производительности SQL запросов
        from enhanced_qa_training import EnhancedQATrainer
        trainer = EnhancedQATrainer()
        await trainer.initialize()
        
        examples = trainer.load_optimization_examples(args.input)
        if not examples:
            logger.error("Не удалось загрузить примеры")
            return
        
        # Создание отчета по производительности
        report = await trainer.create_performance_report(examples)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            logger.info(f"Отчет по производительности сохранен: {args.output}")
        else:
            # Выводим краткий отчет в консоль
            logger.info("📊 Анализ производительности SQL:")
            for analysis in report['performance_analysis']:
                logger.info(f"Вопрос: {analysis['question']}")
                logger.info(f"Оценка производительности: {analysis['analysis'].get('performance_score', 'N/A')}")
                logger.info(f"Стоимость запроса: {analysis['analysis'].get('estimated_cost', 'N/A')}")
                logger.info("---")

if __name__ == '__main__':
    import time
    asyncio.run(main())
