
import re
from pathlib import Path

from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
import chromadb

model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)

client = chromadb.PersistentClient(
    path="documents/chroma_db"
)

collection = client.get_collection(
    name="rbi_regulations"
)


def index_pdf(
    pdf_path,
    document_status="needs_review",
    document_scope="unspecified"
):

    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(pdf_path)

    reader = PdfReader(str(pdf_path))

    documents = []
    metadatas = []
    ids = []

    safe_name = re.sub(
        r"[^A-Za-z0-9]+", "_", pdf_path.stem
    )

    for page_number, page in enumerate(
        reader.pages, start=1
    ):

        text = page.extract_text() or ""
        text = " ".join(text.split())

        if not text:
            continue

        chunk_id = (
            f"{safe_name}_P{page_number}_C1"
        )

        documents.append(text)

        metadatas.append({
            "source": pdf_path.name,
            "page_number": page_number,
            "chunk_index": 1,
            "document_status": document_status,
            "document_scope": document_scope
        })

        ids.append(chunk_id)

    if documents:
        embeddings = model.encode(
            documents,
            show_progress_bar=False
        ).tolist()

        collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )

    return {
        "source": pdf_path.name,
        "pages_indexed": len(documents),
        "collection_count": collection.count()
    }


print("Stable document indexer created successfully!")
