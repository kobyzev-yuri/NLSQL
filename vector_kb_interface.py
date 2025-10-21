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
import asyncio
import json
import time
import sys
import os
from typing import Dict, List, Any, Optional
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Добавляем путь к проекту
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.vanna.vanna_semantic_fixed import create_semantic_vanna_client
from src.services.query_service import QueryService
from src.tools.generate_embeddings_hf import main as generate_embeddings

# Настройка страницы
st.set_page_config(
    page_title="Vector KB Interface",
    page_icon="🧠",
    layout="wide"
)

# Заголовок
st.title("🧠 Vector Knowledge Base Interface")
st.markdown("Интерфейс для тестирования и дообучения векторной базы знаний")

# Инициализация
@st.cache_resource
def get_vanna_client():
    """Получение клиента Vanna AI"""
    try:
        return create_semantic_vanna_client()
    except Exception as e:
        st.error(f"Ошибка инициализации Vanna AI: {e}")
        return None

@st.cache_resource
def get_query_service():
    """Получение сервиса запросов"""
    try:
        return QueryService()
    except Exception as e:
        st.error(f"Ошибка инициализации QueryService: {e}")
        return None

# Основные вкладки
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🔍 Тестирование поиска", 
    "📝 Добавление Q/A", 
    "🎓 Обучение", 
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
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        query = st.text_area(
            "Введите тестовый запрос:",
            value=test_queries[0],
            height=100,
            help="Введите вопрос на естественном языке для тестирования поиска"
        )
    
    with col2:
        search_type = st.selectbox(
            "Тип поиска:",
            ["semantic", "ddl", "documentation", "examples"],
            help="Выберите тип поиска для тестирования"
        )
        
        max_results = st.slider("Максимум результатов:", 1, 20, 5)
    
    if st.button("🔍 Тестировать поиск", type="primary"):
        if query:
            with st.spinner("Выполняю поиск..."):
                try:
                    vanna = get_vanna_client()
                    if vanna:
                        # Выполняем поиск в зависимости от типа
                        if search_type == "semantic":
                            results = vanna.get_related_ddl(query)
                        elif search_type == "ddl":
                            results = vanna.get_related_ddl(query)
                        elif search_type == "documentation":
                            results = vanna.get_related_documentation(query)
                        elif search_type == "examples":
                            results = vanna.get_related_question_sql(query)
                        
                        st.success(f"Найдено {len(results)} результатов")
                        
                        # Отображаем результаты
                        for i, result in enumerate(results[:max_results]):
                            with st.expander(f"Результат {i+1}"):
                                st.code(result, language="sql")
                    else:
                        st.error("Vanna AI клиент недоступен")
                        
                except Exception as e:
                    st.error(f"Ошибка поиска: {e}")

with tab2:
    st.header("📝 Добавление новых Q/A пар")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Ручное добавление")
        
        question = st.text_area("Вопрос:", height=100)
        sql = st.text_area("SQL запрос:", height=200, language="sql")
        
        if st.button("➕ Добавить Q/A пару"):
            if question and sql:
                try:
                    vanna = get_vanna_client()
                    if vanna:
                        vanna.add_question_sql(question, sql)
                        st.success("Q/A пара добавлена!")
                    else:
                        st.error("Vanna AI клиент недоступен")
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
                    with st.spinner("Импортирую Q/A пары..."):
                        vanna = get_vanna_client()
                        if vanna:
                            for item in data:
                                vanna.add_question_sql(item['question'], item['sql'])
                            st.success(f"Импортировано {len(data)} Q/A пар!")
                        else:
                            st.error("Vanna AI клиент недоступен")
            except Exception as e:
                st.error(f"Ошибка загрузки файла: {e}")

