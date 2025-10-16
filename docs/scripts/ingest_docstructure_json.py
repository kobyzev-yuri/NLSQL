#!/usr/bin/env python3
"""
Ингест JSON из DocStructureSchema в векторную БД как documentation
- Добавляет filename и source в metadata
- Пропускает уже загруженные файлы (по имени)
"""

import os
import json
import logging
from pathlib import Path
import sys

_here = Path(__file__).resolve()
_repo_root = _here.parents[2]

import psycopg

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    base_dir = Path(__file__).parents[2]
    schema_dir = base_dir / 'DocStructureSchema'
    if not schema_dir.exists():
        logger.error(f"Нет директории: {schema_dir}")
        sys.exit(1)

    database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:1234@localhost:5432/test_docstructure')
    vector_table = os.getenv('VECTOR_TABLE', 'vanna_vectors')

    # Подключение к PostgreSQL
    try:
        conn = psycopg.connect(database_url)
    except Exception as e:
        logger.error(f"Не удалось подключиться к PostgreSQL: {e}")
        sys.exit(1)

    # Соберем уже загруженные файлы по маркеру в контенте
    existing_filenames = set()
    try:
        with conn.cursor() as cur:
            cur.execute(f"""
                SELECT content FROM {vector_table}
                WHERE content_type = 'documentation'
                  AND content LIKE '[DocStructureSchema:%]%' 
            """)
            for (content,) in cur.fetchall():
                # Извлекаем имя из префикса [DocStructureSchema:fname]
                if content.startswith('[DocStructureSchema:'):
                    end = content.find(']')
                    if end > 20:
                        marker = content[19:end]  # 'DocStructureSchema:' = 19 символов включая скобку?
                        # Скорректируем извлечение безопасно
                        try:
                            prefix = content[1:end]
                            # prefix == 'DocStructureSchema:fname'
                            parts = prefix.split(':', 1)
                            if len(parts) == 2:
                                existing_filenames.add(parts[1])
                        except Exception:
                            pass
    except Exception as e:
        logger.warning(f"Не удалось получить существующие DocStructure документы: {e}")

    added = 0
    skipped = 0

    for json_path in sorted(schema_dir.glob('*.json')):
        fname = json_path.name
        if fname in existing_filenames:
            skipped += 1
            continue
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Для улучшения поиска добавим короткий префикс с именем файла
            doc_text = f"[DocStructureSchema:{fname}]\n" + content

            metadata = json.dumps({
                'type': 'documentation',
                'source': 'DocStructureSchema',
                'filename': fname
            })

            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    INSERT INTO {vector_table} (content, content_type, metadata)
                    VALUES (%s, %s, %s)
                    RETURNING id
                    """,
                    (doc_text, 'documentation', metadata)
                )
                _ = cur.fetchone()
                conn.commit()
                added += 1
                logger.info(f"Добавлен: {fname}")
        except Exception as e:
            logger.error(f"Ошибка загрузки {fname}: {e}")

    print(f"✅ Ингест завершен. Добавлено: {added}, пропущено: {skipped}")
    try:
        conn.close()
    except Exception:
        pass


if __name__ == '__main__':
    main()


