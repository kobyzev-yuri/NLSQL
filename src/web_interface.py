"""
Тестовый веб-интерфейс для отладки NL→SQL системы
Простой HTML интерфейс для тестирования pipeline
"""

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
import httpx
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import httpx
import logging
import os
from typing import Optional, Dict
from src.vanna.vanna_pgvector_native import create_native_vanna_client
from src.utils.plan_sql_converter import sql_to_plan

logger = logging.getLogger(__name__)

# Создание FastAPI приложения для веб-интерфейса
web_app = FastAPI(
    title="NL→SQL Web Interface",
    description="Тестовый веб-интерфейс для отладки NL→SQL системы",
    version="1.0.0"
)

# Настройка шаблонов
templates = Jinja2Templates(directory="templates")

# Конфигурация
NL_SQL_API_URL = "http://localhost:8000"
MOCK_CUSTOMER_API_URL = "http://localhost:8080"

# Инициализация обученного Vanna AI агента
def get_vanna_agent():
    """Получение обученного Vanna AI агента"""
    try:
        # Переменные окружения должны быть заданы снаружи (не хардкодим ключи в коде)
        # PROXYAPI_KEY, PROXYAPI_BASE_URL, PROXYAPI_CHAT_MODEL
        
        # Создаем обученного агента
        vanna = create_native_vanna_client(use_proxyapi=True)
        logger.info("✅ Обученный Vanna AI агент инициализирован")
        return vanna
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации Vanna AI агента: {e}")
        return None

# Глобальная переменная для агента
vanna_agent = None

