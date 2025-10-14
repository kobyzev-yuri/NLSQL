# NL→SQL Assistant

Система для преобразования естественного языка в SQL с поддержкой ролевых ограничений и KB (pgvector).

## 🚀 Быстрый старт (актуально)
1) Core API (порт 8000):
PYTHONPATH=$(pwd) uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
2) Mock Customer API (порт 8080):
PYTHONPATH=$(pwd) uvicorn src.mock_customer_api:mock_app --host 0.0.0.0 --port 8080 --reload
3) Простой веб‑интерфейс (порт 3000):
PYTHONPATH=$(pwd) uvicorn src.simple_web_interface:app --host 0.0.0.0 --port 3000 --reload
4) Streamlit UI (порт 8501):
PYTHONPATH=$(pwd) streamlit run src/streamlit_app.py --server.port 8501 --server.address 0.0.0.0

## 🌐 Интерфейсы
- http://localhost:3000 (simple UI)
- http://localhost:8501 (Streamlit)
- http://localhost:8000/docs (Core API)
- http://localhost:8080/health (Mock API)

## Файлы
- src/api/main.py, src/mock_customer_api.py, src/simple_web_interface.py, src/streamlit_app.py
- src/services/query_service.py, src/vanna/optimized_dual_pipeline.py, src/utils/plan_sql_converter.py

## 📊 Результаты тестирования моделей

Проведено сравнительное тестирование 7 моделей Ollama для генерации SQL:

### 🏆 Рейтинг по качеству
1. **sqlcoder:latest** - 7.0/5 (лучшее качество)
2. **llama3:latest** - 6.8/5 (стабильное качество)  
3. **qwen3:8b** - 6.6/5 (хороший баланс)
4. **qwen2.5-coder:1.5b** - 6.4/5 (оптимальный выбор)
5. **qwen2.5:1.5b** - 6.4/5 (компактная)
6. **phi3:latest** - 6.2/5 (быстрая)
7. **mistral:7b** - 5.8/5 (медленный)

### ⚡ Рейтинг по скорости
1. **qwen2.5-coder:1.5b** - 13.9с (самый быстрый)
2. **phi3:latest** - 19.5с
3. **llama3:latest** - 31.0с
4. **qwen2.5:1.5b** - 31.0с
5. **qwen3:8b** - 33.6с
6. **sqlcoder:latest** - 33.8с
7. **mistral:7b** - 89.0с (самый медленный)

### 📋 Документация результатов
- [BENCHMARK_RESULTS.md](BENCHMARK_RESULTS.md) - полные результаты тестирования
- [SQL_QUALITY_ANALYSIS.md](SQL_QUALITY_ANALYSIS.md) - детальный анализ критериев оценки
- [ollama_models_comparison.json](ollama_models_comparison.json) - данные в JSON формате

### 🎯 Рекомендации
- **Для продакшена**: `qwen2.5-coder:1.5b` (оптимальный баланс скорости и качества)
- **Для максимальной точности**: `sqlcoder:latest`
- **Для быстрого прототипирования**: `qwen2.5-coder:1.5b`

## Конфигурация
ENV: PROXYAPI_KEY/OPENAI_API_KEY, OPENAI_BASE_URL, OLLAMA_BASE_URL, OLLAMA_MODEL, CUSTOMER_DB_DSN
