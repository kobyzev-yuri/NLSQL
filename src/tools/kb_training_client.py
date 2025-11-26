#!/usr/bin/env python3
"""
Унифицированный клиент для обучения векторной базы знаний
Использует Core API для всех операций, обеспечивая единообразие с интерфейсом
"""

import os
import sys
import json
import asyncio
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / "config.env", override=True)

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


class KBTrainingClient:
    """
    Клиент для обучения векторной базы знаний через Core API
    """
    
    def __init__(self, api_base_url: str = None):
        """
        Инициализация клиента
        
        Args:
            api_base_url: Базовый URL Core API (по умолчанию из env или http://localhost:8000)
        """
        self.api_base_url = api_base_url or API_BASE_URL
    
    def check_api_connection(self) -> bool:
        """Проверка подключения к API"""
        try:
            response = requests.get(f"{self.api_base_url}/health", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def add_training_example(
        self,
        question: str,
        sql: str,
        user_id: str = "kb_training_client",
        verified: bool = True,
        sql_basic: Optional[str] = None,
        sql_optimized: Optional[str] = None,
        improvement: Optional[str] = None,
        domain: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Добавление одного примера обучения через API
        
        Args:
            question: Вопрос на естественном языке
            sql: SQL запрос (оптимизированный вариант)
            user_id: ID пользователя
            verified: Проверен ли пример
            sql_basic: Базовый (неоптимизированный) SQL для сравнения
            sql_optimized: Оптимизированный SQL (альтернатива sql)
            improvement: Описание улучшения производительности
            domain: Домен вопроса (users, payments, assignments, etc.)
            tags: Список тегов для категоризации
            
        Returns:
            Dict с результатом добавления (example_id, explain_plan, etc.)
        """
        if not self.check_api_connection():
            raise ConnectionError(f"Core API недоступен на {self.api_base_url}")
        
        request_data = {
            "question": question,
            "sql": sql_optimized if sql_optimized else sql,
            "user_id": user_id,
            "verified": verified
        }
        
        # Добавляем опциональные поля
        if sql_basic:
            request_data["sql_basic"] = sql_basic
        if sql_optimized:
            request_data["sql_optimized"] = sql_optimized
        if improvement:
            request_data["improvement"] = improvement
        if domain:
            request_data["domain"] = domain
        if tags:
            request_data["tags"] = tags
        
        try:
            response = requests.post(
                f"{self.api_base_url}/training/example",
                json=request_data,
                timeout=60  # Увеличенный таймаут для генерации EXPLAIN планов
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"API вернул ошибку: {response.status_code} - {response.text}")
                
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Ошибка подключения к API: {e}")
    
    def add_training_examples_batch(
        self,
        examples: List[Dict[str, Any]],
        user_id: str = "kb_training_client",
        verbose: bool = True
    ) -> Dict[str, Any]:
        """
        Массовое добавление примеров обучения
        
        Args:
            examples: Список словарей с примерами (формат как в JSON файлах)
            user_id: ID пользователя
            verbose: Выводить прогресс
            
        Returns:
            Dict со статистикой: {total, success, failed, errors}
        """
        stats = {
            "total": len(examples),
            "success": 0,
            "failed": 0,
            "errors": []
        }
        
        for i, example in enumerate(examples, 1):
            if verbose:
                print(f"[{i}/{len(examples)}] Добавление: {example.get('question', '')[:50]}...")
            
            try:
                # Нормализуем формат
                question = example.get("question") or example.get("q")
                sql = example.get("sql") or example.get("sql_optimized") or example.get("answer") or example.get("a")
                
                if not question or not sql:
                    raise ValueError("Отсутствует question или sql")
                
                result = self.add_training_example(
                    question=question,
                    sql=sql,
                    user_id=user_id,
                    sql_basic=example.get("sql_basic"),
                    sql_optimized=example.get("sql_optimized"),
                    improvement=example.get("improvement"),
                    domain=example.get("domain"),
                    tags=example.get("tags")
                )
                
                if result.get("success"):
                    stats["success"] += 1
                    if verbose:
                        example_id = result.get("example_id", "unknown")
                        print(f"  ✅ Добавлено (ID: {example_id})")
                else:
                    stats["failed"] += 1
                    error_msg = result.get("error", "Неизвестная ошибка")
                    stats["errors"].append(f"Пример #{i}: {error_msg}")
                    if verbose:
                        print(f"  ❌ Ошибка: {error_msg}")
                        
            except Exception as e:
                stats["failed"] += 1
                error_msg = str(e)
                stats["errors"].append(f"Пример #{i}: {error_msg}")
                if verbose:
                    print(f"  ❌ Исключение: {error_msg}")
        
        return stats
    
    def add_from_json_file(
        self,
        json_file: Path,
        user_id: str = "kb_training_client",
        verbose: bool = True
    ) -> Dict[str, Any]:
        """
        Добавление примеров из JSON файла
        
        Args:
            json_file: Путь к JSON файлу с примерами
            user_id: ID пользователя
            verbose: Выводить прогресс
            
        Returns:
            Dict со статистикой
        """
        if not json_file.exists():
            raise FileNotFoundError(f"Файл не найден: {json_file}")
        
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            raise ValueError("JSON должен быть массивом объектов")
        
        if verbose:
            print(f"📋 Загружено {len(data)} примеров из {json_file}")
        
        return self.add_training_examples_batch(data, user_id=user_id, verbose=verbose)


def main():
    """CLI интерфейс для обучения KB"""
    parser = argparse.ArgumentParser(
        description="Обучение векторной базы знаний через Core API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:

  # Добавление из JSON файла
  python -m src.tools.kb_training_client --file training_data/sql_examples.json

  # Добавление с указанием API URL
  python -m src.tools.kb_training_client --file qa_pairs.json --api-url http://localhost:8000

  # Тихий режим (без вывода прогресса)
  python -m src.tools.kb_training_client --file examples.json --quiet
        """
    )
    
    parser.add_argument(
        "--file", "-f",
        type=Path,
        required=True,
        help="Путь к JSON файлу с примерами обучения"
    )
    
    parser.add_argument(
        "--api-url",
        default=None,
        help=f"URL Core API (по умолчанию: {API_BASE_URL})"
    )
    
    parser.add_argument(
        "--user-id",
        default="kb_training_client",
        help="ID пользователя для логирования"
    )
    
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Тихий режим (минимальный вывод)"
    )
    
    args = parser.parse_args()
    
    # Создаем клиент
    client = KBTrainingClient(api_base_url=args.api_url)
    
    # Проверяем подключение
    if not args.quiet:
        print(f"🔗 Подключение к Core API: {client.api_base_url}")
    
    if not client.check_api_connection():
        print(f"❌ Ошибка: Core API недоступен на {client.api_base_url}", file=sys.stderr)
        print(f"💡 Убедитесь, что сервис запущен: ./run_stack.sh start", file=sys.stderr)
        sys.exit(1)
    
    if not args.quiet:
        print("✅ Подключение к API установлено")
    
    # Добавляем примеры
    try:
        stats = client.add_from_json_file(
            json_file=args.file,
            user_id=args.user_id,
            verbose=not args.quiet
        )
        
        # Выводим статистику
        print("\n" + "="*60)
        print("📊 Статистика добавления:")
        print(f"  Всего примеров: {stats['total']}")
        print(f"  ✅ Успешно: {stats['success']}")
        print(f"  ❌ Ошибок: {stats['failed']}")
        
        if stats['errors']:
            print("\n❌ Ошибки:")
            for error in stats['errors'][:10]:  # Показываем первые 10 ошибок
                print(f"  • {error}")
            if len(stats['errors']) > 10:
                print(f"  ... и еще {len(stats['errors']) - 10} ошибок")
        
        print("\n💡 После добавления примеров сгенерируйте эмбеддинги:")
        print("   python -m src.tools.generate_embeddings_hf --dsn \"$DATABASE_URL\" --model \"$HF_MODEL_NAME\"")
        print("="*60)
        
        # Возвращаем код выхода в зависимости от результата
        sys.exit(0 if stats['failed'] == 0 else 1)
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

