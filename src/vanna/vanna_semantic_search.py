#!/usr/bin/env python3
"""
Vanna AI с настоящим семантическим поиском через pgvector
"""

import os
import logging
import asyncio
import asyncpg
from typing import List, Dict, Any, Optional
from openai import OpenAI

logger = logging.getLogger(__name__)

class SemanticRAG:
    """RAG с семантическим поиском через pgvector"""
    
    def __init__(self, dsn: str, api_key: str, base_url: str = None):
        self.dsn = dsn
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url or "https://api.proxyapi.ru/openai/v1"
        )
    
    async def get_semantic_context(self, question: str, limit: int = 3) -> Dict[str, List[str]]:
        """
        Получение семантически релевантного контекста
        
        Args:
            question: Вопрос пользователя
            limit: Количество релевантных записей по типу
            
        Returns:
            Dict с релевантными данными по типам
        """
        try:
            # Генерируем эмбеддинг для вопроса
            question_embedding = await self._generate_embedding(question)
            
            # Подключаемся к БД
            conn = await asyncpg.connect(self.dsn)
            
            # Семантический поиск по документации
            docs = await self._semantic_search(conn, question_embedding, 'documentation', limit)
            
            # Семантический поиск по Q/A парам
            qa_pairs = await self._semantic_search(conn, question_embedding, 'question_sql', limit)
            
            # Семантический поиск по DDL
            ddl = await self._semantic_search(conn, question_embedding, 'ddl', limit)
            
            await conn.close()
            
            return {
                'documentation': docs,
                'question_sql': qa_pairs,
                'ddl': ddl
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка семантического поиска: {e}")
            return {'documentation': [], 'question_sql': [], 'ddl': []}
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """Генерация эмбеддинга для текста"""
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
            return model.encode(text, convert_to_tensor=True).tolist()
        except Exception as e:
            logger.error(f"❌ Ошибка генерации эмбеддинга: {e}")
            return []
    
    async def _semantic_search(self, conn: asyncpg.Connection, query_embedding: List[float], 
                              content_type: str, limit: int) -> List[str]:
        """Семантический поиск по типу контента"""
        try:
            # Конвертируем эмбеддинг в строку для pgvector
            embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
            
            # Семантический поиск с использованием cosine distance
            query = """
                SELECT content, embedding <-> $1::vector as distance
                FROM vanna_vectors 
                WHERE content_type = $2 AND embedding IS NOT NULL
                ORDER BY embedding <-> $1::vector
                LIMIT $3
            """
            
            results = await conn.fetch(query, embedding_str, content_type, limit)
            
            # Извлекаем только контент, отсортированный по релевантности
            content = [row['content'] for row in results]
            
            logger.info(f"✅ Найдено {len(content)} релевантных {content_type} записей")
            return content
            
        except Exception as e:
            logger.error(f"❌ Ошибка семантического поиска {content_type}: {e}")
            return []

async def test_semantic_search():
    """Тестирование семантического поиска"""
    dsn = "postgresql://postgres:1234@localhost:5432/test_docstructure"
    api_key = os.getenv("PROXYAPI_KEY")
    
    if not api_key:
        logger.error("❌ PROXYAPI_KEY не найден")
        return
    
    rag = SemanticRAG(dsn, api_key)
    
    # Тестовые вопросы
    test_questions = [
        "Покажи поручения за последний месяц",
        "Список пользователей по отделам", 
        "Платежи по клиентам",
        "Структура таблицы пользователей"
    ]
    
    for question in test_questions:
        print(f"\n🔍 Вопрос: {question}")
        context = await rag.get_semantic_context(question, limit=2)
        
        for content_type, items in context.items():
            if items:
                print(f"  📋 {content_type}: {len(items)} записей")
                for i, item in enumerate(items[:1]):  # Показываем только первую
                    preview = item[:100] + "..." if len(item) > 100 else item
                    print(f"    {i+1}. {preview}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_semantic_search())

