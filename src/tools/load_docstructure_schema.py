#!/usr/bin/env python3
"""
Скрипт для загрузки документации из data/DocStructureSchema в векторную базу знаний
Анализирует JSON файлы и создает структурированную документацию о таблицах, полях и бизнес-логике
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Добавляем путь к проекту
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.tools.kb_training_client import KBTrainingClient

# Загружаем переменные окружения
load_dotenv(dotenv_path=Path(__file__).parent.parent.parent / "config.env", override=True)

# Путь к директории с данными
DOCSTRUCTURE_DIR = os.getenv("DOCSTRUCTURE_DIR", "data/DocStructureSchema")


def load_json_file(file_path: Path) -> List[Dict[str, Any]]:
    """Загрузка JSON файла"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data if isinstance(data, list) else [data]
    except Exception as e:
        print(f"⚠️ Ошибка загрузки {file_path}: {e}")
        return []


def extract_table_info_from_doctypes(doctypes: List[Dict]) -> Dict[str, Dict]:
    """Извлечение информации о таблицах из типов документов"""
    tables = {}
    
    for doctype in doctypes:
        if doctype.get('deleted') in (1, '1', True, 't'):
            continue
            
        tablename = doctype.get('tablename')
        if not tablename:
            continue
            
        doctype_name = (doctype.get('doctype') or '').strip()
        category = (doctype.get('category') or '').strip()
        tooltip = (doctype.get('tooltip') or '').strip()
        
        if tablename not in tables:
            tables[tablename] = {
                'name': tablename,
                'doctypes': [],
                'categories': set(),
                'descriptions': []
            }
        
        tables[tablename]['doctypes'].append(doctype_name)
        if category:
            tables[tablename]['categories'].add(category)
        if tooltip:
            tables[tablename]['descriptions'].append(tooltip)
    
    # Преобразуем sets в lists для JSON сериализации
    for table in tables.values():
        table['categories'] = list(table['categories'])
    
    return tables


def extract_categories_info(categories: List[Dict]) -> Dict[str, str]:
    """Извлечение информации о категориях"""
    cat_info = {}
    
    for cat in categories:
        if cat.get('deleted') in (1, '1', True, 't'):
            continue
            
        cat_name = (cat.get('categoryname') or '').strip()
        description = (cat.get('description') or '').strip()
        tooltip = (cat.get('tooltip') or '').strip()
        
        if cat_name:
            desc_text = description or tooltip or ''
            if desc_text:
                cat_info[cat_name] = desc_text
    
    return cat_info


def extract_states_info(states: List[Dict]) -> Dict[str, List[Dict]]:
    """Извлечение информации о состояниях документов по типам"""
    states_by_doctype = {}
    
    for state in states:
        if state.get('deleted') in (1, '1', True, 't'):
            continue
            
        docid = state.get('docid')
        if not docid:
            continue
            
        statename = (state.get('statename') or '').strip()
        statedescription = (state.get('statedescription') or '').strip()
        
        if docid not in states_by_doctype:
            states_by_doctype[docid] = []
        
        states_by_doctype[docid].append({
            'name': statename,
            'code': statedescription
        })
    
    return states_by_doctype


def create_table_documentation(
    table_name: str,
    table_info: Dict,
    categories_info: Dict[str, str],
    states_by_doctype: Dict[str, List[Dict]],
    doctypes_map: Dict[str, Dict]
) -> str:
    """Создание документации для таблицы"""
    doc_parts = []
    
    doc_parts.append(f"## Таблица: {table_name}")
    doc_parts.append("")
    
    # Типы документов
    if table_info['doctypes']:
        doc_parts.append("### Типы документов:")
        for doctype_name in table_info['doctypes']:
            doc_parts.append(f"- {doctype_name}")
        doc_parts.append("")
    
    # Категории
    if table_info['categories']:
        doc_parts.append("### Категории:")
        for cat in table_info['categories']:
            cat_desc = categories_info.get(cat, '')
            if cat_desc:
                doc_parts.append(f"- {cat}: {cat_desc}")
            else:
                doc_parts.append(f"- {cat}")
        doc_parts.append("")
    
    # Описания
    if table_info['descriptions']:
        doc_parts.append("### Описание:")
        for desc in table_info['descriptions']:
            if desc:
                doc_parts.append(f"- {desc}")
        doc_parts.append("")
    
    # Состояния документов (если есть)
    doctype_ids = [dt_id for dt_id, dt_info in doctypes_map.items() 
                   if dt_info.get('tablename') == table_name]
    
    all_states = []
    for dt_id in doctype_ids:
        states = states_by_doctype.get(dt_id, [])
        all_states.extend(states)
    
    if all_states:
        doc_parts.append("### Возможные состояния:")
        unique_states = {}
        for state in all_states:
            code = state.get('code', '')
            if code and code not in unique_states:
                unique_states[code] = state.get('name', code)
        
        for code, name in sorted(unique_states.items()):
            doc_parts.append(f"- {name} ({code})")
        doc_parts.append("")
    
    return "\n".join(doc_parts)


