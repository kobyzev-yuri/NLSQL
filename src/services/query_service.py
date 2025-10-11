"""
Сервис для работы с запросами и Vanna AI
"""

import logging
from typing import Dict, Any, Optional
from src.vanna.vanna_client import DocStructureVanna

logger = logging.getLogger(__name__)


class QueryService:
    """
    Сервис для обработки запросов и генерации SQL
    """
    
    def __init__(self):
        """
        Инициализация сервиса
        """
        self.vanna_client = None
        self._initialize_vanna()
    
    def _initialize_vanna(self):
        """
        Инициализация Vanna AI клиента
        """
        try:
            # Конфигурация для Vanna AI
            config = {
                "api_key": "your-openai-api-key",  # Заменить на реальный ключ
                "model": "gpt-4",
                "chroma_db_path": "./chroma_db"
            }
            
            self.vanna_client = DocStructureVanna(config=config)
            logger.info("Vanna AI клиент инициализирован")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации Vanna AI: {e}")
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
            
            # Генерация SQL через Vanna AI
            sql = self.vanna_client.generate_sql(question, user_context)
            
            logger.info(f"Сгенерирован SQL: {sql}")
            return sql
            
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
            
            # Добавление примера в Vanna AI
            self.vanna_client.add_training_example(question, sql)
            
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
        return self.vanna_client is not None
    
    async def train_on_database_schema(self, db_connection):
        """
        Обучение модели на схеме базы данных
        
        Args:
            db_connection: Подключение к базе данных
        """
        try:
            logger.info("Начало обучения на схеме базы данных")
            
            # Обучение на схеме базы данных
            self.vanna_client.train_on_database_schema(db_connection)
            
            logger.info("Обучение на схеме базы данных завершено")
            
        except Exception as e:
            logger.error(f"Ошибка обучения на схеме: {e}")
            raise
