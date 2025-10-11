#!/usr/bin/env python3
"""
Обновленный Vanna AI клиент с поддержкой различных векторных БД
"""

from typing import Optional, Dict, Any
import logging
from pathlib import Path

# Импорты для разных векторных БД
try:
    from vanna.openai.openai_chat import OpenAI_Chat
    from vanna.chromadb.chromadb_vector import ChromaDB_VectorStore
    from vanna.postgresql.postgresql_vector import PostgreSQL_VectorStore
    from vanna.faiss.faiss_vector import FAISS_VectorStore
except ImportError as e:
    logging.warning(f"Некоторые векторные БД недоступны: {e}")

from src.vanna.vector_db_configs import get_recommended_config

logger = logging.getLogger(__name__)

class DocStructureVannaUpdated:
    """
    Обновленный Vanna AI клиент с поддержкой различных векторных БД
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Инициализация Vanna AI клиента
        
        Args:
            config: Конфигурация с настройками векторной БД
        """
        if config is None:
            config = {}
            
        self.config = config
        self.vector_db_type = config.get("vector_db", "pgvector")
        self.database_url = config.get("database_url", "postgresql://postgres:1234@localhost:5432/test_docstructure")
        
        # Инициализируем векторную БД
        self._init_vector_db()
        
        # Инициализируем LLM
        self._init_llm()
        
        logger.info(f"Vanna AI клиент инициализирован с {self.vector_db_type}")
    
    def _init_vector_db(self):
        """Инициализация векторной БД"""
        try:
            if self.vector_db_type == "pgvector":
                self._init_pgvector()
            elif self.vector_db_type == "faiss":
                self._init_faiss()
            elif self.vector_db_type == "chromadb":
                self._init_chromadb()
            else:
                raise ValueError(f"Неподдерживаемый тип векторной БД: {self.vector_db_type}")
        except Exception as e:
            logger.error(f"Ошибка инициализации векторной БД: {e}")
            # Fallback на простую логику
            self.vector_db = None
    
    def _init_pgvector(self):
        """Инициализация pgvector"""
        try:
            from vanna.postgresql.postgresql_vector import PostgreSQL_VectorStore
            self.vector_db = PostgreSQL_VectorStore(config=self.config)
            logger.info("✅ pgvector инициализирован")
        except ImportError:
            logger.error("❌ PostgreSQL_VectorStore недоступен. Установите vanna[postgresql]")
            raise
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации pgvector: {e}")
            raise
    
    def _init_faiss(self):
        """Инициализация FAISS"""
        try:
            from vanna.faiss.faiss_vector import FAISS_VectorStore
            self.vector_db = FAISS_VectorStore(config=self.config)
            logger.info("✅ FAISS инициализирован")
        except ImportError:
            logger.error("❌ FAISS_VectorStore недоступен. Установите vanna[faiss]")
            raise
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации FAISS: {e}")
            raise
    
    def _init_chromadb(self):
        """Инициализация ChromaDB"""
        try:
            from vanna.chromadb.chromadb_vector import ChromaDB_VectorStore
            self.vector_db = ChromaDB_VectorStore(config=self.config)
            logger.info("✅ ChromaDB инициализирован")
        except ImportError:
            logger.error("❌ ChromaDB_VectorStore недоступен. Установите vanna[chromadb]")
            raise
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации ChromaDB: {e}")
            raise
    
    def _init_llm(self):
        """Инициализация LLM"""
        try:
            from vanna.openai.openai_chat import OpenAI_Chat
            self.llm = OpenAI_Chat(config=self.config)
            logger.info("✅ LLM инициализирован")
        except ImportError:
            logger.error("❌ OpenAI_Chat недоступен. Установите vanna[openai]")
            raise
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации LLM: {e}")
            raise
    
    def train(self, **kwargs):
        """
        Обучение на данных
        
        Args:
            **kwargs: Параметры обучения (ddl, documentation, question, sql)
        """
        try:
            if self.vector_db is None:
                logger.warning("⚠️ Векторная БД недоступна, используем fallback логику")
                return
                
            # Обучаем векторную БД
            if hasattr(self.vector_db, 'train'):
                self.vector_db.train(**kwargs)
                logger.info("✅ Обучение векторной БД завершено")
            else:
                logger.warning("⚠️ Векторная БД не поддерживает обучение")
                
        except Exception as e:
            logger.error(f"❌ Ошибка обучения: {e}")
            raise
    
    def generate_sql(self, question: str, user_context: Dict[str, Any] = None) -> str:
        """
        Генерация SQL запроса
        
        Args:
            question: Вопрос на естественном языке
            user_context: Контекст пользователя
            
        Returns:
            str: SQL запрос
        """
        try:
            logger.info(f"Генерация SQL для вопроса: {question}")
            
            # Если векторная БД недоступна, используем простую логику
            if self.vector_db is None:
                return self._generate_sql_fallback(question)
            
            # Получаем релевантные данные из векторной БД
            relevant_data = self._get_relevant_data(question)
            
            # Генерируем SQL с помощью LLM
            sql = self._generate_sql_with_llm(question, relevant_data, user_context)
            
            logger.info(f"Сгенерирован SQL: {sql}")
            return sql
            
        except Exception as e:
            logger.error(f"Ошибка генерации SQL: {e}")
            # Fallback на простую логику
            return self._generate_sql_fallback(question)
    
    def _get_relevant_data(self, question: str) -> str:
        """Получение релевантных данных из векторной БД"""
        try:
            if hasattr(self.vector_db, 'get_similar_documentation'):
                return self.vector_db.get_similar_documentation(question)
            else:
                return ""
        except Exception as e:
            logger.error(f"Ошибка получения релевантных данных: {e}")
            return ""
    
    def _generate_sql_with_llm(self, question: str, relevant_data: str, user_context: Dict[str, Any] = None) -> str:
        """Генерация SQL с помощью LLM"""
        try:
            if hasattr(self.llm, 'generate_sql'):
                return self.llm.generate_sql(question, relevant_data, user_context)
            else:
                return self._generate_sql_fallback(question)
        except Exception as e:
            logger.error(f"Ошибка генерации SQL с LLM: {e}")
            return self._generate_sql_fallback(question)
    
    def _generate_sql_fallback(self, question: str) -> str:
        """Fallback логика для генерации SQL"""
        question_lower = question.lower()
        
        if "пользовател" in question_lower or "пользователи" in question_lower:
            return "SELECT COUNT(*) as user_count FROM equsers WHERE deleted = false"
        elif "клиент" in question_lower:
            return "SELECT COUNT(*) as client_count FROM tbl_business_unit WHERE deleted = false"
        elif "поручен" in question_lower:
            return "SELECT COUNT(*) as assignment_count FROM tbl_principal_assignment WHERE deleted = false"
        elif "платеж" in question_lower:
            return "SELECT COUNT(*) as payment_count FROM tbl_incoming_payments WHERE deleted = false"
        elif "отдел" in question_lower:
            return "SELECT COUNT(*) as department_count FROM eq_departments WHERE deleted = false"
        else:
            return "SELECT 'Неизвестный запрос' as message"

def create_vanna_client(vector_db_type: str = "pgvector", database_url: str = None) -> DocStructureVannaUpdated:
    """
    Создание Vanna AI клиента с указанным типом векторной БД
    
    Args:
        vector_db_type: Тип векторной БД ("pgvector", "faiss", "chromadb")
        database_url: URL подключения к БД
        
    Returns:
        DocStructureVannaUpdated: Настроенный клиент
    """
    if database_url is None:
        database_url = "postgresql://postgres:1234@localhost:5432/test_docstructure"
    
    # Получаем конфигурацию
    config = get_recommended_config(database_url, vector_db_type)
    
    # Создаем клиент
    return DocStructureVannaUpdated(config=config)
