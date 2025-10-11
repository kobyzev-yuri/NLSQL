# 🚀 Быстрая настройка pgAdmin

## ⚡ **Самый простой способ (Docker)**

```bash
# Запуск pgAdmin в Docker (1 команда)
docker run --name pgadmin \
  -e PGADMIN_DEFAULT_EMAIL=admin@example.com \
  -e PGADMIN_DEFAULT_PASSWORD=admin \
  -p 8080:80 \
  -d dpage/pgadmin4

# Доступ: http://localhost:8080
# Email: admin@example.com
# Пароль: admin
```

## 🐧 **Linux (Ubuntu/Debian)**

```bash
# Автоматическая настройка
chmod +x setup_admin_interface.sh
./setup_admin_interface.sh

# Или вручную:
sudo apt install pgadmin4 apache2
sudo systemctl start apache2
# Доступ: http://localhost/pgadmin4
```

## 🪟 **Windows**

1. Скачать pgAdmin 4 с https://www.pgadmin.org/download/
2. Установить
3. Запустить pgAdmin 4
4. Доступ: http://localhost:5050

## 🔧 **Настройка подключения к базе данных**

### **Параметры подключения:**
- **Host:** localhost
- **Port:** 5432
- **Database:** test_docstructure
- **Username:** postgres
- **Password:** 1234

### **Пошаговая настройка в pgAdmin:**

1. **Открыть pgAdmin** (http://localhost:8080 или http://localhost/pgadmin4)
2. **Войти** с учетными данными
3. **Правый клик** на "Servers" → "Create" → "Server"
4. **General tab:**
   - Name: `DocStructureSchema`
5. **Connection tab:**
   - Host: `localhost`
   - Port: `5432`
   - Database: `test_docstructure`
   - Username: `postgres`
   - Password: `1234`
6. **Save** - подключение готово!

## 🎯 **Проверка подключения**

После настройки вы должны увидеть:
- База данных `test_docstructure`
- Таблицы: `equsers`, `tbl_business_unit`, `tbl_principal_assignment`, и др.
- ~200 таблиц в общей сложности

## 🚨 **Устранение проблем**

### **Ошибка подключения:**
```bash
# Проверить, что PostgreSQL запущен
sudo systemctl status postgresql

# Проверить порт
netstat -an | grep 5432
```

### **Ошибка Docker:**
```bash
# Проверить статус контейнера
docker ps | grep pgadmin

# Перезапустить контейнер
docker restart pgadmin
```

### **Ошибка Apache:**
```bash
# Проверить статус Apache
sudo systemctl status apache2

# Перезапустить Apache
sudo systemctl restart apache2
```

## 📋 **Быстрые команды**

```bash
# Запуск pgAdmin в Docker
docker run --name pgadmin -e PGADMIN_DEFAULT_EMAIL=admin@example.com -e PGADMIN_DEFAULT_PASSWORD=admin -p 8080:80 -d dpage/pgadmin4

# Остановка pgAdmin
docker stop pgadmin

# Удаление pgAdmin
docker rm pgadmin

# Проверка статуса
docker ps | grep pgadmin
```

## 🎉 **Готово!**

После настройки у вас будет:
- ✅ Веб-интерфейс для администрирования PostgreSQL
- ✅ Возможность просматривать таблицы и данные
- ✅ Выполнение SQL запросов
- ✅ Управление базой данных

**Доступ:** http://localhost:8080 (Docker) или http://localhost/pgadmin4 (Linux)
