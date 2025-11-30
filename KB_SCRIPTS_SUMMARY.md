# Скрипты для загрузки и индексации KB

## Основные скрипты

### 1. `src/tools/load_docstructure_schema.py`
**Назначение:** Загрузка документации из DocStructureSchema

Загружает структурированную документацию из JSON/XML файлов:
- Парсит `EQDocTypes.json`, `EQCategories.json`, `EQDocStates.json`
- Генерирует документацию по таблицам, бизнес-логике и связям
- Загружает через `KBTrainingClient` (API) с fallback на прямое добавление

**Использование:**
```bash
export $(cat config.env | grep -v '^#' | xargs)
python src/tools/load_docstructure_schema.py
```

---

### 2. `src/tools/extract_sql_from_docstructure.py`
**Назначение:** Извлечение SQL запросов и DDL

Извлекает:
- Q/A примеры из `EQView.json` (SQL из представлений)
- DDL statements из `TradecoTemplateTestDB.sql`

**Использование:**
```bash
export $(cat config.env | grep -v '^#' | xargs)
python src/tools/extract_sql_from_docstructure.py
```

---

### 3. `src/tools/generate_embeddings_hf.py`
**Назначение:** Генерация векторных эмбеддингов

Генерирует эмбеддинги для всех записей без них:
- Использует HuggingFace модели (например, `intfloat/multilingual-e5-base`)
- Поддерживает GPU (CUDA)
- Размерность: 768 для `multilingual-e5-base`

**Использование:**
```bash
export $(cat config.env | grep -v '^#' | xargs)
python -m src.tools.generate_embeddings_hf \
  --dsn "$DATABASE_URL" \
  --model "$HF_MODEL_NAME"
```

---

## Полный процесс пополнения KB

```bash
# 1. Загрузка документации
python src/tools/load_docstructure_schema.py

# 2. Извлечение SQL и DDL
python src/tools/extract_sql_from_docstructure.py

# 3. Генерация эмбеддингов
python -m src.tools.generate_embeddings_hf \
  --dsn "$DATABASE_URL" \
  --model "$HF_MODEL_NAME"
```

Подробнее см. [docs/KB_POPULATION_GUIDE.md](docs/KB_POPULATION_GUIDE.md)
