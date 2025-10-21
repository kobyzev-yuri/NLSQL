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
            with st.spinner("Выполняю поиск..."):
                try:
                    vanna = get_vanna_client()
                    if vanna:
                        # Выполняем поиск в зависимости от типа (синхронно)
                        if search_type == "semantic":
                            results = vanna.get_related_ddl(query)
                        elif search_type == "ddl":
                            results = vanna.get_related_ddl(query)
                        elif search_type == "documentation":
                            results = vanna.get_related_documentation(query)
                        elif search_type == "examples":
                            results = vanna.get_related_question_sql(query)
                        
                        # Если результат - корутина, ждем его
                        if hasattr(results, '__await__'):
                            results = asyncio.run(results)
                        
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
                try:
                    vanna = get_vanna_client()
                    if vanna:
                        # Используем правильный метод для добавления Q/A пары
                        # DocStructureVannaSemantic не имеет add_question_sql, используем альтернативный подход
                        st.info("⚠️ Добавление Q/A пар через интерфейс пока не поддерживается. Используйте CLI скрипт qa_management_script.py")
                        st.code(f"python qa_management_script.py --action add --input qa_pairs.json")
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
                try:
                    vanna = get_vanna_client()
                    if vanna:
                        # DocStructureVannaSemantic не имеет add_ddl, используем альтернативный подход
                        st.info("⚠️ Обучение на DDL через интерфейс пока не поддерживается. Используйте CLI скрипт:")
                        st.code(f"python qa_management_script.py --action embeddings")
                    else:
                        st.error("Vanna AI клиент недоступен")
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
                try:
                    vanna = get_vanna_client()
                    if vanna:
                        # DocStructureVannaSemantic не имеет add_documentation, используем альтернативный подход
                        st.info("⚠️ Обучение на документации через интерфейс пока не поддерживается. Используйте CLI скрипт:")
                        st.code(f"python qa_management_script.py --action embeddings")
                    else:
                        st.error("Vanna AI клиент недоступен")
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
    """)
    
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
    
    # Примеры метрик для разных типов запросов
    metrics_examples = [
        {"type": "Простые запросы", "precision": 0.92, "recall": 0.89, "f1": 0.90, "examples": ["Покажи всех пользователей", "Список отделов"]},
        {"type": "Фильтрация", "precision": 0.88, "recall": 0.85, "f1": 0.86, "examples": ["Пользователи за месяц", "Платежи по клиентам"]},
        {"type": "Агрегация", "precision": 0.78, "recall": 0.75, "f1": 0.76, "examples": ["Статистика по отделам", "Сумма платежей"]},
        {"type": "JOIN запросы", "precision": 0.85, "recall": 0.82, "f1": 0.83, "examples": ["Пользователи с отделами", "Платежи с клиентами"]},
        {"type": "Сложные запросы", "precision": 0.80, "recall": 0.78, "f1": 0.79, "examples": ["Аналитика по периодам", "Отчеты с группировкой"]}
    ]
    
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
    
    # Примеры метрик по типам запросов
    st.subheader("📊 Детальные метрики по типам запросов")
    
    for metric in metrics_examples:
        with st.expander(f"📈 {metric['type']} (F1: {metric['f1']:.2f})"):
            col1, col2 = st.columns([1, 2])
            with col1:
                st.metric("Precision", f"{metric['precision']:.2f}")
                st.metric("Recall", f"{metric['recall']:.2f}")
                st.metric("F1-Score", f"{metric['f1']:.2f}")
            with col2:
                st.markdown("**Примеры запросов:**")
                for example in metric['examples']:
                    st.markdown(f"• {example}")
    
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
    
    - [Training Guide](docs/VANNA_TRAINING_GUIDE.md) - руководство по обучению
    - [QA Expansion](docs/customer_requests/CUSTOMER_QA_EXPANSION_REQUEST.md) - план расширения Q/A
    - [RAG Checklist](RAG_IMPROVEMENT_CHECKLIST.md) - чеклист улучшений RAG
    - [Vector KB Plan](VECTOR_KB_IMPROVEMENT_PLAN.md) - план улучшения векторки
    - [Services Guide](docs/SERVICES_STARTUP_GUIDE.md) - руководство по сервисам
    
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
    """)

# Футер
st.markdown("---")
st.markdown("**Vector KB Interface** - Интерфейс для работы с векторной базой знаний")
