#!/usr/bin/env python3
"""
Vanna AI клиент с pgvector для DocStructureSchema
Использует нативный код Vanna AI
"""

import os
import logging
from typing import Optional, Dict, Any
from vanna.postgresql.postgresql_vector import PostgreSQL_VectorStore
from vanna.openai.openai_chat import OpenAI_Chat

logger = logging.getLogger(__name__)

class DocStructureVannaPGVector(PostgreSQL_VectorStore, OpenAI_Chat):
    """
    Vanna AI клиент с pgvector для DocStructureSchema
    Наследует от нативных классов Vanna AI
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Инициализация Vanna AI клиента с pgvector
        
        Args:
            config: Конфигурация для PostgreSQL и OpenAI
        """
        if config is None:
            config = {}
            
        # Настройки по умолчанию
        default_config = {
            "database_url": "postgresql://postgres:1234@localhost:5432/test_docstructure",
            "vector_table": "vanna_vectors",
            "vector_dimension": 1536,
            "distance_metric": "cosine",
            "openai_api_key": os.getenv("OPENAI_API_KEY"),
            "openai_model": "gpt-3.5-turbo"
        }
        
        # Объединяем с переданной конфигурацией
        config = {**default_config, **config}
        
        # Инициализируем родительские классы
        try:
            PostgreSQL_VectorStore.__init__(self, config=config)
            OpenAI_Chat.__init__(self, config=config)
            logger.info("✅ Vanna AI с pgvector инициализирован успешно")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации: {e}")
            raise
    
    def train_on_database_schema(self, db_connection=None):
        """
        Обучение на схеме базы данных
        
        Args:
            db_connection: Подключение к базе данных
        """
        try:
            logger.info("🎓 Начало обучения на схеме базы данных...")
            
            # Получаем DDL структуру
            ddl_statements = self._get_ddl_statements()
            
            # Обучаем на DDL
            for ddl in ddl_statements:
                self.train(ddl=ddl)
                logger.info(f"✅ Обучение на DDL: {ddl[:100]}...")
            
            logger.info("✅ Обучение на схеме базы данных завершено")
            
        except Exception as e:
            logger.error(f"❌ Ошибка обучения на схеме: {e}")
            raise
    
    def train_on_documentation(self, documentation: str):
        """
        Обучение на документации
        
        Args:
            documentation: Текст документации
        """
        try:
            logger.info("📚 Обучение на документации...")
            self.train(documentation=documentation)
            logger.info("✅ Обучение на документации завершено")
        except Exception as e:
            logger.error(f"❌ Ошибка обучения на документации: {e}")
            raise
    
    def train_on_sql_examples(self, examples: list):
        """
        Обучение на SQL примерах
        
        Args:
            examples: Список примеров с вопросами и SQL
        """
        try:
            logger.info("💡 Обучение на SQL примерах...")
            for example in examples:
                question = example.get("question")
                sql = example.get("sql")
                if question and sql:
                    self.train(question=question, sql=sql)
            logger.info("✅ Обучение на SQL примерах завершено")
        except Exception as e:
            logger.error(f"❌ Ошибка обучения на SQL примерах: {e}")
            raise
    
    def _get_ddl_statements(self) -> list:
        """
        Получение DDL операторов для обучения
        
        Returns:
            list: Список DDL операторов
        """
        # Основные таблицы DocStructureSchema
        ddl_statements = [
            """
            CREATE TABLE equsers (
                id UUID PRIMARY KEY,
                login VARCHAR(255) NOT NULL,
                email VARCHAR(255),
                surname VARCHAR(255),
                firstname VARCHAR(255),
                patronymic VARCHAR(255),
                department UUID REFERENCES eq_departments(id),
                accessgranted BOOLEAN DEFAULT true,
                build_in_account BOOLEAN DEFAULT false,
                pass VARCHAR(255),
                refresh_token TEXT,
                validity DATE,
                creationdatetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deleted BOOLEAN DEFAULT false
            );
            """,
            
            """
            CREATE TABLE eq_departments (
                id UUID PRIMARY KEY,
                departmentname VARCHAR(255) NOT NULL,
                parentid UUID REFERENCES eq_departments(id),
                description TEXT,
                creationdatetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deleted BOOLEAN DEFAULT false
            );
            """,
            
            """
            CREATE TABLE tbl_business_unit (
                id UUID PRIMARY KEY,
                business_unit_name VARCHAR(255) NOT NULL,
                inn VARCHAR(20),
                kpp VARCHAR(20),
                ogrn VARCHAR(20),
                legal_address TEXT,
                actual_address TEXT,
                phone VARCHAR(50),
                email VARCHAR(255),
                phone_2 VARCHAR(50),
                website VARCHAR(255),
                creationdatetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deleted BOOLEAN DEFAULT false
            );
            """,
            
            """
            CREATE TABLE tbl_principal_assignment (
                id UUID PRIMARY KEY,
                assignment_number VARCHAR(100) NOT NULL,
                assignment_date DATE,
                amount DECIMAL(15,2),
                currency_id UUID,
                status_id UUID,
                business_unit_id UUID REFERENCES tbl_business_unit(id),
                manager_id UUID REFERENCES equsers(id),
                description TEXT,
                creationdatetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deleted BOOLEAN DEFAULT false
            );
            """,
            
            """
            CREATE TABLE tbl_incoming_payments (
                id UUID PRIMARY KEY,
                payment_number VARCHAR(100) NOT NULL,
                payment_date DATE,
                amount DECIMAL(15,2),
                currency_id UUID,
                business_unit_id UUID REFERENCES tbl_business_unit(id),
                assignment_id UUID REFERENCES tbl_principal_assignment(id),
                description TEXT,
                creationdatetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deleted BOOLEAN DEFAULT false
            );
            """
        ]
        
        return ddl_statements

def create_pgvector_vanna_client(database_url: str = None, openai_api_key: str = None) -> DocStructureVannaPGVector:
    """
    Создание Vanna AI клиента с pgvector
    
    Args:
        database_url: URL подключения к PostgreSQL
        openai_api_key: API ключ OpenAI
        
    Returns:
        DocStructureVannaPGVector: Настроенный клиент
    """
    if database_url is None:
        database_url = "postgresql://postgres:1234@localhost:5432/test_docstructure"
    
    if openai_api_key is None:
        openai_api_key = os.getenv("OPENAI_API_KEY")
    
    config = {
        "database_url": database_url,
        "openai_api_key": openai_api_key,
        "vector_table": "vanna_vectors",
        "vector_dimension": 1536,
        "distance_metric": "cosine"
    }
    
    return DocStructureVannaPGVector(config=config)
