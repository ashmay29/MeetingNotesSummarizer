import os
from typing import List, Tuple, Optional
import numpy as np

try:
    import faiss  # type: ignore
    _has_faiss = True
except Exception:
    faiss = None  # type: ignore
    _has_faiss = False

# Pinecone (optional) - used when VECTOR_BACKEND=pinecone
_has_pinecone = False
try:
    from pinecone import Pinecone
    _has_pinecone = True
except Exception:
    Pinecone = None  # type: ignore
    _has_pinecone = False

# Two separate indexes for title and summary scopes
class VectorStore:
    def __init__(self, dim: int):
        self.dim = dim
        self.backend = os.getenv("VECTOR_BACKEND", "faiss").lower()
        self.use_faiss = _has_faiss and self.backend == "faiss"
        # in-memory ids and vectors for fallback
        self._ids_title: List[str] = []
        self._vecs_title: List[np.ndarray] = []
        self._ids_summary: List[str] = []
        self._vecs_summary: List[np.ndarray] = []
        if self.use_faiss:
            self._index_title = faiss.IndexFlatIP(dim)
            self._index_summary = faiss.IndexFlatIP(dim)
        else:
            self._index_title = None
            self._index_summary = None

        # Pinecone init if selected
        self.use_pinecone = (self.backend == "pinecone")
        if self.use_pinecone:
            if not _has_pinecone:
                raise RuntimeError("Pinecone client not installed. Add 'pinecone' to requirements and set VECTOR_BACKEND=pinecone")
            api_key = os.getenv("PINECONE_API_KEY")
            index_name = os.getenv("PINECONE_INDEX")
            host = os.getenv("PINECONE_HOST")
            if not api_key or not index_name:
                raise RuntimeError("PINECONE_API_KEY and PINECONE_INDEX must be set in backend_py/.env when using Pinecone")
            self._pc = Pinecone(api_key=api_key)
            # Connect to existing index. If host provided (serverless), use it.
            try:
                if host:
                    self._index = self._pc.Index(host=host)
                else:
                    self._index = self._pc.Index(index_name)
            except Exception as e:
                raise RuntimeError(f"Failed to initialize Pinecone index '{index_name}'. Ensure it exists and PINECONE_HOST (if serverless) is correct: {e}")
            # Target index dimension: if provided via env, use it to fit vectors
            try:
                self._index_dim = int(os.getenv("PINECONE_DIM", "0")) or self.dim
            except Exception:
                self._index_dim = self.dim

    @staticmethod
    def _to_unit(vec: np.ndarray) -> np.ndarray:
        n = np.linalg.norm(vec) + 1e-12
        return (vec / n).astype("float32")

    def _faiss_add(self, scope: str, ids: List[str], vectors: List[List[float]]):
        vecs = np.array([self._to_unit(np.array(v, dtype="float32")) for v in vectors], dtype="float32")
        if scope == "title":
            self._index_title.add(vecs)  # type: ignore
            self._ids_title.extend(ids)
        else:
            self._index_summary.add(vecs)  # type: ignore
            self._ids_summary.extend(ids)

    def _fallback_add(self, scope: str, ids: List[str], vectors: List[List[float]]):
        arrs = [self._to_unit(np.array(v, dtype="float32")) for v in vectors]
        if scope == "title":
            self._ids_title.extend(ids)
            self._vecs_title.extend(arrs)
        else:
            self._ids_summary.extend(ids)
            self._vecs_summary.extend(arrs)

    def upsert(self, scope: str, id: str, vector: List[float]):
        # Pinecone path
        if self.use_pinecone:
            namespace = "title" if scope == "title" else "summary"
            values = vector
            # Fit vector to index dimension if necessary
            if hasattr(self, "_index_dim") and self._index_dim:
                if len(values) < self._index_dim:
                    values = [*values, *([0.0] * (self._index_dim - len(values)))]
                elif len(values) > self._index_dim:
                    values = values[: self._index_dim]
            self._index.upsert(vectors=[{"id": id, "values": values}], namespace=namespace)
            return
        # FAISS / fallback path
        if self.use_faiss:
            self._faiss_add(scope, [id], [vector])
        else:
            self._fallback_add(scope, [id], [vector])

    def bulk_load(self, scope: str, items: List[Tuple[str, List[float]]]):
        ids = [i for i, _ in items]
        vecs = [v for _, v in items]
        if not ids:
            return
        if self.use_pinecone:
            namespace = "title" if scope == "title" else "summary"
            vecs = []
            tgt = getattr(self, "_index_dim", None)
            for i, v in items:
                values = v
                if tgt:
                    if len(values) < tgt:
                        values = [*values, *([0.0] * (tgt - len(values)))]
                    elif len(values) > tgt:
                        values = values[:tgt]
                vecs.append({"id": i, "values": values})
            self._index.upsert(vectors=vecs, namespace=namespace)
            return
        if self.use_faiss:
            self._faiss_add(scope, ids, vecs)
        else:
            self._fallback_add(scope, ids, vecs)

    def search(self, scope: str, query_vec: List[float], k: int = 10) -> List[Tuple[str, float]]:
        if self.use_pinecone:
            namespace = "title" if scope == "title" else "summary"
            qv = query_vec
            tgt = getattr(self, "_index_dim", None)
            if tgt:
                if len(qv) < tgt:
                    qv = [*qv, *([0.0] * (tgt - len(qv)))]
                elif len(qv) > tgt:
                    qv = qv[:tgt]
            res = self._index.query(vector=qv, top_k=k, include_values=False, namespace=namespace)
            matches = getattr(res, "matches", []) or res.get("matches", [])  # supports different client returns
            out: List[Tuple[str, float]] = []
            for m in matches:
                mid = getattr(m, "id", None) or (m.get("id") if isinstance(m, dict) else None)
                score = getattr(m, "score", None) or (m.get("score") if isinstance(m, dict) else None)
                if mid is not None and score is not None:
                    out.append((str(mid), float(score)))
            return out
        # Local FAISS / cosine fallback
        q = self._to_unit(np.array(query_vec, dtype="float32")).reshape(1, -1)
        if scope == "title":
            ids, vecs = self._ids_title, self._vecs_title
            index = self._index_title
        else:
            ids, vecs = self._ids_summary, self._vecs_summary
            index = self._index_summary
        if self.use_faiss and index is not None:
            D, I = index.search(q, min(k, len(ids)))  # type: ignore
            return [(ids[i], float(D[0][j])) for j, i in enumerate(I[0]) if 0 <= i < len(ids)]
        if not ids:
            return []
        mat = np.stack(vecs, axis=0)
        sims = mat @ q.T
        sims = sims.reshape(-1)
        topk_idx = np.argsort(-sims)[:k]
        return [(ids[i], float(sims[i])) for i in topk_idx]

    def delete(self, id: str):
        # Pinecone deletion for both namespaces
        if self.use_pinecone:
            try:
                self._index.delete(ids=[id], namespace="title")
            except Exception:
                pass
            try:
                self._index.delete(ids=[id], namespace="summary")
            except Exception:
                pass
            return
        # Best-effort local deletion (non-FAISS path keeps vectors in memory)
        if id in self._ids_title:
            idxs = [i for i, x in enumerate(self._ids_title) if x == id]
            for i in reversed(idxs):
                del self._ids_title[i]
                if i < len(self._vecs_title):
                    del self._vecs_title[i]
        if id in self._ids_summary:
            idxs = [i for i, x in enumerate(self._ids_summary) if x == id]
            for i in reversed(idxs):
                del self._ids_summary[i]
                if i < len(self._vecs_summary):
                    del self._vecs_summary[i]

# Global store singleton
_store: Optional[VectorStore] = None


def get_store(dim: int) -> VectorStore:
    global _store
    if _store is None:
        _store = VectorStore(dim)
    return _store
