#!/bin/bash
# 🚀 Запуск Core API и Mock API (базовые сервисы)
# Обертка над run_stack.sh для удобства использования

exec "$(dirname "$0")/run_stack.sh" start-core "$@"
