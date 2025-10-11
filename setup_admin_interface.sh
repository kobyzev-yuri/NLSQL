#!/bin/bash

# Скрипт для настройки веб-интерфейса администрирования PostgreSQL
# Автор: AI Assistant
# Дата: $(date)

set -e  # Остановка при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для вывода сообщений
print_message() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_message "Настройка веб-интерфейса для администрирования PostgreSQL"
print_message "================================================================"

# Проверка операционной системы
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
else
    print_error "Неподдерживаемая операционная система: $OSTYPE"
    exit 1
fi

print_message "Обнаружена ОС: $OS"

# Функция установки pgAdmin на Linux
install_pgadmin_linux() {
    print_message "Установка pgAdmin 4 на Linux..."
    
    # Обновление пакетов
    sudo apt update
    
    # Установка pgAdmin 4
    sudo apt install -y pgadmin4
    
    # Установка Apache (если не установлен)
    if ! command -v apache2 &> /dev/null; then
        print_message "Установка Apache..."
        sudo apt install -y apache2
    fi
    
    # Запуск Apache
    sudo systemctl start apache2
    sudo systemctl enable apache2
    
    print_success "pgAdmin 4 установлен и настроен"
    print_message "Доступ: http://localhost/pgadmin4"
}

# Функция установки phpPgAdmin на Linux
install_phppgadmin_linux() {
    print_message "Установка phpPgAdmin на Linux..."
    
    # Установка Apache, PHP и phpPgAdmin
    sudo apt install -y apache2 php php-pgsql phppgadmin
    
    # Настройка phpPgAdmin
    print_message "Настройка phpPgAdmin..."
    sudo sed -i "s/\$conf\['extra_login_security'\] = true;/\$conf['extra_login_security'] = false;/" /etc/phppgadmin/config.inc.php
    
    # Перезапуск Apache
    sudo systemctl restart apache2
    
    print_success "phpPgAdmin установлен и настроен"
    print_message "Доступ: http://localhost/phppgadmin"
}

# Функция запуска pgAdmin в Docker
start_pgadmin_docker() {
    print_message "Запуск pgAdmin в Docker..."
    
    # Проверка наличия Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker не установлен! Установите Docker и повторите попытку."
        exit 1
    fi
    
    # Остановка существующего контейнера (если есть)
    docker stop pgadmin 2>/dev/null || true
    docker rm pgadmin 2>/dev/null || true
    
    # Запуск pgAdmin в Docker
    docker run --name pgadmin \
        -e PGADMIN_DEFAULT_EMAIL=admin@example.com \
        -e PGADMIN_DEFAULT_PASSWORD=admin \
        -p 8080:80 \
        -d dpage/pgadmin4
    
    print_success "pgAdmin запущен в Docker"
    print_message "Доступ: http://localhost:8080"
    print_message "Email: admin@example.com"
    print_message "Пароль: admin"
}

# Функция проверки статуса
check_status() {
    print_message "Проверка статуса сервисов..."
    
    # Проверка PostgreSQL
    if systemctl is-active --quiet postgresql; then
        print_success "PostgreSQL: запущен"
    else
        print_warning "PostgreSQL: не запущен"
    fi
    
    # Проверка Apache
    if systemctl is-active --quiet apache2; then
        print_success "Apache: запущен"
    else
        print_warning "Apache: не запущен"
    fi
    
    # Проверка Docker
    if docker ps | grep -q pgadmin; then
        print_success "pgAdmin Docker: запущен"
    else
        print_warning "pgAdmin Docker: не запущен"
    fi
}

# Главное меню
show_menu() {
    echo ""
    print_message "Выберите вариант установки веб-интерфейса:"
    echo "1) pgAdmin 4 (рекомендуется)"
    echo "2) phpPgAdmin (через Apache)"
    echo "3) pgAdmin в Docker"
    echo "4) Проверить статус"
    echo "5) Выход"
    echo ""
    read -p "Введите номер варианта (1-5): " choice
}

# Основной цикл
while true; do
    show_menu
    
    case $choice in
        1)
            if [[ "$OS" == "linux" ]]; then
                install_pgadmin_linux
            else
                print_error "pgAdmin 4 для macOS требует ручной установки"
                print_message "Скачайте с https://www.pgadmin.org/download/"
            fi
            break
            ;;
        2)
            if [[ "$OS" == "linux" ]]; then
                install_phppgadmin_linux
            else
                print_error "phpPgAdmin для macOS требует ручной установки"
            fi
            break
            ;;
        3)
            start_pgadmin_docker
            break
            ;;
        4)
            check_status
            ;;
        5)
            print_message "Выход..."
            exit 0
            ;;
        *)
            print_error "Неверный выбор. Попробуйте снова."
            ;;
    esac
done

# Финальная информация
print_message "================================================================"
print_success "Веб-интерфейс настроен!"
print_message ""
print_message "Для подключения к базе данных используйте:"
print_message "Host: localhost"
print_message "Port: 5432"
print_message "Database: test_docstructure"
print_message "Username: postgres"
print_message "Password: 1234"
print_message ""
print_message "Полезные команды:"
print_message "- Проверка статуса: sudo systemctl status apache2"
print_message "- Перезапуск Apache: sudo systemctl restart apache2"
print_message "- Логи Apache: sudo tail -f /var/log/apache2/error.log"
print_message "================================================================"
