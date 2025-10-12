#!/usr/bin/env python3
"""
Полный веб-интерфейс для NL→SQL системы с ролевыми ограничениями
Работает с FastAPI сервисом и Mock Customer API
"""

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
import httpx
import logging
import asyncio
from typing import Optional

logger = logging.getLogger(__name__)

# Создание FastAPI приложения
app = FastAPI(
    title="NL→SQL Full Web Interface",
    description="Полный веб-интерфейс с ролевыми ограничениями",
    version="2.0.0"
)

# Конфигурация API
NL_SQL_API_URL = "http://localhost:8000"
MOCK_CUSTOMER_API_URL = "http://localhost:8080"

@app.get("/", response_class=HTMLResponse)
async def home():
    """Главная страница с полным интерфейсом"""
    return """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>NL→SQL Полная Система</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                max-width: 1200px;
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
            .api-status {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin-bottom: 30px;
            }
            .status-card {
                padding: 15px;
                border-radius: 10px;
                text-align: center;
                font-weight: bold;
            }
            .status-healthy {
                background: #d4edda;
                color: #155724;
                border: 2px solid #c3e6cb;
            }
            .status-unhealthy {
                background: #f8d7da;
                color: #721c24;
                border: 2px solid #f5c6cb;
            }
            .form-section {
                background: #f8f9fa;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 20px;
            }
            .form-group {
                margin-bottom: 20px;
            }
            label {
                display: block;
                margin-bottom: 8px;
                font-weight: 600;
                color: #555;
            }
            input, select, textarea {
                width: 100%;
                padding: 12px;
                border: 2px solid #e1e5e9;
                border-radius: 8px;
                font-size: 16px;
                transition: border-color 0.3s;
            }
            input:focus, select:focus, textarea:focus {
                outline: none;
                border-color: #667eea;
            }
            textarea {
                resize: vertical;
                min-height: 120px;
            }
            .button-group {
                display: flex;
                gap: 10px;
                margin: 20px 0;
            }
            button {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 12px 24px;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                font-size: 16px;
                font-weight: 600;
                transition: transform 0.2s;
                flex: 1;
            }
            button:hover {
                transform: translateY(-2px);
            }
            button:disabled {
                opacity: 0.6;
                cursor: not-allowed;
                transform: none;
            }
            .result {
                margin-top: 30px;
                padding: 20px;
                background: #f8f9fa;
                border-radius: 10px;
                border-left: 5px solid #667eea;
            }
            .result.error {
                border-left-color: #dc3545;
                background: #f8d7da;
            }
            .result.success {
                border-left-color: #28a745;
                background: #d4edda;
            }
            .result.loading {
                text-align: center;
                color: #666;
                font-style: italic;
            }
            .examples {
                background: #e9ecef;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 20px;
            }
            .examples h3 {
                margin-top: 0;
                color: #495057;
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
            .user-context {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 15px;
            }
            .sql-display {
                background: #2d3748;
                color: #e2e8f0;
                padding: 15px;
                border-radius: 8px;
                font-family: 'Courier New', monospace;
                overflow-x: auto;
                margin: 10px 0;
            }
            .table-display {
                overflow-x: auto;
                margin: 10px 0;
            }
            .table-display table {
                width: 100%;
                border-collapse: collapse;
                background: white;
            }
            .table-display th, .table-display td {
                padding: 8px 12px;
                text-align: left;
                border-bottom: 1px solid #dee2e6;
            }
            .table-display th {
                background: #f8f9fa;
                font-weight: 600;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 NL→SQL Полная Система</h1>
            
            <div class="api-status">
                <div class="status-card status-unhealthy" id="nl-sql-status">
                    <div>NL→SQL API</div>
                    <div>Проверка...</div>
                </div>
                <div class="status-card status-unhealthy" id="mock-api-status">
                    <div>Mock Customer API</div>
                    <div>Проверка...</div>
                </div>
            </div>
            
            <div class="examples">
                <h3>💡 Примеры вопросов:</h3>
                <div class="example" onclick="setQuestion('Покажи всех пользователей')">Покажи всех пользователей</div>
                <div class="example" onclick="setQuestion('Список отделов')">Список отделов</div>
                <div class="example" onclick="setQuestion('Пользователи по отделам')">Пользователи по отделам</div>
                <div class="example" onclick="setQuestion('Статистика по отделам')">Статистика по отделам</div>
            </div>
            
            <form id="queryForm">
                <div class="form-section">
                    <h3>👤 Контекст пользователя</h3>
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
                </div>
                
                <div class="form-section">
                    <h3>❓ Запрос</h3>
                    <div class="form-group">
                        <label for="question">Вопрос на русском языке:</label>
                        <textarea id="question" name="question" placeholder="Например: Покажи всех пользователей, Сколько клиентов в системе?, Поручения за последний месяц" required></textarea>
                    </div>
                </div>
                
                <div class="button-group">
                    <button type="button" onclick="generateSQL()">🔍 Генерировать SQL</button>
                    <button type="button" onclick="executeQuery()">⚡ Выполнить запрос</button>
                    <button type="button" onclick="clearResults()">🗑️ Очистить</button>
                </div>
            </form>
            
            <div id="result" class="result" style="display: none;">
                <h3>Результат:</h3>
                <div id="resultContent"></div>
            </div>
        </div>
        
        <script>
            // Проверка статуса API при загрузке
            window.onload = function() {
                checkAPIStatus();
            };
            
            async function checkAPIStatus() {
                // Проверка NL→SQL API
                try {
                    const response = await fetch('http://localhost:8000/health');
                    const data = await response.json();
                    const statusEl = document.getElementById('nl-sql-status');
                    statusEl.textContent = data.status === 'healthy' ? 'Работает' : 'Ошибка';
                    statusEl.className = 'status-card ' + (data.status === 'healthy' ? 'status-healthy' : 'status-unhealthy');
                } catch (error) {
                    document.getElementById('nl-sql-status').textContent = 'Недоступен';
                    document.getElementById('nl-sql-status').className = 'status-card status-unhealthy';
                }
                
                // Проверка Mock Customer API
                try {
                    const response = await fetch('http://localhost:8080/health');
                    const data = await response.json();
                    const statusEl = document.getElementById('mock-api-status');
                    statusEl.textContent = data.status === 'healthy' ? 'Работает' : 'Ошибка';
                    statusEl.className = 'status-card ' + (data.status === 'healthy' ? 'status-healthy' : 'status-unhealthy');
                } catch (error) {
                    document.getElementById('mock-api-status').textContent = 'Недоступен';
                    document.getElementById('mock-api-status').className = 'status-card status-unhealthy';
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
                            <h4>✅ Сгенерированный SQL:</h4>
                            <div class="sql-display">${result.sql}</div>
                            <p><strong>Вопрос:</strong> ${result.question}</p>
                            <p><strong>Пользователь:</strong> ${result.user_id}</p>
                            <p><strong>Время:</strong> ${new Date(result.timestamp).toLocaleString()}</p>
                        `, 'success');
                    } else {
                        showResult(`<h4>❌ Ошибка:</h4><p>${result.detail || 'Неизвестная ошибка'}</p>`, 'error');
                    }
                } catch (error) {
                    showResult(`<h4>❌ Ошибка подключения:</h4><p>${error.message}</p>`, 'error');
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
                            tableHTML = '<h4>📊 Результаты запроса:</h4>';
                            tableHTML += '<div class="table-display">';
                            tableHTML += '<table>';
                            
                            // Заголовки
                            tableHTML += '<tr>';
                            result.columns.forEach(col => {
                                tableHTML += `<th>${col}</th>`;
                            });
                            tableHTML += '</tr>';
                            
                            // Данные
                            result.data.forEach(row => {
                                tableHTML += '<tr>';
                                result.columns.forEach(col => {
                                    tableHTML += `<td>${row[col] || ''}</td>`;
                                });
                                tableHTML += '</tr>';
                            });
                            
                            tableHTML += '</table>';
                            tableHTML += '</div>';
                        }
                        
                        showResult(`
                            <h4>✅ Выполненный SQL:</h4>
                            <div class="sql-display">${result.sql}</div>
                            <p><strong>Строк:</strong> ${result.row_count}</p>
                            <p><strong>Время выполнения:</strong> ${result.execution_time.toFixed(3)}с</p>
                            ${tableHTML}
                        `, 'success');
                    } else {
                        showResult(`<h4>❌ Ошибка:</h4><p>${result.detail || 'Неизвестная ошибка'}</p>`, 'error');
                    }
                } catch (error) {
                    showResult(`<h4>❌ Ошибка подключения:</h4><p>${error.message}</p>`, 'error');
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
            
            function setQuestion(text) {
                document.getElementById('question').value = text;
            }
            
            // Синхронизация user_id и role
            document.getElementById('user_id').addEventListener('change', function() {
                document.getElementById('role').value = this.value;
            });
        </script>
    </body>
    </html>
    """

@app.get("/api/status")
async def get_api_status():
    """Получение статуса всех API"""
    status = {
        "nl_sql_api": {"status": "unknown", "url": NL_SQL_API_URL},
        "mock_api": {"status": "unknown", "url": MOCK_CUSTOMER_API_URL}
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
                status["mock_api"]["status"] = data.get("status", "unknown")
    except Exception as e:
        status["mock_api"]["error"] = str(e)
    
    return status

if __name__ == "__main__":
    import uvicorn
    print("🚀 Запуск полного веб-интерфейса NL→SQL системы...")
    print("📱 Откройте браузер и перейдите по адресу: http://localhost:3000")
    print("🛑 Для остановки нажмите Ctrl+C")
    uvicorn.run(app, host="0.0.0.0", port=3000)
