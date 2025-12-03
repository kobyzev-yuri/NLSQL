# Автоматическое обучение KB из материалов заказчика

## Назначение

Этот документ описывает процесс **автоматического обучения KB** на материалах, предоставленных заказчиком (дампах БД, документации, SQL примерах). Интерфейс используется для корректировки уже созданной KB, а не для первичного обучения.

## Workflow

```
┌─────────────────────────────────┐
│  Материалы заказчика:          │
│  - Дамп БД (SQL файл)          │
│  - Документация (текст/файлы)  │
│  - Примеры SQL запросов        │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│  Скрипты автоматического       │
│  обучения:                      │
│  - Извлечение DDL из дампа     │
│  - Парсинг документации        │
│  - Обработка SQL примеров      │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│  Core API (KBTrainingClient)   │
│  - /training/ddl                │
│  - /training/documentation      │
│  - /training/example            │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│  Векторная база знаний (KB)    │
│  - DDL statements               │
│  - Документация                 │
│  - Q/A пары                     │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│  Интерфейс (корректировка)      │
│  - Просмотр KB                  │
│  - Добавление примеров          │
│  - Оптимизация SQL              │
└─────────────────────────────────┘
```

## Автоматическое извлечение DDL

### Из дампа БД (SQL файл)

```python
from src.tools.kb_training_client import KBTrainingClient
import re

def extract_ddl_from_dump(dump_file: str):
    """Извлечение DDL statements из SQL дампа"""
    client = KBTrainingClient()
    
    with open(dump_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Ищем все CREATE TABLE statements
    create_table_pattern = r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:([^\s.]+)\.)?([^\s(]+)[^;]*;'
    matches = re.finditer(create_table_pattern, content, re.IGNORECASE | re.DOTALL)
    
    ddl_statements = []
    for match in matches:
        ddl = match.group(0)
        schema = match.group(1)
        table = match.group(2)
        table_name = f"{schema}.{table}" if schema else table
        
        ddl_statements.append({
            'ddl': ddl,
            'table_name': table_name,
            'source': 'database_dump',
            'version': None
        })
    
    # Добавляем через API
    result = client.add_ddl_statements(
        ddl_statements=ddl_statements,
        user_id="automatic_training"
    )
    
    return result
```

### Из INFORMATION_SCHEMA (активная БД)

```python
from src.adapters.postgresql_adapter import PostgreSQLAdapter
from src.tools.kb_training_client import KBTrainingClient

def extract_ddl_from_schema(database_url: str):
    """Извлечение DDL из INFORMATION_SCHEMA активной БД"""
    adapter = PostgreSQLAdapter(database_url)
    client = KBTrainingClient()
    
    # Получаем список таблиц
    tables = adapter.get_tables()
    
    ddl_statements = []
    for table in tables:
        # Получаем DDL для каждой таблицы
        ddl = adapter.get_table_ddl(table['name'])
        
        if ddl:
            ddl_statements.append({
                'ddl': ddl,
                'table_name': table['name'],
                'source': 'information_schema',
                'version': None
            })
    
    # Добавляем через API
    result = client.add_ddl_statements(
        ddl_statements=ddl_statements,
        user_id="automatic_training"
    )
    
    return result
```

## Автоматическое добавление документации

### Из текстовых файлов

```python
from src.tools.kb_training_client import KBTrainingClient
from pathlib import Path

def add_documentation_from_files(docs_dir: str):
    """Добавление документации из текстовых файлов"""
    client = KBTrainingClient()
    
    docs_path = Path(docs_dir)
    documents = []
    
    for doc_file in docs_path.glob("*.txt"):
        with open(doc_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        documents.append({
            'content': content,
            'title': doc_file.stem,
            'source': 'customer_docs',
            'domain': None,
            'tags': []
        })
    
    # Добавляем через API
    result = client.add_documentation(
        documents=documents,
        user_id="automatic_training"
    )
    
    return result
```

## Автоматическое добавление Q/A пар

### Из JSON файла с примерами SQL

```python
from src.tools.kb_training_client import KBTrainingClient
from pathlib import Path
import json

def add_qa_from_json(json_file: str):
    """Добавление Q/A пар из JSON файла"""
    client = KBTrainingClient()
    
    # Массовое добавление через унифицированный клиент
    stats = client.add_from_json_file(
        json_file=Path(json_file),
        user_id="automatic_training"
    )
    
    return stats
```

