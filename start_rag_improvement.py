#!/usr/bin/env python3
"""
Скрипт для быстрого старта работ по улучшению RAG
Запускает диагностику и создает baseline метрики
"""

import asyncio
import json
import time
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.services.query_service import QueryService
from src.vanna.vanna_semantic_fixed import create_semantic_vanna_client
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RAGDiagnostic:
    def __init__(self):
        self.results = {
            'timestamp': time.time(),
            'baseline_metrics': {},
            'issues_found': [],
            'recommendations': []
        }
    
    async def run_full_diagnostic(self):
        """Запуск полной диагностики RAG системы"""
        logger.info("🔍 Запуск диагностики RAG системы...")
        
        # 1. Тест семантического поиска
        await self.test_semantic_search()
        
        # 2. Анализ качества контекста
        await self.analyze_context_quality()
        
        # 3. Тест генерации SQL
        await self.test_sql_generation()
        
        # 4. Анализ производительности
        await self.analyze_performance()
        
        # 5. Создание отчета
        self.create_report()
        
        logger.info("✅ Диагностика завершена. Результаты в rag_diagnostic_report.json")
    
    async def test_semantic_search(self):
        """Тест семантического поиска"""
        logger.info("🔍 Тестирование семантического поиска...")
        
        try:
            semantic_client = create_semantic_vanna_client()
            
            test_questions = [
                "покажи пользователей",
                "статистика по отделам", 
                "платежи за месяц"
            ]
            
            search_results = {}
            for question in test_questions:
                logger.info(f"  Тестируем: {question}")
                
                # Тест DDL поиска
                ddl_results = await semantic_client.get_related_ddl(question)
                logger.info(f"    DDL результатов: {len(ddl_results)}")
                
                # Тест документации
                doc_results = await semantic_client.get_related_documentation(question)
                logger.info(f"    Документации: {len(doc_results)}")
                
                # Тест Q&A
                qa_results = await semantic_client.get_similar_question_sql(question)
                logger.info(f"    Q&A пар: {len(qa_results)}")
                
                search_results[question] = {
                    'ddl_count': len(ddl_results),
                    'doc_count': len(doc_results),
                    'qa_count': len(qa_results),
                    'ddl_results': ddl_results[:3],  # Первые 3 результата
                    'doc_results': doc_results[:3],
                    'qa_results': qa_results[:3]
                }
            
            self.results['semantic_search'] = search_results
            
            # Анализ проблем
            total_ddl = sum(r['ddl_count'] for r in search_results.values())
            if total_ddl == 0:
                self.results['issues_found'].append("КРИТИЧНО: DDL поиск не возвращает результатов")
                self.results['recommendations'].append("Исправить семантический поиск DDL")
            
            if total_ddl < len(test_questions):
                self.results['issues_found'].append("ПРОБЛЕМА: DDL поиск работает частично")
                self.results['recommendations'].append("Улучшить качество эмбеддингов для DDL")
                
        except Exception as e:
            logger.error(f"❌ Ошибка тестирования семантического поиска: {e}")
            self.results['issues_found'].append(f"ОШИБКА: Семантический поиск не работает - {e}")
    
    async def analyze_context_quality(self):
        """Анализ качества контекста"""
        logger.info("📊 Анализ качества контекста...")
        
        try:
            query_service = QueryService()
            
            test_questions = [
                "покажи всех пользователей",
                "статистика по отделам",
                "платежи по клиентам"
            ]
            
            context_analysis = {}
            for question in test_questions:
                logger.info(f"  Анализируем контекст для: {question}")
                
                # Генерируем SQL и анализируем контекст
                start_time = time.time()
                sql = await query_service.generate_sql(question, {})
                end_time = time.time()
                
                # Анализ размера контекста (примерная оценка)
                context_size = len(question) + len(sql) + 1000  # Примерная оценка
                
                context_analysis[question] = {
                    'response_time': end_time - start_time,
                    'sql_generated': sql,
                    'context_size_estimate': context_size,
                    'sql_quality': self.analyze_sql_quality(sql)
                }
            
            self.results['context_analysis'] = context_analysis
            
            # Анализ проблем
            avg_response_time = sum(r['response_time'] for r in context_analysis.values()) / len(context_analysis)
            if avg_response_time > 30:
                self.results['issues_found'].append(f"МЕДЛЕННО: Среднее время ответа {avg_response_time:.1f}с")
                self.results['recommendations'].append("Оптимизировать производительность")
            
            avg_context_size = sum(r['context_size_estimate'] for r in context_analysis.values()) / len(context_analysis)
            if avg_context_size > 4000:
                self.results['issues_found'].append(f"БОЛЬШОЙ КОНТЕКСТ: Средний размер {avg_context_size:.0f} токенов")
                self.results['recommendations'].append("Уменьшить размер контекста")
                
        except Exception as e:
            logger.error(f"❌ Ошибка анализа контекста: {e}")
            self.results['issues_found'].append(f"ОШИБКА: Анализ контекста не работает - {e}")
    
    async def test_sql_generation(self):
        """Тест генерации SQL"""
        logger.info("🧪 Тестирование генерации SQL...")
        
        try:
            query_service = QueryService()
            
            test_cases = [
                {
                    'question': 'покажи всех пользователей',
                    'expected_tables': ['equsers'],
                    'expected_complexity': 'simple'
                },
                {
                    'question': 'статистика по отделам',
                    'expected_tables': ['equsers', 'eq_departments'],
                    'expected_complexity': 'complex'
                },
                {
                    'question': 'платежи по клиентам',
                    'expected_tables': ['equsers', 'payments'],
                    'expected_complexity': 'complex'
                }
            ]
            
            sql_test_results = {}
            for test_case in test_cases:
                logger.info(f"  Тестируем: {test_case['question']}")
                
                sql = await query_service.generate_sql(test_case['question'], {})
                
                # Анализ SQL
                sql_analysis = {
                    'sql': sql,
                    'quality_score': self.analyze_sql_quality(sql),
                    'has_expected_tables': self.check_expected_tables(sql, test_case['expected_tables']),
                    'has_invented_tables': self.check_invented_tables(sql),
                    'complexity_match': self.check_complexity(sql, test_case['expected_complexity'])
                }
                
                sql_test_results[test_case['question']] = sql_analysis
                
                logger.info(f"    Качество: {sql_analysis['quality_score']}/5")
                logger.info(f"    Ожидаемые таблицы: {sql_analysis['has_expected_tables']}")
                logger.info(f"    Изобретенные таблицы: {sql_analysis['has_invented_tables']}")
            
            self.results['sql_generation'] = sql_test_results
            
            # Анализ проблем
            invented_tables_count = sum(1 for r in sql_test_results.values() if r['has_invented_tables'])
            if invented_tables_count > 0:
                self.results['issues_found'].append(f"ПРОБЛЕМА: {invented_tables_count} запросов содержат изобретенные таблицы")
                self.results['recommendations'].append("Улучшить поиск DDL и схему БД")
            
            avg_quality = sum(r['quality_score'] for r in sql_test_results.values()) / len(sql_test_results)
            if avg_quality < 5:
                self.results['issues_found'].append(f"НИЗКОЕ КАЧЕСТВО: Средняя оценка {avg_quality:.1f}/5")
                self.results['recommendations'].append("Добавить few-shot примеры и улучшить промпты")
                
        except Exception as e:
            logger.error(f"❌ Ошибка тестирования SQL: {e}")
            self.results['issues_found'].append(f"ОШИБКА: Генерация SQL не работает - {e}")
    
    async def analyze_performance(self):
        """Анализ производительности"""
        logger.info("⚡ Анализ производительности...")
        
        try:
            query_service = QueryService()
            
            # Тест производительности
            test_question = "покажи всех пользователей"
            times = []
            
            for i in range(3):
                start_time = time.time()
                await query_service.generate_sql(test_question, {})
                end_time = time.time()
                times.append(end_time - start_time)
                logger.info(f"  Попытка {i+1}: {times[-1]:.1f}с")
            
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)
            
            self.results['performance'] = {
                'avg_response_time': avg_time,
                'min_response_time': min_time,
                'max_response_time': max_time,
                'all_times': times
            }
            
            # Анализ производительности
            if avg_time > 30:
                self.results['issues_found'].append(f"МЕДЛЕННО: Среднее время {avg_time:.1f}с")
                self.results['recommendations'].append("Оптимизировать производительность")
            
            if max_time - min_time > 20:
                self.results['issues_found'].append("НЕСТАБИЛЬНО: Большой разброс времени ответа")
                self.results['recommendations'].append("Стабилизировать производительность")
                
        except Exception as e:
            logger.error(f"❌ Ошибка анализа производительности: {e}")
            self.results['issues_found'].append(f"ОШИБКА: Анализ производительности не работает - {e}")
    
    def analyze_sql_quality(self, sql):
        """Анализ качества SQL"""
        if not sql or not sql.strip():
            return 0
        
        sql_lower = sql.lower().strip()
        
        # Базовые проверки
        if not sql_lower.startswith('select'):
            return 0
        
        # Штрафы
        penalty = 0
        if 'eqorders' in sql_lower or 'eqpayments' in sql_lower:
            penalty += 1
        
        # Бонусы
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
    
    def check_expected_tables(self, sql, expected_tables):
        """Проверка наличия ожидаемых таблиц"""
        sql_lower = sql.lower()
        return any(table.lower() in sql_lower for table in expected_tables)
    
    def check_invented_tables(self, sql):
        """Проверка на изобретенные таблицы"""
        sql_lower = sql.lower()
        invented_tables = ['eqorders', 'eqpayments', 'payments']
        return any(table in sql_lower for table in invented_tables)
    
    def check_complexity(self, sql, expected_complexity):
        """Проверка соответствия сложности"""
        sql_lower = sql.lower()
        
        if expected_complexity == 'simple':
            return not ('join' in sql_lower or 'group by' in sql_lower)
        elif expected_complexity == 'complex':
            return 'join' in sql_lower or 'group by' in sql_lower
        
        return True
    
    def create_report(self):
        """Создание отчета"""
        logger.info("📝 Создание отчета...")
        
        # Сохранение результатов
        with open('rag_diagnostic_report.json', 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        # Создание текстового отчета
        report_lines = [
            "# RAG Diagnostic Report",
            f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Issues Found:",
        ]
        
        if self.results['issues_found']:
            for issue in self.results['issues_found']:
                report_lines.append(f"- {issue}")
        else:
            report_lines.append("- No critical issues found")
        
        report_lines.extend([
            "",
            "## Recommendations:",
        ])
        
        if self.results['recommendations']:
            for rec in self.results['recommendations']:
                report_lines.append(f"- {rec}")
        else:
            report_lines.append("- No specific recommendations")
        
        report_lines.extend([
            "",
            "## Next Steps:",
            "1. Review the detailed JSON report: rag_diagnostic_report.json",
            "2. Address critical issues first",
            "3. Implement recommendations",
            "4. Re-run diagnostic to verify improvements",
            "",
            "## Files to Check:",
            "- src/vanna/vanna_semantic_fixed.py (DDL search)",
            "- src/services/query_service.py (Context optimization)",
            "- src/vanna/optimized_dual_pipeline.py (Few-shot learning)"
        ])
        
        with open('rag_diagnostic_report.md', 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        
        logger.info("📊 Отчет создан:")
        logger.info("  - rag_diagnostic_report.json (детальные данные)")
        logger.info("  - rag_diagnostic_report.md (краткий отчет)")

async def main():
    """Основная функция"""
    print("🚀 Запуск диагностики RAG системы...")
    print("=" * 50)
    
    diagnostic = RAGDiagnostic()
    await diagnostic.run_full_diagnostic()
    
    print("\n" + "=" * 50)
    print("✅ Диагностика завершена!")
    print("📋 Проверьте файлы:")
    print("  - rag_diagnostic_report.json")
    print("  - rag_diagnostic_report.md")
    print("  - TOMORROW_RAG_IMPROVEMENT_PLAN.md")
    print("  - RAG_IMPROVEMENT_CHECKLIST.md")

if __name__ == "__main__":
    asyncio.run(main())










