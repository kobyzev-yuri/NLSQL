#!/bin/bash
# 🚀 Запуск Vector KB Interface
# Обертка над run_stack.sh для удобства использования
# Автоматически запускает core сервисы если они не запущены

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"

# Сначала убеждаемся, что core сервисы запущены
"$REPO_DIR/run_stack.sh" start-core >/dev/null 2>&1
sleep 1

# Запускаем Vector KB режим
exec "$REPO_DIR/run_stack.sh" start-vector-kb "$@"
