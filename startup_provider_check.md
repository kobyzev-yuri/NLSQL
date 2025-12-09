# Автоматическая проверка и запуск LLM провайдера

## Проблема

При старте сервисов не проверялся `LLM_PROVIDER` из `config.env`, и если был выбран `ollama`, Ollama не запускался автоматически, что приводило к ошибкам подключения.

## Решение

Добавлена автоматическая проверка провайдера и запуск Ollama при необходимости в скрипт `run_stack.sh`.

### Добавленные функции

1. **`check_ollama()`** - проверяет, установлен ли Ollama
2. **`is_ollama_running()`** - проверяет, запущен ли Ollama (проверка порта 11434)
3. **`start_ollama()`** - запускает Ollama сервис
4. **`stop_ollama()`** - останавливает Ollama сервис
5. **`check_and_start_llm_provider()`** - проверяет `LLM_PROVIDER` и запускает Ollama если нужно

### Как это работает

1. При запуске сервисов (`start_web`, `start_vector_kb_mode`) вызывается `check_and_start_llm_provider()`
2. Функция читает `LLM_PROVIDER` из `config.env`
3. Если `LLM_PROVIDER=ollama`:
   - Проверяет, запущен ли Ollama
   - Если не запущен - запускает автоматически
   - Если уже запущен - пропускает
4. Если `LLM_PROVIDER=openai` (или другой):
   - Ollama не запускается

### Изменения в командах

#### `./run_stack.sh start` / `start-web`
- Теперь проверяет провайдер и запускает Ollama если нужно

#### `./run_stack.sh stop`
- Останавливает Ollama только если `LLM_PROVIDER=ollama`

#### `./run_stack.sh status`
- Показывает статус LLM провайдера
- Показывает статус Ollama (если используется)

## Примеры использования

### С OpenAI/GPT-4 (текущая конфигурация)

```bash
# config.env
LLM_PROVIDER=openai

# Запуск
./run_stack.sh start-web

# Вывод:
# 🔍 LLM Provider: openai
# 🤖 OpenAI/GPT-4 провайдер выбран (Ollama не требуется)
# === Starting core services ===
# ...
```

### С Ollama

```bash
# config.env
LLM_PROVIDER=ollama

# Запуск
./run_stack.sh start-web

# Вывод:
# 🔍 LLM Provider: ollama
# 🤖 Ollama провайдер выбран, проверяю Ollama...
#    Ollama не запущен, запускаю...
# [start] Ollama service
# [ok]   Ollama started (pid 12345)
# === Starting core services ===
# ...
```

## Гарантии

✅ **Один провайдер везде**: Все сервисы используют один `LLM_PROVIDER` из `config.env`

✅ **Автоматический запуск**: Если выбран Ollama, он запускается автоматически

✅ **Проверка статуса**: Команда `status` показывает, какой провайдер используется

✅ **Корректная остановка**: При остановке сервисов Ollama останавливается только если он использовался

## Текущий статус

- **LLM_PROVIDER**: `openai` (GPT-4o)
- **Ollama**: Не требуется, не запущен
- **Все сервисы**: Используют GPT-4o через ProxyAPI

