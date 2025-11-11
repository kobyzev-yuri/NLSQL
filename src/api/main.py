"""
Основной FastAPI сервер для NL→SQL системы
"""

import sys
import os
from pathlib import Path

# Load environment variables from config.env
from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / "config.env")

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import logging
from typing import Dict, Any, List, Optional
import asyncpg

from models.requests import QueryRequest, TrainingExampleRequest, HealthCheckRequest
from models.responses import SQLResponse, QueryResultResponse, ErrorResponse, HealthCheckResponse, TrainingResponse
from services.query_service import QueryService
from services.customer_api_service import CustomerAPIService

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Вывод в stdout/stderr
    ]
)
logger = logging.getLogger(__name__)

# Устанавливаем уровень логирования для vanna модулей
logging.getLogger('src.vanna').setLevel(logging.INFO)
logging.getLogger('src.services').setLevel(logging.INFO)
logging.getLogger('src.vanna.vanna_semantic_fixed').setLevel(logging.INFO)
logging.getLogger('src.services.query_service').setLevel(logging.INFO)

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

# Модели для работы с комментариями
class CommentRequest(BaseModel):
    comment: str

class TableInfo(BaseModel):
    table_name: str
    table_comment: Optional[str] = None

class ColumnInfo(BaseModel):
    column_name: str
    data_type: str
    column_comment: Optional[str] = None

class CommentsStats(BaseModel):
    total_tables: int
    tables_with_comments: int
    tables_without_comments: int
    total_columns: int
    columns_with_comments: int
    columns_without_comments: int
    coverage_tables: float
    coverage_columns: float

