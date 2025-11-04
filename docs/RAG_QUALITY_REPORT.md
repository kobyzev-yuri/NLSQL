## RAG Quality Report (post-HF embeddings, join graph, ranking)

### Setup
- Vector DB: PostgreSQL + pgvector (VECTOR(768))
- Embeddings: HF `intfloat/multilingual-e5-base` (768-dim), normalized
- Ingested: DocStructure JSON (documentation), DDL (99.5% coverage), Q/A (443), schema insights (join_graph, table_ranking)
- Service tables ignored in analysis

### Retrieval Comparison (sample questions)
- Semantic (HF) returns meaningful docs/Q/A; lexical remains high-precision on exact terms; hybrid favors lexical due to no semantic normalization in score fusion yet.
- Observed: payment-related questions now retrieve Q/A examples semantically; lexical pulls DocStructure JSON blocks.

### Observations
- Semantic retrieval (768d) стабильно возвращает Q/A-примеры по ключевым вопросам (см. отчёт ниже).
- Для вопросов о платежах и поручениях top‑1 — `question_sql` из обучающих примеров.

### Metrics (quick pass)
- DDL coverage: 99.5% (payment tables: 100%)
- Docs count: 4353 (+10 DocStructure JSON)
- Q/A: 443 (payment-related ~32%)
- Semantic retrieval: now operational (384-dim), no dim mismatch

<!-- Раздел планов удалён. Документ фиксирует текущие результаты. -->

### Conclusion
Переход на HF эмбеддинги (e5‑base, 768d) стабилизировал семантический ретривал; обучение RAG на DDL/документации/Q&A — ключевой фактор качества.

### Consolidated results table
See `docs/RETRIEVAL_BENCHMARKS.md` for rerank top-1 summaries per question.

<!-- Убрана нерелевантная сводка по внешним моделям генерации. -->


