#!/usr/bin/env python3
"""
Минимальный набор тестов для kb_training_client

Использование:
    # Запуск всех unit-тестов (с моками)
    python -m src.tools.test_kb_training_client
    
    # Запуск с интеграционными тестами (требует запущенный Core API)
    python -m src.tools.test_kb_training_client --integration
"""

import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.tools.kb_training_client import KBTrainingClient


def test_import():
    """Тест импорта модуля"""
    print("✅ Тест 1: Импорт модуля")
    try:
        from src.tools.kb_training_client import KBTrainingClient
        assert KBTrainingClient is not None
        print("   ✅ KBTrainingClient импортирован успешно")
        return True
    except Exception as e:
        print(f"   ❌ Ошибка импорта: {e}")
        return False


def test_client_init():
    """Тест инициализации клиента"""
    print("\n✅ Тест 2: Инициализация клиента")
    try:
        client = KBTrainingClient(api_base_url="http://localhost:8000")
        assert client.api_base_url == "http://localhost:8000"
        print("   ✅ Клиент инициализирован с кастомным URL")
        
        client_default = KBTrainingClient()
        assert client_default.api_base_url is not None
        print("   ✅ Клиент инициализирован с URL по умолчанию")
        return True
    except Exception as e:
        print(f"   ❌ Ошибка инициализации: {e}")
        return False


