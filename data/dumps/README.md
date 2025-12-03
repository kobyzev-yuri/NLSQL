# Дампы векторной базы знаний

## vanna_vectors_dump.sql

Полный дамп таблицы `vanna_vectors` со всеми данными и эмбеддингами.

**Размер:** ~66MB (с эмбеддингами)

**Содержимое:**
- DDL statements (380 записей)
- Documentation (4,434 записи)
- Question_SQL примеры (471 запись)
- Векторные эмбеддинги для всех записей

**Восстановление:**
```bash
psql "$DATABASE_URL" < data/dumps/vanna_vectors_dump.sql
```

**Примечание:** После восстановления может потребоваться пересоздание индексов pgvector.

## Формирование дампа

Для создания нового дампа:

```bash
pg_dump "$DATABASE_URL" \
  -t vanna_vectors \
  --data-only \
  --inserts \
  --no-owner \
  --no-privileges \
  > data/dumps/vanna_vectors_dump.sql
```

## Версия дампа

- **Дата создания:** 2025-11-30
- **Версия KB:** После загрузки DocStructureSchema
- **Всего записей:** 5,285
- **С эмбеддингами:** 5,285 (100%)


