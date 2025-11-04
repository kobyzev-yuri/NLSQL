# Обзор системы NL→SQL

**Дата обновления:** 4 ноября 2025  
**Версия:** 2.0

## 🎯 Описание системы

Система преобразования естественного языка в SQL запросы с использованием GPT-4o и семантического поиска (RAG).

## 🏗️ Архитектура системы

```
┌─────────────────────────────────────────────────────────────────────┐
│                        ПОЛЬЗОВАТЕЛЬ                                 │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐ │
│  │  Simple UI   │  │ Streamlit UI │  │  Vector KB Interface     │ │
│  │  :3000       │  │   :8501      │  │  :8503 (Обучение RAG)   │ │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────────┐
│                        CORE API (:8000)                             │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  QueryService                                                 │  │
│  │  • Определение домена запроса                                │  │
│  │  • Получение DDL таблиц                                      │  │
│  │  • Семантический поиск (RAG) по векторной базе              │  │
│  │  • Построение умного промпта                                 │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                            ↓                                        │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  GPT-4o через ProxyAPI.ru                                    │  │
│  │  • Генерация SQL из промпта                                  │  │
│  │  • Модель: gpt-4o-2024-08-06                                │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    MOCK CUSTOMER API (:8081)                        │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Ролевые ограничения                                         │  │
│  │  • admin: полный доступ                                      │  │
│  │  • manager: данные своего отдела                            │  │
│  │  • user: только свои данные + временные ограничения         │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                            ↓                                        │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Выполнение SQL в PostgreSQL                                 │  │
│  │  • База: test_docstructure                                   │  │
│  │  • Применение ограничений                                    │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    PostgreSQL DATABASE                              │
│  • Таблицы: equsers, tbl_principal_assignment, etc.               │
│  • Векторная база (vanna_vectors) для RAG                        │
└─────────────────────────────────────────────────────────────────────┘
```

## 📊 Компоненты системы

### 1. **Пользовательские интерфейсы**

#### Simple UI (порт 3000)
- Веб-интерфейс с детальной информацией
- Отображение SQL шаблона, плана, ограничений
- Выбор роли и отдела
- Выполнение SQL запросов
- **URL:** `http://localhost:3000`

#### Streamlit UI (порт 8501)
- Основной пользовательский интерфейс
- Упрощенный интерфейс для конечных пользователей
- История запросов
- **URL:** `http://localhost:8501`

#### Vector KB Interface (порт 8503)
- **Интерфейс для обучения и тестирования векторной базы знаний**
- Функции:
  - 🔍 Тестирование семантического поиска
  - ➕ Добавление Q/A пар
  - 🎓 Обучение на примерах DDL/SQL
  - 📊 Метрики и бенчмарки retrieval (Top‑1/Top‑3/MRR)
- **URL:** `http://localhost:8503` (если 8503 занят — 8504)
- **Скрипт запуска:** `./start_vector_kb.sh`

### 2. **Core API (порт 8000)**

Основной сервис генерации SQL с использованием GPT-4o и RAG.

**Основные эндпоинты:**
- `POST /query` - генерация и выполнение SQL
- `GET /health` - проверка здоровья
- `POST /semantic-search` - поиск по векторной базе
- `GET /docs` - Swagger документация

**Процесс генерации SQL:**

1. **Определение домена** (users/payments/reports/general)
2. **Получение DDL** таблиц для домена
3. **Семантический поиск (RAG):**
   - Поиск похожих вопросов в векторной базе
   - Получение примеров Q/A пар
   - Top‑K семантический поиск по векторной базе
4. **Построение промпта:**
   ```
   Domain: USERS
   Tables DDL: [схема таблиц]
   Similar examples: [примеры из RAG]
   Question: [вопрос пользователя]
   ```
5. **Вызов GPT-4o** через ProxyAPI
6. **Возврат SQL**

### 3. **Mock Customer API (порт 8081)**

Имитация API заказчика для применения ролевых ограничений.

**Эндпоинты:**
- `POST /api/sql/execute` - выполнение SQL с ограничениями
- `POST /api/plan/execute` - выполнение плана запроса
- `GET /health` - проверка здоровья

**Ролевая модель:**

| Роль | Доступ | Ограничения |
|------|--------|-------------|
| **admin** | Полный доступ | Нет ограничений |
| **manager** | Отдел | `department = current_department` |
| **user** | Личные данные | `login = current_user` + временные |

**Примеры ограничений:**
```sql
-- user + equsers
SELECT * FROM equsers WHERE deleted = false 
AND login = 'test_user'

-- manager + equsers (отдел IT)
SELECT * FROM equsers WHERE deleted = false 
AND department = (SELECT id FROM eq_departments WHERE name = 'IT')

-- user + tbl_principal_assignment
SELECT * FROM tbl_principal_assignment WHERE deleted = false 
AND creationdatetime >= CURRENT_DATE - INTERVAL '1 month'
```

### 4. **Векторная база знаний (RAG)**

**Таблица:** `vanna_vectors`

**Типы контента:**
- `ddl` - схемы таблиц
- `sql` - Q/A пары (вопрос → SQL)
- `documentation` - документация

**Процесс работы:**
1. Эмбеддинги генерируются через `intfloat/multilingual-e5-base` (768d)
2. Хранятся в PostgreSQL с pgvector
3. Семантический поиск по cosine similarity

**Обучение векторной базы:**
- Через Vector KB Interface (:8503)
- Автоматическое добавление DDL при первом запуске
- Ручное добавление Q/A пар через интерфейс

### 5. **LLM модель**

**Текущая:** GPT-4o (gpt-4o-2024-08-06)  
**Провайдер:** ProxyAPI.ru  
**Base URL:** https://api.proxyapi.ru/openai/v1