### Из логов SQL запросов

```python
from src.tools.kb_training_client import KBTrainingClient
import re

def extract_qa_from_logs(log_file: str):
    """Извлечение Q/A пар из логов SQL запросов"""
    client = KBTrainingClient()
    
    # Парсинг логов (пример)
    with open(log_file, 'r', encoding='utf-8') as f:
        logs = f.read()
    
    # Пример паттерна для извлечения SQL из логов
    sql_pattern = r'SELECT.*?;'
    sql_queries = re.findall(sql_pattern, logs, re.IGNORECASE | re.DOTALL)
    
    examples = []
    for sql in sql_queries:
        # Генерируем вопрос на основе SQL (можно использовать LLM)
        # Или использовать готовые пары из логов, если они есть
        examples.append({
            'question': f"SQL запрос: {sql[:50]}...",
            'sql': sql
        })
    
    # Добавляем через API
    stats = client.add_training_examples_batch(
        examples=examples,
        user_id="automatic_training"
    )
    
    return stats
```

## Полный скрипт автоматического обучения

```python
#!/usr/bin/env python3
"""
Скрипт автоматического обучения KB из материалов заказчика
"""

from src.tools.kb_training_client import KBTrainingClient
from pathlib import Path
import argparse

def main():
    parser = argparse.ArgumentParser(description="Автоматическое обучение KB")
    parser.add_argument("--ddl-dump", help="Путь к SQL дампу БД")
    parser.add_argument("--ddl-schema", help="Использовать INFORMATION_SCHEMA активной БД")
    parser.add_argument("--docs-dir", help="Директория с документацией")
    parser.add_argument("--qa-json", help="JSON файл с Q/A парами")
    parser.add_argument("--api-url", default="http://localhost:8000")
    
    args = parser.parse_args()
    
    client = KBTrainingClient(api_base_url=args.api_url)
    
    if not client.check_api_connection():
        print("❌ Core API недоступен")
        return
    
    # 1. Добавление DDL
    if args.ddl_dump:
        print("📝 Извлечение DDL из дампа...")
        # extract_ddl_from_dump(args.ddl_dump)
    
    if args.ddl_schema:
        print("📝 Извлечение DDL из INFORMATION_SCHEMA...")
        # extract_ddl_from_schema(args.ddl_schema)
    
    # 2. Добавление документации
    if args.docs_dir:
        print("📝 Добавление документации...")
        # add_documentation_from_files(args.docs_dir)
    
    # 3. Добавление Q/A пар
    if args.qa_json:
        print("📝 Добавление Q/A пар...")
        stats = client.add_from_json_file(
            json_file=Path(args.qa_json),
            user_id="automatic_training"
        )
        print(f"✅ Добавлено: {stats['success']}/{stats['total']}")
    
    print("✅ Автоматическое обучение завершено")
    print("💡 Теперь можно использовать интерфейс для корректировки KB")

if __name__ == "__main__":
    main()
```

## Использование интерфейса для корректировки

После автоматического обучения KB:

1. **Просмотр KB**: Откройте Vector KB Interface (http://localhost:8503)
2. **Проверка DDL**: Убедитесь, что все таблицы добавлены корректно
3. **Добавление примеров**: Добавьте недостающие Q/A пары через интерфейс
4. **Оптимизация SQL**: Отметьте оптимизированные SQL запросы
5. **Тестирование**: Проверьте качество KB через тестирование поиска

## Рекомендации

1. **Автоматическое обучение**: Используйте скрипты для первичного обучения на материалах заказчика
2. **Корректировка**: Используйте интерфейс для точечных улучшений и добавления примеров
3. **Версионирование**: Сохраняйте метаданные о источниках (source, version) для отслеживания изменений
4. **Логирование**: Проверяйте логи Core API для подтверждения успешного добавления

## См. также

- [KB_TRAINING_UNIFICATION.md](KB_TRAINING_UNIFICATION.md) - унификация обучения через API
- [TRAINING_GUIDE.md](TRAINING_GUIDE.md) - общее руководство по обучению
- [API_REFERENCE.md](API_REFERENCE.md) - описание API эндпоинтов




