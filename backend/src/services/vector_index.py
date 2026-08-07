"""本地向量索引：无 LLM 时用确定性哈希向量；优先 FAISS，否则 numpy 余弦检索。"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import numpy as np
from pycore.core import get_logger

from src.core.config import BACKEND_ROOT, settings

logger = get_logger()

DIM = 256
_TOKEN_RE = re.compile(r"[\w\u4e00-\u9fff]+", re.UNICODE)

try:
    import faiss  # type: ignore

    _HAS_FAISS = True
except Exception:  # noqa: BLE001
    faiss = None
    _HAS_FAISS = False


def _index_dir() -> Path:
    path = Path(settings.vector_index_dir)
    if not path.is_absolute():
        path = BACKEND_ROOT / path
    path.mkdir(parents=True, exist_ok=True)
    return path


def _tokenize_for_embed(text: str) -> list[str]:
    """中英混合分词：英文/数字整词 + 汉字单字/双字，避免整句当成一个 token。"""
    text = (text or "").lower()
    tokens: list[str] = []
    for m in re.finditer(r"[a-z0-9]+|[\u4e00-\u9fff]+", text):
        piece = m.group(0)
        if re.fullmatch(r"[a-z0-9]+", piece):
            tokens.append(piece)
            continue
        # 汉字：单字 + 双字（重叠）
        chars = list(piece)
        tokens.extend(chars)
        tokens.extend(chars[i] + chars[i + 1] for i in range(len(chars) - 1))
    return tokens


def embed_text(text: str) -> np.ndarray:
    """确定性本地 embedding（无需 API Key），便于演示发布/检索闭环。"""
    tokens = _tokenize_for_embed(text)
    vec = np.zeros(DIM, dtype=np.float32)
    if not tokens:
        return vec
    for token in tokens:
        digest = hashlib.md5(token.encode("utf-8")).digest()
        idx = int.from_bytes(digest[:4], "little") % DIM
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        # 双字权重大于单字，提升「住宿/深圳」等短语命中
        weight = 1.5 if len(token) >= 2 and not token.isascii() else 1.0
        vec[idx] += sign * weight
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec /= norm
    return vec


class VectorIndex:
    """按 chunk_id 维护向量；发布写入、下线删除、检索 TopK。"""

    def __init__(self) -> None:
        self._meta_path = _index_dir() / "knowledge_meta.json"
        self._vec_path = _index_dir() / "knowledge_vectors.npy"
        self._ids: list[str] = []
        self._meta: dict[str, dict] = {}
        self._matrix: np.ndarray = np.zeros((0, DIM), dtype=np.float32)
        self._load()

    def _load(self) -> None:
        if self._meta_path.exists() and self._vec_path.exists():
            raw = json.loads(self._meta_path.read_text(encoding="utf-8"))
            self._ids = list(raw.get("ids", []))
            self._meta = dict(raw.get("meta", {}))
            self._matrix = np.load(self._vec_path)
            if len(self._ids) != len(self._matrix):
                logger.warning("Vector index size mismatch; resetting")
                self._ids, self._meta = [], {}
                self._matrix = np.zeros((0, DIM), dtype=np.float32)
        else:
            self._ids, self._meta = [], {}
            self._matrix = np.zeros((0, DIM), dtype=np.float32)

    def _persist(self) -> None:
        self._meta_path.write_text(
            json.dumps({"ids": self._ids, "meta": self._meta}, ensure_ascii=False),
            encoding="utf-8",
        )
        np.save(self._vec_path, self._matrix)

    def upsert_chunks(self, items: list[tuple[str, str, dict]]) -> None:
        """items: (chunk_id, text, meta)."""
        for chunk_id, text, meta in items:
            vec = embed_text(text)
            if chunk_id in self._ids:
                idx = self._ids.index(chunk_id)
                self._matrix[idx] = vec
                self._meta[chunk_id] = meta
            else:
                self._ids.append(chunk_id)
                self._meta[chunk_id] = meta
                if self._matrix.size == 0:
                    self._matrix = vec.reshape(1, -1)
                else:
                    self._matrix = np.vstack([self._matrix, vec.reshape(1, -1)])
        self._persist()

    def remove_document(self, document_id: str) -> None:
        keep_ids: list[str] = []
        keep_rows: list[np.ndarray] = []
        keep_meta: dict[str, dict] = {}
        for i, chunk_id in enumerate(self._ids):
            meta = self._meta.get(chunk_id, {})
            if meta.get("document_id") == document_id:
                continue
            keep_ids.append(chunk_id)
            keep_rows.append(self._matrix[i])
            keep_meta[chunk_id] = meta
        self._ids = keep_ids
        self._meta = keep_meta
        self._matrix = (
            np.vstack(keep_rows).astype(np.float32)
            if keep_rows
            else np.zeros((0, DIM), dtype=np.float32)
        )
        self._persist()

    def search(self, query: str, top_k: int = 5) -> list[tuple[str, float, dict]]:
        if not self._ids:
            return []
        q = embed_text(query)
        if _HAS_FAISS and len(self._ids) > 0:
            index = faiss.IndexFlatIP(DIM)
            index.add(self._matrix.astype(np.float32))
            scores, indices = index.search(q.reshape(1, -1), min(top_k, len(self._ids)))
            hits: list[tuple[str, float, dict]] = []
            for score, idx in zip(scores[0], indices[0], strict=False):
                if idx < 0:
                    continue
                chunk_id = self._ids[int(idx)]
                hits.append((chunk_id, float(score), self._meta.get(chunk_id, {})))
            return hits

        scores = self._matrix @ q
        order = np.argsort(-scores)[:top_k]
        return [
            (self._ids[int(i)], float(scores[int(i)]), self._meta.get(self._ids[int(i)], {}))
            for i in order
        ]

    @property
    def backend_name(self) -> str:
        return "faiss" if _HAS_FAISS else "numpy"


_vector_index: VectorIndex | None = None


def get_vector_index() -> VectorIndex:
    global _vector_index
    if _vector_index is None:
        _vector_index = VectorIndex()
    return _vector_index