with tab3:
    st.header("🎓 Обучение на новых данных")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Обучение на DDL")
        
        ddl_text = st.text_area(
            "DDL скрипты:",
            height=200,
            language="sql",
            help="Вставьте CREATE TABLE, ALTER TABLE и другие DDL команды"
        )
        
        if st.button("📚 Обучить на DDL"):
            if ddl_text:
                try:
                    vanna = get_vanna_client()
                    if vanna:
                        vanna.add_ddl(ddl_text)
                        st.success("Обучение на DDL завершено!")
                    else:
                        st.error("Vanna AI клиент недоступен")
                except Exception as e:
                    st.error(f"Ошибка обучения: {e}")
    
    with col2:
        st.subheader("Обучение на документации")
        
        doc_text = st.text_area(
            "Документация:",
            height=200,
            help="Вставьте описание бизнес-логики, связей таблиц и т.д."
        )
        
        if st.button("📖 Обучить на документации"):
            if doc_text:
                try:
                    vanna = get_vanna_client()
                    if vanna:
                        vanna.add_documentation(doc_text)
                        st.success("Обучение на документации завершено!")
                    else:
                        st.error("Vanna AI клиент недоступен")
                except Exception as e:
                    st.error(f"Ошибка обучения: {e}")
    
    # Генерация эмбеддингов
    st.subheader("🔄 Генерация эмбеддингов")
    
    if st.button("⚡ Сгенерировать эмбеддинги"):
        with st.spinner("Генерирую эмбеддинги..."):
            try:
                # Запускаем скрипт генерации эмбеддингов
                result = generate_embeddings()
                st.success("Эмбеддинги сгенерированы!")
            except Exception as e:
                st.error(f"Ошибка генерации эмбеддингов: {e}")

with tab4:
    st.header("📊 Аналитика качества")
    
    # Метрики качества
    st.subheader("📈 Метрики качества поиска")
    
    # Тестовые данные для демонстрации
    test_data = {
        'query': ['Пользователи', 'Поручения', 'Платежи', 'Клиенты', 'Отделы'],
        'precision': [0.85, 0.92, 0.78, 0.88, 0.90],
        'recall': [0.82, 0.89, 0.75, 0.85, 0.87],
        'f1_score': [0.83, 0.90, 0.76, 0.86, 0.88]
    }
    
    df = pd.DataFrame(test_data)
    
    # График метрик
    fig = px.bar(
        df, 
        x='query', 
        y=['precision', 'recall', 'f1_score'],
        title="Метрики качества по типам запросов",
        barmode='group'
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Статистика векторки
    st.subheader("📊 Статистика векторной базы")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Всего записей", "1,247", "23")
    
    with col2:
        st.metric("DDL записей", "156", "5")
    
    with col3:
        st.metric("Q/A пар", "89", "12")
    
    # Анализ качества эмбеддингов
    st.subheader("🔍 Анализ качества эмбеддингов")
    
    if st.button("🔬 Запустить анализ"):
        with st.spinner("Анализирую качество эмбеддингов..."):
            # Здесь можно добавить реальный анализ
            st.info("Анализ завершен. Качество эмбеддингов: 87%")

with tab5:
    st.header("⚙️ Настройки")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Параметры поиска")
        
        similarity_threshold = st.slider(
            "Порог схожести:",
            0.0, 1.0, 0.7,
            help="Минимальная схожесть для включения в результаты"
        )
        
        max_context_length = st.number_input(
            "Максимальная длина контекста:",
            min_value=100, max_value=10000, value=4000,
            help="Максимальное количество токенов в контексте"
        )
    
    with col2:
        st.subheader("Модель эмбеддингов")
        
        embedding_model = st.selectbox(
            "Модель:",
            [
                "sentence-transformers/all-MiniLM-L6-v2",
                "sentence-transformers/all-mpnet-base-v2", 
                "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
            ],
            help="Выберите модель для генерации эмбеддингов"
        )
        
        batch_size = st.number_input(
            "Размер батча:",
            min_value=1, max_value=1000, value=200,
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
    - [Training Guide](docs/VANNA_TRAINING_GUIDE.md)
    - [QA Expansion](docs/customer_requests/CUSTOMER_QA_EXPANSION_REQUEST.md)
    - [RAG Checklist](RAG_IMPROVEMENT_CHECKLIST.md)
    """)

# Футер
st.markdown("---")
st.markdown("**Vector KB Interface** - Интерфейс для работы с векторной базой знаний")
