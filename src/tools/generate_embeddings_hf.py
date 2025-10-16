#!/usr/bin/env python3
"""
Generate 384-dim HF embeddings for records in vanna_vectors where embedding IS NULL.
Uses sentence-transformers (HF). Assumes embedding column is VECTOR(384).
"""

import os
import asyncio
import asyncpg
import logging
from typing import List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--dsn', default=os.getenv('DATABASE_URL', 'postgresql://postgres:1234@localhost:5432/test_docstructure'))
    parser.add_argument('--model', default=os.getenv('HF_MODEL_NAME', 'sentence-transformers/all-MiniLM-L6-v2'))
    parser.add_argument('--batch-size', type=int, default=200)
    args = parser.parse_args()

    # Lazy import to avoid startup cost when unused
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(args.model)
    logger.info(f"Loaded HF model: {args.model}")

    conn = await asyncpg.connect(args.dsn)
    records = await conn.fetch("""
        SELECT id, content FROM vanna_vectors WHERE embedding IS NULL ORDER BY id
    """)
    total = len(records)
    logger.info(f"Found {total} records without embeddings")

    for i in range(0, total, args.batch_size):
        batch = records[i:i+args.batch_size]
        texts: List[str] = [(r['content'] or '').replace('\x00', '').strip() for r in batch]
        emb = model.encode(texts, normalize_embeddings=True)
        # Save
        for rec, vec in zip(batch, emb):
            vec_str = '[' + ','.join(map(lambda x: f"{float(x)}", vec.tolist())) + ']'
            await conn.execute("""
                UPDATE vanna_vectors SET embedding = $1::vector WHERE id = $2
            """, vec_str, rec['id'])
        logger.info(f"Processed {min(i+args.batch_size, total)}/{total}")

    await conn.close()
    logger.info("Done")


if __name__ == '__main__':
    asyncio.run(main())


