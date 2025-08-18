import os
import google.generativeai as genai
from typing import List
from dotenv import load_dotenv
load_dotenv()

# Initialize Gemini client lazily
_genai_configured = False


def _ensure_config():
    global _genai_configured
    if _genai_configured:
        return
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY not set for embeddings")
    genai.configure(api_key=api_key)
    _genai_configured = True


def embed_texts(texts: List[str]) -> List[List[float]]:
    """Return embeddings for a list of texts using Gemini embeddings (text-embedding-004).
    Calls the API per item to avoid SDK differences across versions.
    """
    _ensure_config()
    out: List[List[float]] = []
    model = "models/text-embedding-004" if "text-embedding-004" not in "models/text-embedding-004" else "text-embedding-004"
    for t in texts:
        content = t if (isinstance(t, str) and t.strip()) else " "
        resp = genai.embed_content(model=model, content=content)
        # Expect {'embedding': [...]} across versions
        vec = resp.get("embedding") if isinstance(resp, dict) else None
        if not vec and hasattr(resp, "embedding"):
            vec = getattr(resp, "embedding")
        if not vec:
            raise RuntimeError("Failed to obtain embedding from Gemini response")
        out.append(list(vec))
    return out
