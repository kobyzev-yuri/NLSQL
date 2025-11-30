#!/usr/bin/env python3
"""
Скрипт для извлечения SQL запросов из DocStructureSchema и загрузки их как Q/A примеров
Извлекает SQL из представлений (EQView.json) и создает Q/A пары
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Добавляем путь к проекту
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.tools.kb_training_client import KBTrainingClient

# Загружаем переменные окружения
load_dotenv(dotenv_path=Path(__file__).parent.parent.parent / "config.env", override=True)

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


def extract_sql_from_views(views: List[Dict], doctypes: List[Dict]) -> List[Dict[str, Any]]:
    """Извлечение SQL запросов из представлений и создание Q/A пар"""
    qa_examples = []
    
    # Создаем маппинг doctype_id -> doctype_name для понимания контекста
    doctypes_map = {}
    for dt in doctypes:
        if dt.get('deleted') in (1, '1', True, 't'):
            continue
        dt_id = dt.get('id')
        dt_name = (dt.get('doctype') or '').strip()
        tablename = (dt.get('tablename') or '').strip()
        if dt_id:
            doctypes_map[dt_id] = {
                'name': dt_name,
                'table': tablename
            }
    
    for view in views:
        if view.get('deleted') in (1, '1', True, 't'):
            continue
        
        viewname = (view.get('viewname') or '').strip()
        parentid = view.get('parentid')
        sql_script = view.get('generated_sql_script') or view.get('default_sql_script')
        conditions = (view.get('conditions') or '').strip()
        
        if not sql_script or not sql_script.strip():
            continue
        
        # Очищаем SQL от лишних пробелов
        sql_script = ' '.join(sql_script.split())
        
        # Пропускаем пустые запросы
        if not sql_script or len(sql_script) < 10:
            continue
        
        # Формируем вопрос на основе названия представления и контекста
        doctype_info = doctypes_map.get(parentid) if parentid else None
        
        if doctype_info:
            doctype_name = doctype_info['name']
            table_name = doctype_info['table']
            
            # Формируем вопрос
            if viewname:
                question = f"Покажи данные из представления '{viewname}'"
                if doctype_name:
                    question += f" для типа документа '{doctype_name}'"
            elif doctype_name:
                question = f"Покажи данные для типа документа '{doctype_name}'"
            else:
                question = f"Покажи данные из таблицы {table_name}" if table_name else "Покажи данные"
        else:
            question = f"Покажи данные из представления '{viewname}'" if viewname else "Покажи данные"
        
        # Добавляем условия к SQL если они есть
        sql_query = sql_script
        if conditions:
            # Простое добавление WHERE если его еще нет
            if 'WHERE' not in sql_query.upper():
                sql_query += f" WHERE {conditions}"
            else:
                sql_query += f" AND {conditions}"
        
        # Нормализуем SQL (добавляем точку с запятой если нужно)
        if not sql_query.strip().endswith(';'):
            sql_query = sql_query.strip() + ';'
        
        qa_examples.append({
            'question': question,
            'sql': sql_query,
            'domain': 'views',
            'tags': ['view', 'docstructure'],
            'metadata': {
                'viewname': viewname,
                'view_id': view.get('id'),
                'parentid': parentid,
                'source': 'DocStructureSchema',
                'filename': 'EQView.json'
            }
        })
    
    return qa_examples


def extract_ddl_from_sql_file(sql_file: Path) -> List[Dict[str, Any]]:
    """Извлечение DDL из SQL файла"""
    ddl_statements = []
    
    if not sql_file.exists():
        print(f"⚠️ SQL файл не найден: {sql_file}")
        return ddl_statements
    
    try:
        # Читаем файл как бинарный и фильтруем нулевые байты
        with open(sql_file, 'rb') as f:
            binary_content = f.read()
        
        # Удаляем нулевые байты и другие непечатаемые символы (кроме переносов строк и табуляции)
        cleaned_content = binary_content.replace(b'\x00', b'')
        
        # Пытаемся декодировать как UTF-8
        try:
            content = cleaned_content.decode('utf-8', errors='ignore')
        except:
            # Если не получается, пробуем другие кодировки
            content = cleaned_content.decode('latin-1', errors='ignore')
        
        # Ищем CREATE TABLE statements
        create_table_pattern = r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:([^\s.]+)\.)?([^\s(]+)'
        
        # Разбиваем на отдельные statements по точке с запятой
        statements = re.split(r';\s*\n', content)
        
        for statement in statements:
            statement = statement.strip()
            if not statement:
                continue
            
            # Пропускаем слишком короткие или подозрительные statements
            if len(statement) < 20:
                continue
            
            # Пропускаем если содержит слишком много непечатаемых символов
            if len([c for c in statement if ord(c) < 32 and c not in '\n\r\t']) > len(statement) * 0.1:
                continue
            
            # Ищем CREATE TABLE
            if re.search(r'CREATE\s+TABLE', statement, re.IGNORECASE):
                match = re.search(create_table_pattern, statement, re.IGNORECASE)
                if match:
                    schema = match.group(1)
                    table = match.group(2)
                    table_name = f"{schema}.{table}" if schema else table
                    
                    # Очищаем statement от лишних символов
                    statement = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F]', '', statement)
                    
                    # Добавляем точку с запятой если нужно
                    if not statement.endswith(';'):
                        statement = statement.strip() + ';'
                    
                    ddl_statements.append({
                        'ddl': statement,
                        'table_name': table_name,
                        'source': 'TradecoTemplateTestDB',
                        'version': None,
                        'metadata': {
                            'filename': sql_file.name,
                            'source': 'DocStructureSchema'
                        }
                    })
        
        print(f"  - Найдено DDL statements: {len(ddl_statements)}")
        
    except Exception as e:
        print(f"⚠️ Ошибка чтения SQL файла: {e}")
    
    return ddl_statements


def main():
    """Основная функция"""
    print("🚀 Извлечение SQL запросов из DocStructureSchema")
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
    
    # 1. Извлекаем Q/A примеры из представлений
    print("📖 Извлечение Q/A примеров из представлений...")
    
    views_file = schema_dir / "EQView.json"
    doctypes_file = schema_dir / "EQDocTypes.json"
    
    views = load_json_file(views_file) if views_file.exists() else []
    doctypes = load_json_file(doctypes_file) if doctypes_file.exists() else []
    
    print(f"  - Загружено представлений: {len(views)}")
    print(f"  - Загружено типов документов: {len(doctypes)}")
    
    qa_examples = extract_sql_from_views(views, doctypes)
    print(f"  - Извлечено Q/A примеров: {len(qa_examples)}")
    print("")
    
    # 2. Извлекаем DDL из SQL файла
    print("📖 Извлечение DDL из SQL файла...")
    
    sql_file = Path("TradecoTemplateDBAndDocStructure") / "TradecoTemplateTestDB.sql"
    ddl_statements = extract_ddl_from_sql_file(sql_file)
    print("")
    
    # 3. Загружаем Q/A примеры
    if qa_examples:
        print(f"💾 Загрузка {len(qa_examples)} Q/A примеров...")
        
        stats = {
            'total': len(qa_examples),
            'success': 0,
            'failed': 0,
            'errors': []
        }
        
        for i, example in enumerate(qa_examples, 1):
            try:
                result = client.add_training_example(
                    question=example['question'],
                    sql=example['sql'],
                    domain=example.get('domain'),
                    tags=example.get('tags'),
                    user_id="extract_sql_from_docstructure"
                )
                
                if result.get('success'):
                    stats['success'] += 1
                    if i % 10 == 0:
                        print(f"  Обработано: {i}/{len(qa_examples)}")
                else:
                    stats['failed'] += 1
                    error_msg = result.get('error', 'Неизвестная ошибка')
                    stats['errors'].append(f"Пример #{i}: {error_msg}")
                    
            except Exception as e:
                stats['failed'] += 1
                stats['errors'].append(f"Пример #{i}: {str(e)}")
        
        print(f"  ✅ Успешно: {stats['success']}")
        print(f"  ❌ Ошибок: {stats['failed']}")
        if stats['errors']:
            print(f"  Первые ошибки:")
            for err in stats['errors'][:5]:
                print(f"    - {err}")
        print("")
    
    # 4. Загружаем DDL
    if ddl_statements:
        print(f"💾 Загрузка {len(ddl_statements)} DDL statements...")
        
        try:
            result = client.add_ddl_statements(
                ddl_statements=ddl_statements,
                user_id="extract_sql_from_docstructure"
            )
            
            if result.get('success'):
                print(f"  ✅ Добавлено: {result.get('added', 0)}")
                print(f"  🔄 Обновлено: {result.get('updated', 0)}")
                print(f"  ❌ Ошибок: {result.get('failed', 0)}")
            else:
                print(f"  ❌ Ошибка: {result.get('errors', [])}")
        except Exception as e:
            print(f"  ❌ Исключение: {e}")
        print("")
    
    # Итоги
    print("=" * 60)
    print("📊 Итоговая статистика:")
    if qa_examples:
        print(f"  Q/A примеров: {stats['success']}/{stats['total']} успешно загружено")
    if ddl_statements:
        print(f"  DDL statements: {len(ddl_statements)} обработано")
    print("=" * 60)
    print("")
    
    if (qa_examples and stats['failed'] == 0) or (not qa_examples and ddl_statements):
        print("✅ Извлечение завершено успешно!")
        print("")
        print("💡 Следующий шаг: сгенерируйте эмбеддинги:")
        print("   python -m src.tools.generate_embeddings_hf --dsn \"$DATABASE_URL\" --model \"$HF_MODEL_NAME\"")
    else:
        print("⚠️ Извлечение завершено с ошибками")
        if qa_examples and stats['failed'] > 0:
            sys.exit(1)


if __name__ == "__main__":
    main()

