# 🎯 План оптимизации интерфейса и chunking

> **Цель:** Адаптировать интерфейс для удобного документирования конкретной БД заказчиком и оптимизировать chunking для эффективного извлечения релевантных кусков для агента.

## 📋 Часть 1: Адаптация интерфейса для документирования БД

### Задача 1.1: Управление COMMENT ON TABLE/COLUMN

#### Текущее состояние:
- ✅ Реализован интерфейс для добавления COMMENT ON TABLE
- ✅ Реализован интерфейс для добавления COMMENT ON COLUMN
- ✅ Реализована визуализация существующих комментариев
- ✅ Добавлена статистика по комментариям
- ✅ Реализован поиск и фильтрация таблиц
- ✅ Оптимизирована загрузка колонок (только по запросу)

#### Требования:
1. **Список таблиц с индикацией комментариев**
   - Показать все таблицы из БД
   - Зеленый индикатор = есть комментарий
   - Красный индикатор = нет комментария
   - Сортировка: сначала без комментариев

2. **Форма для COMMENT ON TABLE**
   - Выбор таблицы из списка
   - Text area для комментария с подсветкой
   - Шаблоны комментариев (на основе примеров из CUSTOMER_DATA_PREPARATION_GUIDE.md)
   - Предпросмотр перед сохранением
   - Кнопка "Применить" → выполнение SQL

3. **Форма для COMMENT ON COLUMN**
   - Выбор таблицы → список колонок
   - Text area для комментария
   - Шаблоны для типичных случаев (FK, флаги, бизнес-логика)
   - Массовое добавление для нескольких колонок

4. **Статистика и отчеты**
   - Сколько таблиц с/без комментариев
   - Сколько колонок с/без комментариев
   - Экспорт списка таблиц без комментариев (CSV)
   - Прогресс-бар заполненности документации

#### Реализация:

**API эндпоинты (добавить в `src/api/endpoints.py`):**
```python
@router.get("/api/database/tables")
async def get_tables_with_comments():
    """Получить список всех таблиц с информацией о комментариях"""
    # SELECT table_name, 
    #        obj_description('public.'||table_name::regclass, 'pg_class') as table_comment
    # FROM information_schema.tables
    # WHERE table_schema = 'public'

@router.get("/api/database/tables/{table_name}/columns")
async def get_table_columns(table_name: str):
    """Получить список колонок таблицы с комментариями"""
    # SELECT column_name, data_type,
    #        col_description('public.'||table_name::regclass::oid, ordinal_position) as column_comment
    # FROM information_schema.columns
    # WHERE table_schema = 'public' AND table_name = $1

@router.post("/api/database/tables/{table_name}/comment")
async def add_table_comment(table_name: str, comment: str):
    """Добавить или обновить COMMENT ON TABLE"""
    # EXECUTE f"COMMENT ON TABLE public.{table_name} IS %s", comment

@router.post("/api/database/tables/{table_name}/columns/{column_name}/comment")
async def add_column_comment(table_name: str, column_name: str, comment: str):
    """Добавить или обновить COMMENT ON COLUMN"""
    # EXECUTE f"COMMENT ON COLUMN public.{table_name}.{column_name} IS %s", comment

@router.get("/api/database/comments/stats")
async def get_comments_statistics():
    """Получить статистику по комментариям"""
    # Возвращает: total_tables, tables_with_comments, total_columns, columns_with_comments
```

