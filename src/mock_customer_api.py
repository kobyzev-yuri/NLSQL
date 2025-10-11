"""
Mock API заказчика для отладки NL→SQL системы
Имитирует функционал API заказчика для тестирования pipeline
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import asyncio
import random
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Создание FastAPI приложения для mock API
mock_app = FastAPI(
    title="Mock Customer API",
    description="Mock API заказчика для отладки NL→SQL системы",
    version="1.0.0"
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
        {"id": "1", "login": "admin", "email": "admin@company.com", "department": "IT"},
        {"id": "2", "login": "manager1", "email": "manager1@company.com", "department": "Sales"},
        {"id": "3", "login": "user1", "email": "user1@company.com", "department": "Support"},
    ],
    "tbl_business_unit": [
        {"id": "1", "business_unit_name": "ООО Ромашка", "inn": "1234567890", "phone": "+7-495-123-45-67"},
        {"id": "2", "business_unit_name": "ИП Иванов", "inn": "0987654321", "phone": "+7-495-765-43-21"},
    ],
    "tbl_principal_assignment": [
        {"id": "1", "assignment_number": "A001", "amount": 100000, "business_unit_id": "1"},
        {"id": "2", "assignment_number": "A002", "amount": 50000, "business_unit_id": "2"},
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

@mock_app.get("/health")
async def health_check():
    """Проверка здоровья mock API"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "database": "connected",
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
        
        # Получение контекста пользователя
        user_id = request.user_context.get("user_id", "user")
        role = request.user_context.get("role", "user")
        department = request.user_context.get("department", "Support")
        
        # Применение ролевых ограничений
        restricted_sql = apply_role_restrictions(
            request.sql_template, 
            user_id, 
            role, 
            department
        )
        
        # Имитация выполнения SQL
        result = await simulate_sql_execution(restricted_sql, user_id, role)
        
        # Имитация времени выполнения
        execution_time = random.uniform(0.01, 0.5)
        await asyncio.sleep(execution_time)
        
        logger.info(f"SQL выполнен успешно, получено {result.get('row_count', 0)} строк")
        
        return {
            "success": True,
            "final_sql": restricted_sql,
            "data": result.get("data", []),
            "columns": result.get("columns", []),
            "row_count": result.get("row_count", 0),
            "execution_time": execution_time,
            "user_context": request.user_context,
            "restrictions_applied": get_applied_restrictions(user_id, role)
        }
        
    except Exception as e:
        logger.error(f"Ошибка выполнения SQL: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка выполнения SQL: {str(e)}")

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

def apply_role_restrictions(sql: str, user_id: str, role: str, department: str) -> str:
    """
    Применение ролевых ограничений к SQL запросу
    """
    logger.info(f"Применение ограничений для роли: {role}")
    
    # Базовые ограничения по ролям
    if role == "user":
        # Пользователи видят только свои данные
        if "equsers" in sql.lower():
            sql += f" AND id = '{user_id}'"
        elif "tbl_business_unit" in sql.lower():
            sql += f" AND created_by = '{user_id}'"
    
    elif role == "manager":
        # Менеджеры видят данные своего отдела
        if "equsers" in sql.lower():
            sql += f" AND department = '{department}'"
        elif "tbl_principal_assignment" in sql.lower():
            sql += f" AND manager_id = '{user_id}'"
    
    elif role == "admin":
        # Админы видят все данные (без дополнительных ограничений)
        pass
    
    return sql

async def simulate_sql_execution(sql: str, user_id: str, role: str) -> Dict[str, Any]:
    """
    Имитация выполнения SQL запроса
    """
    logger.info(f"Имитация выполнения SQL для роли: {role}")
    
    # Простая логика определения таблицы и возврата данных
    sql_lower = sql.lower()
    
    if "equsers" in sql_lower:
        data = MOCK_DATA["equsers"]
        columns = ["id", "login", "email", "department"]
    elif "tbl_business_unit" in sql_lower:
        data = MOCK_DATA["tbl_business_unit"]
        columns = ["id", "business_unit_name", "inn", "phone"]
    elif "tbl_principal_assignment" in sql_lower:
        data = MOCK_DATA["tbl_principal_assignment"]
        columns = ["id", "assignment_number", "amount", "business_unit_id"]
    else:
        data = []
        columns = []
    
    # Применение ограничений по роли
    if role == "user":
        data = [row for row in data if row.get("id") == user_id]
    elif role == "manager":
        data = data[:2]  # Менеджеры видят ограниченный набор
    
    return {
        "data": data,
        "columns": columns,
        "row_count": len(data)
    }

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

def get_applied_restrictions(user_id: str, role: str) -> List[str]:
    """
    Получение списка примененных ограничений
    """
    restrictions = []
    
    if role == "user":
        restrictions.append(f"Пользователь {user_id} видит только свои данные")
    elif role == "manager":
        restrictions.append(f"Менеджер {user_id} видит данные своего отдела")
    elif role == "admin":
        restrictions.append("Администратор имеет полный доступ")
    
    return restrictions

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(mock_app, host="0.0.0.0", port=8080)
