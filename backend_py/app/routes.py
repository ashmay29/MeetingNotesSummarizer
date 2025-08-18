import os
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from bson import ObjectId
from typing import Optional, List
from .db import db
from .services.summarizer import summarize
from .services.mailer import send_email
from .services.embeddings import embed_texts
from .services.vector_store import get_store
import markdown as md
from pymongo import ReturnDocument

router = APIRouter()

COLLECTION = "meetings"


def oid(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid id")


@router.get("/")
async def list_meetings():
    items = []
    async for d in db()[COLLECTION].find().sort("createdAt", -1).limit(100):
        d["_id"] = str(d["_id"])  # ensure stringified id for frontend
        items.append(d)
    return items


@router.get("/search")
async def semantic_search(q: str, scope: str = "both", limit: int = 10):
    scope = scope.lower()
    if scope not in {"title", "summary", "both"}:
        raise HTTPException(status_code=400, detail="Invalid scope")
    # Embed query
    try:
        q_emb = embed_texts([q or " "])[0]
    except Exception as e:
        raise HTTPException(status_code=503, detail="Embeddings not configured. Set GOOGLE_API_KEY in backend .env.")
    dim = len(q_emb) if isinstance(q_emb, list) else 768
    store = get_store(dim)
    results: List[tuple[str, float]] = []
    if scope in ("title", "both"):
        results.extend(store.search("title", q_emb, k=limit))
    if scope in ("summary", "both"):
        results.extend(store.search("summary", q_emb, k=limit))
    # Merge by id taking max score
    agg: dict[str, float] = {}
    for mid, score in results:
        agg[mid] = max(score, agg.get(mid, -1e9))
    # Sort by score desc
    ranked = sorted(agg.items(), key=lambda x: -x[1])[:limit]
    ids = [oid(i) for i, _ in ranked]
    if not ids:
        return []
    # Fetch docs
    items = []
    async for d in db()[COLLECTION].find({"_id": {"$in": ids}}):
        d["_id"] = str(d["_id"]) 
        items.append(d)
    # Maintain ranking order
    order = {i: idx for idx, (i, _) in enumerate(ranked)}
    items.sort(key=lambda d: order.get(d["_id"], 1e9))
    return items


@router.get("/{id}")
async def get_meeting(id: str):
    d = await db()[COLLECTION].find_one({"_id": oid(id)})
    if not d:
        raise HTTPException(status_code=404, detail="Not found")
    d["_id"] = str(d["_id"])
    return d


@router.post("/summarize")
async def create_summary(
    title: Optional[str] = Form(None),
    instructions: Optional[str] = Form(None),
    text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
):
    transcript_text = text or ""
    if not transcript_text and file is not None:
        # Best-effort assume text/plain
        b = await file.read()
        transcript_text = b.decode("utf-8", errors="ignore")

    if not transcript_text.strip():
        raise HTTPException(status_code=400, detail="No transcript text provided")

    s = summarize(transcript_text, instructions)
    from datetime import datetime

    # Compute embeddings for title and summary (best-effort)
    title_emb = summary_emb = None
    try:
        embs = embed_texts([title or "", s or ""])  # may raise if GOOGLE_API_KEY missing
        title_emb, summary_emb = embs[0], embs[1]
    except Exception:
        # Skip embeddings silently; search will be unavailable until configured
        pass

    doc = {
        "title": title,
        "transcriptText": transcript_text,
        "instructions": instructions,
        "summary": s,
        **({"titleEmbedding": title_emb} if title_emb is not None else {}),
        **({"summaryEmbedding": summary_emb} if summary_emb is not None else {}),
        "recipients": [],
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow(),
    }
    result = await db()[COLLECTION].insert_one(doc)
    saved = await db()[COLLECTION].find_one({"_id": result.inserted_id})
    saved["_id"] = str(saved["_id"])
    # Upsert into vector store if embeddings computed
    if isinstance(summary_emb, list) and isinstance(title_emb, list):
        dim = len(summary_emb) or len(title_emb)
        store = get_store(dim or 768)
        store.upsert("title", saved["_id"], title_emb)
        store.upsert("summary", saved["_id"], summary_emb)
    return saved


@router.put("/{id}")
async def update_meeting(id: str, body: dict):
    allowed = {k: v for k, v in body.items() if k in {"title", "summary", "instructions"}}
    if not allowed:
        return await get_meeting(id)
    from datetime import datetime

    allowed["updatedAt"] = datetime.utcnow()
    # If title or summary updated, recompute embeddings
    if any(k in allowed for k in ("title", "summary")):
        # fetch original to know final values
        current = await db()[COLLECTION].find_one({"_id": oid(id)})
        if not current:
            raise HTTPException(status_code=404, detail="Not found")
        new_title = allowed.get("title", current.get("title") or "")
        new_summary = allowed.get("summary", current.get("summary") or "")
        try:
            t_emb, s_emb = embed_texts([new_title, new_summary])
            allowed["titleEmbedding"] = t_emb
            allowed["summaryEmbedding"] = s_emb
        except Exception:
            # Leave embeddings unchanged if unavailable
            pass

    res = await db()[COLLECTION].find_one_and_update(
        {"_id": oid(id)}, {"$set": allowed}, return_document=ReturnDocument.AFTER
    )
    if not res:
        raise HTTPException(status_code=404, detail="Not found")
    res["_id"] = str(res["_id"])
    # Upsert vectors if present
    if isinstance(allowed.get("summaryEmbedding"), list) or isinstance(allowed.get("titleEmbedding"), list):
        dim = len((allowed.get("summaryEmbedding") or allowed.get("titleEmbedding") or [])) or 768
        store = get_store(dim)
        if "titleEmbedding" in allowed and isinstance(allowed["titleEmbedding"], list):
            store.upsert("title", res["_id"], allowed["titleEmbedding"]) 
        if "summaryEmbedding" in allowed and isinstance(allowed["summaryEmbedding"], list):
            store.upsert("summary", res["_id"], allowed["summaryEmbedding"]) 
    return res


@router.post("/{id}/email")
async def email_summary(id: str, body: dict):
    to = body.get("to")
    subject = body.get("subject")
    if not isinstance(to, list) or not to:
        raise HTTPException(status_code=400, detail="Recipients required")

    item = await db()[COLLECTION].find_one({"_id": oid(id)})
    if not item:
        raise HTTPException(status_code=404, detail="Not found")

    subj = subject or item.get("title") or "Meeting Summary"
    provided_html = body.get("html")
    if provided_html and isinstance(provided_html, str) and provided_html.strip():
        html = provided_html
    else:
        # Convert Markdown summary to HTML for styled emails
        summary_md = item.get("summary", "")
        summary_html = md.markdown(summary_md, extensions=["extra", "sane_lists"])
        html = (
            f"<div style='font-family:Inter,Segoe UI,Arial,sans-serif;line-height:1.6;color:#111827'>"
            f"<h2 style='margin:0 0 12px;font-size:20px'>{subj}</h2>"
            f"<div>{summary_html}</div>"
            f"</div>"
        )

    try:
        info = await send_email(to=to, subject=subj, text=item.get("summary", ""), html=html)
        # Update recipients history
        merged = sorted(list(set([*(item.get("recipients", [])), *to])))
        await db()[COLLECTION].update_one({"_id": item["_id"]}, {"$set": {"recipients": merged}})
        return {"ok": True, "messageId": info.get("messageId")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {e}")