**Streamlit компонент (добавить в `src/vector_kb_interface.py`):**
```python
# Новая вкладка "📝 Документирование БД"
with tab_db_docs:
    st.header("📝 Документирование базы данных")
    
    # Статистика
    stats = call_api_get_comments_stats()
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Всего таблиц", stats['total_tables'])
    with col2:
        st.metric("С комментариями", stats['tables_with_comments'], 
                  delta=f"{stats['coverage_tables']:.1f}%")
    with col3:
        st.metric("Всего колонок", stats['total_columns'])
    with col4:
        st.metric("С комментариями", stats['columns_with_comments'],
                  delta=f"{stats['coverage_columns']:.1f}%")
    
    # Прогресс-бар
    st.progress(stats['coverage_tables'] / 100)
    st.caption(f"Прогресс документирования: {stats['coverage_tables']:.1f}%")
    
    # Список таблиц
    st.subheader("📋 Список таблиц")
    tables = call_api_get_tables_with_comments()
    
    # Фильтр: все / с комментариями / без комментариев
    filter_type = st.radio("Фильтр:", ["Все", "С комментариями", "Без комментариев"])
    
    # Таблица со списком
    for table in filtered_tables:
        has_comment = table['table_comment'] is not None
        icon = "✅" if has_comment else "❌"
        st.markdown(f"{icon} **{table['table_name']}**")
        if has_comment:
            with st.expander("Показать комментарий"):
                st.text(table['table_comment'])
        st.button("Редактировать", key=f"edit_{table['table_name']}")
    
    # Форма для добавления COMMENT ON TABLE
    st.subheader("➕ Добавить COMMENT ON TABLE")
    selected_table = st.selectbox("Таблица:", [t['name'] for t in tables])
    
    # Шаблоны комментариев
    template = st.selectbox("Шаблон:", [
        "Пустой",
        "Таблица пользователей",
        "Таблица платежей",
        "Таблица документов",
        "Справочник"
    ])
    
    if template != "Пустой":
        comment_template = get_comment_template(template, selected_table)
        st.text_area("Комментарий:", value=comment_template, height=200)
    
    if st.button("💾 Сохранить COMMENT ON TABLE"):
        # Вызов API
        pass
```

### Задача 1.2: Структурированная документация

#### Требования:
1. **Загрузка Markdown файлов**
   - Drag & drop или выбор файла
   - Валидация формата
   - Предпросмотр перед сохранением

2. **Генерация документации из БД**
   - Автоматическая генерация Markdown из COMMENT ON TABLE/COLUMN
   - Экспорт в файл
   - Формат: таблица → описание → колонки

3. **Редактор документации**
   - WYSIWYG редактор для Markdown
   - Предпросмотр
   - Сохранение в векторную БД

### Задача 1.3: Визуализация связей

#### Требования:
1. **Граф связей таблиц**
   - Визуализация FK связей
   - Интерактивный граф (networkx + plotly)
   - Показ таблиц с/без комментариев

2. **Статистика по доменам**
   - Группировка таблиц по доменам (users, payments, etc.)
   - Покрытие документацией по доменам

---

## 📊 Часть 2: Оптимизация chunking для эффективного извлечения

### Проблема текущего chunking:

1. **Большие чанки теряют релевантность:**
   - 10MB чанки содержат слишком много информации
   - Семантический поиск возвращает менее релевантные результаты

2. **Нет перекрытий:**
   - Контекст теряется на границах
   - Важная информация может быть разделена

3. **Нет учета структуры:**
   - DDL разбивается по символам, а не по таблицам
   - Документация разбивается без учета разделов

### Задача 2.1: Умное разбиение по типам контента

#### Для DDL:
```python
def chunk_ddl_smart(ddl_text: str) -> List[str]:
    """
    Разбивает DDL по таблицам, а не по символам
    Каждая таблица = отдельный чанк
    """
    chunks = []
    current_table = None
    current_ddl = []
    
    for line in ddl_text.splitlines():
        # Ищем CREATE TABLE
        if re.match(r'CREATE\s+TABLE', line, re.I):
            if current_table:
                chunks.append('\n'.join(current_ddl))
            current_table = line
            current_ddl = [line]
        elif line.strip().startswith('COMMENT ON'):
            # Комментарии добавляем к текущей таблице
            current_ddl.append(line)
        else:
            current_ddl.append(line)
    
    if current_ddl:
        chunks.append('\n'.join(current_ddl))
    
    return chunks
```

#### Для документации:
```python
def chunk_documentation_smart(doc_text: str, max_chars: int = 3000, overlap: int = 300) -> List[str]:
    """
    Разбивает документацию по разделам (заголовки Markdown)
    С перекрытиями для сохранения контекста
    """
    chunks = []
    
    # Разбиваем по заголовкам (## Section)
    sections = re.split(r'\n(##+\s+.+)\n', doc_text)
    
    current_chunk = []
    current_length = 0
    
    for section in sections:
        section_length = len(section)
        
        if current_length + section_length > max_chars and current_chunk:
            # Сохраняем текущий чанк
            chunk_text = '\n'.join(current_chunk)
            chunks.append(chunk_text)
            
            # Начинаем новый чанк с перекрытием
            overlap_text = '\n'.join(current_chunk[-overlap//50:]) if overlap > 0 else ""
            current_chunk = [overlap_text, section] if overlap_text else [section]
            current_length = len(overlap_text) + section_length
        else:
            current_chunk.append(section)
            current_length += section_length
    
    if current_chunk:
        chunks.append('\n'.join(current_chunk))
    
    return chunks
```

