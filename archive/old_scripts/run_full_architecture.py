#!/usr/bin/env python3
"""
Скрипт для запуска полной архитектуры NL→SQL системы
Включает: FastAPI сервис, Mock Customer API, Веб-интерфейс
"""

import subprocess
import time
import signal
import sys
import os
from pathlib import Path

def run_command(command, name, port):
    """Запуск команды в фоновом режиме"""
    try:
        print(f"🚀 Запуск {name} на порту {port}...")
        logs_dir = Path("/mnt/ai/cnn/sql4A/logs")
        logs_dir.mkdir(parents=True, exist_ok=True)
        stdout_path = logs_dir / f"{name.replace(' ', '_').lower()}_{port}.out"
        stderr_path = logs_dir / f"{name.replace(' ', '_').lower()}_{port}.err"
        stdout_file = open(stdout_path, "ab", buffering=0)
        stderr_file = open(stderr_path, "ab", buffering=0)
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=stdout_file,
            stderr=stderr_file,
            preexec_fn=os.setsid if os.name != 'nt' else None
        )
        return process
    except Exception as e:
        print(f"❌ Ошибка запуска {name}: {e}")
        return None

def check_port(port):
    """Проверка доступности порта"""
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex(('localhost', port))
            return result == 0
    except:
        return False

def main():
    """Основная функция запуска"""
    print("🏗️ Запуск полной архитектуры NL→SQL системы...")
    print("=" * 60)
    
    # Список сервисов для запуска (uvicorn)
    services = [
        {
            "name": "Mock Customer API",
            "command": "cd /mnt/ai/cnn/sql4A && uvicorn src.mock_customer_api:mock_app --host 0.0.0.0 --port 8080",
            "port": 8080,
            "url": "http://localhost:8080"
        },
        {
            "name": "FastAPI NL→SQL Service", 
            "command": "cd /mnt/ai/cnn/sql4A && uvicorn src.api.main:app --host 0.0.0.0 --port 8000",
            "port": 8000,
            "url": "http://localhost:8000"
        },
        {
            "name": "Web Interface",
            "command": "cd /mnt/ai/cnn/sql4A && uvicorn src.web_interface:web_app --host 0.0.0.0 --port 3000", 
            "port": 3000,
            "url": "http://localhost:3000"
        }
    ]
    
    processes = []
    
    try:
        # Запуск всех сервисов
        for service in services:
            process = run_command(service["command"], service["name"], service["port"])
            if process:
                processes.append((process, service))
                print(f"✅ {service['name']} запущен (PID: {process.pid})")
            else:
                print(f"❌ Не удалось запустить {service['name']}")
                return
        
        print("\n⏳ Ожидание запуска сервисов...")
        time.sleep(5)
        
        # Проверка статуса сервисов
        print("\n📊 Проверка статуса сервисов:")
        for process, service in processes:
            if check_port(service["port"]):
                print(f"✅ {service['name']} - Работает ({service['url']})")
            else:
                print(f"❌ {service['name']} - Недоступен")
        
        print("\n🌐 Веб-интерфейс доступен по адресу: http://localhost:3000")
        print("📚 API документация: http://localhost:8000/docs")
        print("🔧 Mock API: http://localhost:8080")
        print("\n🛑 Для остановки нажмите Ctrl+C")
        
        # Ожидание завершения
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Остановка сервисов...")
        
        # Остановка всех процессов
        for process, service in processes:
            try:
                if os.name != 'nt':
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                else:
                    process.terminate()
                print(f"✅ {service['name']} остановлен")
            except:
                print(f"⚠️ Не удалось остановить {service['name']}")
        
        print("👋 Все сервисы остановлены")

if __name__ == "__main__":
    main()
