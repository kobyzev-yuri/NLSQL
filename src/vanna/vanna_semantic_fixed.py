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
from openai import OpenAI

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
            context = await self._semantic_search(question, 'question_sql', limit=3)
            logger.info(f"✅ Получено {len(context)} релевантных Q/A пар")
            return context
        except Exception as e:
            logger.error(f"❌ Ошибка получения Q/A пар: {e}")
            return []
    
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
        """Генерация эмбеддинга для текста"""
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            return response.data[0].embedding
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
