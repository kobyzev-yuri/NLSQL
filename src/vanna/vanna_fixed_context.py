#!/usr/bin/env python3
"""
Vanna AI с исправленной логикой получения контекста
"""

import os
import logging
from typing import Optional, Dict, Any, List
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor

try:
    from vanna.openai import OpenAI_Chat
except ImportError:
    from vanna.base import VannaBase
    class OpenAI_Chat(VannaBase):
        def __init__(self, **kwargs):
            super().__init__()
            self.config = kwargs

from vanna.base import VannaBase

logger = logging.getLogger(__name__)

class DocStructureVectorDBFixed(VannaBase):
    """
    Исправленная векторная БД для DocStructureSchema
    с правильной логикой получения контекста
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Инициализация векторной БД с исправленной логикой
        """
        if config is None:
            config = {}
            
        self.config = config
        self.database_url = config.get("database_url", "postgresql://postgres:1234@localhost:5432/test_docstructure")
        self.vector_table = config.get("vector_table", "vanna_vectors")
        
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
            "tbl_personal_account"         # Личные кабинеты
        ]
        
        # Инициализируем подключение к PostgreSQL
        self._init_postgres_connection()
        
        logger.info("✅ DocStructureVectorDBFixed инициализирован")
    
    def _init_postgres_connection(self):
        """Инициализация подключения к PostgreSQL"""
        try:
            self.conn = psycopg2.connect(self.database_url)
            logger.info("✅ Подключение к PostgreSQL установлено")
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к PostgreSQL: {e}")
            raise
    
    def add_ddl(self, ddl: str, **kwargs) -> str:
        """Добавление DDL в векторную БД"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO vanna_vectors (content, content_type, metadata)
                    VALUES (%s, %s, %s)
                    RETURNING id
                """, (ddl, 'ddl', '{}'))
                
                result = cur.fetchone()
                self.conn.commit()
                
                logger.info("✅ DDL добавлен в векторную БД")
                return str(result[0])
                
        except Exception as e:
            logger.error(f"❌ Ошибка добавления DDL: {e}")
            raise
    
    def add_documentation(self, doc: str, **kwargs) -> str:
        """Добавление документации в векторную БД"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO vanna_vectors (content, content_type, metadata)
                    VALUES (%s, %s, %s)
                    RETURNING id
                """, (doc, 'documentation', '{}'))
                
                result = cur.fetchone()
                self.conn.commit()
                
                logger.info("✅ Документация добавлена в векторную БД")
                return str(result[0])
                
        except Exception as e:
            logger.error(f"❌ Ошибка добавления документации: {e}")
            raise
    
    def add_question_sql(self, question: str, sql: str, **kwargs) -> str:
        """Добавление вопроса и SQL в векторную БД"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO vanna_vectors (content, content_type, metadata)
                    VALUES (%s, %s, %s)
                    RETURNING id
                """, (f"Q: {question}\nA: {sql}", 'question_sql', '{}'))
                
                result = cur.fetchone()
                self.conn.commit()
                
                logger.info("✅ Вопрос и SQL добавлены в векторную БД")
                return str(result[0])
                
        except Exception as e:
            logger.error(f"❌ Ошибка добавления вопроса и SQL: {e}")
            raise
    
    def get_related_ddl(self, question: str, **kwargs) -> List[str]:
        """Получение связанных DDL с исправленной логикой"""
        try:
            # Проверяем подключение
            if not hasattr(self, 'conn') or self.conn is None:
                logger.error("❌ Нет подключения к базе данных")
                return []
                
            # Получаем DDL для приоритетных таблиц
            ddl_list = []
            
            for table in self.priority_tables:
                try:
                    # Получаем DDL для таблицы
                    ddl_query = f"""
                    SELECT 
                        table_name,
                        column_name,
                        data_type,
                        is_nullable,
                        column_default,
                        character_maximum_length
                    FROM information_schema.columns 
                    WHERE table_name = '{table}'
                    AND table_schema = 'public'
                    ORDER BY ordinal_position
                    """
                    
                    with self.conn.cursor() as cur:
                        cur.execute(ddl_query)
                        results = cur.fetchall()
                        
                        if results:
                            # Формируем DDL для таблицы
                            table_ddl = f"Таблица {table}:\n"
                            table_ddl += f"Колонки: {', '.join([row[1] for row in results])}\n"
                            
                            for row in results:
                                col_name, data_type, is_nullable = row[1], row[2], row[3]
                                col_info = f"- {col_name}: {data_type}"
                                if is_nullable == 'NO':
                                    col_info += " (NOT NULL)"
                                table_ddl += col_info + "\n"
                            
                            ddl_list.append(table_ddl)
                            
                except Exception as e:
                    logger.warning(f"⚠️ Не удалось получить DDL для таблицы {table}: {e}")
                    continue
            
            logger.info(f"✅ Получено {len(ddl_list)} DDL для приоритетных таблиц")
            return ddl_list
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения DDL: {e}")
            return []
    
    def get_related_documentation(self, question: str, **kwargs) -> List[str]:
        """Получение связанной документации"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT content FROM vanna_vectors 
                    WHERE content_type = 'documentation'
                    ORDER BY created_at DESC
                    LIMIT 5
                """)
                
                results = cur.fetchall()
                docs = [row[0] for row in results]
                
                logger.info(f"✅ Получено {len(docs)} документов")
                return docs
                
        except Exception as e:
            logger.error(f"❌ Ошибка получения документации: {e}")
            return []
    
    def get_similar_question_sql(self, question: str, **kwargs) -> List[str]:
        """Получение похожих вопросов и SQL"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT content FROM vanna_vectors 
                    WHERE content_type = 'question_sql'
                    ORDER BY created_at DESC
                    LIMIT 5
                """)
                
                results = cur.fetchall()
                qa_pairs = [row[0] for row in results]
                
                logger.info(f"✅ Получено {len(qa_pairs)} Q/A пар")
                return qa_pairs
                
        except Exception as e:
            logger.error(f"❌ Ошибка получения Q/A пар: {e}")
            return []
    
    def get_training_data(self, **kwargs) -> pd.DataFrame:
        """Получение всех данных для обучения"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT id, content, content_type, metadata, created_at
                    FROM vanna_vectors
                    ORDER BY created_at DESC
                """)
                
                results = cur.fetchall()
                columns = ['id', 'content', 'content_type', 'metadata', 'created_at']
                return pd.DataFrame(results, columns=columns)
                
        except Exception as e:
            logger.error(f"❌ Ошибка получения данных обучения: {e}")
            return pd.DataFrame()
    
    def remove_training_data(self, id: str, **kwargs) -> bool:
        """Удаление данных обучения"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("DELETE FROM vanna_vectors WHERE id = %s", (id,))
                self.conn.commit()
                
                logger.info(f"✅ Данные с ID {id} удалены")
                return True
                
        except Exception as e:
            logger.error(f"❌ Ошибка удаления данных: {e}")
            return False
    
    def _create_vector_table(self):
        """Создание таблицы векторов"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS vanna_vectors (
                        id SERIAL PRIMARY KEY,
                        content TEXT NOT NULL,
                        content_type VARCHAR(50) NOT NULL,
                        metadata JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                self.conn.commit()
                
                logger.info("✅ Таблица vanna_vectors создана")
                
        except Exception as e:
            logger.error(f"❌ Ошибка создания таблицы векторов: {e}")
            raise
    
    def generate_embedding(self, text: str, **kwargs) -> List[float]:
        """Генерация эмбеддинга для текста"""
        # Упрощенная реализация - возвращаем пустой список
        # В реальной реализации здесь должен быть вызов модели эмбеддингов
        return []
    
    def run_sql(self, sql: str) -> pd.DataFrame:
        """Выполнение SQL запроса"""
        try:
            with self.conn.cursor() as cur:
                cur.execute(sql)
                results = cur.fetchall()
                
                columns = [desc[0] for desc in cur.description] if cur.description else []
                df = pd.DataFrame(results, columns=columns)
                
                logger.info(f"✅ SQL выполнен успешно, получено {len(df)} строк")
                return df
                
        except Exception as e:
            logger.error(f"❌ Ошибка выполнения SQL: {e}")
            raise


