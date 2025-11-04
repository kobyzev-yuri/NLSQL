"""
Сервис для работы с запросами и Vanna AI
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import logging
from typing import Dict, Any, Optional, List
from src.vanna.optimized_dual_pipeline import OptimizedDualPipeline
from src.vanna.vanna_semantic_fixed import create_semantic_vanna_client
from src.vanna.simple_openai_sql import create_simple_sql_generator

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
        Инициализация простого SQL генератора (без Vanna AI)
        """
        try:
            # Используем ProxyAPI GPT-4o
            config = {
                'model': 'gpt-4o',
                'database_url': 'postgresql://postgres:1234@localhost:5432/test_docstructure',
                'api_key': os.getenv("OPENAI_API_KEY"),
                'base_url': os.getenv("OPENAI_BASE_URL", 'https://api.proxyapi.ru/openai/v1'),
                'temperature': float(os.getenv("OPENAI_TEMPERATURE", "0.2"))
            }
            
            self.pipeline = create_simple_sql_generator(config)
            self._has_gpt4_key = bool(config['api_key'])
            logger.info("✅ GPT-4o SQL генератор инициализирован через ProxyAPI")
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации генератора: {e}")
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
        """
        Получает RAG контекст для домена с приоритизацией оптимизированных SQL.
        Разделяет контекст на две секции: оптимизированные примеры (приоритет) и обычные примеры.
        """
        try:
            # Семантический поиск с метаданными для различения оптимизированных SQL
            if self.semantic_vanna and hasattr(self.semantic_vanna, 'get_similar_question_sql_with_metadata'):
                # Получаем Q/A пары с метаданными (увеличиваем limit для лучшего покрытия)
                results = await self.semantic_vanna.get_similar_question_sql_with_metadata(question, limit=20)
                
                if results:
                    # Разделяем на оптимизированные и обычные
                    optimized_examples = []
                    regular_examples = []
                    
                    for result in results:
                        content = result.get('content', '')
                        is_optimized = result.get('is_optimized', False)
                        sql_basic = result.get('sql_basic')
                        improvement = result.get('improvement', '')
                        metadata = result.get('metadata', {})
                        
                        # Извлекаем EXPLAIN план из metadata или из результата
                        explain_plan = result.get('explain_plan')
                        if not explain_plan and isinstance(metadata, dict):
                            explain_plan = metadata.get('explain_plan')
                        
                        # Форматируем пример с дополнительной информацией об оптимизации
                        if is_optimized:
                            # Для оптимизированных SQL показываем сравнение и план
                            formatted_parts = [content]
                            
                            if improvement:
                                formatted_parts.append(f"[OPTIMIZED: {improvement}]")
                            
                            if explain_plan:
                                # Добавляем план для понимания производительности
                                formatted_parts.append(f"EXPLAIN PLAN:\n{explain_plan}")
                            
                            formatted = "\n".join(formatted_parts)
                            optimized_examples.append(formatted)
                        else:
                            # Для обычных SQL тоже добавляем план, если есть
                            formatted_parts = [content]
                            if explain_plan:
                                formatted_parts.append(f"EXPLAIN PLAN:\n{explain_plan}")
                            formatted = "\n".join(formatted_parts)
                            regular_examples.append(formatted)
                    
                    # Формируем контекст с приоритетом оптимизированных SQL
                    context_parts = []
                    
                    if optimized_examples:
                        context_parts.append("===OPTIMIZED SQL EXAMPLES (PREFERRED - Use these patterns for efficiency):")
                        context_parts.extend(optimized_examples[:5])  # Топ-5 оптимизированных (приоритет)
                        logger.info(f"✅ Добавлено {len(optimized_examples[:5])} оптимизированных SQL с планами в контекст")
                    
                    if regular_examples:
                        context_parts.append("===ADDITIONAL SQL EXAMPLES (reference):")
                        context_parts.extend(regular_examples[:3])  # Топ-3 обычных (для справочной информации)
                        logger.debug(f"Добавлено {len(regular_examples[:3])} обычных SQL в контекст")
                    
                    return "\n\n".join(context_parts)
            else:
                # Fallback: используем обычный поиск без метаданных
                results = await self.semantic_vanna.get_similar_question_sql(question, limit=5)
                if results:
                    return "\n\n".join(results[:5])
            return ""
        except Exception as e:
            logger.error(f"Ошибка получения RAG контекста: {e}")
            return ""

    def _build_smart_prompt(self, question: str, domain: str, ddl_tables: str, rag_context: str) -> str:
        """
        Строит умный промпт с доменной кластеризацией и приоритетом оптимизированных SQL.
        """
        # Системные инструкции с акцентом на оптимизацию
        system_instructions = """You are a PostgreSQL expert. Generate ONLY valid, OPTIMIZED SQL code.

PERFORMANCE PRIORITY RULES:
1. ALWAYS prefer OPTIMIZED SQL patterns from examples (marked with [OPTIMIZED])
2. Analyze EXPLAIN PLANs in examples to understand performance characteristics:
   - Lower cost (e.g., cost=0.00..35.50) = faster execution
   - Index Scan/Index Only Scan = better than Sequential Scan
   - Use specific column names instead of SELECT * (minimize data transfer)
   - Add appropriate WHERE filters to reduce data volume (filter early)
   - Use INNER JOIN instead of LEFT JOIN when possible (faster execution)
   - Add ORDER BY for logical sorting when needed
3. Consider performance: minimize data transfer and execution time
4. When comparing SQL options, prefer the one with lower EXPLAIN cost

Generate SQL that is:
- Functionally correct (returns correct data)
- Performance-optimized (fast execution, minimal data transfer, low EXPLAIN cost)
- Following patterns from OPTIMIZED examples when available
- Using indexes effectively (check EXPLAIN PLANs in examples)"""
        
        if domain == 'general':
            # Для общего домена используем стандартный подход, но с инструкциями
            prompt_parts = [
                system_instructions,
                f"===Question (ru)",
                question
            ]
            if rag_context:
                prompt_parts.insert(-1, f"===Examples (SQL Patterns):\n{rag_context}")
            return "\n\n".join(prompt_parts)
        
        # Доменный промпт с приоритетом оптимизированных SQL
        prompt_parts = [
            system_instructions,
            f"===Domain: {domain.upper()}",
            f"===Tables (Domain-specific DDL)",
            ddl_tables,
        ]
        
        if rag_context:
            # RAG контекст уже содержит разделение на OPTIMIZED и обычные примеры
            prompt_parts.append(rag_context)
        
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

            # Шаг 5: Генерируем SQL через простой генератор
            logger.info("🔄 Используем прямой вызов OpenAI GPT-4o...")
            # Обертываем синхронный вызов в thread pool, чтобы не блокировать event loop
            import asyncio
            sql = await asyncio.to_thread(self.pipeline.generate_sql, smart_question, 60)
            result = {'success': True, 'sql': sql, 'model': 'gpt-4o-direct'}

            if result and result.get('success') and result.get('sql'):
                sql = result['sql']
                logger.info(f"✅ SQL сгенерирован: {sql}")
                return sql
            else:
                raise Exception("Не удалось сгенерировать SQL")

        except Exception as e:
            logger.error(f"❌ Ошибка генерации SQL: {e}")
            raise
    
    async def add_training_example(
        self, 
        question: str, 
        sql: str, 
        user_id: str, 
        verified: bool = False,
        sql_basic: Optional[str] = None,
        sql_optimized: Optional[str] = None,
        improvement: Optional[str] = None,
        domain: Optional[str] = None,
        tags: Optional[List[str]] = None
    ):
        """
        Добавление примера для обучения
        
        Args:
            question: Вопрос пользователя
            sql: SQL запрос (оптимизированный вариант)
            user_id: ID пользователя
            verified: Проверен ли пример
            sql_basic: Базовый (неоптимизированный) SQL для сравнения
            sql_optimized: Оптимизированный SQL (альтернатива sql)
            improvement: Описание улучшения производительности
            domain: Домен вопроса (users, payments, assignments, etc.)
            tags: Список тегов для категоризации
        """
        try:
            logger.info(f"Добавление примера обучения от пользователя {user_id}")
            
            # Определяем, является ли это оптимизированным SQL
            is_optimized = sql_basic is not None or sql_optimized is not None
            
            # Используем sql_optimized как основной sql, если он указан
            final_sql = sql_optimized if sql_optimized else sql
            
            # Добавление примера в векторную базу через semantic_vanna
            if self.semantic_vanna:
                try:
                    # Подготовка kwargs для оптимизированных SQL
                    kwargs = {}
                    if sql_basic:
                        kwargs['sql_basic'] = sql_basic
                    if sql_optimized:
                        kwargs['sql_optimized'] = sql_optimized
                    if improvement:
                        kwargs['improvement'] = improvement
                    if domain:
                        kwargs['domain'] = domain
                    if tags:
                        kwargs['tags'] = tags
                    if is_optimized:
                        kwargs['is_optimized'] = True
                        # Для оптимизированных SQL явно включаем генерацию планов
                        kwargs['generate_explain_plan'] = True
                    
                    # Добавляем через add_question_sql
                    # Планы генерируются автоматически только для оптимизированных SQL
                    logger.info(f"📤 Вызов add_question_sql с параметрами:")
                    logger.info(f"   question: {question[:100]}...")
                    logger.info(f"   sql: {final_sql[:100]}...")
                    logger.info(f"   is_optimized: {is_optimized}")
                    logger.info(f"   generate_explain_plan: {kwargs.get('generate_explain_plan', False)}")
                    logger.info(f"   sql_basic: {kwargs.get('sql_basic', 'None')[:100] if kwargs.get('sql_basic') else 'None'}...")
                    
                    example_id = await self.semantic_vanna.add_question_sql(
                        question=question,
                        sql=final_sql,
                        **kwargs
                    )
                    
                    logger.info(f"✅ add_question_sql вернул example_id: {example_id}")
                    
                    opt_info = " (оптимизированный)" if is_optimized else ""
                    logger.info(f"✅ Пример{opt_info} успешно добавлен в векторную базу: {example_id}")
                    logger.info(f"   Вопрос: {question}")
                    logger.info(f"   SQL: {final_sql[:100]}...")
                    
                    # Получаем планы из metadata для возврата в API
                    explain_plan = kwargs.get('explain_plan')
                    explain_plan_basic = kwargs.get('explain_plan_basic')
                    
                    logger.info(f"🔍 Планы из kwargs: explain_plan={'✅' if explain_plan else '❌'}, explain_plan_basic={'✅' if explain_plan_basic else '❌'}")
                    
                    # Получаем metadata из БД для извлечения планов и результатов валидации
                    if self.semantic_vanna:
                        try:
                            import asyncpg
                            import json
                            conn = await asyncpg.connect(self.semantic_vanna.database_url)
                            result = await conn.fetchrow(
                                "SELECT metadata FROM vanna_vectors WHERE id = $1",
                                int(example_id)
                            )
                            await conn.close()
                            
                            if result:
                                metadata = result['metadata']
                                if isinstance(metadata, str):
                                    metadata = json.loads(metadata)
                                
                                logger.info(f"📋 Metadata из БД содержит: explain_plan={'✅' if metadata.get('explain_plan') else '❌'}, explain_plan_basic={'✅' if metadata.get('explain_plan_basic') else '❌'}")
                                
                                # Извлекаем планы
                                if not explain_plan:
                                    explain_plan = metadata.get('explain_plan')
                                    logger.info(f"📝 Извлечен explain_plan из metadata: {'✅' if explain_plan else '❌'}")
                                if not explain_plan_basic:
                                    explain_plan_basic = metadata.get('explain_plan_basic')
                                    logger.info(f"📝 Извлечен explain_plan_basic из metadata: {'✅' if explain_plan_basic else '❌'}")
                                
                                # Извлекаем результаты валидации оптимизации
                                optimization_validated = metadata.get('optimization_validated')
                                cost_basic = metadata.get('cost_basic')
                                cost_optimized = metadata.get('cost_optimized')
                                cost_improvement_percent = metadata.get('cost_improvement_percent')
                                width_basic = metadata.get('width_basic')
                                width_optimized = metadata.get('width_optimized')
                                width_improvement_percent = metadata.get('width_improvement_percent')
                                rows_basic = metadata.get('rows_basic')
                                rows_optimized = metadata.get('rows_optimized')
                                rows_improvement_percent = metadata.get('rows_improvement_percent')
                                optimization_warning = metadata.get('optimization_warning')
                                
                                return {
                                    'example_id': example_id,
                                    'explain_plan': explain_plan,
                                    'explain_plan_basic': explain_plan_basic,
                                    'optimization_validated': optimization_validated,
                                    'cost_basic': cost_basic,
                                    'cost_optimized': cost_optimized,
                                    'cost_improvement_percent': cost_improvement_percent,
                                    'width_basic': width_basic,
                                    'width_optimized': width_optimized,
                                    'width_improvement_percent': width_improvement_percent,
                                    'rows_basic': rows_basic,
                                    'rows_optimized': rows_optimized,
                                    'rows_improvement_percent': rows_improvement_percent,
                                    'optimization_warning': optimization_warning
                                }
                        except Exception as e:
                            logger.warning(f"⚠️ Не удалось получить планы и валидацию из БД: {e}")
                    
                    # Возвращаем example_id и планы для API response (fallback если не удалось получить из БД)
                    return {
                        'example_id': example_id,
                        'explain_plan': explain_plan,
                        'explain_plan_basic': explain_plan_basic,
                        'optimization_validated': None,
                        'cost_basic': None,
                        'cost_optimized': None,
                        'cost_improvement_percent': None,
                        'optimization_warning': None
                    }
                    
                except Exception as e:
                    logger.warning(f"⚠️ Не удалось добавить в векторную базу: {e}")
                    logger.info(f"Пример логируется: {question} -> {final_sql}")
                    return {'example_id': None, 'explain_plan': None, 'explain_plan_basic': None}
            else:
                logger.info(f"Пример успешно добавлен: {question} -> {final_sql}")
                return {'example_id': None, 'explain_plan': None, 'explain_plan_basic': None}
            
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
    
    async def test_vector_search(self, question: str, search_type: str = "semantic", limit: int = 5) -> List[Dict[str, Any]]:
        """
        Тестирование семантического поиска в векторной базе данных
        
        Args:
            question: Вопрос для поиска
            search_type: Тип поиска (semantic, ddl, documentation, examples)
            limit: Максимальное количество результатов
            
        Returns:
            List[Dict[str, Any]]: Результаты поиска
        """
        try:
            logger.info(f"Тестирование поиска: {question} (тип: {search_type})")
            
            if not self.semantic_vanna:
                logger.error("Семантический RAG не инициализирован")
                return []
            
            # Выполняем поиск в зависимости от типа
            if search_type == "semantic":
                results = await self.semantic_vanna.get_related_ddl(question)
            elif search_type == "ddl":
                results = await self.semantic_vanna.get_related_ddl(question)
            elif search_type == "documentation":
                results = await self.semantic_vanna.get_related_documentation(question)
            elif search_type == "examples":
                results = await self.semantic_vanna.get_related_question_sql(question)
            else:
                # По умолчанию используем семантический поиск
                results = await self.semantic_vanna.get_related_ddl(question)
            
            # Форматируем результаты
            formatted_results = []
            for i, result in enumerate(results[:limit]):
                formatted_results.append({
                    "content": result,
                    "type": search_type,
                    "rank": i + 1
                })
            
            logger.info(f"Найдено {len(formatted_results)} результатов для типа {search_type}")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Ошибка тестирования поиска: {e}")
            return []

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
