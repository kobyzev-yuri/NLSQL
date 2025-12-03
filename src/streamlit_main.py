"""
Streamlit приложение для NL→SQL системы
"""

import streamlit as st
import requests
import json
import os
from pathlib import Path
from typing import Dict, Any

# Load environment variables from config.env before anything else
from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / "config.env", override=True)

# Настройка страницы
st.set_page_config(
    page_title="NL→SQL System",
    page_icon="🔍",
    layout="wide"
)

# Заголовок
st.title("🔍 NL→SQL System")
st.markdown("Система генерации SQL из естественного языка")

# Информация о текущем провайдере из config.env
import os
current_config_provider = os.getenv("LLM_PROVIDER", "openai")
provider_display = "GPT-4o (OpenAI/ProxyAPI)" if current_config_provider == "openai" else f"Qwen (Ollama) - {os.getenv('OLLAMA_MODEL', 'qwen2.5-coder:1.5b')}"
st.info(f"⚙️ **Провайдер по умолчанию в config.env:** {provider_display} | 💡 Вы можете переключить провайдер ниже для этого запроса")

# Форма ввода запроса
st.subheader("📝 Введите запрос")

# Параметры
col_provider, col_timeout, col_role, col_dept = st.columns(4)
with col_provider:
    llm_provider = st.selectbox(
        "🤖 LLM Провайдер:",
        ["openai", "ollama"],
        format_func=lambda x: "GPT-4o (OpenAI/ProxyAPI)" if x == "openai" else "Qwen (Ollama локально)",
        help="Выберите провайдер для генерации SQL. Переключается для каждого запроса."
    )
    # Визуальная индикация выбранного провайдера
    if llm_provider == "ollama":
        st.info("🦙 Используется: **Qwen (Ollama)** - локальная модель, медленнее (~30-45 сек)")
    else:
        st.info("🤖 Используется: **GPT-4o** - облачный API, быстрее (~2-5 сек)")
with col_timeout:
    import os
    default_timeout = int(os.getenv("OLLAMA_TIMEOUT", "500")) if llm_provider == "ollama" else int(os.getenv("OPENAI_TIMEOUT", "60"))
    timeout = st.number_input(
        "⏱️ Таймаут (сек):",
        min_value=10,
        max_value=600,
        value=default_timeout,
        step=10,
        help="Таймаут для генерации SQL в секундах"
    )
with col_role:
    role = st.selectbox("Роль:", ["admin", "manager", "user"])
with col_dept:
    department = st.selectbox("Отдел:", ["Департамент продаж", "Отдел 1", "Продажи", "Продажи 2", "Управление Крупного Крупнейшего Бизнеса"])

# Поле ввода
# Инициализируем session state для примера
if "example_question" not in st.session_state:
    st.session_state.example_question = ""

question = st.text_area(
    "Ваш вопрос:",
    value=st.session_state.example_question,
    placeholder="Например: Покажи всех пользователей с email, Сколько поручений в системе?",
    height=100,
    key="question_input"
)

