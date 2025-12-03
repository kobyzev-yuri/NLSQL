# Руководство по переключению между Ollama и GPT

## Переключение через веб-интерфейс

### Simple Web Interface (http://localhost:3000)

1. Откройте веб-интерфейс
2. В форме генерации SQL найдите выпадающий список **"🤖 LLM Провайдер"**
3. Выберите нужный провайдер:
   - **GPT-4o (OpenAI/ProxyAPI)** - быстрая генерация через облачный API
   - **Qwen (Ollama локально)** - локальная генерация через Ollama

4. Введите вопрос и нажмите "🔍 Генерировать SQL"

### Streamlit Interface (http://localhost:8501)

Переключение провайдера в Streamlit интерфейсе пока не реализовано. Используйте Simple Web Interface или конфигурационный файл.

## Переключение через config.env

### Использовать Ollama

Отредактируйте `config.env`:
```env
LLM_PROVIDER=ollama
OLLAMA_MODEL=qwen2.5-coder:1.5b
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TEMPERATURE=0.2
```

Затем перезапустите сервисы:
```bash
./run_stack.sh restart core_api
./run_stack.sh restart simple_ui
```

### Использовать GPT-4o (OpenAI/ProxyAPI)

Отредактируйте `config.env`:
```env
LLM_PROVIDER=openai
OPENAI_MODEL=gpt-4o
OPENAI_BASE_URL=https://api.proxyapi.ru/openai/v1
OPENAI_TEMPERATURE=0.2
```

Затем перезапустите сервисы:
```bash
./run_stack.sh restart core_api
./run_stack.sh restart simple_ui
```

## Сравнение провайдеров

| Параметр | GPT-4o | Qwen (Ollama) |
|----------|--------|---------------|
| Скорость | ~2-5 сек | ~30-45 сек |
| Качество | Высокое | Хорошее |
| Стоимость | Платно | Бесплатно |
| Интернет | Требуется | Не требуется |
| Размер модели | N/A | 986 MB - 5.2 GB |

## Доступные модели Ollama

Проверьте доступные модели:
```bash
ollama ls
```

Рекомендуемые модели:
- `qwen2.5-coder:1.5b` - быстрая, легкая (986 MB)
- `qwen2.5:1.5b` - альтернатива (986 MB)
- `qwen3:8b` - более мощная, но медленная (5.2 GB)

## Устранение проблем

### Ollama не отвечает

1. Проверьте, что Ollama запущен:
```bash
curl http://localhost:11434/api/tags
```

2. Проверьте, что модель загружена:
```bash
ollama list | grep qwen
```

3. Если модель не загружена:
```bash
ollama pull qwen2.5-coder:1.5b
```

### Таймаут при генерации SQL

- Для Ollama таймаут увеличен до 120 секунд
- Если все еще таймаут, попробуйте более легкую модель (`qwen2.5-coder:1.5b`)

### Ошибка инициализации QueryService

Проверьте логи:
```bash
tail -50 logs/core_api_8000.out
```

Убедитесь, что:
- `config.env` правильно настроен
- Ollama доступен (если используете Ollama)
- API ключ OpenAI установлен (если используете OpenAI)

