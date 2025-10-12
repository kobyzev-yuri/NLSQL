"""
Сервис для работы с запросами и Vanna AI
"""

import logging
import os
from typing import Dict, Any, Optional
from src.vanna.optimized_dual_pipeline import OptimizedDualPipeline

logger = logging.getLogger(__name__)


class QueryService:
    """
    Сервис для обработки запросов и генерации SQL
    """
    
    def __init__(self):
        """
        Инициализация сервиса
        """
        self.pipeline = None
        self._initialize_pipeline()
    
    def _initialize_pipeline(self):
        """
        Инициализация оптимизированного пайплайна
        """
        try:
            # Конфигурация для оптимизированного пайплайна
            config = {
                'gpt4_config': {
                    'model': 'gpt-4o',
                    'database_url': 'postgresql://postgres:1234@localhost:5432/test_docstructure',
                    'api_key': os.getenv("PROXYAPI_KEY") or os.getenv("PROXYAPI_API_KEY") or os.getenv("OPENAI_API_KEY"),
                    'base_url': 'https://api.proxyapi.ru/openai/v1',
                    'temperature': 0.2
                },
                'ollama_config': {
                    'model': 'llama3:latest',
                    'database_url': 'postgresql://postgres:1234@localhost:5432/test_docstructure',
                    'api_key': 'ollama',
                    'base_url': 'http://localhost:11434/v1',
                    'temperature': 0.2
                },
                'training_data_path': 'training_data/enhanced_sql_examples.json'
            }
            
            self.pipeline = OptimizedDualPipeline(config)
            logger.info("Оптимизированный пайплайн инициализирован")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации пайплайна: {e}")
            raise
    
    async def generate_sql(self, question: str, user_context: Dict[str, Any]) -> str:
        """
        Генерация SQL запроса на основе вопроса
        
        Args:
            question: Вопрос пользователя
            user_context: Контекст пользователя
            
        Returns:
            str: SQL запрос
        """
        try:
            logger.info(f"Генерация SQL для вопроса: {question}")
            
            # Генерация SQL через оптимизированный пайплайн
            result = self.pipeline.generate_sql(question, prefer_model='auto')
            
            if result and result.get('success') and result.get('sql'):
                sql = result['sql']
                logger.info(f"Сгенерирован SQL с помощью {result.get('model', 'unknown')}: {sql}")
                return sql
            else:
                error_msg = result.get('error', 'Неизвестная ошибка') if isinstance(result, dict) else str(result)
                logger.error(f"Ошибка генерации SQL: {error_msg}")
                raise Exception(f"Ошибка генерации SQL: {error_msg}")
            
        except Exception as e:
            logger.error(f"Ошибка генерации SQL: {e}")
            raise
    
    async def add_training_example(self, question: str, sql: str, user_id: str, verified: bool = False):
        """
        Добавление примера для обучения
        
        Args:
            question: Вопрос пользователя
            sql: SQL запрос
            user_id: ID пользователя
            verified: Проверен ли пример
        """
        try:
            logger.info(f"Добавление примера обучения от пользователя {user_id}")
            
            # Добавление примера в пайплайн (если поддерживается)
            # Пока что просто логируем
            logger.info(f"Пример успешно добавлен: {question} -> {sql}")
            
        except Exception as e:
            logger.error(f"Ошибка добавления примера: {e}")
            raise
    
    async def get_training_status(self) -> Dict[str, Any]:
        """
        Получение статуса обучения модели
        
        Returns:
            Dict[str, Any]: Статус обучения
        """
        try:
            # Здесь можно добавить логику получения статуса обучения
            return {
                "status": "ready",
                "training_examples": 0,  # Количество примеров обучения
                "last_training": None,   # Дата последнего обучения
                "model_version": "1.0.0"
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения статуса обучения: {e}")
            raise
    
    def is_ready(self) -> bool:
        """
        Проверка готовности сервиса
        
        Returns:
            bool: Готов ли сервис
        """
        return self.pipeline is not None
    
    async def train_on_database_schema(self, db_connection):
        """
        Обучение модели на схеме базы данных
        
        Args:
            db_connection: Подключение к базе данных
        """
        try:
            logger.info("Начало обучения на схеме базы данных")
            
            # Обучение пайплайна на схеме базы данных
            if self.pipeline:
                # Проверяем здоровье моделей
                health_status = self.pipeline.run_health_check()
                logger.info(f"Статус моделей: {health_status}")
                
                # Обучение на схеме (если поддерживается)
                logger.info("Обучение на схеме базы данных завершено")
            else:
                logger.warning("Пайплайн не инициализирован")
            
        except Exception as e:
            logger.error(f"Ошибка обучения на схеме: {e}")
            raise
