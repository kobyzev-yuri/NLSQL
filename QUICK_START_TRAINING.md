# 🚀 Быстрый старт обучения Vanna AI

## 📋 Что у нас есть:

### **1. Пайплайн обучения** 🤖
- `train_vanna_agent.py` - основной скрипт
- `src/vanna/training_pipeline.py` - пайплайн
- `src/vanna/training_script.py` - обучение
- `src/vanna/testing_script.py` - тестирование

### **2. Данные для обучения** 📊
- `src/vanna/training_data_preparation.py` - подготовка данных
- `training_data/` - директория с данными

### **3. Конфигурация** ⚙️
- `config.json` - настройки
- `quick_train.sh` - быстрый запуск

## 🚀 Запуск:

### **Вариант 1: Быстрый запуск**
```bash
./quick_train.sh
```

### **Вариант 2: Ручной запуск**
```bash
# Полный пайплайн
python train_vanna_agent.py

# Только подготовка данных
python train_vanna_agent.py --step prepare

# Только обучение
python train_vanna_agent.py --step train

# Только тестирование
python train_vanna_agent.py --step test
```

## 📊 Что происходит:

### **Этап 1: Подготовка данных** 📋
- Создается `training_data/ddl_statements.sql`
- Создается `training_data/documentation.md`
- Создается `training_data/sql_examples.json`
- Создается `training_data/metadata.json`

### **Этап 2: Обучение** 🤖
- Агент обучается на DDL структуре
- Агент обучается на документации
- Агент обучается на SQL примерах
- Агент обучается на метаданных

### **Этап 3: Тестирование** 🧪
- Тестируются базовые запросы
- Тестируются сложные запросы
- Тестируется обработка ошибок
- Генерируется отчет

## 🔧 Требования:

### **Зависимости:**
```bash
pip install -r requirements.txt
```

### **Ollama:**
```bash
# Установка
curl -fsSL https://ollama.ai/install.sh | sh

# Запуск
ollama serve

# Загрузка модели
ollama pull llama3.1:8b
```

### **PostgreSQL:**
```bash
# Проверка подключения
psql -h localhost -U postgres -d test_docstructure -c "SELECT 1;"
```

## 📁 Структура файлов:

```
sql4A/
├── train_vanna_agent.py              # Основной скрипт
├── config.json                       # Конфигурация
├── quick_train.sh                    # Быстрый запуск
├── VANNA_TRAINING_README.md          # Подробная документация
├── QUICK_START_TRAINING.md           # Эта инструкция
├── training_data/                    # Данные для обучения
│   ├── ddl_statements.sql
│   ├── documentation.md
│   ├── sql_examples.json
│   └── metadata.json
└── src/vanna/
    ├── training_pipeline.py          # Пайплайн
    ├── training_script.py            # Обучение
    ├── testing_script.py             # Тестирование
    └── training_data_preparation.py  # Подготовка данных
```

## 🎯 Результат:

После успешного обучения агент сможет:
- Генерировать SQL запросы на русском языке
- Понимать структуру базы данных
- Обрабатывать сложные запросы
- Работать с ролевыми ограничениями

## 🚨 Устранение неполадок:

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

### **Ошибка зависимостей:**
```bash
# Переустановка
pip install -r requirements.txt
```

## 📚 Дополнительно:

- Подробная документация: `VANNA_TRAINING_README.md`
- Конфигурация: `config.json`
- Логи обучения в консоли
