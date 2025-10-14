"""
Упрощенный веб-интерфейс для NL→SQL системы
Минималистичный интерфейс с обученным Vanna AI агентом
"""

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, JSONResponse
import httpx
import logging
import os
import sys
import re
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.utils.plan_sql_converter import sql_to_plan
from src.services.query_service import QueryService

def fix_sql_for_mock_api(sql: str) -> str:
    """Исправляет SQL для совместимости с Mock API"""
    if not sql:
        return sql
    
    # Убираем алиасы таблиц только в FROM и JOIN, не трогая ключевые слова WHERE/ON
    # Пример: FROM equsers u -> FROM equsers (но не удалять WHERE)
    sql = re.sub(r'FROM\s+(\w+)\s+(?!WHERE\b)(\w+)\b', r'FROM \1', sql, flags=re.IGNORECASE)
    # Пример: JOIN eq_departments d ON ... -> JOIN eq_departments ON ... (не удалять ON)
    sql = re.sub(r'JOIN\s+(\w+)\s+(?!ON\b)(\w+)\b', r'JOIN \1', sql, flags=re.IGNORECASE)
    
    # Убираем алиасы в полях (например, u.id -> id, d.name -> name)
    sql = re.sub(r'\b\w+\.(\w+)\b', r'\1', sql)
    
    return sql

def normalize_sql_for_postgres(sql: str) -> str:
    """Ничего не меняем в тексте SQL (во избежание поломок)."""
    return sql

def extract_sql_from_text(text: str) -> str:
    """Извлекает SQL из произвольного текста. Ищет блок SELECT ... [;]."""
    if not text:
        return text
    # Попытка найти код-блок
    m = re.search(r"```sql\s*(.*?)\s*```", text, flags=re.IGNORECASE | re.DOTALL)
    if m:
        return m.group(1).strip()
    # Попытка найти выражение SELECT ... ;
    m2 = re.search(r"(select[\s\S]+?;)", text, flags=re.IGNORECASE)
    if m2:
        return m2.group(1).strip()
    # Если нет точки с запятой, берем от SELECT до конца
    m3 = re.search(r"(select[\s\S]+)$", text, flags=re.IGNORECASE)
    if m3:
        return m3.group(1).strip()
    return text.strip()

## Удалён rule-based фоллбэк: если модель не вернула корректный SELECT, отвечаем ошибкой

# Функция apply_role_restrictions удалена - роли применяются в Mock API
logger = logging.getLogger(__name__)

# Создание FastAPI приложения
app = FastAPI(
    title="NL→SQL Simple Interface",
    description="Упрощенный интерфейс для тестирования обученного Vanna AI агента",
    version="2.0.0"
)

# Инициализация QueryService с KB
def get_query_service():
    """Получение QueryService с загруженным KB"""
    try:
        # Создаем QueryService (он загружает KB и правильные данные)
        query_service = QueryService()
        logger.info("✅ QueryService с KB инициализирован")
        return query_service
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации QueryService: {e}")
        return None

# Глобальная переменная для QueryService
query_service = None

