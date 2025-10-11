# Команды для ручной загрузки PostgreSQL дампа

## 🔧 **Проблема**
Файл `TradecoTemplateTestDB.sql` - это PostgreSQL custom-format dump, который нужно загружать через `pg_restore`, а не `psql`.

## 📋 **Команды для ручной загрузки**

### **1. Создание базы данных**
```bash
# Подключиться к PostgreSQL
sudo -u postgres psql

# Создать базу данных
CREATE DATABASE test_docstructure;

# Выйти
\q
```

### **2. Загрузка дампа**
```bash
# Загрузить дамп в базу данных
pg_restore -h localhost -p 5432 -U postgres -d test_docstructure --clean --if-exists TradecoTemplateTestDB.sql
```

### **3. Альтернативный способ (если нужен пароль)**
```bash
# Загрузить с запросом пароля
pg_restore -h localhost -p 5432 -U postgres -d test_docstructure --clean --if-exists --verbose TradecoTemplateTestDB.sql
```

### **4. Проверка загрузки**
```bash
# Подключиться к базе данных
sudo -u postgres psql -d test_docstructure

# Посмотреть список таблиц
\dt

# Посмотреть основные таблицы
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('equsers', 'eqdoctypes', 'eqdocstructure', 'tbl_business_unit', 'tbl_principal_assignment', 'tbl_incoming_payments')
ORDER BY table_name;

# Выйти
\q
```

## 🎯 **Одной командой**
```bash
# Создать базу и загрузить дамп
sudo -u postgres createdb test_docstructure && \
pg_restore -h localhost -p 5432 -U postgres -d test_docstructure --clean --if-exists TradecoTemplateTestDB.sql
```

## 🔍 **Проверка результата**
```bash
# Подсчитать таблицы
sudo -u postgres psql -d test_docstructure -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';"

# Показать основные таблицы
sudo -u postgres psql -d test_docstructure -c "\dt" | grep -E "(equsers|eqdoctypes|tbl_business_unit)"
```

## ⚠️ **Возможные проблемы**

### **Если ошибка доступа:**
```bash
# Проверить права доступа к файлу
ls -la TradecoTemplateTestDB.sql

# Проверить подключение к PostgreSQL
sudo -u postgres psql -c "SELECT version();"
```

### **Если ошибка формата:**
```bash
# Проверить формат файла
file TradecoTemplateTestDB.sql

# Должно показать: "PostgreSQL custom database dump"
```

## 🚀 **После успешной загрузки**

### **Подключение к базе:**
```bash
sudo -u postgres psql -d test_docstructure
```

### **Основные команды:**
```sql
-- Список таблиц
\dt

-- Структура таблицы
\d equsers

-- Количество записей в таблице
SELECT COUNT(*) FROM equsers;

-- Выход
\q
```
