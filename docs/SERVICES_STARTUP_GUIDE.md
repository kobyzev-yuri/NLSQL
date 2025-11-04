# 🚀 Руководство по запуску сервисов NL→SQL

## 📋 Обзор сервисов

Система состоит из 4 основных сервисов:

| Сервис | Порт | Описание | URL |
|--------|------|----------|-----|
| **Core API** | 8000 | Основной API для NL→SQL | http://localhost:8000/docs |
| **Mock API** | 8081 | API заказчика с ролевыми ограничениями | http://localhost:8081/health |
| **Simple UI** | 3000 | Простой веб-интерфейс | http://localhost:3000 |
| **Streamlit UI** | 8501 | Продвинутый интерфейс | http://localhost:8501 |

## 🔧 Архитектура взаимодействия

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit     │    │   Simple UI     │    │   Core API      │
│   (8501)        │───▶│   (3000)        │───▶│   (8000)        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │
         │                       ▼
         │              ┌─────────────────┐
         └──────────────▶│   Mock API      │
                        │   (8081)        │
                        └─────────────────┘
```

## 🐍 Требования

- **Python**: 3.10+
- **Виртуальное окружение**: Anaconda `py310`
- **База данных**: PostgreSQL с тестовой БД `test_docstructure`

## ⚡ Быстрый запуск

### 1. Активация окружения
```bash
cd /mnt/ai/cnn/sql4A
source /mnt/ai/src/anaconda3/bin/activate py310
source config.env
```

### 2. Запуск всех сервисов
```bash
# Автоматический запуск
./start_all_services.sh

# Или ручной запуск
./run_stack.sh start
```

### 3. Проверка статуса
```bash
./run_stack.sh status
```

## 🛠️ Ручной запуск сервисов

### Core API (8000)
```bash
cd /mnt/ai/cnn/sql4A
source /mnt/ai/src/anaconda3/bin/activate py310
source config.env
PYTHONPATH=$(pwd) uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Mock API (8081)
```bash
cd /mnt/ai/cnn/sql4A
source /mnt/ai/src/anaconda3/bin/activate py310
source config.env
PYTHONPATH=$(pwd) uvicorn src.mock_customer_api:mock_app --host 0.0.0.0 --port 8081 --reload
```

### Simple UI (3000)
```bash
cd /mnt/ai/cnn/sql4A
source /mnt/ai/src/anaconda3/bin/activate py310
source config.env
PYTHONPATH=$(pwd) uvicorn src.simple_web_interface:app --host 0.0.0.0 --port 3000 --reload
```

### Streamlit UI (8501)
```bash
cd /mnt/ai/cnn/sql4A
source /mnt/ai/src/anaconda3/bin/activate py310
source config.env
PYTHONPATH=$(pwd) streamlit run src/streamlit_main.py --server.port 8501 --server.address 0.0.0.0
```

## 🔍 Проверка работоспособности

### Проверка портов
```bash
netstat -tlnp | grep -E ":(3000|8000|8081|8501)"
```

### Проверка HTTP
```bash
curl -s http://localhost:8000/docs | head -1
curl -s http://localhost:8081/health
curl -s http://localhost:3000 | head -1
curl -s http://localhost:8501 | head -1
```

## 🛑 Остановка сервисов

### Остановка всех сервисов
```bash
./run_stack.sh stop
```

### Остановка конкретных процессов
```bash
pkill -f "uvicorn.*8000"  # Core API
pkill -f "uvicorn.*8081"  # Mock API
pkill -f "uvicorn.*3000"  # Simple UI
pkill -f "streamlit.*8501" # Streamlit
```

## 📊 Мониторинг

### Просмотр логов
```bash
./run_stack.sh logs
```

### Статус сервисов
```bash
./run_stack.sh status
```

## 🔧 Управление

### Команды run_stack.sh
```bash
./run_stack.sh start    # Запуск всех сервисов
./run_stack.sh stop     # Остановка всех сервисов
./run_stack.sh restart  # Перезапуск всех сервисов
./run_stack.sh status   # Статус сервисов
./run_stack.sh logs     # Просмотр логов
```

## 🐛 Устранение проблем

### Streamlit не загружается (белый экран)
```bash
# Убедитесь, что используете правильный файл
streamlit run src/streamlit_main.py --server.port 8501 --server.address 0.0.0.0

# НЕ используйте src/streamlit_app.py (удален из-за рекурсии)
```

### Порт уже занят
```bash
# Найти процесс, занимающий порт
lsof -i :8080
lsof -i :8081

# Остановить процесс
sudo fuser -k 8080/tcp
sudo fuser -k 8081/tcp
```

### Неправильные порты в коде
```bash
# Убедитесь, что Mock API запущен на порту 8081, а не 8080
# Simple UI и Streamlit обращаются к Mock API на порту 8081
# Проверьте в коде: grep -r "8081" src/
```

### Проблемы с виртуальным окружением
```bash
# Проверить активное окружение
echo $CONDA_DEFAULT_ENV

# Переактивировать
conda deactivate
source /mnt/ai/src/anaconda3/bin/activate py310
```

### Проблемы с базой данных
```bash
# Проверить подключение к БД
psql -h localhost -U postgres -d test_docstructure -c "SELECT 1;"
```

## 📝 Конфигурация

### Переменные окружения (config.env)
```bash
# ProxyAPI Configuration
PROXYAPI_BASE_URL=https://api.proxyapi.ru/openai/v1
PROXYAPI_API_KEY=sk-...
PROXYAPI_CHAT_MODEL=gpt-4o

# Database Configuration
DATABASE_URL=postgresql://postgres:1234@localhost:5432/test_docstructure

# Vanna AI Configuration
VECTOR_TABLE=vanna_vectors
TRAINING_DATA_DIR=training_data
```

## 🎯 Использование

1. **Откройте браузер** и перейдите на http://localhost:3000 или http://localhost:8501
2. **Введите вопрос** на русском языке (например: "Покажи всех пользователей")
3. **Выберите роль** (admin, manager, user)
4. **Нажмите "Генерировать SQL"** или "Выполнить SQL"
5. **Просмотрите результаты** с примененными ролевыми ограничениями

## 📚 Дополнительные ресурсы

- [API Reference](API_REFERENCE.md)
- [System Overview](SYSTEM_OVERVIEW.md)
- [Training Guide](TRAINING_GUIDE.md)
- [Vector DB](VECTOR_DB.md)
