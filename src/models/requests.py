"""
Pydantic модели для входящих запросов
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class QueryRequest(BaseModel):
    """
    Запрос на генерацию SQL
    """
    question: str = Field(..., description="Вопрос пользователя на русском языке")
    user_id: str = Field(..., description="ID пользователя")
    role: str = Field(..., description="Роль пользователя")
    department: Optional[str] = Field(None, description="Отдел пользователя")
    context: Optional[Dict[str, Any]] = Field(None, description="Дополнительный контекст")


class SQLTemplateRequest(BaseModel):
    """
    Запрос SQL шаблона для API заказчика
    """
    sql_template: str = Field(..., description="SQL шаблон")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Параметры запроса")
    user_context: Dict[str, Any] = Field(..., description="Контекст пользователя")
    request_id: str = Field(..., description="ID запроса")


class TrainingExampleRequest(BaseModel):
    """
    Запрос на добавление примера обучения
    """
    question: str = Field(..., description="Вопрос пользователя")
    sql: str = Field(..., description="SQL запрос")
    user_id: str = Field(..., description="ID пользователя")
    verified: bool = Field(False, description="Проверен ли пример")


class HealthCheckRequest(BaseModel):
    """
    Запрос проверки здоровья системы
    """
    timestamp: datetime = Field(default_factory=datetime.now)
    component: str = Field("api", description="Компонент системы")
