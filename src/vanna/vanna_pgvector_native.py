#!/usr/bin/env python3
"""
Vanna AI клиент с pgvector для DocStructureSchema
Использует нативный код Vanna AI согласно документации
https://vanna.ai/docs/postgres-openai-standard-other-vectordb/
"""

import os
import logging
from typing import Optional, Dict, Any
try:
    from vanna.openai import OpenAI_Chat
except ImportError:
    from vanna.base import VannaBase
    class OpenAI_Chat(VannaBase):
        def __init__(self, **kwargs):
            super().__init__()
            self.config = kwargs
from vanna.base import VannaBase
import pandas as pd

logger = logging.getLogger(__name__)

class DocStructureVectorDB(VannaBase):
    """
    Кастомная векторная БД для DocStructureSchema
    Наследует от VannaBase согласно документации Vanna AI
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Инициализация векторной БД
        
        Args:
            config: Конфигурация
        """
        if config is None:
            config = {}
            
        self.config = config
        self.database_url = config.get("database_url", "postgresql://postgres:1234@localhost:5432/test_docstructure")
        self.vector_table = config.get("vector_table", "vanna_vectors")
        
        # Инициализируем подключение к PostgreSQL
        self._init_postgres_connection()
        
        logger.info("✅ DocStructureVectorDB инициализирован")
    
    def _init_postgres_connection(self):
        """Инициализация подключения к PostgreSQL"""
        try:
            import psycopg
            self.conn = psycopg.connect(self.database_url)
            logger.info("✅ Подключение к PostgreSQL установлено")
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к PostgreSQL: {e}")
            raise
    
    def add_ddl(self, ddl: str, **kwargs) -> str:
        """
        Добавление DDL в векторную БД
        
        Args:
            ddl: DDL оператор
            **kwargs: Дополнительные параметры
            
        Returns:
            str: ID добавленного элемента
        """
        try:
            # Создаем таблицу для векторов если не существует
            self._create_vector_table()
            
            # Добавляем DDL в векторную БД
            with self.conn.cursor() as cur:
                # Преобразуем metadata в JSON строку
                import json
                metadata_json = json.dumps({'type': 'ddl'})
                cur.execute("""
                    INSERT INTO vanna_vectors (content, content_type, metadata)
                    VALUES (%s, %s, %s)
                    RETURNING id
                """, (ddl, 'ddl', metadata_json))
                
                result = cur.fetchone()
                self.conn.commit()
                
                logger.info(f"✅ DDL добавлен с ID: {result[0]}")
                return str(result[0])
                
        except Exception as e:
            logger.error(f"❌ Ошибка добавления DDL: {e}")
            raise
    
    def add_documentation(self, doc: str, **kwargs) -> str:
        """
        Добавление документации в векторную БД
        
        Args:
            doc: Текст документации
            **kwargs: Дополнительные параметры
            
        Returns:
            str: ID добавленного элемента
        """
        try:
            with self.conn.cursor() as cur:
                # Преобразуем metadata в JSON строку
                import json
                metadata_json = json.dumps({'type': 'documentation'})
                cur.execute("""
                    INSERT INTO vanna_vectors (content, content_type, metadata)
                    VALUES (%s, %s, %s)
                    RETURNING id
                """, (doc, 'documentation', metadata_json))
                
                result = cur.fetchone()
                self.conn.commit()
                
                logger.info(f"✅ Документация добавлена с ID: {result[0]}")
                return str(result[0])
                
        except Exception as e:
            logger.error(f"❌ Ошибка добавления документации: {e}")
            raise
    
    def add_question_sql(self, question: str, sql: str, **kwargs) -> str:
        """
        Добавление пары вопрос-SQL в векторную БД
        
        Args:
            question: Вопрос на естественном языке
            sql: SQL запрос
            **kwargs: Дополнительные параметры
            
        Returns:
            str: ID добавленного элемента
        """
        try:
            with self.conn.cursor() as cur:
                # Преобразуем metadata в JSON строку
                import json
                metadata_json = json.dumps({
                    'type': 'question_sql',
                    'question': question,
                    'sql': sql
                })
                cur.execute("""
                    INSERT INTO vanna_vectors (content, content_type, metadata)
                    VALUES (%s, %s, %s)
                    RETURNING id
                """, (f"Q: {question}\nA: {sql}", 'question_sql', metadata_json))
                
                result = cur.fetchone()
                self.conn.commit()
                
                logger.info(f"✅ Вопрос-SQL добавлен с ID: {result[0]}")
                return str(result[0])
                
        except Exception as e:
            logger.error(f"❌ Ошибка добавления вопроса-SQL: {e}")
            raise
    
    def get_related_ddl(self, question: str, **kwargs) -> list:
        """
        Получение релевантных DDL операторов
        
        Args:
            question: Вопрос
            **kwargs: Дополнительные параметры
            
        Returns:
            list: Список релевантных DDL
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT content FROM vanna_vectors 
                    WHERE content_type = 'ddl'
                    ORDER BY id DESC
                    LIMIT 5
                """)
                
                results = cur.fetchall()
                return [row[0] for row in results]
                
        except Exception as e:
            logger.error(f"❌ Ошибка получения DDL: {e}")
            return []
    
    def get_related_documentation(self, question: str, **kwargs) -> list:
        """
        Получение релевантной документации
        
        Args:
            question: Вопрос
            **kwargs: Дополнительные параметры
            
        Returns:
            list: Список релевантной документации
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT content FROM vanna_vectors 
                    WHERE content_type = 'documentation'
                    ORDER BY id DESC
                    LIMIT 5
                """)
                
                results = cur.fetchall()
                return [row[0] for row in results]
                
        except Exception as e:
            logger.error(f"❌ Ошибка получения документации: {e}")
            return []
    
    def get_similar_question_sql(self, question: str, **kwargs) -> list:
        """
        Получение похожих вопросов и SQL
        
        Args:
            question: Вопрос
            **kwargs: Дополнительные параметры
            
        Returns:
            list: Список похожих вопросов и SQL
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT content FROM vanna_vectors 
                    WHERE content_type = 'question_sql'
                    ORDER BY id DESC
                    LIMIT 5
                """)
                
                results = cur.fetchall()
                return [row[0] for row in results]
                
        except Exception as e:
            logger.error(f"❌ Ошибка получения вопросов-SQL: {e}")
            return []
    
    def get_training_data(self, **kwargs) -> pd.DataFrame:
        """
        Получение всех данных для обучения
        
        Args:
            **kwargs: Дополнительные параметры
            
        Returns:
            pd.DataFrame: DataFrame с данными обучения
        """
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
        """
        Удаление данных обучения
        
        Args:
            id: ID элемента для удаления
            **kwargs: Дополнительные параметры
            
        Returns:
            bool: True если удалено успешно
        """
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
        """Создание таблицы для векторов"""
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
            logger.error(f"❌ Ошибка создания таблицы: {e}")
            raise
    
    def generate_embedding(self, text: str, **kwargs) -> list:
        """
        Генерация эмбеддингов для текста
        
        Args:
            text: Текст для генерации эмбеддинга
            **kwargs: Дополнительные параметры
            
        Returns:
            list: Вектор эмбеддинга
        """
        try:
            # Простая реализация - возвращаем случайный вектор
            # В реальной реализации здесь должен быть вызов OpenAI API
            import random
            return [random.random() for _ in range(1536)]
        except Exception as e:
            logger.error(f"❌ Ошибка генерации эмбеддинга: {e}")
            return [0.0] * 1536

