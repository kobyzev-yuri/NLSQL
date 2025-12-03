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
from pathlib import Path

# Load environment variables from config.env before anything else
from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / "config.env", override=True)

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

@app.on_event("startup")
async def startup_event():
    """Инициализация QueryService при старте FastAPI"""
    global query_service
    logger.info("🚀 Инициализация QueryService...")
    query_service = get_query_service()
    if query_service:
        logger.info("✅ QueryService готов к работе!")
    else:
        logger.error("❌ Ошибка инициализации QueryService")

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
                <h3>💡 Примеры вопросов (тестовые из MaxB):</h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 10px;">
                    <div>
                        <h4 style="margin: 10px 0 5px 0; color: #495057; font-size: 14px;">👥 Пользователи:</h4>
                        <div class="example" onclick="setQuestion('Выведи список пользователей, зарегистрированных после 1 августа 2025 года')">Выведи список пользователей, зарегистрированных после 1 августа 2025 года</div>
                        <div class="example" onclick="setQuestion('Выведи список пользователей, являющихся менеджерами')">Выведи список пользователей, являющихся менеджерами</div>
                        <div class="example" onclick="setQuestion('Список пользователей из equsers, имеющих имя Иван')">Список пользователей из equsers, имеющих имя Иван</div>
                        <div class="example" onclick="setQuestion('Покажи всех активных пользователей с их контактными данными')">Покажи всех активных пользователей с их контактными данными</div>
                    </div>
                    <div>
                        <h4 style="margin: 10px 0 5px 0; color: #495057; font-size: 14px;">🏢 Профили компаний:</h4>
                        <div class="example" onclick="setQuestion('Выведи список профилей, находящихся в статусе На доработке в КЦ')">Выведи список профилей, находящихся в статусе На доработке в КЦ</div>
                        <div class="example" onclick="setQuestion('Выведи список профилей компаний, работающих в Уральском федеральном округе и отсортируй его по дате регистрации')">Выведи список профилей компаний, работающих в Уральском федеральном округе и отсортируй его по дате регистрации</div>
                        <div class="example" onclick="setQuestion('Выведи список профилей компаний, имеющих соглашения')">Выведи список профилей компаний, имеющих соглашения</div>
                        <div class="example" onclick="setQuestion('Список бизнес-единиц с комментариями из tbl_business_unit_comment')">Список бизнес-единиц с комментариями из tbl_business_unit_comment</div>
                    </div>
                    <div>
                        <h4 style="margin: 10px 0 5px 0; color: #495057; font-size: 14px;">📋 Поручения:</h4>
                        <div class="example" onclick="setQuestion('Выведи список всех поручений, относящихся к канцтоварам')">Выведи список всех поручений, относящихся к канцтоварам</div>
                        <div class="example" onclick="setQuestion('Выведи регистрационные номера и наименования банков для 10 самых дорогих поручений (по сумме платежа в рублях), находящихся в статусе Отправлен в рейс')">Выведи регистрационные номера и наименования банков для 10 самых дорогих поручений (по сумме платежа в рублях), находящихся в статусе Отправлен в рейс</div>
                        <div class="example" onclick="setQuestion('Покажи поручения, созданные за последний месяц, отсортированные по сумме платежа')">Покажи поручения, созданные за последний месяц, отсортированные по сумме платежа</div>
                    </div>
                    <div>
                        <h4 style="margin: 10px 0 5px 0; color: #495057; font-size: 14px;">💰 Валюты и фильтры:</h4>
                        <div class="example" onclick="setQuestion('Фильтр по валютам в tbl_currencies с курсом выше 100')">Фильтр по валютам в tbl_currencies с курсом выше 100</div>
                        <div class="example" onclick="setQuestion('Найди профили компаний с ИНН, начинающимся с 77')">Найди профили компаний с ИНН, начинающимся с 77</div>
                        <div class="example" onclick="setQuestion('Покажи поручения с суммой платежа больше 100000 рублей в статусе Отправлен в рейс')">Покажи поручения с суммой платежа больше 100000 рублей в статусе Отправлен в рейс</div>
                    </div>
                </div>
            </div>
            
            <form id="sqlForm">
                <div class="form-group">
                    <label for="question">Вопрос на русском языке:</label>
                    <textarea id="question" name="question" placeholder="Например: Покажи всех пользователей с email, Сколько поручений в системе?, Список бизнес-единиц с ИНН" required></textarea>
                </div>
                <div class="form-group" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; align-items: end;">
                    <div>
                        <label for="llm_provider">🤖 LLM Провайдер:</label>
                        <select id="llm_provider" name="llm_provider" style="width: 100%; padding: 8px; border: 2px solid #e1e5e9; border-radius: 8px;" onchange="updateTimeout()">
                            <option value="openai">GPT-4o (OpenAI/ProxyAPI)</option>
                            <option value="ollama">Qwen (Ollama локально)</option>
                        </select>
                    </div>
                    <div>
                        <label for="timeout">⏱️ Таймаут генерации (сек):</label>
                        <input type="number" id="timeout" name="timeout" value="500" min="10" max="600" step="10" style="width: 100%; padding: 8px; border: 2px solid #e1e5e9; border-radius: 8px;" title="Таймаут для генерации SQL в секундах">
                    </div>
                    <div>
                        <label for="exec_timeout">⏱️ Таймаут выполнения (сек):</label>
                        <input type="number" id="exec_timeout" name="exec_timeout" value="60" min="10" max="600" step="10" style="width: 100%; padding: 8px; border: 2px solid #e1e5e9; border-radius: 8px;" title="Таймаут для выполнения SQL запроса в секундах">
                    </div>
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
                            <option value="Департамент продаж">Департамент продаж</option>
                            <option value="Отдел 1">Отдел 1</option>
                            <option value="Продажи">Продажи</option>
                            <option value="Продажи 2">Продажи 2</option>
                            <option value="Управление Крупного Крупнейшего Бизнеса">Управление Крупного Крупнейшего Бизнеса</option>
                        </select>
                    </div>
                </div>
                
                <div class="button-container">
                    <button type="submit">🔍 Генерировать SQL</button>
                    <button type="button" onclick="executeSQL()">⚡ Выполнить SQL</button>
                </div>
                
                <div style="margin-top: 20px; padding: 15px; background: #e9ecef; border-radius: 8px;">
                    <h4>🔐 Текущая роль:</h4>
                    <p><strong>Роль:</strong> <span id="currentRole">admin (Администратор)</span></p>
                    <p><strong>Отдел:</strong> <span id="currentDepartment">Департамент продаж</span></p>
                    <p><strong>Логин:</strong> <span id="currentUser">test_user</span></p>
                    <div class="roles-grid">
                        <div class="role-card" data-role="admin">
                            <p class="role-title">👑 admin (Администратор)</p>
                            <p class="role-desc">Полный доступ ко всем данным независимо от отдела</p>
                        </div>
                        <div class="role-card" data-role="manager">
                            <p class="role-title">👨‍💼 manager (Менеджер)</p>
                            <p class="role-desc">Доступ к данным своего отдела (выберите отдел отдельно)</p>
                        </div>
                        <div class="role-card" data-role="user">
                            <p class="role-title">👤 user (Пользователь)</p>
                            <p class="role-desc">Ограниченный доступ к своим данным</p>
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
            
            function updateTimeout() {
                const provider = document.getElementById('llm_provider').value;
                const timeoutInput = document.getElementById('timeout');
                // Устанавливаем значения по умолчанию в зависимости от провайдера
                if (provider === 'ollama') {
                    timeoutInput.value = 500;
                    timeoutInput.placeholder = 'Рекомендуется: 500 сек';
                } else {
                    timeoutInput.value = 90;
                    timeoutInput.placeholder = 'Рекомендуется: 90 сек';
                    // Обновляем таймаут выполнения при переключении провайдера
                    const execTimeoutInput = document.getElementById('exec_timeout');
                    if (execTimeoutInput) {
                        execTimeoutInput.value = 60; // Стандартный таймаут для выполнения SQL
                    }
                }
            }
            
            // Инициализация при загрузке страницы
            document.addEventListener('DOMContentLoaded', function() {
                updateTimeout();
            });

            document.getElementById('sqlForm').addEventListener('submit', async function(e) {
                e.preventDefault();
                
                const question = document.getElementById('question').value;
                const role = document.getElementById('role').value;
                const department = document.getElementById('department').value;
                const llm_provider = document.getElementById('llm_provider').value;
                const timeoutSeconds = parseInt(document.getElementById('timeout').value) || (llm_provider === 'ollama' ? 500 : 90);
                const resultDiv = document.getElementById('result');
                const resultContent = document.getElementById('resultContent');
                
                if (!question.trim()) {
                    alert('Пожалуйста, введите вопрос');
                    return;
                }
                
                // Показываем загрузку
                resultDiv.style.display = 'block';
                resultDiv.className = 'result loading';
                resultContent.innerHTML = `🤖 Генерирую SQL и план запроса... (таймаут: ${timeoutSeconds} сек)`;
                
                // Засекаем время начала генерации
                const startTime = performance.now();
                
                try {
                    const formData = new FormData();
                    formData.append('question', question);
                    formData.append('role', role);
                    formData.append('department', department);
                    formData.append('llm_provider', llm_provider);
                    formData.append('timeout', timeoutSeconds.toString());
                    
                    // Таймаут в миллисекундах для fetch
                    const timeout = timeoutSeconds * 1000;
                    const controller = new AbortController();
                    const timeoutId = setTimeout(() => controller.abort(), timeout);
                    
                    let response;
                    try {
                        response = await fetch('/generate-sql', {
                            method: 'POST',
                            body: formData,
                            signal: controller.signal
                        });
                        clearTimeout(timeoutId);
                    } catch (fetchError) {
                        clearTimeout(timeoutId);
                        if (fetchError.name === 'AbortError' || fetchError.message.includes('aborted')) {
                            const providerName = llm_provider === 'ollama' ? 'Qwen (Ollama)' : 'GPT-4o';
                            const timeoutSec = timeout / 1000;
                            throw new Error(`⏱️ Таймаут при генерации через ${providerName} (${timeoutSec} сек). ${llm_provider === 'ollama' ? 'Модель работает очень медленно. Попробуйте более простой запрос или переключитесь на GPT-4o. Проверьте Ollama: curl http://localhost:11434/api/tags' : 'Попробуйте более простой запрос.'}`);
                        }
                        throw fetchError;
                    }
                    
                    if (!response.ok) {
                        const errorText = await response.text();
                        let errorData;
                        try {
                            errorData = JSON.parse(errorText);
                        } catch {
                            errorData = { error: errorText };
                        }
                        throw new Error(errorData.error || `HTTP ${response.status}: ${errorText.substring(0, 200)}`);
                    }
                    
                    const data = await response.json();
                    
                    // Вычисляем время генерации (клиентское время)
                    const endTime = performance.now();
                    const clientTime = ((endTime - startTime) / 1000).toFixed(2);
                    const providerName = llm_provider === 'ollama' ? 'Qwen (Ollama)' : 'GPT-4o';
                    
                    // Используем время генерации из ответа API, если доступно
                    const generationTime = data.generation_time || clientTime;
                    const totalTime = data.total_time || clientTime;
                    
                    if (data.success) {
                        resultDiv.className = 'result success';
                        const sqlTemplate = (data.sql_template || '').trim();
                        const sqlCorrected = (data.sql_corrected || '').trim();
                        const sqlWithRoles = (data.sql_with_roles || data.final_sql || '').trim();
                        const sqlGenerated = (data.sql || '').trim();

                        let html = `<div style="background: #e8f5e9; padding: 12px; border-radius: 5px; margin-bottom: 15px; border-left: 4px solid #4caf50;">
                            <strong>✅ SQL успешно сгенерирован</strong><br>
                            <span style="color: #666; font-size: 14px;">
                                ⏱️ <strong>Время генерации SQL:</strong> ${generationTime} сек | 
                                ⏱️ <strong>Общее время:</strong> ${totalTime} сек | 
                                🤖 <strong>Провайдер:</strong> ${providerName}
                            </span>
                        </div>`;

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
                    let errorMessage = error.message || String(error);
                    
                    // Улучшаем сообщения об ошибках для Ollama
                    if (llm_provider === 'ollama') {
                        if (errorMessage.includes('timeout') || errorMessage.includes('Таймаут') || errorMessage.includes('AbortError') || errorMessage.includes('aborted') || errorMessage.includes('signal')) {
                            errorMessage = `⏱️ <strong>Таймаут при генерации через Qwen (Ollama)</strong><br><br>
                            💡 <strong>Рекомендации:</strong><br>
                            • Используйте более простой запрос<br>
                            • Переключитесь на GPT-4o для быстрой генерации<br>
                            • Проверьте, что Ollama запущен: <code>curl http://localhost:11434/api/tags</code><br>
                            • Проверьте модель: <code>ollama list | grep qwen</code>`;
                        } else if (errorMessage.includes('11434') || errorMessage.includes('connection') || errorMessage.includes('ECONNREFUSED')) {
                            errorMessage = `❌ <strong>Не удалось подключиться к Ollama</strong><br><br>
                            💡 <strong>Проверьте:</strong><br>
                            • Запущен ли Ollama: <code>ollama serve</code><br>
                            • Доступна ли модель: <code>ollama list | grep qwen</code><br>
                            • Если модель отсутствует: <code>ollama pull qwen2.5-coder:1.5b</code>`;
                        }
                    }
                    
                    resultContent.innerHTML = `
                        <h4>❌ Ошибка соединения:</h4>
                        <div>${errorMessage}</div>
                    `;
                    console.error('Ошибка генерации SQL:', error);
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
                    const execTimeout = parseInt(document.getElementById('exec_timeout').value) || 60;
                    const formData = new FormData();
                    formData.append('question', question);
                    formData.append('role', role);
                    formData.append('department', department);
                    
                    // Используем AbortController для таймаута выполнения SQL
                    const controller = new AbortController();
                    const timeoutId = setTimeout(() => controller.abort(), execTimeout * 1000);
                    
                    let response;
                    try {
                        response = await fetch('/execute-sql', {
                            method: 'POST',
                            body: formData,
                            signal: controller.signal
                        });
                        clearTimeout(timeoutId);
                    } catch (fetchError) {
                        clearTimeout(timeoutId);
                        if (fetchError.name === 'AbortError' || fetchError.message.includes('aborted')) {
                            throw new Error(`⏱️ Таймаут при выполнении SQL (${execTimeout} сек). Запрос выполняется слишком долго.`);
                        }
                        throw fetchError;
                    }
                    
                    let data;
                    if (!response.ok) {
                        // Если статус не 200, пытаемся получить текст ошибки
                        const errorText = await response.text();
                        try {
                            data = JSON.parse(errorText);
                        } catch {
                            data = { success: false, error: `HTTP ${response.status}: ${errorText.substring(0, 200)}` };
                        }
                    } else {
                        data = await response.json();
                    }
                    
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
            const currentUser = document.getElementById('currentUser');
            roleSelect.addEventListener('change', () => {
                const map = { admin: 'admin (Администратор)', manager: 'manager (Менеджер)', user: 'user (Пользователь)' };
                currentRole.textContent = map[roleSelect.value] || roleSelect.value;
                // Обновляем логин в зависимости от роли
                currentUser.textContent = 'test_user';
            });
            deptSelect.addEventListener('change', () => {
                currentDept.textContent = deptSelect.value;
            });

            // Быстрый выбор роли из карточек (без изменения отдела)
            document.querySelectorAll('.role-card').forEach(card => {
                card.addEventListener('click', () => {
                    const r = card.getAttribute('data-role');
                    roleSelect.value = r;
                    const map = { admin: 'admin (Администратор)', manager: 'manager (Менеджер)', user: 'user (Пользователь)' };
                    currentRole.textContent = map[r] || r;
                    // Отдел не меняем - он выбирается отдельно
                });
            });
        </script>
    </body>
    </html>
    """

def get_query_service_with_provider(llm_provider: str = None):
    """Создает QueryService с указанным провайдером"""
    import os
    from src.services.query_service import QueryService
    
    # Временно переключаем провайдер
    original_provider = os.getenv("LLM_PROVIDER")
    if llm_provider:
        os.environ["LLM_PROVIDER"] = llm_provider
    
    try:
        service = QueryService()
        return service
    finally:
        # Восстанавливаем оригинальный провайдер
        if original_provider:
            os.environ["LLM_PROVIDER"] = original_provider
        elif "LLM_PROVIDER" in os.environ:
            del os.environ["LLM_PROVIDER"]

@app.post("/generate-sql")
async def generate_sql(
    question: str = Form(...),
    role: str = Form("admin"),
    department: str = Form("Департамент продаж"),
    llm_provider: str = Form("openai"),
    timeout: str = Form(None)
):
    """Генерация SQL через QueryService с KB"""
    import time
    import os
    start_time = time.time()
    global query_service
    
    try:
        # Определяем таймаут из параметра или config.env
        if timeout:
            request_timeout = int(timeout)
        else:
            # Используем значения из config.env
            if llm_provider == "ollama":
                request_timeout = int(os.getenv("OLLAMA_TIMEOUT", "500"))
            else:
                request_timeout = int(os.getenv("OPENAI_TIMEOUT", "60"))
        
        logger.info(f"Генерация SQL для вопроса: {question} (провайдер: {llm_provider}, таймаут: {request_timeout} сек)")
        
        # Создаем QueryService с нужным провайдером
        service = get_query_service_with_provider(llm_provider)
        if service is None:
            return JSONResponse(
                status_code=500,
                content={"success": False, "error": "Не удалось инициализировать QueryService"}
            )
        
        # Генерируем SQL через QueryService (с KB и правильными данными)
        import asyncio
        sql_generation_start = time.time()
        sql = await service.generate_sql(question, {}, timeout=request_timeout)
        sql_generation_time = time.time() - sql_generation_start
        
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
                    "http://localhost:8081/api/plan/execute",
                    json={
                        "plan": plan,
                        "user_context": {
                            "login": "test_user",
                            "role": role,  # Используем роль из формы
                            "department": department  # Используем отдел из формы
                        },
                        "request_id": "simple_ui_demo_plan"
                    }
                )
                if resp.status_code == 200:
                    data = resp.json()
                    # План→SQL может терять WHERE условия, используем оригинал
                    decoded_sql = data.get("decoded_sql")  
                    final_sql = data.get("final_sql")
                    restrictions = data.get("restrictions_applied", [])
                
                # Всегда пробуем и SQL endpoint для правильных ограничений
                if not final_sql or final_sql == decoded_sql:
                    resp2 = await client.post(
                        "http://localhost:8081/api/sql/execute",
                        json={
                            "sql_template": sql_template,
                            "user_context": {
                                "login": "test_user",
                                "role": role,  # Используем роль из формы
                                "department": department  # Используем отдел из формы
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
        
        # Вычисляем общее время обработки
        total_time = time.time() - start_time
        
        return JSONResponse(content={
            "success": True,
            "sql": sql,
            "plan": plan,
            "sql_template": sql_template,
            "sql_with_roles": final_sql,  # Для отображения в JS
            "final_sql": final_sql,  # Для совместимости
            "restrictions": restrictions,
            "explanation": "SQL сгенерирован QueryService с KB и правильными данными, план построен конвертером SQL→План; при наличии Mock API показан финальный SQL с ролевыми ограничениями",
            "agent_type": "QueryService с KB",
            "generation_time": round(sql_generation_time, 2),  # Время генерации SQL в секундах
            "total_time": round(total_time, 2)  # Общее время обработки запроса
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
    department: str = Form("Департамент продаж")
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
                    "http://localhost:8081/api/sql/execute",
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

@app.get("/status")
async def status():
    """Детальный статус готовности системы"""
    global query_service
    
    if query_service is None:
        return {
            "ready": False,
            "status": "initializing",
            "message": "QueryService инициализируется...",
            "components": {
                "fastapi": True,
                "query_service": False
            }
        }
    else:
        return {
            "ready": True,
            "status": "ready",
            "message": "Система готова к работе",
            "components": {
                "fastapi": True,
                "query_service": True
            }
        }

@app.get("/vector-stats")
async def get_vector_stats():
    """Получение статистики векторной базы знаний"""
    global query_service
    
    if query_service is None:
        return {"error": "QueryService не инициализирован"}
    
    try:
        # Получаем статистику через QueryService
        stats = await query_service.get_vector_stats()
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/embedding-quality")
async def analyze_embedding_quality():
    """Анализ качества эмбеддингов"""
    global query_service
    
    if query_service is None:
        return {"error": "QueryService не инициализирован"}
    
    try:
        # Анализируем качество эмбеддингов
        quality = await query_service.analyze_embedding_quality()
        return {
            "success": True,
            "quality": quality
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
