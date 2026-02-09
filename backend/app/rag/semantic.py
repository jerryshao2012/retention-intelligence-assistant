from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

import numpy as np
from langchain_ollama import OllamaEmbeddings

from app.core.config import OLLAMA_BASE_URL, OLLAMA_EMBED_MODEL


@dataclass
class CorpusItem:
    id: str
    text: str
    payload: Dict[str, Any]


class SemanticIndex:
    def __init__(self, items: List[CorpusItem]):
        self.items = items
        self._embeddings = None
        self._model = OllamaEmbeddings(model=OLLAMA_EMBED_MODEL, base_url=OLLAMA_BASE_URL)

    def _embed(self, texts: List[str]) -> np.ndarray:
        vectors = self._model.embed_documents(texts)
        return np.array(vectors, dtype=np.float32)

    def _ensure_embeddings(self):
        if self._embeddings is None:
            self._embeddings = self._embed([item.text for item in self.items])

    def search(self, query: str, top_k: int = 3) -> List[Tuple[CorpusItem, float]]:
        if not self.items:
            return []
        self._ensure_embeddings()
        query_vec = self._embed([query])[0]
        denom = np.linalg.norm(self._embeddings, axis=1) * np.linalg.norm(query_vec)
        scores = np.dot(self._embeddings, query_vec) / np.clip(denom, 1e-6, None)
        ranked_idx = np.argsort(scores)[::-1][:top_k]
        return [(self.items[i], float(scores[i])) for i in ranked_idx]
