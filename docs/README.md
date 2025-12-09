# Документация NL→SQL

**Актуальные документы:**

## 🚀 Быстрый старт
- **[README.md](../README.md)** (корень) - Быстрый старт и обзор системы

## 📚 Основные документы
- **[SYSTEM_OVERVIEW.md](SYSTEM_OVERVIEW.md)** - Полный обзор системы, архитектура, компоненты
- **[USER_GUIDE.md](USER_GUIDE.md)** - Руководство для пользователей системы
- **[API_REFERENCE.md](API_REFERENCE.md)** - Справочник API эндпоинтов

## ⚙️ Настройка и конфигурация
- **[SERVICES_STARTUP_GUIDE.md](SERVICES_STARTUP_GUIDE.md)** - Запуск и управление сервисами
- **[ROLE_RESTRICTIONS_GUIDE.md](ROLE_RESTRICTIONS_GUIDE.md)** - Настройка ролевых ограничений безопасности
- **[POSTGRESQL_INSTALLATION.md](POSTGRESQL_INSTALLATION.md)** - Установка и настройка PostgreSQL
- **[QUICK_PGADMIN_SETUP.md](QUICK_PGADMIN_SETUP.md)** - Быстрая настройка pgAdmin

## 🎓 Обучение Knowledge Base
- **[KB_TRAINING_FROM_SCRATCH.md](KB_TRAINING_FROM_SCRATCH.md)** ⭐ - **Полное руководство по обучению KB с нуля** (рекомендуется)
- **[TRAINING_GUIDE.md](TRAINING_GUIDE.md)** - Основное руководство по обучению RAG
- **[VECTOR_KB_INTERFACE_GUIDE.md](VECTOR_KB_INTERFACE_GUIDE.md)** - Работа с интерфейсом обучения (Streamlit)
- **[KB_TRAINING_UNIFICATION.md](KB_TRAINING_UNIFICATION.md)** - Техническая документация по унификации обучения
- **[CUSTOMER_DATA_PREPARATION_GUIDE.md](CUSTOMER_DATA_PREPARATION_GUIDE.md)** - Инструкция для заказчика по подготовке данных

## 🔍 Оптимизация и производительность
- **[SQL_OPTIMIZATION_TRAINING_GUIDE.md](SQL_OPTIMIZATION_TRAINING_GUIDE.md)** - Обучение на оптимизированных SQL
- **[EXPLAIN_PLAN_INTEGRATION.md](EXPLAIN_PLAN_INTEGRATION.md)** - Интеграция EXPLAIN планов в контекст генерации
- **[EXPLAIN_PLAN_OPTIMIZATION.md](EXPLAIN_PLAN_OPTIMIZATION.md)** - Оптимизация генерации EXPLAIN планов
- **[OPTIMIZED_SQL_MARKING.md](OPTIMIZED_SQL_MARKING.md)** - Маркировка оптимизированных SQL
- **[OPTIMIZATION_VALIDATION.md](OPTIMIZATION_VALIDATION.md)** - Валидация оптимизации SQL
- **[SLOW_QUERY_ANALYSIS.md](../SLOW_QUERY_ANALYSIS.md)** - Анализ медленных запросов

## 📊 Chunking и RAG
- **[CHUNKING_STRATEGY.md](CHUNKING_STRATEGY.md)** - Стратегия разбиения на чанки и оптимизация параметров
- **[VECTOR_DB.md](VECTOR_DB.md)** - Структура векторной базы данных (pgvector)
- **[RETRIEVAL_BENCHMARKS.md](RETRIEVAL_BENCHMARKS.md)** - Метрики качества RAG поиска
- **[METRICS_EXPLANATION.md](METRICS_EXPLANATION.md)** - Объяснение метрик качества
- **[EVALUATION_METHODOLOGY.md](EVALUATION_METHODOLOGY.md)** - Методология оценки качества

## 🧪 Тестирование
- **[KB_TESTING_GUIDE.md](KB_TESTING_GUIDE.md)** - Руководство по тестированию Knowledge Base

## 🗄️ Специфичные базы данных
- **[ORACLE_DDL_EXTRACTION.md](ORACLE_DDL_EXTRACTION.md)** - Извлечение DDL из Oracle
- **[ORACLE_KB_ARCHITECTURE.md](ORACLE_KB_ARCHITECTURE.md)** - Архитектура KB для Oracle

## 📖 Дополнительные документы
- **[customer_requests/INTEGRATION_DATAFLOW.md](customer_requests/INTEGRATION_DATAFLOW.md)** - Интеграция с заказчиком
- **[analysis/DATABASE_SCHEMA_ANALYSIS.md](analysis/DATABASE_SCHEMA_ANALYSIS.md)** - Анализ схемы базы данных

## ⚙️ Конфигурация и настройка
- **[LLM_PROVIDER_SWITCHING_GUIDE.md](LLM_PROVIDER_SWITCHING_GUIDE.md)** - Переключение между Ollama и GPT
- **[OLLAMA_TROUBLESHOOTING.md](OLLAMA_TROUBLESHOOTING.md)** - Устранение проблем с Ollama
- **[TIMEOUT_CONFIGURATION.md](TIMEOUT_CONFIGURATION.md)** - Настройка таймаутов
- **[SLOW_QUERY_ANALYSIS.md](SLOW_QUERY_ANALYSIS.md)** - Анализ и оптимизация медленных запросов

---

## 📦 Архив

**Устаревшие документы** перемещены в `archive/2025_cleanup/`:
- Планы и анализы интерфейса
- Дублирующиеся гайды по обучению (интегрированы в KB_TRAINING_FROM_SCRATCH.md)
- Тестовые документы
- Отчеты и анализы
- Временные документы

---

## 💡 Рекомендации по чтению

**Для начала работы:**
1. [README.md](../README.md) - быстрый старт
2. [SYSTEM_OVERVIEW.md](SYSTEM_OVERVIEW.md) - понимание архитектуры
3. [SERVICES_STARTUP_GUIDE.md](SERVICES_STARTUP_GUIDE.md) - запуск системы

**Для обучения KB:**
1. [KB_TRAINING_FROM_SCRATCH.md](KB_TRAINING_FROM_SCRATCH.md) ⭐ - полное руководство
2. [VECTOR_KB_INTERFACE_GUIDE.md](VECTOR_KB_INTERFACE_GUIDE.md) - работа с интерфейсом
3. [CUSTOMER_DATA_PREPARATION_GUIDE.md](CUSTOMER_DATA_PREPARATION_GUIDE.md) - подготовка данных

**Для разработчиков:**
1. [API_REFERENCE.md](API_REFERENCE.md) - API эндпоинты
2. [KB_TRAINING_UNIFICATION.md](KB_TRAINING_UNIFICATION.md) - техническая документация
3. [VECTOR_DB.md](VECTOR_DB.md) - структура векторной БД
