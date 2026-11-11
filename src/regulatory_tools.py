
import chromadb
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

client = chromadb.PersistentClient(path="documents/chroma_db")
collection = client.get_collection(name="rbi_regulations")


def format_evidence(results):
    evidence = []

    for i, document in enumerate(results["documents"][0]):
        metadata = results["metadatas"][0][i]

        evidence.append({
            "source": metadata["source"],
            "page": metadata["page_number"],
            "status": metadata.get("document_status", "unknown"),
            "scope": metadata.get("document_scope", "unknown"),
            "chunk_type": metadata.get("chunk_type", "original_chunk"),
            "text": document
        })

    return evidence


def search_regulations(question, top_k=5):
    embedding = model.encode(question).tolist()

    results = collection.query(
        query_embeddings=[embedding],
        n_results=top_k
    )

    return format_evidence(results)


def retrieve_by_status(status, top_k=10):
    results = collection.get(
        where={"document_status": status},
        limit=top_k,
        include=["documents", "metadatas"]
    )

    evidence = []

    for document, metadata in zip(
        results["documents"],
        results["metadatas"]
    ):
        evidence.append({
            "source": metadata["source"],
            "page": metadata["page_number"],
            "status": metadata.get("document_status", "unknown"),
            "scope": metadata.get("document_scope", "unknown"),
            "chunk_type": metadata.get("chunk_type", "original_chunk"),
            "text": document
        })

    return evidence


def retrieve_page_evidence(source, page_number):
    results = collection.get(
        where={
            "$and": [
                {"source": source},
                {"page_number": page_number}
            ]
        },
        include=["documents", "metadatas"]
    )

    evidence = []

    for document, metadata in zip(
        results["documents"],
        results["metadatas"]
    ):
        evidence.append({
            "source": metadata["source"],
            "page": metadata["page_number"],
            "status": metadata.get("document_status", "unknown"),
            "scope": metadata.get("document_scope", "unknown"),
            "chunk_type": metadata.get("chunk_type", "original_chunk"),
            "text": document
        })

    return evidence


print("Regulatory retrieval tools updated successfully!")
