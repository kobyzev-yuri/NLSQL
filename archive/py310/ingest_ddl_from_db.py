#!/usr/bin/env python3
"""
Ingest DDL from live PostgreSQL into vanna_vectors (content_type='ddl').
- Extracts per-table DDL via pg_dump -s -t schema.table
- Generates OpenAI embeddings (1536-dim) for content
- Inserts rows with metadata: {"schema":..., "table":...}
"""

import os
import subprocess
import json
import asyncio
import asyncpg
from typing import List, Tuple
from src.utils.embeddings import embed

DB_DSN = os.getenv("CUSTOMER_DB_DSN", "postgresql://postgres:1234@localhost:5432/test_docstructure")
SCHEMA = os.getenv("DDL_SCHEMA", "public")

async def get_public_tables() -> List[Tuple[str, str]]:
    conn = await asyncpg.connect(DB_DSN)
    rows = await conn.fetch(
        """
        SELECT table_schema, table_name
        FROM information_schema.tables
        WHERE table_schema=$1 AND table_type='BASE TABLE'
        ORDER BY table_name
        """,
        SCHEMA,
    )
    await conn.close()
    return [(r["table_schema"], r["table_name"]) for r in rows]

def get_table_ddl(schema: str, table: str) -> str:
    # Use pg_dump to get precise DDL
    conn_uri = DB_DSN
    # pg_dump DSN format via env PGPASSWORD not needed for URI
    cmd = [
        "pg_dump",
        "--schema-only",
        "--no-owner",
        "--no-privileges",
        "--table",
        f"{schema}.{table}",
        conn_uri,
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"pg_dump failed for {schema}.{table}: {res.stderr}")
    return res.stdout.strip()

def embed_vector_literal(text: str) -> str:
    vec = embed(text)
    return to_vector_literal(vec)

def to_vector_literal(vec):
    return '[' + ','.join(map(str, vec)) + ']'

async def upsert_ddl(schema: str, table: str, ddl: str) -> None:
    conn = await asyncpg.connect(DB_DSN)
    # Check existing
    existing = await conn.fetchrow(
        """
        SELECT id FROM vanna_vectors
        WHERE content_type='ddl' AND metadata->>'schema'=$1 AND metadata->>'table'=$2
        """,
        schema,
        table,
    )
    embedding_str = embed_vector_literal(ddl)
    metadata_json = json.dumps({"schema": schema, "table": table})
    if existing:
        await conn.execute(
            """
            UPDATE vanna_vectors
            SET content=$1,
                embedding=$2::vector,
                metadata=$3::jsonb,
                created_at=NOW()
            WHERE id=$4
            """,
            ddl,
            embedding_str,
            metadata_json,
            existing["id"],
        )
    else:
        await conn.execute(
            """
            INSERT INTO vanna_vectors (content, content_type, metadata, embedding)
            VALUES ($1, 'ddl', $2::jsonb, $3::vector)
            """,
            ddl,
            metadata_json,
            embedding_str,
        )
    await conn.close()

async def ingest_tables(tables: List[Tuple[str, str]]):
    ok, fail = 0, 0
    for schema, table in tables:
        try:
            ddl = get_table_ddl(schema, table)
            if not ddl.strip():
                continue
            await upsert_ddl(schema, table, ddl)
            ok += 1
            print(f"✅ Ingested DDL: {schema}.{table}")
        except Exception as e:
            fail += 1
            print(f"❌ {schema}.{table}: {e}")
    print(f"Done. ok={ok}, fail={fail}")

async def main():
    # If specific tables provided via env DDL_TABLES (comma-separated), use them
    tables_arg = os.getenv("DDL_TABLES")
    if tables_arg:
        pairs: List[Tuple[str,str]] = []
        for name in [t.strip() for t in tables_arg.split(",") if t.strip()]:
            if "." in name:
                schema, table = name.split(".", 1)
            else:
                schema, table = SCHEMA, name
            pairs.append((schema, table))
    else:
        pairs = await get_public_tables()
    await ingest_tables(pairs)

if __name__ == "__main__":
    asyncio.run(main())
