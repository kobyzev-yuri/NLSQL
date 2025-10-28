#!/usr/bin/env python3
"""
Интерфейс для тестирования и дообучения векторной базы знаний
Позволяет:
- Тестировать качество поиска в векторке
- Добавлять новые Q/A пары
- Обучать на новых данных
- Анализировать метрики качества
"""

import streamlit as st
import requests
import json
import time
import sys
import os
from typing import Dict, List, Any, Optional
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Настройка страницы
st.set_page_config(
    page_title="Vector KB Interface",
    page_icon="🧠",
    layout="wide"
)

# Заголовок
st.title("🧠 Vector Knowledge Base Interface")
st.markdown("Интерфейс для тестирования и дообучения векторной базы знаний")

# Конфигурация API
API_BASE_URL = "http://localhost:3000"

def test_api_connection():
    """Проверка подключения к FastAPI"""
    try:
        response = requests.get(f"{API_BASE_URL}/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get("ready", False)
        return False
    except:
        return False

def call_api_search(question: str, search_type: str = "semantic", limit: int = 5):
    """Вызов API для тестирования поиска через generate-sql"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/generate-sql",
            data={
                "question": question,
                "role": "admin",
                "department": "IT"
            },
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                # Форматируем результат как результаты поиска
                results = []
                if data.get('sql'):
                    results.append({
                        "content": f"Сгенерированный SQL: {data['sql']}",
                        "type": "sql",
                        "rank": 1
                    })
                if data.get('plan'):
                    results.append({
                        "content": f"План запроса: {data['plan']}",
                        "type": "plan", 
                        "rank": 2
                    })
                if data.get('explanation'):
                    results.append({
                        "content": f"Объяснение: {data['explanation']}",
                        "type": "explanation",
                        "rank": 3
                    })
                
                return {
                    "success": True,
                    "question": question,
                    "search_type": search_type,
                    "results": results[:limit],
                    "total_found": len(results[:limit])
                }
            else:
                return {"error": data.get('error', 'Неизвестная ошибка')}
        else:
            return {"error": f"HTTP {response.status_code}", "details": response.text}
    except Exception as e:
        return {"error": str(e)}

def call_api_generate_sql(question: str):
    """Вызов API для генерации SQL"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/generate-sql",
            data={"question": question},
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP {response.status_code}", "details": response.text}
    except Exception as e:
        return {"error": str(e)}

# Основные вкладки
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🔍 Тестирование поиска", 
    "📝 Добавление Q/A", 
    "🎓 Обучение", 
    "🚀 Оптимизация SQL",
    "📊 Аналитика", 
    "⚙️ Настройки"
])

with tab1:
    st.header("🔍 Тестирование качества поиска")
    
    # Тестовые запросы
    test_queries = [
        "Покажи всех пользователей",
        "Поручения за последний месяц", 
        "Клиенты с определенным ИНН",
        "Платежи по отделам",
        "Статистика по пользователям"
    ]
    
    # Примеры для разных типов поиска
    semantic_examples = [
        "Покажи всех пользователей системы",
        "Поручения за последний месяц",
        "Платежи по клиентам за квартал", 
        "Статистика по отделам",
        "Активные пользователи с встроенными аккаунтами"
    ]
    
    ddl_examples = [
        "Структура таблицы пользователей",
        "Схема таблицы поручений",
        "Поля таблицы платежей",
        "Связи между таблицами",
        "Индексы для поиска"
    ]
    
    doc_examples = [
        "Описание бизнес-процессов",
        "Ролевые ограничения системы",
        "Логика работы с документами",
        "Правила безопасности данных",
        "Архитектура системы"
    ]
    
    qa_examples = [
        "Примеры SQL запросов",
        "Частые вопросы пользователей",
        "Типовые бизнес-запросы",
        "Сложные аналитические запросы",
        "Отчеты по системе"
    ]
    
    col1, col2 = st.columns([2, 1])
    
    with col2:
        search_type = st.selectbox(
            "Тип поиска:",
            ["semantic", "ddl", "documentation", "examples"],
            help="Выберите тип поиска для тестирования"
        )
        
        max_results = st.slider("Максимум результатов:", 1, 20, 5)
    
    with col1:
        # Динамические примеры в зависимости от типа поиска
        if search_type == "semantic":
            examples = semantic_examples
        elif search_type == "ddl":
            examples = ddl_examples
        elif search_type == "documentation":
            examples = doc_examples
        elif search_type == "examples":
            examples = qa_examples
        else:
            examples = test_queries
        
        # Показываем примеры
        st.markdown("**💡 Примеры запросов:**")
        for i, example in enumerate(examples, 1):
            if st.button(f"{i}. {example}", key=f"example_{i}"):
                st.session_state.selected_query = example
        
        query = st.text_area(
            "Введите тестовый запрос:",
            value=st.session_state.get('selected_query', examples[0]),
            height=100,
            help="Введите вопрос на естественном языке для тестирования поиска"
        )
    
    if st.button("🔍 Тестировать поиск", type="primary"):
        if query:
            # Проверяем подключение к API
            if not test_api_connection():
                st.error("❌ FastAPI недоступен на порту 3000. Убедитесь, что сервис запущен.")
                st.stop()
            
            with st.spinner("Выполняю поиск через FastAPI..."):
                try:
                    # Вызываем API для поиска
                    search_result = call_api_search(query, search_type, max_results)
                    
                    if "error" in search_result:
                        st.error(f"Ошибка API: {search_result['error']}")
                        st.stop()
                    
                    results = search_result.get('results', [])
                    st.success(f"Найдено {len(results)} результатов")
                    
                    # Отображаем результаты
                    for i, result in enumerate(results[:max_results]):
                        with st.expander(f"Результат {i+1}"):
                            if isinstance(result, dict):
                                content = result.get('content', str(result))
                            else:
                                content = str(result)
                            st.code(content, language="sql")
                            
                except Exception as e:
                    st.error(f"Ошибка поиска: {e}")