### Задача 2.2: Метаданные для лучшего поиска

#### Добавить метаданные в чанки:
```python
metadata = {
    'table_name': 'equsers',  # Для DDL
    'section': 'users',        # Для документации
    'chunk_index': 0,          # Индекс в последовательности
    'total_chunks': 5,         # Всего чанков
    'chunk_type': 'ddl',       # Тип чанка
    'keywords': ['users', 'departments', 'roles'],  # Ключевые слова
    'domain': 'users'          # Домен (users, payments, etc.)
}
```

### Задача 2.3: Приоритизация чанков

#### Веса для разных типов контента:
```python
CHUNK_WEIGHTS = {
    'ddl': 1.0,              # DDL - самый важный
    'documentation': 0.8,    # Документация - важна
    'question_sql': 0.9,     # Q/A пары - очень важны для примеров
    'schema_insights': 0.7   # Инсайты - полезны
}
```

#### Функция поиска с приоритизацией:
```python
async def search_with_priority(query: str, limit: int = 10) -> List[Dict]:
    """
    Поиск с учетом весов типов контента
    """
    results = await semantic_search(query, limit=limit * 2)  # Берем больше
    
    # Применяем веса
    for result in results:
        chunk_type = result.get('content_type', 'documentation')
        weight = CHUNK_WEIGHTS.get(chunk_type, 0.5)
        result['score'] = result['score'] * weight
    
    # Сортируем по взвешенному score
    results.sort(key=lambda x: x['score'], reverse=True)
    
    return results[:limit]
```

### Задача 2.4: Анализ эффективности chunking

#### Метрики для оценки:
1. **Recall@K** - сколько релевантных чанков найдено в топ-K
2. **Precision@K** - сколько из топ-K релевантны
3. **MRR (Mean Reciprocal Rank)** - средний ранг первого релевантного чанка
4. **Размер контекста** - сколько токенов в итоговом контексте
5. **Время поиска** - как быстро находится релевантный контент

#### Скрипт для тестирования:
```python
# src/tools/test_chunking_quality.py

async def test_chunking_quality():
    """
    Тестирует качество chunking на наборе вопросов
    """
    test_queries = [
        ("Покажи всех пользователей", ["equsers", "eq_departments"]),
        ("Сколько платежей поступило", ["tbl_incoming_payments"]),
        # ...
    ]
    
    results = []
    for query, expected_tables in test_queries:
        chunks = await search_with_priority(query, limit=10)
        
        # Проверяем, есть ли нужные таблицы в результатах
        found_tables = extract_tables_from_chunks(chunks)
        recall = len(set(found_tables) & set(expected_tables)) / len(expected_tables)
        
        results.append({
            'query': query,
            'recall': recall,
            'found_tables': found_tables,
            'expected_tables': expected_tables
        })
    
    return results
```

---

## 🚀 План реализации

### Фаза 1: Базовый интерфейс документирования (2-3 дня) ✅ ЗАВЕРШЕНО

**День 1:**
- [x] Добавить API эндпоинты для работы с комментариями
- [x] Реализовать получение списка таблиц с комментариями
- [x] Реализовать получение колонок таблицы

**День 2:**
- [x] Добавить форму для COMMENT ON TABLE
- [x] Добавить форму для COMMENT ON COLUMN
- [x] Реализовать сохранение комментариев в БД

**День 3:**
- [x] Добавить статистику и визуализацию
- [x] Добавить поиск и фильтрацию таблиц
- [x] Оптимизировать загрузку колонок (только по запросу)
- [x] Тестирование

### Фаза 2: Оптимизация chunking (3-4 дня)

**День 1:**
- [ ] Реализовать умное разбиение DDL по таблицам
- [ ] Реализовать умное разбиение документации по разделам
- [ ] Добавить перекрытия (overlap)

**День 2:**
- [ ] Добавить метаданные в чанки (table_name, domain, keywords)
- [ ] Реализовать приоритизацию чанков по типам
- [ ] Обновить поиск с учетом весов

**День 3:**
- [ ] Создать скрипт для пересоздания чанков с новыми параметрами
- [ ] Разбить существующие большие чанки (>8K)
- [ ] Тестирование на реальных данных