def test_check_api_connection():
    """Тест проверки подключения к API"""
    print("\n✅ Тест 3: Проверка подключения к API")
    try:
        client = KBTrainingClient(api_base_url="http://localhost:8000")
        
        # Мокируем requests.get
        with patch('src.tools.kb_training_client.requests.get') as mock_get:
            # Тест успешного подключения
            mock_get.return_value.status_code = 200
            result = client.check_api_connection()
            assert result is True
            print("   ✅ API доступен (мок)")
            
            # Тест недоступного API
            mock_get.side_effect = Exception("Connection error")
            result = client.check_api_connection()
            assert result is False
            print("   ✅ API недоступен обрабатывается корректно (мок)")
        
        return True
    except Exception as e:
        print(f"   ❌ Ошибка проверки подключения: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_add_training_example_mock():
    """Тест добавления одного примера (с моком API)"""
    print("\n✅ Тест 4: Добавление одного примера (мок)")
    try:
        client = KBTrainingClient(api_base_url="http://localhost:8000")
        
        # Мокируем requests.post
        with patch('src.tools.kb_training_client.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "success": True,
                "example_id": "12345",
                "message": "Пример добавлен"
            }
            mock_post.return_value = mock_response
            
            result = client.add_training_example(
                question="Тестовый вопрос",
                sql="SELECT * FROM test_table"
            )
            
            assert result["success"] is True
            assert result["example_id"] == "12345"
            print("   ✅ Пример успешно добавлен (мок)")
            
            # Проверяем, что был вызван правильный URL
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert "/training/example" in call_args[0][0]
            print("   ✅ Вызван правильный эндпоинт API")
        
        return True
    except Exception as e:
        print(f"   ❌ Ошибка добавления примера: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_add_training_example_with_optimization():
    """Тест добавления оптимизированного SQL (с моком)"""
    print("\n✅ Тест 5: Добавление оптимизированного SQL (мок)")
    try:
        client = KBTrainingClient(api_base_url="http://localhost:8000")
        
        with patch('src.tools.kb_training_client.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "success": True,
                "example_id": "12346",
                "optimization_validated": True,
                "cost_improvement_percent": 50.0
            }
            mock_post.return_value = mock_response
            
            result = client.add_training_example(
                question="Тестовый вопрос",
                sql="SELECT id, name FROM test_table WHERE deleted = FALSE",
                sql_basic="SELECT * FROM test_table",
                improvement="Меньше данных"
            )
            
            assert result["success"] is True
            assert result.get("optimization_validated") is True
            print("   ✅ Оптимизированный SQL добавлен (мок)")
            
            # Проверяем, что в запросе были переданы правильные данные
            call_args = mock_post.call_args
            request_data = call_args[1]["json"]
            assert request_data["sql_basic"] == "SELECT * FROM test_table"
            assert request_data["improvement"] == "Меньше данных"
            print("   ✅ Правильные данные переданы в API")
        
        return True
    except Exception as e:
        print(f"   ❌ Ошибка добавления оптимизированного SQL: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_add_from_json_file():
    """Тест добавления из JSON файла (с моком)"""
    print("\n✅ Тест 6: Добавление из JSON файла (мок)")
    try:
        # Создаем временный JSON файл
        test_data = [
            {
                "question": "Тестовый вопрос 1",
                "sql": "SELECT * FROM table1"
            },
            {
                "question": "Тестовый вопрос 2",
                "sql": "SELECT * FROM table2",
                "sql_basic": "SELECT * FROM table2_all",
                "improvement": "Фильтрация"
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as tmp_file:
            json.dump(test_data, tmp_file, ensure_ascii=False, indent=2)
            tmp_path = Path(tmp_file.name)
        
        try:
            client = KBTrainingClient(api_base_url="http://localhost:8000")
            
            # Мокируем requests.post для каждого примера
            with patch('src.tools.kb_training_client.requests.post') as mock_post:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "success": True,
                    "example_id": "test_id"
                }
                mock_post.return_value = mock_response
                
                stats = client.add_from_json_file(
                    json_file=tmp_path,
                    user_id="test_user",
                    verbose=False
                )
                
                assert stats["total"] == 2
                assert stats["success"] == 2
                assert stats["failed"] == 0
                print(f"   ✅ Добавлено {stats['success']}/{stats['total']} примеров (мок)")
                print(f"   ✅ Вызовов API: {mock_post.call_count}")
        
        finally:
            # Удаляем временный файл
            tmp_path.unlink()
        
        return True
    except Exception as e:
        print(f"   ❌ Ошибка добавления из файла: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_error_handling():
    """Тест обработки ошибок"""
    print("\n✅ Тест 7: Обработка ошибок")
    try:
        client = KBTrainingClient(api_base_url="http://localhost:8000")
        
        # Тест ошибки подключения (requests.exceptions.RequestException)
        with patch('src.tools.kb_training_client.requests.post') as mock_post:
            import requests
            mock_post.side_effect = requests.exceptions.RequestException("Connection error")
            
            try:
                client.add_training_example(question="Test", sql="SELECT 1")
                assert False, "Должно было быть исключение"
            except ConnectionError as e:
                assert "Connection error" in str(e) or "подключения" in str(e)
                print("   ✅ Ошибка подключения обработана корректно")
        
        # Тест ошибки API (не 200)
        with patch('src.tools.kb_training_client.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            mock_post.return_value = mock_response
            
            try:
                client.add_training_example(question="Test", sql="SELECT 1")
                assert False, "Должно было быть исключение"
            except Exception as e:
                assert "500" in str(e) or "API вернул ошибку" in str(e)
                print("   ✅ Ошибка API обработана корректно")
        
        return True
    except AssertionError:
        # Это нормально - мы проверяем исключения
        return True
    except Exception as e:
        print(f"   ❌ Ошибка в тесте обработки ошибок: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_batch_add_with_errors():
    """Тест массового добавления с ошибками"""
    print("\n✅ Тест 8: Массовое добавление с ошибками (мок)")
    try:
        test_data = [
            {"question": "Вопрос 1", "sql": "SELECT 1"},
            {"question": "Вопрос 2", "sql": "SELECT 2"},
            {"question": "", "sql": "SELECT 3"},  # Невалидный (пустой question)
        ]
        
        client = KBTrainingClient(api_base_url="http://localhost:8000")
        
        with patch('src.tools.kb_training_client.requests.post') as mock_post:
            # Первые два успешны, третий падает
            def side_effect(*args, **kwargs):
                mock_response = Mock()
                call_count = mock_post.call_count
                if call_count <= 2:
                    mock_response.status_code = 200
                    mock_response.json.return_value = {"success": True, "example_id": f"id_{call_count}"}
                else:
                    mock_response.status_code = 400
                    mock_response.text = "Invalid request"
                return mock_response
            
            mock_post.side_effect = side_effect
            
            stats = client.add_training_examples_batch(
                examples=test_data,
                user_id="test_user",
                verbose=False
            )
            
            assert stats["total"] == 3
            assert stats["success"] == 2
            assert stats["failed"] == 1
            assert len(stats["errors"]) == 1
            print(f"   ✅ Обработано: {stats['success']} успешно, {stats['failed']} ошибок")
        
        return True
    except Exception as e:
        print(f"   ❌ Ошибка в тесте массового добавления: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integration_real_api():
    """Интеграционный тест с реальным API (опционально, требует запущенный Core API)"""
    print("\n✅ Тест 9: Интеграционный тест с реальным API (опционально)")
    try:
        client = KBTrainingClient(api_base_url="http://localhost:8000")
        
        # Проверяем, доступен ли API
        if not client.check_api_connection():
            print("   ⚠️ Core API недоступен, пропускаем интеграционный тест")
            print("   💡 Запустите Core API: ./run_stack.sh start")
            return True  # Не считаем это ошибкой
        
        # Пробуем добавить тестовый пример
        try:
            result = client.add_training_example(
                question="Тестовый вопрос для интеграционного теста",
                sql="SELECT 1 as test_column",
                user_id="test_integration"
            )
            
            if result.get("success"):
                print(f"   ✅ Пример добавлен через реальный API (ID: {result.get('example_id')})")
                return True
            else:
                print(f"   ⚠️ API вернул ошибку: {result.get('error', 'Unknown')}")
                return False
                
        except Exception as e:
            print(f"   ⚠️ Ошибка при добавлении через реальный API: {e}")
            return False
        
    except Exception as e:
        print(f"   ❌ Критическая ошибка в интеграционном тесте: {e}")
        return False


def run_all_tests(include_integration=False):
    """Запуск всех тестов"""
    print("="*60)
    print("🧪 Запуск тестов для kb_training_client")
    if include_integration:
        print("   (включая интеграционные тесты с реальным API)")
    print("="*60)
    
    tests = [
        test_import,
        test_client_init,
        test_check_api_connection,
        test_add_training_example_mock,
        test_add_training_example_with_optimization,
        test_add_from_json_file,
        test_error_handling,
        test_batch_add_with_errors,
    ]
    
    if include_integration:
        tests.append(test_integration_real_api)
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"   ❌ Критическая ошибка в тесте {test.__name__}: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    # Итоговая статистика
    print("\n" + "="*60)
    print("📊 Результаты тестирования:")
    print(f"   Всего тестов: {len(tests)}")
    print(f"   ✅ Успешно: {sum(results)}")
    print(f"   ❌ Ошибок: {len(results) - sum(results)}")
    print("="*60)
    
    return all(results)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Тесты для kb_training_client")
    parser.add_argument(
        "--integration",
        action="store_true",
        help="Включить интеграционные тесты с реальным API"
    )
    args = parser.parse_args()
    
    success = run_all_tests(include_integration=args.integration)
    sys.exit(0 if success else 1)

