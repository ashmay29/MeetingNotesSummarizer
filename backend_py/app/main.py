import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import router
from .db import connect_db, close_db

load_dotenv()

PORT = int(os.getenv("PORT", "4000"))
CORS_ORIGIN = os.getenv("CORS_ORIGIN", "http://localhost:3000")

app = FastAPI(title="meeting-notes-summarizer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in CORS_ORIGIN.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def on_startup():
    await connect_db()

@app.on_event("shutdown")
async def on_shutdown():
    await close_db()

@app.get("/api/health")
async def health():
    from datetime import datetime
    return {"ok": True, "service": "meeting-notes-summarizer", "time": datetime.utcnow().isoformat()}

app.include_router(router, prefix="/api/meetings")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=PORT, reload=True)
# 