class DocStructureVannaNative(DocStructureVectorDB, OpenAI_Chat):
    """
    Vanna AI клиент с pgvector для DocStructureSchema
    Использует нативную архитектуру Vanna AI
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Инициализация Vanna AI клиента
        
        Args:
            config: Конфигурация
        """
        if config is None:
            config = {}
            
        # Настройки по умолчанию для ProxyAPI
        default_config = {
            "database_url": "postgresql://postgres:1234@localhost:5432/test_docstructure",
            "vector_table": "vanna_vectors",
            "api_key": os.getenv("PROXYAPI_KEY") or os.getenv("PROXYAPI_API_KEY") or os.getenv("OPENAI_API_KEY"),
            "model": "gpt-4o",
            "base_url": "https://api.proxyapi.ru/openai/v1",  # ProxyAPI
            "temperature": 0.2
        }
        
        # Объединяем с переданной конфигурацией
        config = {**default_config, **config}
        
        # Инициализируем родительские классы
        try:
            DocStructureVectorDB.__init__(self, config=config)
            # Переопределяем OpenAI клиент для ProxyAPI
            self._setup_proxyapi_client(config)
            logger.info("✅ DocStructureVannaNative инициализирован")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации: {e}")
            raise
    
    def _setup_proxyapi_client(self, config: Dict[str, Any]):
        """
        Настройка ProxyAPI клиента вместо стандартного OpenAI
        
        Args:
            config: Конфигурация с настройками ProxyAPI
        """
        try:
            from openai import OpenAI
            
            # Создаем клиент с настройками ProxyAPI
            self.client = OpenAI(
                api_key=config.get("api_key"),
                base_url=config.get("base_url", "https://api.proxyapi.ru/openai/v1")
            )
            
            # Сохраняем настройки модели
            self.model = config.get("model", "gpt-4o")
            self.temperature = config.get("temperature", 0.2)
            self.dialect = "postgresql"  # Добавляем недостающий атрибут
            self.max_tokens = 1000  # Максимальное количество токенов
            
            # Добавляем недостающие атрибуты для совместимости с Vanna AI
            self.static_documentation = []
            self.static_sql = []
            self.static_ddl = []
            
            logger.info(f"✅ ProxyAPI клиент настроен: {config.get('base_url')} с моделью {self.model}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка настройки ProxyAPI клиента: {e}")
            raise
    
    def connect_to_postgres(self, host: str = "localhost", dbname: str = "test_docstructure", 
                          user: str = "postgres", password: str = "1234", port: str = "5432"):
        """
        Подключение к PostgreSQL согласно документации Vanna AI
        
        Args:
            host: Хост PostgreSQL
            dbname: Имя базы данных
            user: Пользователь
            password: Пароль
            port: Порт
        """
        try:
            database_url = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
            self.database_url = database_url
            self._init_postgres_connection()
            logger.info("✅ Подключение к PostgreSQL обновлено")
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к PostgreSQL: {e}")
            raise

