#!/usr/bin/env python3
"""
Vanna AI с исправленным контекстом и семантическим поиском
"""

import os
import logging
import asyncio
import asyncpg
import pandas as pd
from typing import List, Dict, Any, Optional
from pathlib import Path
from openai import OpenAI

# Load environment variables from config.env
from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / "config.env", override=True)

logger = logging.getLogger(__name__)

class DocStructureVectorDBSemantic:
    """
    Векторная БД с семантическим поиском для DocStructureSchema
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if config is None:
            config = {}
            
        self.config = config
        self.database_url = config.get("database_url", "postgresql://postgres:1234@localhost:5432/test_docstructure")
        self.vector_table = config.get("vector_table", "vanna_vectors")
        
        # OpenAI клиент для эмбеддингов
        self.openai_client = OpenAI(
            api_key=config.get("api_key", os.getenv("PROXYAPI_KEY")),
            base_url=config.get("base_url", "https://api.proxyapi.ru/openai/v1")
        )
        
        # Кеш модели эмбеддингов
        self._embedding_model = None
        self._embedding_model_name = None
        
        logger.info("✅ DocStructureVectorDBSemantic инициализирован")
    
    async def get_related_ddl(self, question: str, **kwargs) -> List[str]:
        """Получение релевантных DDL через семантический поиск"""
        try:
            context = await self._semantic_search(question, 'ddl', limit=3)
            logger.info(f"✅ Получено {len(context)} релевантных DDL")
            return context
        except Exception as e:
            logger.error(f"❌ Ошибка получения DDL: {e}")
            return []
    
    async def get_related_documentation(self, question: str, **kwargs) -> List[str]:
        """Получение релевантной документации через семантический поиск"""
        try:
            context = await self._semantic_search(question, 'documentation', limit=3)
            logger.info(f"✅ Получено {len(context)} релевантных документов")
            return context
        except Exception as e:
            logger.error(f"❌ Ошибка получения документации: {e}")
            return []
    
    async def get_similar_question_sql(self, question: str, **kwargs) -> List[str]:
        """Получение похожих Q/A пар через семантический поиск"""
        try:
            limit = int(kwargs.get('limit', 3))
            context = await self._semantic_search(question, 'question_sql', limit=limit)
            logger.info(f"✅ Получено {len(context)} релевантных Q/A пар")
            return context
        except Exception as e:
            logger.error(f"❌ Ошибка получения Q/A пар: {e}")
            return []
    
    async def get_similar_question_sql_with_metadata(self, question: str, **kwargs) -> List[Dict[str, Any]]:
        """
        Получение похожих Q/A пар с метаданными (для различения оптимизированных SQL)
        
        Распознает маркировку [OPTIMIZED SQL] из content (явная маркировка для агента LLM)
        и извлекает информацию из metadata (основной источник данных).
        Это помогает агенту сразу видеть оптимизированные примеры в контексте.
        
        Returns:
            List[Dict] с полями: content, metadata, is_optimized, sql_basic, improvement, explain_plan
        """
        try:
            limit = int(kwargs.get('limit', 10))
            
            # Генерируем эмбеддинг для вопроса
            question_embedding = await self._generate_embedding(question)
            if not question_embedding:
                return []
            
            # Подключаемся к БД
            conn = await asyncpg.connect(self.database_url)
            
            # Конвертируем эмбеддинг в строку для pgvector
            embedding_str = '[' + ','.join(map(str, question_embedding)) + ']'
            
            # Семантический поиск с метаданными
            query = """
                SELECT content, metadata, embedding <-> $1::vector as distance
                FROM vanna_vectors 
                WHERE content_type = 'question_sql' AND embedding IS NOT NULL
                ORDER BY embedding <-> $1::vector
                LIMIT $2
            """
            
            results = await conn.fetch(query, embedding_str, limit)
            await conn.close()
            
            # Парсим результаты с метаданными
            qa_pairs = []
            for row in results:
                content = row['content'] or ''
                metadata = row['metadata'] or {}
                
                # Парсим JSON, если metadata - строка
                if isinstance(metadata, str):
                    try:
                        import json
                        metadata = json.loads(metadata)
                    except:
                        metadata = {}
                
                # Проверяем, является ли это оптимизированным SQL
                # Используем два источника: metadata (основной) и content (явная маркировка для агента)
                is_optimized_from_metadata = metadata.get('is_optimized', False) if isinstance(metadata, dict) else False
                is_optimized_from_content = '[OPTIMIZED SQL]' in content if content else False
                is_optimized = is_optimized_from_metadata or is_optimized_from_content
                
                # Если improvement не в metadata, но есть в content маркировке, извлекаем
                improvement = None
                if isinstance(metadata, dict):
                    improvement = metadata.get('improvement')
                
                if not improvement and is_optimized_from_content:
                    import re
                    match = re.search(r'\[OPTIMIZED SQL(?::\s*(.+?))?\]', content)
                    if match and match.group(1):
                        improvement = match.group(1).strip()
                
                qa_pairs.append({
                    'content': content,
                    'metadata': metadata,
                    'is_optimized': is_optimized,
                    'sql_basic': metadata.get('sql_basic') if isinstance(metadata, dict) else None,
                    'improvement': improvement,
                    'explain_plan': metadata.get('explain_plan') if isinstance(metadata, dict) else None,
                    'explain_plan_basic': metadata.get('explain_plan_basic') if isinstance(metadata, dict) else None,
                    'distance': row['distance']
                })
            
            # Сортируем: сначала оптимизированные, потом обычные
            # Приоритет оптимизированных SQL даже при большем расстоянии
            qa_pairs.sort(key=lambda x: (
                not x['is_optimized'],  # Оптимизированные сначала (False < True для not)
                x['distance']  # Затем по расстоянию
            ))
            
            optimized_count = sum(1 for x in qa_pairs if x['is_optimized'])
            logger.info(f"✅ Получено {len(qa_pairs)} Q/A пар (оптимизированных: {optimized_count})")
            
            # Отладочная информация: показываем топ-5 с флагами
            if logger.isEnabledFor(logging.DEBUG):
                for i, pair in enumerate(qa_pairs[:5], 1):
                    logger.debug(f"  #{i}: optimized={pair['is_optimized']}, distance={pair['distance']:.4f}, has_plan={'explain_plan' in pair}")
            
            return qa_pairs
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения Q/A пар с метаданными: {e}")
            return []
    
    def _extract_cost_from_plan(self, plan: str) -> Optional[float]:
        """
        Извлечение максимального cost из EXPLAIN плана
        
        Args:
            plan: Текст EXPLAIN плана
            
        Returns:
            float: Максимальный cost (второе значение в cost=0.00..59.24) или None
        """
        if not plan:
            return None
        
        import re
        # Ищем паттерн cost=start..end
        # Например: "Seq Scan on equsers  (cost=0.00..59.24 rows=1117 width=55)"
        cost_pattern = r'cost=([\d.]+)\.\.([\d.]+)'
        matches = re.findall(cost_pattern, plan)
        
        if not matches:
            return None
        
        # Берем максимальный cost из всех найденных (вложенные операции)
        max_cost = 0.0
        for start, end in matches:
            try:
                end_cost = float(end)
                max_cost = max(max_cost, end_cost)
            except ValueError:
                continue
        
        return max_cost if max_cost > 0 else None
    
    def _extract_plan_metrics(self, plan: str) -> Dict[str, Optional[float]]:
        """
        Извлечение метрик из EXPLAIN плана (cost, rows, width)
        
        Args:
            plan: Текст EXPLAIN плана
            
        Returns:
            Dict с полями: cost, rows, width
        """
        if not plan:
            return {'cost': None, 'rows': None, 'width': None}
        
        import re
        metrics = {'cost': None, 'rows': None, 'width': None}
        
        # Извлекаем cost (максимальный из всех операций)
        cost = self._extract_cost_from_plan(plan)
        metrics['cost'] = cost
        
        # Извлекаем rows и width из первой строки плана (основная операция)
        # Паттерн: "Seq Scan on equsers  (cost=0.00..59.24 rows=1117 width=71)"
        main_line_pattern = r'\(cost=[\d.]+\.[\d.]+ rows=(\d+) width=(\d+)\)'
        match = re.search(main_line_pattern, plan)
        if match:
            try:
                metrics['rows'] = float(match.group(1))
                metrics['width'] = float(match.group(2))
            except ValueError:
                pass
        
        return metrics
    
    async def _get_explain_plan(self, sql: str) -> Optional[str]:
        """
        Генерация EXPLAIN плана для SQL запроса
        
        Args:
            sql: SQL запрос
            
        Returns:
            str: EXPLAIN план или None при ошибке
        """
        if not sql or not sql.strip():
            logger.warning("⚠️ Пустой SQL запрос для EXPLAIN")
            return None
        
        logger.info(f"🔧 _get_explain_plan вызван для SQL: {sql[:100]}...")
        logger.info(f"   database_url: {self.database_url.split('@')[1] if '@' in self.database_url else '...'}")
        
        try:
            logger.info(f"🔗 Подключение к БД...")
            conn = await asyncpg.connect(self.database_url)
            logger.info(f"✅ Подключение успешно")
            
            # Генерируем EXPLAIN план
            # Используем простой EXPLAIN (FORMAT TEXT) - он не выполняет запрос
            explain_sql = f"EXPLAIN (FORMAT TEXT) {sql}"
            
            try:
                logger.info(f"📝 Выполняем EXPLAIN: {explain_sql[:150]}...")
                result = await conn.fetch(explain_sql)
                logger.info(f"📊 EXPLAIN вернул результат: type={type(result)}, len={len(result) if result else 0}")
                
                # Форматируем план из результата
                # asyncpg возвращает список Record объектов
                # Record ведет себя как dict и tuple одновременно
                if result and len(result) > 0:
                    plan_lines = []
                    for row in result:
                        # asyncpg Record поддерживает доступ по ключу и индексу
                        # Колонка EXPLAIN называется 'QUERY PLAN' (с пробелом)
                        plan_line = None
                        
                        # Способ 1: Доступ по ключу (основной способ для asyncpg)
                        try:
                            # asyncpg Record работает как dict
                            plan_line = row['QUERY PLAN']
                            logger.debug(f"   ✅ Доступ по ключу 'QUERY PLAN' успешен")
                        except (KeyError, TypeError, AttributeError) as e:
                            logger.debug(f"   ❌ Доступ по ключу 'QUERY PLAN' не удался: {e}")
                            # Пробуем найти правильное имя ключа
                            try:
                                if hasattr(row, 'keys'):
                                    keys = list(row.keys())
                                    logger.warning(f"   🔍 Доступные ключи в row: {keys}")
                                    # Пробуем найти ключ с 'plan' или 'query'
                                    for key in keys:
                                        if 'plan' in key.lower() or 'query' in key.lower():
                                            logger.warning(f"   🔍 Пробуем ключ: {key}")
                                            plan_line = row[key]
                                            logger.warning(f"   ✅ Значение через ключ '{key}': {plan_line[:100] if isinstance(plan_line, str) else plan_line}")
                                            break
                            except Exception as e2:
                                logger.debug(f"   ❌ Ошибка при поиске ключей: {e2}")
                        
                        # Способ 2: Доступ по индексу (первая и единственная колонка)
                        if not plan_line:
                            try:
                                plan_line = row[0]
                                logger.debug(f"   ✅ Доступ по индексу [0] успешен")
                            except (IndexError, TypeError) as e:
                                logger.debug(f"   ❌ Доступ по индексу [0] не удался: {e}")
                        
                        # Способ 3: Преобразование в строку (fallback)
                        if not plan_line:
                            plan_line = str(row)
                            logger.debug(f"   🔍 Преобразовали row в строку: {plan_line[:100]}")
                            # Если это строка вида "Record('QUERY PLAN'='...')", пытаемся извлечь значение
                            import re
                            match = re.search(r"'QUERY PLAN':\s*'([^']+)'", plan_line)
                            if match:
                                plan_line = match.group(1)
                                logger.debug(f"   ✅ Извлекли через regex: {plan_line[:100]}")
                        
                        if plan_line:
                            plan_lines.append(str(plan_line).strip())
                        else:
                            logger.warning(f"   ⚠️ Не удалось извлечь план из строки: {row}")
                    
                    if plan_lines:
                        plan = '\n'.join(plan_lines)
                        if plan and plan.strip():
                            logger.info(f"✅ EXPLAIN план сгенерирован для SQL: {sql[:50]}...")
                            logger.debug(f"   План (первые 200 символов): {plan[:200]}")
                            return plan
                        else:
                            logger.warning(f"⚠️ EXPLAIN план пустой после форматирования для SQL: {sql[:50]}...")
                            logger.warning(f"   plan_lines: {plan_lines}")
                            return None
                    else:
                        logger.warning(f"⚠️ Не удалось извлечь план из результата для SQL: {sql[:50]}...")
                        logger.warning(f"   Тип result: {type(result)}, len: {len(result) if result else 0}")
                        if result and len(result) > 0:
                            logger.warning(f"   Тип row: {type(result[0])}")
                            logger.warning(f"   row repr: {repr(result[0])}")
                            # Пробуем вывести все доступные ключи
                            try:
                                if hasattr(result[0], 'keys'):
                                    keys = list(result[0].keys())
                                    logger.warning(f"   Доступные ключи: {keys}")
                                    # Пробуем каждый ключ
                                    for key in keys:
                                        try:
                                            val = result[0][key]
                                            logger.warning(f"     {key} = {val[:100] if isinstance(val, str) else val}")
                                        except:
                                            pass
                            except Exception as e:
                                logger.warning(f"   Ошибка при проверке ключей: {e}")
                        return None
                else:
                    logger.warning(f"⚠️ EXPLAIN вернул пустой результат для SQL: {sql[:50]}...")
                    return None
                    
            except asyncpg.exceptions.SyntaxError as e:
                logger.error(f"❌ Синтаксическая ошибка в SQL при генерации плана: {e}")
                logger.error(f"   SQL: {sql}")
                import traceback
                logger.error(f"   Traceback: {traceback.format_exc()}")
                return None
            except asyncpg.exceptions.UndefinedTableError as e:
                logger.error(f"❌ Таблица не найдена при генерации плана: {e}")
                logger.error(f"   SQL: {sql}")
                import traceback
                logger.error(f"   Traceback: {traceback.format_exc()}")
                return None
            except asyncpg.exceptions.UndefinedColumnError as e:
                logger.error(f"❌ Колонка не найдена в SQL при генерации плана: {e}")
                logger.error(f"   SQL: {sql}")
                logger.error(f"   💡 Проверьте правильность имен колонок в SQL запросе")
                logger.error(f"   💡 Используйте скрипт: python src/tools/check_table_columns.py для проверки структуры таблицы")
                # Пытаемся извлечь имя таблицы из SQL для помощи пользователю
                import re
                table_match = re.search(r'FROM\s+(\w+)', sql, re.IGNORECASE)
                if table_match:
                    table_name = table_match.group(1)
                    logger.error(f"   💡 Проверьте структуру таблицы: {table_name}")
                import traceback
                logger.error(f"   Traceback: {traceback.format_exc()}")
                return None
            except Exception as e:
                logger.error(f"❌ Неожиданная ошибка при генерации EXPLAIN плана: {e}")
                logger.error(f"   SQL: {sql[:200]}...")
                logger.error(f"   Тип ошибки: {type(e).__name__}")
                import traceback
                logger.error(f"   Traceback: {traceback.format_exc()}")
                return None
            finally:
                await conn.close()
            
        except Exception as e:
            logger.error(f"❌ Не удалось подключиться к БД или сгенерировать EXPLAIN план: {e}")
            logger.error(f"   SQL: {sql[:100]}...")
            import traceback
            logger.error(f"   Traceback: {traceback.format_exc()}")
            return None
    
    async def add_question_sql(self, question: str, sql: str, **kwargs) -> str:
        """
        Добавление пары вопрос-SQL в векторную БД (асинхронная версия)
        
        Args:
            question: Вопрос на естественном языке
            sql: SQL запрос (оптимизированный вариант)
            **kwargs: Дополнительные параметры:
                - sql_basic: базовый (неоптимизированный) SQL для сравнения
                - sql_optimized: альтернативное название для sql (для совместимости)
                - improvement: описание улучшения производительности
                - domain: домен вопроса (users, payments, assignments, etc.)
                - tags: список тегов для категоризации
                - is_optimized: флаг, что это оптимизированный SQL
                - explain_plan: EXPLAIN план (если не указан, генерируется автоматически)
                
        Returns:
            str: ID добавленного элемента
        """
        try:
            import json
            
            # Определяем, является ли это оптимизированным SQL
            is_optimized = kwargs.get('is_optimized', False) or kwargs.get('sql_basic') is not None or kwargs.get('sql_optimized') is not None
            
            # Если sql_optimized указан, используем его как основной sql
            if kwargs.get('sql_optimized'):
                sql = kwargs['sql_optimized']
                logger.debug(f"Используется sql_optimized как основной SQL")
            
            # Флаг для генерации планов: только для оптимизированных SQL или если явно указано
            generate_plan = kwargs.get('generate_explain_plan', False)  # По умолчанию False для производительности
            if is_optimized:
                generate_plan = True  # Для оптимизированных SQL всегда генерируем план
                logger.info(f"🔍 Режим оптимизированного SQL: generate_plan={generate_plan}, is_optimized={is_optimized}")
                logger.info(f"   sql: {sql[:100]}...")
                logger.info(f"   sql_basic: {kwargs.get('sql_basic', 'None')[:100] if kwargs.get('sql_basic') else 'None'}...")
                logger.info(f"   sql_optimized: {kwargs.get('sql_optimized', 'None')[:100] if kwargs.get('sql_optimized') else 'None'}...")
            
            metadata = {
                'type': 'question_sql',
                'question': question,
                'sql': sql
            }
            
            # Генерируем EXPLAIN план только если нужно (для оптимизированных SQL или явно указано)
            explain_plan = kwargs.get('explain_plan')
            if explain_plan is None and generate_plan:
                try:
                    logger.info(f"🔄 Генерируем EXPLAIN план для оптимизированного SQL")
                    logger.info(f"   SQL для генерации плана: {sql[:150]}...")
                    logger.info(f"   generate_plan={generate_plan}, explain_plan из kwargs={kwargs.get('explain_plan')}")
                    explain_plan = await self._get_explain_plan(sql)
                    logger.info(f"📊 Результат _get_explain_plan: {'✅ План получен' if explain_plan else '❌ None вернулся'}")
                    if explain_plan:
                        logger.info(f"✅ EXPLAIN план сгенерирован для оптимизированного SQL")
                        logger.info(f"   План (первые 200 символов): {explain_plan[:200]}")
                    else:
                        logger.warning(f"⚠️ EXPLAIN план вернул None для оптимизированного SQL!")
                        logger.warning(f"   SQL: {sql[:200]}...")
                        logger.warning(f"   Проверьте логи выше для деталей ошибки")
                        logger.warning(f"   Возможные причины: ошибка SQL, таблица не существует, нет прав доступа")
                except Exception as e:
                    logger.error(f"❌ Исключение при генерации EXPLAIN плана для оптимизированного SQL: {e}")
                    logger.error(f"   SQL: {sql[:200]}...")
                    logger.error(f"   Тип ошибки: {type(e).__name__}")
                    import traceback
                    logger.error(f"   Traceback: {traceback.format_exc()}")
                    explain_plan = None
            
            # Добавляем план в metadata только если он есть
            if explain_plan:
                metadata['explain_plan'] = explain_plan
                logger.info(f"💾 План оптимизированного SQL сохранен в metadata")
            else:
                logger.warning(f"⚠️ План оптимизированного SQL НЕ сохранен в metadata (explain_plan=None)")
            
            # Для оптимизированных SQL генерируем план и для базового SQL (для сравнения)
            if is_optimized:
                metadata['is_optimized'] = True
                if kwargs.get('sql_basic'):
                    metadata['sql_basic'] = kwargs['sql_basic']
                    # Генерируем план для базового SQL только если генерируем планы
                    if generate_plan:
                        basic_plan = None
                        try:
                            logger.info(f"🔄 Генерируем EXPLAIN план для базового SQL: {kwargs['sql_basic'][:100]}...")
                            basic_plan = await self._get_explain_plan(kwargs['sql_basic'])
                            if basic_plan:
                                metadata['explain_plan_basic'] = basic_plan
                                logger.info(f"✅ EXPLAIN план для базового SQL сгенерирован")
                                logger.info(f"💾 План базового SQL сохранен в metadata")
                            else:
                                logger.warning(f"⚠️ EXPLAIN план вернул None для базового SQL!")
                                logger.warning(f"   SQL: {kwargs['sql_basic'][:200]}...")
                                logger.warning(f"⚠️ План базового SQL НЕ сохранен в metadata (basic_plan=None)")
                        except Exception as e:
                            logger.warning(f"⚠️ Не удалось сгенерировать EXPLAIN план для базового SQL: {e}")
                            basic_plan = None
                        
                        # ВАЛИДАЦИЯ: Проверяем, что оптимизированный SQL действительно лучше
                        # Валидация выполняется только если оба плана сгенерированы
                        if explain_plan and basic_plan:
                            # Извлекаем метрики из обоих планов
                            basic_metrics = self._extract_plan_metrics(basic_plan)
                            optimized_metrics = self._extract_plan_metrics(explain_plan)
                            
                            basic_cost = basic_metrics.get('cost')
                            optimized_cost = optimized_metrics.get('cost')
                            basic_width = basic_metrics.get('width')
                            optimized_width = optimized_metrics.get('width')
                            basic_rows = basic_metrics.get('rows')
                            optimized_rows = optimized_metrics.get('rows')
                            
                            # Сохраняем все метрики в metadata
                            metadata['cost_basic'] = basic_cost
                            metadata['cost_optimized'] = optimized_cost
                            metadata['width_basic'] = basic_width
                            metadata['width_optimized'] = optimized_width
                            metadata['rows_basic'] = basic_rows
                            metadata['rows_optimized'] = optimized_rows
                            
                            # Проверяем улучшение по нескольким критериям
                            improvements = []
                            
                            # 1. Cost улучшение
                            if basic_cost is not None and optimized_cost is not None:
                                cost_improvement = (basic_cost - optimized_cost) / basic_cost * 100
                                improvements.append(('cost', cost_improvement))
                                metadata['cost_improvement_percent'] = round(cost_improvement, 2)
                            
                            # 2. Width улучшение (размер данных) - важный показатель!
                            if basic_width is not None and optimized_width is not None:
                                width_improvement = (basic_width - optimized_width) / basic_width * 100
                                improvements.append(('width', width_improvement))
                                metadata['width_improvement_percent'] = round(width_improvement, 2)
                            
                            # 3. Rows улучшение (количество строк)
                            if basic_rows is not None and optimized_rows is not None:
                                rows_improvement = (basic_rows - optimized_rows) / basic_rows * 100 if basic_rows > 0 else 0
                                improvements.append(('rows', rows_improvement))
                                metadata['rows_improvement_percent'] = round(rows_improvement, 2)
                            
                            # Валидация: оптимизированный SQL лучше если:
                            # - cost меньше ИЛИ
                            # - width меньше (меньше данных) ИЛИ  
                            # - rows меньше (меньше строк)
                            # Хотя бы ОДИН критерий должен быть лучше
                            is_better = False
                            better_criteria = []
                            
                            if optimized_cost is not None and basic_cost is not None:
                                if optimized_cost < basic_cost:
                                    is_better = True
                                    better_criteria.append('cost')
                            
                            if optimized_width is not None and basic_width is not None:
                                if optimized_width < basic_width:
                                    is_better = True
                                    better_criteria.append('width')
                            
                            if optimized_rows is not None and basic_rows is not None:
                                if optimized_rows < basic_rows:
                                    is_better = True
                                    better_criteria.append('rows')
                            
                            if is_better:
                                improvement_summary = ", ".join([f"{metric}: {imp:.2f}%" for metric, imp in improvements])
                                criteria_str = ", ".join(better_criteria) if better_criteria else "неизвестно"
                                logger.info(
                                    f"✅ Валидация пройдена: оптимизированный SQL лучше "
                                    f"(улучшения: {improvement_summary}, лучшие критерии: {criteria_str})"
                                )
                                metadata['optimization_validated'] = True
                                # Общее улучшение (среднее или максимальное)
                                if improvements:
                                    avg_improvement = sum(imp for _, imp in improvements) / len(improvements)
                                    metadata['cost_improvement_percent'] = round(avg_improvement, 2)
                            else:
                                # Оптимизированный SQL не лучше или хуже базового!
                                warning_msg = (
                                    f"⚠️ ВНИМАНИЕ: Оптимизированный SQL НЕ лучше базового!\n"
                                    f"   Базовый: cost={basic_cost}, width={basic_width}, rows={basic_rows}\n"
                                    f"   Оптимизированный: cost={optimized_cost}, width={optimized_width}, rows={optimized_rows}\n"
                                    f"   Рекомендуется проверить правильность оптимизации."
                                )
                                logger.warning(warning_msg)
                                metadata['optimization_validated'] = False
                                metadata['optimization_warning'] = warning_msg
                                if improvements:
                                    avg_improvement = sum(imp for _, imp in improvements) / len(improvements)
                                    metadata['cost_improvement_percent'] = round(avg_improvement, 2)
                        else:
                            logger.warning(
                                "⚠️ Не удалось извлечь метрики из планов для валидации. "
                                "Проверка оптимизации пропущена."
                            )
                            metadata['optimization_validated'] = None
                            logger.warning(f"   explain_plan: {'✅' if explain_plan else '❌'}, basic_plan: {'✅' if basic_plan else '❌'}")
                if kwargs.get('sql_optimized'):
                    metadata['sql_optimized'] = kwargs['sql_optimized']
                if kwargs.get('improvement'):
                    metadata['improvement'] = kwargs['improvement']
            
            # Добавляем дополнительные метаданные
            if kwargs.get('domain'):
                metadata['domain'] = kwargs['domain']
            if kwargs.get('tags'):
                metadata['tags'] = kwargs['tags']
            
            metadata_json = json.dumps(metadata, ensure_ascii=False)
            
            # Логируем что сохраняется в metadata
            logger.info(f"📦 Metadata перед сохранением:")
            logger.info(f"   explain_plan: {'✅' if metadata.get('explain_plan') else '❌'}")
            logger.info(f"   explain_plan_basic: {'✅' if metadata.get('explain_plan_basic') else '❌'}")
            logger.info(f"   is_optimized: {metadata.get('is_optimized', False)}")
            
            # Формируем content с явной маркировкой для оптимизированных SQL
            # Это помогает агенту (LLM) сразу видеть оптимизированные примеры в контексте
            if is_optimized:
                # Для оптимизированных SQL добавляем явную маркировку в начало content
                # Формат: [OPTIMIZED SQL] - видно агенту при чтении контекста
                improvement_text = kwargs.get('improvement', '')
                opt_marker = "[OPTIMIZED SQL]"
                if improvement_text:
                    opt_marker = f"[OPTIMIZED SQL: {improvement_text}]"
                content = f"{opt_marker}\nQ: {question}\nA: {sql}"
                # Добавляем базовый SQL для сравнения, если есть
                if kwargs.get('sql_basic'):
                    content += f"\n[BASIC SQL (for comparison)]: {kwargs['sql_basic']}"
            else:
                content = f"Q: {question}\nA: {sql}"
            
            # Подключаемся к БД
            conn = await asyncpg.connect(self.database_url)
            
            # Добавляем запись
            logger.info(f"💾 Сохранение в БД: content_type=question_sql")
            result = await conn.fetchrow("""
                INSERT INTO vanna_vectors (content, content_type, metadata)
                VALUES ($1, $2, $3::jsonb)
                RETURNING id
            """, content, 'question_sql', metadata_json)
            
            await conn.close()
            
            example_id = str(result['id'])
            opt_info = " (оптимизированный)" if is_optimized else ""
            plan_info = " с планом" if explain_plan else ""
            logger.info(f"✅ Вопрос-SQL{opt_info}{plan_info} добавлен с ID: {example_id}")
            logger.info(f"   Планы в metadata при сохранении: explain_plan={'✅' if metadata.get('explain_plan') else '❌'}, explain_plan_basic={'✅' if metadata.get('explain_plan_basic') else '❌'}")
            
            return example_id
            
        except Exception as e:
            logger.error(f"❌ Ошибка добавления вопроса-SQL: {e}")
            raise
    
    async def _semantic_search(self, question: str, content_type: str, limit: int) -> List[str]:
        """Семантический поиск релевантного контента"""
        try:
            # Генерируем эмбеддинг для вопроса
            question_embedding = await self._generate_embedding(question)
            if not question_embedding:
                return []
            
            # Подключаемся к БД
            conn = await asyncpg.connect(self.database_url)
            
            # Конвертируем эмбеддинг в строку для pgvector
            embedding_str = '[' + ','.join(map(str, question_embedding)) + ']'
            
            # Семантический поиск с использованием cosine distance
            query = """
                SELECT content, embedding <-> $1::vector as distance
                FROM vanna_vectors 
                WHERE content_type = $2 AND embedding IS NOT NULL
                ORDER BY embedding <-> $1::vector
                LIMIT $3
            """
            
            results = await conn.fetch(query, embedding_str, content_type, limit)
            await conn.close()
            
            # Извлекаем только контент, отсортированный по релевантности
            content = [row['content'] for row in results]
            
            logger.info(f"✅ Семантический поиск: найдено {len(content)} релевантных {content_type}")
            return content
            
        except Exception as e:
            logger.error(f"❌ Ошибка семантического поиска {content_type}: {e}")
            return []
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """Генерация эмбеддинга для текста (HF модель настраивается через HF_MODEL_NAME)."""
        try:
            from sentence_transformers import SentenceTransformer
            
            model_name = os.getenv('HF_MODEL_NAME', 'sentence-transformers/all-MiniLM-L6-v2')
            
            # Кешируем модель для повторного использования
            if self._embedding_model is None or self._embedding_model_name != model_name:
                logger.info(f"Loading embedding model: {model_name}")
                self._embedding_model = SentenceTransformer(model_name)
                self._embedding_model_name = model_name
                test_dim = len(self._embedding_model.encode(["test"], normalize_embeddings=True)[0])
                logger.info(f"Embedding model dimension: {test_dim}")
            
            vec = self._embedding_model.encode(text, normalize_embeddings=True)
            return vec.tolist()
        except Exception as e:
            logger.error(f"❌ Ошибка генерации эмбеддинга: {e}")
            return []
    
    def run_sql(self, sql: str) -> pd.DataFrame:
        """Выполнение SQL запроса (синхронная версия для совместимости)"""
        try:
            # Для совместимости с Vanna AI - используем синхронную версию
            import psycopg2
            conn = psycopg2.connect(self.database_url)
            df = pd.read_sql(sql, conn)
            conn.close()
            
            logger.info(f"✅ SQL выполнен успешно, получено {len(df)} строк")
            return df
            
        except Exception as e:
            logger.error(f"❌ Ошибка выполнения SQL: {e}")
            return pd.DataFrame()

class DocStructureVannaSemantic(DocStructureVectorDBSemantic):
    """
    Vanna AI клиент с семантическим поиском
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
        # Настройка OpenAI клиента для генерации SQL
        self.openai_client = OpenAI(
            api_key=config.get("api_key", os.getenv("PROXYAPI_KEY")),
            base_url=config.get("base_url", "https://api.proxyapi.ru/openai/v1")
        )
        self.model = config.get("model", "gpt-4o")
        self.temperature = config.get("temperature", 0.2)
        
        logger.info("✅ DocStructureVannaSemantic инициализирован")
    
    def generate_sql(self, question: str) -> str:
        """
        Генерация SQL с семантическим поиском контекста
        """
        try:
            # Получаем релевантный контекст через семантический поиск
            context_parts = []
            
            # Получаем DDL (синхронная версия)
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Если event loop уже запущен, используем create_task
                    ddl_task = asyncio.create_task(self.get_related_ddl(question))
                    ddl_list = loop.run_until_complete(ddl_task)
                else:
                    ddl_list = asyncio.run(self.get_related_ddl(question))
            except:
                ddl_list = []
            
            if ddl_list:
                context_parts.append("\n".join(ddl_list))
            
            # Получаем документацию
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    docs_task = asyncio.create_task(self.get_related_documentation(question))
                    docs_list = loop.run_until_complete(docs_task)
                else:
                    docs_list = asyncio.run(self.get_related_documentation(question))
            except:
                docs_list = []
            
            if docs_list:
                context_parts.append("\n".join(docs_list))
            
            # Получаем Q/A пары
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    qa_task = asyncio.create_task(self.get_similar_question_sql(question))
                    qa_list = loop.run_until_complete(qa_task)
                else:
                    qa_list = asyncio.run(self.get_similar_question_sql(question))
            except:
                qa_list = []
            
            if qa_list:
                context_parts.append("\n".join(qa_list))
            
            context = "\n\n".join(context_parts)
            
            # Создаем промпт с семантически релевантным контекстом
            prompt = f"""
You are a postgresql expert. Please help to generate a SQL query to answer the question. Your response should ONLY be based on the given context and follow the response guidelines and format instructions.

===Tables

===Additional Context

{context}

===Response Guidelines
1. If the provided context is sufficient, please generate a valid SQL query without any explanations for the question.
2. If the provided context is almost sufficient but requires knowledge of a specific string in a particular column, please generate an intermediate SQL query to find the distinct strings in that column. Prepend the query with a comment saying intermediate_sql
3. If the provided context is insufficient, please explain why it can't be generated.
4. Please use the most relevant table(s).
5. If the question has been asked and answered before, please repeat the answer exactly as it was given before.
6. Ensure that the output SQL is postgresql-compliant and executable, and free of syntax errors.
"""
            
            # Генерируем SQL с помощью LLM
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=1000
            )
            
            sql = response.choices[0].message.content.strip()
            logger.info(f"✅ SQL сгенерирован с семантическим контекстом: {sql[:100]}...")
            return sql
            
        except Exception as e:
            logger.error(f"❌ Ошибка генерации SQL: {e}")
            return f"SELECT * FROM {question}"

# Функция для создания клиента
def create_semantic_vanna_client(use_proxyapi: bool = True) -> DocStructureVannaSemantic:
    """
    Создание Vanna AI клиента с семантическим поиском
    """
    config = {
        "database_url": "postgresql://postgres:1234@localhost:5432/test_docstructure",
        "vector_table": "vanna_vectors"
    }
    
    if use_proxyapi:
        config.update({
            "api_key": os.getenv("PROXYAPI_KEY") or os.getenv("PROXYAPI_API_KEY"),
            "base_url": os.getenv("OPENAI_BASE_URL", "https://api.proxyapi.ru/openai/v1"),
            "model": os.getenv("PROXYAPI_CHAT_MODEL", "gpt-4o"),
            "temperature": float(os.getenv("PROXYAPI_TEMPERATURE", "0.2"))
        })
    else:
        config.update({
            "api_key": os.getenv("OPENAI_API_KEY"),
            "model": "gpt-3.5-turbo"
        })
    
    return DocStructureVannaSemantic(config=config)
