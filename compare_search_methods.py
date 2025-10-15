#!/usr/bin/env python3
"""
Сравнение семантического и лексического поиска
"""

import asyncio
import asyncpg
import os
import logging
import re
from typing import List, Dict, Any, Tuple
from openai import OpenAI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SearchMethodComparator:
    """Сравнитель методов поиска"""
    
    def __init__(self):
        self.database_url = "postgresql://postgres:1234@localhost:5432/test_docstructure"
        self.openai_client = OpenAI(
            api_key=os.getenv("PROXYAPI_KEY"),
            base_url="https://api.proxyapi.ru/openai/v1"
        )
    
    async def semantic_search(self, question: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Семантический поиск"""
        try:
            # Генерируем эмбеддинг
            response = self.openai_client.embeddings.create(
                model="text-embedding-ada-002",
                input=question
            )
            question_embedding = response.data[0].embedding
            
            # Подключаемся к БД
            conn = await asyncpg.connect(self.database_url)
            
            # Конвертируем эмбеддинг
            embedding_str = '[' + ','.join(map(str, question_embedding)) + ']'
            
            # Семантический поиск
            query = """
                SELECT content, embedding <-> $1::vector as distance, content_type
                FROM vanna_vectors 
                WHERE embedding IS NOT NULL
                ORDER BY embedding <-> $1::vector
                LIMIT $2
            """
            
            results = await conn.fetch(query, embedding_str, limit)
            await conn.close()
            
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"Ошибка семантического поиска: {e}")
            return []
    
    async def lexical_search(self, question: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Лексический поиск (по ключевым словам)"""
        try:
            # Извлекаем ключевые слова из вопроса
            keywords = self._extract_keywords(question)
            if not keywords:
                return []
            
            # Подключаемся к БД
            conn = await asyncpg.connect(self.database_url)
            
            # Строим поисковый запрос
            search_conditions = []
            params = []
            
            for i, keyword in enumerate(keywords):
                search_conditions.append(f"content ILIKE ${i + 1}")
                params.append(f"%{keyword}%")
            
            if not search_conditions:
                await conn.close()
                return []
            
            # Лексический поиск
            query = f"""
                SELECT content, 
                       CASE 
                           WHEN content ILIKE ANY(${len(params) + 1}) THEN 1.0
                           ELSE 0.5
                       END as relevance,
                       content_type
                FROM vanna_vectors 
                WHERE {' OR '.join(search_conditions)}
                ORDER BY relevance DESC, content
                LIMIT ${len(params) + 2}
            """
            
            # Добавляем массив ключевых слов для проверки
            params.append([f"%{kw}%" for kw in keywords])
            params.append(limit)
            
            results = await conn.fetch(query, *params)
            await conn.close()
            
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"Ошибка лексического поиска: {e}")
            return []
    
    def _extract_keywords(self, question: str) -> List[str]:
        """Извлечение ключевых слов из вопроса"""
        # Убираем стоп-слова и извлекаем значимые слова
        stop_words = {
            'и', 'в', 'на', 'с', 'по', 'для', 'от', 'до', 'за', 'из', 'к', 'о', 'об', 'при', 'про', 'со', 'у',
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'
        }
        
        # Разбиваем на слова и фильтруем
        words = re.findall(r'\b\w+\b', question.lower())
        keywords = [word for word in words if len(word) > 2 and word not in stop_words]
        
        return keywords
    
    async def hybrid_search(self, question: str, limit: int = 5, semantic_weight: float = 0.7) -> List[Dict[str, Any]]:
        """Гибридный поиск (комбинация семантического и лексического)"""
        try:
            # Получаем результаты обоих методов
            semantic_results = await self.semantic_search(question, limit * 2)
            lexical_results = await self.lexical_search(question, limit * 2)
            
            # Создаем словарь для объединения результатов
            combined_results = {}
            
            # Добавляем семантические результаты
            for result in semantic_results:
                content = result['content']
                if content not in combined_results:
                    combined_results[content] = {
                        'content': content,
                        'content_type': result['content_type'],
                        'semantic_score': 1.0 - result['distance'],  # Конвертируем расстояние в score
                        'lexical_score': 0.0,
                        'hybrid_score': 0.0
                    }
                else:
                    combined_results[content]['semantic_score'] = 1.0 - result['distance']
            
            # Добавляем лексические результаты
            for result in lexical_results:
                content = result['content']
                if content not in combined_results:
                    combined_results[content] = {
                        'content': content,
                        'content_type': result['content_type'],
                        'semantic_score': 0.0,
                        'lexical_score': result['relevance'],
                        'hybrid_score': 0.0
                    }
                else:
                    combined_results[content]['lexical_score'] = result['relevance']
            
            # Вычисляем гибридный score
            for content, result in combined_results.items():
                semantic_score = result['semantic_score']
                lexical_score = result['lexical_score']
                
                # Нормализуем scores к 0-1
                semantic_score = min(1.0, max(0.0, semantic_score))
                lexical_score = min(1.0, max(0.0, lexical_score))
                
                # Взвешенная комбинация
                hybrid_score = (semantic_weight * semantic_score + 
                              (1 - semantic_weight) * lexical_score)
                
                result['semantic_score'] = semantic_score
                result['lexical_score'] = lexical_score
                result['hybrid_score'] = hybrid_score
            
            # Сортируем по гибридному score
            final_results = list(combined_results.values())
            final_results.sort(key=lambda x: x['hybrid_score'], reverse=True)
            
            return final_results[:limit]
            
        except Exception as e:
            logger.error(f"Ошибка гибридного поиска: {e}")
            return []
    
    async def compare_methods(self, question: str) -> Dict[str, Any]:
        """Сравнение всех методов поиска"""
        print(f"\n🔍 Сравнение методов поиска для: '{question}'")
        print("=" * 60)
        
        # Семантический поиск
        print("\n📊 Семантический поиск:")
        semantic_results = await self.semantic_search(question, 3)
        for i, result in enumerate(semantic_results, 1):
            distance = result['distance']
            content_type = result['content_type']
            content_preview = result['content'][:100] + "..." if len(result['content']) > 100 else result['content']
            print(f"  {i}. [{content_type}] (расстояние: {distance:.4f})")
            print(f"     {content_preview}")
        
        # Лексический поиск
        print("\n📊 Лексический поиск:")
        lexical_results = await self.lexical_search(question, 3)
        for i, result in enumerate(lexical_results, 1):
            relevance = result['relevance']
            content_type = result['content_type']
            content_preview = result['content'][:100] + "..." if len(result['content']) > 100 else result['content']
            print(f"  {i}. [{content_type}] (релевантность: {relevance:.4f})")
            print(f"     {content_preview}")
        
        # Гибридный поиск
        print("\n📊 Гибридный поиск:")
        hybrid_results = await self.hybrid_search(question, 3)
        for i, result in enumerate(hybrid_results, 1):
            hybrid_score = result['hybrid_score']
            semantic_score = result['semantic_score']
            lexical_score = result['lexical_score']
            content_type = result['content_type']
            content_preview = result['content'][:100] + "..." if len(result['content']) > 100 else result['content']
            print(f"  {i}. [{content_type}] (гибридный: {hybrid_score:.4f}, семантический: {semantic_score:.4f}, лексический: {lexical_score:.4f})")
            print(f"     {content_preview}")
        
        return {
            'semantic': semantic_results,
            'lexical': lexical_results,
            'hybrid': hybrid_results
        }

async def main():
    """Основная функция сравнения"""
    comparator = SearchMethodComparator()
    
    print("🚀 Сравнение методов поиска...")
    
    # Тестовые вопросы
    test_questions = [
        "Платежи за месяц по клиентам",
        "Покажи все платежи",
        "Статистика по платежам",
        "Пользователи системы",
        "Покажи таблицы с платежами"
    ]
    
    for question in test_questions:
        await comparator.compare_methods(question)
        print("\n" + "=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
