#!/usr/bin/env python3
"""
Unified embedding utility with switchable backend:
- OPENAI (default): uses text-embedding-ada-002 or TEXT_EMBEDDING_MODEL
- HF (sentence-transformers): loads from HF_MODEL_NAME or HF_MODEL_PATH

Env vars:
- EMBEDDER=OPENAI|HF
- TEXT_EMBEDDING_MODEL (default: text-embedding-ada-002)
- OPENAI_BASE_URL, PROXYAPI_KEY/OPENAI_API_KEY
- HF_MODEL_NAME or HF_MODEL_PATH (e.g., ../steccom-rag-lk/model or 'BAAI/bge-m3')
"""

import os
import threading
from typing import List

_init_lock = threading.Lock()
_state = {
    "backend": None,
    "openai_client": None,
    "openai_model": None,
    "hf_model": None,
    "hf_tokenizer": None,
}


def _ensure_initialized():
    if _state["backend"] is not None:
        return
    with _init_lock:
        if _state["backend"] is not None:
            return
        backend = (os.getenv("EMBEDDER") or "OPENAI").upper()
        if backend not in ("OPENAI", "HF"):
            backend = "OPENAI"
        _state["backend"] = backend

        if backend == "OPENAI":
            from openai import OpenAI
            base_url = os.getenv("OPENAI_BASE_URL")
            api_key = os.getenv("PROXYAPI_KEY") or os.getenv("PROXYAPI_API_KEY") or os.getenv("OPENAI_API_KEY")
            model = os.getenv("TEXT_EMBEDDING_MODEL", "text-embedding-ada-002")
            _state["openai_client"] = OpenAI(api_key=api_key, base_url=base_url) if api_key else OpenAI()
            _state["openai_model"] = model
        else:
            # HF sentence-transformers backend
            model_name = os.getenv("HF_MODEL_NAME") or os.getenv("HF_MODEL_PATH") or "sentence-transformers/all-MiniLM-L6-v2"
            try:
                from sentence_transformers import SentenceTransformer
                _state["hf_model"] = SentenceTransformer(model_name)
            except Exception:
                # Fallback to transformers if sentence-transformers not available
                from transformers import AutoTokenizer, AutoModel
                import torch
                tok = AutoTokenizer.from_pretrained(model_name)
                mdl = AutoModel.from_pretrained(model_name)
                _state["hf_tokenizer"] = tok
                _state["hf_model"] = mdl


def embed(text: str) -> List[float]:
    """Embed a single text to a vector (list[float])."""
    _ensure_initialized()
    backend = _state["backend"]

    if backend == "OPENAI":
        resp = _state["openai_client"].embeddings.create(model=_state["openai_model"], input=text)
        return resp.data[0].embedding

    # HF backend
    if _state.get("hf_tokenizer") is None:
        # sentence-transformers API
        vec = _state["hf_model"].encode([text], normalize_embeddings=True)
        return vec[0].tolist()

    # transformers fallback (no sentence-transformers)
    import torch
    tok = _state["hf_tokenizer"]
    mdl = _state["hf_model"]
    with torch.no_grad():
        inputs = tok(text, return_tensors='pt', truncation=True, max_length=512)
        outputs = mdl(**inputs)
        # mean pooling over token embeddings
        last_hidden = outputs.last_hidden_state  # (1, seq, hidden)
        mask = inputs['attention_mask'].unsqueeze(-1)
        summed = (last_hidden * mask).sum(dim=1)
        counts = mask.sum(dim=1).clamp(min=1)
        mean = summed / counts
        vec = mean[0].cpu().tolist()
        # Optionally L2 normalize
        import math
        norm = math.sqrt(sum(x*x for x in vec)) or 1.0
        return [x / norm for x in vec]


def embed_texts(texts: List[str]) -> List[List[float]]:
    _ensure_initialized()
    backend = _state["backend"]

    if backend == "OPENAI":
        # Batch embedding for efficiency
        resp = _state["openai_client"].embeddings.create(model=_state["openai_model"], input=texts)
        return [d.embedding for d in resp.data]

    if _state.get("hf_tokenizer") is None:
        mat = _state["hf_model"].encode(texts, normalize_embeddings=True)
        return [row.tolist() for row in mat]

    import torch
    tok = _state["hf_tokenizer"]
    mdl = _state["hf_model"]
    out: List[List[float]] = []
    with torch.no_grad():
        for text in texts:
            inputs = tok(text, return_tensors='pt', truncation=True, max_length=512)
            outputs = mdl(**inputs)
            last_hidden = outputs.last_hidden_state
            mask = inputs['attention_mask'].unsqueeze(-1)
            summed = (last_hidden * mask).sum(dim=1)
            counts = mask.sum(dim=1).clamp(min=1)
            mean = summed / counts
            vec = mean[0].cpu().tolist()
            import math
            norm = math.sqrt(sum(x*x for x in vec)) or 1.0
            out.append([x / norm for x in vec])
    return out


