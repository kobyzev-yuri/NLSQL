"""
Pydantic модели для входящих запросов
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
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
    sql: str = Field(..., description="SQL запрос (оптимизированный вариант)")
    user_id: str = Field(..., description="ID пользователя")
    verified: bool = Field(False, description="Проверен ли пример")
    # Опциональные поля для оптимизированных SQL
    sql_basic: Optional[str] = Field(None, description="Базовый (неоптимизированный) SQL для сравнения")
    sql_optimized: Optional[str] = Field(None, description="Оптимизированный SQL (альтернатива sql)")
    improvement: Optional[str] = Field(None, description="Описание улучшения производительности")
    domain: Optional[str] = Field(None, description="Домен вопроса (users, payments, assignments, etc.)")
    tags: Optional[List[str]] = Field(None, description="Список тегов для категоризации")


class HealthCheckRequest(BaseModel):
    """
    Запрос проверки здоровья системы
    """
    timestamp: datetime = Field(default_factory=datetime.now)
    component: str = Field("api", description="Компонент системы")
