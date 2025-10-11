"""
Vanna AI клиент для генерации SQL запросов
"""

from typing import Optional, Dict, Any
from vanna.openai.openai_chat import OpenAI_Chat
from vanna.chromadb.chromadb_vector import ChromaDB_VectorStore
import logging

logger = logging.getLogger(__name__)


class DocStructureVanna(ChromaDB_VectorStore, OpenAI_Chat):
    """
    Vanna AI клиент для работы с DocStructureSchema
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Инициализация Vanna AI клиента
        
        Args:
            config: Конфигурация для OpenAI и ChromaDB
        """
        if config is None:
            config = {}
            
        # Инициализация ChromaDB
        ChromaDB_VectorStore.__init__(self, config=config)
        
        # Инициализация OpenAI
        OpenAI_Chat.__init__(self, config=config)
        
        logger.info("Vanna AI клиент инициализирован")
    
    def train_on_database_schema(self, db_connection):
        """
        Обучение модели на схеме базы данных
        
        Args:
            db_connection: Подключение к базе данных
        """
        try:
            # Получение DDL структуры
            ddl_statements = self._get_ddl_statements(db_connection)
            
            # Обучение на DDL
            for ddl in ddl_statements:
                self.train(ddl=ddl)
                logger.info(f"Обучение на DDL: {ddl[:100]}...")
            
            # Добавление документации
            documentation = self._get_database_documentation()
            self.train(documentation=documentation)
            
            logger.info("Обучение на схеме базы данных завершено")
            
        except Exception as e:
            logger.error(f"Ошибка обучения на схеме: {e}")
            raise
    
    def _get_ddl_statements(self, db_connection):
        """
        Получение DDL операторов из базы данных
        
        Args:
            db_connection: Подключение к базе данных
            
        Returns:
            List[str]: Список DDL операторов
        """
        # Здесь будет логика получения DDL из PostgreSQL
        # Пока возвращаем примеры основных таблиц
        return [
            """
            CREATE TABLE equsers (
                id UUID PRIMARY KEY,
                login VARCHAR(255),
                email VARCHAR(255),
                department UUID,
                accessgranted BOOLEAN,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            CREATE TABLE eq_departments (
                id UUID PRIMARY KEY,
                departmentname VARCHAR(255),
                parentid UUID,
                description TEXT
            );
            """,
            """
            CREATE TABLE tbl_business_unit (
                id UUID PRIMARY KEY,
                business_unit_name VARCHAR(255),
                inn VARCHAR(20),
                kpp VARCHAR(20),
                ogrn VARCHAR(20),
                legal_address TEXT,
                phone VARCHAR(50),
                email VARCHAR(255)
            );
            """
        ]
    
    def _get_database_documentation(self):
        """
        Получение документации по базе данных
        
        Returns:
            str: Документация на русском языке
        """
        return """
        DocStructureSchema - система управления документами и пользователями
        
        Основные таблицы:
        - equsers: пользователи системы
        - eq_departments: отделы организации
        - eqgroups: группы пользователей
        - eqroles: роли системы
        - eqdoctypes: типы документов
        - eqdocstructure: структура полей документов
        - tbl_business_unit: профили клиентов
        - tbl_principal_assignment: поручения принципала
        - tbl_incoming_payments: входящие платежи
        
        Бизнес-логика:
        - Каждый пользователь принадлежит отделу
        - Пользователи могут иметь несколько ролей
        - Роли определяют доступ к данным
        - Поручения связаны с клиентами
        - Платежи связаны с поручениями
        """
    
    def generate_sql(self, question: str, user_context: Dict[str, Any] = None) -> str:
        """
        Генерация SQL запроса на основе вопроса
        
        Args:
            question: Вопрос пользователя на русском языке
            user_context: Контекст пользователя (роль, отдел и т.д.)
            
        Returns:
            str: SQL запрос
        """
        try:
            # Генерация SQL через Vanna AI
            sql = self.ask(question)
            
            logger.info(f"Сгенерирован SQL: {sql}")
            return sql
            
        except Exception as e:
            logger.error(f"Ошибка генерации SQL: {e}")
            raise
    
    def add_training_example(self, question: str, sql: str):
        """
        Добавление примера для обучения
        
        Args:
            question: Вопрос пользователя
            sql: SQL запрос
        """
        try:
            self.train(sql=sql)
            logger.info(f"Добавлен пример обучения: {question} -> {sql}")
            
        except Exception as e:
            logger.error(f"Ошибка добавления примера: {e}")
            raise
