#!/usr/bin/env python3
"""
Оптимизированный двухмодельный пайплайн
Включает улучшенную логику контекста и приоритизацию таблиц
"""

import os
import logging
import time
from typing import Optional, Dict, Any, List
from pathlib import Path
import sys

# Добавляем путь к модулям
sys.path.append(str(Path(__file__).parent.parent))

from src.vanna.vanna_pgvector_native import DocStructureVannaNative
from src.vanna.vanna_fixed_context import DocStructureVannaFixed

logger = logging.getLogger(__name__)

class OptimizedDualPipeline:
    """
    Оптимизированный двухмодельный пайплайн
    Включает улучшенную логику контекста и приоритизацию таблиц
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Инициализация оптимизированного пайплайна
        
        Args:
            config: Конфигурация для обеих моделей
        """
        if config is None:
            config = {}
            
        self.config = config
        
        # Конфигурация для GPT-4o (основная модель)
        self.gpt4_config = {
            'model': 'gpt-4o',
            'database_url': 'postgresql://postgres:1234@localhost:5432/test_docstructure',
            'api_key': os.getenv('PROXYAPI_KEY') or os.getenv('PROXYAPI_API_KEY') or os.getenv('OPENAI_API_KEY'),
            'base_url': os.getenv('OPENAI_BASE_URL', 'https://api.proxyapi.ru/openai/v1'),
            'temperature': float(os.getenv('LLM_TEMPERATURE', '0.2'))
        }
        
        # Конфигурация для Ollama (резервная модель)
        self.ollama_config = {
            'model': os.getenv('OLLAMA_MODEL', 'llama3:latest'),
            'database_url': 'postgresql://postgres:1234@localhost:5432/test_docstructure',
            'api_key': 'ollama',
            'base_url': os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434/v1'),
            'temperature': float(os.getenv('LLM_TEMPERATURE', '0.2'))
        }
        
        # Конфигурация для SQLCoder (специализированная SQL модель)
        self.sqlcoder_config = {
            'model': 'sqlcoder:latest',
            'database_url': 'postgresql://postgres:1234@localhost:5432/test_docstructure',
            'api_key': 'ollama',
            'base_url': os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434/v1'),
            'temperature': float(os.getenv('LLM_TEMPERATURE', '0.2'))
        }
        
        # Объединяем с переданной конфигурацией
        self.gpt4_config.update(config.get('gpt4', {}))
        self.ollama_config.update(config.get('ollama', {}))
        self.sqlcoder_config.update(config.get('sqlcoder', {}))
        
        # Инициализируем агентов
        self.gpt4_agent = None
        self.ollama_agent = None
        self.sqlcoder_agent = None
        self.current_model = None
        
        # Приоритетные бизнес-таблицы
        self.priority_tables = [
            "equsers",                    # Пользователи
            "eq_departments",             # Отделы
            "eqgroups",                   # Группы
            "eqroles",                    # Роли
            "tbl_business_unit",          # Клиенты
            "tbl_principal_assignment",  # Поручения
            "tbl_incoming_payments",      # Платежи
            "tbl_accounts_document",      # Учетные записи
            "tbl_personal_account"        # Личные кабинеты
        ]
        
        # Системные таблицы для исключения
        self.system_tables = [
            "views", "view_table_usage", "vanna_vectors",
            "information_schema", "pg_catalog", "pg_*"
        ]
        
        # Статистика использования
        self.usage_stats = {
            'gpt4': {'calls': 0, 'success': 0, 'errors': 0, 'total_time': 0},
            'ollama': {'calls': 0, 'success': 0, 'errors': 0, 'total_time': 0},
            'sqlcoder': {'calls': 0, 'success': 0, 'errors': 0, 'total_time': 0}
        }
        
        logger.info("✅ OptimizedDualPipeline инициализирован")
    
    def _init_gpt4_agent(self) -> bool:
        """Инициализация GPT-4o агента"""
        try:
            if self.gpt4_agent is None:
                self.gpt4_agent = DocStructureVannaNative(self.gpt4_config)
                logger.info("✅ GPT-4o агент инициализирован")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации GPT-4o: {e}")
            return False
    
    def _init_ollama_agent(self) -> bool:
        """Инициализация Ollama агента"""
        try:
            if self.ollama_agent is None:
                self.ollama_agent = DocStructureVannaNative(self.ollama_config)
                logger.info("✅ Ollama агент инициализирован")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации Ollama: {e}")
            return False
    
    def _init_sqlcoder_agent(self) -> bool:
        """Инициализация SQLCoder агента"""
        try:
            if self.sqlcoder_agent is None:
                self.sqlcoder_agent = DocStructureVannaNative(self.sqlcoder_config)
                logger.info("✅ SQLCoder агент инициализирован")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации SQLCoder: {e}")
            return False
    
    def _get_optimized_context(self, question: str, agent: DocStructureVannaNative) -> str:
        """
        Получение оптимизированного контекста с приоритизацией бизнес-таблиц
        
        Args:
            question: Вопрос
            agent: Агент для получения контекста
            
        Returns:
            str: Оптимизированный контекст
        """
        try:
            context_parts = []
            
            # 1. Получаем DDL для приоритетных бизнес-таблиц
            for table in self.priority_tables:
                try:
                    ddl_query = f"""
                    SELECT 
                        table_name, column_name, data_type, is_nullable, 
                        column_default, character_maximum_length
                    FROM information_schema.columns 
                    WHERE table_name = '{table}' AND table_schema = 'public'
                    ORDER BY ordinal_position
                    """
                    
                    df = agent.run_sql(ddl_query)
                    
                    if not df.empty:
                        table_ddl = f"Таблица {table}:\n"
                        table_ddl += f"Колонки: {', '.join(df['column_name'].tolist())}\n"
                        
                        for _, row in df.iterrows():
                            col_info = f"- {row['column_name']}: {row['data_type']}"
                            if row['is_nullable'] == 'NO':
                                col_info += " (NOT NULL)"
                            if row['character_maximum_length']:
                                col_info += f"({row['character_maximum_length']})"
                            table_ddl += col_info + "\n"
                        
                        context_parts.append(table_ddl)
                        
                except Exception as e:
                    logger.warning(f"⚠️ Не удалось получить DDL для {table}: {e}")
                    continue
            
            # 2. Получаем связанную документацию
            try:
                docs_list = agent.get_related_documentation(question)
                if docs_list:
                    context_parts.extend(docs_list)
            except Exception as e:
                logger.warning(f"⚠️ Ошибка получения документации: {e}")
            
            # 3. Получаем похожие Q/A
            try:
                qa_list = agent.get_similar_question_sql(question)
                if qa_list:
                    context_parts.extend(qa_list)
            except Exception as e:
                logger.warning(f"⚠️ Ошибка получения Q/A: {e}")
            
            # Объединяем контекст
            context = "\n\n".join(context_parts)
            
            logger.info(f"✅ Получен оптимизированный контекст из {len(context_parts)} источников")
            return context
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения оптимизированного контекста: {e}")
            return ""
    
    def _generate_sql_with_optimized_context(self, question: str, agent: DocStructureVannaNative) -> str:
        """
        Генерация SQL с оптимизированным контекстом
        
        Args:
            question: Вопрос
            agent: Агент для генерации
            
        Returns:
            str: Сгенерированный SQL
        """
        try:
            # Используем стандартный метод Vanna AI (контекст уже оптимизирован в get_related_ddl)
            response = agent.generate_sql(question)
            return response
            
        except Exception as e:
            logger.error(f"❌ Ошибка генерации SQL с оптимизированным контекстом: {e}")
            return f"Ошибка генерации SQL: {e}"
    
    def generate_sql(self, question: str, prefer_model: str = 'auto', timeout: int = 30) -> Dict[str, Any]:
        """
        Генерация SQL с оптимизированным контекстом
        
        Args:
            question: Вопрос на естественном языке
            prefer_model: Предпочитаемая модель ('gpt4', 'ollama', 'auto')
            timeout: Таймаут для запроса в секундах
            
        Returns:
            Dict с результатом генерации
        """
        start_time = time.time()
        
        # Определяем порядок моделей
        if prefer_model == 'gpt4':
            models_order = ['gpt4', 'sqlcoder', 'ollama']
        elif prefer_model == 'ollama':
            models_order = ['ollama', 'sqlcoder', 'gpt4']
        elif prefer_model == 'sqlcoder':
            models_order = ['sqlcoder', 'gpt4', 'ollama']
        else:  # auto
            models_order = ['gpt4', 'sqlcoder', 'ollama']  # GPT-4o по умолчанию
        
        for model_name in models_order:
            try:
                logger.info(f"🔄 Попытка генерации SQL с {model_name}...")
                
                if model_name == 'gpt4':
                    if not self._init_gpt4_agent():
                        continue
                    agent = self.gpt4_agent
                elif model_name == 'sqlcoder':
                    if not self._init_sqlcoder_agent():
                        continue
                    agent = self.sqlcoder_agent
                else:  # ollama
                    if not self._init_ollama_agent():
                        continue
                    agent = self.ollama_agent
                
                # Генерируем SQL с оптимизированным контекстом
                model_start = time.time()
                sql = self._generate_sql_with_optimized_context(question, agent)
                model_end = time.time()
                
                # Обновляем статистику
                self.usage_stats[model_name]['calls'] += 1
                self.usage_stats[model_name]['success'] += 1
                self.usage_stats[model_name]['total_time'] += (model_end - model_start)
                
                self.current_model = model_name
                total_time = time.time() - start_time
                
                result = {
                    'success': True,
                    'sql': sql,
                    'model': model_name,
                    'time': total_time,
                    'model_time': model_end - model_start,
                    'question': question,
                    'context_used': True
                }
                
                logger.info(f"✅ SQL сгенерирован с {model_name} за {total_time:.2f} сек")
                return result
                
            except Exception as e:
                logger.warning(f"⚠️ Ошибка с {model_name}: {e}")
                self.usage_stats[model_name]['errors'] += 1
                continue
        
        # Если все модели не сработали
        total_time = time.time() - start_time
        return {
            'success': False,
            'error': 'Все модели недоступны',
            'time': total_time,
            'question': question
        }
    
    def train_on_schema(self) -> bool:
        """Обучение на схеме БД для обеих моделей"""
        success_count = 0
        
        # Обучаем GPT-4o
        if self._init_gpt4_agent():
            try:
                logger.info("📚 Обучение GPT-4o на схеме БД...")
                schema_query = "SELECT * FROM INFORMATION_SCHEMA.COLUMNS"
                df_schema = self.gpt4_agent.run_sql(schema_query)
                plan = self.gpt4_agent.get_training_plan_generic(df_schema)
                self.gpt4_agent.train(plan=plan)
                logger.info("✅ GPT-4o обучен на схеме")
                success_count += 1
            except Exception as e:
                logger.error(f"❌ Ошибка обучения GPT-4o: {e}")
        
        # Обучаем Ollama
        if self._init_ollama_agent():
            try:
                logger.info("📚 Обучение Ollama на схеме БД...")
                schema_query = "SELECT * FROM INFORMATION_SCHEMA.COLUMNS"
                df_schema = self.ollama_agent.run_sql(schema_query)
                plan = self.ollama_agent.get_training_plan_generic(df_schema)
                self.ollama_agent.train(plan=plan)
                logger.info("✅ Ollama обучен на схеме")
                success_count += 1
            except Exception as e:
                logger.error(f"❌ Ошибка обучения Ollama: {e}")
        
        # Обучаем SQLCoder
        if self._init_sqlcoder_agent():
            try:
                logger.info("📚 Обучение SQLCoder на схеме БД...")
                schema_query = "SELECT * FROM INFORMATION_SCHEMA.COLUMNS"
                df_schema = self.sqlcoder_agent.run_sql(schema_query)
                plan = self.sqlcoder_agent.get_training_plan_generic(df_schema)
                self.sqlcoder_agent.train(plan=plan)
                logger.info("✅ SQLCoder обучен на схеме")
                success_count += 1
            except Exception as e:
                logger.error(f"❌ Ошибка обучения SQLCoder: {e}")
        
        return success_count > 0
    
    def train_on_examples(self, examples: List[Dict[str, str]]) -> bool:
        """Обучение на примерах для обеих моделей"""
        success_count = 0
        
        for example in examples:
            question = example.get('question', '')
            sql = example.get('sql', '')
            
            if not question or not sql:
                continue
            
            # Обучаем GPT-4o
            if self._init_gpt4_agent():
                try:
                    self.gpt4_agent.train(question=question, sql=sql)
                except Exception as e:
                    logger.warning(f"⚠️ Ошибка обучения GPT-4o на примере: {e}")
            
            # Обучаем Ollama
            if self._init_ollama_agent():
                try:
                    self.ollama_agent.train(question=question, sql=sql)
                except Exception as e:
                    logger.warning(f"⚠️ Ошибка обучения Ollama на примере: {e}")
            
            # Обучаем SQLCoder
            if self._init_sqlcoder_agent():
                try:
                    self.sqlcoder_agent.train(question=question, sql=sql)
                except Exception as e:
                    logger.warning(f"⚠️ Ошибка обучения SQLCoder на примере: {e}")
        
        logger.info(f"✅ Обучение на {len(examples)} примерах завершено")
        return True
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Получение статистики использования"""
        stats = {}
        
        for model_name, model_stats in self.usage_stats.items():
            if model_stats['calls'] > 0:
                stats[model_name] = {
                    'calls': model_stats['calls'],
                    'success_rate': model_stats['success'] / model_stats['calls'],
                    'error_rate': model_stats['errors'] / model_stats['calls'],
                    'avg_time': model_stats['total_time'] / model_stats['success'] if model_stats['success'] > 0 else 0
                }
            else:
                stats[model_name] = {
                    'calls': 0,
                    'success_rate': 0,
                    'error_rate': 0,
                    'avg_time': 0
                }
        
        return stats
    
    def health_check(self) -> Dict[str, bool]:
        """Проверка здоровья обеих моделей"""
        health = {}
        
        # Проверяем GPT-4o
        try:
            if self._init_gpt4_agent():
                # Простой тест
                test_result = self.gpt4_agent.generate_sql("SELECT 1")
                health['gpt4'] = True
            else:
                health['gpt4'] = False
        except Exception as e:
            logger.warning(f"⚠️ GPT-4o недоступен: {e}")
            health['gpt4'] = False
        
        # Проверяем Ollama
        try:
            if self._init_ollama_agent():
                # Простой тест
                test_result = self.ollama_agent.generate_sql("SELECT 1")
                health['ollama'] = True
            else:
                health['ollama'] = False
        except Exception as e:
            logger.warning(f"⚠️ Ollama недоступен: {e}")
            health['ollama'] = False
        
        # Проверяем SQLCoder
        try:
            if self._init_sqlcoder_agent():
                # Простой тест
                test_result = self.sqlcoder_agent.generate_sql("SELECT 1")
                health['sqlcoder'] = True
            else:
                health['sqlcoder'] = False
        except Exception as e:
            logger.warning(f"⚠️ SQLCoder недоступен: {e}")
            health['sqlcoder'] = False
        
        return health

def create_optimized_dual_pipeline(config: Optional[Dict[str, Any]] = None) -> OptimizedDualPipeline:
    """
    Создание оптимизированного двухмодельного пайплайна
    
    Args:
        config: Конфигурация
        
    Returns:
        OptimizedDualPipeline: Настроенный пайплайн
    """
    return OptimizedDualPipeline(config)

if __name__ == "__main__":
    # Тестирование пайплайна
    pipeline = OptimizedDualPipeline()
    
    # Проверка здоровья
    health = pipeline.health_check()
    print(f"Здоровье моделей: {health}")
    
    # Тест генерации
    result = pipeline.generate_sql("Покажи всех пользователей")
    print(f"Результат: {result}")
    
    # Статистика
    stats = pipeline.get_usage_stats()
    print(f"Статистика: {stats}")