# Функция для получения подключения к БД
async def get_db_connection():
    """Получить подключение к PostgreSQL"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise HTTPException(status_code=500, detail="DATABASE_URL не настроен")
    try:
        conn = await asyncpg.connect(database_url)
        return conn
    except Exception as e:
        logger.error(f"Ошибка подключения к БД: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка подключения к БД: {str(e)}")


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


@app.post("/test-search")
async def test_vector_search(request: dict):
    """
    Тестирование семантического поиска в векторной базе данных
    """
    try:
        question = request.get("question", "")
        search_type = request.get("search_type", "semantic")
        limit = request.get("limit", 5)
        
        if not question:
            raise HTTPException(status_code=400, detail="Вопрос не может быть пустым")
        
        logger.info(f"Тестирование поиска: {question} (тип: {search_type})")
        
        # Получаем результаты поиска через query_service
        search_results = await query_service.test_vector_search(
            question=question,
            search_type=search_type,
            limit=limit
        )
        
        return {
            "success": True,
            "question": question,
            "search_type": search_type,
            "results": search_results,
            "total_found": len(search_results)
        }
        
    except Exception as e:
        logger.error(f"Ошибка тестирования поиска: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка тестирования поиска: {str(e)}")


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
        logger.info(f"📝 Добавление примера обучения от пользователя {request.user_id}")
        logger.info(f"   Вопрос: {request.question[:100]}...")
        logger.info(f"   SQL: {request.sql[:100] if request.sql else 'None'}...")
        logger.info(f"   SQL базовый: {request.sql_basic[:100] if request.sql_basic else 'None'}...")
        logger.info(f"   SQL оптимизированный: {request.sql_optimized[:100] if request.sql_optimized else 'None'}...")
        
        # Добавление примера в Vanna AI
        result = await query_service.add_training_example(
            question=request.question,
            sql=request.sql,
            user_id=request.user_id,
            verified=request.verified,
            sql_basic=request.sql_basic,
            sql_optimized=request.sql_optimized,
            improvement=request.improvement,
            domain=request.domain,
            tags=request.tags
        )
        
        # result может быть dict с example_id, планами и результатами валидации, или None
        logger.info(f"📊 Результат добавления: type={type(result)}")
        if isinstance(result, dict):
            example_id = result.get('example_id') or f"example_{request.user_id}_{hash(request.question)}"
            explain_plan = result.get('explain_plan')
            explain_plan_basic = result.get('explain_plan_basic')
            logger.info(f"📋 Планы из result: explain_plan={'✅' if explain_plan else '❌'}, explain_plan_basic={'✅' if explain_plan_basic else '❌'}")
            optimization_validated = result.get('optimization_validated')
            cost_basic = result.get('cost_basic')
            cost_optimized = result.get('cost_optimized')
            cost_improvement_percent = result.get('cost_improvement_percent')
            width_basic = result.get('width_basic')
            width_optimized = result.get('width_optimized')
            width_improvement_percent = result.get('width_improvement_percent')
            rows_basic = result.get('rows_basic')
            rows_optimized = result.get('rows_optimized')
            rows_improvement_percent = result.get('rows_improvement_percent')
            optimization_warning = result.get('optimization_warning')
        else:
            example_id = f"example_{request.user_id}_{hash(request.question)}"
            explain_plan = None
            explain_plan_basic = None
            optimization_validated = None
            cost_basic = None
            cost_optimized = None
            cost_improvement_percent = None
            width_basic = None
            width_optimized = None
            width_improvement_percent = None
            rows_basic = None
            rows_optimized = None
            rows_improvement_percent = None
            optimization_warning = None
        
        # Формируем сообщение с учетом валидации
        if optimization_validated is False:
            message = f"Пример добавлен, но ⚠️ оптимизация не подтверждена: {optimization_warning or 'оптимизированный SQL не лучше базового'}"
        elif optimization_validated is True:
            # Формируем список улучшений
            improvements = []
            if cost_improvement_percent is not None and cost_improvement_percent > 0:
                improvements.append(f"cost: {cost_improvement_percent:.2f}%")
            if width_improvement_percent is not None and width_improvement_percent > 0:
                improvements.append(f"width: {width_improvement_percent:.2f}%")
            if rows_improvement_percent is not None and rows_improvement_percent > 0:
                improvements.append(f"rows: {rows_improvement_percent:.2f}%")
            
            if improvements:
                improvement_str = ", ".join(improvements)
                message = f"Пример успешно добавлен. ✅ Оптимизация подтверждена: улучшение ({improvement_str})"
            else:
                message = f"Пример успешно добавлен. ✅ Оптимизация подтверждена"
        else:
            message = "Пример успешно добавлен"
        
        logger.info(f"📤 Возвращаем TrainingResponse:")
        logger.info(f"   explain_plan: {'✅' if explain_plan else '❌'}")
        logger.info(f"   explain_plan_basic: {'✅' if explain_plan_basic else '❌'}")
        
        return TrainingResponse(
            success=True,
            message=message,
            example_id=example_id,
            explain_plan=explain_plan,
            explain_plan_basic=explain_plan_basic,
            optimization_validated=optimization_validated,
            cost_basic=cost_basic,
            cost_optimized=cost_optimized,
            cost_improvement_percent=cost_improvement_percent,
            width_basic=width_basic,
            width_optimized=width_optimized,
            width_improvement_percent=width_improvement_percent,
            rows_basic=rows_basic,
            rows_optimized=rows_optimized,
            rows_improvement_percent=rows_improvement_percent,
            optimization_warning=optimization_warning
        )
        
    except Exception as e:
        logger.error(f"❌ Ошибка добавления примера: {e}")
        import traceback
        logger.error(f"   Traceback: {traceback.format_exc()}")
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


# ==================== Эндпоинты для работы с комментариями БД ====================

@app.get("/api/database/tables", response_model=List[TableInfo])
async def get_tables_with_comments():
    """
    Получить список всех таблиц с информацией о комментариях
    """
    conn = None
    try:
        conn = await get_db_connection()
        
        # Получаем список таблиц с комментариями
        rows = await conn.fetch("""
            SELECT 
                t.table_name,
                COALESCE(obj_description(c.oid, 'pg_class'), '') as table_comment
            FROM information_schema.tables t
            LEFT JOIN pg_class c ON c.relname = t.table_name
            LEFT JOIN pg_namespace n ON n.oid = c.relnamespace AND n.nspname = 'public'
            WHERE t.table_schema = 'public'
            AND t.table_type = 'BASE TABLE'
            ORDER BY 
                CASE WHEN obj_description(c.oid, 'pg_class') IS NULL THEN 0 ELSE 1 END,
                t.table_name
        """)
        
        tables = [
            TableInfo(
                table_name=row['table_name'],
                table_comment=row['table_comment'] if row['table_comment'] else None
            )
            for row in rows
        ]
        
        return tables
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения списка таблиц: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения списка таблиц: {str(e)}")
    finally:
        if conn:
            await conn.close()


@app.get("/api/database/tables/{table_name}/columns", response_model=List[ColumnInfo])
async def get_table_columns(table_name: str):
    """
    Получить список колонок таблицы с комментариями
    """
    conn = None
    try:
        conn = await get_db_connection()
        
        # Получаем OID таблицы
        table_oid = await conn.fetchval("""
            SELECT c.oid
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE c.relname = $1 AND n.nspname = 'public'
        """, table_name)
        
        if not table_oid:
            raise HTTPException(status_code=404, detail=f"Таблица '{table_name}' не найдена")
        
        # Получаем колонки с комментариями
        rows = await conn.fetch("""
            SELECT 
                c.column_name,
                c.data_type,
                COALESCE(col_description($1::oid, c.ordinal_position), '') as column_comment
            FROM information_schema.columns c
            WHERE c.table_schema = 'public' 
            AND c.table_name = $2
            ORDER BY c.ordinal_position
        """, table_oid, table_name)
        
        columns = [
            ColumnInfo(
                column_name=row['column_name'],
                data_type=row['data_type'],
                column_comment=row['column_comment'] if row['column_comment'] else None
            )
            for row in rows
        ]
        
        return columns
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения колонок таблицы {table_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения колонок: {str(e)}")
    finally:
        if conn:
            await conn.close()


@app.post("/api/database/tables/{table_name}/comment")
async def add_table_comment(table_name: str, request: CommentRequest):
    """
    Добавить или обновить COMMENT ON TABLE
    """
    conn = None
    try:
        conn = await get_db_connection()
        
        # Проверяем существование таблицы
        table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = $1
            )
        """, table_name)
        
        if not table_exists:
            raise HTTPException(status_code=404, detail=f"Таблица '{table_name}' не найдена")
        
        # Выполняем COMMENT ON TABLE
        # PostgreSQL не поддерживает параметризацию для COMMENT, поэтому используем безопасное форматирование
        # Экранируем одинарные кавычки в комментарии
        escaped_comment = request.comment.replace("'", "''")
        await conn.execute(
            f"COMMENT ON TABLE public.\"{table_name}\" IS '{escaped_comment}'"
        )
        
        logger.info(f"✅ Комментарий добавлен для таблицы {table_name}")
        
        return {
            "success": True,
            "message": f"Комментарий для таблицы '{table_name}' успешно добавлен",
            "table_name": table_name,
            "comment": request.comment
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка добавления комментария для таблицы {table_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка добавления комментария: {str(e)}")
    finally:
        if conn:
            await conn.close()


@app.post("/api/database/tables/{table_name}/columns/{column_name}/comment")
async def add_column_comment(table_name: str, column_name: str, request: CommentRequest):
    """
    Добавить или обновить COMMENT ON COLUMN
    """
    conn = None
    try:
        conn = await get_db_connection()
        
        # Проверяем существование колонки
        column_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = $1 
                AND column_name = $2
            )
        """, table_name, column_name)
        
        if not column_exists:
            raise HTTPException(
                status_code=404, 
                detail=f"Колонка '{column_name}' в таблице '{table_name}' не найдена"
            )
        
        # Выполняем COMMENT ON COLUMN
        # PostgreSQL не поддерживает параметризацию для COMMENT, поэтому используем безопасное форматирование
        # Экранируем одинарные кавычки в комментарии
        escaped_comment = request.comment.replace("'", "''")
        await conn.execute(
            f"COMMENT ON COLUMN public.\"{table_name}\".\"{column_name}\" IS '{escaped_comment}'"
        )
        
        logger.info(f"✅ Комментарий добавлен для колонки {table_name}.{column_name}")
        
        return {
            "success": True,
            "message": f"Комментарий для колонки '{table_name}.{column_name}' успешно добавлен",
            "table_name": table_name,
            "column_name": column_name,
            "comment": request.comment
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка добавления комментария для колонки {table_name}.{column_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка добавления комментария: {str(e)}")
    finally:
        if conn:
            await conn.close()


@app.get("/api/database/comments/stats", response_model=CommentsStats)
async def get_comments_statistics():
    """
    Получить статистику по комментариям в БД
    """
    conn = None
    try:
        conn = await get_db_connection()
        
        # Статистика по таблицам
        table_stats = await conn.fetchrow("""
            SELECT 
                COUNT(*) as total_tables,
                COUNT(CASE WHEN obj_description(c.oid, 'pg_class') IS NOT NULL THEN 1 END) as tables_with_comments
            FROM information_schema.tables t
            LEFT JOIN pg_class c ON c.relname = t.table_name
            LEFT JOIN pg_namespace n ON n.oid = c.relnamespace AND n.nspname = 'public'
            WHERE t.table_schema = 'public'
            AND t.table_type = 'BASE TABLE'
        """)
        
        # Статистика по колонкам
        column_stats = await conn.fetchrow("""
            SELECT 
                COUNT(*) as total_columns,
                COUNT(CASE WHEN col_description(c.oid, col.ordinal_position) IS NOT NULL THEN 1 END) as columns_with_comments
            FROM information_schema.columns col
            JOIN information_schema.tables t ON t.table_name = col.table_name AND t.table_schema = col.table_schema
            LEFT JOIN pg_class c ON c.relname = col.table_name
            LEFT JOIN pg_namespace n ON n.oid = c.relnamespace AND n.nspname = 'public'
            WHERE col.table_schema = 'public'
            AND t.table_type = 'BASE TABLE'
        """)
        
        total_tables = table_stats['total_tables'] or 0
        tables_with_comments = table_stats['tables_with_comments'] or 0
        tables_without_comments = total_tables - tables_with_comments
        
        total_columns = column_stats['total_columns'] or 0
        columns_with_comments = column_stats['columns_with_comments'] or 0
        columns_without_comments = total_columns - columns_with_comments
        
        coverage_tables = (tables_with_comments / total_tables * 100) if total_tables > 0 else 0.0
        coverage_columns = (columns_with_comments / total_columns * 100) if total_columns > 0 else 0.0
        
        return CommentsStats(
            total_tables=total_tables,
            tables_with_comments=tables_with_comments,
            tables_without_comments=tables_without_comments,
            total_columns=total_columns,
            columns_with_comments=columns_with_comments,
            columns_without_comments=columns_without_comments,
            coverage_tables=round(coverage_tables, 2),
            coverage_columns=round(coverage_columns, 2)
        )
        
    except Exception as e:
        logger.error(f"Ошибка получения статистики по комментариям: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения статистики: {str(e)}")
    finally:
        if conn:
            await conn.close()


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
