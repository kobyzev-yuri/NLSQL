#!/usr/bin/env python3
"""
Generate HF embeddings for records in vanna_vectors.
Supports rebuild (recompute all) and auto-alter vector dimension to match model.
"""

import os
import asyncio
import asyncpg
import logging
from typing import List
from pathlib import Path
from datetime import datetime

# Load environment variables from config.env
from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / "config.env")

# Setup logging with file handler
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f"generate_embeddings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
logger.info(f"Logging to {log_file}")


async def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--dsn', default=os.getenv('DATABASE_URL', 'postgresql://postgres:1234@localhost:5432/test_docstructure'))
    parser.add_argument('--model', default=os.getenv('HF_MODEL_NAME', 'sentence-transformers/all-MiniLM-L6-v2'))
    parser.add_argument('--batch-size', type=int, default=200)
    parser.add_argument('--rebuild', action='store_true', help='Пересчитать эмбеддинги для всех записей')
    parser.add_argument('--alter', action='store_true', help='Автоматически изменить размерности vector под модель')
    args = parser.parse_args()

    # Lazy import to avoid startup cost when unused
    from sentence_transformers import SentenceTransformer

    logger.info("=" * 80)
    logger.info(f"Starting embedding generation")
    logger.info(f"Model: {args.model}")
    logger.info(f"Database: {args.dsn}")
    logger.info(f"Rebuild mode: {args.rebuild}")
    logger.info(f"Alter dimension: {args.alter}")
    logger.info(f"Batch size: {args.batch_size}")
    logger.info("=" * 80)
    
    model = SentenceTransformer(args.model)
    logger.info(f"Loaded HF model: {args.model}")
    # Determine embedding dimension
    test_vec = model.encode(["test"], normalize_embeddings=True)[0]
    dim = len(test_vec)
    logger.info(f"Model embedding dimension: {dim}")

    conn = await asyncpg.connect(args.dsn)

    async def get_current_dim() -> int | None:
        try:
            row = await conn.fetchrow(
                """
                SELECT format_type(a.atttypid, a.atttypmod) AS t
                FROM pg_attribute a
                JOIN pg_class c ON a.attrelid = c.oid
                WHERE c.relname = 'vanna_vectors' AND a.attname = 'embedding'
                """
            )
            if not row or not row['t']:
                return None
            t: str = row['t']
            if t.startswith('vector(') and t.endswith(')'):
                return int(t[len('vector('):-1])
            return None
        except Exception:
            return None

    # Ensure vector dim matches model
    target_dim = dim
    current_dim = await get_current_dim()
    logger.info(f"Current embedding dim: {current_dim}, target: {target_dim}")
    write_column = 'embedding'

    if args.alter and current_dim != target_dim:
        # Try simple ALTER first
        try:
            await conn.execute(f"ALTER TABLE vanna_vectors ALTER COLUMN embedding TYPE vector({target_dim})")
            logger.info(f"ALTERed vanna_vectors.embedding -> vector({target_dim})")
            current_dim = target_dim
        except Exception as e:
            logger.warning(f"Direct ALTER failed: {e}")
            # Fallback: create new column, write there, then swap (only safe in rebuild mode)
            if not args.rebuild:
                raise RuntimeError("Column dim mismatch and cannot ALTER; rerun with --rebuild --alter")
            try:
                await conn.execute(f"ALTER TABLE vanna_vectors ADD COLUMN embedding_new vector({target_dim})")
                write_column = 'embedding_new'
                logger.info(f"Created column embedding_new vector({target_dim})")
            except Exception as e2:
                # If column already exists, assume to use it
                logger.warning(f"ADD COLUMN embedding_new failed/exists: {e2}\\nUsing existing embedding column where possible.")
                # Try to detect existence
                row = await conn.fetchrow(
                    """
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='vanna_vectors' AND column_name='embedding_new'
                    """
                )
                if row:
                    write_column = 'embedding_new'

    where_clause = "" if args.rebuild else "WHERE embedding IS NULL"
    records = await conn.fetch(f"""
        SELECT id, content FROM vanna_vectors {where_clause} ORDER BY id
    """)
    total = len(records)
    logger.info(f"Records to (re)embed: {total}")

    for i in range(0, total, args.batch_size):
        batch = records[i:i+args.batch_size]
        texts: List[str] = [(r['content'] or '').replace('\x00', '').strip() for r in batch]
        emb = model.encode(texts, normalize_embeddings=True)
        # Save
        for rec, vec in zip(batch, emb):
            vec_str = '[' + ','.join(map(lambda x: f"{float(x)}", vec.tolist())) + ']'
            await conn.execute(
                f"""
                UPDATE vanna_vectors SET {write_column} = $1::vector WHERE id = $2
                """,
                vec_str, rec['id']
            )
        logger.info(f"Processed {min(i+args.batch_size, total)}/{total}")

    # If we wrote to embedding_new, swap columns
    if write_column == 'embedding_new':
        logger.info("Swapping embedding_new -> embedding")
        try:
            await conn.execute("ALTER TABLE vanna_vectors DROP COLUMN embedding")
        except Exception as e:
            logger.warning(f"Drop old embedding failed: {e}")
        await conn.execute("ALTER TABLE vanna_vectors RENAME COLUMN embedding_new TO embedding")

    await conn.close()
    logger.info("=" * 80)
    logger.info(f"Completed: processed {total} records")
    logger.info(f"Log saved to: {log_file}")
    logger.info("=" * 80)


if __name__ == '__main__':
    asyncio.run(main())









