#!/usr/bin/env python3
"""
Run retrieval (semantic HF + lexical + hybrid) and apply cross-encoder reranking.
Outputs a markdown table with top results per question.
"""

import os
import asyncpg
import asyncio
from typing import List, Dict
from sentence_transformers import SentenceTransformer, CrossEncoder

DB_DSN = os.getenv('DATABASE_URL', 'postgresql://postgres:1234@localhost:5432/test_docstructure')
HF_MODEL = os.getenv('HF_MODEL_NAME', 'sentence-transformers/all-MiniLM-L6-v2')
RERANK_MODEL = os.getenv('RERANK_MODEL_NAME', 'cross-encoder/ms-marco-MiniLM-L-6-v2')


async def semantic_search(conn, embedder: SentenceTransformer, question: str, limit: int = 20) -> List[Dict]:
    q_emb = embedder.encode([question], normalize_embeddings=True)[0]
    emb_str = '[' + ','.join(map(lambda x: f"{float(x)}", q_emb.tolist())) + ']'
    rows = await conn.fetch(
        """
        SELECT id, content, content_type, 1 - (embedding <-> $1::vector) as score
        FROM vanna_vectors
        WHERE embedding IS NOT NULL
        ORDER BY embedding <-> $1::vector
        LIMIT $2
        """,
        emb_str, limit,
    )
    return [dict(r) for r in rows]


async def lexical_search(conn, question: str, limit: int = 20) -> List[Dict]:
    import re
    words = re.findall(r'\b\w+\b', question.lower())
    stop = {'и','в','на','с','по','для','от','до','за','из','к','о','об','при','про','со','у','the','a','an','and','or','but','in','on','at','to','for','of','with','by'}
    kw = [w for w in words if len(w) > 2 and w not in stop]
    if not kw:
        return []
    params = [f"%{w}%" for w in kw]
    placeholders = ' OR '.join([f"content ILIKE ${i+1}" for i in range(len(params))])
    rows = await conn.fetch(
        f"""
        SELECT id, content, content_type, 1.0 as score
        FROM vanna_vectors
        WHERE {placeholders}
        LIMIT ${len(params)+1}
        """,
        *params, limit,
    )
    return [dict(r) for r in rows]


def rerank(cross: CrossEncoder, question: str, candidates: List[Dict], top_k: int = 10) -> List[Dict]:
    pairs = [(question, c['content'][:2000]) for c in candidates]
    scores = cross.predict(pairs)
    for c, s in zip(candidates, scores):
        c['rerank_score'] = float(s)
    return sorted(candidates, key=lambda x: x['rerank_score'], reverse=True)[:top_k]


async def run():
    questions = [
        "Платежи за месяц по клиентам",
        "Покажи все платежи",
        "Пользователи системы",
        "Покажи таблицы с платежами"
    ]
    embedder = SentenceTransformer(HF_MODEL)
    cross = CrossEncoder(RERANK_MODEL)
    conn = await asyncpg.connect(DB_DSN)

    lines = []
    lines.append("| Вопрос | Метод | Top1 type | Rerank score | Preview |")
    lines.append("|---|---|---|---:|---|")

    for q in questions:
        sem = await semantic_search(conn, embedder, q, 20)
        lex = await lexical_search(conn, q, 20)
        combined = {c['id']: c for c in sem}
        for c in lex:
            combined.setdefault(c['id'], c)
        cand = list(combined.values())
        reranked = rerank(cross, q, cand, top_k=5)
        if reranked:
            top = reranked[0]
            preview = (top['content'][:80] + '...') if len(top['content']) > 80 else top['content']
            lines.append(f"| {q} | rerank | {top['content_type']} | {top['rerank_score']:.3f} | {preview.replace('|','/')} |")
        else:
            lines.append(f"| {q} | rerank | - | 0.000 | - |")

    await conn.close()

    out_path = os.path.join(os.path.dirname(__file__), '..', 'RETRIEVAL_BENCHMARKS.md')
    out_path = os.path.abspath(out_path)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
    print(f"Saved: {out_path}")


if __name__ == '__main__':
    asyncio.run(run())


