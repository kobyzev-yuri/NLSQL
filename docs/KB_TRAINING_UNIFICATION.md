# Унификация обучения векторной базы знаний

## Проблема

Ранее обучение KB выполнялось разными способами:
- **Интерфейс (vector_kb_interface.py)**: Использовал API `/training/example` → `QueryService.add_training_example()` → `semantic_vanna.add_question_sql()`
- **Скрипты (training_script.py)**: Использовали напрямую `DocStructureVannaNative` → `vanna.train()` или `vanna.add_question_sql()`

Это приводило к дублированию кода и разным путям выполнения одной и той же логики.

## Решение

Создан унифицированный клиент `src/tools/kb_training_client.py`, который:
- Использует единый API для всех операций обучения:
  - `/training/example` - для Q/A пар
  - `/training/ddl` - для DDL statements
  - `/training/documentation` - для документации
- Обеспечивает единообразие между интерфейсом и CLI скриптами
- Поддерживает массовое добавление из JSON файлов
- Автоматически генерирует EXPLAIN планы для оптимизированных SQL
- Транзакционность: все операции выполняются в транзакциях с откатом при ошибках
- Логирование изменений: при обновлении существующих записей логируются детали изменений

## Архитектура

```
┌─────────────────────┐
│  Vector KB UI      │──┐
│  (Streamlit 8503)   │  │
└─────────────────────┘  │
                         │  HTTP API
┌─────────────────────┐  │  /training/example
│  CLI Scripts        │──┼──▶  /training/ddl
│  kb_training_client │  │      /training/documentation
└─────────────────────┘  │      │
                         │      ▼
┌─────────────────────┐  │  Core API (8000)
│  training_script.py │──┘      │
│  (с fallback)       │          ▼
└─────────────────────┘     QueryService
                                   │
                    ┌──────────────┼──────────────┐
                    ▼              ▼              ▼
            add_training_  add_ddl_    add_documentation()
            example()      statements()
                    │              │              │
                    └──────────────┼──────────────┘
                                   ▼
                            semantic_vanna
                                   │
                                   ▼
                            PostgreSQL + pgvector
                            (vanna_vectors)
```

## Использование

### Через интерфейс (Vector KB UI)

1. **Ручное добавление**: Вкладка "Добавление новых Q/A пар" → использует API напрямую
2. **Массовое добавление**: Загрузите JSON файл → использует `KBTrainingClient` через API

### Через CLI скрипт

```bash
# Массовое добавление из JSON файла
python -m src.tools.kb_training_client --file data/training_data/sql_examples.json

# С указанием API URL
python -m src.tools.kb_training_client --file qa_pairs.json --api-url http://localhost:8000

# Тихий режим
python -m src.tools.kb_training_client --file examples.json --quiet
```

### Через Python API

```python
from src.tools.kb_training_client import KBTrainingClient

client = KBTrainingClient(api_base_url="http://localhost:8000")

# Добавление одного примера
result = client.add_training_example(
    question="Покажи всех пользователей",
    sql="SELECT id, login FROM equsers WHERE deleted = FALSE",
    sql_basic="SELECT * FROM equsers",
    improvement="Меньше данных, быстрее выполнение"
)

# Массовое добавление
stats = client.add_from_json_file(
    json_file=Path("data/training_data/sql_examples.json"),
    user_id="my_script"
)
```

## Формат JSON файла

```json
[
    {
        "question": "Покажи всех пользователей",
        "sql": "SELECT id, login, email FROM equsers WHERE deleted = FALSE",
        "sql_basic": "SELECT * FROM equsers",
        "sql_optimized": "SELECT id, login, email FROM equsers WHERE deleted = FALSE",
        "improvement": "50% меньше данных, быстрее выполнение",
        "domain": "users",
        "tags": ["optimization", "performance"]
    }
]
```

## Миграция существующих скриптов

### Старый способ (прямое использование vanna):

```python
from src.vanna.vanna_pgvector_native import DocStructureVannaNative

vanna = DocStructureVannaNative()
vanna.add_question_sql(question="...", sql="...")
```

### Новый способ (через унифицированный клиент):

```python
from src.tools.kb_training_client import KBTrainingClient

client = KBTrainingClient()
client.add_training_example(question="...", sql="...")
```

## Преимущества унификации

1. **Единообразие**: Все операции обучения используют один и тот же код через API
2. **Автоматическая генерация EXPLAIN планов**: Для оптимизированных SQL планы генерируются автоматически
3. **Валидация оптимизации**: Сравнение планов выполнения базового и оптимизированного SQL
4. **Централизованная логика**: Изменения в логике обучения применяются везде автоматически
5. **Удобство отладки**: Все операции логируются через Core API

## Обратная совместимость

Скрипт `training_script.py` обновлен для использования унифицированного клиента:
- Для Q/A пар: использует `KBTrainingClient` через API
- Для DDL и документации: использует прямое добавление через vanna (API не поддерживает эти типы)

Если API недоступен, скрипт автоматически переключается на прямое добавление (fallback).

## Следующие шаги

1. ✅ Создан унифицированный клиент `kb_training_client.py`
2. ✅ Обновлен `training_script.py` для использования клиента
3. ✅ Обновлен интерфейс для использования клиента при массовом добавлении
4. ⏳ Обновить другие скрипты обучения (если есть)
5. ⏳ Добавить эндпоинт для массового добавления (опционально, для производительности)

