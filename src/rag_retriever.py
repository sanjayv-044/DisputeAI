
import chromadb
from sentence_transformers import SentenceTransformer

# Load the embedding model
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# Connect to the existing ChromaDB database
client = chromadb.PersistentClient(
    path="documents/chroma_db"
)

# Access the RBI regulations collection
collection = client.get_collection(
    name="rbi_regulations"
)


def retrieve_rbi_rules(question, top_k=5):
    """
    Search RBI documents for passages relevant to a question.
    Returns source, page number, text and relevance distance.
    """

    question_embedding = model.encode(question).tolist()

    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=top_k
    )

    retrieved_rules = []

    for i, document in enumerate(results["documents"][0]):
        metadata = results["metadatas"][0][i]

        retrieved_rules.append({
            "source": metadata["source"],
            "page_number": metadata["page_number"],
            "text": document,
            "distance": results["distances"][0][i]
        })

    return retrieved_rules


print("RAG retrieval module created successfully!")