@web_app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """
    Главная страница веб-интерфейса
    """
    return """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>NL→SQL Тестовый Интерфейс v2</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 {
                color: #333;
                text-align: center;
                margin-bottom: 30px;
            }
            .form-group {
                margin-bottom: 20px;
            }
            label {
                display: block;
                margin-bottom: 5px;
                font-weight: bold;
                color: #555;
            }
            input, select, textarea {
                width: 100%;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 5px;
                font-size: 14px;
            }
            textarea {
                height: 100px;
                resize: vertical;
            }
            button {
                background-color: #007bff;
                color: white;
                padding: 12px 24px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
                margin-right: 10px;
            }
            button:hover {
                background-color: #0056b3;
            }
            .result {
                margin-top: 20px;
                padding: 15px;
                background-color: #f8f9fa;
                border-radius: 5px;
                border-left: 4px solid #007bff;
            }
            .error {
                border-left-color: #dc3545;
                background-color: #f8d7da;
            }
            .success {
                border-left-color: #28a745;
                background-color: #d4edda;
            }
            .loading {
                text-align: center;
                color: #666;
            }
            .user-context {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 15px;
                margin-bottom: 20px;
            }
            .api-status {
                display: flex;
                gap: 20px;
                margin-bottom: 20px;
            }
            .status-indicator {
                padding: 5px 10px;
                border-radius: 3px;
                font-size: 12px;
                font-weight: bold;
            }
            .status-healthy {
                background-color: #d4edda;
                color: #155724;
            }
            .status-unhealthy {
                background-color: #f8d7da;
                color: #721c24;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 NL→SQL Тестовый Интерфейс</h1>
            
            <div class="api-status">
                <div>
                    <span>NL→SQL API:</span>
                    <span id="nl-sql-status" class="status-indicator status-unhealthy">Проверка...</span>
                </div>
                <div>
                    <span>Mock Customer API:</span>
                    <span id="customer-api-status" class="status-indicator status-unhealthy">Проверка...</span>
                </div>
            </div>
            
            <form id="queryForm">
                <div class="user-context">
                    <div class="form-group">
                        <label for="user_id">ID Пользователя:</label>
                        <select id="user_id" name="user_id">
                            <option value="admin">admin (Администратор)</option>
                            <option value="manager">manager (Менеджер)</option>
                            <option value="user">user (Пользователь)</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="role">Роль:</label>
                        <select id="role" name="role">
                            <option value="admin">admin</option>
                            <option value="manager">manager</option>
                            <option value="user">user</option>
                        </select>
                    </div>
                </div>
                
                <div class="form-group">
                    <label for="question">Вопрос на русском языке:</label>
                    <textarea id="question" name="question" placeholder="Например: Покажи всех пользователей, Сколько клиентов в системе?, Поручения за последний месяц"></textarea>
                </div>

                <div class="form-group">
                    <label>Быстрые примеры:</label>
                    <div style="display:flex; flex-wrap: wrap; gap: 8px;">
                        <button type="button" onclick="setQuestion('Покажи всех пользователей')">Пользователи</button>
                        <button type="button" onclick="setQuestion('Сколько клиентов в системе?')">Счёт клиентов</button>
                        <button type="button" onclick="setQuestion('Покажи поручения за последний месяц')">Поручения (30д)</button>
                        <button type="button" onclick="setQuestion('Статистика по отделам')">Статистика отделов</button>
                        <button type="button" onclick="setQuestion('Активные пользователи IT отдела')">Активные IT</button>
                        <button type="button" onclick="setQuestion('Платежи за сегодня по клиентам')">Платежи сегодня</button>
                        <button type="button" onclick="setQuestion('Поручения менеджера manager')">Поручения manager</button>
                        <button type="button" onclick="setQuestion('Список бизнес-единиц с ИНН')">Бизнес-единицы с ИНН</button>
                    </div>
                </div>
                
                <div class="form-group">
                    <label for="department">Отдел (опционально):</label>
                    <input type="text" id="department" name="department" placeholder="IT, Sales, Support">
                </div>
                
                <button type="button" onclick="generateSQL()">🔍 Генерировать SQL</button>
                <button type="button" onclick="executeQuery()">⚡ Выполнить запрос</button>
                <button type="button" onclick="clearResults()">🗑️ Очистить</button>
            </form>
            
            <div id="result" class="result" style="display: none;">
                <h3>Результат:</h3>
                <div id="resultContent"></div>
            </div>
        </div>
        
        <script>
            function setQuestion(text) {
                document.getElementById('question').value = text;
            }
            // Проверка статуса API при загрузке
            window.onload = function() {
                // Принудительная очистка кэша
                if ('caches' in window) {
                    caches.keys().then(function(names) {
                        for (let name of names) {
                            caches.delete(name);
                        }
                    });
                }
                checkAPIStatus();
                // Заполняем дефолтный вопрос для быстрого теста
                setQuestion('Покажи всех пользователей');
                // Переодическая проверка статуса API (на случай позднего старта)
                setTimeout(checkAPIStatus, 1500);
                setInterval(checkAPIStatus, 10000);
                // Загрузка реальных пользователей и отделов
                loadRealUsersAndDepartments();
            };

            async function loadRealUsersAndDepartments() {
                try {
                    const [usersResp, depsResp] = await Promise.all([
                        fetch('http://localhost:8080/api/users/sample'),
                        fetch('http://localhost:8080/api/departments')
                    ]);
                    const users = (await usersResp.json()).users || [];
                    const deps = (await depsResp.json()).departments || [];
                    const userSel = document.getElementById('user_id');
                    const roleSel = document.getElementById('role');
                    const depInput = document.getElementById('department');
                    if (users.length > 0) {
                        userSel.innerHTML = '';
                        users.slice(0, 50).forEach(u => {
                            const opt = document.createElement('option');
                            opt.value = u.login;
                            opt.textContent = `${u.login} (${u.email || 'no-email'})`;
                            userSel.appendChild(opt);
                        });
                        // по умолчанию роль user
                        roleSel.value = 'user';
                    }
                    if (deps.length > 0) {
                        // автодополнение первого отдела
                        depInput.value = deps[0].name || '';
                    }
                } catch (e) {
                    console.warn('Не удалось загрузить пользователей/отделы:', e);
                }
            }
            
            async function checkAPIStatus() {
                // Проверка NL→SQL API
                try {
                    const response = await fetch('http://localhost:8000/health');
                    const data = await response.json();
                    document.getElementById('nl-sql-status').textContent = data.status === 'healthy' ? 'Работает' : 'Ошибка';
                    document.getElementById('nl-sql-status').className = 'status-indicator ' + (data.status === 'healthy' ? 'status-healthy' : 'status-unhealthy');
                } catch (error) {
                    document.getElementById('nl-sql-status').textContent = 'Недоступен';
                    document.getElementById('nl-sql-status').className = 'status-indicator status-unhealthy';
                }
                
                // Проверка Mock Customer API
                try {
                    const response = await fetch('http://localhost:8080/health?v=' + Date.now());
                    const data = await response.json();
                    document.getElementById('customer-api-status').textContent = data.status === 'healthy' ? 'Работает' : 'Ошибка';
                    document.getElementById('customer-api-status').className = 'status-indicator ' + (data.status === 'healthy' ? 'status-healthy' : 'status-unhealthy');
                } catch (error) {
                    document.getElementById('customer-api-status').textContent = 'Недоступен';
                    document.getElementById('customer-api-status').className = 'status-indicator status-unhealthy';
                }
            }
            
            async function generateSQL() {
                const formData = new FormData(document.getElementById('queryForm'));
                const data = Object.fromEntries(formData);
                
                if (!data.question || !data.question.trim()) {
                    showResult('<h4>Ошибка:</h4><p>Введите вопрос перед генерацией SQL.</p>', 'error');
                    return;
                }
                
                showLoading();
                
                try {
                    const response = await fetch('/api/generate_chain', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ question: data.question })
                    });
                    const result = await response.json();
                    
                    if (response.ok && result.success) {
                        showResult(`
                            <h4>Сгенерированный SQL:</h4>
                            <pre style="background: #f8f9fa; padding: 10px; border-radius: 5px; overflow-x: auto;">${result.sql}</pre>
                            <h4>План (SQL→План):</h4>
                            <pre style="background: #f8f9fa; padding: 10px; border-radius: 5px; overflow-x: auto;">${JSON.stringify(result.plan, null, 2)}</pre>
                            ${result.decoded_sql ? `<h4>Декодированный из плана SQL:</h4><pre style=\"background:#f8f9fa;padding:10px;border-radius:5px;overflow-x:auto;\">${result.decoded_sql}</pre>` : ''}
                            <p style="margin-top:8px;color:#555;">Для финального SQL с ролевыми ограничениями нажмите «Выполнить запрос».</p>
                        `, 'success');
                    } else {
                        showResult(`<h4>Ошибка:</h4><p>${result.error || result.detail || 'Неизвестная ошибка'}</p>`, 'error');
                    }
                } catch (error) {
                    showResult(`<h4>Ошибка подключения:</h4><p>${error.message}</p>`, 'error');
                }
            }
            
            async function executeQuery() {
                const formData = new FormData(document.getElementById('queryForm'));
                const data = Object.fromEntries(formData);
                
                if (!data.question || !data.question.trim()) {
                    showResult('<h4>Ошибка:</h4><p>Введите вопрос перед выполнением запроса.</p>', 'error');
                    return;
                }
                
                showLoading();
                
                try {
                    const response = await fetch('/api/execute_chain', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            question: data.question,
                            user_id: data.user_id,
                            role: data.role,
                            department: data.department
                        })
                    });
                    const result = await response.json();
                    
                    if (response.ok && result.success) {
                        let tableHTML = '';
                        if (result.data && result.data.length > 0) {
                            tableHTML = '<h4>Результаты запроса:</h4>';
                            tableHTML += '<table border="1" style="width: 100%; border-collapse: collapse; margin-top: 10px;">';
                            tableHTML += '<tr style="background-color: #f8f9fa;">';
                            result.columns.forEach(col => { tableHTML += `<th style=\"padding: 8px; text-align: left;\">${col}</th>`; });
                            tableHTML += '</tr>';
                            result.data.forEach(row => {
                                tableHTML += '<tr>';
                                result.columns.forEach(col => { tableHTML += `<td style=\"padding: 8px;\">${row[col] || ''}</td>`; });
                                tableHTML += '</tr>';
                            });
                            tableHTML += '</table>';
                        }
                        
                        showResult(`
                            <h4>Декодированный из плана SQL:</h4>
                            <pre style="background: #f8f9fa; padding: 10px; border-radius: 5px; overflow-x: auto;">${result.decoded_sql}</pre>
                            <h4>Финальный SQL (с ролевыми ограничениями):</h4>
                            <pre style="background: #f8f9fa; padding: 10px; border-radius: 5px; overflow-x: auto;">${result.final_sql}</pre>
                            <p><strong>Строк:</strong> ${result.row_count}</p>
                            <p><strong>Время выполнения:</strong> ${result.execution_time.toFixed(3)}с</p>
                            ${result.restrictions && result.restrictions.length ? `<p><strong>Ограничения:</strong> ${result.restrictions.join(', ')}</p>` : ''}
                            ${tableHTML}
                        `, 'success');
                    } else {
                        showResult(`<h4>Ошибка:</h4><p>${result.error || result.detail || 'Неизвестная ошибка'}</p>`, 'error');
                    }
                } catch (error) {
                    showResult(`<h4>Ошибка подключения:</h4><p>${error.message}</p>`, 'error');
                }
            }
            
            function showLoading() {
                document.getElementById('result').style.display = 'block';
                document.getElementById('result').className = 'result loading';
                document.getElementById('resultContent').innerHTML = '⏳ Обработка запроса...';
            }
            
            function showResult(content, type) {
                document.getElementById('result').style.display = 'block';
                document.getElementById('result').className = `result ${type}`;
                document.getElementById('resultContent').innerHTML = content;
            }
            
            function clearResults() {
                document.getElementById('result').style.display = 'none';
                document.getElementById('question').value = '';
            }
            
            // Синхронизация user_id и role
            document.getElementById('user_id').addEventListener('change', function() {
                document.getElementById('role').value = this.value;
            });
        </script>
    </body>
    </html>
    """