with tab2:
    st.header("📝 Добавление новых Q/A пар")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Ручное добавление")
        
        # Примеры Q/A пар
        qa_examples = [
            {
                "question": "Покажи всех пользователей системы",
                "sql": "SELECT * FROM equsers WHERE deleted = FALSE"
            },
            {
                "question": "Поручения за последний месяц",
                "sql": "SELECT * FROM tbl_principal_assignment WHERE creationdatetime >= CURRENT_DATE - INTERVAL '1 month'"
            },
            {
                "question": "Клиенты с определенным ИНН",
                "sql": "SELECT * FROM tbl_business_unit WHERE inn = '1234567890'"
            },
            {
                "question": "Платежи по отделам",
                "sql": "SELECT d.name, SUM(p.amount) FROM tbl_incoming_payments p JOIN equsers u ON p.user_id = u.id JOIN eq_departments d ON u.department = d.id GROUP BY d.name"
            },
            {
                "question": "Статистика по пользователям",
                "sql": "SELECT COUNT(*) as total_users, COUNT(CASE WHEN deleted = FALSE THEN 1 END) as active_users FROM equsers"
            }
        ]
        
        # Показываем примеры
        st.markdown("**💡 Примеры Q/A пар:**")
        selected_example = st.selectbox(
            "Выберите пример:",
            ["Выберите пример..."] + [f"{i+1}. {ex['question']}" for i, ex in enumerate(qa_examples)],
            key="qa_example_selector"
        )
        
        if selected_example != "Выберите пример...":
            example_idx = int(selected_example.split('.')[0]) - 1
            example = qa_examples[example_idx]
            st.session_state.example_question = example['question']
            st.session_state.example_sql = example['sql']
        
        question = st.text_area(
            "Вопрос:", 
            value=st.session_state.get('example_question', ''),
            height=100
        )
        sql = st.text_area(
            "SQL запрос:", 
            value=st.session_state.get('example_sql', ''),
            height=200
        )
        
        if st.button("➕ Добавить Q/A пару"):
            if question and sql:
                # Проверяем подключение к API
                if not test_api_connection():
                    st.error("❌ FastAPI недоступен на порту 3000. Убедитесь, что сервис запущен.")
                    st.stop()
                
                try:
                    # Пока что используем CLI скрипт, так как API для добавления Q/A пар еще не реализован
                    st.info("⚠️ Добавление Q/A пар через интерфейс пока не поддерживается. Используйте CLI скрипт qa_management_script.py")
                    st.code(f"python qa_management_script.py --action add --input qa_pairs.json")
                    
                    # В будущем здесь будет вызов API для добавления Q/A пар
                    # api_result = call_api_add_qa(question, sql)
                    
                except Exception as e:
                    st.error(f"Ошибка добавления: {e}")
            else:
                st.warning("Заполните оба поля")
    
    with col2:
        st.subheader("Массовое добавление")
        
        # Загрузка файла
        uploaded_file = st.file_uploader(
            "Загрузите JSON файл с Q/A парами:",
            type=['json'],
            help="Формат: [{'question': '...', 'sql': '...'}, ...]"
        )
        
        if uploaded_file:
            try:
                data = json.load(uploaded_file)
                st.info(f"Загружено {len(data)} Q/A пар")
                
                if st.button("📥 Импортировать все"):
                    # Проверяем подключение к API
                    if not test_api_connection():
                        st.error("❌ FastAPI недоступен на порту 3000. Убедитесь, что сервис запущен.")
                        st.stop()
                    
                    with st.spinner("Импортирую Q/A пары..."):
                        # Пока что используем CLI скрипт, так как API для массового добавления еще не реализован
                        st.info("⚠️ Массовое добавление Q/A пар через интерфейс пока не поддерживается. Используйте CLI скрипт:")
                        st.code(f"python qa_management_script.py --action add --input qa_pairs.json")
                        
                        # В будущем здесь будет вызов API для массового добавления
                        # api_result = call_api_bulk_add_qa(data)
                        
                        st.success(f"Инструкции для импорта {len(data)} Q/A пар показаны выше!")
            except Exception as e:
                st.error(f"Ошибка загрузки файла: {e}")

