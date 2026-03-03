"""
文件上传端点

支持：
- PDF 文件上传（multipart/form-data）
- GitHub URL 粘贴（JSON body）

上传后异步进行 parsing → chunking → ready 状态流转。
"""

import uuid
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from pydantic import BaseModel

from backend.store import get_session_store

logger = logging.getLogger(__name__)
router = APIRouter(tags=["upload"])

UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class UrlUploadRequest(BaseModel):
    planId: str
    url: str  # GitHub URL 或其他网页 URL


class UploadResponse(BaseModel):
    id: str
    name: str
    type: str
    status: str
    addedAt: str


def _detect_type(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        return "pdf"
    return "other"


async def _process_pdf(material_id: str, plan_id: str, file_path: Path, filename: str):
    """后台任务：PDF 解析 → chunking → ready，更新 store 状态"""
    store = get_session_store(plan_id)
    materials: list = store.setdefault("materials", [])

    def _set_status(status: str):
        for m in materials:
            if m["id"] == material_id:
                m["status"] = status
                break

    try:
        _set_status("parsing")
        await asyncio.sleep(0.5)  # 模拟解析延迟

        # 尝试用 RAGEngine 真实解析
        try:
            from src.rag import RAGEngine
            rag = RAGEngine(collection_name=f"plan_{plan_id}")
            content = file_path.read_bytes()
            # 用 PyMuPDF 或 pdfplumber 提取文本
            text = _extract_pdf_text(content)
            if text:
                _set_status("chunking")
                await asyncio.sleep(0.3)
                rag.add_document(
                    content=text,
                    metadata={"source": filename, "plan_id": plan_id, "material_id": material_id},
                    doc_id=material_id,
                )
        except Exception as e:
            logger.warning(f"RAG ingest failed for {filename}: {e}")

        _set_status("ready")
    except Exception as e:
        logger.error(f"PDF processing failed: {e}")
        _set_status("error")


def _extract_pdf_text(content: bytes) -> str:
    """提取 PDF 文本，优先 PyMuPDF，降级 pdfplumber"""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(stream=content, filetype="pdf")
        return "\n".join(page.get_text() for page in doc)
    except ImportError:
        pass
    try:
        import pdfplumber, io
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            return "\n".join(p.extract_text() or "" for p in pdf.pages)
    except ImportError:
        pass
    return ""


async def _process_url(material_id: str, plan_id: str, url: str):
    """后台任务：抓取 URL 内容 → chunking → ready"""
    store = get_session_store(plan_id)
    materials: list = store.setdefault("materials", [])

    def _set_status(status: str):
        for m in materials:
            if m["id"] == material_id:
                m["status"] = status
                break

    try:
        _set_status("parsing")
        await asyncio.sleep(1.0)
        # TODO: 接入 GitHub README 抓取 / 网页爬取
        _set_status("ready")
    except Exception as e:
        logger.error(f"URL processing failed: {e}")
        _set_status("error")


@router.post("/upload", response_model=UploadResponse, status_code=201)
async def upload_file(
    background_tasks: BackgroundTasks,
    plan_id: str = "",
    file: UploadFile = File(...),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename")

    material_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat() + "Z"
    mat_type = _detect_type(file.filename)

    # 保存文件
    save_path = UPLOAD_DIR / f"{material_id}_{file.filename}"
    content = await file.read()
    save_path.write_bytes(content)

    # 写入 store
    store = get_session_store(plan_id)
    store.setdefault("materials", []).append({
        "id": material_id,
        "name": file.filename,
        "type": mat_type,
        "status": "parsing",
        "addedAt": now,
    })

    # 后台处理
    background_tasks.add_task(_process_pdf, material_id, plan_id, save_path, file.filename)

    return UploadResponse(
        id=material_id,
        name=file.filename,
        type=mat_type,
        status="parsing",
        addedAt=now,
    )


@router.post("/upload/url", response_model=UploadResponse, status_code=201)
async def upload_url(body: UrlUploadRequest, background_tasks: BackgroundTasks):
    material_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat() + "Z"

    # 从 URL 推断名称
    name = body.url.split("/")[-1] or body.url[:40]
    mat_type = "github" if "github.com" in body.url else "web"

    store = get_session_store(body.planId)
    store.setdefault("materials", []).append({
        "id": material_id,
        "name": name,
        "type": mat_type,
        "url": body.url,
        "status": "parsing",
        "addedAt": now,
    })

    background_tasks.add_task(_process_url, material_id, body.planId, body.url)

    return UploadResponse(
        id=material_id,
        name=name,
        type=mat_type,
        status="parsing",
        addedAt=now,
    )


@router.get("/material/{material_id}/status")
async def get_material_status(material_id: str, plan_id: str = ""):
    """轮询材料处理状态"""
    store = get_session_store(plan_id)
    for m in store.get("materials", []):
        if m["id"] == material_id:
            return {"id": material_id, "status": m["status"]}
    raise HTTPException(status_code=404, detail="Material not found")


@router.get("/material/{material_id}/summary")
async def get_material_summary(material_id: str, plan_id: str = ""):
    """获取材料摘要，点击材料时插入对话区"""
    store = get_session_store(plan_id)
    for m in store.get("materials", []):
        if m["id"] == material_id:
            name = m.get("name", "未知材料")
            return {
                "id": material_id,
                "name": name,
                "summary": f"📄 已加载材料：{name}。你可以向 AI 提问关于此材料的内容。",
            }
    raise HTTPException(status_code=404, detail="Material not found")


@router.delete("/material/{material_id}", status_code=204)
async def delete_material(material_id: str, plan_id: str = ""):
    """移除材料"""
    store = get_session_store(plan_id)
    materials = store.get("materials", [])
    store["materials"] = [m for m in materials if m["id"] != material_id]
