"""
Тестовый веб-интерфейс для отладки NL→SQL системы
Простой HTML интерфейс для тестирования pipeline
"""

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import httpx
import logging
import os
from typing import Optional
from src.vanna.vanna_pgvector_native import create_native_vanna_client

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
        # Загружаем переменные окружения для ProxyAPI
        os.environ['PROXYAPI_KEY'] = 'sk-
        os.environ['PROXYAPI_BASE_URL'] = 'https://api.proxyapi.ru/openai/v1'
        os.environ['PROXYAPI_CHAT_MODEL'] = 'gpt-4o'
        
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
            };
            
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
                    const response = await fetch('http://localhost:8081/health?v=' + Date.now());
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
                
                showLoading();
                
                try {
                    const response = await fetch('http://localhost:8000/query', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(data)
                    });
                    
                    const result = await response.json();
                    
                    if (response.ok) {
                        showResult(`
                            <h4>Сгенерированный SQL:</h4>
                            <pre style="background: #f8f9fa; padding: 10px; border-radius: 5px; overflow-x: auto;">${result.sql}</pre>
                            <p><strong>Вопрос:</strong> ${result.question}</p>
                            <p><strong>Пользователь:</strong> ${result.user_id}</p>
                            <p><strong>Время:</strong> ${new Date(result.timestamp).toLocaleString()}</p>
                        `, 'success');
                    } else {
                        showResult(`<h4>Ошибка:</h4><p>${result.detail || 'Неизвестная ошибка'}</p>`, 'error');
                    }
                } catch (error) {
                    showResult(`<h4>Ошибка подключения:</h4><p>${error.message}</p>`, 'error');
                }
            }
            
            async function executeQuery() {
                const formData = new FormData(document.getElementById('queryForm'));
                const data = Object.fromEntries(formData);
                
                showLoading();
                
                try {
                    const response = await fetch('http://localhost:8000/query/execute', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(data)
                    });
                    
                    const result = await response.json();
                    
                    if (response.ok) {
                        let tableHTML = '';
                        if (result.data && result.data.length > 0) {
                            tableHTML = '<h4>Результаты запроса:</h4>';
                            tableHTML += '<table border="1" style="width: 100%; border-collapse: collapse; margin-top: 10px;">';
                            
                            // Заголовки
                            tableHTML += '<tr style="background-color: #f8f9fa;">';
                            result.columns.forEach(col => {
                                tableHTML += `<th style="padding: 8px; text-align: left;">${col}</th>`;
                            });
                            tableHTML += '</tr>';
                            
                            // Данные
                            result.data.forEach(row => {
                                tableHTML += '<tr>';
                                result.columns.forEach(col => {
                                    tableHTML += `<td style="padding: 8px;">${row[col] || ''}</td>`;
                                });
                                tableHTML += '</tr>';
                            });
                            
                            tableHTML += '</table>';
                        }
                        
                        showResult(`
                            <h4>Выполненный SQL:</h4>
                            <pre style="background: #f8f9fa; padding: 10px; border-radius: 5px; overflow-x: auto;">${result.sql}</pre>
                            <p><strong>Строк:</strong> ${result.row_count}</p>
                            <p><strong>Время выполнения:</strong> ${result.execution_time.toFixed(3)}с</p>
                            ${tableHTML}
                        `, 'success');
                    } else {
                        showResult(`<h4>Ошибка:</h4><p>${result.detail || 'Неизвестная ошибка'}</p>`, 'error');
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
