import os
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from bson import ObjectId
from typing import Optional, List
from .db import db
from .services.summarizer import summarize
from .services.mailer import send_email
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

    doc = {
        "title": title,
        "transcriptText": transcript_text,
        "instructions": instructions,
        "summary": s,
        "recipients": [],
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow(),
    }
    result = await db()[COLLECTION].insert_one(doc)
    saved = await db()[COLLECTION].find_one({"_id": result.inserted_id})
    saved["_id"] = str(saved["_id"])
    return saved


@router.put("/{id}")
async def update_meeting(id: str, body: dict):
    allowed = {k: v for k, v in body.items() if k in {"title", "summary", "instructions"}}
    if not allowed:
        return await get_meeting(id)
    from datetime import datetime

    allowed["updatedAt"] = datetime.utcnow()
    res = await db()[COLLECTION].find_one_and_update(
        {"_id": oid(id)}, {"$set": allowed}, return_document=ReturnDocument.AFTER
    )
    if not res:
        raise HTTPException(status_code=404, detail="Not found")
    res["_id"] = str(res["_id"])
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
    html = f"<div><h2>{subj}</h2><pre style=\"white-space:pre-wrap;font-family:inherit\">{item.get('summary','')}</pre></div>"

    try:
        info = await send_email(to=to, subject=subj, text=item.get("summary", ""), html=html)
        # Update recipients history
        merged = sorted(list(set([*(item.get("recipients", [])), *to])))
        await db()[COLLECTION].update_one({"_id": item["_id"]}, {"$set": {"recipients": merged}})
        return {"ok": True, "messageId": info.get("messageId")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {e}")
