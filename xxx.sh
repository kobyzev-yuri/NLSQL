cd /mnt/ai/cnn/sql4A

# 1) Создать актуальный README в docs
mkdir -p docs
cat > docs/README_CURRENT.md <<'EOF'
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

## Конфигурация
ENV: PROXYAPI_KEY/OPENAI_API_KEY, OPENAI_BASE_URL, OLLAMA_BASE_URL, OLLAMA_MODEL, CUSTOMER_DB_DSN
EOF

# 2) Скопировать в корень и закоммитить
cp docs/README_CURRENT.md README.md
git add README.md docs/README_CURRENT.md
git commit -m "docs: update README to current run instructions (8000/8080/3000/8501), env-based config"
git push origin main
