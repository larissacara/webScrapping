#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG index builder and query utilities for SENAC cursos JSON/PDF data.

Creates a FAISS index with sentence embeddings and stores per-snippet metadata
including articleId, nomeCurso (title), campo (tipoName) and source field.
"""

from __future__ import annotations

import json
import os
import re
import uuid
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np
from sentence_transformers import SentenceTransformer

try:
    import faiss  # type: ignore
except Exception as exc:  # pragma: no cover
    raise RuntimeError(
        "faiss-cpu is required. Please install dependencies from requirements.txt"
    ) from exc


# ----------------------------- Data structures ----------------------------- #

@dataclass
class Snippet:
    text: str
    metadata: Dict[str, str]


# ----------------------------- Text utilities ------------------------------ #

_HTML_TAG_RE = re.compile(r"<[^>]+>")


def strip_html(value: str) -> str:
    if not value:
        return ""
    value = _HTML_TAG_RE.sub("", value)
    value = value.replace("\u00a0", " ")
    value = re.sub(r"\s+", " ", value).strip()
    return value


def join_non_empty(parts: Iterable[str], sep: str = "\n\n") -> str:
    return sep.join([p for p in (s.strip() for s in parts) if p])


def simple_chunk(text: str, max_chars: int = 900, overlap: int = 150) -> List[str]:
    """Greedy chunking by characters with overlap to keep context."""
    text = text.strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]
    chunks: List[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + max_chars)
        # try to cut on sentence boundary
        cut = text.rfind(". ", start, end)
        if cut == -1 or cut <= start + 0.5 * max_chars:
            cut = end
        chunk = text[start:cut].strip()
        if chunk:
            chunks.append(chunk)
        start = max(cut - overlap, start + 1)
    return chunks


# ----------------------------- Index handling ------------------------------ #

DEFAULT_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def _load_model(model_name: str = DEFAULT_MODEL_NAME) -> SentenceTransformer:
    return SentenceTransformer(model_name)


def _embed_texts(model: SentenceTransformer, texts: List[str]) -> np.ndarray:
    embeddings = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
    return np.asarray(embeddings, dtype="float32")


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _metadata_path(index_dir: str) -> str:
    return os.path.join(index_dir, "metadata.jsonl")


def _faiss_index_path(index_dir: str) -> str:
    return os.path.join(index_dir, "index.faiss")


def _dim_for_model(model: SentenceTransformer) -> int:
    # Encode a small probe to discover dimension
    vec = model.encode(["probe"], show_progress_bar=False, normalize_embeddings=True)
    return int(vec.shape[1])


def build_index(
    json_path: str,
    index_dir: str = "rag_index",
    model_name: str = DEFAULT_MODEL_NAME,
    campo_override: Optional[str] = None,
) -> None:
    """Build a FAISS index from cursos JSON.

    - json_path: path to cursos_filtrados.json
    - index_dir: output directory for FAISS index and metadata.jsonl
    - model_name: sentence-transformers model
    - campo_override: if provided, forces metadata "campo" to this value
    """

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    cursos: List[Dict] = data.get("cursos", [])
    if not cursos:
        raise ValueError("JSON does not contain key 'cursos' or it's empty")

    model = _load_model(model_name)
    dim = _dim_for_model(model)

    # Use IndexFlatIP because vectors are normalized
    index = faiss.IndexFlatIP(dim)

    snippets: List[Snippet] = []

    for course in cursos:
        article_id = str(course.get("articleId", ""))
        title = str(course.get("title") or course.get("toDisplay", {}).get("title") or "")
        to_display = course.get("toDisplay", {}) or {}
        tipo_name = str(to_display.get("tipoName") or "")
        campo_value = campo_override or tipo_name or ""

        objetivo = strip_html(course.get("objetivoComercial", ""))
        como = strip_html(course.get("comoVouAprender", ""))
        requisitos = strip_html(course.get("possoFazerEsseCurso", ""))
        o_que = strip_html(course.get("oqueVouAprender", ""))

        fields: List[Tuple[str, str]] = [
            ("objetivo", objetivo),
            ("metodologia", como),
            ("requisitos", requisitos),
            ("conteudo", o_que),
        ]

        for field_name, field_text in fields:
            if not field_text:
                continue
            for chunk in simple_chunk(field_text):
                meta = {
                    "id": str(uuid.uuid4()),
                    "articleId": article_id,
                    "nomeCurso": title,
                    "campo": campo_value,
                    "field": field_name,
                }
                snippets.append(Snippet(text=chunk, metadata=meta))

    if not snippets:
        raise ValueError("No textual content found to index")

    texts = [s.text for s in snippets]
    vectors = _embed_texts(model, texts)
    index.add(vectors)

    _ensure_dir(index_dir)
    faiss.write_index(index, _faiss_index_path(index_dir))

    # Save metadata aligned by vector order
    with open(_metadata_path(index_dir), "w", encoding="utf-8") as mf:
        for s in snippets:
            rec = {**s.metadata, "text": s.text}
            mf.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _load_index(index_dir: str, model_name: str) -> Tuple[faiss.Index, SentenceTransformer, List[Dict[str, str]]]:
    index_path = _faiss_index_path(index_dir)
    meta_path = _metadata_path(index_dir)
    if not os.path.exists(index_path) or not os.path.exists(meta_path):
        raise FileNotFoundError(f"Index not found in {index_dir}. Build it first.")

    index = faiss.read_index(index_path)
    model = _load_model(model_name)

    metadata: List[Dict[str, str]] = []
    with open(meta_path, "r", encoding="utf-8") as mf:
        for line in mf:
            if line.strip():
                metadata.append(json.loads(line))

    return index, model, metadata


def query_index(
    query: str,
    index_dir: str = "rag_index",
    model_name: str = DEFAULT_MODEL_NAME,
    top_k: int = 5,
) -> List[Dict[str, str]]:
    """Query the FAISS index and return top-k snippets with metadata."""
    index, model, metadata = _load_index(index_dir, model_name)
    q_vec = _embed_texts(model, [query])
    scores, indices = index.search(q_vec, min(top_k, len(metadata)))
    results: List[Dict[str, str]] = []
    for score, idx in zip(scores[0].tolist(), indices[0].tolist()):
        if idx < 0 or idx >= len(metadata):
            continue
        rec = metadata[idx].copy()
        rec["score"] = float(score)
        results.append(rec)
    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build and query RAG index for SENAC cursos")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_build = sub.add_parser("build", help="Build index from JSON")
    p_build.add_argument("--json", default="cursos_filtrados.json")
    p_build.add_argument("--out", default="rag_index")
    p_build.add_argument("--model", default=DEFAULT_MODEL_NAME)
    p_build.add_argument("--campo", default=None)

    p_query = sub.add_parser("query", help="Query existing index")
    p_query.add_argument("query")
    p_query.add_argument("--index", default="rag_index")
    p_query.add_argument("--model", default=DEFAULT_MODEL_NAME)
    p_query.add_argument("--k", type=int, default=5)

    args = parser.parse_args()
    if args.cmd == "build":
        build_index(args.json, args.out, args.model, args.campo)
        print(f"Index built at {args.out}")
    else:
        hits = query_index(args.query, args.index, args.model, args.k)
        for h in hits:
            print(json.dumps(h, ensure_ascii=False))


