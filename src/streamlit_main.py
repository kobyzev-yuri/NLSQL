"""
Streamlit приложение для NL→SQL системы
"""

import streamlit as st
import requests
import json
from typing import Dict, Any

# Настройка страницы
st.set_page_config(
    page_title="NL→SQL System",
    page_icon="🔍",
    layout="wide"
)

# Заголовок
st.title("🔍 NL→SQL System")
st.markdown("Система генерации SQL из естественного языка")

# Основной интерфейс
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📝 Введите запрос")
    
    # Параметры
    col_role, col_dept = st.columns(2)
    with col_role:
        role = st.selectbox("Роль:", ["admin", "manager", "user"])
    with col_dept:
        department = st.selectbox("Отдел:", ["IT", "Finance", "HR"])
    
    # Поле ввода
    # Инициализируем session state для примера
    if "example_question" not in st.session_state:
        st.session_state.example_question = ""
    
    question = st.text_area(
        "Ваш вопрос:",
        value=st.session_state.example_question,
        placeholder="Например: Покажи все поручения за последний месяц",
        height=100,
        key="question_input"
    )
    
    # Кнопка генерации
    if st.button("🔍 Генерировать SQL", type="primary", use_container_width=True):
        if question:
            with st.spinner("Генерация SQL..."):
                try:
                    # Вызов API
                    response = requests.post(
                        "http://localhost:3000/generate-sql",
                        data={
                            "question": question,
                            "role": role,
                            "department": department
                        },
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("success"):
                            st.success("✅ SQL сгенерирован!")
                            st.code(data.get("sql", ""), language="sql")
                            
                            # Сохраняем SQL в session state для выполнения
                            st.session_state.generated_sql = data.get("sql", "")
                            st.session_state.generated_role = role
                            st.session_state.generated_department = department
                        else:
                            st.error(f"❌ Ошибка генерации: {data.get('error', 'Unknown error')}")
                    else:
                        st.error(f"❌ HTTP ошибка: {response.status_code}")
                        
                except requests.exceptions.RequestException as e:
                    st.error(f"❌ Ошибка соединения: {e}")
                except Exception as e:
                    st.error(f"❌ Неожиданная ошибка: {e}")
        else:
            st.warning("⚠️ Введите вопрос")

with col2:
    st.subheader("⚙️ Действия")
    
    # Показываем сгенерированный SQL
    if hasattr(st.session_state, 'generated_sql') and st.session_state.generated_sql:
        st.markdown("**Сгенерированный SQL:**")
        st.code(st.session_state.generated_sql, language="sql")
        
        # Кнопка выполнения
        if st.button("▶️ Выполнить SQL", use_container_width=True):
            with st.spinner("Выполнение SQL..."):
                try:
                    exec_response = requests.post(
                        "http://localhost:3000/execute-sql",
                        data={
                            "question": st.session_state.generated_sql,
                            "role": st.session_state.generated_role,
                            "department": st.session_state.generated_department
                        },
                        timeout=30
                    )
                    
                    if exec_response.status_code == 200:
                        exec_data = exec_response.json()
                        if exec_data.get("success"):
                            st.success("✅ SQL выполнен!")
                            
                            # Показываем результаты в отдельной секции
                            st.markdown("**Результаты:**")
                            if exec_data.get("data"):
                                st.dataframe(exec_data.get("data"), use_container_width=True)
                            else:
                                st.info("Нет данных для отображения")
                        else:
                            st.error(f"❌ Ошибка выполнения: {exec_data.get('error', 'Unknown error')}")
                    else:
                        st.error(f"❌ HTTP ошибка: {exec_response.status_code}")
                        
                except requests.exceptions.RequestException as e:
                    st.error(f"❌ Ошибка соединения: {e}")
                except Exception as e:
                    st.error(f"❌ Неожиданная ошибка: {e}")
    else:
        st.info("Сначала сгенерируйте SQL")

# Примеры запросов
st.subheader("💡 Примеры запросов")
examples = [
    "Покажи все поручения",
    "Найди пользователей из IT отдела", 
    "Покажи статистику по платежам",
    "Найди документы за последний месяц"
]

# Создаем кнопки примеров
cols = st.columns(2)
for i, example in enumerate(examples):
    with cols[i % 2]:
        if st.button(f"📝 {example}", key=f"example_{i}", use_container_width=True):
            # Устанавливаем пример в session state
            st.session_state.example_question = example
            st.rerun()

# Статус системы
st.subheader("📊 Статус системы")
col1, col2, col3 = st.columns(3)

with col1:
    try:
        response = requests.get("http://localhost:3000/", timeout=5)
        if response.status_code == 200:
            st.success("✅ FastAPI (3000)")
        else:
            st.error("❌ FastAPI (3000)")
    except:
        st.error("❌ FastAPI (3000)")

with col2:
    try:
        response = requests.get("http://localhost:8081/health", timeout=5)
        if response.status_code == 200:
            st.success("✅ Mock API (8081)")
        else:
            st.error("❌ Mock API (8081)")
    except:
        st.error("❌ Mock API (8081)")

with col3:
    st.success("✅ Streamlit (8501)")