class DocStructureVannaFixed(DocStructureVectorDBFixed, OpenAI_Chat):
    """
    Исправленный Vanna AI клиент с правильной логикой получения контекста
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Инициализация исправленного Vanna AI клиента
        """
        if config is None:
            config = {}
            
        # Настройки по умолчанию для ProxyAPI
        default_config = {
            "database_url": "postgresql://postgres:1234@localhost:5432/test_docstructure",
            "vector_table": "vanna_vectors",
            "api_key": os.getenv("PROXYAPI_KEY") or os.getenv("PROXYAPI_API_KEY") or os.getenv("OPENAI_API_KEY"),
            "model": "gpt-4o",
            "base_url": "https://api.proxyapi.ru/openai/v1",
            "temperature": 0.2
        }
        
        # Объединяем с переданной конфигурацией
        config = {**default_config, **config}
        
        # Инициализируем родительские классы
        try:
            DocStructureVectorDBFixed.__init__(self, config)
            logger.info("✅ DocStructureVectorDBFixed инициализирован")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации DocStructureVectorDBFixed: {e}")
            raise
        
        # Инициализируем OpenAI_Chat без дополнительных параметров
        try:
            OpenAI_Chat.__init__(self)
            logger.info("✅ OpenAI_Chat инициализирован")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации OpenAI_Chat: {e}")
            raise
        
        # Настраиваем ProxyAPI клиент
        try:
            self._setup_proxyapi_client(config)
            logger.info("✅ ProxyAPI клиент настроен")
        except Exception as e:
            logger.error(f"❌ Ошибка настройки ProxyAPI клиента: {e}")
            raise
        
        logger.info("✅ DocStructureVannaFixed инициализирован")
    
    def _setup_proxyapi_client(self, config: Dict[str, Any]):
        """Настройка ProxyAPI клиента"""
        try:
            self.api_key = config.get("api_key")
            self.model = config.get("model", "gpt-4o")
            self.base_url = config.get("base_url", "https://api.proxyapi.ru/openai/v1")
            self.temperature = config.get("temperature", 0.2)
            
            logger.info("✅ ProxyAPI клиент настроен")
            
        except Exception as e:
            logger.error(f"❌ Ошибка настройки ProxyAPI клиента: {e}")
            raise
    
    def generate_sql(self, question: str) -> str:
        """
        Генерация SQL с исправленной логикой получения контекста
        """
        try:
            # Получаем связанные данные с исправленной логикой
            ddl_list = self.get_related_ddl(question)
            docs_list = self.get_related_documentation(question)
            qa_list = self.get_similar_question_sql(question)
            
            # Формируем контекст
            context_parts = []
            
            if ddl_list:
                context_parts.append("\n".join(ddl_list))
            
            if docs_list:
                context_parts.append("\n".join(docs_list))
            
            if qa_list:
                context_parts.append("\n".join(qa_list))
            
            context = "\n\n".join(context_parts)
            
            # Создаем промпт
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
            
            # Используем родительский метод для генерации SQL
            return super().generate_sql(prompt, question)
            
        except Exception as e:
            logger.error(f"❌ Ошибка генерации SQL: {e}")
            raise


def create_fixed_vanna_client(use_proxyapi: bool = True) -> DocStructureVannaFixed:
    """
    Создание исправленного Vanna AI клиента
    
    Args:
        use_proxyapi: Использовать ProxyAPI вместо OpenAI
        
    Returns:
        DocStructureVannaFixed: Исправленный клиент
    """
    config = {
        "database_url": "postgresql://postgres:1234@localhost:5432/test_docstructure",
        "vector_table": "vanna_vectors",
        "api_key": "sk-xF20r7G4tq9ezBMNKIjCPvva2io4S8FV",
        "model": "gpt-4o",
        "base_url": "https://api.proxyapi.ru/openai/v1",
        "temperature": 0.2
    }
    
    return DocStructureVannaFixed(config)
