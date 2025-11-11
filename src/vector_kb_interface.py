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
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import asyncpg

# Load environment variables from config.env
from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / "config.env", override=True)

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
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")  # Core API port

def test_api_connection():
    """Проверка подключения к FastAPI"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get("status") == "healthy"
        return False
    except:
        return False

@st.cache_data(ttl=300)  # Кэш на 5 минут
def get_documentation_from_db():
    """Загрузка реальных документов из базы данных"""
    try:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            return []
        
        # Используем простой подход с созданием нового event loop
        import asyncio
        
        async def fetch_docs():
            conn = await asyncpg.connect(database_url)
            try:
                rows = await conn.fetch("""
                    SELECT id, content, created_at 
                    FROM vanna_vectors 
                    WHERE content_type = 'documentation' 
                    ORDER BY created_at DESC 
                    LIMIT 50
                """)
                return [{"id": r["id"], "content": r["content"], "created_at": str(r["created_at"])} for r in rows]
            finally:
                await conn.close()
        
        # Создаем новый event loop для Streamlit
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            docs = loop.run_until_complete(fetch_docs())
            loop.close()
            return docs
        except Exception as loop_error:
            # Если не удалось через async, возвращаем пустой список
            return []
    except Exception as e:
        # Если не удалось загрузить из БД, возвращаем пустой список
        return []

@st.cache_data(ttl=300)  # Кэш на 5 минут
def get_ddl_from_db():
    """Загрузка реальных DDL из базы данных с фильтрацией тестовых таблиц"""
    try:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            return []
        
        import asyncio
        import re as regex_module
        
        # Список паттернов для исключения тестовых/временных таблиц
        exclude_patterns = [
            r'^temp$',
            r'^test_',
            r'^tmp_',
            r'^temp_',
            r'_test$',
            r'_temp$',
            r'^public\.temp',
            r'^public\.test_',
            r'^public\.tmp_',
        ]
        
        async def fetch_ddl():
            conn = await asyncpg.connect(database_url)
            try:
                rows = await conn.fetch("""
                    SELECT id, content, metadata, created_at 
                    FROM vanna_vectors 
                    WHERE content_type = 'ddl' 
                    ORDER BY created_at DESC 
                    LIMIT 200
                """)
                result = []
                for r in rows:
                    # Извлекаем имя таблицы из DDL или metadata
                    table_name = None
                    if r["metadata"]:
                        table_name = r["metadata"].get("table_name") if isinstance(r["metadata"], dict) else None
                    
                    # Если нет в metadata, пытаемся извлечь из content
                    if not table_name:
                        content = r["content"]
                        # Ищем CREATE TABLE table_name (может быть с schema)
                        match = regex_module.search(
                            r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:([^\s.]+)\.)?([^\s(]+)',
                            content,
                            regex_module.IGNORECASE
                        )
                        if match:
                            schema = match.group(1)
                            table = match.group(2)
                            if schema:
                                table_name = f"{schema}.{table}"
                            else:
                                table_name = table
                    
                    if not table_name:
                        table_name = "Unknown"
                    
                    # Фильтруем тестовые/временные таблицы
                    should_exclude = False
                    for pattern in exclude_patterns:
                        if regex_module.match(pattern, table_name, regex_module.IGNORECASE):
                            should_exclude = True
                            break
                    
                    if should_exclude:
                        continue  # Пропускаем тестовые таблицы
                    
                    result.append({
                        "id": r["id"],
                        "content": r["content"],
                        "table_name": table_name,
                        "created_at": str(r["created_at"])
                    })
                return result
            finally:
                await conn.close()
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            ddl_list = loop.run_until_complete(fetch_ddl())
            loop.close()
            return ddl_list
        except Exception as loop_error:
            return []
    except Exception as e:
        return []

def call_api_search(question: str, search_type: str = "semantic", limit: int = 5):
    """Вызов API для тестирования поиска через /test-search"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/test-search",
            json={
                "question": question,
                "search_type": search_type,
                "limit": limit
            },
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            # /test-search возвращает результаты поиска с чанками
            if data.get('success') is True:
                return {
                    "success": True,
                    "question": question,
                    "search_type": search_type,
                    "results": data.get('results', []),
                    "total_found": data.get('total_found', len(data.get('results', [])))
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
            f"{API_BASE_URL}/query",
            json={
                "question": question,
                "user_id": "kb_test_user",
                "role": "admin",
                "department": "IT",
                "context": {}
            },
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP {response.status_code}", "details": response.text}
    except Exception as e:
        return {"error": str(e)}

def call_api_execute_sql(sql: str):
    """Вызов Mock Customer API для выполнения SQL напрямую"""
    try:
        import uuid
        # Используем Mock API напрямую для выполнения SQL
        mock_api_url = os.getenv('MOCK_API_URL', 'http://localhost:8081')
        response = requests.post(
            f"{mock_api_url}/api/sql/execute",
            json={
                "sql_template": sql,
                "user_context": {
                    "user_id": "kb_test_user",
                    "login": "kb_test_user",
                    "role": "admin",
                    "department": "IT"
                },
                "request_id": str(uuid.uuid4())
            },
            timeout=60
        )
        if response.status_code == 200:
            data = response.json()
            # Mock API возвращает результат напрямую, не в формате {success: 1}
            if 'data' in data or 'columns' in data:
                return {
                    "success": True,
                    "data": data.get('data', []),
                    "columns": data.get('columns', []),
                    "row_count": data.get('row_count', len(data.get('data', []))),
                    "execution_time": data.get('execution_time', 0.0),
                    "sql": data.get('final_sql', data.get('sql', sql))
                }
            elif data.get('success') == 1:
                return {
                    "success": True,
                    "data": data.get('data', []),
                    "columns": data.get('columns', []),
                    "row_count": len(data.get('data', [])),
                    "execution_time": data.get('execution_time', 0.0),
                    "sql": data.get('final_sql', sql)
                }
            else:
                return {"success": False, "error": data.get('errormsg', data.get('detail', 'Ошибка выполнения SQL'))}
        else:
            error_text = response.text
            try:
                error_json = response.json()
                error_msg = error_json.get('detail', error_json.get('message', error_text))
            except:
                error_msg = error_text
            return {"success": False, "error": f"HTTP {response.status_code}: {error_msg}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# Функции для работы с комментариями БД
def call_api_get_tables_with_comments():
    """Получить список таблиц с комментариями"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/database/tables", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP {response.status_code}", "details": response.text}
    except Exception as e:
        return {"error": str(e)}

def call_api_get_table_columns(table_name: str):
    """Получить список колонок таблицы с комментариями"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/database/tables/{table_name}/columns", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP {response.status_code}", "details": response.text}
    except Exception as e:
        return {"error": str(e)}

def call_api_add_table_comment(table_name: str, comment: str):
    """Добавить COMMENT ON TABLE"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/database/tables/{table_name}/comment",
            json={"comment": comment},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        else:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {"detail": response.text}
            return {"success": False, "error": error_data.get('detail', f"HTTP {response.status_code}")}
    except Exception as e:
        return {"success": False, "error": str(e)}

def call_api_add_column_comment(table_name: str, column_name: str, comment: str):
    """Добавить COMMENT ON COLUMN"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/database/tables/{table_name}/columns/{column_name}/comment",
            json={"comment": comment},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        else:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {"detail": response.text}
            return {"success": False, "error": error_data.get('detail', f"HTTP {response.status_code}")}
    except Exception as e:
        return {"success": False, "error": str(e)}

def call_api_get_comments_stats():
    """Получить статистику по комментариям"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/database/comments/stats", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP {response.status_code}", "details": response.text}
    except Exception as e:
        return {"error": str(e)}

# Основные вкладки
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "🔍 Тестирование поиска", 
    "📝 Добавление Q/A", 
    "🎓 Обучение", 
    "🚀 Оптимизация SQL",
    "📊 Аналитика", 
    "⚙️ Настройки",
    "📝 Документирование БД"
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
        
        max_results = st.slider(
            "Максимум результатов:", 
            1, 20, 5,
            help="Количество чанков для отображения (1-20)"
        )
        
        st.caption(f"📊 Будет возвращено до {max_results} наиболее релевантных чанков")
    
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
    
    # Инициализация session_state если нужно
    if 'search_results' not in st.session_state:
        st.session_state.search_results = []
    if 'search_query' not in st.session_state:
        st.session_state.search_query = ''
    if 'search_type' not in st.session_state:
        st.session_state.search_type = 'semantic'
    
    if st.button("🔍 Тестировать поиск", type="primary"):
        if query:
            # Проверяем подключение к API
            if not test_api_connection():
                st.error(f"❌ Core API недоступен на {API_BASE_URL}. Убедитесь, что сервис запущен.")
                st.stop()
            
            with st.spinner("Выполняю поиск через FastAPI..."):
                try:
                    # Вызываем API для поиска
                    search_result = call_api_search(query, search_type, max_results)
                    
                    if "error" in search_result:
                        st.error(f"Ошибка API: {search_result['error']}")
                        st.stop()
                    
                    results = search_result.get('results', [])
                    # Сохраняем результаты в session_state ПЕРЕД любыми другими операциями
                    st.session_state.search_results = results
                    st.session_state.search_query = query
                    st.session_state.search_type = search_type
                    
                    if len(results) == 0:
                        st.warning(f"⚠️ Результаты не найдены для запроса: '{query}' (тип: {search_type})")
                        st.info("💡 Возможные причины:")
                        st.info("   - Векторная база знаний пуста (не проведено обучение)")
                        st.info("   - Семантический RAG не инициализирован")
                        st.info("   - Запрос не соответствует ни одному чанку в базе")
                        st.info("   - Попробуйте другой тип поиска (ddl, documentation, examples)")
                        st.session_state.search_results = []  # Очищаем результаты
                    else:
                        st.success(f"✅ Найдено {len(results)} результатов")
                        # Перезагружаем страницу для отображения результатов
                        st.rerun()
                    
                except Exception as e:
                    st.error(f"Ошибка поиска: {e}")
                    st.session_state.search_results = []
    
    # Показываем сохраненные результаты поиска (из нового поиска или из session_state)
    # ВАЖНО: этот блок должен быть ВНЕ блока кнопки поиска, чтобы результаты не терялись
    display_results = st.session_state.get('search_results', [])
    display_query = st.session_state.get('search_query', '')
    display_search_type = st.session_state.get('search_type', 'semantic')
    
    if display_results:
        # Отображаем результаты с метаданными чанков
        st.divider()
        st.markdown(f"**📋 Результаты поиска для: '{display_query}'** (тип: {display_search_type})")
        
        for i, result in enumerate(display_results[:max_results]):
            if isinstance(result, dict):
                content = result.get('content', result.get('ddl', result.get('documentation', result.get('question', str(result)))))
                content_type = result.get('content_type', result.get('type', display_search_type))
                score = result.get('score', result.get('distance'))
                rank = result.get('rank', i + 1)
                metadata = result.get('metadata', {})
                
                # Формируем заголовок с информацией о чанке
                title_parts = [f"Результат {rank}"]
                if content_type and content_type != 'unknown':
                    title_parts.append(f"📋 {content_type}")
                if score is not None:
                    if isinstance(score, float):
                        title_parts.append(f"⭐ {score:.4f}")
                    else:
                        title_parts.append(f"⭐ {score}")
                
                with st.expander(" | ".join(title_parts)):
                    # Показываем метаданные
                    col1, col2 = st.columns(2)
                    with col1:
                        if content_type and content_type != 'unknown':
                            st.markdown(f"**Тип:** `{content_type}`")
                        if metadata:
                            if 'table' in metadata:
                                st.markdown(f"**Таблица:** `{metadata.get('table')}`")
                            if 'column' in metadata:
                                st.markdown(f"**Колонка:** `{metadata.get('column')}`")
                    with col2:
                        if score is not None:
                            if isinstance(score, float):
                                score_str = f"{score:.4f}"
                            else:
                                score_str = str(score)
                            st.markdown(f"**Релевантность:** `{score_str}`")
                        if metadata:
                            if 'source' in metadata:
                                st.markdown(f"**Источник:** `{metadata.get('source')}`")
                    
                    # Показываем содержимое чанка
                    st.markdown("**Содержимое чанка:**")
                    if content_type in ['ddl', 'DDL'] or 'DDL' in str(content):
                        st.code(content, language="sql")
                    elif content_type in ['documentation', 'doc']:
                        st.markdown(content)
                    elif content_type in ['question_sql', 'examples', 'qa']:
                        # Для Q/A пар показываем вопрос и SQL
                        if isinstance(result, dict) and 'question' in result and 'sql' in result:
                            st.markdown(f"**Вопрос:** {result.get('question')}")
                            st.code(result.get('sql', content), language="sql")
                        else:
                            st.code(content, language="sql")
                    else:
                        # По умолчанию показываем как SQL
                        st.code(content, language="sql")
                    
                    # Дополнительные метаданные
                    if metadata and len(metadata) > 2:
                        with st.expander("📋 Все метаданные"):
                            st.json(metadata)
            else:
                # Fallback для не-словарей (строки)
                with st.expander(f"Результат {i+1} | 📋 {display_search_type}"):
                    st.markdown(f"**Тип:** `{display_search_type}`")
                    st.markdown("**Содержимое чанка:**")
                    # Определяем язык по типу поиска
                    if display_search_type in ['ddl', 'semantic']:
                        st.code(str(result), language="sql")
                    elif display_search_type == 'documentation':
                        st.markdown(str(result))
                    else:
                        st.code(str(result), language="sql")
        
        # После отображения результатов - предлагаем сгенерировать SQL
        st.divider()
        st.subheader("🚀 Генерация SQL на основе найденных чанков")
        
        col_gen, col_exec = st.columns(2)
        
        with col_gen:
            if st.button("📝 Сгенерировать SQL", type="primary", key="generate_sql_btn"):
                # Сохраняем результаты поиска перед генерацией
                st.session_state.search_results = display_results
                st.session_state.search_query = display_query
                st.session_state.search_type = display_search_type
                
                with st.spinner("Генерирую SQL запрос..."):
                    try:
                        sql_result = call_api_generate_sql(display_query)
                        if sql_result and sql_result.get('sql'):
                            st.session_state.generated_sql = sql_result['sql']
                            st.session_state.show_sql = True
                            st.rerun()  # Перезагружаем для отображения SQL
                        else:
                            st.error(f"Ошибка генерации SQL: {sql_result.get('error', 'Неизвестная ошибка')}")
                    except Exception as e:
                        st.error(f"Ошибка: {e}")
        
        with col_exec:
            if st.session_state.get('generated_sql'):
                if st.button("▶️ Выполнить SQL", key="execute_sql_btn"):
                    # Сохраняем результаты поиска перед выполнением
                    st.session_state.search_results = display_results
                    st.session_state.search_query = display_query
                    st.session_state.search_type = display_search_type
                    
                    with st.spinner("Выполняю SQL запрос..."):
                        try:
                            execute_result = call_api_execute_sql(st.session_state.generated_sql)
                            if execute_result and execute_result.get('success'):
                                st.session_state.sql_execution_result = execute_result
                                st.session_state.show_execution = True
                                st.rerun()  # Перезагружаем для отображения результатов
                            else:
                                st.error(f"Ошибка выполнения: {execute_result.get('error', 'Неизвестная ошибка')}")
                        except Exception as e:
                            st.error(f"Ошибка: {e}")
        
        # Показываем сгенерированный SQL (без перезагрузки страницы)
        if st.session_state.get('show_sql') and st.session_state.get('generated_sql'):
            st.markdown("**📝 Сгенерированный SQL:**")
            st.code(st.session_state.generated_sql, language="sql")
            
            # Показываем результаты выполнения
            if st.session_state.get('show_execution') and st.session_state.get('sql_execution_result'):
                exec_result = st.session_state.sql_execution_result
                st.markdown("**📊 Результаты выполнения:**")
                
                if exec_result.get('data') and len(exec_result.get('data', [])) > 0:
                    # Преобразуем данные в DataFrame для лучшего отображения
                    columns = exec_result.get('columns', [])
                    data = exec_result.get('data', [])
                    
                    if columns and data:
                        # Если есть названия колонок, используем их
                        if isinstance(data[0], dict):
                            df = pd.DataFrame(data)
                        elif isinstance(data[0], list):
                            df = pd.DataFrame(data, columns=columns)
                        else:
                            df = pd.DataFrame(data)
                        
                        st.dataframe(df, use_container_width=True, height=400)
                        st.success(f"✅ Найдено строк: {exec_result.get('row_count', len(data))} | Время выполнения: {exec_result.get('execution_time', 0):.3f}с")
                    else:
                        st.dataframe(data, use_container_width=True)
                        st.success(f"✅ Найдено строк: {len(data)}")
                else:
                    st.info("ℹ️ Запрос выполнен успешно, но результатов нет")

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
                    st.error(f"❌ Core API недоступен на {API_BASE_URL}. Убедитесь, что сервис запущен.")
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
        
        # Формат JSON файла
        with st.expander("📋 Формат JSON файла", expanded=False):
            st.markdown("""
            **Формат:** Массив объектов с полями `question` и `sql`
            
            **Пример файла `qa_pairs.json`:**
            ```json
            [
                {
                    "question": "Покажи всех пользователей системы",
                    "sql": "SELECT id, login, email, surname, firstname, department FROM equsers WHERE deleted = FALSE"
                },
                {
                    "question": "Список всех клиентов с их контактами",
                    "sql": "SELECT id, business_unit_name, inn, kpp, ogrn, phone, email FROM tbl_business_unit WHERE deleted = FALSE"
                },
                {
                    "question": "Пользователи отдела Продажи за последний месяц",
                    "sql": "SELECT u.login, u.email, u.surname, u.firstname FROM equsers u JOIN eq_departments d ON u.department = d.id WHERE d.name = 'Продажи' AND u.created_at >= CURRENT_DATE - INTERVAL '1 month'"
                }
            ]
            ```
            
            **Обязательные поля:**
            - `question` (string) - вопрос на естественном языке
            - `sql` (string) - SQL запрос для ответа на вопрос (оптимизированный вариант)
            
            **Опциональные поля:**
            - `sql_basic` (string) - базовый (неоптимизированный) SQL для сравнения
            - `sql_optimized` (string) - оптимизированный SQL (альтернатива `sql` для пар SQL/SQL optimized)
            - `improvement` (string) - описание улучшения производительности
            - `domain` (string) - домен вопроса (users, payments, assignments, etc.)
            - `tags` (array) - список тегов для категоризации
            
            **Пример с SQL optimized (для скрипта optimize):**
            ```json
            {
                "question": "Покажи всех пользователей",
                "sql_basic": "SELECT * FROM equsers",
                "sql_optimized": "SELECT id, login, email FROM equsers WHERE deleted = FALSE",
                "improvement": "50% меньше данных, быстрее выполнение"
            }
            ```
            
            **Примечание:** Для обучения на оптимизированных SQL используйте формат с `sql_basic` и `sql_optimized`.
            Для массового добавления как Q/A пары используйте `sql` (оптимизированный) и опционально `sql_basic` для сравнения.
            """)
        
        # Загрузка файла
        uploaded_file = st.file_uploader(
            "Загрузите JSON файл с Q/A парами:",
            type=['json'],
            help="Формат: массив объектов [{'question': '...', 'sql': '...'}, ...]"
        )
        
        if uploaded_file:
            try:
                data = json.load(uploaded_file)
                
                # Валидация формата
                if not isinstance(data, list):
                    st.error("❌ Ошибка: JSON должен быть массивом объектов")
                    st.code('{"error": "Ожидается массив: [...]"}')
                    st.stop()
                
                # Проверка структуры каждой пары
                valid_pairs = []
                invalid_pairs = []
                for i, pair in enumerate(data):
                    if not isinstance(pair, dict):
                        invalid_pairs.append(f"Пара #{i+1}: не является объектом")
                        continue
                    
                    # Проверяем наличие question и sql (или sql_optimized)
                    if "question" not in pair:
                        invalid_pairs.append(f"Пара #{i+1}: отсутствует поле 'question'")
                        continue
                    
                    # SQL может быть в поле 'sql' или 'sql_optimized'
                    sql_value = pair.get("sql") or pair.get("sql_optimized")
                    if not sql_value:
                        invalid_pairs.append(f"Пара #{i+1}: отсутствует поле 'sql' или 'sql_optimized'")
                        continue
                    
                    if not isinstance(pair["question"], str) or not pair["question"].strip():
                        invalid_pairs.append(f"Пара #{i+1}: поле 'question' должно быть непустой строкой")
                        continue
                    
                    if not isinstance(sql_value, str) or not sql_value.strip():
                        invalid_pairs.append(f"Пара #{i+1}: поле 'sql'/'sql_optimized' должно быть непустой строкой")
                        continue
                    
                    # Нормализуем: если есть sql_optimized, но нет sql, используем sql_optimized как sql
                    normalized_pair = pair.copy()
                    if "sql_optimized" in normalized_pair and "sql" not in normalized_pair:
                        normalized_pair["sql"] = normalized_pair["sql_optimized"]
                    
                    # Для оптимизированных SQL: если есть sql_basic, это оптимизированный SQL
                    if normalized_pair.get("sql_basic") or normalized_pair.get("sql_optimized"):
                        # Убедимся, что sql_optimized установлен
                        if "sql_optimized" not in normalized_pair:
                            normalized_pair["sql_optimized"] = normalized_pair["sql"]
                    
                    valid_pairs.append(normalized_pair)
                
                # Отображение результатов валидации
                if invalid_pairs:
                    st.warning(f"⚠️ Найдено {len(invalid_pairs)} невалидных пар:")
                    for error in invalid_pairs:
                        st.text(f"  • {error}")
                
                if valid_pairs:
                    st.success(f"✅ Валидных Q/A пар: {len(valid_pairs)}")
                    
                    # Показываем примеры валидных пар
                    with st.expander(f"📖 Просмотр валидных пар (первые 3 из {len(valid_pairs)})"):
                        for i, pair in enumerate(valid_pairs[:3], 1):
                            st.markdown(f"**Пара #{i}:**")
                            st.code(f"Q: {pair['question']}\nA: {pair['sql']}", language="sql")
                            # Если есть sql_basic, показываем его для сравнения
                            if pair.get('sql_basic'):
                                st.markdown("*Базовый SQL (для сравнения):*")
                                st.code(pair['sql_basic'], language="sql")
                            if pair.get('improvement'):
                                st.info(f"💡 Улучшение: {pair['improvement']}")
                    
                    if st.button("📥 Импортировать валидные пары", type="primary"):
                        # Проверяем подключение к API
                        if not test_api_connection():
                            st.error(f"❌ Core API недоступен на {API_BASE_URL}. Убедитесь, что сервис запущен.")
                            st.stop()
                        
                        with st.spinner(f"Импортирую {len(valid_pairs)} Q/A пар..."):
                            # Пока что используем CLI скрипт, так как API для массового добавления еще не реализован
                            st.info("⚠️ Массовое добавление Q/A пар через интерфейс пока не поддерживается. Используйте CLI скрипт:")
                            
                            # Сохраняем валидные пары во временный файл
                            import tempfile
                            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as tmp_file:
                                json.dump(valid_pairs, tmp_file, ensure_ascii=False, indent=2)
                                tmp_path = tmp_file.name
                            
                            st.code(f"python qa_management_script.py --action add --input {tmp_path} --validate")
                            st.info(f"💾 Валидные пары сохранены во временный файл: {tmp_path}")
                            st.success(f"✅ Готово к импорту {len(valid_pairs)} Q/A пар!")
                            
                            # В будущем здесь будет вызов API для массового добавления
                            # api_result = call_api_bulk_add_qa(valid_pairs)
                else:
                    st.error("❌ Нет валидных Q/A пар для импорта")
                    
            except json.JSONDecodeError as e:
                st.error(f"❌ Ошибка парсинга JSON: {e}")
                st.code(f"Позиция ошибки: строка {e.lineno}, колонка {e.colno}")
            except Exception as e:
                st.error(f"❌ Ошибка загрузки файла: {e}")
                import traceback
                with st.expander("Детали ошибки"):
                    st.code(traceback.format_exc())

with tab3:
    st.header("🎓 Обучение на новых данных")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Обучение на DDL")
        
        # Загружаем реальные DDL из базы данных
        db_ddl = get_ddl_from_db()
        
        # Примеры-шаблоны для новых DDL (если в БД нет DDL)
        ddl_templates = [
            "CREATE TABLE equsers (id SERIAL PRIMARY KEY, login VARCHAR(50), email VARCHAR(100), department VARCHAR(50), deleted BOOLEAN DEFAULT FALSE);",
            "CREATE TABLE tbl_principal_assignment (id SERIAL PRIMARY KEY, assignment_number VARCHAR(20), amount DECIMAL(15,2), business_unit_id INTEGER, creationdatetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP);",
            "CREATE TABLE tbl_business_unit (id SERIAL PRIMARY KEY, business_unit_name VARCHAR(200), inn VARCHAR(12), phone VARCHAR(20));",
            "CREATE TABLE eq_departments (id SERIAL PRIMARY KEY, name VARCHAR(100), code VARCHAR(20), deleted BOOLEAN DEFAULT FALSE);",
            "CREATE TABLE tbl_incoming_payments (id SERIAL PRIMARY KEY, amount DECIMAL(15,2), payment_date DATE, user_id INTEGER, business_unit_id INTEGER);"
        ]
        
        # Формируем список для выбора
        if db_ddl:
            st.markdown(f"**📚 Уже обученные DDL из БД ({len(db_ddl)}):**")
            
            # Группируем по таблицам для удобства
            ddl_options = ["Выберите DDL..."] + [
                f"📄 {ddl['table_name']} (ID {ddl['id']})" 
                for ddl in db_ddl
            ]
            
            selected_ddl = st.selectbox(
                "Выберите DDL для редактирования или как шаблон:",
                ddl_options,
                key="ddl_db_selector"
            )
            
            if selected_ddl != "Выберите DDL...":
                # Найти выбранный DDL
                ddl_id = int(selected_ddl.split("ID ")[1].split(")")[0])
                selected_ddl_data = next((d for d in db_ddl if d["id"] == ddl_id), None)
                if selected_ddl_data:
                    st.session_state.selected_ddl = selected_ddl_data["content"]
                    st.info(f"📅 Создан: {selected_ddl_data['created_at']} | Таблица: {selected_ddl_data['table_name']}")
            
            st.markdown("---")
            st.markdown("**💡 Или используйте шаблоны для новых DDL:**")
            template_options = ["Выберите шаблон..."] + [
                f"{i+1}. {ex.split('(')[0].split()[-1] if '(' in ex else ex.split()[2]}" 
                for i, ex in enumerate(ddl_templates)
            ]
            selected_template = st.selectbox(
                "Шаблоны DDL:",
                template_options,
                key="ddl_template_selector"
            )
            
            if selected_template != "Выберите шаблон...":
                ddl_idx = int(selected_template.split('.')[0]) - 1
                st.session_state.selected_ddl = ddl_templates[ddl_idx]
        else:
            st.markdown("**💡 Примеры-шаблоны DDL (в БД пока нет DDL):**")
            selected_ddl = st.selectbox(
                "Выберите шаблон:",
                ["Выберите шаблон..."] + [f"{i+1}. {ex.split('(')[0].split()[-1]}" for i, ex in enumerate(ddl_templates)],
                key="ddl_example_selector"
            )
            
            if selected_ddl != "Выберите шаблон...":
                ddl_idx = int(selected_ddl.split('.')[0]) - 1
                st.session_state.selected_ddl = ddl_templates[ddl_idx]
        
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
                    st.error(f"❌ Core API недоступен на {API_BASE_URL}. Убедитесь, что сервис запущен.")
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
        
        # Загружаем реальные документы из базы данных
        db_docs = get_documentation_from_db()
        
        # Примеры-шаблоны для новых документов (если в БД нет документов)
        doc_templates = [
            "Система управления документами DocStructureSchema содержит 12 основных таблиц. Пользователи (equsers) принадлежат к отделам (eq_departments) и имеют ролевые ограничения.",
            "Поручения (tbl_principal_assignment) создаются для бизнес-единиц (tbl_business_unit) и привязаны к пользователям. Платежи (tbl_incoming_payments) связаны с поручениями и клиентами.",
            "Ролевая модель: admin - полный доступ, manager - данные своего отдела, user - только свои данные. Ограничения применяются на уровне SQL запросов.",
            "Бизнес-логика: поручения создаются на основе платежей, пользователи работают в рамках своих отделов, клиенты имеют уникальные ИНН и контактные данные.",
            "Архитектура: PostgreSQL с Row Level Security, векторная база pgvector для семантического поиска, API на FastAPI с поддержкой ролевых ограничений."
        ]
        
        # Формируем список для выбора
        if db_docs:
            st.markdown(f"**📚 Уже обученные документы из БД ({len(db_docs)}):**")
            doc_options = ["Выберите документ..."] + [
                f"📄 ID {doc['id']}: {doc['content'][:60]}..." 
                for doc in db_docs
            ]
            
            selected_doc = st.selectbox(
                "Выберите документ для редактирования или как шаблон:",
                doc_options,
                key="doc_db_selector"
            )
            
            if selected_doc != "Выберите документ...":
                # Найти выбранный документ
                doc_id = int(selected_doc.split("ID ")[1].split(":")[0])
                selected_doc_data = next((d for d in db_docs if d["id"] == doc_id), None)
                if selected_doc_data:
                    st.session_state.selected_doc = selected_doc_data["content"]
                    st.info(f"📅 Создан: {selected_doc_data['created_at']}")
            
            st.markdown("---")
            st.markdown("**💡 Или используйте шаблоны для новых документов:**")
            template_options = ["Выберите шаблон..."] + [f"{i+1}. {ex[:50]}..." for i, ex in enumerate(doc_templates)]
            selected_template = st.selectbox(
                "Шаблоны:",
                template_options,
                key="doc_template_selector"
            )
            
            if selected_template != "Выберите шаблон...":
                doc_idx = int(selected_template.split('.')[0]) - 1
                st.session_state.selected_doc = doc_templates[doc_idx]
        else:
            st.markdown("**💡 Примеры-шаблоны документации (в БД пока нет документов):**")
            selected_doc = st.selectbox(
                "Выберите шаблон:",
                ["Выберите шаблон..."] + [f"{i+1}. {ex[:50]}..." for i, ex in enumerate(doc_templates)],
                key="doc_template_selector"
            )
            
            if selected_doc != "Выберите шаблон...":
                doc_idx = int(selected_doc.split('.')[0]) - 1
                st.session_state.selected_doc = doc_templates[doc_idx]
        
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
                    st.error(f"❌ Core API недоступен на {API_BASE_URL}. Убедитесь, что сервис запущен.")
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
        st.subheader("➕ Добавление пары SQL/SQL optimized")
        
        question_opt = st.text_input(
            "Вопрос:",
            placeholder="Покажи всех пользователей",
            key="opt_question"
        )
        
        sql_basic_opt = st.text_area(
            "Базовый SQL (неоптимизированный):",
            height=100,
            placeholder="SELECT * FROM equsers",
            key="opt_sql_basic"
        )
        
        sql_optimized_opt = st.text_area(
            "Оптимизированный SQL:",
            height=100,
            placeholder="SELECT id, login, email, department FROM equsers WHERE deleted = FALSE",
            key="opt_sql_optimized"
        )
        
        improvement_opt = st.text_input(
            "Описание улучшения (опционально):",
            placeholder="50% меньше данных, быстрее выполнение",
            key="opt_improvement"
        )
        
        col_add_json, col_add_db = st.columns([1, 1])
        
        with col_add_json:
            if st.button("➕ Добавить в JSON (для скачивания)"):
                if question_opt and sql_basic_opt and sql_optimized_opt:
                    # Формируем JSON в формате optimized_sql_examples.json
                    pair_data = {
                        "question": question_opt.strip(),
                        "sql_basic": sql_basic_opt.strip(),
                        "sql_optimized": sql_optimized_opt.strip(),
                        "improvement": improvement_opt.strip() if improvement_opt else ""
                    }
                    
                    st.success("✅ Пара сформирована!")
                    st.code(json.dumps(pair_data, ensure_ascii=False, indent=2), language="json")
                    
                    # Добавляем в сессию для возможности сохранения
                    if "optimized_pairs" not in st.session_state:
                        st.session_state.optimized_pairs = []
                    st.session_state.optimized_pairs.append(pair_data)
                    
                    st.info(f"💡 Пара сохранена в сессии. Всего пар: {len(st.session_state.optimized_pairs)}")
                    st.info("💡 Формат соответствует optimized_sql_examples.json для скрипта optimize")
                else:
                    st.warning("Заполните вопрос и оба SQL запроса")
        
        with col_add_db:
            if st.button("💾 Добавить в векторную базу (с EXPLAIN планом)"):
                if question_opt and sql_basic_opt and sql_optimized_opt:
                    # Проверяем подключение к API
                    if not test_api_connection():
                        st.error(f"❌ Core API недоступен. Убедитесь, что сервис запущен на {API_BASE_URL}")
                        st.info("💡 Запустите: ./run_stack.sh start core_api")
                        st.stop()
                    
                    # Формируем запрос для добавления в векторную базу
                    request_data = {
                        "question": question_opt.strip(),
                        "sql": sql_optimized_opt.strip(),  # Оптимизированный SQL как основной
                        "user_id": "vector_kb_interface",
                        "verified": True,
                        "sql_basic": sql_basic_opt.strip(),
                        "sql_optimized": sql_optimized_opt.strip(),
                        "improvement": improvement_opt.strip() if improvement_opt else "",
                        "is_optimized": True
                    }
                    
                    try:
                        with st.spinner("🔄 Добавление в векторную базу с генерацией EXPLAIN планов..."):
                            response = requests.post(
                                f"{API_BASE_URL}/training/example",
                                json=request_data,
                                timeout=30
                            )
                            
                            if response.status_code == 200:
                                result = response.json()
                                example_id = result.get("example_id", "unknown")
                                
                                # Проверяем результаты валидации оптимизации
                                optimization_validated = result.get("optimization_validated")
                                cost_basic = result.get("cost_basic")
                                cost_optimized = result.get("cost_optimized")
                                cost_improvement_percent = result.get("cost_improvement_percent")
                                optimization_warning = result.get("optimization_warning")
                                
                                # Показываем статус добавления с учетом валидации
                                if optimization_validated is True:
                                    st.success(f"✅ Оптимизированный SQL добавлен в векторную базу!")
                                    st.success(f"✅ Валидация пройдена: улучшение на {cost_improvement_percent}%")
                                    if cost_basic is not None and cost_optimized is not None:
                                        st.info(f"📊 Cost: {cost_basic:.2f} → {cost_optimized:.2f} (улучшение: {cost_improvement_percent:.2f}%)")
                                elif optimization_validated is False:
                                    st.warning(f"⚠️ Оптимизированный SQL добавлен, но валидация не пройдена!")
                                    if optimization_warning:
                                        st.error(optimization_warning)
                                    if cost_basic is not None and cost_optimized is not None:
                                        st.info(f"📊 Cost: базовый={cost_basic:.2f}, оптимизированный={cost_optimized:.2f}")
                                else:
                                    st.success(f"✅ Оптимизированный SQL добавлен в векторную базу!")
                                
                                st.info(f"📋 ID примера: {example_id}")
                                st.info("💡 EXPLAIN планы сгенерированы автоматически для обоих SQL")
                                
                                # Показываем результаты валидации
                                if optimization_validated is not None:
                                    with st.expander("📊 Результаты валидации оптимизации"):
                                        if optimization_validated:
                                            st.success("✅ Валидация пройдена: оптимизированный SQL лучше базового")
                                        else:
                                            st.error("❌ Валидация не пройдена: оптимизированный SQL не лучше базового")
                                        
                                        if cost_basic is not None:
                                            st.metric("Cost базового SQL", f"{cost_basic:.2f}")
                                        if cost_optimized is not None:
                                            st.metric("Cost оптимизированного SQL", f"{cost_optimized:.2f}")
                                        if cost_improvement_percent is not None:
                                            color = "normal" if cost_improvement_percent > 0 else "inverse"
                                            st.metric("Улучшение", f"{cost_improvement_percent:.2f}%", delta=f"{cost_improvement_percent:.2f}%")
                                
                                # Показываем информацию о планах
                                st.markdown("**📊 EXPLAIN планы сгенерированы автоматически:**")
                                st.markdown("- План для оптимизированного SQL сохранен в `metadata.explain_plan`")
                                st.markdown("- План для базового SQL сохранен в `metadata.explain_plan_basic`")
                                st.markdown("- Планы будут включены в контекст при генерации SQL")
                                
                                # Опционально: показываем планы (если API возвращает их)
                                if "explain_plan" in result or "explain_plan_basic" in result:
                                    with st.expander("📈 Просмотр EXPLAIN планов"):
                                        explain_plan_opt = result.get("explain_plan")
                                        explain_plan_basic_val = result.get("explain_plan_basic")
                                        
                                        if explain_plan_opt:
                                            st.markdown("**Оптимизированный SQL:**")
                                            st.code(explain_plan_opt, language="sql")
                                        else:
                                            st.markdown("**Оптимизированный SQL:**")
                                            st.warning("⚠️ План не сгенерирован (возможно ошибка выполнения или SQL)")
                                            st.info("💡 Проверьте логи Core API для деталей ошибки. Возможные причины:")
                                            st.info("   - Неверное имя колонки (используйте: python src/tools/check_table_columns.py)")
                                            st.info("   - Неверное имя таблицы")
                                            st.info("   - Синтаксическая ошибка в SQL")
                                        
                                        if explain_plan_basic_val:
                                            st.markdown("**Базовый SQL:**")
                                            st.code(explain_plan_basic_val, language="sql")
                                        else:
                                            st.markdown("**Базовый SQL:**")
                                            st.warning("⚠️ План не сгенерирован")
                                        
                                        # Показываем сравнение, если есть метрики
                                        width_basic = result.get("width_basic")
                                        width_optimized = result.get("width_optimized")
                                        rows_basic = result.get("rows_basic")
                                        rows_optimized = result.get("rows_optimized")
                                        
                                        if cost_basic is not None or width_basic is not None:
                                            st.markdown("---")
                                            st.markdown("**📊 Сравнение метрик:**")
                                            
                                            comparison_rows = []
                                            if cost_basic is not None and cost_optimized is not None:
                                                comparison_rows.append({
                                                    "Метрика": "Cost",
                                                    "Базовый SQL": f"{cost_basic:.2f}",
                                                    "Оптимизированный SQL": f"{cost_optimized:.2f}",
                                                    "Улучшение": f"{cost_improvement_percent:.2f}%" if cost_improvement_percent is not None else "N/A"
                                                })
                                            if width_basic is not None and width_optimized is not None:
                                                width_improvement = result.get("width_improvement_percent", 0)
                                                comparison_rows.append({
                                                    "Метрика": "Width (байт/строка)",
                                                    "Базовый SQL": f"{width_basic:.0f}",
                                                    "Оптимизированный SQL": f"{width_optimized:.0f}",
                                                    "Улучшение": f"{width_improvement:.2f}%" if width_improvement is not None else "N/A"
                                                })
                                            if rows_basic is not None and rows_optimized is not None:
                                                rows_improvement = result.get("rows_improvement_percent", 0)
                                                comparison_rows.append({
                                                    "Метрика": "Rows (строк)",
                                                    "Базовый SQL": f"{rows_basic:.0f}",
                                                    "Оптимизированный SQL": f"{rows_optimized:.0f}",
                                                    "Улучшение": f"{rows_improvement:.2f}%" if rows_improvement is not None else "N/A"
                                                })
                                            
                                            if comparison_rows:
                                                st.dataframe(pd.DataFrame(comparison_rows), use_container_width=True)
                            else:
                                error_detail = response.json().get("detail", "Неизвестная ошибка") if response.status_code != 200 else "Ошибка API"
                                st.error(f"❌ Ошибка добавления: {error_detail}")
                                st.code(f"Status: {response.status_code}\nResponse: {response.text}")
                    except requests.exceptions.Timeout:
                        st.error("❌ Таймаут при добавлении. SQL может быть сложным для генерации плана.")
                    except Exception as e:
                        st.error(f"❌ Ошибка: {str(e)}")
                        st.info("💡 Убедитесь, что Core API запущен и доступен")
                else:
                    st.warning("Заполните вопрос и оба SQL запроса")
        
        # Показываем сохраненные пары и возможность скачать
        if "optimized_pairs" in st.session_state and st.session_state.optimized_pairs:
            st.markdown("---")
            st.markdown(f"**📋 Сохранено пар: {len(st.session_state.optimized_pairs)}**")
            
            # Показываем предпросмотр
            with st.expander(f"📖 Просмотр сохраненных пар (первые 2 из {len(st.session_state.optimized_pairs)})"):
                for i, pair in enumerate(st.session_state.optimized_pairs[:2], 1):
                    st.markdown(f"**Пара #{i}:**")
                    st.code(f"Q: {pair['question']}\nБазовый: {pair['sql_basic']}\nОптимизированный: {pair['sql_optimized']}", language="sql")
            
            col_download, col_clear = st.columns([2, 1])
            
            with col_download:
                if st.button("📥 Скачать optimized_sql_examples.json"):
                    json_str = json.dumps(st.session_state.optimized_pairs, ensure_ascii=False, indent=2)
                    st.download_button(
                        label="⬇️ Скачать optimized_sql_examples.json",
                        data=json_str,
                        file_name="optimized_sql_examples.json",
                        mime="application/json"
                    )
                    st.success("✅ Файл готов! Используйте его для:")
                    st.code("""
# Анализ производительности
python qa_management_script.py --action performance --input optimized_sql_examples.json

# Обучение на оптимизированных SQL
python qa_management_script.py --action optimize --input optimized_sql_examples.json --output performance_report.json
                    """)
            
            with col_clear:
                if st.button("🗑️ Очистить"):
                    st.session_state.optimized_pairs = []
                    st.success("✅ Пара очищена")
                    st.rerun()
        
        st.markdown("---")
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
                            f"{API_BASE_URL}/query",
                            json={
                                "question": qa["question"],
                                "user_id": "kb_test_user",
                                "role": "admin",
                                "department": "IT",
                                "context": {}
                            },
                            timeout=30
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            # /query возвращает SQLResponse с полем sql
                            if data.get('sql'):
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
    
    st.info("""
    **💡 Важно:** Настройки в этом интерфейсе предназначены для предпросмотра и примеров. 
    Реальная конфигурация системы задается в файле `config.env`.
    
    Для смены модели эмбеддингов и перестроения индексов используйте CLI инструменты (см. инструкции ниже).
    """)
    
    st.markdown("---")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Параметры поиска (⚠️ Не реализовано)")
        
        st.warning("""
        **⚠️ Внимание:** Эти параметры в настоящее время НЕ используются в системе.
        Они сохранены здесь только для справки и будущей реализации.
        
        **Текущая реализация:**
        - Поиск возвращает фиксированное количество результатов (`limit`)
        - Фильтрация по порогу схожести не применяется
        - Ограничение длины контекста не реализовано
        """)
        
        st.markdown("---")
        st.markdown("**💡 Планируемая функциональность:**")
        
        # Примеры настроек (для справки)
        config_examples = [
            {"name": "Консервативный", "similarity": 0.8, "context": 2000, "description": "Высокая точность, меньше результатов"},
            {"name": "Сбалансированный", "similarity": 0.7, "context": 4000, "description": "Оптимальный баланс точности и полноты"},
            {"name": "Агрессивный", "similarity": 0.5, "context": 6000, "description": "Больше результатов, может быть шум"},
            {"name": "Быстрый", "similarity": 0.6, "context": 1000, "description": "Быстрый поиск, минимальный контекст"},
            {"name": "Точный", "similarity": 0.9, "context": 3000, "description": "Максимальная точность, меньше ложных срабатываний"}
        ]
        
        st.markdown("**Примеры конфигураций (для справки):**")
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
            "Порог схожести (не используется):",
            0.0, 1.0, st.session_state.get('selected_similarity', 0.7),
            help="⚠️ Планируется: минимальная схожесть (cosine distance) для включения в результаты. Сейчас не применяется."
        )
        
        max_context_length = st.number_input(
            "Максимальная длина контекста (не используется):",
            min_value=100, max_value=10000, value=st.session_state.get('selected_context', 4000),
            help="⚠️ Планируется: максимальное количество токенов в контексте для LLM. Сейчас не применяется."
        )
        
        st.info("""
        **Как работает сейчас:**
        - Поиск возвращает топ-N результатов по cosine distance (без порога)
        - Контекст формируется из всех найденных чанков (без ограничения длины)
        - Параметр `limit` в API определяет количество чанков (обычно 3-10)
        """)
    
    with col2:
        st.subheader("Текущая конфигурация")
        
        # Показываем текущую модель из config.env
        current_model = os.getenv("HF_MODEL_NAME", "не задана")
        st.info(f"""
        **Текущая модель эмбеддингов:**
        `{current_model}`
        
        Задается в `config.env` через переменную `HF_MODEL_NAME`.
        """)
        
        st.markdown("---")
        st.markdown("**💡 Доступные модели:**")
        st.markdown("""
        - `intfloat/multilingual-e5-base` (768 dim) - многоязычная, текущая
        - `sentence-transformers/all-MiniLM-L6-v2` (384 dim) - быстрая, компактная
        - `sentence-transformers/all-mpnet-base-v2` (768 dim) - высокое качество
        - `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (384 dim) - многоязычная
        
        Для смены модели см. инструкции ниже.
        """)
        
        # Размер батча - тоже не используется в интерфейсе, только в CLI
        st.markdown("---")
        st.markdown("**💡 Размер батча:**")
        st.info("""
        Задается через параметр `--batch-size` в CLI скрипте `generate_embeddings_hf.py`.
        По умолчанию: 200.
        
        Пример:
        ```bash
        python -m src.tools.generate_embeddings_hf \\
          --dsn "$DATABASE_URL" \\
          --model "$HF_MODEL_NAME" \\
          --batch-size 200
        ```
        """)
    
    st.markdown("---")
    st.subheader("📚 Как изменить модель эмбеддингов и перестроить индексы")
    
    st.markdown("""
    ### 1. Изменение модели эмбеддингов
    
    **Текущая модель** задается в `config.env`:
    ```bash
    HF_MODEL_NAME=intfloat/multilingual-e5-base
    ```
    
    **Доступные модели:**
    - `intfloat/multilingual-e5-base` (768 dim) - текущая, многоязычная
    - `sentence-transformers/all-MiniLM-L6-v2` (384 dim) - быстрая, компактная
    - `sentence-transformers/all-mpnet-base-v2` (768 dim) - высокое качество
    - `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (384 dim) - многоязычная
    
    **Шаги для смены модели:**
    1. Отредактируйте `config.env` и установите новую модель в `HF_MODEL_NAME`
    2. Пересоздайте эмбеддинги с новой моделью (см. ниже)
    
    ### 2. Перестроение индексов и эмбеддингов
    
    **Используйте CLI скрипт:**
    ```bash
    # Полная перестройка всех эмбеддингов
    python -m src.tools.generate_embeddings_hf \
      --dsn "$DATABASE_URL" \
      --model "$HF_MODEL_NAME" \
      --rebuild
    
    # Автоматическое изменение размерности (384 → 768)
    python -m src.tools.generate_embeddings_hf \
      --dsn "$DATABASE_URL" \
      --model "$HF_MODEL_NAME" \
      --alter
    
    # С указанием размера батча
    python -m src.tools.generate_embeddings_hf \
      --dsn "$DATABASE_URL" \
      --model "$HF_MODEL_NAME" \
      --rebuild \
      --batch-size 200
    ```
    
    **Флаги:**
    - `--rebuild` - полная перестройка всех эмбеддингов (удаляет старые и создает новые)
    - `--alter` - автоматическое изменение размерности столбца `embedding` (например, 384 → 768)
    - `--batch-size` - размер батча для обработки (по умолчанию 200)
    
    **Важно:** После смены модели обязательно пересоздайте индексы:
    ```sql
    -- Удалить старый индекс
    DROP INDEX IF EXISTS vanna_vectors_embedding_ivf;
    
    -- Создать новый индекс (после пересоздания эмбеддингов)
    CREATE INDEX vanna_vectors_embedding_ivf
    ON vanna_vectors USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);
    ```
    
    ### 3. Документация
    
    Подробнее см.:
    - [VECTOR_DB.md](../docs/VECTOR_DB.md) - структура и обучение векторной БД
    - [TRAINING_GUIDE.md](../docs/TRAINING_GUIDE.md) - руководство по обучению
    - [VECTOR_KB_INTERFACE_GUIDE.md](../docs/VECTOR_KB_INTERFACE_GUIDE.md) - руководство по интерфейсу
    """)
    

with tab7:
    st.header("📝 Документирование базы данных")
    st.markdown("""
    **Цель:** Добавление комментариев к таблицам и колонкам прямо в PostgreSQL через `COMMENT ON TABLE` и `COMMENT ON COLUMN`.
    
    Комментарии сохраняются в самой БД и автоматически попадают в векторную базу знаний при генерации DDL.
    """)
    
    # Проверка подключения к API
    if not test_api_connection():
        st.error(f"❌ Core API недоступен на {API_BASE_URL}. Убедитесь, что сервис запущен.")
        st.info("💡 Запустите: ./run_stack.sh start core_api")
        st.stop()
    
    # Статистика
    st.subheader("📊 Статистика комментариев")
    stats_result = call_api_get_comments_stats()
    
    if "error" in stats_result:
        st.error(f"❌ Ошибка получения статистики: {stats_result.get('error')}")
    else:
        stats = stats_result
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Всего таблиц", stats.get('total_tables', 0))
        with col2:
            st.metric(
                "С комментариями", 
                stats.get('tables_with_comments', 0),
                delta=f"{stats.get('coverage_tables', 0):.1f}%"
            )
        with col3:
            st.metric("Всего колонок", stats.get('total_columns', 0))
        with col4:
            st.metric(
                "С комментариями",
                stats.get('columns_with_comments', 0),
                delta=f"{stats.get('coverage_columns', 0):.1f}%"
            )
        
        # Прогресс-бар
        coverage = stats.get('coverage_tables', 0)
        st.progress(coverage / 100)
        st.caption(f"Прогресс документирования таблиц: {coverage:.1f}%")
    
    st.markdown("---")
    
    # Список таблиц
    st.subheader("📋 Список таблиц")
    
    # Поиск таблиц
    search_query = st.text_input(
        "🔍 Поиск таблицы:",
        placeholder="Введите название таблицы для поиска...",
        key="table_search"
    )
    
    # Фильтр
    filter_type = st.radio(
        "Фильтр:",
        ["Все", "С комментариями", "Без комментариев"],
        horizontal=True
    )
    
    # Загрузка списка таблиц
    with st.spinner("Загрузка списка таблиц..."):
        tables_result = call_api_get_tables_with_comments()
    
    if "error" in tables_result:
        st.error(f"❌ Ошибка получения списка таблиц: {tables_result.get('error')}")
    else:
        tables = tables_result
        
        # Фильтрация по типу комментариев
        if filter_type == "С комментариями":
            filtered_tables = [t for t in tables if t.get('table_comment')]
        elif filter_type == "Без комментариев":
            filtered_tables = [t for t in tables if not t.get('table_comment')]
        else:
            filtered_tables = tables
        
        # Фильтрация по поисковому запросу
        if search_query:
            search_lower = search_query.lower()
            filtered_tables = [t for t in filtered_tables if search_lower in t['table_name'].lower()]
        
        st.info(f"Найдено таблиц: {len(filtered_tables)} из {len(tables)}")
        
        # Показываем таблицы порциями (пагинация)
        if len(filtered_tables) > 20:
            st.warning(f"⚠️ Найдено {len(filtered_tables)} таблиц. Показаны первые 20. Используйте поиск для фильтрации.")
            filtered_tables = filtered_tables[:20]
        
        # Отображение таблиц
        for table in filtered_tables:
            has_comment = table.get('table_comment') is not None
            icon = "✅" if has_comment else "❌"
            
            with st.expander(f"{icon} **{table['table_name']}**"):
                st.markdown(f"### 📝 Комментарий к таблице `{table['table_name']}`")
                st.info("💡 **Комментарий таблицы** описывает общее назначение таблицы, её роль в системе, связи с другими таблицами.")
                
                # Показываем текущий комментарий
                if has_comment:
                    st.markdown("**Текущий комментарий:**")
                    st.info(table['table_comment'])
                else:
                    st.warning("⚠️ Комментарий отсутствует")
                
                st.markdown("---")
                
                # Поле для ввода комментария с placeholder
                comment_key = f"comment_input_{table['table_name']}"
                current_comment = table.get('table_comment', '')
                
                # Показываем краткую подсказку с примером
                st.caption("💡 **Подсказка:** Опишите назначение таблицы, основные поля, связи. Пример: 'Таблица пользователей системы. Содержит учетные записи сотрудников с привязкой к отделам (eq_departments). Основные поля: login, email, department.'")
                
                # Поле для ввода комментария (показываем текущий комментарий или пустое поле)
                comment_text = st.text_area(
                    f"**Введите или отредактируйте комментарий для таблицы `{table['table_name']}`:**",
                    value=current_comment,
                    height=150,
                    placeholder="Например: Таблица пользователей системы. Содержит учетные записи сотрудников с привязкой к отделам и ролям. Основные поля: login, email, department.",
                    help="Опишите назначение таблицы, основные поля, связи с другими таблицами, бизнес-правила. Комментарий будет сохранен в PostgreSQL через COMMENT ON TABLE.",
                    key=comment_key
                )
                
                if st.button("💾 Сохранить комментарий таблицы", key=f"save_table_{table['table_name']}", type="primary"):
                    if comment_text.strip():
                        with st.spinner("Сохранение комментария..."):
                            result = call_api_add_table_comment(table['table_name'], comment_text.strip())
                            if result.get('success'):
                                st.success(f"✅ Комментарий для таблицы `{table['table_name']}` успешно сохранен!")
                                st.rerun()
                            else:
                                st.error(f"❌ Ошибка: {result.get('error', 'Неизвестная ошибка')}")
                    else:
                        st.warning("⚠️ Комментарий не может быть пустым")
                
                st.markdown("---")
                
                # Раздел для комментариев колонок (только по запросу)
                st.markdown(f"### 📝 Комментарии к колонкам (опционально)")
                st.info("💡 **Комментарии колонок** обычно нужны только для ключевых таблиц. Нажмите кнопку ниже, если нужно добавить комментарии к колонкам этой таблицы.")
                
                # Ключ для хранения состояния загрузки колонок
                show_columns_key = f"show_columns_{table['table_name']}"
                
                # Кнопка для загрузки колонок
                if st.button("📋 Показать колонки для комментирования", key=f"btn_show_cols_{table['table_name']}"):
                    st.session_state[show_columns_key] = True
                    st.rerun()
                
                # Загружаем колонки только если пользователь нажал кнопку
                if st.session_state.get(show_columns_key, False):
                    with st.spinner("Загрузка колонок..."):
                        columns_result = call_api_get_table_columns(table['table_name'])
                    
                    if "error" in columns_result:
                        st.error(f"❌ Ошибка получения колонок: {columns_result.get('error')}")
                    else:
                        columns = columns_result
                        st.markdown(f"**Всего колонок:** {len(columns)}")
                        
                        # Кнопка для скрытия колонок
                        if st.button("❌ Скрыть колонки", key=f"btn_hide_cols_{table['table_name']}"):
                            st.session_state[show_columns_key] = False
                            st.rerun()
                        
                        if not columns:
                            st.warning("⚠️ Колонки не найдены")
                        else:
                            # Показываем все колонки с возможностью редактирования
                            for col in columns:
                                col_has_comment = col.get('column_comment') is not None
                                col_icon = "✅" if col_has_comment else "❌"
                                
                                st.markdown("---")
                                st.markdown(f"#### {col_icon} **{col['column_name']}** (`{col.get('data_type', '')}`)")
                                
                                if col_has_comment:
                                    st.markdown("**Текущий комментарий:**")
                                    st.info(col['column_comment'])
                                else:
                                    st.warning("⚠️ Комментарий отсутствует")
                                
                                # Поле для ввода комментария колонки
                                col_comment_key = f"col_comment_{table['table_name']}_{col['column_name']}"
                                col_current_comment = col.get('column_comment', '')
                                
                                col_comment_text = st.text_area(
                                    f"**Комментарий для колонки `{col['column_name']}`:**",
                                    value=col_current_comment,
                                    height=100,
                                    placeholder=f"Например: {'Внешний ключ на таблицу...' if 'id' in col['column_name'].lower() else 'Описание назначения колонки...'}",
                                    help=f"Опишите назначение колонки {col['column_name']}, её тип ({col.get('data_type', '')}), ограничения, связи.",
                                    key=col_comment_key
                                )
                                
                                if st.button("💾 Сохранить", key=f"save_col_{table['table_name']}_{col['column_name']}", type="primary"):
                                    if col_comment_text.strip():
                                        with st.spinner("Сохранение комментария..."):
                                            result = call_api_add_column_comment(
                                                table['table_name'],
                                                col['column_name'],
                                                col_comment_text.strip()
                                            )
                                            if result.get('success'):
                                                st.success(f"✅ Комментарий для колонки `{col['column_name']}` успешно сохранен!")
                                                st.rerun()
                                            else:
                                                st.error(f"❌ Ошибка: {result.get('error', 'Неизвестная ошибка')}")
                                    else:
                                        st.warning("⚠️ Комментарий не может быть пустым")
    
    st.markdown("---")
    st.info("💡 **Подсказка:** Раскройте нужную таблицу в списке выше, чтобы добавить или отредактировать комментарий. Для комментирования колонок используйте кнопку '📋 Показать колонки для комментирования' внутри каждой таблицы. Комментарии сохраняются прямо в PostgreSQL через `COMMENT ON TABLE` и `COMMENT ON COLUMN`.")
    st.markdown("---")

# Боковая панель
with st.sidebar:
    # Статус API - важная информация о доступности сервиса
    st.subheader("📡 Статус API")
    if test_api_connection():
        st.success(f"✅ Core API ({API_BASE_URL}) - Работает")
    else:
        st.error(f"❌ Core API ({API_BASE_URL}) - Недоступен")
        st.warning(f"Убедитесь, что сервис запущен: uvicorn src.api.main:app --host 0.0.0.0 --port 8000")
    
    st.header("📁 Документация")
    
    # GitHub репозиторий (можно настроить через переменную окружения)
    github_repo = os.getenv("GITHUB_REPO_URL", "https://github.com/kobyzev-yuri/NLSQL")
    # Если репозиторий переименован, можно использовать формат: owner/repo
    # или полный URL: https://github.com/owner/repo
    
    st.markdown(f"""
    **📚 Документация проекта:**
    
    Все ссылки на документацию находятся в основном README проекта:
    
    **[📖 README.md на GitHub]({github_repo}/blob/main/README.md)**
    
    В README вы найдете ссылки на:
    - [Vector KB Interface Guide]({github_repo}/blob/main/docs/VECTOR_KB_INTERFACE_GUIDE.md) - руководство по работе с этим интерфейсом
    - [Vector DB Documentation]({github_repo}/blob/main/docs/VECTOR_DB.md) - структура и обучение векторной БД
    - [KB Testing Guide]({github_repo}/blob/main/docs/KB_TESTING_GUIDE.md) - методика тестирования базы знаний
    - [User Guide]({github_repo}/blob/main/docs/USER_GUIDE.md) - руководство для пользователей
    - [API Reference]({github_repo}/blob/main/docs/API_REFERENCE.md) - документация API для разработчиков
    - И другие документы в директории `docs/`
    
    **💡 Подсказка:** 
    - Если репозиторий переименован, установите переменную окружения `GITHUB_REPO_URL` в `config.env`
    - Все документы также доступны локально в директории `docs/` проекта
    """)
    
    # Локальный доступ к файлам
    with st.expander("📂 Локальный доступ к документам"):
        st.markdown("""
        **Доступ через терминал:**
        ```bash
        # Открыть в редакторе
        code docs/USER_GUIDE.md
        code docs/VECTOR_KB_INTERFACE_GUIDE.md
        code docs/VECTOR_DB.md
        
        # Просмотр в терминале
        cat docs/VECTOR_KB_INTERFACE_GUIDE.md
        less docs/VECTOR_DB.md
        ```
        """)

# Футер
st.markdown("---")
st.markdown("**Vector KB Interface** - Интерфейс для работы с векторной базой знаний")
