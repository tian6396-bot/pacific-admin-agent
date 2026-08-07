"""知识解析管线：提取正文、切分 Chunk、标记低置信。"""

from __future__ import annotations

import re
import uuid
from pathlib import Path

from pycore.core import get_logger

from src.db.models import KnowledgeChunk

logger = get_logger()

LOW_CONFIDENCE = 0.7


def extract_text_from_pdf(file_path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("缺少 pypdf，请安装 backend/requirements.txt") from exc

    reader = PdfReader(str(file_path))
    parts: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        parts.append(text.strip())
    joined = "\n".join(p for p in parts if p)
    if not joined.strip():
        raise ValueError("未能从 PDF 提取到文本，请检查文件是否为扫描件")
    return joined


def split_chunks(text: str, *, max_len: int = 180) -> list[tuple[str, float]]:
    """按段落/句号粗切；含 OCR 疑似词或过短片段标低置信。"""
    blocks = [b.strip() for b in re.split(r"\n{2,}", text) if b.strip()]
    if not blocks:
        blocks = [text.strip()]

    pieces: list[str] = []
    for block in blocks:
        if len(block) <= max_len:
            pieces.append(block)
            continue
        sentences = re.split(r"(?<=[。！？；;.!?])", block)
        buf = ""
        for sent in sentences:
            sent = sent.strip()
            if not sent:
                continue
            if len(buf) + len(sent) <= max_len:
                buf = f"{buf}{sent}"
            else:
                if buf:
                    pieces.append(buf)
                buf = sent
        if buf:
            pieces.append(buf)

    results: list[tuple[str, float]] = []
    for piece in pieces:
        conf = 0.92
        if len(piece) < 12:
            conf = 0.55
        if any(mark in piece for mark in ("�", "疑似", "OCR", "□", "??")):
            conf = min(conf, 0.6)
        results.append((piece, conf))
    return results or [(text.strip()[:max_len], 0.8)]


def build_chunks(document_id: str, text: str) -> list[KnowledgeChunk]:
    chunks: list[KnowledgeChunk] = []
    for idx, (piece, conf) in enumerate(split_chunks(text)):
        chunks.append(
            KnowledgeChunk(
                id=str(uuid.uuid4()),
                document_id=document_id,
                index=idx + 1,
                text=piece,
                confidence=conf,
                needs_review=conf < LOW_CONFIDENCE,
            )
        )
    logger.info("Chunks built", document_id=document_id, count=len(chunks))
    return chunks
