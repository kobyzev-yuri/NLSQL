"""
Mock API заказчика для отладки NL→SQL системы
Имитирует функционал API заказчика для тестирования pipeline
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import asyncio
import random
import logging
from datetime import datetime
from src.utils.plan_sql_converter import plan_to_sql
import os
import asyncpg

logger = logging.getLogger(__name__)

# Создание FastAPI приложения для mock API
mock_app = FastAPI(
    title="Mock Customer API",
    description="Mock API заказчика для отладки NL→SQL системы",
    version="1.0.0"
)

# Добавление CORS middleware
mock_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Модели для mock API
class SQLExecuteRequest(BaseModel):
    sql_template: str
    user_context: Dict[str, Any]
    request_id: str

class SQLValidateRequest(BaseModel):
    sql_template: str
    user_context: Dict[str, Any]
    validate_only: bool = True

class PlanExecuteRequest(BaseModel):
    plan: Dict[str, Any]
    user_context: Dict[str, Any]
    request_id: str

class UserPermissionsRequest(BaseModel):
    user_id: str

# Mock данные для тестирования
MOCK_USERS = {
    "admin": {
        "id": "admin",
        "role": "admin",
        "department": "IT",
        "permissions": ["read", "write", "delete", "admin"],
        "restrictions": []
    },
    "manager": {
        "id": "manager", 
        "role": "manager",
        "department": "Sales",
        "permissions": ["read", "write"],
        "restrictions": ["department_only"]
    },
    "user": {
        "id": "user",
        "role": "user", 
        "department": "Support",
        "permissions": ["read"],
        "restrictions": ["own_data_only"]
    }
}

MOCK_DATA = {
    "equsers": [
        {"id": "1", "login": "admin", "email": "admin@company.com", "department": "IT", "firstname": "Админ", "surname": "Админов"},
        {"id": "2", "login": "manager", "email": "manager@company.com", "department": "IT", "firstname": "Менеджер", "surname": "IT"},
        {"id": "3", "login": "user", "email": "user@company.com", "department": "IT", "firstname": "Пользователь", "surname": "IT"},
        {"id": "4", "login": "sales_manager", "email": "sales@company.com", "department": "Sales", "firstname": "Менеджер", "surname": "Продаж"},
        {"id": "5", "login": "support_user", "email": "support@company.com", "department": "Support", "firstname": "Пользователь", "surname": "Поддержки"},
    ],
    "eq_departments": [
        {"id": "1", "name": "IT", "code": "IT"},
        {"id": "2", "name": "Sales", "code": "SALES"},
        {"id": "3", "name": "Support", "code": "SUPPORT"},
    ],
    "tbl_business_unit": [
        {"id": "1", "business_unit_name": "ООО Ромашка", "inn": "1234567890", "phone": "+7-495-123-45-67"},
        {"id": "2", "business_unit_name": "ИП Иванов", "inn": "0987654321", "phone": "+7-495-765-43-21"},
    ],
    "tbl_principal_assignment": [
        {"id": "1", "assignment_number": "A001", "amount": 100000, "business_unit_id": "1", "login": "back_office"},
        {"id": "2", "assignment_number": "A002", "amount": 50000, "business_unit_id": "2", "login": "a7a_manager"},
    ]
}

@mock_app.get("/")
async def root():
    """Корневой эндпоинт mock API"""
    return {
        "message": "Mock Customer API работает",
        "version": "1.0.0",
        "description": "Mock API заказчика для отладки NL→SQL системы"
    }

DB_DSN = os.getenv("CUSTOMER_DB_DSN", "postgresql://postgres:1234@localhost:5432/test_docstructure")
db_pool: Optional[asyncpg.Pool] = None


@mock_app.on_event("startup")
async def on_startup():
    global db_pool
    try:
        db_pool = await asyncpg.create_pool(dsn=DB_DSN, min_size=1, max_size=5)
        logger.info("✅ DB pool initialized")
    except Exception as e:
        logger.error(f"❌ Failed to init DB pool: {e}")


@mock_app.on_event("shutdown")
async def on_shutdown():
    global db_pool
    if db_pool:
        await db_pool.close()


@mock_app.get("/health")
async def health_check():
    """Проверка здоровья mock API"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "database": "connected" if db_pool is not None else "unavailable",
            "auth": "enabled", 
            "permissions": "loaded"
        }
    }

