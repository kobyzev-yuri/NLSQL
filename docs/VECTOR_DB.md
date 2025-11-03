## Векторная база: структура и обучение

Этот модуль обеспечивает хранение контента (DDL, документация, Q/A) и семантический поиск для NL→SQL.

### 1) Архитектура и таблицы
- Основная таблица: `vanna_vectors`
- Рекомендуемая схема (pgvector):
```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS vanna_vectors (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    content_type VARCHAR(50) NOT NULL, -- 'ddl' | 'documentation' | 'question_sql'
    metadata JSONB,
    embedding vector(384),             -- или 1536 при использовании OpenAI
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Индексы для семантического поиска (пример IVF Flat)
CREATE INDEX IF NOT EXISTS vanna_vectors_embedding_ivf
ON vanna_vectors USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

CREATE INDEX IF NOT EXISTS vanna_vectors_type_idx
ON vanna_vectors (content_type);
```

Замечание: в текущем коде есть имплементации, где таблица создаётся без `embedding`. Для корректной работы семантического поиска из `vanna_semantic_fixed.py` и `src/services/query_service.py` (RAG) требуется столбец `embedding` и индекс. Добавьте его миграцией:
```sql
ALTER TABLE vanna_vectors ADD COLUMN IF NOT EXISTS embedding vector(384);
```

### 2) Откуда берутся данные
- DDL: из `INFORMATION_SCHEMA.COLUMNS` (см. `DocStructureVannaNative.get_training_plan_generic` и методы `add_ddl`)
- Документация: из внутренних текстов/файлов (метод `add_documentation`)
- Q/A пары: ручные и полуавтоматические примеры (метод `add_question_sql`)

Кодовые точки:
- `src/vanna/vanna_pgvector_native.py` (класс `DocStructureVectorDB` / `DocStructureVannaNative`):
  - `_create_vector_table()` (создание таблицы — при необходимости расширьте по образцу выше)
  - `add_ddl`, `add_documentation`, `add_question_sql` — запись контента
- `src/vanna/vanna_semantic_fixed.py` (семантический поиск):
  - ожидает `embedding` и использует pgvector `<->` cosine

### 3) Обучение/ингест
Шаги:
1. Создайте таблицу и индексы (см. DDL выше)
2. Сгенерируйте обучающий контент:
   - Схема БД → `train(plan=...)` из `DocStructureVannaNative`
   - Документация → `add_documentation`
   - Q/A → `add_question_sql`
3. Сгенерируйте эмбеддинги для записей и сохраните в `embedding`:
   - Используйте HF-модель `sentence-transformers/all-MiniLM-L6-v2` (размер 384)
   - Или OpenAI embeddings (размер 1536) — потребуется изменить размерность столбца

Практика генерации эмбеддингов:
- `src/tools/generate_embeddings_hf.py` — базовый скрипт для генерации/обновления `embedding` (адаптируйте под вашу схему)

### 4) Ретривер (семантический поиск)
Запросы вида:
```sql
SELECT content, embedding <-> $1::vector AS distance
FROM vanna_vectors
WHERE content_type = $2 AND embedding IS NOT NULL
ORDER BY embedding <-> $1::vector
LIMIT $3;
```
Используется в:
- `src/vanna/vanna_semantic_fixed.py` (асинхронные методы `get_related_ddl`, `get_related_documentation`, `get_similar_question_sql`)
- `src/services/query_service.py` (гибридные ретриверы для домена payments)

### 5) Текущие ограничения и TODO
- В некоторых местах `_create_vector_table()` создаёт таблицу без `embedding`; добавьте столбец и индекс миграцией (см. выше)
- Генерация эмбеддингов не всегда вызывается автоматически — запустите утилиту и/или встроите шаг в пайплайн обучения
- Размерность `embedding` должна совпадать с выбранной моделью (384 для HF miniLM, 1536 для OpenAI) во всех местах
- Настройте периодическую переиндексацию/обновление IVF параметров для больших массивов данных

### 6) Рекомендации по конфигурации
- См. `src/vanna/vector_db_configs.py` — готовые профили для pgvector/FAISS/ChromaDB
- Для pgvector: используйте cosine distance и IVF индекс с `lists ~ 100` (на старте), подбирайте эмпирически

### 7) Мини-контрольный список
- [ ] Установлен `pgvector`
- [ ] Таблица `vanna_vectors` содержит `embedding vector(d)`
- [ ] Есть ivfflat индекс по `embedding`
- [ ] Контент (ddl/documentation/question_sql) загружен
- [ ] Эмбеддинги сгенерированы и сохранены
- [ ] Семантический поиск возвращает релевантные результаты


