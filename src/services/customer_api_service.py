"""
Сервис для работы с API заказчика
"""

import logging
import httpx
from typing import Dict, Any, Optional
import asyncio

logger = logging.getLogger(__name__)


class CustomerAPIService:
    """
    Сервис для взаимодействия с API заказчика
    """
    
    def __init__(self, customer_api_url: str = "http://localhost:8081"):
        """
        Инициализация сервиса
        
        Args:
            customer_api_url: URL API заказчика
        """
        self.customer_api_url = customer_api_url
        self.timeout = 30.0  # Таймаут для запросов
    
    async def execute_sql(self, sql_template: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Отправка SQL шаблона в API заказчика для выполнения
        
        Args:
            sql_template: SQL шаблон
            user_context: Контекст пользователя
            
        Returns:
            Dict[str, Any]: Результат выполнения
        """
        try:
            logger.info(f"Отправка SQL в API заказчика: {sql_template[:100]}...")
            
            # Подготовка запроса
            request_data = {
                "sql_template": sql_template,
                "user_context": user_context,
                "request_id": f"req_{hash(sql_template)}"
            }
            
            # Отправка запроса
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.customer_api_url}/api/sql/execute",
                    json=request_data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"SQL успешно выполнен, получено {result.get('row_count', 0)} строк")
                    return result
                else:
                    logger.error(f"Ошибка API заказчика: {response.status_code} - {response.text}")
                    raise Exception(f"API заказчика вернул ошибку: {response.status_code}")
                    
        except httpx.TimeoutException:
            logger.error("Таймаут при обращении к API заказчика")
            raise Exception("Таймаут при обращении к API заказчика")
        except Exception as e:
            logger.error(f"Ошибка обращения к API заказчика: {e}")
            raise
    
    async def validate_sql(self, sql_template: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Валидация SQL шаблона через API заказчика
        
        Args:
            sql_template: SQL шаблон
            user_context: Контекст пользователя
            
        Returns:
            Dict[str, Any]: Результат валидации
        """
        try:
            logger.info(f"Валидация SQL через API заказчика: {sql_template[:100]}...")
            
            # Подготовка запроса
            request_data = {
                "sql_template": sql_template,
                "user_context": user_context,
                "validate_only": True
            }
            
            # Отправка запроса
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.customer_api_url}/api/sql/validate",
                    json=request_data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info("SQL успешно валидирован")
                    return result
                else:
                    logger.error(f"Ошибка валидации SQL: {response.status_code} - {response.text}")
                    raise Exception(f"Ошибка валидации SQL: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Ошибка валидации SQL: {e}")
            raise
    
    async def get_user_permissions(self, user_id: str) -> Dict[str, Any]:
        """
        Получение прав пользователя через API заказчика
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Dict[str, Any]: Права пользователя
        """
        try:
            logger.info(f"Получение прав пользователя {user_id}")
            
            # Отправка запроса
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.customer_api_url}/api/users/{user_id}/permissions"
                )
                
                if response.status_code == 200:
                    permissions = response.json()
                    logger.info(f"Получены права пользователя {user_id}")
                    return permissions
                else:
                    logger.error(f"Ошибка получения прав: {response.status_code} - {response.text}")
                    raise Exception(f"Ошибка получения прав: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Ошибка получения прав пользователя: {e}")
            raise
    
    def is_ready(self) -> bool:
        """
        Проверка готовности API заказчика
        
        Returns:
            bool: Готов ли API заказчика
        """
        try:
            # Здесь можно добавить ping запрос к API заказчика
            # Пока возвращаем True для тестирования
            return True
            
        except Exception:
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Проверка здоровья API заказчика
        
        Returns:
            Dict[str, Any]: Статус API заказчика
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.customer_api_url}/health")
                
                if response.status_code == 200:
                    return {"status": "healthy", "response_time": response.elapsed.total_seconds()}
                else:
                    return {"status": "unhealthy", "status_code": response.status_code}
                    
        except Exception as e:
            logger.error(f"Ошибка проверки здоровья API заказчика: {e}")
            return {"status": "unhealthy", "error": str(e)}