with tab3:
    st.header("🎓 Обучение на новых данных")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Обучение на DDL")
        
        # Примеры DDL
        ddl_examples = [
            "CREATE TABLE equsers (id SERIAL PRIMARY KEY, login VARCHAR(50), email VARCHAR(100), department VARCHAR(50), deleted BOOLEAN DEFAULT FALSE);",
            "CREATE TABLE tbl_principal_assignment (id SERIAL PRIMARY KEY, assignment_number VARCHAR(20), amount DECIMAL(15,2), business_unit_id INTEGER, creationdatetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP);",
            "CREATE TABLE tbl_business_unit (id SERIAL PRIMARY KEY, business_unit_name VARCHAR(200), inn VARCHAR(12), phone VARCHAR(20));",
            "CREATE TABLE eq_departments (id SERIAL PRIMARY KEY, name VARCHAR(100), code VARCHAR(20), deleted BOOLEAN DEFAULT FALSE);",
            "CREATE TABLE tbl_incoming_payments (id SERIAL PRIMARY KEY, amount DECIMAL(15,2), payment_date DATE, user_id INTEGER, business_unit_id INTEGER);"
        ]
        
        # Показываем примеры DDL
        st.markdown("**💡 Примеры DDL скриптов:**")
        selected_ddl = st.selectbox(
            "Выберите пример DDL:",
            ["Выберите пример..."] + [f"{i+1}. {ex.split('(')[0].split()[-1]}" for i, ex in enumerate(ddl_examples)],
            key="ddl_example_selector"
        )
        
        if selected_ddl != "Выберите пример...":
            ddl_idx = int(selected_ddl.split('.')[0]) - 1
            st.session_state.selected_ddl = ddl_examples[ddl_idx]
        
        ddl_text = st.text_area(
            "DDL скрипты:",
            value=st.session_state.get('selected_ddl', ''),
            height=200,
            help="Вставьте CREATE TABLE, ALTER TABLE и другие DDL команды"
        )
        
        if st.button("📚 Обучить на DDL"):
            if ddl_text:
                # Проверяем подключение к API
                if not test_api_connection():
                    st.error("❌ FastAPI недоступен на порту 3000. Убедитесь, что сервис запущен.")
                    st.stop()
                
                try:
                    # Пока что используем CLI скрипт, так как API для обучения еще не реализован
                    st.info("⚠️ Обучение на DDL через интерфейс пока не поддерживается. Используйте CLI скрипт:")
                    st.code(f"python qa_management_script.py --action embeddings")
                    
                    # В будущем здесь будет вызов API для обучения на DDL
                    # api_result = call_api_train_ddl(ddl_text)
                    
                except Exception as e:
                    st.error(f"Ошибка обучения: {e}")
    
    with col2:
        st.subheader("Обучение на документации")
        
        # Примеры документации
        doc_examples = [
            "Система управления документами DocStructureSchema содержит 12 основных таблиц. Пользователи (equsers) принадлежат к отделам (eq_departments) и имеют ролевые ограничения.",
            "Поручения (tbl_principal_assignment) создаются для бизнес-единиц (tbl_business_unit) и привязаны к пользователям. Платежи (tbl_incoming_payments) связаны с поручениями и клиентами.",
            "Ролевая модель: admin - полный доступ, manager - данные своего отдела, user - только свои данные. Ограничения применяются на уровне SQL запросов.",
            "Бизнес-логика: поручения создаются на основе платежей, пользователи работают в рамках своих отделов, клиенты имеют уникальные ИНН и контактные данные.",
            "Архитектура: PostgreSQL с Row Level Security, векторная база pgvector для семантического поиска, API на FastAPI с поддержкой ролевых ограничений."
        ]
        
        # Показываем примеры документации
        st.markdown("**💡 Примеры документации:**")
        selected_doc = st.selectbox(
            "Выберите пример документации:",
            ["Выберите пример..."] + [f"{i+1}. {ex[:50]}..." for i, ex in enumerate(doc_examples)],
            key="doc_example_selector"
        )
        
        if selected_doc != "Выберите пример...":
            doc_idx = int(selected_doc.split('.')[0]) - 1
            st.session_state.selected_doc = doc_examples[doc_idx]
        
        doc_text = st.text_area(
            "Документация:",
            value=st.session_state.get('selected_doc', ''),
            height=200,
            help="Вставьте описание бизнес-логики, связей таблиц и т.д."
        )
        
        if st.button("📖 Обучить на документации"):
            if doc_text:
                # Проверяем подключение к API
                if not test_api_connection():
                    st.error("❌ FastAPI недоступен на порту 3000. Убедитесь, что сервис запущен.")
                    st.stop()
                
                try:
                    # Пока что используем CLI скрипт, так как API для обучения еще не реализован
                    st.info("⚠️ Обучение на документации через интерфейс пока не поддерживается. Используйте CLI скрипт:")
                    st.code(f"python qa_management_script.py --action embeddings")
                    
                    # В будущем здесь будет вызов API для обучения на документации
                    # api_result = call_api_train_documentation(doc_text)
                    
                except Exception as e:
                    st.error(f"Ошибка обучения: {e}")
    
    # Генерация эмбеддингов
    st.subheader("🔄 Генерация эмбеддингов")
    
    st.info("💡 Для работы с векторкой используйте CLI скрипт:")
    st.code("""
# Создание шаблона Q/A пар
python qa_management_script.py --action template --output qa_template.json

# Добавление Q/A пар
python qa_management_script.py --action add --input qa_pairs.json --validate

# Тестирование качества
python qa_management_script.py --action test --input qa_pairs.json

# Генерация эмбеддингов
python qa_management_script.py --action embeddings

# 🚀 НОВОЕ: Обучение на оптимизированных SQL
python qa_management_script.py --action optimize --input optimized_sql_examples.json --output performance_report.json

# Анализ производительности SQL
python qa_management_script.py --action performance --input optimized_sql_examples.json
    """)
    
    if st.button("⚡ Сгенерировать эмбеддинги"):
        # Проверяем подключение к API
        if not test_api_connection():
            st.error("❌ FastAPI недоступен на порту 3000. Убедитесь, что сервис запущен.")
            st.stop()
        
        with st.spinner("Генерирую эмбеддинги через CLI скрипт..."):
            try:
                # Пока что используем CLI скрипт, так как API для генерации эмбеддингов еще не реализован
                st.info("💡 Генерация эмбеддингов через CLI скрипт:")
                st.code("python qa_management_script.py --action embeddings")
                
                # В будущем здесь будет вызов API для генерации эмбеддингов
                # api_result = call_api_generate_embeddings()
                
                st.success("Инструкции для генерации эмбеддингов показаны выше!")
            except Exception as e:
                st.error(f"Ошибка генерации эмбеддингов: {e}")

