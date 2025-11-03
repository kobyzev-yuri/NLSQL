"""
Скрипт для запуска всей NL→SQL системы
Запускает все компоненты: NL→SQL API, Mock Customer API, Web Interface
"""

import subprocess
import time
import signal
import sys
import os
from pathlib import Path
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NLSystemRunner:
    """
    Класс для запуска всей NL→SQL системы
    """
    
    def __init__(self):
        self.processes = {}
        self.running = True
        
        # Обработчик сигналов для корректного завершения
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """
        Обработчик сигналов для корректного завершения
        """
        logger.info("Получен сигнал завершения, останавливаем все процессы...")
        self.running = False
        self.stop_all_processes()
        sys.exit(0)
    
    def start_nl_sql_api(self):
        """
        Запуск NL→SQL API сервера
        """
        logger.info("Запуск NL→SQL API сервера...")
        try:
            process = subprocess.Popen([
                sys.executable, "-m", "uvicorn", 
                "src.api.main:app", 
                "--host", "0.0.0.0", 
                "--port", "8000",
                "--reload"
            ], cwd=Path(__file__).parent)
            
            self.processes["nl_sql_api"] = process
            logger.info("NL→SQL API сервер запущен на http://localhost:8000")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка запуска NL→SQL API: {e}")
            return False
    
    def start_mock_customer_api(self):
        """
        Запуск Mock Customer API
        """
        logger.info("Запуск Mock Customer API...")
        try:
            process = subprocess.Popen([
                sys.executable, "-m", "uvicorn", 
                "src.mock_customer_api:mock_app", 
                "--host", "0.0.0.0", 
                "--port", "8080",
                "--reload"
            ], cwd=Path(__file__).parent)
            
            self.processes["mock_customer_api"] = process
            logger.info("Mock Customer API запущен на http://localhost:8080")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка запуска Mock Customer API: {e}")
            return False
    
    def start_web_interface(self):
        """
        Запуск веб-интерфейса
        """
        logger.info("Запуск веб-интерфейса...")
        try:
            process = subprocess.Popen([
                sys.executable, "-m", "uvicorn", 
                "src.web_interface:web_app", 
                "--host", "0.0.0.0", 
                "--port", "3000",
                "--reload"
            ], cwd=Path(__file__).parent)
            
            self.processes["web_interface"] = process
            logger.info("Веб-интерфейс запущен на http://localhost:3000")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка запуска веб-интерфейса: {e}")
            return False
    
    def prepare_training_data(self):
        """
        Подготовка данных для обучения Vanna AI
        """
        logger.info("Подготовка данных для обучения...")
        try:
            from src.vanna.training_data_preparation import VannaTrainingDataPreparator
            
            preparator = VannaTrainingDataPreparator()
            preparator.save_training_data("./training_data")
            
            logger.info("Данные для обучения подготовлены в ./training_data/")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка подготовки данных обучения: {e}")
            return False
    
    def start_all_services(self):
        """
        Запуск всех сервисов
        """
        logger.info("🚀 Запуск NL→SQL системы...")
        
        # Подготовка данных обучения
        self.prepare_training_data()
        
        # Запуск сервисов
        services = [
            ("NL→SQL API", self.start_nl_sql_api),
            ("Mock Customer API", self.start_mock_customer_api),
            ("Web Interface", self.start_web_interface)
        ]
        
        started_services = []
        
        for service_name, start_func in services:
            if start_func():
                started_services.append(service_name)
                time.sleep(2)  # Небольшая задержка между запусками
            else:
                logger.error(f"Не удалось запустить {service_name}")
        
        if started_services:
            logger.info(f"✅ Успешно запущены: {', '.join(started_services)}")
            self.print_system_info()
        else:
            logger.error("❌ Не удалось запустить ни одного сервиса")
            return False
        
        return True
    
    def print_system_info(self):
        """
        Вывод информации о запущенной системе
        """
        print("\n" + "="*60)
        print("🎉 NL→SQL СИСТЕМА ЗАПУЩЕНА!")
        print("="*60)
        print("\n📡 Доступные сервисы:")
        print("  • NL→SQL API:        http://localhost:8000")
        print("  • Mock Customer API: http://localhost:8080") 
        print("  • Web Interface:     http://localhost:3000")
        print("\n📚 Документация:")
        print("  • API Docs:          http://localhost:8000/docs")
        print("  • Mock API Docs:      http://localhost:8080/docs")
        print("\n🧪 Тестирование:")
        print("  • Веб-интерфейс:     http://localhost:3000")
        print("  • Проверка здоровья:  http://localhost:8000/health")
        print("\n💡 Примеры запросов:")
        print("  • 'Покажи всех пользователей'")
        print("  • 'Сколько клиентов в системе?'")
        print("  • 'Поручения за последний месяц'")
        print("\n⏹️  Для остановки нажмите Ctrl+C")
        print("="*60)
    
    def monitor_processes(self):
        """
        Мониторинг процессов
        """
        logger.info("Мониторинг процессов запущен...")
        
        while self.running:
            try:
                # Проверка статуса процессов
                for name, process in self.processes.items():
                    if process.poll() is not None:
                        logger.error(f"Процесс {name} завершился неожиданно")
                        self.running = False
                        break
                
                time.sleep(5)  # Проверка каждые 5 секунд
                
            except KeyboardInterrupt:
                logger.info("Получен сигнал прерывания")
                self.running = False
                break
    
    def stop_all_processes(self):
        """
        Остановка всех процессов
        """
        logger.info("Остановка всех процессов...")
        
        for name, process in self.processes.items():
            try:
                logger.info(f"Остановка {name}...")
                process.terminate()
                process.wait(timeout=10)
                logger.info(f"{name} остановлен")
            except subprocess.TimeoutExpired:
                logger.warning(f"Принудительная остановка {name}...")
                process.kill()
            except Exception as e:
                logger.error(f"Ошибка остановки {name}: {e}")
        
        logger.info("Все процессы остановлены")
    
    def run(self):
        """
        Основной метод запуска системы
        """
        try:
            # Запуск всех сервисов
            if not self.start_all_services():
                logger.error("Не удалось запустить систему")
                return False
            
            # Мониторинг процессов
            self.monitor_processes()
            
        except Exception as e:
            logger.error(f"Ошибка в основном цикле: {e}")
            return False
        finally:
            self.stop_all_processes()
        
        return True

def main():
    """
    Главная функция
    """
    print("🤖 NL→SQL System Runner")
    print("=" * 40)
    
    # Проверка зависимостей
    try:
        import uvicorn
        import httpx
        import fastapi
    except ImportError as e:
        print(f"❌ Отсутствуют зависимости: {e}")
        print("Установите зависимости: pip install -r requirements.txt")
        return False
    
    # Запуск системы
    runner = NLSystemRunner()
    return runner.run()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
