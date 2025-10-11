# 🐛 Отладка NL→SQL системы

## 🎯 **Цель отладки**

Создание полного pipeline для тестирования NL→SQL системы с mock API заказчика и веб-интерфейсом для отладки.

## 🏗️ **Архитектура отладки**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Interface│    │   NL→SQL API     │    │ Mock Customer   │
│   (localhost:3000)│    │   (localhost:8000)│    │ API (localhost:8080)│
│                 │    │                 │    │                 │
│ • HTML интерфейс│    │ • FastAPI       │    │ • Mock API      │
│ • Тестирование │    │ • Vanna AI      │    │ • Ролевые       │
│ • Отладка      │    │ • Генерация SQL │    │   ограничения  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 **Быстрый запуск**

### **1. Установка зависимостей**
```bash
pip install -r requirements.txt
```

### **2. Запуск всей системы**
```bash
python run_system.py
```

### **3. Доступ к интерфейсам**
- **Веб-интерфейс:** http://localhost:3000
- **NL→SQL API:** http://localhost:8000
- **Mock Customer API:** http://localhost:8080
- **API документация:** http://localhost:8000/docs

## 🔧 **Компоненты системы**

### **1. Mock Customer API (`src/mock_customer_api.py`)**
Имитирует API заказчика для тестирования:

**Эндпоинты:**
- `POST /api/sql/execute` - выполнение SQL с ролевыми ограничениями
- `POST /api/sql/validate` - валидация SQL запросов
- `GET /api/users/{user_id}/permissions` - права пользователя
- `GET /health` - проверка здоровья

**Ролевая модель:**
- `admin` - полный доступ
- `manager` - доступ к данным отдела
- `user` - доступ только к своим данным

### **2. Веб-интерфейс (`src/web_interface.py`)**
HTML интерфейс для тестирования:

**Функции:**
- Выбор пользователя и роли
- Ввод вопросов на русском языке
- Генерация SQL запросов
- Выполнение запросов с результатами
- Проверка статуса API

### **3. Подготовка данных обучения (`src/vanna/training_data_preparation.py`)**
Автоматическая подготовка данных для Vanna AI:

**Генерирует:**
- DDL операторы для основных таблиц
- Документацию на русском языке
- Примеры SQL запросов
- Метаданные базы данных

## 📊 **Тестовые данные**

### **Mock пользователи:**
```json
{
  "admin": {
    "role": "admin",
    "permissions": ["read", "write", "delete", "admin"]
  },
  "manager": {
    "role": "manager", 
    "permissions": ["read", "write"],
    "restrictions": ["department_only"]
  },
  "user": {
    "role": "user",
    "permissions": ["read"],
    "restrictions": ["own_data_only"]
  }
}
```

### **Mock данные:**
- **equsers** - 3 пользователя
- **tbl_business_unit** - 2 клиента
- **tbl_principal_assignment** - 2 поручения

## 🧪 **Тестирование**

### **1. Простые запросы:**
- "Покажи всех пользователей"
- "Список отделов"
- "Все клиенты"

### **2. Сложные запросы:**
- "Пользователи по отделам"
- "Поручения с клиентами"
- "Платежи по клиентам"

### **3. Ролевые ограничения:**
- `admin` - видит все данные
- `manager` - видит данные отдела
- `user` - видит только свои данные

## 🔍 **Отладка**

### **1. Проверка статуса API:**
```bash
# NL→SQL API
curl http://localhost:8000/health

# Mock Customer API  
curl http://localhost:8080/health

# Веб-интерфейс
curl http://localhost:3000/api/status
```

### **2. Тестирование запросов:**
```bash
# Генерация SQL
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Покажи всех пользователей",
    "user_id": "admin",
    "role": "admin"
  }'

# Выполнение запроса
curl -X POST "http://localhost:8000/query/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Сколько клиентов в системе?",
    "user_id": "manager",
    "role": "manager"
  }'
```

### **3. Логи системы:**
```bash
# Просмотр логов
tail -f logs/app.log

# Или в консоли при запуске run_system.py
```

## 📋 **Подготовка данных для Vanna AI**

### **Автоматическая подготовка:**
```python
from src.vanna.training_data_preparation import VannaTrainingDataPreparator

preparator = VannaTrainingDataPreparator()
preparator.save_training_data("./training_data")
```

### **Созданные файлы:**
- `training_data/ddl_statements.sql` - DDL операторы
- `training_data/documentation.txt` - документация
- `training_data/sql_examples.json` - примеры SQL
- `training_data/metadata.json` - метаданные

## 🎯 **Сценарии тестирования**

### **1. Базовое тестирование:**
1. Запустить систему: `python run_system.py`
2. Открыть веб-интерфейс: http://localhost:3000
3. Выбрать пользователя `admin`
4. Ввести вопрос: "Покажи всех пользователей"
5. Нажать "Генерировать SQL"
6. Проверить сгенерированный SQL
7. Нажать "Выполнить запрос"
8. Проверить результаты

### **2. Тестирование ролевых ограничений:**
1. Выбрать пользователя `user`
2. Ввести вопрос: "Покажи всех пользователей"
3. Выполнить запрос
4. Проверить, что видны только данные пользователя

### **3. Тестирование сложных запросов:**
1. Выбрать пользователя `manager`
2. Ввести вопрос: "Поручения с клиентами"
3. Выполнить запрос
4. Проверить JOIN и результаты

## 🚨 **Устранение неполадок**

### **Проблема: API недоступен**
```bash
# Проверить процессы
ps aux | grep uvicorn

# Перезапустить сервис
python run_system.py
```

### **Проблема: Ошибки Vanna AI**
```bash
# Проверить OpenAI API ключ
export OPENAI_API_KEY="your-key-here"

# Проверить ChromaDB
ls -la chroma_db/
```

### **Проблема: Ошибки подключения к БД**
```bash
# Проверить PostgreSQL
PGPASSWORD=1234 psql -h localhost -p 5432 -U postgres -d test_docstructure -c "SELECT 1;"
```

## 📈 **Мониторинг**

### **Метрики системы:**
- Время ответа API
- Количество запросов
- Ошибки генерации SQL
- Статус компонентов

### **Логи:**
- NL→SQL API: консоль
- Mock Customer API: консоль  
- Веб-интерфейс: консоль

## 🔄 **Следующие шаги**

1. **Настройка реального OpenAI API ключа**
2. **Подключение к реальной PostgreSQL**
3. **Обучение Vanna AI на данных**
4. **Тестирование с реальными запросами**
5. **Интеграция с реальным API заказчика**

## 📚 **Полезные ссылки**

- [Vanna AI Documentation](https://vanna.ai/docs/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [ChromaDB Documentation](https://docs.trychroma.com/)
