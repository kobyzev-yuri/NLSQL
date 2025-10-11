# 🤖 Пайплайн обучения Vanna AI агента

## 📋 Обзор

Пайплайн обучения Vanna AI агента для генерации SQL запросов на основе естественного языка для базы данных DocStructureSchema.

## 🏗️ Архитектура пайплайна

### **Этап 1: Подготовка данных** 📊
- **DDL statements** - структура базы данных
- **Документация** - описание таблиц и полей
- **SQL примеры** - примеры запросов с вопросами
- **Метаданные** - информация о таблицах и связях

### **Этап 2: Обучение агента** 🤖
- Обучение на DDL statements
- Обучение на документации
- Обучение на SQL примерах
- Обучение на метаданных

### **Этап 3: Тестирование** 🧪
- Тестирование базовых запросов
- Тестирование сложных запросов
- Тестирование обработки ошибок

## 🚀 Запуск пайплайна

### **Полный пайплайн:**
```bash
python train_vanna_agent.py
```

### **Отдельные этапы:**
```bash
# Только подготовка данных
python train_vanna_agent.py --step prepare

# Только обучение
python train_vanna_agent.py --step train

# Только тестирование
python train_vanna_agent.py --step test
```

### **С кастомной конфигурацией:**
```bash
python train_vanna_agent.py --config my_config.json --model ollama/llama3.1:8b
```

## ⚙️ Конфигурация

### **config.json:**
```json
{
  "database_url": "postgresql://postgres:1234@localhost:5432/test_docstructure",
  "vanna_model": "ollama/llama3.1:8b",
  "vector_db": "chromadb",
  "training_data_dir": "training_data",
  "test_questions": [
    "Покажи всех пользователей",
    "Сколько клиентов в системе?",
    "Покажи поручения за последний месяц"
  ]
}
```

## 📁 Структура данных для обучения

```
training_data/
├── ddl_statements.sql      # DDL структура БД
├── documentation.md        # Документация по БД
├── sql_examples.json      # Примеры SQL запросов
└── metadata.json          # Метаданные таблиц
```

## 🔧 Требования

### **Зависимости:**
- `vanna` - основной фреймворк
- `ollama` - для локальной модели
- `chromadb` - векторная база данных
- `psycopg2` - для PostgreSQL

### **Установка:**
```bash
pip install -r requirements.txt
```

### **Настройка Ollama:**
```bash
# Установка Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Запуск модели
ollama pull llama3.1:8b
ollama serve
```

## 📊 Мониторинг обучения

### **Логи:**
- Все этапы логируются в консоль
- Уровень логирования: INFO
- Формат: `timestamp - module - level - message`

### **Отчеты:**
- Отчет о тестировании: `test_report.json`
- Статистика обучения в логах

## 🧪 Тестирование

### **Базовые запросы:**
- "Покажи всех пользователей"
- "Сколько клиентов в системе?"
- "Покажи поручения за последний месяц"

### **Сложные запросы:**
- "Покажи пользователей с их отделами и ролями"
- "Статистика по поручениям по отделам за последний месяц"
- "Топ-10 клиентов по количеству поручений"

### **Обработка ошибок:**
- Несуществующие таблицы
- Непонятные запросы
- Сложные запросы с ошибками

## 🔍 Отладка

### **Проверка данных:**
```bash
# Проверка файлов данных
ls -la training_data/

# Проверка содержимого
cat training_data/ddl_statements.sql
cat training_data/documentation.md
```

### **Проверка модели:**
```bash
# Проверка Ollama
ollama list
ollama show llama3.1:8b
```

### **Проверка векторной БД:**
```bash
# Проверка ChromaDB
python -c "import chromadb; print('ChromaDB доступен')"
```

## 📈 Оптимизация

### **Настройки модели:**
- `temperature`: 0.1 (более детерминированные ответы)
- `max_tokens`: 4000 (достаточно для SQL)
- `top_p`: 0.9 (баланс креативности и точности)

### **Настройки векторной БД:**
- `distance_metric`: cosine (лучше для текста)
- `n_results`: 5 (достаточно контекста)

## 🚨 Устранение неполадок

### **Ошибка подключения к БД:**
```bash
# Проверка PostgreSQL
psql -h localhost -U postgres -d test_docstructure -c "SELECT 1;"
```

### **Ошибка модели:**
```bash
# Перезапуск Ollama
pkill ollama
ollama serve
```

### **Ошибка векторной БД:**
```bash
# Очистка ChromaDB
rm -rf chroma_db/
```

## 📚 Дополнительные ресурсы

- [Vanna AI Documentation](https://vanna.ai/docs/)
- [Ollama Documentation](https://ollama.ai/docs)
- [ChromaDB Documentation](https://docs.trychroma.com/)

## 🤝 Поддержка

При возникновении проблем:
1. Проверьте логи
2. Проверьте конфигурацию
3. Проверьте зависимости
4. Создайте issue в репозитории
