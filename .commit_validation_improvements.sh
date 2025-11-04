#!/bin/bash
# Скрипт для коммита улучшений валидации оптимизации SQL

cd /mnt/ai/cnn/sql4A

echo "📦 Добавляем файлы для коммита..."

git add src/vanna/vanna_semantic_fixed.py \
         docs/OPTIMIZATION_VALIDATION.md \
         CORRECTED_SQL_QUERIES.md \
         src/api/main.py \
         src/vector_kb_interface.py \
         src/tools/check_table_columns.py \
         src/tools/check_payments_table.py

echo "✅ Файлы добавлены"

echo "📝 Создаем коммит..."

git commit -m "Улучшение валидации оптимизации SQL: проверка по cost, width и rows

- Улучшена логика валидации: проверка всех трех метрик (cost, width, rows)
- Валидация проходит если хотя бы одна метрика лучше (не только cost)
- Добавлено логирование улучшенных критериев в валидации
- Обновлена документация OPTIMIZATION_VALIDATION.md с примерами
- Добавлены инструменты check_table_columns.py и check_payments_table.py
- Улучшена обработка ошибок UndefinedColumnError с подсказками
- Обновлен CORRECTED_SQL_QUERIES.md с результатами валидации
- Улучшено логирование в API и интерфейсе"

echo "✅ Коммит создан!"

git log --oneline -1