def create_overview_documentation(
    tables: Dict[str, Dict],
    categories_info: Dict[str, str]
) -> str:
    """Создание общего обзора системы"""
    doc_parts = []
    
    doc_parts.append("# Система DocStructureSchema - Обзор")
    doc_parts.append("")
    doc_parts.append("Система управления документами и пользователями с настраиваемой структурой документов.")
    doc_parts.append("")
    
    # Группировка таблиц по категориям
    tables_by_category = {}
    for table_name, table_info in tables.items():
        for cat in table_info.get('categories', []):
            if cat not in tables_by_category:
                tables_by_category[cat] = []
            tables_by_category[cat].append({
                'name': table_name,
                'doctypes': table_info.get('doctypes', [])
            })
    
    # Основные категории
    doc_parts.append("## Основные категории и таблицы:")
    doc_parts.append("")
    
    for category, cat_tables in sorted(tables_by_category.items()):
        cat_desc = categories_info.get(category, '')
        doc_parts.append(f"### {category}")
        if cat_desc:
            doc_parts.append(f"{cat_desc}")
        doc_parts.append("")
        
        for table in cat_tables:
            table_name = table['name']
            doctypes = table.get('doctypes', [])
            if doctypes:
                doctype_list = ", ".join(doctypes[:3])  # Первые 3 типа
                if len(doctypes) > 3:
                    doctype_list += f" и еще {len(doctypes) - 3}"
                doc_parts.append(f"- **{table_name}**: {doctype_list}")
            else:
                doc_parts.append(f"- **{table_name}**")
        doc_parts.append("")
    
    # Статистика
    doc_parts.append("## Статистика:")
    doc_parts.append(f"- Всего таблиц: {len(tables)}")
    doc_parts.append(f"- Категорий: {len(tables_by_category)}")
    doc_parts.append("")
    
    return "\n".join(doc_parts)


def create_business_logic_documentation(
    tables: Dict[str, Dict],
    doctypes: List[Dict]
) -> str:
    """Создание документации о бизнес-логике"""
    doc_parts = []
    
    doc_parts.append("# Бизнес-логика системы DocStructureSchema")
    doc_parts.append("")
    
    # Основные таблицы системы
    system_tables = ['equsers', 'eq_departments', 'eqgroups', 'eqroles', 
                     'eqdoctypes', 'eqdocstructure', 'eqview', 'eqviewfields']
    
    doc_parts.append("## Системные таблицы:")
    doc_parts.append("")
    doc_parts.append("### Пользователи и права доступа:")
    doc_parts.append("- **equsers**: Пользователи системы (логин, email, отдел, права доступа)")
    doc_parts.append("- **eq_departments**: Отделы организации (название, родительский отдел)")
    doc_parts.append("- **eqgroups**: Группы пользователей")
    doc_parts.append("- **eqroles**: Роли системы")
    doc_parts.append("")
    
    doc_parts.append("### Документооборот:")
    doc_parts.append("- **eqdoctypes**: Типы документов (название типа, категория, связанная таблица)")
    doc_parts.append("- **eqdocstructure**: Структура полей документов (имя поля, тип, обязательность)")
    doc_parts.append("- **eqview**: Представления данных (название представления, условия)")
    doc_parts.append("- **eqviewfields**: Поля представлений")
    doc_parts.append("")
    
    # Бизнес-таблицы
    business_tables = {name: info for name, info in tables.items() 
                      if name not in system_tables and name.startswith('tbl_')}
    
    if business_tables:
        doc_parts.append("## Бизнес-таблицы:")
        doc_parts.append("")
        
        for table_name, table_info in sorted(business_tables.items()):
            doctypes = table_info.get('doctypes', [])
            if doctypes:
                doctype_list = ", ".join(doctypes[:2])
                doc_parts.append(f"- **{table_name}**: {doctype_list}")
            else:
                doc_parts.append(f"- **{table_name}**")
        doc_parts.append("")
    
    # Связи
    doc_parts.append("## Основные связи:")
    doc_parts.append("- Пользователи принадлежат отделам: `equsers.department → eq_departments.id`")
    doc_parts.append("- Типы документов связаны с таблицами: `eqdoctypes.tablename → <table_name>`")
    doc_parts.append("- Структура полей связана с типами документов: `eqdocstructure.doctypeid → eqdoctypes.id`")
    doc_parts.append("- Представления используют поля: `eqviewfields.viewid → eqview.id`")
    doc_parts.append("")
    
    return "\n".join(doc_parts)


