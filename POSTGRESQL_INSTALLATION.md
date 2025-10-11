# Установка PostgreSQL и загрузка дампа DocStructureSchema

## 🐧 **Linux (Ubuntu/Debian)**

### **1. Установка PostgreSQL**

```bash
# Обновление пакетов
sudo apt update

# Установка PostgreSQL
sudo apt install postgresql postgresql-contrib

# Запуск службы
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Проверка статуса
sudo systemctl status postgresql
```

### **2. Настройка PostgreSQL**

```bash
# Переключение на пользователя postgres
sudo -u postgres psql

# Создание пользователя (если нужно)
CREATE USER cnn WITH PASSWORD '1234';
ALTER USER cnn CREATEDB;

# Выход
\q
```

### **3. Настройка аутентификации**

```bash
# Редактирование pg_hba.conf
sudo nano /etc/postgresql/*/main/pg_hba.conf

# Изменить строку:
# local   all             postgres                                peer
# на:
# local   all             postgres                                md5

# Перезапуск PostgreSQL
sudo systemctl restart postgresql
```

### **4. Загрузка дампа**

```bash
# Переход в директорию проекта
cd /mnt/ai/cnn/sql4A

# Запуск скрипта загрузки
chmod +x load_database.sh
./load_database.sh
```

---

## 🪟 **Windows**

### **1. Установка PostgreSQL**

#### **Способ 1: Официальный установщик**
1. Скачать с [postgresql.org](https://www.postgresql.org/download/windows/)
2. Запустить установщик
3. Выбрать компоненты: PostgreSQL Server, pgAdmin, Command Line Tools
4. Установить пароль для пользователя `postgres`
5. Выбрать порт (по умолчанию 5432)

#### **Способ 2: Chocolatey**
```cmd
# Установка Chocolatey (если не установлен)
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Установка PostgreSQL
choco install postgresql
```

### **2. Настройка PostgreSQL**

```cmd
# Добавление PostgreSQL в PATH (если не добавлен автоматически)
setx PATH "%PATH%;C:\Program Files\PostgreSQL\15\bin"

# Перезапуск командной строки
```

### **3. Проверка установки**

```cmd
# Проверка версии
psql --version

# Подключение к PostgreSQL
psql -U postgres
```

### **4. Загрузка дампа**

```cmd
# Переход в директорию проекта
cd C:\path\to\sql4A

# Запуск скрипта загрузки
load_database.bat
```

---

## 🔧 **Ручная загрузка дампа (если скрипты не работают)**

### **Linux/macOS:**

```bash
# 1. Создание базы данных
sudo -u postgres createdb test_docstructure

# 2. Загрузка дампа
pg_restore -h localhost -p 5432 -U postgres -d test_docstructure --clean --if-exists TradecoTemplateTestDB.sql

# 3. Проверка загрузки
sudo -u postgres psql -d test_docstructure -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';"
```

### **Windows:**

```cmd
REM 1. Создание базы данных
createdb -U postgres test_docstructure

REM 2. Загрузка дампа
pg_restore -h localhost -p 5432 -U postgres -d test_docstructure --clean --if-exists TradecoTemplateTestDB.sql

REM 3. Проверка загрузки
psql -U postgres -d test_docstructure -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';"
```

---

## 🐳 **Docker (альтернативный способ)**

### **1. Запуск PostgreSQL в Docker**

```bash
# Создание и запуск контейнера
docker run --name postgres-docstructure \
  -e POSTGRES_PASSWORD=1234 \
  -e POSTGRES_DB=test_docstructure \
  -p 5432:5432 \
  -d postgres:15

# Проверка запуска
docker ps
```

### **2. Загрузка дампа в Docker**

```bash
# Копирование дампа в контейнер
docker cp TradecoTemplateTestDB.sql postgres-docstructure:/tmp/

# Загрузка дампа
docker exec -it postgres-docstructure pg_restore -U postgres -d test_docstructure --clean --if-exists /tmp/TradecoTemplateTestDB.sql
```

---

## 🔍 **Проверка загрузки**

### **Подключение к базе данных:**

```bash
# Linux
sudo -u postgres psql -d test_docstructure

# Windows
psql -U postgres -d test_docstructure
```

### **Основные команды:**

```sql
-- Список таблиц
\dt

-- Количество таблиц
SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';

-- Основные таблицы
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('equsers', 'eqdoctypes', 'eqdocstructure', 'tbl_business_unit', 'tbl_principal_assignment', 'tbl_incoming_payments')
ORDER BY table_name;

-- Количество записей в основных таблицах
SELECT 'equsers' as table_name, COUNT(*) as row_count FROM equsers
UNION ALL
SELECT 'tbl_business_unit', COUNT(*) FROM tbl_business_unit
UNION ALL
SELECT 'tbl_principal_assignment', COUNT(*) FROM tbl_principal_assignment;

-- Выход
\q
```

---

## ⚠️ **Устранение проблем**

### **Ошибка подключения:**
```bash
# Проверка статуса службы
sudo systemctl status postgresql  # Linux
net start postgresql-x64-15        # Windows

# Проверка порта
netstat -an | grep 5432
```

### **Ошибка аутентификации:**
```bash
# Linux: проверка pg_hba.conf
sudo nano /etc/postgresql/*/main/pg_hba.conf

# Windows: проверка настроек в pgAdmin
```

### **Ошибка загрузки дампа:**
```bash
# Проверка формата файла
file TradecoTemplateTestDB.sql

# Должно показать: "PostgreSQL custom database dump"
```

### **Ошибка прав доступа:**
```bash
# Linux: проверка прав на файл
ls -la TradecoTemplateTestDB.sql

# Windows: запуск от имени администратора
```

---

## 📋 **Чек-лист установки**

### **Linux:**
- [ ] PostgreSQL установлен
- [ ] Служба запущена
- [ ] Пользователь postgres создан
- [ ] Пароль установлен
- [ ] Права доступа настроены
- [ ] Дамп загружен
- [ ] Таблицы созданы

### **Windows:**
- [ ] PostgreSQL установлен
- [ ] Служба запущена
- [ ] Пароль для postgres установлен
- [ ] PATH настроен
- [ ] Дамп загружен
- [ ] Таблицы созданы

---

## 🚀 **Следующие шаги**

После успешной загрузки дампа:

1. **Настройка переменных окружения:**
   ```bash
   export DATABASE_URL="postgresql://postgres:1234@localhost:5432/test_docstructure"
   ```

2. **Запуск NL→SQL системы:**
   ```bash
   python run_system.py
   ```

3. **Проверка работы:**
   - Веб-интерфейс: http://localhost:3000
   - API: http://localhost:8000/health

---

## 📚 **Полезные ссылки**

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [pg_restore Documentation](https://www.postgresql.org/docs/current/app-pgrestore.html)
- [PostgreSQL Windows Installation](https://www.postgresql.org/docs/current/install-windows.html)
- [Docker PostgreSQL](https://hub.docker.com/_/postgres)
