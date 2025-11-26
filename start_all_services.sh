#!/bin/bash
# 🚀 Запуск всех сервисов (Web режим)
# Обертка над run_stack.sh для удобства использования

exec "$(dirname "$0")/run_stack.sh" start-web "$@"
