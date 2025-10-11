"""
Основной FastAPI сервер для NL→SQL системы
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from typing import Dict, Any

from src.models.requests import QueryRequest, TrainingExampleRequest, HealthCheckRequest
from src.models.responses import SQLResponse, QueryResultResponse, ErrorResponse, HealthCheckResponse, TrainingResponse
from src.services.query_service import QueryService
from src.services.customer_api_service import CustomerAPIService

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создание FastAPI приложения
app = FastAPI(
    title="NL→SQL API",
    description="API для генерации SQL запросов на естественном языке",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Инициализация сервисов
query_service = QueryService()
customer_api_service = CustomerAPIService()


@app.get("/", response_model=Dict[str, str])
async def root():
    """
    Корневой эндпоинт
    """
    return {"message": "NL→SQL API работает", "version": "1.0.0"}


@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """
    Проверка здоровья системы
    """
    try:
        # Проверка компонентов
        components = {
            "api": "healthy",
            "vanna": "healthy" if query_service.is_ready() else "unhealthy",
            "customer_api": "healthy" if customer_api_service.is_ready() else "unhealthy"
        }
        
        status = "healthy" if all(status == "healthy" for status in components.values()) else "unhealthy"
        
        return HealthCheckResponse(
            status=status,
            components=components,
            version="1.0.0"
        )
        
    except Exception as e:
        logger.error(f"Ошибка проверки здоровья: {e}")
        raise HTTPException(status_code=500, detail="Ошибка проверки здоровья системы")


@app.post("/query", response_model=SQLResponse)
async def generate_sql(request: QueryRequest):
    """
    Генерация SQL запроса на основе вопроса пользователя
    """
    try:
        logger.info(f"Получен запрос от пользователя {request.user_id}: {request.question}")
        
        # Генерация SQL через Vanna AI
        sql = await query_service.generate_sql(
            question=request.question,
            user_context={
                "user_id": request.user_id,
                "role": request.role,
                "department": request.department,
                "context": request.context
            }
        )
        
        return SQLResponse(
            sql=sql,
            question=request.question,
            user_id=request.user_id
        )
        
    except Exception as e:
        logger.error(f"Ошибка генерации SQL: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка генерации SQL: {str(e)}")


@app.post("/query/execute", response_model=QueryResultResponse)
async def execute_query(request: QueryRequest):
    """
    Генерация и выполнение SQL запроса
    """
    try:
        logger.info(f"Выполнение запроса от пользователя {request.user_id}: {request.question}")
        
        # Генерация SQL
        sql = await query_service.generate_sql(
            question=request.question,
            user_context={
                "user_id": request.user_id,
                "role": request.role,
                "department": request.department,
                "context": request.context
            }
        )
        
        # Отправка в API заказчика для выполнения
        result = await customer_api_service.execute_sql(
            sql_template=sql,
            user_context={
                "user_id": request.user_id,
                "role": request.role,
                "department": request.department
            }
        )
        
        return QueryResultResponse(
            data=result.get("data", []),
            columns=result.get("columns", []),
            row_count=result.get("row_count", 0),
            execution_time=result.get("execution_time", 0.0),
            sql=result.get("final_sql", sql)
        )
        
    except Exception as e:
        logger.error(f"Ошибка выполнения запроса: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка выполнения запроса: {str(e)}")


@app.post("/training/example", response_model=TrainingResponse)
async def add_training_example(request: TrainingExampleRequest):
    """
    Добавление примера для обучения модели
    """
    try:
        logger.info(f"Добавление примера обучения от пользователя {request.user_id}")
        
        # Добавление примера в Vanna AI
        await query_service.add_training_example(
            question=request.question,
            sql=request.sql,
            user_id=request.user_id,
            verified=request.verified
        )
        
        return TrainingResponse(
            success=True,
            message="Пример успешно добавлен",
            example_id=f"example_{request.user_id}_{hash(request.question)}"
        )
        
    except Exception as e:
        logger.error(f"Ошибка добавления примера: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка добавления примера: {str(e)}")


@app.get("/training/status")
async def get_training_status():
    """
    Получение статуса обучения модели
    """
    try:
        status = await query_service.get_training_status()
        return status
        
    except Exception as e:
        logger.error(f"Ошибка получения статуса обучения: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения статуса: {str(e)}")


# Обработчик ошибок
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Глобальный обработчик ошибок
    """
    logger.error(f"Необработанная ошибка: {exc}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Внутренняя ошибка сервера",
            error_code="INTERNAL_ERROR"
        ).dict()
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
