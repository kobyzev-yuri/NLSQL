#!/usr/bin/env python3
import os
import sys
import argparse
import asyncio
from typing import List, Dict, Any, Tuple
import asyncpg
import json


async def read_schema(conn: asyncpg.Connection, include_schemas: List[str]) -> Tuple[List[str], Dict[str, List[str]], List[Tuple[str, str, str]]]:
    schemas_tuple = tuple(include_schemas)
    tables = await conn.fetch(
        """
        select table_schema, table_name
        from information_schema.tables
        where table_schema = any($1::text[]) and table_type = 'BASE TABLE'
        order by 1,2
        """,
        schemas_tuple,
    )
    cols: Dict[str, List[str]] = {}
    for row in tables:
        fqtn = f"{row['table_schema']}.{row['table_name']}"
        colrows = await conn.fetch(
            """
            select column_name
            from information_schema.columns
            where table_schema=$1 and table_name=$2
            order by ordinal_position
            """,
            row['table_schema'], row['table_name']
        )
        cols[fqtn] = [c['column_name'] for c in colrows]
    fks = await conn.fetch(
        """
        select
          tc.table_schema as src_schema,
          tc.table_name   as src_table,
          kcu.column_name as src_column,
          ccu.table_schema as dst_schema,
          ccu.table_name   as dst_table,
          ccu.column_name  as dst_column
        from information_schema.table_constraints tc
        join information_schema.key_column_usage kcu
          on tc.constraint_name = kcu.constraint_name
         and tc.table_schema = kcu.table_schema
        join information_schema.constraint_column_usage ccu
          on ccu.constraint_name = tc.constraint_name
         and ccu.table_schema = tc.table_schema
        where tc.constraint_type = 'FOREIGN KEY'
          and tc.table_schema = any($1::text[])
        order by 1,2
        """,
        schemas_tuple,
    )
    fk_list = [(r['src_schema']+'.'+r['src_table'], r['src_column'], r['dst_schema']+'.'+r['dst_table']) for r in fks]
    return [f"{r['table_schema']}.{r['table_name']}" for r in tables], cols, fk_list


def make_select_examples(tables: List[str], cols: Dict[str, List[str]], limit: int) -> List[Dict[str, Any]]:
    examples: List[Dict[str, Any]] = []
    for t in tables:
        c = cols.get(t, [])
        sel_cols = ', '.join(c[:5]) if c else '*'
        sql = f"select {sel_cols} from {t} limit {limit};"
        q = f"Простая выборка из {t}"
        examples.append({"question": q, "sql": sql})
    return examples


def make_join_examples(fks: List[Tuple[str, str, str]], cols: Dict[str, List[str]], limit: int) -> List[Dict[str, Any]]:
    seen = set()
    examples: List[Dict[str, Any]] = []
    for src, src_col, dst in fks:
        key = (src, dst)
        if key in seen:
            continue
        seen.add(key)
        src_cols = cols.get(src, [])
        dst_cols = cols.get(dst, [])
        sel = []
        sel += [f"s.{c}" for c in src_cols[:3]]
        sel += [f"d.{c}" for c in dst_cols[:2]]
        sel_cols = ', '.join(sel) if sel else 's.*'
        sql = (
            f"select {sel_cols} from {src} s "
            f"join {dst} d on s.{src_col} = d.{(dst_cols[0] if dst_cols else src_col)} "
            f"limit {limit};"
        )
        q = f"Связанный отчёт {src} → {dst}"
        examples.append({"question": q, "sql": sql})
    return examples


async def validate_examples(conn: asyncpg.Connection, examples: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    valid: List[Dict[str, Any]] = []
    for ex in examples:
        sql = ex.get('sql', '')
        if not sql.lower().strip().startswith('select'):
            continue
        try:
            stmt = await conn.prepare(sql)
            await stmt.fetch(0)
            valid.append(ex)
        except Exception:
            # skip invalid
            pass
    return valid


async def main() -> int:
    parser = argparse.ArgumentParser(description="Generate DB‑relevant SQL examples based on live schema")
    parser.add_argument("--dsn", required=False, default=os.getenv("CUSTOMER_DB_DSN", ""))
    parser.add_argument("--schemas", nargs="+", default=["public"], help="Schemas to include")
    parser.add_argument("--limit", type=int, default=50, help="LIMIT for generated SELECTs")
    parser.add_argument("--out", required=True, help="Output .jsonl file")
    args = parser.parse_args()

    if not args.dsn:
        print("CUSTOMER_DB_DSN not set. Use --dsn or set env.", file=sys.stderr)
        return 2

    conn = await asyncpg.connect(dsn=args.dsn)
    try:
        tables, cols, fks = await read_schema(conn, args.schemas)
        ex1 = make_select_examples(tables, cols, args.limit)
        ex2 = make_join_examples(fks, cols, args.limit)
        valid = await validate_examples(conn, ex1 + ex2)
        with open(args.out, 'w', encoding='utf-8') as f:
            for ex in valid:
                f.write(json.dumps(ex, ensure_ascii=False) + "\n")
        print(f"Generated valid examples: {len(valid)} → {args.out}")
        return 0
    finally:
        await conn.close()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))



