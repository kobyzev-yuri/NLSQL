"""
Упрощенный веб-интерфейс для NL→SQL системы
Минималистичный интерфейс с обученным Vanna AI агентом
"""

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
import logging
import os
from typing import Optional
from src.vanna.vanna_pgvector_native import create_native_vanna_client

logger = logging.getLogger(__name__)

# Создание FastAPI приложения
app = FastAPI(
    title="NL→SQL Simple Interface",
    description="Упрощенный интерфейс для тестирования обученного Vanna AI агента",
    version="2.0.0"
)

# Инициализация обученного Vanna AI агента
def get_vanna_agent():
    """Получение обученного Vanna AI агента"""
    try:
        # Загружаем переменные окружения для ProxyAPI
        os.environ['PROXYAPI_KEY'] = 'sk-xF20r7G4tq9ezBMNKIjCPvva2io4S8FV'
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
                max-width: 800px;
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
            </div>
            
            <form id="sqlForm">
                <div class="form-group">
                    <label for="question">Вопрос на русском языке:</label>
                    <textarea id="question" name="question" placeholder="Например: Покажи всех пользователей, Сколько клиентов в системе?, Поручения за последний месяц" required></textarea>
                </div>
                
                <div class="button-container">
                    <button type="submit">🔍 Генерировать SQL</button>
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
                const resultDiv = document.getElementById('result');
                const resultContent = document.getElementById('resultContent');
                
                if (!question.trim()) {
                    alert('Пожалуйста, введите вопрос');
                    return;
                }
                
                // Показываем загрузку
                resultDiv.style.display = 'block';
                resultDiv.className = 'result loading';
                resultContent.innerHTML = '🤖 Генерирую SQL запрос...';
                
                try {
                    const formData = new FormData();
                    formData.append('question', question);
                    
                    const response = await fetch('/generate-sql', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        resultDiv.className = 'result success';
                        resultContent.innerHTML = `
                            <h4>✅ SQL запрос:</h4>
                            <pre style="background: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto;">${data.sql}</pre>
                            <p><strong>Объяснение:</strong> ${data.explanation}</p>
                            <p><strong>Агент:</strong> ${data.agent_type}</p>
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
            });
        </script>
    </body>
    </html>
    """

@app.post("/generate-sql")
async def generate_sql(question: str = Form(...)):
    """Генерация SQL с обученным Vanna AI агентом"""
    global vanna_agent
    
    try:
        logger.info(f"Генерация SQL для вопроса: {question}")
        
        # Инициализируем агента если нужно
        if vanna_agent is None:
            vanna_agent = get_vanna_agent()
            if vanna_agent is None:
                return JSONResponse(
                    status_code=500,
                    content={"success": False, "error": "Не удалось инициализировать Vanna AI агента"}
                )
        
        # Генерируем SQL с обученным агентом
        sql = vanna_agent.generate_sql(question)
        
        return JSONResponse(content={
            "success": True,
            "sql": sql,
            "explanation": "SQL сгенерирован обученным Vanna AI агентом с ProxyAPI и pgvector",
            "agent_type": "Vanna AI + ProxyAPI + pgvector"
        })
                
    except Exception as e:
        logger.error(f"Ошибка генерации SQL: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.get("/health")
async def health():
    """Проверка состояния системы"""
    return {"status": "healthy", "agent": "Vanna AI + ProxyAPI + pgvector"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