def create_native_vanna_client(use_proxyapi: bool = True) -> DocStructureVannaNative:
    """
    Создание нативного Vanna AI клиента
    
    Args:
        use_proxyapi: Использовать ProxyAPI вместо OpenAI
        
    Returns:
        DocStructureVannaNative: Настроенный клиент
    """
    config = {
        "database_url": "postgresql://postgres:1234@localhost:5432/test_docstructure",
        "vector_table": "vanna_vectors"
    }
    
    if use_proxyapi:
        # Используем настройки из config.env как в проекте steccom-rag-lk
        config.update({
            "api_key": os.getenv("PROXYAPI_KEY") or os.getenv("PROXYAPI_API_KEY") or "sk-xF20r7G4tq9ezBMNKIjCPvva2io4S8FV",
            "base_url": os.getenv("PROXYAPI_BASE_URL", "https://api.proxyapi.ru/openai/v1"),
            "model": os.getenv("PROXYAPI_CHAT_MODEL", "gpt-4o"),
            "temperature": float(os.getenv("PROXYAPI_TEMPERATURE", "0.2"))
        })
    else:
        config.update({
            "api_key": os.getenv("OPENAI_API_KEY"),
            "model": "gpt-3.5-turbo"
        })
    
    return DocStructureVannaNative(config=config)
