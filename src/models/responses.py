"""
Pydantic модели для исходящих ответов
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class SQLResponse(BaseModel):
    """
    Ответ с SQL запросом
    """
    sql: str = Field(..., description="Сгенерированный SQL запрос")
    question: str = Field(..., description="Исходный вопрос")
    user_id: str = Field(..., description="ID пользователя")
    timestamp: datetime = Field(default_factory=datetime.now)
    confidence: Optional[float] = Field(None, description="Уверенность модели")


class QueryResultResponse(BaseModel):
    """
    Ответ с результатом выполнения запроса
    """
    data: List[Dict[str, Any]] = Field(..., description="Результаты запроса")
    columns: List[str] = Field(..., description="Названия колонок")
    row_count: int = Field(..., description="Количество строк")
    execution_time: float = Field(..., description="Время выполнения в секундах")
    sql: str = Field(..., description="Выполненный SQL запрос")


class ErrorResponse(BaseModel):
    """
    Ответ с ошибкой
    """
    error: str = Field(..., description="Описание ошибки")
    error_code: str = Field(..., description="Код ошибки")
    timestamp: datetime = Field(default_factory=datetime.now)
    request_id: Optional[str] = Field(None, description="ID запроса")


class HealthCheckResponse(BaseModel):
    """
    Ответ проверки здоровья системы
    """
    status: str = Field(..., description="Статус системы")
    timestamp: datetime = Field(default_factory=datetime.now)
    components: Dict[str, str] = Field(..., description="Статус компонентов")
    version: str = Field("1.0.0", description="Версия системы")


class TrainingResponse(BaseModel):
    """
    Ответ на запрос обучения
    """
    success: bool = Field(..., description="Успешность операции")
    message: str = Field(..., description="Сообщение")
    example_id: Optional[str] = Field(None, description="ID добавленного примера")
    explain_plan: Optional[str] = Field(None, description="EXPLAIN план для SQL")
    explain_plan_basic: Optional[str] = Field(None, description="EXPLAIN план для базового SQL")
    timestamp: datetime = Field(default_factory=datetime.now)
    # Результаты валидации оптимизации
    optimization_validated: Optional[bool] = Field(None, description="Результат валидации оптимизации (True=лучше, False=хуже/равно, None=не валидировано)")
    cost_basic: Optional[float] = Field(None, description="Cost базового SQL")
    cost_optimized: Optional[float] = Field(None, description="Cost оптимизированного SQL")
    cost_improvement_percent: Optional[float] = Field(None, description="Улучшение cost в процентах")
    width_basic: Optional[float] = Field(None, description="Width (байт/строка) базового SQL")
    width_optimized: Optional[float] = Field(None, description="Width (байт/строка) оптимизированного SQL")
    width_improvement_percent: Optional[float] = Field(None, description="Улучшение width в процентах")
    rows_basic: Optional[float] = Field(None, description="Rows (строк) базового SQL")
    rows_optimized: Optional[float] = Field(None, description="Rows (строк) оптимизированного SQL")
    rows_improvement_percent: Optional[float] = Field(None, description="Улучшение rows в процентах")
    optimization_warning: Optional[str] = Field(None, description="Предупреждение если оптимизация не подтверждена")


class TrainingBatchResponse(BaseModel):
    """
    Ответ на запрос массового обучения (DDL или документация)
    """
    success: bool = Field(..., description="Успешность операции")
    message: str = Field(..., description="Сообщение")
    added: int = Field(0, description="Количество добавленных записей")
    updated: int = Field(0, description="Количество обновленных записей")
    failed: int = Field(0, description="Количество неудачных операций")
    errors: List[str] = Field(default_factory=list, description="Список ошибок")
    timestamp: datetime = Field(default_factory=datetime.now)