**День 4:**
- [ ] Создать скрипт для тестирования качества chunking
- [ ] Измерить метрики (Recall@K, Precision@K, MRR)
- [ ] Оптимизация параметров на основе метрик

### Фаза 3: Дополнительные функции (2-3 дня)

**День 1:**
- [ ] Визуализация графа связей таблиц
- [ ] Статистика по доменам
- [ ] Генерация документации из БД

**День 2:**
- [ ] Загрузка Markdown файлов
- [ ] WYSIWYG редактор документации
- [ ] Экспорт документации в файл

**День 3:**
- [ ] Интеграция всех функций в единый интерфейс
- [ ] Финальное тестирование
- [ ] Документация для пользователей

---

## 📊 Метрики успеха

### Для интерфейса документирования:
- ✅ 100% таблиц имеют COMMENT ON TABLE
- ✅ 80%+ ключевых колонок имеют COMMENT ON COLUMN
- ✅ Время добавления комментария < 2 минут
- ✅ Удобство использования (опрос пользователей)

### Для оптимизации chunking:
- ✅ Recall@10 > 0.8 (80% релевантных чанков в топ-10)
- ✅ Precision@10 > 0.7 (70% из топ-10 релевантны)
- ✅ MRR < 3 (первый релевантный чанк в топ-3)
- ✅ Размер контекста < 32K токенов
- ✅ Время поиска < 100ms

---

## 🔗 Связанные документы

- [CUSTOMER_DATA_PREPARATION_GUIDE.md](CUSTOMER_DATA_PREPARATION_GUIDE.md) - Инструкция для заказчика
- [CHUNKING_STRATEGY.md](CHUNKING_STRATEGY.md) - Стратегия chunking
- [CHUNKING_ANALYSIS.md](CHUNKING_ANALYSIS.md) - Анализ текущего состояния
- [INTERFACE_DATA_PREPARATION_COMPLIANCE.md](INTERFACE_DATA_PREPARATION_COMPLIANCE.md) - Соответствие требованиям

---

## 🎯 Предложения по дальнейшему развитию (важные и выполнимые)

### Приоритет 1: Улучшение UX интерфейса комментирования

#### 1. Экспорт списка таблиц без комментариев
- **Цель**: Помочь заказчику быстро найти таблицы, требующие документирования
- **Реализация**: Кнопка "📥 Экспорт CSV" в разделе статистики
- **Формат**: CSV с колонками: table_name, columns_count, last_modified
- **Оценка**: 1-2 часа

#### 2. Массовое редактирование комментариев
- **Цель**: Ускорить процесс документирования для похожих таблиц
- **Реализация**: Чекбоксы для выбора таблиц + кнопка "Применить шаблон"
- **Функционал**: Применить один шаблон комментария к нескольким таблицам
- **Оценка**: 2-3 часа

#### 3. История изменений комментариев
- **Цель**: Отслеживание изменений документации
- **Реализация**: Таблица `comment_history` с полями: table_name, comment_text, changed_by, changed_at
- **Интерфейс**: Показ истории в expander'е таблицы
- **Оценка**: 3-4 часа

### Приоритет 2: Интеграция с обучением RAG

#### 4. Автоматическое обновление векторки при изменении комментариев
- **Цель**: Синхронизация комментариев БД с векторной базой знаний
- **Реализация**: Триггер или фоновый процесс, который пересоздает эмбеддинги для измененных таблиц
- **Оценка**: 4-5 часов

#### 5. Предпросмотр влияния комментариев на RAG
- **Цель**: Показать, как комментарии улучшают качество поиска
- **Реализация**: Тестовый поиск до/после добавления комментариев
- **Интерфейс**: Кнопка "🔍 Тест влияния на поиск" в форме комментария
- **Оценка**: 3-4 часа

### Приоритет 3: Производительность и масштабируемость

#### 6. Кэширование списка таблиц
- **Цель**: Ускорить загрузку интерфейса при большом количестве таблиц
- **Реализация**: Использование `@st.cache_data` для списка таблиц
- **TTL**: 5 минут или инвалидация при изменении комментариев
- **Оценка**: 1 час

#### 7. Пагинация таблиц
- **Цель**: Улучшить производительность при 100+ таблицах
- **Реализация**: Показ по 20 таблиц на странице с кнопками "Следующие/Предыдущие"
- **Оценка**: 2 часа

---

**Дата создания:** 2025-11-04  
**Дата обновления:** 2025-11-11  
**Версия:** 1.1

