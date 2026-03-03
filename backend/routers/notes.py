"""
笔记 CRUD 端点（Task 8 完整实现）
"""

import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter(tags=["notes"])

_notes: dict = {}


class NoteCreate(BaseModel):
    planId: str
    title: str
    content: str


class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None


class NoteResponse(BaseModel):
    id: str
    planId: str
    title: str
    content: str
    updatedAt: str


@router.post("/notes", response_model=NoteResponse, status_code=201)
async def create_note(body: NoteCreate):
    note_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat() + "Z"
    note = NoteResponse(id=note_id, planId=body.planId, title=body.title, content=body.content, updatedAt=now)
    _notes[note_id] = note.model_dump()
    return note


@router.put("/notes/{note_id}", response_model=NoteResponse)
async def update_note(note_id: str, body: NoteUpdate):
    if note_id not in _notes:
        raise HTTPException(status_code=404, detail="Note not found")
    note = _notes[note_id]
    if body.title is not None:
        note["title"] = body.title
    if body.content is not None:
        note["content"] = body.content
    note["updatedAt"] = datetime.utcnow().isoformat() + "Z"
    return note


@router.delete("/notes/{note_id}", status_code=204)
async def delete_note(note_id: str):
    if note_id not in _notes:
        raise HTTPException(status_code=404, detail="Note not found")
    del _notes[note_id]
