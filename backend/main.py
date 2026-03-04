"""
FastAPI 后端入口

提供 REST + SSE API，供 React 前端调用。
集成现有 TutorAgent、ProgressTracker、Orchestrator。
"""

import sys
import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import plans, session, chat, upload, search, studio, notes, resource

app = FastAPI(title="XLearning API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(plans.router, prefix="/api")
app.include_router(session.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(upload.router, prefix="/api")
app.include_router(search.router, prefix="/api")
app.include_router(studio.router, prefix="/api")
app.include_router(notes.router, prefix="/api")
app.include_router(resource.router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok"}
