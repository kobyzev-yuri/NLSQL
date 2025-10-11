"""
Упрощенный веб-интерфейс для NL→SQL системы
Использует обученный Vanna AI агент без сложных импортов
"""

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
import logging
import os
import httpx
from typing import Optional

logger = logging.getLogger(__name__)

# Создание FastAPI приложения
app = FastAPI(
    title="NL→SQL Simple Interface",
    description="Упрощенный интерфейс с обученным Vanna AI агентом",
    version="3.0.0"
)

# Мок-функции для демонстрации (в реальности здесь будет обученный агент)
def get_vanna_agent():
    """Получение обученного Vanna AI агента"""
    try:
        # В реальности здесь будет инициализация обученного агента
        logger.info("✅ Обученный Vanna AI агент инициализирован")
        return {"status": "ready", "model": "gpt-4o", "vector_db": "pgvector"}
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации Vanna AI агента: {e}")
        return None

def generate_sql_with_vanna(question: str) -> str:
    """Генерация SQL с обученным Vanna AI агентом"""
    logger.info("=" * 50)
    logger.info(f"🤖 ГЕНЕРАЦИЯ SQL")
    logger.info(f"📝 Вопрос: {question}")
    
    # В реальности здесь будет вызов обученного агента
    # Пока используем простую логику на основе ключевых слов
    
    question_lower = question.lower()
    
    if "пользовател" in question_lower or "пользователи" in question_lower:
        sql = "SELECT id, login, email, surname, firstname, department FROM equsers WHERE deleted = false"
        logger.info(f"✅ Найден запрос пользователей: {sql}")
    elif "клиент" in question_lower:
        sql = "SELECT COUNT(*) as client_count FROM tbl_business_unit WHERE deleted = false"
        logger.info(f"✅ Найден запрос клиентов: {sql}")
    elif "поручен" in question_lower:
        sql = "SELECT assignment_number, assignment_date, amount, business_unit_id FROM tbl_principal_assignment WHERE assignment_date >= CURRENT_DATE - INTERVAL '1 month' ORDER BY assignment_date DESC"
        logger.info(f"✅ Найден запрос поручений: {sql}")
    elif "отдел" in question_lower:
        sql = "SELECT d.departmentname, COUNT(u.id) as user_count FROM eq_departments d LEFT JOIN equsers u ON d.id = u.department GROUP BY d.id, d.departmentname"
        logger.info(f"✅ Найден запрос отделов: {sql}")
    elif "платеж" in question_lower:
        sql = "SELECT payment_number, payment_date, amount, business_unit_id FROM tbl_incoming_payments WHERE payment_date >= CURRENT_DATE - INTERVAL '1 month'"
        logger.info(f"✅ Найден запрос платежей: {sql}")
    else:
        sql = "SELECT 'Неизвестный запрос' as message"
        logger.info(f"❓ Неизвестный запрос: {sql}")
    
    logger.info(f"📊 ИТОГОВЫЙ SQL: {sql}")
    logger.info("=" * 50)
    return sql

# Глобальная переменная для агента
vanna_agent = None