@mock_app.post("/api/sql/execute")
async def execute_sql(request: SQLExecuteRequest):
    """
    Выполнение SQL запроса с ролевыми ограничениями
    """
    try:
        logger.info(f"Получен запрос на выполнение SQL: {request.sql_template[:100]}...")
        logger.info(f"User context: {request.user_context}")
        
        # Получение контекста пользователя
        login = request.user_context.get("login", "user")
        role = request.user_context.get("role", "user")
        department = request.user_context.get("department", "Support")
        logger.info(f"Extracted: login={login}, role={role}, department={department}")
        
        # Применение ролевых ограничений
        restricted_sql = apply_role_restrictions(
            request.sql_template, 
            login, 
            role, 
            department
        )
        
        # Реальное выполнение SQL
        result = await execute_sql_against_db(restricted_sql)
        
        # Имитация времени выполнения для UX
        execution_time = random.uniform(0.01, 0.2)
        await asyncio.sleep(execution_time)
        
        logger.info(f"SQL выполнен успешно, получено {result.get('row_count', 0)} строк")
        
        return {
            "success": True,
            "sql_template": request.sql_template,  # Оригинальный SQL шаблон
            "sql_with_roles": restricted_sql,      # SQL с примененными ролями
            "final_sql": restricted_sql,           # Для совместимости
            "data": result.get("data", []),
            "columns": result.get("columns", []),
            "row_count": result.get("row_count", 0),
            "execution_time": execution_time,
            "user_context": request.user_context,
            "restrictions_applied": get_applied_restrictions(login, role)
        }
        
    except Exception as e:
        logger.error(f"Ошибка выполнения SQL: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка выполнения SQL: {str(e)}")

@mock_app.post("/api/plan/execute")
async def execute_plan(request: PlanExecuteRequest):
    """
    Выполнение плана: конвертация План→SQL, затем применение ролевых ограничений
    """
    try:
        logger.info(f"Получен запрос на выполнение Плана (request_id={request.request_id})")

        # Получение контекста пользователя
        login = request.user_context.get("login", "user")
        role = request.user_context.get("role", "user")
        department = request.user_context.get("department", "Support")

        # Конвертация плана в SQL
        decoded_sql = plan_to_sql(request.plan)

        # Применение ролевых ограничений
        restricted_sql = apply_role_restrictions(decoded_sql, login, role, department)

        # Реальное выполнение
        result = await execute_sql_against_db(restricted_sql)
        execution_time = random.uniform(0.01, 0.2)
        await asyncio.sleep(execution_time)

        logger.info(f"План выполнен успешно, получено {result.get('row_count', 0)} строк")

        return {
            "success": True,
            "decoded_sql": decoded_sql,
            "final_sql": restricted_sql,
            "data": result.get("data", []),
            "columns": result.get("columns", []),
            "row_count": result.get("row_count", 0),
            "execution_time": execution_time,
            "user_context": request.user_context,
            "restrictions_applied": get_applied_restrictions(login, role)
        }

    except Exception as e:
        logger.error(f"Ошибка выполнения Плана: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка выполнения Плана: {str(e)}")

@mock_app.post("/api/sql/validate")
async def validate_sql(request: SQLValidateRequest):
    """
    Валидация SQL запроса
    """
    try:
        logger.info(f"Валидация SQL: {request.sql_template[:100]}...")
        
        # Простая валидация SQL
        sql = request.sql_template.lower().strip()
        
        # Проверка на опасные операции
        dangerous_operations = ["drop", "delete", "truncate", "alter", "create"]
        if any(op in sql for op in dangerous_operations):
            return {
                "valid": False,
                "error": "Операция не разрешена для данной роли",
                "suggestions": ["Используйте SELECT запросы"]
            }
        
        # Проверка синтаксиса
        if not sql.startswith("select"):
            return {
                "valid": False,
                "error": "Разрешены только SELECT запросы",
                "suggestions": ["Используйте SELECT для получения данных"]
            }
        
        return {
            "valid": True,
            "message": "SQL запрос валиден",
            "estimated_rows": random.randint(1, 1000)
        }
        
    except Exception as e:
        logger.error(f"Ошибка валидации SQL: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка валидации: {str(e)}")

