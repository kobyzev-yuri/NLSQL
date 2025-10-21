# 📚 Документация NL→SQL системы

## 🎯 Обзор

Этот раздел содержит полную документацию системы NL→SQL, включая архитектуру, API, компоненты и примеры использования.

---

## 📋 Структура документации

### 🏗️ **Архитектура и дизайн**
- [**Системная архитектура**](SYSTEM_ARCHITECTURE.md) - Общая архитектура системы
- [**Финальная архитектура**](FINAL_ARCHITECTURE.md) - Финальная версия архитектуры
- [**Улучшенная архитектура SQL→План**](ENHANCED_SQL_TO_PLAN_ARCHITECTURE.md) - Архитектура конвертера
- [**Интеграция Vanna AI**](ARCHITECTURE_VANNA_INTEGRATION.md) - Интеграция с Vanna AI

### 🔧 **API и интерфейсы**
- [**API Reference**](API_REFERENCE.md) - Полная документация API
- [**Поток данных SQL**](SQL_DATA_FLOW.md) - Поток данных в системе
- [**Отладка системы**](DEBUG_README.md) - Руководство по отладке

### 💻 **Код и компоненты**
- [**Код документация**](CODE_DOCUMENTATION.md) - JavaDoc-стиль документация кода
- [**База знаний**](KNOWLEDGE_BASE.md) - Структурированная база знаний
- [**Методология обучения**](TRAINING_METHODOLOGY.md) - Подходы к обучению системы

### 🚀 **Запуск и конфигурация**
- [**Быстрый старт**](../README.md) - Основное руководство по запуску
- [**Конфигурация**](../config.env) - Переменные окружения
- [**Скрипты запуска**](../run_stack.sh) - Скрипты для запуска системы

---

## 🎯 Быстрый старт

### 1. **Запуск основных сервисов**

```bash
# Simple Web Interface (порт 3000)
uvicorn src.simple_web_interface:app --host 0.0.0.0 --port 3000

# Mock Customer API (порт 8080)
uvicorn src.mock_customer_api:mock_app --host 0.0.0.0 --port 8080
```

### 2. **Проверка работоспособности**

```bash
# Проверка Simple Web Interface
curl http://localhost:3000/health

# Проверка Mock Customer API
curl http://localhost:8080/health
```

### 3. **Тестирование API**

```bash
# Генерация SQL
curl -X POST http://localhost:3000/generate-sql \
  -d "question=покажи пользователей&role=admin&department=IT"

# Выполнение SQL
curl -X POST http://localhost:3000/execute-sql \
  -d "question=покажи пользователей&role=admin&department=IT"
```

---

## 🏗️ Архитектура системы

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Пользователь  │───▶│  Web Interface  │───▶│  Query Service  │
│                 │    │   (FastAPI)      │    │   (Vanna AI)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │◀───│   Mock API      │◀───│   SQL Query     │
│   (Results)     │    │   (Roles)       │    │   (Generated)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### **Основные компоненты:**

1. **Web Interface Layer** - Веб-интерфейс для пользователей
2. **Service Layer** - Бизнес-логика и генерация SQL
3. **Vanna AI Integration** - Семантический поиск и генерация
4. **Mock API Layer** - Применение ролевых ограничений
5. **Database Layer** - PostgreSQL с pgvector

---

## 🔧 Ключевые компоненты

### **1. Simple Web Interface**
- **Файл**: `src/simple_web_interface.py`
- **Порт**: 3000
- **Функции**: Веб-интерфейс, генерация SQL, выполнение запросов

### **2. Query Service**
- **Файл**: `src/services/query_service.py`
- **Функции**: Генерация SQL, управление контекстом, интеграция с Vanna AI

### **3. Vanna AI Integration**
- **Файлы**: `src/vanna/vanna_pgvector_native.py`, `src/vanna/optimized_dual_pipeline.py`
- **Функции**: Семантический поиск, генерация SQL, управление базой знаний

### **4. Mock Customer API**
- **Файл**: `src/mock_customer_api.py`
- **Порт**: 8080
- **Функции**: Применение ролевых ограничений, выполнение SQL