with tab4:
    st.header("🚀 Оптимизация SQL")
    
    st.markdown("""
    **Цель:** Обучение модели генерировать не просто рабочий SQL, а **эффективный SQL** с учетом производительности.
    
    **Подход:** Использование Q/A пар где один SQL делает ту же работу, но быстрее и дешевле по explain plan.
    """)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📚 Примеры оптимизации")
        
        # Примеры оптимизированных SQL
        optimization_examples = [
            {
                "question": "Покажи всех пользователей",
                "sql_basic": "SELECT * FROM equsers",
                "sql_optimized": "SELECT id, login, email, department FROM equsers WHERE deleted = FALSE",
                "improvement": "50% меньше данных, быстрее выполнение"
            },
            {
                "question": "Поручения за последний месяц", 
                "sql_basic": "SELECT * FROM tbl_principal_assignment WHERE creationdatetime >= CURRENT_DATE - INTERVAL '1 month'",
                "sql_optimized": "SELECT assignment_number, amount, creationdatetime FROM tbl_principal_assignment WHERE creationdatetime >= CURRENT_DATE - INTERVAL '1 month' ORDER BY creationdatetime DESC",
                "improvement": "30% быстрее за счет индекса, логичная сортировка"
            },
            {
                "question": "Платежи по отделам",
                "sql_basic": "SELECT d.name, SUM(p.amount) FROM tbl_incoming_payments p JOIN equsers u ON p.user_id = u.id JOIN eq_departments d ON u.department = d.id GROUP BY d.name",
                "sql_optimized": "SELECT d.name, SUM(p.amount) as total_amount, COUNT(p.id) as payment_count FROM tbl_incoming_payments p INNER JOIN equsers u ON p.user_id = u.id INNER JOIN eq_departments d ON u.department = d.id WHERE p.payment_date >= CURRENT_DATE - INTERVAL '1 year' GROUP BY d.name ORDER BY total_amount DESC",
                "improvement": "60% быстрее за счет фильтрации и правильных JOIN"
            }
        ]
        
        for i, example in enumerate(optimization_examples, 1):
            with st.expander(f"Пример {i}: {example['question']}"):
                st.markdown("**Базовый SQL:**")
                st.code(example['sql_basic'], language="sql")
                
                st.markdown("**Оптимизированный SQL:**")
                st.code(example['sql_optimized'], language="sql")
                
                st.markdown(f"**Улучшение:** {example['improvement']}")
    
    with col2:
        st.subheader("⚡ Принципы оптимизации")
        
        optimization_principles = [
            "🎯 **Выбирайте конкретные поля** вместо SELECT *",
            "🔍 **Добавляйте фильтры WHERE** для ограничения данных", 
            "🔗 **Используйте INNER JOIN** вместо JOIN для совпадающих записей",
            "📊 **Применяйте HAVING** для фильтрации агрегированных данных",
            "📈 **Добавляйте ORDER BY** для логичной сортировки результатов",
            "🔢 **Используйте LIMIT** для ограничения количества записей",
            "📅 **Фильтруйте по дате** для актуальных данных",
            "🏷️ **Добавляйте метки** для лучшей читаемости"
        ]
        
        for principle in optimization_principles:
            st.markdown(principle)
        
        st.subheader("📊 Анализ производительности")
        
        if st.button("🔍 Анализировать SQL"):
            st.info("💡 Используйте CLI для анализа производительности:")
            st.code("""
# Анализ производительности SQL
python qa_management_script.py --action performance --input optimized_sql_examples.json

# Обучение на оптимизированных SQL
python qa_management_script.py --action optimize --input optimized_sql_examples.json --output performance_report.json
            """)
    
    st.subheader("🎓 Обучение на оптимизированных SQL")
    
    st.markdown("""
    **Процесс обучения:**
    
    1. **Создание примеров** - базовый SQL vs оптимизированный SQL
    2. **Анализ производительности** - оценка стоимости запросов
    3. **Обучение с контекстом** - передача принципов оптимизации
    4. **Валидация результатов** - проверка качества генерируемого SQL
    """)
    
    if st.button("🚀 Запустить обучение на оптимизации"):
        st.info("💡 Обучение на оптимизированных SQL:")
        st.code("""
# 1. Создание примеров оптимизации
python qa_management_script.py --action template --output optimized_sql_examples.json

# 2. Обучение на оптимизированных SQL
python qa_management_script.py --action optimize --input optimized_sql_examples.json --output performance_report.json

# 3. Анализ результатов
python qa_management_script.py --action performance --input optimized_sql_examples.json
        """)

