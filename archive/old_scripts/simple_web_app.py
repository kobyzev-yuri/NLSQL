#!/usr/bin/env python3
"""
Простой веб-интерфейс для NL-to-SQL системы
Использует оптимизированный пайплайн напрямую
"""

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
import logging
import os
import sys
from pathlib import Path

# Добавляем путь к модулям
sys.path.append(str(Path(__file__).parent))

logger = logging.getLogger(__name__)

# Создание FastAPI приложения
app = FastAPI(
    title="NL→SQL Simple Interface",
    description="Простой интерфейс для тестирования NL-to-SQL системы",
    version="3.0.0"
)

# Глобальная переменная для пайплайна
optimized_pipeline = None

def get_optimized_pipeline():
    """Получение оптимизированного пайплайна"""
    global optimized_pipeline
    
    if optimized_pipeline is None:
        try:
            from src.vanna.optimized_dual_pipeline import OptimizedDualPipeline
            
            # Конфигурация для GPT-4o
            gpt4_config = {
                "database_url": "postgresql://postgres:1234@localhost:5432/test_docstructure",
                "vector_table": "vanna_vectors",
                "api_key": os.getenv("PROXYAPI_KEY"),
                "model": "gpt-4o",
                "base_url": "https://api.proxyapi.ru/openai/v1",
                "temperature": 0.2
            }
            
            # Конфигурация для Ollama
            ollama_config = {
                "database_url": "postgresql://postgres:1234@localhost:5432/test_docstructure",
                "vector_table": "vanna_vectors",
                "api_key": "ollama",
                "model": "llama3:latest",
                "base_url": "http://localhost:11434/v1",
                "temperature": 0.2
            }
            
            # Путь к данным обучения
            training_data_path = "training_data/enhanced_sql_examples.json"
            
            # Создаем оптимизированный пайплайн
            optimized_pipeline = OptimizedDualPipeline()
            logger.info("✅ Оптимизированный пайплайн инициализирован")
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации оптимизированного пайплайна: {e}")
            return None
    
    return optimized_pipeline

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
                <div class="example" onclick="setQuestion('Список отделов')">Список отделов</div>
                <div class="example" onclick="setQuestion('Пользователи по отделам')">Пользователи по отделам</div>
                <div class="example" onclick="setQuestion('Все клиенты')">Все клиенты</div>
            </div>
            
            <form id="sqlForm">
                <div class="form-group">
                    <label for="question">Вопрос на русском языке:</label>
                    <textarea id="question" name="question" placeholder="Например: Покажи всех пользователей, Список отделов, Пользователи по отделам" required></textarea>
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
    """Генерация SQL с оптимизированным пайплайном"""
    try:
        logger.info(f"Генерация SQL для вопроса: {question}")
        
        # Получаем оптимизированный пайплайн
        pipeline = get_optimized_pipeline()
        if pipeline is None:
            return JSONResponse(
                status_code=500,
                content={"success": False, "error": "Не удалось инициализировать оптимизированный пайплайн"}
            )
        
        # Генерируем SQL с оптимизированным пайплайном
        result = pipeline.generate_sql(question, prefer_model='auto')
        
        if result and result.get('success') and result.get('sql'):
            return JSONResponse(content={
                "success": True,
                "sql": result['sql'],
                "explanation": f"SQL сгенерирован с помощью {result.get('model', 'unknown')} (оптимизированный пайплайн)",
                "agent_type": f"Optimized Pipeline - {result.get('model', 'unknown')}"
            })
        else:
            return JSONResponse(
                status_code=500,
                content={"success": False, "error": result.get('error', 'Неизвестная ошибка') if isinstance(result, dict) else str(result)}
            )
                
    except Exception as e:
        logger.error(f"Ошибка генерации SQL: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.get("/health")
async def health():
    """Проверка состояния системы"""
    return {"status": "healthy", "agent": "Optimized Dual Pipeline (GPT-4o + Ollama)"}

if __name__ == "__main__":
    import uvicorn
    print("🚀 Запуск веб-интерфейса NL-to-SQL системы...")
    print("📱 Откройте браузер и перейдите по адресу: http://localhost:3000")
    print("🛑 Для остановки нажмите Ctrl+C")
    
    uvicorn.run(app, host="0.0.0.0", port=3000, log_level="info")
