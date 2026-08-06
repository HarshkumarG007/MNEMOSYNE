import os
from typing import Any, Dict, List, Optional

import chromadb
from mnemosyne.models.embeddings import embed

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data")
CHROMA_DIR = os.path.join(DATA_DIR, "chroma")


class VectorStore:
    """Semantic vector store powered by ChromaDB."""

    def __init__(self):  # type: ignore
        os.makedirs(CHROMA_DIR, exist_ok=True)
        self.client = chromadb.PersistentClient(path=CHROMA_DIR)

    async def add(self, case_id: str, documents: List[str], metadatas: List[Dict[str, Any]], ids: List[str]) -> None:
        """
        Add a list of documents to the vector store.
        Collections are isolated per case_id.
        """
        if not documents:
            return

        collection = self.client.get_or_create_collection(name=f"case_{case_id}", metadata={"hnsw:space": "cosine"})

        # Generate embeddings
        embeddings = await embed(documents)

        # Add to collection
        collection.upsert(documents=documents, embeddings=embeddings, metadatas=metadatas, ids=ids)  # type: ignore

    async def search(
        self,
        case_id: str,
        query: str,
        k: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for semantically similar documents within a case.
        """
        try:
            collection = self.client.get_collection(name=f"case_{case_id}")
        except ValueError:
            # Collection does not exist
            return []

        query_embedding = (await embed([query]))[0]

        results = collection.query(query_embeddings=[query_embedding], n_results=k, where=filter_metadata)

        # Format results
        formatted = []
        if results and results.get("documents") and results["documents"][0]:  # type: ignore
            docs = results["documents"][0]  # type: ignore
            metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)  # type: ignore
            dists = results["distances"][0] if results.get("distances") else [0.0] * len(docs)  # type: ignore
            id_list = results["ids"][0]

            for doc, meta, dist, doc_id in zip(docs, metas, dists, id_list, strict=False):
                formatted.append({"id": doc_id, "document": doc, "metadata": meta, "distance": dist})
        return formatted
