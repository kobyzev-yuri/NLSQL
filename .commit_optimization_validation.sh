#!/bin/bash
# Скрипт для коммита изменений валидации оптимизации SQL

cd /mnt/ai/cnn/sql4A || exit 1

echo "📝 Добавляем изменения..."

# Добавляем измененные файлы
git add src/vanna/vanna_semantic_fixed.py
git add src/services/query_service.py
git add src/models/responses.py
git add src/api/main.py
git add docs/OPTIMIZATION_VALIDATION.md
git add docs/EXPLAIN_PLAN_USAGE_ANALYSIS.md
git add docs/OPTIMIZED_SQL_MARKING.md
git add docs/TEST_RESULTS.md
git add src/tools/test_optimized_sql_rag_hypothesis.py
git add QUICK_ADD_OPTIMIZED_SQL.md

echo "📋 Статус изменений:"
git status --short

echo ""
echo "💾 Создаем коммит..."

git commit -m "feat: добавлена валидация оптимизации SQL и маркировка [OPTIMIZED SQL]

- Добавлена автоматическая валидация: проверка что оптимизированный SQL лучше базового по cost
- Маркировка [OPTIMIZED SQL] в content для явной видимости агенту LLM
- Извлечение cost из EXPLAIN планов для сравнения производительности
- Сохранение метрик валидации в metadata (cost_basic, cost_optimized, improvement_percent)
- Предупреждения если оптимизированный SQL не лучше базового
- Обновлен API response с результатами валидации
- Добавлена документация: OPTIMIZATION_VALIDATION.md, EXPLAIN_PLAN_USAGE_ANALYSIS.md
- Создан тест гипотезы: test_optimized_sql_rag_hypothesis.py
- Обновлена документация по добавлению оптимизированных SQL"

echo ""
echo "✅ Коммит создан!"
echo ""
echo "📤 Для отправки на GitHub выполните:"
echo "   git push origin main"