with tab5:
    st.header("📊 Аналитика качества")
    
    # Метрики качества
    st.subheader("📈 Метрики качества поиска")
    
    # Объяснение метрик
    with st.expander("📚 Что означают метрики P, R, F1?"):
        st.markdown("""
        **Precision (Точность)**: Доля корректных SQL запросов среди всех сгенерированных
        - **Формула**: P = TP / (TP + FP)
        - **Диапазон**: 0.0 - 1.0 (0% - 100%)
        - **Пример**: Если из 10 запросов 8 корректных, то P = 0.8 (80%)
        
        **Recall (Полнота)**: Доля найденных корректных SQL от общего количества возможных
        - **Формула**: R = TP / (TP + FN)  
        - **Диапазон**: 0.0 - 1.0 (0% - 100%)
        - **Пример**: Если из 10 возможных корректных запросов найдено 7, то R = 0.7 (70%)
        
        **F1-Score (Гармоническое среднее)**: Балансированная оценка качества
        - **Формула**: F1 = 2 × (P × R) / (P + R)
        - **Диапазон**: 0.0 - 1.0 (0% - 100%)
        - **Пример**: Если P = 0.8 и R = 0.7, то F1 = 2 × (0.8 × 0.7) / (0.8 + 0.7) = 0.75 (75%)
        
        **Интерпретация**:
        - **0.9 - 1.0**: Отличное качество (90-100%)
        - **0.7 - 0.9**: Хорошее качество (70-90%)
        - **0.5 - 0.7**: Удовлетворительное качество (50-70%)
        - **0.0 - 0.5**: Плохое качество (0-50%)
        """)
    
    # Реальные метрики из бенчмарка
    st.subheader("📊 Реальные метрики из бенчмарка")
    
    # Загружаем результаты бенчмарка
    benchmark_file = "complexity_benchmark_results.json"
    if os.path.exists(benchmark_file):
        with open(benchmark_file, 'r', encoding='utf-8') as f:
            benchmark_data = json.load(f)
        
        complexity_groups = benchmark_data.get('complexity_groups', {})
        
        for group_name, group_data in complexity_groups.items():
            st.write(f"**{group_name}** ({group_data['count']} запросов)")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Precision", f"{group_data['precision']:.3f}")
            with col2:
                st.metric("Recall", f"{group_data['recall']:.3f}")
            
            st.divider()
    else:
        st.info("Запустите бенчмарк для получения реальных метрик")
        if st.button("🚀 Запустить бенчмарк"):
            with st.spinner("Запускаю бенчмарк..."):
                import subprocess
                result = subprocess.run(['python', 'benchmark_by_complexity.py'], 
                                     capture_output=True, text=True)
                if result.returncode == 0:
                    st.success("Бенчмарк завершен! Обновите страницу.")
                else:
                    st.error(f"Ошибка бенчмарка: {result.stderr}")
    
    # Метрики качества агента
    st.subheader("📊 Метрики качества агента")
    
    if st.button("🚀 Вычислить метрики P, R"):
        with st.spinner("Вычисляю метрики для агента..."):
            try:
                # Выбираем по 3 Q/A каждой сложности
                test_data = {
                    "Простые": [
                        {"question": "Покажи всех пользователей", "sql": "SELECT id, login, email, surname, firstname, department FROM equsers WHERE deleted = false"},
                        {"question": "Список отделов", "sql": "SELECT id, departmentname, parentid, description FROM eq_departments WHERE deleted = false"},
                        {"question": "Все клиенты", "sql": "SELECT id, business_unit_name, inn, kpp, ogrn, phone, email FROM tbl_business_unit WHERE deleted = false"}
                    ],
                    "Средние": [
                        {"question": "Пользователи по отделам", "sql": "SELECT u.login, u.email, u.surname, u.firstname, d.departmentname FROM equsers u LEFT JOIN eq_departments d ON u.department = d.id WHERE u.deleted = false"},
                        {"question": "Поручения с клиентами", "sql": "SELECT pa.assignment_number, pa.assignment_date, pa.amount, bu.business_unit_name, bu.inn FROM tbl_principal_assignment pa JOIN tbl_business_unit bu ON pa.business_unit_id = bu.id WHERE pa.deleted = false"},
                        {"question": "Пользователи с ролями", "sql": "SELECT u.login, u.email, r.rolename, r.description FROM equsers u JOIN user_roles ur ON u.id = ur.user_id JOIN eqroles r ON ur.role_id = r.id WHERE u.deleted = false"}
                    ],
                    "Сложные": [
                        {"question": "Платежи по клиентам", "sql": "SELECT bu.business_unit_name, SUM(ip.amount) as total_payments FROM tbl_incoming_payments ip JOIN tbl_business_unit bu ON ip.business_unit_id = bu.id WHERE ip.deleted = false GROUP BY bu.id, bu.business_unit_name ORDER BY total_payments DESC"},
                        {"question": "Количество пользователей по отделам", "sql": "SELECT d.departmentname, COUNT(u.id) as user_count FROM eq_departments d LEFT JOIN equsers u ON d.id = u.department AND u.deleted = false WHERE d.deleted = false GROUP BY d.id, d.departmentname ORDER BY user_count DESC"},
                        {"question": "Сумма платежей по месяцам", "sql": "SELECT DATE_TRUNC('month', payment_date) as month, SUM(amount) as total_amount FROM tbl_incoming_payments WHERE deleted = false GROUP BY DATE_TRUNC('month', payment_date) ORDER BY month DESC"}
                    ]
                }
                
                # Вычисляем метрики для каждой группы
                results = {}
                for complexity, qa_pairs in test_data.items():
                    st.write(f"**{complexity} запросы:**")
                    
                    total_precision = 0
                    total_recall = 0
                    count = 0
                    
                    for qa in qa_pairs:
                        # Генерируем SQL через API
                        response = requests.post(
                            f"{API_BASE_URL}/generate-sql",
                            data={"question": qa["question"]},
                            timeout=30
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            if data.get('success'):
                                generated_sql = data.get('sql', '')
                                
                                # Вычисляем метрики
                                from sql_metrics_calculator import SQLMetricsCalculator
                                calculator = SQLMetricsCalculator()
                                metrics = calculator.calculate_metrics(qa["sql"], generated_sql)
                                
                                precision = metrics['precision']
                                recall = metrics['recall']
                                
                                total_precision += precision
                                total_recall += recall
                                count += 1
                                
                                st.write(f"- {qa['question']}: P={precision:.3f}, R={recall:.3f}")
                    
                    if count > 0:
                        avg_precision = total_precision / count
                        avg_recall = total_recall / count
                        results[complexity] = {
                            "precision": avg_precision,
                            "recall": avg_recall,
                            "count": count
                        }
                        
                        st.success(f"Средние метрики: P={avg_precision:.3f}, R={avg_recall:.3f}")
                        st.divider()
                
                # Показываем итоговые результаты
                st.subheader("📈 Итоговые метрики")
                for complexity, metrics in results.items():
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric(f"{complexity} - Precision", f"{metrics['precision']:.3f}")
                    with col2:
                        st.metric(f"{complexity} - Recall", f"{metrics['recall']:.3f}")
                
                # Сохраняем результаты в файл для автоматического отображения
                benchmark_results = {
                    "complexity_groups": {}
                }
                
                for complexity, metrics in results.items():
                    benchmark_results["complexity_groups"][complexity] = {
                        "precision": metrics['precision'],
                        "recall": metrics['recall'],
                        "count": metrics['count']
                    }
                
                # Сохраняем в файл
                with open("complexity_benchmark_results.json", "w", encoding="utf-8") as f:
                    json.dump(benchmark_results, f, indent=2, ensure_ascii=False)
                
                st.success("✅ Результаты сохранены! Обновите страницу для отображения.")
                
            except Exception as e:
                st.error(f"Ошибка вычисления метрик: {e}")
    
    # Информация о бенчмарке
    st.subheader("ℹ️ О бенчмарке")
    
    st.markdown("""
    **Бенчмарк SQL по сложности** использует реальные Q/A пары из векторки:
    
    - **Простые запросы**: SELECT без JOIN (3 запроса)
    - **Средние запросы**: С JOIN, без агрегации (4 запроса)  
    - **Сложные запросы**: С агрегацией, GROUP BY (3 запроса)
    
    **Метрики**: Precision и Recall по компонентам SQL (таблицы, колонки, условия, JOIN)
    """)

with tab6:
    st.header("⚙️ Настройки")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Параметры поиска")
        
        # Примеры настроек
        config_examples = [
            {"name": "Консервативный", "similarity": 0.8, "context": 2000, "description": "Высокая точность, меньше результатов"},
            {"name": "Сбалансированный", "similarity": 0.7, "context": 4000, "description": "Оптимальный баланс точности и полноты"},
            {"name": "Агрессивный", "similarity": 0.5, "context": 6000, "description": "Больше результатов, может быть шум"},
            {"name": "Быстрый", "similarity": 0.6, "context": 1000, "description": "Быстрый поиск, минимальный контекст"},
            {"name": "Точный", "similarity": 0.9, "context": 3000, "description": "Максимальная точность, меньше ложных срабатываний"}
        ]
        
        # Показываем примеры конфигураций
        st.markdown("**💡 Примеры конфигураций:**")
        selected_config = st.selectbox(
            "Выберите предустановку:",
            ["Выберите конфигурацию..."] + [f"{i+1}. {ex['name']} - {ex['description']}" for i, ex in enumerate(config_examples)],
            key="config_example_selector"
        )
        
        if selected_config != "Выберите конфигурацию...":
            config_idx = int(selected_config.split('.')[0]) - 1
            config = config_examples[config_idx]
            st.session_state.selected_similarity = config['similarity']
            st.session_state.selected_context = config['context']
        
        similarity_threshold = st.slider(
            "Порог схожести:",
            0.0, 1.0, st.session_state.get('selected_similarity', 0.7),
            help="Минимальная схожесть для включения в результаты"
        )
        
        max_context_length = st.number_input(
            "Максимальная длина контекста:",
            min_value=100, max_value=10000, value=st.session_state.get('selected_context', 4000),
            help="Максимальное количество токенов в контексте"
        )
    
    with col2:
        st.subheader("Модель эмбеддингов")
        
        # Примеры моделей с описаниями
        model_examples = [
            {
                "name": "all-MiniLM-L6-v2",
                "description": "Быстрая, компактная модель (384 dim)",
                "speed": "⚡ Быстро",
                "quality": "⭐⭐⭐ Хорошо",
                "size": "22MB"
            },
            {
                "name": "all-mpnet-base-v2", 
                "description": "Высокое качество, медленнее (768 dim)",
                "speed": "🐌 Медленно",
                "quality": "⭐⭐⭐⭐⭐ Отлично",
                "size": "420MB"
            },
            {
                "name": "paraphrase-multilingual-MiniLM-L12-v2",
                "description": "Многоязычная модель (384 dim)",
                "speed": "⚡ Быстро",
                "quality": "⭐⭐⭐⭐ Очень хорошо",
                "size": "118MB"
            },
            {
                "name": "all-distilroberta-v1",
                "description": "Сбалансированная модель (768 dim)",
                "speed": "⚡⚡ Средне",
                "quality": "⭐⭐⭐⭐ Очень хорошо",
                "size": "290MB"
            },
            {
                "name": "all-MiniLM-L12-v2",
                "description": "Улучшенная мини-модель (384 dim)",
                "speed": "⚡ Быстро",
                "quality": "⭐⭐⭐⭐ Очень хорошо",
                "size": "33MB"
            }
        ]
        
        # Показываем примеры моделей
        st.markdown("**💡 Примеры моделей:**")
        selected_model = st.selectbox(
            "Выберите модель:",
            ["Выберите модель..."] + [f"{i+1}. {ex['name']} - {ex['description']}" for i, ex in enumerate(model_examples)],
            key="model_example_selector"
        )
        
        if selected_model != "Выберите модель...":
            model_idx = int(selected_model.split('.')[0]) - 1
            model = model_examples[model_idx]
            st.session_state.selected_model = f"sentence-transformers/{model['name']}"
            st.info(f"**{model['speed']}** | **{model['quality']}** | **{model['size']}**")
        
        embedding_model = st.selectbox(
            "Модель:",
            [
                "sentence-transformers/all-MiniLM-L6-v2",
                "sentence-transformers/all-mpnet-base-v2", 
                "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                "sentence-transformers/all-distilroberta-v1",
                "sentence-transformers/all-MiniLM-L12-v2"
            ],
            index=0 if not st.session_state.get('selected_model') else [
                "sentence-transformers/all-MiniLM-L6-v2",
                "sentence-transformers/all-mpnet-base-v2", 
                "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                "sentence-transformers/all-distilroberta-v1",
                "sentence-transformers/all-MiniLM-L12-v2"
            ].index(st.session_state.get('selected_model', "sentence-transformers/all-MiniLM-L6-v2")),
            help="Выберите модель для генерации эмбеддингов"
        )
        
        # Примеры размеров батча
        batch_examples = [
            {"size": 50, "description": "Малый - для тестирования"},
            {"size": 200, "description": "Средний - оптимальный"},
            {"size": 500, "description": "Большой - для больших объемов"},
            {"size": 1000, "description": "Максимальный - для серверов"}
        ]
        
        st.markdown("**💡 Примеры размеров батча:**")
        selected_batch = st.selectbox(
            "Выберите размер батча:",
            ["Выберите размер..."] + [f"{ex['size']} - {ex['description']}" for ex in batch_examples],
            key="batch_example_selector"
        )
        
        if selected_batch != "Выберите размер...":
            batch_size = int(selected_batch.split(' - ')[0])
            st.session_state.selected_batch = batch_size
        
        batch_size = st.number_input(
            "Размер батча:",
            min_value=1, max_value=1000, value=st.session_state.get('selected_batch', 200),
            help="Размер батча для генерации эмбеддингов"
        )
    
    # Сохранение настроек
    if st.button("💾 Сохранить настройки"):
        settings = {
            'similarity_threshold': similarity_threshold,
            'max_context_length': max_context_length,
            'embedding_model': embedding_model,
            'batch_size': batch_size
        }
        
        with open('vector_kb_settings.json', 'w') as f:
            json.dump(settings, f, indent=2)
        
        st.success("Настройки сохранены!")

# Боковая панель с быстрыми действиями
with st.sidebar:
    st.header("🚀 Быстрые действия")
    
    # Статус API
    st.subheader("📡 Статус API")
    if test_api_connection():
        st.success("✅ FastAPI (3000) - Работает")
    else:
        st.error("❌ FastAPI (3000) - Недоступен")
        st.warning("Убедитесь, что сервис запущен: python src/simple_web_interface.py")
    
    if st.button("🔄 Перезагрузить векторку"):
        st.info("Перезагрузка векторки...")
    
    if st.button("🧹 Очистить кэш"):
        st.cache_resource.clear()
        st.info("Кэш очищен!")
    
    if st.button("📊 Полный анализ"):
        st.info("Запуск полного анализа...")
    
    st.header("📁 Файлы")
    
    # Ссылки на важные файлы
    st.markdown("""
    **📚 Документация проекта:**
    
    - [Training Guide](https://github.com/kobyzev-yuri/NLSQL/blob/main/docs/VANNA_TRAINING_GUIDE.md) - руководство по обучению
    - [QA Expansion](https://github.com/kobyzev-yuri/NLSQL/blob/main/docs/customer_requests/CUSTOMER_QA_EXPANSION_REQUEST.md) - план расширения Q/A
    - [RAG Checklist](https://github.com/kobyzev-yuri/NLSQL/blob/main/RAG_IMPROVEMENT_CHECKLIST.md) - чеклист улучшений RAG
    - [Vector KB Plan](https://github.com/kobyzev-yuri/NLSQL/blob/main/VECTOR_KB_IMPROVEMENT_PLAN.md) - план улучшения векторки
    - [Services Guide](https://github.com/kobyzev-yuri/NLSQL/blob/main/docs/SERVICES_STARTUP_GUIDE.md) - руководство по сервисам
    
    **💡 Подсказка:** Документы находятся в корне проекта. 
    
    **Доступ через терминал:**
    ```bash
    # Открыть в редакторе
    code docs/VANNA_TRAINING_GUIDE.md
    code VECTOR_KB_IMPROVEMENT_PLAN.md
    
    # Просмотр в терминале
    cat docs/VANNA_TRAINING_GUIDE.md
    less VECTOR_KB_IMPROVEMENT_PLAN.md
    ```
    
    **🌐 GitHub репозиторий:**
    - [kobyzev-yuri/NLSQL](https://github.com/kobyzev-yuri/NLSQL) - основной репозиторий
    - Или используйте локальные ссылки выше
    """)

# Футер
st.markdown("---")
st.markdown("**Vector KB Interface** - Интерфейс для работы с векторной базой знаний")