# Кнопка генерации
if st.button("🔍 Генерировать SQL", type="primary", use_container_width=True):
    if question:
        provider_name = "Qwen (Ollama)" if llm_provider == "ollama" else "GPT-4o"
        
        # Засекаем время начала генерации
        import time
        start_time = time.time()
        
        with st.spinner(f"Генерация SQL через {provider_name}... (таймаут: {timeout} сек)"):
            try:
                # Вызов API
                response = requests.post(
                    "http://localhost:3000/generate-sql",
                    data={
                        "question": question,
                        "role": role,
                        "department": department,
                        "llm_provider": llm_provider,
                        "timeout": str(timeout)
                    },
                    timeout=timeout
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        # Вычисляем время генерации
                        end_time = time.time()
                        generation_time = end_time - start_time
                        provider_used = "Qwen (Ollama)" if llm_provider == "ollama" else "GPT-4o"
                        
                        st.success(f"✅ SQL сгенерирован через **{provider_used}**!")
                        
                        # Показываем время генерации и информацию о провайдере
                        st.info(f"⏱️ **Время генерации:** {generation_time:.2f} сек | 📡 **Провайдер запроса:** {provider_used} | ⚙️ **Провайдер в config.env:** {current_config_provider}")
                        
                        # Основной SQL
                        st.markdown("### 📝 Сгенерированный SQL:")
                        st.code(data.get("sql", ""), language="sql")
                        
                        # План выполнения (всегда показываем как в интерфейсе 3000)
                        if data.get("plan"):
                            st.markdown("### 🧭 План запроса:")
                            st.json(data.get("plan"))
                        
                        # Дополнительные детали в expanders
                        col_details1, col_details2 = st.columns(2)
                        
                        with col_details1:
                            # Отображаем шаблон SQL (промпт)
                            if data.get("sql_template"):
                                with st.expander("📋 SQL Шаблон (исходный)", expanded=False):
                                    st.code(data.get("sql_template", ""), language="sql")
                        
                        with col_details2:
                            # Финальный SQL с ограничениями
                            if data.get("final_sql"):
                                with st.expander("🔒 Финальный SQL (с ограничениями)", expanded=False):
                                    st.code(data.get("final_sql", ""), language="sql")
                                    if data.get("restrictions"):
                                        st.markdown("**Применённые ограничения:**")
                                        for r in data.get("restrictions", []):
                                            st.markdown(f"- {r}")
                        
                        # Объяснение и агент
                        if data.get("explanation") or data.get("agent_type"):
                            st.markdown("---")
                            info_col1, info_col2 = st.columns([3, 1])
                            with info_col1:
                                if data.get("explanation"):
                                    st.info(data.get("explanation"))
                            with info_col2:
                                if data.get("agent_type"):
                                    st.caption(f"**Агент:** {data.get('agent_type', 'N/A')}")
                        
                        # Сохраняем SQL в session state для выполнения
                        st.session_state.generated_sql = data.get("final_sql") or data.get("sql", "")
                        st.session_state.generated_role = role
                        st.session_state.generated_department = department
                        st.session_state.generated_question = question
                        st.session_state.generated_llm_provider = llm_provider  # Сохраняем для таймаута выполнения SQL
                    else:
                        error_msg = data.get('error', 'Unknown error')
                        if llm_provider == "ollama" and "timeout" in str(error_msg).lower():
                            st.error(f"❌ Таймаут при генерации через Ollama. Модель работает медленно. Попробуйте:\n- Использовать более простой запрос\n- Переключиться на GPT-4o\n- Проверить, что Ollama запущен: `curl http://localhost:11434/api/tags`")
                        else:
                            st.error(f"❌ Ошибка генерации: {error_msg}")
                else:
                    error_text = response.text[:200] if hasattr(response, 'text') else ""
                    st.error(f"❌ HTTP ошибка: {response.status_code}\n{error_text}")
                    
            except requests.exceptions.Timeout as e:
                if llm_provider == "ollama":
                    st.error(f"⏱️ Таймаут при генерации через Ollama (120 сек). Модель работает медленно.\n\n💡 Рекомендации:\n- Используйте более простой запрос\n- Переключитесь на GPT-4o для быстрой генерации\n- Проверьте, что Ollama запущен: `curl http://localhost:11434/api/tags`")
                else:
                    st.error(f"⏱️ Таймаут при генерации через GPT-4o")
            except requests.exceptions.RequestException as e:
                if llm_provider == "ollama" and "11434" in str(e):
                    st.error(f"❌ Не удалось подключиться к Ollama (localhost:11434).\n\n💡 Проверьте:\n- Запущен ли Ollama: `ollama serve`\n- Доступна ли модель: `ollama list | grep qwen`\n- Если модель отсутствует: `ollama pull qwen2.5-coder:1.5b`")
                else:
                    st.error(f"❌ Ошибка соединения: {e}")
            except Exception as e:
                st.error(f"❌ Неожиданная ошибка: {e}")
    else:
        st.warning("⚠️ Введите вопрос")

# Разделитель
st.markdown("---")

# Секция выполнения SQL (внизу)
if hasattr(st.session_state, 'generated_sql') and st.session_state.generated_sql:
    st.subheader("⚙️ Выполнение SQL")
    
    # Показываем сгенерированный SQL для справки
    with st.expander("📋 Просмотреть сгенерированный SQL", expanded=False):
        st.code(st.session_state.generated_sql, language="sql")
        if hasattr(st.session_state, 'generated_question'):
            st.caption(f"**Вопрос:** {st.session_state.generated_question}")
    
    # Параметры выполнения SQL
    col_exec_timeout, col_exec_button = st.columns([1, 3])
    with col_exec_timeout:
        default_exec_timeout = int(os.getenv("OPENAI_TIMEOUT", "60"))  # По умолчанию используем OpenAI timeout
        sql_execution_timeout = st.number_input(
            "⏱️ Таймаут выполнения (сек):",
            min_value=10,
            max_value=600,
            value=default_exec_timeout,
            step=10,
            help="Таймаут для выполнения SQL запроса в секундах",
            key="sql_execution_timeout"
        )
    with col_exec_button:
        st.write("")  # Отступ
        st.write("")  # Отступ
        execute_button = st.button("▶️ Выполнить SQL", type="primary", use_container_width=True)
    
    if execute_button:
        with st.spinner(f"Выполнение SQL... (таймаут: {sql_execution_timeout} сек)"):
            try:
                exec_response = requests.post(
                    "http://localhost:3000/execute-sql",
                    data={
                        "question": st.session_state.generated_question if hasattr(st.session_state, 'generated_question') else st.session_state.generated_sql,
                        "role": st.session_state.generated_role,
                        "department": st.session_state.generated_department
                    },
                    timeout=sql_execution_timeout
                )
                
                if exec_response.status_code == 200:
                    exec_data = exec_response.json()
                    if exec_data.get("success"):
                        st.success("✅ SQL выполнен успешно!")
                        
                        # Показываем SQL который был выполнен
                        st.markdown("### 🔐 Выполненный SQL (с ролевыми ограничениями):")
                        st.code(exec_data.get("final_sql") or exec_data.get("sql", ""), language="sql")
                        
                        # Статистика выполнения
                        col_stat1, col_stat2, col_stat3 = st.columns(3)
                        with col_stat1:
                            st.metric("Строк найдено", exec_data.get("row_count", 0))
                        with col_stat2:
                            st.metric("Время выполнения", f"{exec_data.get('execution_time', 0):.3f}с")
                        with col_stat3:
                            if exec_data.get("restrictions"):
                                st.metric("Ограничений применено", len(exec_data.get("restrictions", [])))
                        
                        # Показываем результаты
                        st.markdown("### 📊 Результаты запроса:")
                        if exec_data.get("data") and len(exec_data.get("data", [])) > 0:
                            st.dataframe(exec_data.get("data"), use_container_width=True, height=400)
                        else:
                            st.info("Нет данных для отображения")
                        
                        # Применённые ограничения
                        if exec_data.get("restrictions"):
                            st.markdown("**Применённые ограничения:**")
                            for r in exec_data.get("restrictions", []):
                                st.markdown(f"- {r}")
                    else:
                        st.error(f"❌ Ошибка выполнения: {exec_data.get('error', 'Unknown error')}")
                else:
                    st.error(f"❌ HTTP ошибка: {exec_response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Ошибка соединения: {e}")
            except Exception as e:
                st.error(f"❌ Неожиданная ошибка: {e}")

# Примеры запросов из MaxB
st.subheader("💡 Примеры запросов (тестовые из MaxB)")

# Группируем примеры по категориям (расширенный список из Simple Web Interface)
example_categories = {
    "👥 Пользователи": [
        "Выведи список пользователей, зарегистрированных после 1 августа 2025 года",
        "Выведи список пользователей, являющихся менеджерами",
        "Список пользователей из equsers, имеющих имя Иван",
        "Покажи всех активных пользователей с их контактными данными"
    ],
    "🏢 Профили компаний": [
        "Выведи список профилей, находящихся в статусе На доработке в КЦ",
        "Выведи список профилей компаний, работающих в Уральском федеральном округе и отсортируй его по дате регистрации",
        "Выведи список профилей компаний, имеющих соглашения",
        "Список бизнес-единиц с комментариями из tbl_business_unit_comment"
    ],
    "📋 Поручения": [
        "Выведи список всех поручений, относящихся к канцтоварам",
        "Выведи регистрационные номера и наименования банков для 10 самых дорогих поручений (по сумме платежа в рублях), находящихся в статусе Отправлен в рейс",
        "Покажи поручения, созданные за последний месяц, отсортированные по сумме платежа"
    ],
    "💰 Валюты и фильтры": [
        "Фильтр по валютам в tbl_currencies с курсом выше 100",
        "Найди профили компаний с ИНН, начинающимся с 77",
        "Покажи поручения с суммой платежа больше 100000 рублей в статусе Отправлен в рейс"
    ]
}

# Создаем вкладки для категорий
tabs = st.tabs(list(example_categories.keys()))

for tab_idx, (category, examples) in enumerate(example_categories.items()):
    with tabs[tab_idx]:
        st.caption(f"Всего примеров в категории: {len(examples)}")
        # Используем адаптивное количество колонок
        num_cols = min(3, len(examples))  # Максимум 3 колонки
        cols = st.columns(num_cols)
        for i, example in enumerate(examples):
            with cols[i % num_cols]:
                # Показываем полный текст примера
                if st.button(f"📝 {example}", key=f"example_{category}_{i}", use_container_width=True, help=example):
                    st.session_state.example_question = example
                    st.rerun()

# Статус системы
st.subheader("📊 Статус системы")
col1, col2, col3 = st.columns(3)

with col1:
    try:
        # Таймаут для проверки здоровья сервиса - короткий, так как это просто проверка
        health_check_timeout = int(os.getenv("HEALTH_CHECK_TIMEOUT", "10"))
        response = requests.get("http://localhost:3000/", timeout=health_check_timeout)
        if response.status_code == 200:
            st.success("✅ Simple UI (3000)")
        else:
            st.error(f"❌ Simple UI (3000) - HTTP {response.status_code}")
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Simple UI (3000) - {str(e)[:50]}")
    except Exception as e:
        st.error(f"❌ Simple UI (3000) - {str(e)[:50]}")

with col2:
    try:
        # Таймаут для проверки здоровья сервиса - короткий, так как это просто проверка
        health_check_timeout = int(os.getenv("HEALTH_CHECK_TIMEOUT", "10"))
        response = requests.get("http://localhost:8081/health", timeout=health_check_timeout)
        if response.status_code == 200:
            st.success("✅ Mock API (8081)")
        else:
            st.error("❌ Mock API (8081)")
    except:
        st.error("❌ Mock API (8081)")

with col3:
    st.success("✅ Streamlit (8501)")