@web_app.post("/api/generate_chain")
async def api_generate_chain(payload: Dict[str, str]):
    try:
        question = payload.get("question", "").strip()
        if not question:
            return JSONResponse(status_code=400, content={"success": False, "error": "question is required"})

        # Получение SQL от Core API
        async with httpx.AsyncClient() as client:
            r = await client.post("http://localhost:8000/query", json={
                "question": question,
                "user_id": "web_ui",
                "role": "admin",
                "department": "IT",
                "context": {}
            })
            r.raise_for_status()
            sql_resp = r.json()
            sql = sql_resp.get("sql", "")

        # Построение плана
        plan = sql_to_plan(sql)

        # Пробуем прогнать план через Mock API (без исполнения)
        decoded_sql = None
        try:
            async with httpx.AsyncClient() as client:
                r2 = await client.post("http://localhost:8080/api/plan/execute", json={
                    "plan": plan,
                    "user_context": {"user_id": "admin", "role": "admin", "department": "IT"},
                    "request_id": "web_ui_generate_chain"
                })
                if r2.status_code == 200:
                    decoded_sql = r2.json().get("decoded_sql")
        except Exception:
            pass

        return {"success": True, "sql": sql, "plan": plan, "decoded_sql": decoded_sql}
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})


@web_app.post("/api/execute_chain")
async def api_execute_chain(payload: Dict[str, str]):
    try:
        question = payload.get("question", "").strip()
        user_id = payload.get("user_id", "user")
        role = payload.get("role", "user")
        department = payload.get("department", "Support")
        if not question:
            return JSONResponse(status_code=400, content={"success": False, "error": "question is required"})

        # Получение SQL от Core API
        async with httpx.AsyncClient() as client:
            r = await client.post("http://localhost:8000/query", json={
                "question": question,
                "user_id": user_id,
                "role": role,
                "department": department,
                "context": {}
            })
            r.raise_for_status()
            sql_resp = r.json()
            sql = sql_resp.get("sql", "")

        # Построение плана
        plan = sql_to_plan(sql)

        # Выполнение: если вопрос про платежи или план без таблиц/падает — используем прямой SQL
        exec_resp = None
        async with httpx.AsyncClient() as client:
            try:
                if ('платеж' in question.lower() or 'payment' in question.lower()) or not plan.get("tables"):
                    raise RuntimeError("empty_plan_tables")
                r2 = await client.post("http://localhost:8080/api/plan/execute", json={
                    "plan": plan,
                    "user_context": {"user_id": user_id, "role": role, "department": department},
                    "request_id": "web_ui_execute_chain"
                })
                r2.raise_for_status()
                exec_resp = r2.json()
            except Exception:
                # Фоллбек: используем исходный SQL; быстрые подстановки для платежей
                safe_sql = sql
                safe_sql = safe_sql.replace("amount_payment_rubles", "credit").replace("business_unit_id", "client_name")
                r3 = await client.post("http://localhost:8080/api/sql/execute", json={
                    "sql_template": safe_sql,
                    "user_context": {"user_id": user_id, "role": role, "department": department},
                    "request_id": "web_ui_execute_chain_sql"
                })
                r3.raise_for_status()
                j = r3.json()
                exec_resp = {
                    "decoded_sql": sql,
                    "final_sql": j.get("final_sql", safe_sql),
                    "data": j.get("data", []),
                    "columns": j.get("columns", []),
                    "row_count": j.get("row_count", 0),
                    "execution_time": j.get("execution_time", 0.0),
                    "restrictions_applied": j.get("restrictions", [])
                }

        return {
            "success": True,
            "decoded_sql": exec_resp.get("decoded_sql"),
            "final_sql": exec_resp.get("final_sql"),
            "data": exec_resp.get("data", []),
            "columns": exec_resp.get("columns", []),
            "row_count": exec_resp.get("row_count", 0),
            "execution_time": exec_resp.get("execution_time", 0.0),
            "restrictions": exec_resp.get("restrictions_applied", [])
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})

@web_app.get("/api/status")
async def get_api_status():
    """
    Получение статуса всех API
    """
    status = {
        "nl_sql_api": {"status": "unknown", "url": NL_SQL_API_URL},
        "customer_api": {"status": "unknown", "url": MOCK_CUSTOMER_API_URL}
    }
    
    # Проверка NL→SQL API
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{NL_SQL_API_URL}/health", timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                status["nl_sql_api"]["status"] = data.get("status", "unknown")
                status["nl_sql_api"]["components"] = data.get("components", {})
    except Exception as e:
        status["nl_sql_api"]["error"] = str(e)
    
    # Проверка Mock Customer API
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MOCK_CUSTOMER_API_URL}/health", timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                status["customer_api"]["status"] = data.get("status", "unknown")
    except Exception as e:
        status["customer_api"]["error"] = str(e)
    
    return status

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(web_app, host="0.0.0.0", port=3000)
