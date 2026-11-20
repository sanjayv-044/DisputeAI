"""
DisputeAI Regulatory Retrieval Tools
Connects to ChromaDB for semantic search over official RBI circulars:
- RBI Customer Protection 2017 (Limiting Liability of Customers)
- RBI Integrated Ombudsman Scheme 2026
Provides self-healing automatic indexing from documents/processed/rbi_chunks.json.
"""

import json
import os
import re
from pathlib import Path
from typing import List, Dict, Any

# Ensure HuggingFace and ChromaDB cache stay inside workspace
ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = ROOT / "documents" / ".cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["XDG_CACHE_HOME"] = str(CACHE_DIR)
os.environ["CHROMA_CACHE_DIR"] = str(CACHE_DIR)

CHROMA_DIR = ROOT / "documents" / "chroma_db"
CHUNKS_FILE = ROOT / "documents" / "processed" / "rbi_chunks.json"

_collection = None
_embed_fn = None


def get_embedding_model():
    """Lazily load sentence-transformers model if local weights exist, else fast fallback."""
    global _embed_fn
    if _embed_fn is not None:
        return _embed_fn

    try:
        # Check if local model cache exists
        cache_dir = Path.home() / ".cache" / "huggingface" / "hub"
        has_local = any("MiniLM" in p.name for p in cache_dir.glob("*")) if cache_dir.exists() else False
        if has_local:
            from sentence_transformers import SentenceTransformer
            _embed_fn = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", local_files_only=True)
            return _embed_fn
    except Exception:
        pass

    _embed_fn = "FALLBACK"
    return _embed_fn


def get_collection():
    """Get or initialize ChromaDB collection with official RBI records."""
    global _collection
    if _collection is not None:
        return _collection

    import chromadb
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    collection = client.get_or_create_collection(
        name="rbi_regulations",
        metadata={"description": "RBI Customer Protection & Ombudsman Regulations"}
    )

    # If collection is empty, automatically index from processed chunks
    if collection.count() == 0 and CHUNKS_FILE.exists():
        try:
            with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
                records = json.load(f)

            ids = []
            documents = []
            metadatas = []

            for idx, r in enumerate(records):
                text = (r.get("text") or "").strip()
                if not text:
                    continue

                source = r.get("source", "RBI_Regulation.pdf")
                page = int(r.get("page_number", 1))
                chunk_id = r.get("chunk_id", f"chunk_{idx}")

                # Determine regulatory status
                status = "current"
                if "2017" in source and re.search(r"\bwithdrawn\b", text, re.I):
                    status = "historical"

                ids.append(chunk_id)
                documents.append(text)
                metadatas.append({
                    "source": source,
                    "page_number": page,
                    "document_status": status,
                    "document_scope": "customer_protection" if "Customer" in source else "ombudsman",
                    "chunk_type": "original_chunk"
                })

            if documents:
                collection.upsert(
                    ids=ids,
                    documents=documents,
                    metadatas=metadatas
                )
        except Exception as e:
            print(f"ChromaDB initialization notice: {e}")

    _collection = collection
    return _collection


def format_evidence(results: Dict[str, Any]) -> List[Dict[str, Any]]:
    evidence = []
    if not results or not results.get("documents"):
        return evidence

    docs = results["documents"][0] if results["documents"] else []
    metas = results["metadatas"][0] if results.get("metadatas") else []

    for i, document in enumerate(docs):
        metadata = metas[i] if i < len(metas) else {}
        evidence.append({
            "source": metadata.get("source", "RBI_Regulation.pdf"),
            "page": metadata.get("page_number", 1),
            "status": metadata.get("document_status", "current"),
            "scope": metadata.get("document_scope", "customer_protection"),
            "chunk_type": metadata.get("chunk_type", "original_chunk"),
            "text": document
        })

    return evidence


def fallback_text_search(question: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Deterministic keyword & semantic token similarity search over rbi_chunks.json."""
    if not CHUNKS_FILE.exists():
        return []

    with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
        records = json.load(f)

    keywords = set(re.findall(r"\w{3,}", question.lower()))
    scored = []

    for r in records:
        text = r.get("text", "")
        text_lower = text.lower()
        score = sum(3 for w in keywords if re.search(r"\b" + re.escape(w) + r"\b", text_lower))

        # Contextual boosts for liability paragraphs
        if "liability" in question.lower() and "limited liability" in text_lower:
            score += 10
        if "zero liability" in question.lower() and "zero liability" in text_lower:
            score += 12
        if "reversal" in question.lower() and "reversal" in text_lower:
            score += 8
        if "ombudsman" in question.lower() and "ombudsman" in text_lower:
            score += 8

        if score > 0:
            status = "current"
            if "2017" in r.get("source", "") and re.search(r"\bwithdrawn\b", text, re.I):
                status = "historical"
            scored.append((score, {
                "source": r.get("source"),
                "page": r.get("page_number"),
                "status": status,
                "scope": "customer_protection" if "Customer" in r.get("source", "") else "ombudsman",
                "chunk_type": "original_chunk",
                "text": text
            }))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored[:top_k]]


def search_regulations(question: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Search RBI circulars using ChromaDB or resilient keyword search."""
    try:
        col = get_collection()
        embedder = get_embedding_model()

        if embedder != "FALLBACK":
            embedding = embedder.encode(question).tolist()
            results = col.query(
                query_embeddings=[embedding],
                n_results=top_k
            )
            evidence = format_evidence(results)
            if evidence:
                return evidence
    except Exception:
        pass

    # Resilient fallback to local structured chunks
    return fallback_text_search(question, top_k=top_k)


def retrieve_by_status(status: str, top_k: int = 10) -> List[Dict[str, Any]]:
    try:
        col = get_collection()
        results = col.get(
            where={"document_status": status},
            limit=top_k,
            include=["documents", "metadatas"]
        )
        evidence = []
        for document, metadata in zip(results.get("documents", []), results.get("metadatas", [])):
            evidence.append({
                "source": metadata.get("source"),
                "page": metadata.get("page_number"),
                "status": metadata.get("document_status", "unknown"),
                "scope": metadata.get("document_scope", "unknown"),
                "chunk_type": metadata.get("chunk_type", "original_chunk"),
                "text": document
            })
        return evidence
    except Exception:
        return []


def retrieve_page_evidence(source: str, page_number: int) -> List[Dict[str, Any]]:
    try:
        col = get_collection()
        results = col.get(
            where={"$and": [{"source": source}, {"page_number": page_number}]},
            include=["documents", "metadatas"]
        )
        evidence = []
        for document, metadata in zip(results.get("documents", []), results.get("metadatas", [])):
            evidence.append({
                "source": metadata.get("source"),
                "page": metadata.get("page_number"),
                "status": metadata.get("document_status", "unknown"),
                "scope": metadata.get("document_scope", "unknown"),
                "chunk_type": metadata.get("chunk_type", "original_chunk"),
                "text": document
            })
        return evidence
    except Exception:
        return []