### **5. Utility Tools**
- **Файлы**: `src/utils/plan_sql_converter.py`, `src/tools/generate_embeddings.py`
- **Функции**: Конвертация SQL↔План, генерация эмбеддингов

---

## 📊 База знаний

### **Структура данных**
```sql
vanna_vectors:
├── id (SERIAL PRIMARY KEY)
├── content (TEXT) - Содержимое для поиска
├── content_type (VARCHAR) - Тип контента
├── metadata (JSONB) - Метаданные
├── embedding (VECTOR(1536)) - Вектор эмбеддинга
└── created_at (TIMESTAMP)
```

### **Типы контента**
- `documentation` - Документация схемы БД
- `question_sql` - Пары вопрос-ответ
- `ddl` - DDL скрипты
- `examples` - Примеры SQL

### **Модели эмбеддингов**
- `text-embedding-ada-002` (1536 dim) - Основная модель
- `text-embedding-3-small` (1536 dim) - Альтернативная
- `sentence-transformers` (384-768 dim) - Локальные модели

---

## 🎯 Ролевые ограничения

| Роль | Доступ | Ограничения |
|------|--------|-------------|
| `admin` | Полный доступ | Нет ограничений |
| `manager` | Данные отдела | `department = 'user_department'` |
| `user` | Собственные данные | `owner_id = 'user_id'` |

---

## 📈 Мониторинг и метрики

### **Ключевые метрики**
- **SQL Quality**: % корректных SQL запросов (> 80%)
- **Response Time**: Среднее время генерации (< 5 сек)
- **Context Relevance**: % релевантной информации (> 70%)
- **Table Accuracy**: % использования реальных таблиц (> 90%)

### **Логирование**
- `logs/rag_*.log` - Логи RAG системы
- `logs/sql_generation.log` - Логи генерации SQL
- `logs/performance.log` - Логи производительности

---

## 🔍 Отладка и тестирование

### **Тестовые скрипты**
```bash
# Отладка семантического поиска
python debug_semantic_search.py

# Тестирование RAG системы
python test_semantic_rag.py

# Сравнение моделей
python compare_ollama_models.py
```

### **Проверка здоровья**
```bash
# Все сервисы
curl http://localhost:3000/health
curl http://localhost:8080/health
curl http://localhost:8000/health
```

---

## 📚 Дополнительные ресурсы

### **Конфигурация**
- `config.env` - Переменные окружения
- `docs/scripts/config.json` - Конфигурация системы
- `src/vanna/vector_db_configs.py` - Конфигурация векторных БД

### **Скрипты и утилиты**
- `run_stack.sh` - Запуск всех сервисов
- `src/tools/` - Утилиты для разработки
- `examples/` - Примеры использования

### **Тестирование**
- `compare_ollama_models.py` - Сравнение моделей
- `test_semantic_rag.py` - Тестирование RAG
- `debug_semantic_search.py` - Отладка поиска

---

## 🚀 Разработка

### **Структура проекта**
```
src/
├── api/                    # Core API
├── services/               # Бизнес-логика
├── vanna/                  # Vanna AI интеграция
├── utils/                  # Утилиты
├── tools/                  # Инструменты разработки
├── models/                 # Модели данных
├── simple_web_interface.py # Основной веб-интерфейс
├── mock_customer_api.py    # Mock API
└── streamlit_app.py       # Streamlit интерфейс
```

### **Основные зависимости**
- `fastapi` - Веб-фреймворк
- `vanna` - Vanna AI
- `uvicorn` - ASGI сервер
- `httpx` - HTTP клиент
- `asyncpg` - PostgreSQL драйвер
- `pgvector` - Векторные операции

---

## 📞 Поддержка

### **Проблемы и решения**
- Проверить логи сервисов
- Убедиться в доступности всех портов
- Проверить переменные окружения
- Перезапустить сервисы при необходимости

### **Контакты**
- **Техническая поддержка**: Проверить логи, перезапустить сервисы
- **Проблемы с БД**: Проверить подключение, восстановить из бэкапа
- **API ошибки**: Проверить ключи, переключиться на fallback

---

**Версия документации**: 1.0.0  
**Дата обновления**: 2024-10-15  
**Автор**: NL→SQL Team