def main():
    """Основная функция загрузки"""
    print("🚀 Начало загрузки документации из DocStructureSchema")
    print(f"📁 Директория: {DOCSTRUCTURE_DIR}")
    print("")
    
    # Проверяем существование директории
    schema_dir = Path(DOCSTRUCTURE_DIR)
    if not schema_dir.exists():
        print(f"❌ Ошибка: Директория {DOCSTRUCTURE_DIR} не найдена")
        sys.exit(1)
    
    # Инициализируем клиент
    client = KBTrainingClient()
    
    if not client.check_api_connection():
        print(f"❌ Ошибка: Core API недоступен на {client.api_base_url}")
        print("💡 Убедитесь, что сервис запущен: ./run_stack.sh start core_api")
        sys.exit(1)
    
    print("✅ Подключение к API установлено")
    print("")
    
    # Загружаем JSON файлы
    print("📖 Загрузка JSON файлов...")
    
    doctypes_file = schema_dir / "EQDocTypes.json"
    categories_file = schema_dir / "EQCategories.json"
    states_file = schema_dir / "EQDocStates.json"
    
    doctypes = load_json_file(doctypes_file) if doctypes_file.exists() else []
    categories = load_json_file(categories_file) if categories_file.exists() else []
    states = load_json_file(states_file) if states_file.exists() else []
    
    print(f"  - EQDocTypes: {len(doctypes)} записей")
    print(f"  - EQCategories: {len(categories)} записей")
    print(f"  - EQDocStates: {len(states)} записей")
    print("")
    
    # Извлекаем информацию
    print("🔍 Извлечение информации...")
    
    tables = extract_table_info_from_doctypes(doctypes)
    categories_info = extract_categories_info(categories)
    states_by_doctype = extract_states_info(states)
    
    # Создаем маппинг doctype_id -> doctype_info
    doctypes_map = {dt.get('id'): dt for dt in doctypes if dt.get('id')}
    
    print(f"  - Найдено таблиц: {len(tables)}")
    print(f"  - Категорий: {len(categories_info)}")
    print("")
    
    # Создаем документы
    print("📝 Формирование документации...")
    
    documents = []
    
    # 1. Общий обзор
    overview_doc = create_overview_documentation(tables, categories_info)
    documents.append({
        'content': overview_doc,
        'title': 'DocStructureSchema - Обзор системы',
        'source': 'DocStructureSchema',
        'domain': 'system',
        'tags': ['overview', 'system'],
        'metadata': {
            'filename': 'overview.md',
            'type': 'overview'
        }
    })
    
    # 2. Бизнес-логика
    business_logic_doc = create_business_logic_documentation(tables, doctypes)
    documents.append({
        'content': business_logic_doc,
        'title': 'DocStructureSchema - Бизнес-логика',
        'source': 'DocStructureSchema',
        'domain': 'system',
        'tags': ['business_logic', 'relationships'],
        'metadata': {
            'filename': 'business_logic.md',
            'type': 'business_logic'
        }
    })
    
    # 3. Документация по каждой таблице
    for table_name, table_info in sorted(tables.items()):
        table_doc = create_table_documentation(
            table_name,
            table_info,
            categories_info,
            states_by_doctype,
            doctypes_map
        )
        
        documents.append({
            'content': table_doc,
            'title': f'Таблица {table_name}',
            'source': 'DocStructureSchema',
            'domain': 'tables',
            'tags': table_info.get('categories', []) + ['table', table_name],
            'metadata': {
                'filename': f'{table_name}.md',
                'type': 'table_documentation',
                'table_name': table_name
            }
        })
    
    print(f"  - Создано документов: {len(documents)}")
    print("")
    
    # Загружаем в векторную базу
    print("💾 Загрузка в векторную базу...")
    
    # Разбиваем на батчи для избежания перегрузки
    batch_size = 10
    total_added = 0
    total_updated = 0
    total_failed = 0
    
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (len(documents) + batch_size - 1) // batch_size
        
        print(f"  Батч {batch_num}/{total_batches} ({len(batch)} документов)...")
        
        try:
            result = client.add_documentation(
                documents=batch,
                user_id="load_docstructure_schema"
            )
            
            if result.get('success'):
                added = result.get('added', 0)
                updated = result.get('updated', 0)
                failed = result.get('failed', 0)
                
                total_added += added
                total_updated += updated
                total_failed += failed
                
                print(f"    ✅ Добавлено: {added}, Обновлено: {updated}, Ошибок: {failed}")
            else:
                errors = result.get('errors', [])
                print(f"    ❌ Ошибка батча: {errors[:3]}")
                total_failed += len(batch)
                
        except Exception as e:
            print(f"    ❌ Исключение: {e}")
            total_failed += len(batch)
    
    print("")
    print("=" * 60)
    print("📊 Итоговая статистика:")
    print(f"  Всего документов: {len(documents)}")
    print(f"  ✅ Добавлено: {total_added}")
    print(f"  🔄 Обновлено: {total_updated}")
    print(f"  ❌ Ошибок: {total_failed}")
    print("=" * 60)
    print("")
    
    if total_failed == 0:
        print("✅ Загрузка завершена успешно!")
        print("")
        print("💡 Следующий шаг: сгенерируйте эмбеддинги:")
        print("   python -m src.tools.generate_embeddings_hf --dsn \"$DATABASE_URL\" --model \"$HF_MODEL_NAME\"")
    else:
        print("⚠️ Загрузка завершена с ошибками")
        sys.exit(1)


if __name__ == "__main__":
    main()

