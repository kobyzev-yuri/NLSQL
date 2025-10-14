#!/usr/bin/env python3
"""
Скрипт для генерации эмбеддингов для существующих записей в vanna_vectors
"""

import os
import sys
import asyncio
import asyncpg
import logging
from typing import List, Dict, Any
from openai import OpenAI

# Добавляем путь к модулям
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

logger = logging.getLogger(__name__)

class EmbeddingGenerator:
    """Генератор эмбеддингов для vanna_vectors"""
    
    def __init__(self, dsn: str, api_key: str, base_url: str = None):
        self.dsn = dsn
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url or "https://api.proxyapi.ru/openai/v1"
        )
        
    async def generate_embeddings(self, batch_size: int = 100, dry_run: bool = False):
        """
        Генерация эмбеддингов для всех записей без embedding
        
        Args:
            batch_size: Размер батча для обработки
            dry_run: Только показать что будет сделано, не выполнять
        """
        try:
            # Подключаемся к БД
            conn = await asyncpg.connect(self.dsn)
            
            # Получаем записи без эмбеддингов
            records = await conn.fetch("""
                SELECT id, content, content_type 
                FROM vanna_vectors 
                WHERE embedding IS NULL
                ORDER BY id
            """)
            
            total = len(records)
            logger.info(f"📊 Найдено {total} записей без эмбеддингов")
            
            if dry_run:
                logger.info("🔍 DRY RUN - показываем что будет сделано:")
                for i, record in enumerate(records[:10]):  # Показываем первые 10
                    logger.info(f"  {i+1}. ID={record['id']}, type={record['content_type']}, content={record['content'][:50]}...")
                if total > 10:
                    logger.info(f"  ... и еще {total-10} записей")
                return
            
            # Обрабатываем батчами
            processed = 0
            for i in range(0, total, batch_size):
                batch = records[i:i + batch_size]
                logger.info(f"🔄 Обрабатываем батч {i//batch_size + 1}/{(total-1)//batch_size + 1} ({len(batch)} записей)")
                
                # Генерируем эмбеддинги для батча
                embeddings = await self._generate_batch_embeddings(batch)
                
                # Сохраняем в БД
                await self._save_embeddings(conn, batch, embeddings)
                
                processed += len(batch)
                logger.info(f"✅ Обработано {processed}/{total} записей")
            
            await conn.close()
            logger.info(f"🎉 Генерация эмбеддингов завершена! Обработано {processed} записей")
            
        except Exception as e:
            logger.error(f"❌ Ошибка генерации эмбеддингов: {e}")
            raise
    
    async def _generate_batch_embeddings(self, batch: List[asyncpg.Record]) -> List[List[float]]:
        """Генерация эмбеддингов для батча записей"""
        try:
            # Подготавливаем тексты для эмбеддингов
            texts = []
            for record in batch:
                # Очищаем текст от NUL-байтов и лишних пробелов
                clean_text = record['content'].replace('\x00', '').strip()
                if clean_text:
                    texts.append(clean_text)
                else:
                    texts.append("")  # Пустой текст для пустых записей
            
            # Генерируем эмбеддинги через OpenAI API
            response = self.client.embeddings.create(
                model="text-embedding-ada-002",
                input=texts
            )
            
            # Извлекаем эмбеддинги
            embeddings = [data.embedding for data in response.data]
            
            logger.info(f"✅ Сгенерировано {len(embeddings)} эмбеддингов")
            return embeddings
            
        except Exception as e:
            logger.error(f"❌ Ошибка генерации батча эмбеддингов: {e}")
            raise
    
    async def _save_embeddings(self, conn: asyncpg.Connection, batch: List[asyncpg.Record], embeddings: List[List[float]]):
        """Сохранение эмбеддингов в БД"""
        try:
            for record, embedding in zip(batch, embeddings):
                # Конвертируем список в строку для pgvector
                embedding_str = '[' + ','.join(map(str, embedding)) + ']'
                await conn.execute("""
                    UPDATE vanna_vectors 
                    SET embedding = $1::vector 
                    WHERE id = $2
                """, embedding_str, record['id'])
            
            logger.info(f"💾 Сохранено {len(embeddings)} эмбеддингов в БД")
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения эмбеддингов: {e}")
            raise

async def main():
    """Основная функция"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Генерация эмбеддингов для vanna_vectors")
    parser.add_argument("--dsn", required=True, help="DSN подключения к PostgreSQL")
    parser.add_argument("--api-key", required=True, help="OpenAI API ключ")
    parser.add_argument("--batch-size", type=int, default=100, help="Размер батча")
    parser.add_argument("--dry-run", action="store_true", help="Только показать что будет сделано")
    
    args = parser.parse_args()
    
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Создаем генератор
    generator = EmbeddingGenerator(
        args.dsn, 
        args.api_key,
        base_url="https://api.proxyapi.ru/openai/v1"
    )
    
    # Генерируем эмбеддинги
    await generator.generate_embeddings(
        batch_size=args.batch_size,
        dry_run=args.dry_run
    )

if __name__ == "__main__":
    asyncio.run(main())
