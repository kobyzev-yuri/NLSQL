#!/usr/bin/env python3
"""
Генерация инсайтов по схеме:
 - Join-граф (связи таблиц по внешним ключам)
 - Ранжирование таблиц по использованию в Q/A
Ингест результатов как documentation в vanna_vectors.
"""

import os
import re
import json
import logging
from collections import defaultdict, Counter
from pathlib import Path

import psycopg

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SERVICE_PREFIXES = (
    'vanna_', 'chroma_', 'pgvector', 'faiss_', 'vector_', 'embeddings_', 'mock_'
)
SERVICE_EXACT = {'vanna_vectors'}


def get_conn():
    db_url = os.getenv('DATABASE_URL', 'postgresql://postgres:1234@localhost:5432/test_docstructure')
    return psycopg.connect(db_url)


def list_public_tables(cur):
    cur.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema='public' AND table_type='BASE TABLE'
    """)
    tables = [r[0] for r in cur.fetchall()]
    result = []
    for t in tables:
        if t in SERVICE_EXACT:
            continue
        if any(t.startswith(p) for p in SERVICE_PREFIXES):
            continue
        result.append(t)
    return sorted(result)


def fetch_foreign_keys(cur):
    cur.execute(
        """
        SELECT
            tc.table_name AS from_table,
            kcu.column_name AS from_column,
            ccu.table_name AS to_table,
            ccu.column_name AS to_column
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
          ON tc.constraint_name = kcu.constraint_name
         AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage AS ccu
          ON ccu.constraint_name = tc.constraint_name
         AND ccu.table_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
          AND tc.table_schema = 'public'
        """
    )
    rows = cur.fetchall()
    return rows


def build_join_graph(tables, fk_rows):
    edges = defaultdict(list)
    degree = Counter()
    for from_table, from_col, to_table, to_col in fk_rows:
        if from_table not in tables or to_table not in tables:
            continue
        edges[from_table].append((to_table, from_col, to_col))
        edges[to_table].append((from_table, to_col, from_col))
        degree[from_table] += 1
        degree[to_table] += 1
    return edges, degree


def extract_table_usage_from_qa(cur, valid_tables):
    cur.execute(
        """
        SELECT content
        FROM vanna_vectors
        WHERE content_type = 'question_sql'
        """
    )
    usage = Counter()
    contents = [r[0] for r in cur.fetchall()]
    # Simple heuristic: count occurrences of valid table names as whole words
    for text in contents:
        for t in valid_tables:
            # word boundary or quotes
            if re.search(rf'\b{re.escape(t)}\b', text):
                usage[t] += 1
    return usage


def format_join_graph_doc(edges, degree):
    top = [t for t, _ in degree.most_common(20)]
    lines = []
    lines.append("Join-граф (верхние 20 по связности):")
    for t in top:
        lines.append(f"- {t} (степень: {degree[t]})")
        for (nbr, from_col, to_col) in edges.get(t, [])[:10]:
            lines.append(f"  • → {nbr} ({from_col} → {to_col})")
    return "\n".join(lines)


def format_table_ranking_doc(usage):
    lines = []
    lines.append("Ранжирование таблиц по использованию в Q/A:")
    for t, c in usage.most_common(50):
        lines.append(f"- {t}: {c}")
    return "\n".join(lines)


def ingest_document(cur, table_name, content, meta):
    cur.execute(
        f"""
        INSERT INTO vanna_vectors (content, content_type, metadata)
        VALUES (%s, 'documentation', %s)
        RETURNING id
        """,
        (content, json.dumps(meta))
    )
    return cur.fetchone()[0]


def main():
    conn = get_conn()
    with conn.cursor() as cur:
        tables = list_public_tables(cur)
        fk_rows = fetch_foreign_keys(cur)
        edges, degree = build_join_graph(tables, fk_rows)

        join_doc = format_join_graph_doc(edges, degree)
        usage = extract_table_usage_from_qa(cur, set(tables))
        rank_doc = format_table_ranking_doc(usage)

        join_id = ingest_document(cur, 'vanna_vectors', join_doc, {
            'type': 'documentation',
            'source': 'schema_insights',
            'kind': 'join_graph'
        })
        rank_id = ingest_document(cur, 'vanna_vectors', rank_doc, {
            'type': 'documentation',
            'source': 'schema_insights',
            'kind': 'table_ranking'
        })
        conn.commit()
        print(f"✅ Ингест инсайтов завершен. join_graph_id={join_id}, ranking_id={rank_id}")
    conn.close()


if __name__ == '__main__':
    main()


