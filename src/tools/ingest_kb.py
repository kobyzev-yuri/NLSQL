#!/usr/bin/env python3
import os
import sys
import argparse
import asyncio
import hashlib
import json
from pathlib import Path
from typing import List, Tuple

import asyncpg


def compute_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def read_items_from_path(path: Path) -> List[Tuple[str, str, str, str]]:
    """
    Return list of items as tuples: (type, uri, title, content)
    Supports files: .sql -> type=ddl, .md/.txt -> type=doc, .jsonl (with {question,answer})-> type=qa
    """
    items: List[Tuple[str, str, str, str]] = []
    if path.is_file():
        paths = [path]
    else:
        paths = list(path.rglob("*"))
    for p in paths:
        if not p.is_file():
            continue
        ext = p.suffix.lower()
        try:
            if ext == ".sql":
                content = p.read_text(encoding="utf-8", errors="ignore").replace('\x00', '')
                items.append(("ddl", str(p), p.name, content))
            elif ext in {".md", ".txt"}:
                content = p.read_text(encoding="utf-8", errors="ignore").replace('\x00', '')
                items.append(("doc", str(p), p.name, content))
            elif ext == ".jsonl":
                for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
                    if not line.strip():
                        continue
                    try:
                        obj = json.loads(line)
                        q = obj.get("question") or obj.get("q") or ""
                        a = obj.get("answer") or obj.get("a") or obj.get("sql") or ""
                        if q or a:
                            content = json.dumps({"question": q, "answer": a}, ensure_ascii=False).replace('\x00', '')
                            items.append(("qa", f"{p}#line", p.name, content))
                    except Exception:
                        # skip broken lines
                        pass
        except Exception:
            # skip unreadable files
            pass
    return items


def chunk_text(text: str, max_chars: int = 4000) -> List[str]:
    chunks: List[str] = []
    cursor = 0
    n = len(text)
    while cursor < n:
        end = min(cursor + max_chars, n)
        chunks.append(text[cursor:end])
        cursor = end
    return chunks if chunks else [""]


async def ingest_items(dsn: str, items: List[Tuple[str, str, str, str]], dry_run: bool = False) -> int:
    conn = await asyncpg.connect(dsn=dsn)
    try:
        total_sources = 0
        for item_type, uri, title, content in items:
            src_hash = compute_hash(f"{item_type}\n{uri}\n{title}\n{content}")
            if dry_run:
                total_sources += 1
                continue
            src_id = await conn.fetchval(
                """
                insert into sources(type, uri, title, hash)
                values($1, $2, $3, $4)
                on conflict do nothing
                returning id
                """,
                item_type, uri, title, src_hash,
            )
            # If conflict (exists), fetch id
            if src_id is None:
                src_id = await conn.fetchval("select id from sources where hash=$1 limit 1", src_hash)
            if src_id is None:
                continue
            parts = chunk_text(content)
            for i, part in enumerate(parts):
                ch_hash = compute_hash(part)
                await conn.execute(
                    """
                    insert into chunks(source_id, ordinal, content, token_count, hash)
                    values($1, $2, $3, 0, $4)
                    on conflict do nothing
                    """,
                    src_id, i, part, ch_hash,
                )
            total_sources += 1
        return total_sources
    finally:
        await conn.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest KB items into RAG tables (sources/chunks)")
    parser.add_argument("input", help="Path to file or directory with KB items (.sql, .md/.txt, .jsonl)")
    parser.add_argument("--dsn", dest="dsn", default=os.getenv("CUSTOMER_DB_DSN", ""), help="Postgres DSN")
    parser.add_argument("--dry-run", action="store_true", help="Do not write to DB; just parse and count")
    args = parser.parse_args()

    if not args.dsn:
        print("CUSTOMER_DB_DSN not set. Use --dsn or set env.", file=sys.stderr)
        return 2
    p = Path(args.input)
    if not p.exists():
        print(f"Input path not found: {p}", file=sys.stderr)
        return 3
    items = read_items_from_path(p)
    print(f"Parsed {len(items)} items from {p}")
    total = asyncio.run(ingest_items(args.dsn, items, dry_run=args.dry_run))
    print(f"Ingested sources: {total} (dry_run={args.dry_run})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