@mock_app.get("/api/users/{user_id}/permissions")
async def get_user_permissions(user_id: str):
    """
    Получение прав пользователя
    """
    try:
        logger.info(f"Получение прав пользователя: {user_id}")
        
        user_info = MOCK_USERS.get(user_id, MOCK_USERS["user"])
        
        return {
            "user_id": user_id,
            "role": user_info["role"],
            "department": user_info["department"],
            "permissions": user_info["permissions"],
            "restrictions": user_info["restrictions"],
            "accessible_tables": get_accessible_tables(user_info["role"]),
            "row_level_security": get_rls_policies(user_info["role"])
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения прав: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения прав: {str(e)}")

def apply_role_restrictions(sql: str, login: str, role: str, department: str) -> str:
    """
    Применение ролевых ограничений к SQL запросу
    Согласно FINAL_ROLE_LOGIC.md
    """
    logger.info(f"Применение ограничений для роли: {role}, login: {login}")
    
    # Убираем финальную точку с запятой и лишние пробелы для корректного добавления условий
    sql = sql.strip()
    if sql.endswith(";"):
        sql = sql[:-1]
    sql_lower = sql.lower()

    def append_condition(base_sql: str, condition: str) -> str:
        base_sql_clean = base_sql.strip()
        base_sql_lower = base_sql_clean.lower()
        logger.info(f"append_condition: проверка SQL: '{base_sql_lower[:100]}'")
        if " where " in base_sql_lower:
            logger.info(f"append_condition: найден WHERE, добавляем AND")
            return f"{base_sql_clean} AND {condition}"
        else:
            logger.info(f"append_condition: WHERE не найден, добавляем WHERE")
            return f"{base_sql_clean} WHERE {condition}"
    
    # Проверяем основную таблицу в FROM, а не JOIN
    if role == "user":
        # Пользователи видят только свои данные
        if "from equsers" in sql_lower:
            # Добавляем ограничение по login (поле существует в схеме)
            # user_id теперь содержит реальный логин из базы данных
            sql = append_condition(sql, f"login = '{login}'")
        elif "from tbl_principal_assignment" in sql_lower:
            # Для поручений пользователь видит только поручения за последний месяц
            # Используем поле creationdatetime, которое генерирует Vanna AI
            sql = append_condition(sql, f"creationdatetime >= CURRENT_DATE - INTERVAL '1 month'")
        elif "from tbl_business_unit" in sql_lower:
            # Для клиентов пользователь видит только активных клиентов
            sql = append_condition(sql, f"business_unit_name IS NOT NULL")
        elif "from tbl_incoming_payments" in sql_lower:
            # Для платежей пользователь видит только платежи за последний месяц
            sql = append_condition(sql, f"payment_date >= CURRENT_DATE - INTERVAL '1 month'")
    
    elif role == "manager":
        # Менеджеры видят данные только своего отдела (по переданному department)
        if "from equsers" in sql_lower:
            # Ограничиваем по отделу (поле department существует в схеме)
            if db_pool is not None:
                sql = append_condition(sql, f"department = (SELECT id FROM eq_departments WHERE name = '{department}')")
            else:
                sql = append_condition(sql, f"department = '{department}'")
        elif "from eq_departments" in sql_lower:
            # Ограничиваем по названию отдела (поле name существует в схеме)
            sql = append_condition(sql, f"name = '{department}'")
        elif "from tbl_principal_assignment" in sql_lower:
            # Для поручений менеджер видит поручения за последние 3 месяца
            # Используем поле creationdatetime, которое генерирует Vanna AI
            sql = append_condition(sql, f"creationdatetime >= CURRENT_DATE - INTERVAL '3 months'")
        elif "from tbl_business_unit" in sql_lower:
            # Для клиентов менеджер видит всех клиентов
            pass  # Без ограничений
        elif "from tbl_incoming_payments" in sql_lower:
            # Для платежей менеджер видит платежи за последние 6 месяцев
            sql = append_condition(sql, f"payment_date >= CURRENT_DATE - INTERVAL '6 months'")
    
    elif role == "admin":
        # Админы видят все данные (без дополнительных ограничений)
        pass
    
    logger.info(f"SQL после применения ограничений: {sql}")
    # Добавляем завершающую точку с запятой для консистентного отображения
    return sql.strip() + ";"

async def simulate_sql_execution(sql: str, login: str, role: str, department: str) -> Dict[str, Any]:
    """
    Имитация выполнения SQL запроса с правильными ролевыми ограничениями
    """
    logger.info(f"Имитация выполнения SQL для роли: {role}, login: {login}")
    
    # Простая логика определения таблицы и возврата данных
    sql_lower = sql.lower()
    
    if "equsers" in sql_lower:
        data = MOCK_DATA["equsers"].copy()
        columns = ["id", "login", "email", "department", "firstname", "surname"]
        
        # Применение ролевых ограничений
        if role == "user":
            # Пользователи видят только свои данные
            data = [row for row in data if row.get("login") == login]
        elif role == "manager":
            # Менеджеры видят только свой отдел
            data = [row for row in data if row.get("department") == department]
        # admin видит все данные без ограничений
        
    elif "eq_departments" in sql_lower:
        data = MOCK_DATA["eq_departments"].copy()
        columns = ["id", "name", "code"]
        
        # Применение ролевых ограничений
        if role == "manager":
            # Менеджеры видят только свой отдел
            data = [row for row in data if row.get("name") == department]
        # admin и user видят все отделы
        
    elif "tbl_business_unit" in sql_lower:
        data = MOCK_DATA["tbl_business_unit"].copy()
        columns = ["id", "business_unit_name", "inn", "phone"]
        
        # Применение ролевых ограничений
        if role == "user":
            # Пользователи видят только свои данные
            data = [row for row in data if row.get("created_by") == login]
        # admin и manager видят все данные
        
    elif "tbl_principal_assignment" in sql_lower:
        data = MOCK_DATA["tbl_principal_assignment"].copy()
        columns = ["id", "assignment_number", "amount", "business_unit_id", "login"]
        
        # Применение ролевых ограничений
        if role == "user":
            # Пользователи видят только свои поручения
            data = [row for row in data if row.get("login") == login]
        elif role == "manager":
            # Менеджеры видят только свой отдел
            # для простоты сопоставляем department по имени 'IT'->"1", 'Sales'->"2", 'Support'->"3"
            dept_id_map = {"IT": "1", "Sales": "2", "Support": "3"}
            target_dept_id = dept_id_map.get(department, None)
            if target_dept_id is not None:
                data = [row for row in data if row.get("department_id") == target_dept_id]
        # admin видит все данные
        
    else:
        data = []
        columns = []
    
    logger.info(f"Результат для роли {role}: {len(data)} строк")
    return {
        "data": data,
        "columns": columns,
        "row_count": len(data)
    }


async def execute_sql_against_db(sql: str) -> Dict[str, Any]:
    """Выполнение SELECT против реальной БД заказчика."""
    if db_pool is None:
        raise HTTPException(status_code=503, detail="База данных недоступна (нет подключения)")
    sql_stripped = sql.strip()
    logger.info(f"Выполнение SQL в БД: {sql_stripped}")
    if not sql_stripped.lower().startswith("select"):
        raise HTTPException(status_code=400, detail="Разрешены только SELECT запросы")
    try:
        async with db_pool.acquire() as conn:
            stmt = await conn.prepare(sql_stripped)
            records = await stmt.fetch()
            columns = list(records[0].keys()) if records else []
            data = [dict(r) for r in records]
            return {"data": data, "columns": columns, "row_count": len(data)}
    except Exception as e:
        logger.error(f"DB error: {e}")
        logger.error(f"SQL был: {sql_stripped}")
        raise HTTPException(status_code=500, detail=f"DB error: {str(e)}")

def get_accessible_tables(role: str) -> List[str]:
    """
    Получение списка доступных таблиц для роли
    """
    if role == "admin":
        return ["equsers", "eq_departments", "tbl_business_unit", "tbl_principal_assignment", "tbl_incoming_payments"]
    elif role == "manager":
        return ["equsers", "tbl_business_unit", "tbl_principal_assignment"]
    else:
        return ["equsers"]

def get_rls_policies(role: str) -> Dict[str, str]:
    """
    Получение политик Row Level Security для роли
    """
    if role == "admin":
        return {}
    elif role == "manager":
        return {
            "equsers": "department = current_user_department()",
            "tbl_principal_assignment": "manager_id = current_user_id()"
        }
    else:
        return {
            "equsers": "id = current_user_id()",
            "tbl_business_unit": "created_by = current_user_id()"
        }

def get_applied_restrictions(login: str, role: str) -> List[str]:
    """
    Получение списка примененных ограничений
    """
    restrictions = []
    
    if role == "user":
        restrictions.append(f"Пользователь {login} видит только свои данные")
    elif role == "manager":
        restrictions.append(f"Менеджер {login} видит данные своего отдела")
    elif role == "admin":
        restrictions.append("Администратор имеет полный доступ")
    
    return restrictions


@mock_app.get("/api/users/sample")
async def get_sample_users(limit: int = 50):
    """Возвращает список реальных пользователей из БД (login, email, department)."""
    if db_pool is None:
        raise HTTPException(status_code=503, detail="База данных недоступна")
    query = "SELECT login, email, department FROM equsers WHERE deleted = false AND login IS NOT NULL LIMIT $1"
    try:
        async with db_pool.acquire() as conn:
            rows = await conn.fetch(query, limit)
            users = [{"login": r["login"], "email": r["email"], "department": r["department"]} for r in rows]
            return {"success": True, "users": users}
    except Exception as e:
        logger.error(f"DB error in get_sample_users: {e}")
        raise HTTPException(status_code=500, detail=f"DB error: {str(e)}")


@mock_app.get("/api/departments")
async def get_departments():
    """Возвращает список отделов из БД (id, name, code)."""
    if db_pool is None:
        raise HTTPException(status_code=503, detail="База данных недоступна")
    query = "SELECT id, name, code FROM eq_departments WHERE deleted = false"
    try:
        async with db_pool.acquire() as conn:
            rows = await conn.fetch(query)
            deps = [{"id": str(r["id"]), "name": r["name"], "code": r["code"]} for r in rows]
            return {"success": True, "departments": deps}
    except Exception as e:
        logger.error(f"DB error in get_departments: {e}")
        raise HTTPException(status_code=500, detail=f"DB error: {str(e)}")
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(mock_app, host="0.0.0.0", port=8080)
