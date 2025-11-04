#!/bin/bash
# Быстрый тест EXPLAIN планов

cd "$(dirname "$0")"

echo "🧪 Запуск теста EXPLAIN планов для оптимизированных SQL..."
echo ""

python3 -m src.tools.test_optimized_sql_with_plan


