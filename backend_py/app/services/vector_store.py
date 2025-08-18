import os
from typing import List, Tuple, Optional, Dict
import numpy as np

try:
    import faiss  # type: ignore
    _has_faiss = True
except Exception:
    faiss = None  # type: ignore
    _has_faiss = False

_has_pinecone = False
try:
    # pinecone v2 client
    from pinecone import Pinecone, ServerlessSpec
    _has_pinecone = True
except Exception:
    Pinecone = None  # type: ignore
    ServerlessSpec = None  # type: ignore
    _has_pinecone = False

# Two separate indexes for title and summary scopes
class VectorStore:
    def __init__(self, dim: int):
        self.dim = dim
        self.backend = os.getenv("VECTOR_BACKEND", "faiss").lower()
        self.use_faiss = _has_faiss and self.backend == "faiss"
        self.use_pinecone = _has_pinecone and self.backend == "pinecone"
        # in-memory ids and vectors for fallback
        self._ids_title: List[str] = []
        self._vecs_title: List[np.ndarray] = []
        self._ids_summary: List[str] = []
        self._vecs_summary: List[np.ndarray] = []
        # FAISS init
        if self.use_faiss:
            self._index_title = faiss.IndexFlatIP(dim)
            self._index_summary = faiss.IndexFlatIP(dim)
        else:
            self._index_title = None
            self._index_summary = None

        # Pinecone init
        self._pc = None
        self._pc_index = None
        self._pc_index_name = None
        if self.use_pinecone:
            api_key = os.getenv("PINECONE_API_KEY")
            index_name = os.getenv("PINECONE_INDEX")
            cloud = os.getenv("PINECONE_CLOUD", "aws")  # for serverless spec
            region = os.getenv("PINECONE_REGION", "us-east-1")
            if not api_key or not index_name:
                # disable pinecone if not properly configured; fallback to memory
                self.use_pinecone = False
            else:
                self._pc = Pinecone(api_key=api_key)  # type: ignore
                self._pc_index_name = index_name
                # Create index if missing (serverless)
                try:
                    existing = {i.name for i in self._pc.list_indexes()}  # type: ignore
                except Exception:
                    existing = set()
                if index_name not in existing:
                    # Create with cosine metric to match our unit vector similarity
                    if ServerlessSpec is None:
                        raise RuntimeError("Pinecone ServerlessSpec unavailable; install pinecone-client >=2.x")
                    self._pc.create_index(  # type: ignore
                        name=index_name,
                        dimension=self.dim,
                        metric="cosine",
                        spec=ServerlessSpec(cloud=cloud, region=region),
                    )
                self._pc_index = self._pc.Index(index_name)  # type: ignore

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
        # simple approach: append; rebuild is handled by initial load. For true upsert we'd need id->pos mapping.
        if self.use_pinecone and self._pc_index is not None:
            try:
                vec = self._to_unit(np.array(vector, dtype="float32")).tolist()
                self._pc_index.upsert(vectors=[{"id": id, "values": vec}], namespace=scope)  # type: ignore
                return
            except Exception:
                # fallback to in-memory if pinecone fails
                pass
        if self.use_faiss:
            self._faiss_add(scope, [id], [vector])
        else:
            self._fallback_add(scope, [id], [vector])

    def bulk_load(self, scope: str, items: List[Tuple[str, List[float]]]):
        ids = [i for i, _ in items]
        vecs = [v for _, v in items]
        if not ids:
            return
        if self.use_pinecone and self._pc_index is not None:
            try:
                payload = []
                for i, v in zip(ids, vecs):
                    vec = self._to_unit(np.array(v, dtype="float32")).tolist()
                    payload.append({"id": i, "values": vec})
                # batch upserts
                for start in range(0, len(payload), 100):
                    batch = payload[start : start + 100]
                    self._pc_index.upsert(vectors=batch, namespace=scope)  # type: ignore
                return
            except Exception:
                pass
        if self.use_faiss:
            self._faiss_add(scope, ids, vecs)
        else:
            self._fallback_add(scope, ids, vecs)

    def search(self, scope: str, query_vec: List[float], k: int = 10) -> List[Tuple[str, float]]:
        q_vec = self._to_unit(np.array(query_vec, dtype="float32"))
        if self.use_pinecone and self._pc_index is not None:
            try:
                res = self._pc_index.query(  # type: ignore
                    vector=q_vec.tolist(),
                    top_k=k,
                    namespace=scope,
                    include_values=False,
                    include_metadata=False,
                )
                matches = getattr(res, "matches", []) or res.get("matches", []) if isinstance(res, dict) else []
                out: List[Tuple[str, float]] = []
                for m in matches:
                    mid = getattr(m, "id", None) or (m.get("id") if isinstance(m, dict) else None)
                    score = getattr(m, "score", None) or (m.get("score") if isinstance(m, dict) else None)
                    if mid is not None and score is not None:
                        out.append((str(mid), float(score)))
                return out
            except Exception:
                # fall back to local search
                pass

        q = q_vec.reshape(1, -1)
        if scope == "title":
            ids, vecs = self._ids_title, self._vecs_title
            index = self._index_title
        else:
            ids, vecs = self._ids_summary, self._vecs_summary
            index = self._index_summary
        if self.use_faiss and index is not None:
            D, I = index.search(q, min(k, len(ids)))  # type: ignore
            return [(ids[i], float(D[0][j])) for j, i in enumerate(I[0]) if 0 <= i < len(ids)]
        # fallback cosine
        if not ids:
            return []
        mat = np.stack(vecs, axis=0)  # [N, dim]
        sims = mat @ q.T  # [N,1]
        sims = sims.reshape(-1)
        topk_idx = np.argsort(-sims)[:k]
        return [(ids[i], float(sims[i])) for i in topk_idx]

# Global store singleton
_store: Optional[VectorStore] = None


def get_store(dim: int) -> VectorStore:
    global _store
    if _store is None:
        _store = VectorStore(dim)
    return _store