@app.get("/", response_class=HTMLResponse)
async def home():
    """Главная страница - простой интерфейс"""
    return """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>NL→SQL Простой Интерфейс</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                max-width: 100%;
                margin: 0;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }
            .container {
                background: white;
                padding: 40px;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                max-width: 1600px;
                margin: 0 auto;
            }
            .roles-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
                gap: 12px;
                margin-top: 12px;
            }
            .role-card {
                border: 1px solid #e1e5e9;
                border-radius: 10px;
                padding: 12px;
                background: #fff;
                cursor: pointer;
                transition: box-shadow 0.2s;
            }
            .role-card:hover { box-shadow: 0 6px 14px rgba(0,0,0,0.08); }
            .role-title { font-weight: 700; margin: 0 0 6px 0; }
            .role-desc { color: #6c757d; margin: 0; font-size: 14px; }
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
            textarea {
                width: 100%;
                padding: 15px;
                border: 2px solid #e1e5e9;
                border-radius: 10px;
                font-size: 16px;
                resize: vertical;
                min-height: 120px;
                transition: border-color 0.3s;
            }
            textarea:focus {
                outline: none;
                border-color: #667eea;
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
            .result {
                margin-top: 30px;
                padding: 20px;
                background: #f8f9fa;
                border-radius: 10px;
                border-left: 5px solid #667eea;
            }
            .error {
                border-left-color: #dc3545;
                background: #f8d7da;
            }
            .success {
                border-left-color: #28a745;
                background: #d4edda;
            }
            .loading {
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
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 NL→SQL Ассистент</h1>
            
            <div class="examples">
                <h3>💡 Примеры вопросов:</h3>
                <div class="example" onclick="setQuestion('Покажи всех пользователей')">Покажи всех пользователей</div>
                <div class="example" onclick="setQuestion('Сколько клиентов в системе?')">Сколько клиентов в системе?</div>
                <div class="example" onclick="setQuestion('Покажи поручения за последний месяц')">Покажи поручения за последний месяц</div>
                <div class="example" onclick="setQuestion('Статистика по отделам')">Статистика по отделам</div>
                <div class="example" onclick="setQuestion('Покажи всех пользователей')">Покажи всех пользователей</div>
                <div class="example" onclick="setQuestion('Пользователи по отделам')">Пользователи по отделам</div>
                <div class="example" onclick="setQuestion('Платежи за сегодня по клиентам')">Платежи за сегодня по клиентам</div>
                <div class="example" onclick="setQuestion('Поручения менеджера manager')">Поручения менеджера manager</div>
                <div class="example" onclick="setQuestion('Список бизнес-единиц с ИНН')">Список бизнес-единиц с ИНН</div>
            </div>
            
            <form id="sqlForm">
                <div class="form-group">
                    <label for="question">Вопрос на русском языке:</label>
                    <textarea id="question" name="question" placeholder="Например: Покажи всех пользователей, Сколько клиентов в системе?, Поручения за последний месяц" required></textarea>
                </div>
                <div class="form-group" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; align-items: end;">
                    <div>
                        <label for="role">Роль:</label>
                        <select id="role" name="role">
                            <option value="admin">admin (Администратор)</option>
                            <option value="manager">manager (Менеджер)</option>
                            <option value="user">user (Пользователь)</option>
                        </select>
                    </div>
                    <div>
                        <label for="department">Отдел:</label>
                        <select id="department" name="department">
                            <option value="IT">IT</option>
                            <option value="Sales">Sales</option>
                            <option value="Support">Support</option>
                        </select>
                    </div>
                </div>
                
                <div class="button-container">
                    <button type="submit">🔍 Генерировать SQL</button>
                    <button type="button" onclick="executeSQL()">⚡ Выполнить SQL</button>
                </div>
                
                <div style="margin-top: 20px; padding: 15px; background: #e9ecef; border-radius: 8px;">
                    <h4>🔐 Текущая роль:</h4>
                    <p><strong>Пользователь:</strong> <span id="currentUser">admin</span></p>
                    <p><strong>Роль:</strong> <span id="currentRole">admin (Администратор)</span></p>
                    <p><strong>Отдел:</strong> <span id="currentDepartment">IT</span></p>
                    <p><strong>Доступ:</strong> Полный доступ ко всем данным</p>
                    <div class="roles-grid">
                        <div class="role-card" data-role="admin" data-dept="IT">
                            <p class="role-title">👑 admin (Администратор)</p>
                            <p class="role-desc">Полный доступ ко всем данным</p>
                        </div>
                        <div class="role-card" data-role="manager" data-dept="Sales">
                            <p class="role-title">👨‍💼 manager (Менеджер)</p>
                            <p class="role-desc">Доступ к данным своего отдела</p>
                        </div>
                        <div class="role-card" data-role="user" data-dept="Support">
                            <p class="role-title">👤 user (Пользователь)</p>
                            <p class="role-desc">Ограниченный доступ к данным</p>
                        </div>
                    </div>
                </div>
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

            document.getElementById('sqlForm').addEventListener('submit', async function(e) {
                e.preventDefault();
                
                const question = document.getElementById('question').value;
                const role = document.getElementById('role').value;
                const department = document.getElementById('department').value;
                const resultDiv = document.getElementById('result');
                const resultContent = document.getElementById('resultContent');
                
                if (!question.trim()) {
                    alert('Пожалуйста, введите вопрос');
                    return;
                }
                
                // Показываем загрузку
                resultDiv.style.display = 'block';
                resultDiv.className = 'result loading';
                resultContent.innerHTML = '🤖 Генерирую SQL и план запроса...';
                
                try {
                    const formData = new FormData();
                    formData.append('question', question);
                    formData.append('role', role);
                    formData.append('department', department);
                    
                    const response = await fetch('/generate-sql', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        resultDiv.className = 'result success';
                        const sqlTemplate = (data.sql_template || '').trim();
                        const sqlCorrected = (data.sql_corrected || '').trim();
                        const sqlWithRoles = (data.sql_with_roles || data.final_sql || '').trim();
                        const sqlGenerated = (data.sql || '').trim();

                        let html = '';

                        // Покажем шаблон, только если он отличается от исправленного/итогового
                        if (sqlTemplate && sqlTemplate !== sqlCorrected && sqlTemplate !== sqlWithRoles) {
                            html += `<h4>📋 SQL Шаблон (оригинальный от Vanna AI):</h4>`;
                            html += `<pre style="background: #e3f2fd; padding: 15px; border-radius: 5px; overflow-x: auto;">${sqlTemplate}</pre>`;
                        } else if (sqlGenerated && sqlGenerated !== sqlCorrected && sqlGenerated !== sqlWithRoles) {
                            html += `<h4>📝 Сгенерированный SQL</h4>`;
                            html += `<pre style="background: #e3f2fd; padding: 15px; border-radius: 5px; overflow-x: auto;">${sqlGenerated}</pre>`;
                        }

                        // Исправленный показываем, если он есть и отличается от итогового
                        if (sqlCorrected && sqlCorrected !== sqlWithRoles) {
                            html += `<h4>🔧 SQL Исправленный (передается в Mock API):</h4>`;
                            html += `<pre style="background: #fff3e0; padding: 15px; border-radius: 5px; overflow-x: auto;">${sqlCorrected}</pre>`;
                        }

                        // SQL с ролевыми ограничениями (если есть)
                        if (sqlWithRoles) {
                            html += `<h4>🔐 SQL с ролевыми ограничениями:</h4>`;
                            html += `<pre style="background: #f3e5f5; padding: 15px; border-radius: 5px; overflow-x: auto;">${sqlWithRoles}</pre>`;
                        }

                        // План
                        html += `<h4>🧭 План запроса:</h4>`;
                        html += `<pre style=\"background: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto;\">${JSON.stringify(data.plan, null, 2)}</pre>`;

                        if (data.restrictions && data.restrictions.length) {
                            html += `<p><strong>Применённые ограничения:</strong> ${data.restrictions.join(', ')}</p>`;
                        }
                        html += `<p><strong>Объяснение:</strong> ${data.explanation}</p>`;
                        html += `<p><strong>Агент:</strong> ${data.agent_type}</p>`;

                        resultContent.innerHTML = html;
                    } else {
                        resultDiv.className = 'result error';
                        resultContent.innerHTML = `
                            <h4>❌ Ошибка:</h4>
                            <p>${data.error}</p>
                        `;
                    }
                } catch (error) {
                    resultDiv.className = 'result error';
                    resultContent.innerHTML = `
                        <h4>❌ Ошибка соединения:</h4>
                        <p>${error.message}</p>
                    `;
                }
            });
            
            async function executeSQL() {
                const question = document.getElementById('question').value;
                const role = document.getElementById('role').value;
                const department = document.getElementById('department').value;
                const resultDiv = document.getElementById('result');
                const resultContent = document.getElementById('resultContent');
                
                if (!question.trim()) {
                    alert('Пожалуйста, введите вопрос');
                    return;
                }
                
                // Показываем загрузку
                resultDiv.style.display = 'block';
                resultDiv.className = 'result loading';
                resultContent.innerHTML = '🤖 Генерирую SQL и выполняю запрос...';
                
                try {
                    const formData = new FormData();
                    formData.append('question', question);
                    formData.append('role', role);
                    formData.append('department', department);
                    
                    const response = await fetch('/execute-sql', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        resultDiv.className = 'result success';
                        
                        // Формируем таблицу с результатами
                        let tableHTML = '';
                        if (data.data && data.data.length > 0) {
                            tableHTML = '<h4>📊 Результаты запроса:</h4>';
                            tableHTML += '<div style="overflow-x: auto; max-width: 100%; margin-top: 10px;">';
                            tableHTML += '<table border="1" style="width: 100%; border-collapse: collapse; min-width: 600px; font-size: 14px;">';
                            tableHTML += '<tr style="background-color: #f8f9fa;">';
                            data.columns.forEach(col => { 
                                tableHTML += `<th style="padding: 8px; text-align: left; white-space: nowrap; max-width: 200px; overflow: hidden; text-overflow: ellipsis;">${col}</th>`; 
                            });
                            tableHTML += '</tr>';
                            data.data.forEach(row => {
                                tableHTML += '<tr>';
                                data.columns.forEach(col => { 
                                    const value = row[col] || '';
                                    const displayValue = value.length > 50 ? value.substring(0, 50) + '...' : value;
                                    tableHTML += `<td style="padding: 8px; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${value}">${displayValue}</td>`; 
                                });
                                tableHTML += '</tr>';
                            });
                            tableHTML += '</table>';
                            tableHTML += '</div>';
                        }
                        
                        resultContent.innerHTML = `
                            <div style="display: grid; gap: 20px;">
                                <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #28a745;">
                                    <h4 style="margin: 0 0 10px 0; color: #28a745;">✅ SQL запрос</h4>
                                    <pre style="background: white; padding: 10px; border-radius: 4px; overflow-x: auto; margin: 0; font-size: 13px;">${data.sql}</pre>
                                </div>
                                
                                <div style="background: #e3f2fd; padding: 15px; border-radius: 8px; border-left: 4px solid #2196f3;">
                                    <h4 style="margin: 0 0 10px 0; color: #2196f3;">🔐 Финальный SQL (с ролевыми ограничениями)</h4>
                                    <pre style="background: white; padding: 10px; border-radius: 4px; overflow-x: auto; margin: 0; font-size: 13px;">${data.final_sql}</pre>
                                </div>
                                
                                <div style="background: #fff3cd; padding: 15px; border-radius: 8px; border-left: 4px solid #ffc107;">
                                    <h4 style="margin: 0 0 10px 0; color: #856404;">📊 Статистика выполнения</h4>
                                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px;">
                                        <div><strong>Строк:</strong> <span style="color: #28a745; font-weight: bold;">${data.row_count}</span></div>
                                        <div><strong>Время:</strong> <span style="color: #007bff; font-weight: bold;">${data.execution_time.toFixed(3)}с</span></div>
                                        ${data.restrictions && data.restrictions.length ? `<div><strong>Ограничения:</strong> <span style="color: #dc3545;">${data.restrictions.join(', ')}</span></div>` : ''}
                                    </div>
                                </div>
                                
                                ${tableHTML}
                                
                                <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #6c757d;">
                                    <h4 style="margin: 0 0 10px 0; color: #6c757d;">ℹ️ Информация</h4>
                                    <p style="margin: 5px 0;"><strong>Объяснение:</strong> ${data.explanation}</p>
                                    <p style="margin: 5px 0;"><strong>Агент:</strong> ${data.agent_type}</p>
                                </div>
                            </div>
                        `;
                    } else {
                        resultDiv.className = 'result error';
                        resultContent.innerHTML = `
                            <h4>❌ Ошибка:</h4>
                            <p>${data.error}</p>
                        `;
                    }
                } catch (error) {
                    resultDiv.className = 'result error';
                    resultContent.innerHTML = `
                        <h4>❌ Ошибка соединения:</h4>
                        <p>${error.message}</p>
                    `;
                }
            }

            // Обновление отображения текущей роли/отдела
            const roleSelect = document.getElementById('role');
            const deptSelect = document.getElementById('department');
            const currentRole = document.getElementById('currentRole');
            const currentDept = document.getElementById('currentDepartment');
            roleSelect.addEventListener('change', () => {
                const map = { admin: 'admin (Администратор)', manager: 'manager (Менеджер)', user: 'user (Пользователь)' };
                currentRole.textContent = map[roleSelect.value] || roleSelect.value;
            });
            deptSelect.addEventListener('change', () => {
                currentDept.textContent = deptSelect.value;
            });

            // Быстрый выбор роли из карточек
            document.querySelectorAll('.role-card').forEach(card => {
                card.addEventListener('click', () => {
                    const r = card.getAttribute('data-role');
                    const d = card.getAttribute('data-dept');
                    roleSelect.value = r;
                    deptSelect.value = d;
                    const map = { admin: 'admin (Администратор)', manager: 'manager (Менеджер)', user: 'user (Пользователь)' };
                    currentRole.textContent = map[r] || r;
                    currentDept.textContent = d;
                });
            });
        </script>
    </body>
    </html>
    """

