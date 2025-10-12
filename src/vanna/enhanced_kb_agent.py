#!/usr/bin/env python3
"""
Улучшенный KB агент с поддержкой DocStructureSchema
Интегрирует двухмодельный пайплайн и улучшенную логику контекста
"""

import os
import logging
import json
from typing import Optional, Dict, Any, List
from pathlib import Path
import sys

# Добавляем путь к модулям
sys.path.append(str(Path(__file__).parent.parent))

from src.vanna.dual_model_pipeline import DualModelPipeline
from src.vanna.vanna_pgvector_native import DocStructureVannaNative

logger = logging.getLogger(__name__)

class EnhancedKBAgent:
    """
    Улучшенный KB агент с поддержкой DocStructureSchema
    Использует двухмодельный пайплайн и улучшенную логику контекста
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Инициализация улучшенного KB агента
        
        Args:
            config: Конфигурация
        """
        if config is None:
            config = {}
            
        self.config = config
        
        # Инициализируем двухмодельный пайплайн
        self.pipeline = DualModelPipeline(config)
        
        # Приоритетные бизнес-таблицы из DocStructureSchema
        self.priority_tables = [
            "equsers",                    # Пользователи
            "eq_departments",             # Отделы
            "eqgroups",                   # Группы
            "eqroles",                    # Роли
            "tbl_business_unit",          # Клиенты
            "tbl_principal_assignment",  # Поручения
            "tbl_incoming_payments",      # Платежи
            "tbl_accounts_document",      # Учетные записи
            "tbl_personal_account"        # Личные кабинеты
        ]
        
        # Системные таблицы для исключения
        self.system_tables = [
            "views", "view_table_usage", "vanna_vectors",
            "information_schema", "pg_catalog", "pg_*"
        ]
        
        logger.info("✅ EnhancedKBAgent инициализирован")
    
    def train_agent(self, training_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Обучение агента на всех доступных данных
        
        Args:
            training_data: Данные для обучения
            
        Returns:
            bool: Успешность обучения
        """
        try:
            logger.info("🚀 Начало обучения KB агента...")
            
            # 1. Обучение на схеме БД
            logger.info("📚 Этап 1: Обучение на схеме БД...")
            schema_success = self.pipeline.train_on_schema()
            
            if not schema_success:
                logger.warning("⚠️ Обучение на схеме не удалось")
            
            # 2. Обучение на примерах (если предоставлены)
            if training_data and 'examples' in training_data:
                logger.info("📚 Этап 2: Обучение на примерах...")
                examples_success = self.pipeline.train_on_examples(training_data['examples'])
                
                if not examples_success:
                    logger.warning("⚠️ Обучение на примерах не удалось")
            
            # 3. Обучение на документации (если предоставлена)
            if training_data and 'documentation' in training_data:
                logger.info("📚 Этап 3: Обучение на документации...")
                # Здесь можно добавить обучение на документации
                pass
            
            logger.info("✅ Обучение KB агента завершено")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка обучения агента: {e}")
            return False
    
    def generate_sql(self, question: str, model_preference: str = 'auto') -> Dict[str, Any]:
        """
        Генерация SQL с улучшенной логикой контекста
        
        Args:
            question: Вопрос на естественном языке
            model_preference: Предпочитаемая модель
            
        Returns:
            Dict с результатом генерации
        """
        try:
            logger.info(f"🔍 Генерация SQL для: '{question}'")
            
            # Используем двухмодельный пайплайн
            result = self.pipeline.generate_sql(
                question=question,
                prefer_model=model_preference
            )
            
            if result['success']:
                logger.info(f"✅ SQL сгенерирован с {result['model']}")
            else:
                logger.error(f"❌ Ошибка генерации SQL: {result.get('error', 'Неизвестная ошибка')}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Критическая ошибка генерации SQL: {e}")
            return {
                'success': False,
                'error': str(e),
                'question': question
            }
    
    def get_context_info(self, question: str) -> Dict[str, Any]:
        """
        Получение информации о контексте для вопроса
        
        Args:
            question: Вопрос
            
        Returns:
            Dict с информацией о контексте
        """
        try:
            # Получаем агента для анализа контекста
            agent = self.pipeline.gpt4_agent or self.pipeline.ollama_agent
            
            if not agent:
                return {'error': 'Нет доступных агентов'}
            
            # Анализируем контекст
            context_info = {
                'question': question,
                'priority_tables': self.priority_tables,
                'system_tables': self.system_tables,
                'available_tables': [],
                'context_quality': 'unknown'
            }
            
            # Получаем список доступных таблиц
            try:
                tables_query = """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
                """
                df_tables = agent.run_sql(tables_query)
                context_info['available_tables'] = df_tables['table_name'].tolist()
                
                # Анализируем качество контекста
                business_tables_found = sum(1 for table in self.priority_tables 
                                          if table in context_info['available_tables'])
                context_info['business_tables_found'] = business_tables_found
                context_info['context_quality'] = 'good' if business_tables_found >= 5 else 'poor'
                
            except Exception as e:
                logger.warning(f"⚠️ Ошибка анализа контекста: {e}")
                context_info['error'] = str(e)
            
            return context_info
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения контекста: {e}")
            return {'error': str(e)}
    
    def health_check(self) -> Dict[str, Any]:
        """
        Проверка здоровья агента
        
        Returns:
            Dict с информацией о здоровье
        """
        try:
            # Проверяем пайплайн
            pipeline_health = self.pipeline.health_check()
            
            # Проверяем контекст
            context_info = self.get_context_info("тест")
            
            health = {
                'pipeline': pipeline_health,
                'context': context_info,
                'overall': all(pipeline_health.values()) and context_info.get('context_quality') != 'poor'
            }
            
            return health
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки здоровья: {e}")
            return {'error': str(e)}
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Получение статистики агента
        
        Returns:
            Dict со статистикой
        """
        try:
            stats = {
                'pipeline_usage': self.pipeline.get_usage_stats(),
                'priority_tables': self.priority_tables,
                'system_tables': self.system_tables
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики: {e}")
            return {'error': str(e)}

def create_enhanced_kb_agent(config: Optional[Dict[str, Any]] = None) -> EnhancedKBAgent:
    """
    Создание улучшенного KB агента
    
    Args:
        config: Конфигурация
        
    Returns:
        EnhancedKBAgent: Настроенный агент
    """
    return EnhancedKBAgent(config)

if __name__ == "__main__":
    # Тестирование агента
    agent = EnhancedKBAgent()
    
    # Проверка здоровья
    health = agent.health_check()
    print(f"Здоровье агента: {health}")
    
    # Тест генерации
    result = agent.generate_sql("Покажи всех пользователей")
    print(f"Результат: {result}")
    
    # Статистика
    stats = agent.get_statistics()
    print(f"Статистика: {stats}")