**Альтернативы (локальные):**
- Ollama llama3:latest (8B)
- Ollama phi3:latest (3.8B)
- Ollama qwen2.5-coder:1.5b
- Ollama sqlcoder:latest

**Переключение моделей:** через `config.env`

## 🔄 Полный поток данных

### Пример: "Покажи всех пользователей" (роль: user)

```
1. [Simple UI :3000]
   ↓ POST /generate-sql
   {question: "Покажи всех пользователей", role: "user", department: "IT"}

2. [Core API :8000 - QueryService]
   ↓ Определение домена: "users"
   ↓ Получение DDL: equsers, eq_departments
   ↓ RAG поиск: похожие вопросы о пользователях
   ↓ Построение промпта с контекстом

3. [GPT-4o via ProxyAPI]
   ↓ Генерация SQL:
   SELECT * FROM equsers WHERE deleted = false

4. [Mock API :8081]
   ↓ Применение ограничений для role="user":
   SELECT * FROM equsers WHERE deleted = false AND login = 'test_user'

5. [PostgreSQL]
   ↓ Выполнение SQL
   ↓ Возврат результатов (0-1 строка)

6. [Simple UI :3000]
   ✅ Отображение:
   - 📋 SQL Шаблон (оригинальный)
   - 🔐 SQL с ролевыми ограничениями
   - 🧭 План запроса
   - 📊 Результаты
```

## 🚀 Управление системой

### Запуск всех сервисов

```bash
cd NLSQL
./start_all_services.sh
```

### Управление отдельными сервисами

```bash
./run_stack.sh status      # Статус
./run_stack.sh start       # Запуск всех
./run_stack.sh stop        # Остановка всех
./run_stack.sh restart     # Перезапуск всех
./run_stack.sh logs        # Просмотр логов
```

### Запуск интерфейса обучения

```bash
./start_vector_kb.sh       # Запуск Vector KB Interface
```

### Проверка здоровья

```bash
curl http://localhost:8000/health  # Core API
curl http://localhost:8081/health  # Mock API
curl http://localhost:3000         # Simple UI
curl http://localhost:8501         # Streamlit
curl http://localhost:8503         # Vector KB
```

## 📁 Структура проекта

```
sql4A/
├── src/
│   ├── api/
│   │   └── main.py                 # Core API (FastAPI)
│   ├── services/
│   │   ├── query_service.py        # Генерация SQL + RAG
│   │   └── customer_api_service.py # Mock API клиент
│   ├── vanna/
│   │   ├── simple_openai_sql.py    # Обертка GPT-4o
│   │   ├── ollama_native_sql.py    # Обертка Ollama
│   │   └── vanna_semantic_fixed.py # RAG/векторный поиск
│   ├── utils/
│   │   └── plan_sql_converter.py   # SQL ↔ Plan конвертер
│   ├── simple_web_interface.py     # Simple UI
│   ├── streamlit_main.py           # Streamlit UI
│   └── mock_customer_api.py        # Mock API
├── vector_kb_interface.py          # Vector KB Interface 🆕
├── docs/                            # Документация
├── logs/                            # Логи сервисов
├── training_data/                   # Данные для обучения
├── config.env                       # Конфигурация
├── start_all_services.sh           # Запуск всех сервисов
├── run_stack.sh                    # Управление сервисами
└── start_vector_kb.sh              # Запуск Vector KB 🆕
```

## 🔧 Конфигурация

**Файл:** `config.env`

```bash
# GPT-4o через ProxyAPI
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.proxyapi.ru/openai/v1
OPENAI_MODEL=gpt-4o

# База данных
DATABASE_URL=postgresql://postgres:1234@localhost:5432/test_docstructure

# Векторная база
VECTOR_TABLE=vanna_vectors
TRAINING_DATA_DIR=training_data
```

## 📚 Документация

- `SYSTEM_OVERVIEW.md` - Этот документ (обзор системы) 🆕
- `ROLE_RESTRICTIONS_GUIDE.md` - Настройка ролевых ограничений
- `VECTOR_KB_INTERFACE_GUIDE.md` - Работа с интерфейсом обучения
- `SERVICES_STARTUP_GUIDE.md` - Запуск и управление сервисами
- `TRAINING_GUIDE.md` - Обучение векторной базы
- `API_REFERENCE.md` - Справочник API

## 🎯 Ключевые особенности

1. **RAG (Retrieval Augmented Generation)**
   - Семантический поиск по векторной базе (pgvector)
   - Обучение на примерах DDL/документации/Q&A

2. **Ролевая безопасность**
   - 3 уровня доступа: admin, manager, user
   - Автоматическое применение ограничений
   - Настраиваемые правила в `mock_customer_api.py`

3. **Интерфейс обучения Vector KB** 🆕
   - Тестирование поиска RAG
   - Добавление обучающих данных
   - Метрики качества retrieval
   - Переобучение векторов

4. **Множество интерфейсов**
   - Simple UI - детальная информация
   - Streamlit - простота использования
   - Vector KB - обучение и тестирование

5. **Гибкая архитектура**
   - Легкое переключение LLM (GPT-4o ↔ Ollama)
   - Модульная структура
   - Расширяемые ограничения

## 📈 Метрики качества

Просмотр метрик через Vector KB Interface:
- Top-1 Accuracy (точность первого результата)
- Top-3 Accuracy
- MRR (Mean Reciprocal Rank)

<!-- Удалено: Roadmap. Документ отражает только текущий функционал. -->

## 📞 Поддержка

При возникновении проблем:
1. Проверьте статус: `./run_stack.sh status`
2. Просмотрите логи: `tail -f logs/core_api_8000.err`
3. Обратитесь к документации в `docs/`

