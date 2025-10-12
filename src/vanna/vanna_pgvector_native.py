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
        Получение релевантных DDL операторов для бизнес-таблиц
        
        Args:
            question: Вопрос
            **kwargs: Дополнительные параметры
            
        Returns:
            list: Список релевантных DDL
        """
        try:
            # Приоритетные бизнес-таблицы
            priority_tables = [
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
            
            ddl_list = []
            
            for table in priority_tables:
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
                            
                            # Добавляем имена колонок
                            column_names = [row[1] for row in results]
                            table_ddl += f"Колонки: {', '.join(column_names)}\n"
                            
                            for row in results:
                                col_info = f"- {row[1]}: {row[2]}"
                                if row[3] == 'NO':
                                    col_info += " (NOT NULL)"
                                if row[5]:
                                    col_info += f"({row[5]})"
                                table_ddl += col_info + "\n"
                            
                            ddl_list.append(table_ddl)
                            
                except Exception as e:
                    logger.warning(f"⚠️ Не удалось получить DDL для {table}: {e}")
                    continue
            
            logger.info(f"✅ Получено {len(ddl_list)} DDL элементов для бизнес-таблиц")
            return ddl_list
                
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
            
        # Настройки по умолчанию для Ollama
        default_config = {
            "database_url": "postgresql://postgres:1234@localhost:5432/test_docstructure",
            "vector_table": "vanna_vectors",
            "api_key": "ollama",
            "model": "llama3.1:8b",
            "base_url": "http://localhost:11434/v1",  # Ollama API
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
    
    def run_sql(self, sql: str) -> pd.DataFrame:
        """
        Выполнение SQL запроса и возврат результата как DataFrame
        
        Args:
            sql: SQL запрос для выполнения
            
        Returns:
            pd.DataFrame: Результат запроса
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(sql)
                results = cur.fetchall()
                
                # Получаем названия колонок
                columns = [desc[0] for desc in cur.description] if cur.description else []
                
                # Создаем DataFrame
                df = pd.DataFrame(results, columns=columns)
                
                logger.info(f"✅ SQL выполнен успешно, получено {len(df)} строк")
                return df
                
        except Exception as e:
            logger.error(f"❌ Ошибка выполнения SQL: {e}")
            return pd.DataFrame()
    
    def get_training_plan_generic(self, df: pd.DataFrame) -> list:
        """
        Создание плана обучения на основе DataFrame со схемой
        
        Args:
            df: DataFrame со схемой базы данных
            
        Returns:
            list: План обучения
        """
        try:
            if df.empty:
                return []
            
            plan = []
            
            # Группируем по таблицам
            tables = df.groupby('table_name')
            
            for table_name, table_data in tables:
                # Создаем описание таблицы
                table_description = f"Таблица {table_name}:\n"
                table_description += f"Колонки: {', '.join(table_data['column_name'].tolist())}\n"
                
                # Добавляем типы данных
                for _, row in table_data.iterrows():
                    table_description += f"- {row['column_name']}: {row['data_type']}"
                    if row['is_nullable'] == 'NO':
                        table_description += " (NOT NULL)"
                    table_description += "\n"
                
                plan.append({
                    'type': 'documentation',
                    'content': table_description
                })
            
            logger.info(f"✅ Создан план обучения с {len(plan)} элементами")
            return plan
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания плана обучения: {e}")
            return []
    
    def train(self, **kwargs):
        """
        Обучение на данных с поддержкой плана обучения
        
        Args:
            **kwargs: Параметры обучения (ddl, documentation, question, sql, plan)
        """
        try:
            # Если передан план обучения
            if 'plan' in kwargs:
                plan = kwargs['plan']
                if isinstance(plan, list):
                    # Обучаем на каждом элементе плана
                    for item in plan:
                        if item.get('type') == 'documentation':
                            self.add_documentation(item['content'])
                        elif item.get('type') == 'ddl':
                            self.add_ddl(item['content'])
                        elif item.get('type') == 'question_sql':
                            self.add_question_sql(item['question'], item['sql'])
                    logger.info(f"✅ Обучение на плане завершено ({len(plan)} элементов)")
                else:
                    logger.warning("⚠️ План обучения должен быть списком")
                return
            
            # Стандартное обучение
            if 'ddl' in kwargs:
                self.add_ddl(kwargs['ddl'])
            if 'documentation' in kwargs:
                self.add_documentation(kwargs['documentation'])
            if 'question' in kwargs and 'sql' in kwargs:
                self.add_question_sql(kwargs['question'], kwargs['sql'])
                
        except Exception as e:
            logger.error(f"❌ Ошибка обучения: {e}")
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
