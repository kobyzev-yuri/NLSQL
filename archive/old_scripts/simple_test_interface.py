#!/usr/bin/env python3
"""
Простой тестовый интерфейс для проверки ролевых ограничений
Одна кнопка - один тест
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
    title="NL→SQL Тест Ролей",
    description="Простой интерфейс для тестирования ролевых ограничений",
    version="1.0.0"
)

# Конфигурация API
NL_SQL_API_URL = "http://localhost:8000"

@app.get("/", response_class=HTMLResponse)
async def home():
    """Главная страница с простым тестом"""
    return """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Тест Ролевых Ограничений</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background: #f5f5f5;
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
            .test-section {
                background: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 20px;
            }
            .role-selector {
                display: flex;
                gap: 10px;
                margin-bottom: 20px;
            }
            .role-btn {
                padding: 10px 20px;
                border: 2px solid #ddd;
                background: white;
                cursor: pointer;
                border-radius: 5px;
                transition: all 0.3s;
            }
            .role-btn.active {
                background: #007bff;
                color: white;
                border-color: #007bff;
            }
            .test-btn {
                width: 100%;
                padding: 15px;
                background: #28a745;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 18px;
                cursor: pointer;
                margin-bottom: 20px;
            }
            .test-btn:hover {
                background: #218838;
            }
            .result {
                margin-top: 20px;
                padding: 15px;
                border-radius: 5px;
                border-left: 4px solid #007bff;
                background: #f8f9fa;
            }
            .result.success {
                border-left-color: #28a745;
                background: #d4edda;
            }
            .result.error {
                border-left-color: #dc3545;
                background: #f8d7da;
            }
            .result.loading {
                text-align: center;
                color: #666;
                font-style: italic;
            }
            .sql-display {
                background: #2d3748;
                color: #e2e8f0;
                padding: 15px;
                border-radius: 5px;
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
            .status {
                display: flex;
                gap: 20px;
                margin-bottom: 20px;
            }
            .status-item {
                padding: 5px 10px;
                border-radius: 3px;
                font-size: 12px;
                font-weight: bold;
            }
            .status-healthy {
                background: #d4edda;
                color: #155724;
            }
            .status-unhealthy {
                background: #f8d7da;
                color: #721c24;
            }
            .question-selector {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 10px;
                margin-bottom: 20px;
            }
            .question-btn {
                padding: 10px;
                border: 2px solid #ddd;
                background: white;
                cursor: pointer;
                border-radius: 5px;
                transition: all 0.3s;
                text-align: left;
                font-size: 14px;
            }
            .question-btn:hover {
                border-color: #007bff;
                background: #f8f9fa;
            }
            .question-btn.active {
                background: #007bff;
                color: white;
                border-color: #007bff;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔐 Тест Ролевых Ограничений</h1>
            
            <div class="status">
                <div>
                    <span>API:</span>
                    <span id="api-status" class="status-item status-unhealthy">Проверка...</span>
                </div>
            </div>
            
            <div class="test-section">
                <h3>Выберите роль для тестирования:</h3>
                <div class="role-selector">
                    <div class="role-btn active" data-role="admin" data-user="admin">
                        👑 Администратор<br><small>Видит все данные</small>
                    </div>
                    <div class="role-btn" data-role="manager" data-user="manager">
                        👨‍💼 Менеджер<br><small>Только IT отдел</small>
                    </div>
                    <div class="role-btn" data-role="user" data-user="user">
                        👤 Пользователь<br><small>Только свои данные</small>
                    </div>
                </div>
                
                <h3>Выберите вопрос для тестирования:</h3>
                <div class="question-selector">
                    <button class="question-btn active" data-question="Покажи всех пользователей">
                        👥 Покажи всех пользователей
                    </button>
                    <button class="question-btn" data-question="Покажи заказы старше 3 дней из категории А больше 1 млн рублей">
                        📦 Заказы старше 3 дней (категория А, >1млн)
                    </button>
                    <button class="question-btn" data-question="Из чего сделан продукт #876?">
                        🔍 Из чего сделан продукт #876?
                    </button>
                    <button class="question-btn" data-question="Когда будет совещание по маркетингу?">
                        📅 Совещание по маркетингу
                    </button>
                    <button class="question-btn" data-question="Покажи статистику по отделам">
                        📊 Статистика по отделам
                    </button>
                    <button class="question-btn" data-question="Список всех отделов">
                        🏢 Список отделов
                    </button>
                </div>
                
                <button class="test-btn" onclick="runTest()">
                    🧪 Запустить тест
                </button>
            </div>
            
            <div id="result" class="result" style="display: none;">
                <h3>Результат теста:</h3>
                <div id="resultContent"></div>
            </div>
        </div>
        
        <script>
            let currentRole = 'admin';
            let currentUser = 'admin';
            let currentQuestion = 'Покажи всех пользователей';
            
            // Проверка статуса API при загрузке
            window.onload = function() {
                checkAPIStatus();
            };
            
            async function checkAPIStatus() {
                try {
                    const response = await fetch('http://localhost:8000/health');
                    const data = await response.json();
                    const statusEl = document.getElementById('api-status');
                    statusEl.textContent = data.status === 'healthy' ? 'Работает' : 'Ошибка';
                    statusEl.className = 'status-item ' + (data.status === 'healthy' ? 'status-healthy' : 'status-unhealthy');
                } catch (error) {
                    document.getElementById('api-status').textContent = 'Недоступен';
                    document.getElementById('api-status').className = 'status-item status-unhealthy';
                }
            }
            
            // Выбор роли
            document.querySelectorAll('.role-btn').forEach(btn => {
                btn.addEventListener('click', function() {
                    document.querySelectorAll('.role-btn').forEach(b => b.classList.remove('active'));
                    this.classList.add('active');
                    currentRole = this.dataset.role;
                    currentUser = this.dataset.user;
                });
            });
            
            // Выбор вопроса
            document.querySelectorAll('.question-btn').forEach(btn => {
                btn.addEventListener('click', function() {
                    document.querySelectorAll('.question-btn').forEach(b => b.classList.remove('active'));
                    this.classList.add('active');
                    currentQuestion = this.dataset.question;
                });
            });
            
            async function runTest() {
                showLoading();
                
                try {
                    const response = await fetch('http://localhost:8000/query/execute', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            question: currentQuestion,
                            user_id: currentUser,
                            role: currentRole,
                            department: 'IT'
                        })
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
                            <h4>✅ Тест выполнен успешно</h4>
                            <p><strong>Вопрос:</strong> ${currentQuestion}</p>
                            <p><strong>Роль:</strong> ${currentRole} (${currentUser})</p>
                            <p><strong>Строк получено:</strong> ${result.row_count}</p>
                            <p><strong>Время выполнения:</strong> ${result.execution_time.toFixed(3)}с</p>
                            <h4>🔧 Примененный SQL:</h4>
                            <div class="sql-display">${result.sql}</div>
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
                document.getElementById('resultContent').innerHTML = '⏳ Выполняется тест...';
            }
            
            function showResult(content, type) {
                document.getElementById('result').style.display = 'block';
                document.getElementById('result').className = `result ${type}`;
                document.getElementById('resultContent').innerHTML = content;
            }
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    import uvicorn
    print("🧪 Запуск простого тестового интерфейса...")
    print("📱 Откройте браузер и перейдите по адресу: http://localhost:3001")
    print("🛑 Для остановки нажмите Ctrl+C")
    uvicorn.run(app, host="0.0.0.0", port=3001)