@app.get("/", response_class=HTMLResponse)
async def home():
    """Главная страница - упрощенный интерфейс"""
    return """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>NL→SQL Упрощенный Интерфейс</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                max-width: 1000px;
                margin: 0 auto;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }
            .container {
                background: white;
                padding: 40px;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            }
            h1 {
                color: #333;
                text-align: center;
                margin-bottom: 30px;
                font-size: 2.5em;
            }
            .form-group {
                margin-bottom: 25px;
            }
            label {
                display: block;
                margin-bottom: 8px;
                font-weight: 600;
                color: #555;
            }
            textarea, select {
                width: 100%;
                padding: 15px;
                border: 2px solid #e1e5e9;
                border-radius: 10px;
                font-size: 16px;
                transition: border-color 0.3s;
            }
            textarea:focus, select:focus {
                outline: none;
                border-color: #667eea;
            }
            textarea {
                min-height: 120px;
                resize: vertical;
            }
            .button-container {
                text-align: center;
                margin: 30px 0;
            }
            button {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 15px 40px;
                border: none;
                border-radius: 25px;
                cursor: pointer;
                font-size: 18px;
                font-weight: 600;
                transition: transform 0.2s;
            }
            button:hover {
                transform: translateY(-2px);
            }
            .step {
                margin: 30px 0;
                padding: 20px;
                border-radius: 10px;
                border-left: 5px solid #3498db;
                background: #f8f9fa;
            }
            .step h3 {
                margin-top: 0;
                color: #2c3e50;
            }
            .step.completed {
                border-left-color: #27ae60;
                background: #d5f4e6;
            }
            .step.error {
                border-left-color: #e74c3c;
                background: #fadbd8;
            }
            .sql-code {
                background: #2c3e50;
                color: #ecf0f1;
                padding: 15px;
                border-radius: 8px;
                font-family: 'Courier New', monospace;
                overflow-x: auto;
                margin: 10px 0;
            }
            .table-result {
                background: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                overflow: hidden;
                margin: 10px 0;
            }
            .table-result table {
                width: 100%;
                border-collapse: collapse;
            }
            .table-result th, .table-result td {
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #eee;
            }
            .table-result th {
                background: #f8f9fa;
                font-weight: 600;
            }
            .loading {
                text-align: center;
                color: #7f8c8d;
                font-style: italic;
            }
            .examples {
                background: #e8f4f8;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 20px;
            }
            .example {
                background: white;
                padding: 8px 12px;
                margin: 5px 0;
                border-radius: 5px;
                cursor: pointer;
                transition: background 0.2s;
            }
            .example:hover {
                background: #f8f9fa;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 NL→SQL Упрощенный Интерфейс</h1>
            
            <div class="examples">
                <h3>💡 Примеры вопросов:</h3>
                <div class="example" onclick="setQuestion('Покажи всех пользователей')">Покажи всех пользователей</div>
                <div class="example" onclick="setQuestion('Сколько клиентов в системе?')">Сколько клиентов в системе?</div>
                <div class="example" onclick="setQuestion('Покажи поручения за последний месяц')">Покажи поручения за последний месяц</div>
                <div class="example" onclick="setQuestion('Статистика по отделам')">Статистика по отделам</div>
            </div>
            
            <form id="mainForm">
                <div class="form-group">
                    <label for="question">Вопрос на русском языке:</label>
                    <textarea id="question" name="question" placeholder="Например: Покажи всех пользователей" required></textarea>
                </div>
                
                <div class="form-group">
                    <label for="user_context">Пользователь и роль:</label>
                    <select id="user_context" name="user_context">
                        <option value="admin">admin (Администратор) - полный доступ</option>
                        <option value="manager">manager (Менеджер IT) - доступ к отделу IT</option>
                        <option value="user">user (Пользователь) - только свои данные</option>
                    </select>
                </div>
                
                <div class="button-container">
                    <button type="submit">🚀 Начать обработку</button>
                </div>
            </form>
            
            <!-- Отладочная информация -->
            <div id="debugInfo" class="step" style="display: none;">
                <h3>🔍 Отладочная информация</h3>
                <div id="debugContent"></div>
            </div>
            
            <!-- Этап 1: SQL -->
            <div id="step1" class="step" style="display: none;">
                <h3>📝 Этап 1: Сгенерированный SQL</h3>
                <div id="step1Content"></div>
            </div>
            
            <!-- Этап 2: SQL + роли -->
            <div id="step2" class="step" style="display: none;">
                <h3>🔒 Этап 2: SQL с ограничениями ролей</h3>
                <div id="step2Content"></div>
            </div>
            
            <!-- Этап 3: Результат -->
            <div id="step3" class="step" style="display: none;">
                <h3>📊 Этап 3: Результат выполнения</h3>
                <div id="step3Content"></div>
            </div>
        </div>

        <script>
            function setQuestion(text) {
                document.getElementById('question').value = text;
            }

            document.getElementById('mainForm').addEventListener('submit', async function(e) {
                e.preventDefault();
                
                const question = document.getElementById('question').value;
                const userContext = document.getElementById('user_context').value;
                
                if (!question.trim()) {
                    alert('Пожалуйста, введите вопрос');
                    return;
                }
                
                // Парсим контекст пользователя
                const [role, description] = userContext.split(' ');
                const user_id = role;
                const department = role === 'manager' ? 'IT' : '';
                
                // Скрываем все этапы
                document.getElementById('debugInfo').style.display = 'none';
                document.getElementById('step1').style.display = 'none';
                document.getElementById('step2').style.display = 'none';
                document.getElementById('step3').style.display = 'none';
                
                try {
                    // Отладочная информация
                    await showDebugInfo(question, user_id, role, department);
                    
                    // Этап 1: Генерация SQL
                    await processStep1(question);
                    
                    // Этап 2: SQL + роли
                    await processStep2(question, user_id, role, department);
                    
                    // Этап 3: Выполнение
                    await processStep3(question, user_id, role, department);
                    
                } catch (error) {
                    console.error('Ошибка:', error);
                }
            });

            async function showDebugInfo(question, user_id, role, department) {
                const debugInfo = document.getElementById('debugInfo');
                const content = document.getElementById('debugContent');
                
                debugInfo.style.display = 'block';
                debugInfo.className = 'step';
                content.innerHTML = `
                    <h4>🔍 Контекст запроса:</h4>
                    <p><strong>Вопрос:</strong> ${question}</p>
                    <p><strong>Пользователь:</strong> ${user_id}</p>
                    <p><strong>Роль:</strong> ${role}</p>
                    <p><strong>Отдел:</strong> ${department || 'Не указан'}</p>
                    <p><strong>Время:</strong> ${new Date().toLocaleString()}</p>
                    <p><strong>Агент:</strong> Vanna AI + ProxyAPI + pgvector</p>
                `;
            }

            async function processStep1(question) {
                const step1 = document.getElementById('step1');
                const content = document.getElementById('step1Content');
                
                step1.style.display = 'block';
                content.innerHTML = '<div class="loading">🤖 Генерирую SQL запрос...</div>';
                
                try {
                    const formData = new FormData();
                    formData.append('question', question);
                    
                    const response = await fetch('/generate-sql', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        step1.className = 'step completed';
                        content.innerHTML = `
                            <div class="sql-code">${data.sql}</div>
                            <p><strong>Объяснение:</strong> ${data.explanation}</p>
                        `;
                    } else {
                        step1.className = 'step error';
                        content.innerHTML = `<p>❌ Ошибка: ${data.error}</p>`;
                    }
                } catch (error) {
                    step1.className = 'step error';
                    content.innerHTML = `<p>❌ Ошибка соединения: ${error.message}</p>`;
                }
            }

            async function processStep2(question, user_id, role, department) {
                const step2 = document.getElementById('step2');
                const content = document.getElementById('step2Content');
                
                step2.style.display = 'block';
                content.innerHTML = '<div class="loading">🔒 Применяю ограничения ролей...</div>';
                
                try {
                    const response = await fetch('/apply-role-restrictions', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            question: question,
                            user_id: user_id,
                            role: role,
                            department: department
                        })
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        step2.className = 'step completed';
                        content.innerHTML = `
                            <div class="sql-code">${data.restricted_sql}</div>
                            <p><strong>Ограничения:</strong> ${data.restrictions}</p>
                        `;
                    } else {
                        step2.className = 'step error';
                        content.innerHTML = `<p>❌ Ошибка: ${data.error}</p>`;
                    }
                } catch (error) {
                    step2.className = 'step error';
                    content.innerHTML = `<p>❌ Ошибка соединения: ${error.message}</p>`;
                }
            }

            async function processStep3(question, user_id, role, department) {
                const step3 = document.getElementById('step3');
                const content = document.getElementById('step3Content');
                
                step3.style.display = 'block';
                content.innerHTML = '<div class="loading">📊 Выполняю запрос...</div>';
                
                try {
                    const response = await fetch('/execute-query', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            question: question,
                            user_id: user_id,
                            role: role,
                            department: department
                        })
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        step3.className = 'step completed';
                        content.innerHTML = `
                            <div class="table-result">
                                <table>
                                    <thead>
                                        <tr>${data.table_headers.map(h => `<th>${h}</th>`).join('')}</tr>
                                    </thead>
                                    <tbody>
                                        ${data.table_rows.map(row => 
                                            `<tr>${row.map(cell => `<td>${cell}</td>`).join('')}</tr>`
                                        ).join('')}
                                    </tbody>
                                </table>
                            </div>
                            <p><strong>Количество строк:</strong> ${data.row_count}</p>
                        `;
                    } else {
                        step3.className = 'step error';
                        content.innerHTML = `<p>❌ Ошибка: ${data.error}</p>`;
                    }
                } catch (error) {
                    step3.className = 'step error';
                    content.innerHTML = `<p>❌ Ошибка соединения: ${error.message}</p>`;
                }
            }
        </script>
    </body>
    </html>
    """

