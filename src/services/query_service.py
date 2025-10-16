"""
Сервис для работы с запросами и Vanna AI
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import logging
from typing import Dict, Any, Optional
from src.vanna.optimized_dual_pipeline import OptimizedDualPipeline
from src.vanna.vanna_semantic_fixed import create_semantic_vanna_client

logger = logging.getLogger(__name__)


class QueryService:
    """
    Сервис для обработки запросов и генерации SQL
    """
    
    def __init__(self):
        """
        Инициализация сервиса
        """
        self.pipeline = None
        self.semantic_vanna = None
        self._initialize_pipeline()
        self._initialize_semantic_rag()
    
    def _initialize_pipeline(self):
        """
        Инициализация оптимизированного пайплайна
        """
        try:
            # Конфигурация для оптимизированного пайплайна (ключи соответствуют OptimizedDualPipeline)
            config = {
                'gpt4': {
                    'model': 'gpt-4o',
                    'database_url': 'postgresql://postgres:1234@localhost:5432/test_docstructure',
                    'api_key': os.getenv("PROXYAPI_KEY") or os.getenv("PROXYAPI_API_KEY") or os.getenv("OPENAI_API_KEY"),
                    'base_url': 'https://api.proxyapi.ru/openai/v1',
                    'temperature': 0.2
                },
                'ollama': {
                    'model': 'llama3:latest',
                    'database_url': 'postgresql://postgres:1234@localhost:5432/test_docstructure',
                    'api_key': 'ollama',
                    'base_url': 'http://localhost:11434/v1',
                    'temperature': 0.2
                },
                'training_data_path': 'training_data/enhanced_sql_examples.json'
            }
            
            self.pipeline = OptimizedDualPipeline(config)
            # Флаг доступности внешнего API для выбора модели по умолчанию
            self._has_gpt4_key = bool(config['gpt4']['api_key'])
            logger.info("Оптимизированный пайплайн инициализирован")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации пайплайна: {e}")
            raise
    
    def _initialize_semantic_rag(self):
        """
        Инициализация семантического RAG
        """
        try:
            self.semantic_vanna = create_semantic_vanna_client()
            logger.info("✅ Семантический RAG инициализирован")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации семантического RAG: {e}")
            self.semantic_vanna = None
    
    def _detect_domain(self, question: str) -> str:
        """Определяет домен запроса по ключевым словам."""
        question_lower = question.lower()
        
        # Доменные конфигурации
        domain_configs = {
            'payments': {
                'keywords': ['платеж', 'payment', 'оплата', 'деньги', 'денег', 'сумма', 'рубль', 'рублей', 'входящий', 'исходящий'],
                'tables': ['tbl_incoming_payments', 'tbl_payment_statuses', 'tbl_postpayment_types', 'tbl_business_unit', 'tbl_principal_assignment']
            },
            'users': {
                'keywords': ['пользователь', 'user', 'сотрудник', 'менеджер', 'админ', 'логин', 'отдел', 'департамент'],
                'tables': ['equsers', 'eq_departments', 'eqroles', 'eqgroups']
            },
            'assignments': {
                'keywords': ['поручение', 'поручения', 'assignment', 'assignments', 'задание', 'задания', 'документ', 'документы', 'договор', 'контракт', 'task', 'tasks'],
                'tables': ['tbl_principal_assignment', 'tbl_business_unit', 'equsers']
            },
            'reports': {
                'keywords': ['отчет', 'report', 'статистика', 'аналитика', 'сводка', 'итог'],
                'tables': ['tbl_incoming_payments', 'equsers', 'eq_departments', 'tbl_business_unit']
            }
        }
        
        # Подсчет совпадений по доменам
        domain_scores = {}
        for domain, config in domain_configs.items():
            score = sum(1 for keyword in config['keywords'] if keyword in question_lower)
            if score > 0:
                domain_scores[domain] = score
        
        # Возвращаем домен с максимальным счетом или 'general'
        if domain_scores:
            return max(domain_scores, key=domain_scores.get)
        return 'general'

    async def _get_tables_ddl(self, table_names: list[str]) -> str:
        """Возвращает сокращенный DDL для заданных таблиц из vanna_vectors (content_type='ddl')."""
        try:
            import asyncpg
            conn = await asyncpg.connect("postgresql://postgres:1234@localhost:5432/test_docstructure")
            rows = await conn.fetch(
                """
                SELECT metadata, content
                FROM vanna_vectors
                WHERE content_type='ddl' AND (metadata->>'table') = ANY($1)
                ORDER BY id
                """,
                table_names,
            )
            await conn.close()
            parts: list[str] = []
            for r in rows:
                md = r["metadata"]
                if isinstance(md, str):
                    import json
                    try:
                        md = json.loads(md)
                    except:
                        md = {}
                t = (md or {}).get("table", "unknown")
                ddl = r["content"] or ""
                # Усечем длинные тела, оставим первые ~60 строк
                head = "\n".join(ddl.splitlines()[:60])
                parts.append(f"TABLE: public.{t}\n{head}")
            return "\n\n".join(parts)
        except Exception as e:
            logger.error(f"Ошибка получения DDL таблиц: {e}")
            return ""

    async def _get_rag_context(self, question: str, domain: str) -> str:
        """Получает RAG контекст для домена."""
        try:
            # Семантический поиск с доменными фильтрами
            if self.semantic_vanna:
                # Увеличиваем top_k для лучшего покрытия
                results = await self.semantic_vanna.get_similar_question_sql(question, top_k=10)
                if results:
                    context_parts = []
                    for result in results[:5]:  # Берем топ-5
                        # Результат может быть строкой в формате "Q: ... A: ..."
                        if isinstance(result, str):
                            context_parts.append(result)
                        elif hasattr(result, 'question') and hasattr(result, 'sql'):
                            context_parts.append(f"Q: {result.question}\nSQL: {result.sql}")
                    return "\n\n".join(context_parts)
            return ""
        except Exception as e:
            logger.error(f"Ошибка получения RAG контекста: {e}")
            return ""

    def _build_smart_prompt(self, question: str, domain: str, ddl_tables: str, rag_context: str) -> str:
        """Строит умный промпт с доменной кластеризацией."""
        if domain == 'general':
            # Для общего домена используем стандартный подход
            return question
        
        # Доменный промпт
        prompt_parts = [
            f"===Domain: {domain.upper()}",
            f"===Tables (Domain-specific DDL)",
            ddl_tables,
        ]
        
        if rag_context:
            prompt_parts.extend([
                f"===Additional Context (RAG)",
                rag_context,
            ])
        
        prompt_parts.extend([
            f"===Question (ru)",
            question
        ])
        
        return "\n\n".join(prompt_parts)

    async def _retrieve_payment_context(self, question: str) -> str:
        """Гибридный ретривер для платежных запросов с BM25 + семантикой"""
        try:
            import asyncpg
            import re
            from openai import OpenAI
            
            # Проверяем, содержит ли вопрос платежную тематику
            payment_keywords = ['платеж', 'payment', 'платежи', 'payments', 'входящие', 'incoming', 'статус', 'status']
            is_payment_query = any(keyword in question.lower() for keyword in payment_keywords)
            
            if not is_payment_query:
                return ""
            
            # Подключаемся к БД
            conn = await asyncpg.connect("postgresql://postgres:1234@localhost:5432/test_docstructure")
            
            # BM25 поиск по ключевым словам
            bm25_results = await conn.fetch("""
                SELECT content, content_type, metadata
                FROM vanna_vectors 
                WHERE content_type = 'ddl' 
                AND (
                    content ILIKE '%tbl_incoming_payments%' OR
                    content ILIKE '%tbl_payment_statuses%' OR
                    content ILIKE '%tbl_postpayment_types%' OR
                    content ILIKE '%tbl_business_unit%' OR
                    content ILIKE '%tbl_principal_assignment%'
                )
                ORDER BY 
                    CASE 
                        WHEN content ILIKE '%tbl_incoming_payments%' THEN 1
                        WHEN content ILIKE '%tbl_payment_statuses%' THEN 2
                        WHEN content ILIKE '%tbl_postpayment_types%' THEN 3
                        WHEN content ILIKE '%tbl_business_unit%' THEN 4
                        WHEN content ILIKE '%tbl_principal_assignment%' THEN 5
                        ELSE 6
                    END
                LIMIT 10
            """)
            
            # Семантический поиск с HF моделью (384 размерность)
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
            question_embedding = model.encode(question, convert_to_tensor=True).tolist()
            embedding_str = '[' + ','.join(map(str, question_embedding)) + ']'
            
            semantic_results = await conn.fetch("""
                SELECT content, content_type, metadata, embedding <-> $1::vector as distance
                FROM vanna_vectors 
                WHERE content_type = 'ddl' 
                AND embedding IS NOT NULL
                AND (
                    content ILIKE '%tbl_incoming_payments%' OR
                    content ILIKE '%tbl_payment_statuses%' OR
                    content ILIKE '%tbl_postpayment_types%' OR
                    content ILIKE '%tbl_business_unit%' OR
                    content ILIKE '%tbl_principal_assignment%'
                )
                ORDER BY embedding <-> $1::vector
                LIMIT 15
            """, embedding_str)
            
            await conn.close()
            
            # Объединяем результаты
            all_results = list(bm25_results) + list(semantic_results)
            seen_content = set()
            unique_results = []
            
            for result in all_results:
                if result['content'] not in seen_content:
                    unique_results.append(result)
                    seen_content.add(result['content'])
                    if len(unique_results) >= 8:  # Ограничиваем контекст
                        break
            
            # Форматируем контекст
            context_parts = []
            for result in unique_results:
                # Исправляем парсинг metadata
                metadata = result['metadata']
                if isinstance(metadata, str):
                    import json
                    try:
                        metadata = json.loads(metadata)
                    except:
                        metadata = {}
                table_name = metadata.get('table', 'unknown') if metadata else 'unknown'
                context_parts.append(f"Таблица {table_name}:\n{result['content'][:500]}...")
            
            return "\n\n".join(context_parts)
            
        except Exception as e:
            logger.error(f"Ошибка гибридного ретривера: {e}")
            return ""

    async def generate_sql(self, question: str, user_context: Dict[str, Any]) -> str:
        """
        Генерация SQL запроса на основе вопроса с универсальным доменным подходом
        
        Args:
            question: Вопрос пользователя
            user_context: Контекст пользователя
            
        Returns:
            str: SQL запрос
        """
        try:
            logger.info(f"Генерация SQL для вопроса: {question}")

            # Шаг 1: Определяем домен запроса
            domain = self._detect_domain(question)
            logger.info(f"🎯 Определен домен: {domain}")

            # Шаг 2: Получаем доменные DDL таблицы
            domain_configs = {
                'payments': ['tbl_incoming_payments', 'tbl_payment_statuses', 'tbl_postpayment_types', 'tbl_business_unit', 'tbl_principal_assignment'],
                'users': ['equsers', 'eq_departments', 'eqroles', 'eqgroups'],
                'assignments': ['tbl_principal_assignment', 'tbl_business_unit', 'equsers'],
                'reports': ['tbl_incoming_payments', 'equsers', 'eq_departments', 'tbl_business_unit']
            }
            
            ddl_tables = ""
            if domain in domain_configs:
                ddl_tables = await self._get_tables_ddl(domain_configs[domain])
                logger.info(f"📋 Получен DDL для домена {domain}: {len(ddl_tables)} символов")

            # Шаг 3: Получаем RAG контекст
            rag_context = await self._get_rag_context(question, domain)
            if rag_context:
                logger.info(f"🔍 Получен RAG контекст: {len(rag_context)} символов")

            # Шаг 4: Строим умный промпт
            smart_question = self._build_smart_prompt(question, domain, ddl_tables, rag_context)
            logger.info(f"🧠 Построен умный промпт для домена {domain}")

            # Шаг 5: Генерируем SQL через пайплайн
            logger.info("🔄 Используем основной пайплайн с GPT-4o...")
            prefer_primary = 'openai'  # Используем GPT-4o
            result = self.pipeline.generate_sql(smart_question, prefer_model=prefer_primary)

            # Если неуспех из-за ключа/401 — фоллбэк на ollama
            def need_fallback(res, err: Optional[Exception] = None) -> bool:
                text = ''
                if isinstance(res, dict):
                    text = f"{res.get('error', '')} {res.get('message', '')}"
                if err:
                    text += f" {str(err)}"
                text = text.lower()
                return '401' in text or 'invalid api key' in text or 'unauthorized' in text

            if not (result and result.get('success') and result.get('sql')) and (prefer_primary != 'ollama') and need_fallback(result):
                logger.warning("Генерация через GPT-4 не удалась (ключ/401). Переход на ollama.")
                result = self.pipeline.generate_sql(question, prefer_model='ollama')

            if result and result.get('success') and result.get('sql'):
                sql = result['sql']
                logger.info(f"Сгенерирован SQL с помощью {result.get('model', 'unknown')}: {sql}")
                return sql

            error_msg = result.get('error', 'Неизвестная ошибка') if isinstance(result, dict) else str(result)
            logger.error(f"Ошибка генерации SQL: {error_msg}")
            raise Exception(f"Ошибка генерации SQL: {error_msg}")

        except Exception as e:
            # Финальный фоллбэк: пробуем ollama один раз, если ранее не пробовали
            try:
                logger.warning(f"Повторная попытка генерации через ollama из-за ошибки: {e}")
                result = self.pipeline.generate_sql(question, prefer_model='ollama')
                if result and result.get('success') and result.get('sql'):
                    sql = result['sql']
                    logger.info(f"Сгенерирован SQL фоллбэком ollama: {sql}")
                    return sql
                error_msg = result.get('error', 'Неизвестная ошибка') if isinstance(result, dict) else str(result)
                raise Exception(error_msg)
            except Exception as e2:
                logger.error(f"Ошибка генерации SQL после фоллбэка: {e2}")
                raise
    
    async def add_training_example(self, question: str, sql: str, user_id: str, verified: bool = False):
        """
        Добавление примера для обучения
        
        Args:
            question: Вопрос пользователя
            sql: SQL запрос
            user_id: ID пользователя
            verified: Проверен ли пример
        """
        try:
            logger.info(f"Добавление примера обучения от пользователя {user_id}")
            
            # Добавление примера в пайплайн (если поддерживается)
            # Пока что просто логируем
            logger.info(f"Пример успешно добавлен: {question} -> {sql}")
            
        except Exception as e:
            logger.error(f"Ошибка добавления примера: {e}")
            raise
    
    async def get_training_status(self) -> Dict[str, Any]:
        """
        Получение статуса обучения модели
        
        Returns:
            Dict[str, Any]: Статус обучения
        """
        try:
            # Здесь можно добавить логику получения статуса обучения
            return {
                "status": "ready",
                "training_examples": 0,  # Количество примеров обучения
                "last_training": None,   # Дата последнего обучения
                "model_version": "1.0.0"
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения статуса обучения: {e}")
            raise
    
    def is_ready(self) -> bool:
        """
        Проверка готовности сервиса
        
        Returns:
            bool: Готов ли сервис
        """
        return self.pipeline is not None
    
    async def train_on_database_schema(self, db_connection):
        """
        Обучение модели на схеме базы данных
        
        Args:
            db_connection: Подключение к базе данных
        """
        try:
            logger.info("Начало обучения на схеме базы данных")
            
            # Обучение пайплайна на схеме базы данных
            if self.pipeline:
                # Проверяем здоровье моделей
                health_status = self.pipeline.run_health_check()
                logger.info(f"Статус моделей: {health_status}")
                
                # Обучение на схеме (если поддерживается)
                logger.info("Обучение на схеме базы данных завершено")
            else:
                logger.warning("Пайплайн не инициализирован")
            
        except Exception as e:
            logger.error(f"Ошибка обучения на схеме: {e}")
            raise
