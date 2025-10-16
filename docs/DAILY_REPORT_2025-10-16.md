## Daily Report — 2025-10-16

### Summary
- Fixed RAG context pipeline and domain detection for assignments.
- Ensured PostgreSQL dialect compliance and unified 384-d embeddings.
- Resolved Mock API conflicts (moved to 8081) and updated all app configs.
- Restored and improved Streamlit UI: examples fill input, SQL executes, layout fixed.
- Verified end-to-end: SQL generated and executed via Mock API.

### Key Changes
- Query context building fixed in `src/services/query_service.py` (await, parsing).
- SQL cleaning enforced in `src/vanna/vanna_pgvector_native.py` and `src/vanna/optimized_dual_pipeline.py`.
- Mock API endpoints and ports updated in:
  - `src/simple_web_interface.py`
  - `src/web_interface.py`
  - `src/services/customer_api_service.py`
  - `src/vanna/vector_db_configs.py`
- Streamlit rebuilt to `src/streamlit_main.py` and launched on 8501.

### Issues Resolved
- Dimension mismatch 384 vs 1536 — unified to HF all-MiniLM-L6-v2.
- Empty/insufficient context — fixed RAG context retrieval and domain mapping.
- Mock API 8080 conflict (Apache) — moved to 8081, updated URLs.
- Streamlit white screen and session state error — rebuilt UI, fixed st.session_state usage.
- HTTP 422 on execute — corrected form param to question.

### Validation
- API /generate-sql -> OK; returns SQL with tbl_principal_assignment.
- API /execute-sql -> OK via Mock API /api/sql/execute.
- Streamlit UI -> examples -> generate -> execute -> table renders.

### Next Steps
- Add more domain synonyms and table map for better recall.
- Add UI toggle to switch reranking on/off for experiments.