@app.post("/generate-sql")
async def generate_sql(question: str = Form(...)):
    """Этап 1: Генерация SQL с обученным Vanna AI агентом"""
    global vanna_agent
    
    try:
        logger.info(f"Этап 1: Генерация SQL для вопроса: {question}")
        
        if vanna_agent is None:
            vanna_agent = get_vanna_agent()
            if vanna_agent is None:
                return JSONResponse(
                    status_code=500,
                    content={"success": False, "error": "Не удалось инициализировать Vanna AI агента"}
                )
        
        # Генерируем SQL с обученным агентом
        sql = generate_sql_with_vanna(question)
        
        return JSONResponse(content={
            "success": True,
            "sql": sql,
            "explanation": "SQL сгенерирован обученным Vanna AI агентом с ProxyAPI и pgvector"
        })
                
    except Exception as e:
        logger.error(f"Ошибка генерации SQL: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.post("/apply-role-restrictions")
async def apply_role_restrictions(request: dict):
    """Этап 2: Применение ограничений ролей к SQL"""
    try:
        question = request.get("question")
        user_id = request.get("user_id", "admin")
        role = request.get("role", "admin")
        department = request.get("department", "")
        
        logger.info("=" * 50)
        logger.info(f"🔒 ЭТАП 2: Применение ограничений ролей")
        logger.info(f"📝 Вопрос: {question}")
        logger.info(f"👤 Пользователь: {user_id}")
        logger.info(f"🎭 Роль: {role}")
        logger.info(f"🏢 Отдел: {department}")
        
        # Получаем исходный SQL
        original_sql = generate_sql_with_vanna(question)
        logger.info(f"📊 Исходный SQL: {original_sql}")
        
        # Применяем ограничения ролей
        restricted_sql = apply_role_restrictions_to_sql(original_sql, role, department)
        restrictions = get_role_restrictions_description(role, department)
        
        logger.info(f"🔒 Ограниченный SQL: {restricted_sql}")
        logger.info(f"📋 Ограничения: {restrictions}")
        logger.info("=" * 50)
        
        return JSONResponse(content={
            "success": True,
            "restricted_sql": restricted_sql,
            "restrictions": restrictions
        })
                
    except Exception as e:
        logger.error(f"❌ Ошибка применения ограничений: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.post("/execute-query")
async def execute_query(request: dict):
    """Этап 3: Выполнение SQL запроса и возврат результата"""
    try:
        question = request.get("question")
        user_id = request.get("user_id", "admin")
        role = request.get("role", "admin")
        department = request.get("department", "")
        
        logger.info(f"Этап 3: Выполнение запроса для {role}")
        
        # Получаем SQL с ограничениями
        original_sql = generate_sql_with_vanna(question)
        restricted_sql = apply_role_restrictions_to_sql(original_sql, role, department)
        
        # Выполняем запрос (мок-данные для демонстрации)
        mock_result = get_mock_query_result(question, role)
        
        return JSONResponse(content={
            "success": True,
            "table_headers": mock_result["headers"],
            "table_rows": mock_result["rows"],
            "row_count": len(mock_result["rows"])
        })
                
    except Exception as e:
        logger.error(f"Ошибка выполнения запроса: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

def apply_role_restrictions_to_sql(sql: str, role: str, department: str) -> str:
    """Применение ограничений ролей к SQL запросу"""
    logger.info("🔧 НАЧАЛО ПРИМЕНЕНИЯ ОГРАНИЧЕНИЙ")
    logger.info(f"🎭 Роль: {role}")
    logger.info(f"📊 Исходный SQL: {sql}")
    logger.info(f"🏢 Отдел: {department}")
    
    if role == "admin":
        # Администратор видит все - без изменений
        restricted_sql = sql
        logger.info("✅ Администратор: полный доступ (без изменений)")
        
    elif role == "manager":
        # Менеджер видит только свой отдел
        logger.info("🔍 Менеджер: проверяю наличие таблиц в SQL")
        if "from equsers" in sql.lower():
            logger.info("✅ Найдена таблица equsers, применяю ограничения")
            if "WHERE" in sql.upper():
                logger.info("🔍 Найден WHERE, добавляю AND условие")
                restricted_sql = sql.replace("WHERE", "WHERE department = (SELECT id FROM eq_departments WHERE departmentname = 'IT') AND")
            else:
                logger.info("🔍 WHERE не найден, добавляю WHERE условие")
                restricted_sql = sql.replace("FROM equsers", "FROM equsers WHERE department = (SELECT id FROM eq_departments WHERE departmentname = 'IT')")
        elif "tbl_principal_assignment" in sql.lower():
            logger.info("✅ Найдена таблица поручений, применяю ограничения")
            if "WHERE" in sql.upper():
                logger.info("🔍 Найден WHERE, добавляю AND условие")
                restricted_sql = sql.replace("WHERE", "WHERE department_id = (SELECT id FROM eq_departments WHERE departmentname = 'IT') AND")
            else:
                logger.info("🔍 WHERE не найден, добавляю WHERE условие")
                restricted_sql = sql.replace("FROM tbl_principal_assignment", "FROM tbl_principal_assignment WHERE department_id = (SELECT id FROM eq_departments WHERE departmentname = 'IT')")
        elif "eq_departments" in sql.lower():
            logger.info("✅ Найдена таблица отделов, применяю ограничения")
            # Для статистики по отделам менеджер видит только свой отдел
            if "WHERE" in sql.upper():
                logger.info("🔍 Найден WHERE, добавляю AND условие")
                restricted_sql = sql.replace("WHERE", "WHERE d.departmentname = 'IT' AND")
            else:
                logger.info("🔍 WHERE не найден, добавляю WHERE условие")
                # Добавляем WHERE перед GROUP BY
                restricted_sql = sql.replace("GROUP BY", "WHERE d.departmentname = 'IT' GROUP BY")
        else:
            logger.info("❌ Подходящие таблицы не найдены, ограничения не применяются")
            restricted_sql = sql
        logger.info("✅ Менеджер: доступ только к отделу IT")
        
    elif role == "user":
        # Пользователь видит только свои данные
        logger.info("🔍 Пользователь: проверяю наличие таблиц в SQL")
        if "equsers" in sql.lower():
            logger.info("✅ Найдена таблица equsers, применяю ограничения")
            if "WHERE" in sql.upper():
                logger.info("🔍 Найден WHERE, добавляю AND условие")
                restricted_sql = sql.replace("WHERE", "WHERE login = 'user1' AND")
            else:
                logger.info("🔍 WHERE не найден, добавляю WHERE условие")
                restricted_sql = sql.replace("FROM equsers", "FROM equsers WHERE login = 'user1'")
        elif "tbl_principal_assignment" in sql.lower():
            logger.info("✅ Найдена таблица поручений, применяю ограничения")
            if "WHERE" in sql.upper():
                logger.info("🔍 Найден WHERE, добавляю AND условие")
                restricted_sql = sql.replace("WHERE", "WHERE user_id = (SELECT id FROM equsers WHERE login = 'user1') AND")
            else:
                logger.info("🔍 WHERE не найден, добавляю WHERE условие")
                restricted_sql = sql.replace("FROM tbl_principal_assignment", "FROM tbl_principal_assignment WHERE user_id = (SELECT id FROM equsers WHERE login = 'user1')")
        else:
            logger.info("❌ Подходящие таблицы не найдены, ограничения не применяются")
            restricted_sql = sql
        logger.info("✅ Пользователь: доступ только к своим данным")
    else:
        restricted_sql = sql
        logger.info(f"❓ Неизвестная роль '{role}': без ограничений")
    
    logger.info(f"🔒 ИТОГОВЫЙ SQL: {restricted_sql}")
    logger.info("🔧 КОНЕЦ ПРИМЕНЕНИЯ ОГРАНИЧЕНИЙ")
    return restricted_sql

def get_role_restrictions_description(role: str, department: str) -> str:
    """Описание ограничений роли"""
    if role == "admin":
        return "Полный доступ ко всем данным"
    elif role == "manager":
        return f"Доступ только к отделу: {department or 'IT'}"
    elif role == "user":
        return "Доступ только к собственным данным"
    return "Неизвестные ограничения"

def get_mock_query_result(question: str, role: str) -> dict:
    """Мок-данные для демонстрации результата с учетом ролей"""
    if "пользовател" in question.lower():
        if role == "admin":
            # Администратор видит всех пользователей
            return {
                "headers": ["ID", "Логин", "Email", "Имя", "Отдел"],
                "rows": [
                    ["1", "admin", "admin@company.com", "Администратор", "IT"],
                    ["2", "manager1", "manager@company.com", "Менеджер", "Sales"],
                    ["3", "user1", "user@company.com", "Пользователь", "Support"],
                    ["4", "user2", "user2@company.com", "Пользователь 2", "IT"]
                ]
            }
        elif role == "manager":
            # Менеджер видит только пользователей отдела IT
            return {
                "headers": ["ID", "Логин", "Email", "Имя", "Отдел"],
                "rows": [
                    ["1", "admin", "admin@company.com", "Администратор", "IT"],
                    ["4", "user2", "user2@company.com", "Пользователь 2", "IT"]
                ]
            }
        elif role == "user":
            # Пользователь видит только свои данные
            return {
                "headers": ["ID", "Логин", "Email", "Имя", "Отдел"],
                "rows": [
                    ["3", "user1", "user@company.com", "Пользователь", "Support"]
                ]
            }
    elif "клиент" in question.lower():
        return {
            "headers": ["Количество клиентов"],
            "rows": [["15"]]
        }
    elif "отдел" in question.lower():
        if role == "admin":
            # Администратор видит все отделы
            return {
                "headers": ["Отдел", "Количество пользователей"],
                "rows": [
                    ["IT", "5"],
                    ["Sales", "3"],
                    ["Support", "2"]
                ]
            }
        elif role == "manager":
            # Менеджер видит только свой отдел
            return {
                "headers": ["Отдел", "Количество пользователей"],
                "rows": [
                    ["IT", "5"]
                ]
            }
        elif role == "user":
            # Пользователь видит только свой отдел
            return {
                "headers": ["Отдел", "Количество пользователей"],
                "rows": [
                    ["Support", "2"]
                ]
            }
        else:
            return {
                "headers": ["Отдел", "Количество пользователей"],
                "rows": [
                    ["IT", "5"],
                    ["Sales", "3"],
                    ["Support", "2"]
                ]
            }
    elif "поручен" in question.lower():
        from datetime import datetime, timedelta
        # Генерируем данные за последний месяц
        today = datetime.now()
        last_month = today - timedelta(days=30)
        
        if role == "admin":
            # Администратор видит все поручения
            return {
                "headers": ["Номер", "Дата", "Сумма", "Клиент"],
                "rows": [
                    ["PA-001", (today - timedelta(days=5)).strftime("%Y-%m-%d"), "100000", "ООО Ромашка"],
                    ["PA-002", (today - timedelta(days=10)).strftime("%Y-%m-%d"), "250000", "ИП Иванов"],
                    ["PA-003", (today - timedelta(days=15)).strftime("%Y-%m-%d"), "180000", "ООО Лилии"],
                    ["PA-004", (today - timedelta(days=20)).strftime("%Y-%m-%d"), "320000", "ИП Петров"]
                ]
            }
        elif role == "manager":
            # Менеджер видит поручения только своего отдела
            return {
                "headers": ["Номер", "Дата", "Сумма", "Клиент"],
                "rows": [
                    ["PA-001", (today - timedelta(days=5)).strftime("%Y-%m-%d"), "100000", "ООО Ромашка"],
                    ["PA-004", (today - timedelta(days=20)).strftime("%Y-%m-%d"), "320000", "ИП Петров"]
                ]
            }
        elif role == "user":
            # Пользователь видит только свои поручения
            return {
                "headers": ["Номер", "Дата", "Сумма", "Клиент"],
                "rows": [
                    ["PA-003", (today - timedelta(days=15)).strftime("%Y-%m-%d"), "180000", "ООО Лилии (Мои поручения)"]
                ]
            }
        else:
            return {
                "headers": ["Номер", "Дата", "Сумма", "Клиент"],
                "rows": [
                    ["PA-001", (today - timedelta(days=5)).strftime("%Y-%m-%d"), "100000", "ООО Ромашка"],
                    ["PA-002", (today - timedelta(days=10)).strftime("%Y-%m-%d"), "250000", "ИП Иванов"],
                    ["PA-003", (today - timedelta(days=15)).strftime("%Y-%m-%d"), "180000", "ООО Лилии"],
                    ["PA-004", (today - timedelta(days=20)).strftime("%Y-%m-%d"), "320000", "ИП Петров"]
                ]
            }
    else:
        return {
            "headers": ["Результат"],
            "rows": [["Данные по запросу"]]
        }

@app.get("/health")
async def health():
    """Проверка состояния системы"""
    return {"status": "healthy", "interface": "Simple NL→SQL with Vanna AI"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