@app.post("/generate-sql")
async def generate_sql(
    question: str = Form(...),
    role: str = Form("admin"),
    department: str = Form("IT")
):
    """Генерация SQL через QueryService с KB"""
    global query_service
    
    try:
        logger.info(f"Генерация SQL для вопроса: {question}")
        
        # Инициализируем QueryService если нужно
        if query_service is None:
            query_service = get_query_service()
            if query_service is None:
                return JSONResponse(
                    status_code=500,
                    content={"success": False, "error": "Не удалось инициализировать QueryService"}
                )
        
        # Генерируем SQL через QueryService (с KB и правильными данными)
        import asyncio
        sql = await query_service.generate_sql(question, {})
        sql = extract_sql_from_text(sql)
        sql = normalize_sql_for_postgres(sql)

        # Повторная нормализация не требуется; если не SELECT — отдадим ошибку на клиенте выполнения
        
        # Ролевые ограничения применяются в Mock API
        # Преобразуем SQL в план (упрощенный план отображается в UI)
        try:
            plan = sql_to_plan(sql)
        except Exception as conv_err:
            plan = {"error": f"Не удалось построить план: {conv_err}"}

        # Пытаемся применить ролевые ограничения через Mock Customer API (если он доступен)
        final_sql = None
        sql_template = sql
        restrictions = []
        decoded_sql = None
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                # Сначала пробуем новую цепочку: отправляем ПЛАН в Mock API
                resp = await client.post(
                    "http://localhost:8080/api/plan/execute",
                    json={
                        "plan": plan,
                        "user_context": {
                            "login": "a7a_head_department",
                            "role": "admin",
                            "department": "Департамент продаж"
                        },
                        "request_id": "simple_ui_demo_plan"
                    }
                )
                if resp.status_code == 200:
                    data = resp.json()
                    final_sql = data.get("final_sql")
                    decoded_sql = data.get("decoded_sql")
                    restrictions = data.get("restrictions_applied", [])
                else:
                    # Фоллбэк: старый путь SQL→Mock API
                    resp2 = await client.post(
                        "http://localhost:8080/api/sql/execute",
                        json={
                            "sql_template": sql_template,
                            "user_context": {
                                "login": "a7a_head_department",
                                "role": "admin",
                                "department": "Департамент продаж"
                            },
                            "request_id": "simple_ui_demo_sql"
                        }
                    )
                    if resp2.status_code == 200:
                        data2 = resp2.json()
                        final_sql = data2.get("final_sql")
                        restrictions = data2.get("restrictions_applied", [])
        except Exception:
            # Тихо игнорируем, если Mock API недоступен; UI покажет только sql+plan
            pass
        
        return JSONResponse(content={
            "success": True,
            "sql": sql,
            "plan": plan,
            "sql_template": sql_template,
            "final_sql": final_sql,
            "restrictions": restrictions,
            "explanation": "SQL сгенерирован QueryService с KB и правильными данными, план построен конвертером SQL→План; при наличии Mock API показан финальный SQL с ролевыми ограничениями",
            "agent_type": "QueryService с KB"
        })
                
    except Exception as e:
        logger.error(f"Ошибка генерации SQL: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.post("/execute-sql")
async def execute_sql(
    question: str = Form(...),
    role: str = Form("admin"),
    department: str = Form("IT")
):
    """Выполнение SQL и показ результатов"""
    global query_service
    
    try:
        logger.info(f"Выполнение SQL для вопроса: {question}")
        
        # Инициализируем QueryService если нужно
        if query_service is None:
            query_service = get_query_service()
            if query_service is None:
                return JSONResponse(
                    status_code=500,
                    content={"success": False, "error": "Не удалось инициализировать QueryService"}
                )
        
        # Генерируем SQL через QueryService
        import asyncio
        sql = await query_service.generate_sql(question, {})
        logger.info(f"Сгенерированный SQL: {sql}")
        
        # Извлекаем SQL из текста (если агент вернул объяснение с SQL)
        import re
        extracted = extract_sql_from_text(sql)
        if extracted and extracted != sql:
            sql = extracted
            logger.info(f"Извлеченный SQL: {sql}")
        
        # Сохраняем оригинальный SQL для отображения
        original_sql = sql
        
        # Исправляем синтаксис SQL для PostgreSQL
        sql = normalize_sql_for_postgres(sql)

        # Итоговая проверка
        if not sql or not sql.strip().lower().startswith("select"):
            logger.error(f"Сгенерирован невалидный SQL (не SELECT): {sql}")
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": "Генерация SQL не удалась: модель не вернула корректный SELECT",
                    "sql_template": original_sql
                }
            )

        # Безопасная нормализация: только кавычки интервалов и удаление public.
        sql = normalize_sql_for_postgres(sql)
        # Нормализуем пробелы
        sql = re.sub(r"\s+", " ", sql).strip()
        
        # Исправляем JOIN с отделами - заменяем на LEFT JOIN для NULL значений
        import re
        
        # Заменяем все JOIN с отделами на LEFT JOIN
        sql = re.sub(r'JOIN\s+(eq_)?departments\s+(\w+)\s+ON', r'LEFT JOIN \1departments \2 ON', sql)
        sql = re.sub(r'JOIN\s+(eq_)?departments\s+ON', r'LEFT JOIN \1departments ON', sql)
        
        # Дополнительно исправляем условия WHERE для LEFT JOIN
        if 'LEFT JOIN eq_departments' in sql and 'ed.deleted = FALSE' in sql:
            sql = sql.replace('ed.deleted = FALSE', 'ed.deleted = FALSE OR ed.deleted IS NULL')
        if 'LEFT JOIN eq_departments' in sql and 'd.deleted = FALSE' in sql:
            sql = sql.replace('d.deleted = FALSE', 'd.deleted = FALSE OR d.deleted IS NULL')
        
        # Исправляем условия WHERE для LEFT JOIN - убираем проверку deleted для отделов
        if 'LEFT JOIN eq_departments' in sql:
            # Убираем условие d.deleted = FALSE из WHERE
            sql = sql.replace('AND d.deleted = FALSE', '')
            sql = sql.replace('AND ed.deleted = FALSE', '')
            sql = sql.replace('AND eqd.deleted = FALSE', '')
            # Добавляем COALESCE для отображения NULL отделов
            if 'd.name AS department_name' in sql:
                sql = sql.replace('d.name AS department_name', 'COALESCE(d.name, \'Без отдела\') AS department_name')
            if 'ed.name AS department_name' in sql:
                sql = sql.replace('ed.name AS department_name', 'COALESCE(ed.name, \'Без отдела\') AS department_name')
            if 'eqd.name AS department_name' in sql:
                sql = sql.replace('eqd.name AS department_name', 'COALESCE(eqd.name, \'Без отдела\') AS department_name')
        
        # Выполняем SQL через Mock Customer API
        try:
            logger.info(f"Отправка SQL в Mock API: {sql}")
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    "http://localhost:8080/api/sql/execute",
                    json={
                        "sql_template": sql,  # Передаем исправленный SQL
                        "user_context": {
                            "login": "a7a_head_department" if role == "admin" else ("a7a_manager" if role == "manager" else "user"),
                            "role": role,
                            "department": department
                        },
                        "request_id": "simple_ui_execute"
                    }
                )
                
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("success", False):
                        return JSONResponse(content={
                            "success": True,
                            "sql_template": original_sql,  # Оригинальный SQL (от Vanna AI)
                            "sql_corrected": sql,  # Исправленный SQL (передается в Mock API)
                            "sql_with_roles": data.get("sql_with_roles", data.get("final_sql", sql)),  # SQL с ролями
                            "sql": data.get("sql_with_roles", data.get("final_sql", sql)),  # Для совместимости
                            "final_sql": data.get("final_sql", sql),  # Для совместимости
                            "data": data.get("data", []),
                            "columns": data.get("columns", []),
                            "row_count": data.get("row_count", 0),
                            "execution_time": data.get("execution_time", 0),
                            "restrictions": data.get("restrictions_applied", []),
                            "explanation": f"SQL выполнен успешно. Найдено {data.get('row_count', 0)} записей.",
                            "agent_type": "QueryService с KB + Mock API"
                        })
                    else:
                        return JSONResponse(
                            status_code=500,
                            content={"success": False, "error": f"Ошибка выполнения SQL: {data.get('error', 'Неизвестная ошибка')}"}
                        )
                else:
                    error_text = resp.text
                    return JSONResponse(
                        status_code=500,
                        content={"success": False, "error": f"Ошибка выполнения SQL: {resp.status_code} - {error_text}"}
                    )
        except Exception as api_error:
            logger.warning(f"Mock API недоступен: {api_error}")
            return JSONResponse(
                status_code=500,
                content={"success": False, "error": f"Mock API недоступен: {api_error}"}
            )
            
    except Exception as e:
        logger.error(f"Ошибка выполнения SQL: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Ошибка выполнения SQL: {str(e)}"}
        )

@app.get("/health")
async def health():
    """Проверка состояния системы"""
    return {"status": "healthy", "agent": "Vanna AI + ProxyAPI + pgvector"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
