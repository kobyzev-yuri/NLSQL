#!/usr/bin/env python3
"""
Скрипт для запуска веб-интерфейса NL-to-SQL системы
"""

import sys
import os
from pathlib import Path

# Добавляем путь к модулям
sys.path.append(str(Path(__file__).parent))

# Импортируем и запускаем веб-интерфейс
from src.simple_web_interface import app
import uvicorn

if __name__ == "__main__":
    print("🚀 Запуск веб-интерфейса NL-to-SQL системы...")
    print("📱 Откройте браузер и перейдите по адресу: http://localhost:3000")
    print("🛑 Для остановки нажмите Ctrl+C")
    
    uvicorn.run(app, host="0.0.0.0", port=3000, log_level="info")
