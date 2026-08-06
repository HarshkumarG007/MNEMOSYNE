import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from rank_bm25 import BM25Okapi  # type: ignore
from sentence_transformers import CrossEncoder

logger = logging.getLogger(__name__)


@dataclass
class RetrievedNode:
    id: str
    content: str
    metadata: Dict[str, Any]
    score: float
    source: str  # "dense", "sparse", or "hybrid"


class HybridRetriever:
    """
    Combines Dense vector search (ChromaDB) with BM25 sparse retrieval.
    Re-ranks the blended pool using a Cross-Encoder.
    """

    def __init__(self, vector_store, reranker_model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):  # type: ignore
        self.vector_store = vector_store
        # Initialize Cross-Encoder
        try:
            self.reranker = CrossEncoder(reranker_model_name)
        except Exception as e:
            logger.error(f"Failed to load reranker {reranker_model_name}: {e}")
            self.reranker = None

        # In-memory BM25 index components
        self.corpus: List[Dict[str, Any]] = []
        self.bm25: Optional[BM25Okapi] = None

    def add_to_bm25(self, document_id: str, content: str, metadata: Dict[str, Any]) -> None:
        """Adds a document to the in-memory sparse index."""
        self.corpus.append({"id": document_id, "content": content, "metadata": metadata})
        # Rebuild index (naive approach for MVP)
        tokenized_corpus = [doc["content"].lower().split(" ") for doc in self.corpus]
        self.bm25 = BM25Okapi(tokenized_corpus)

    def _sparse_search(self, query: str, top_k: int = 5) -> List[RetrievedNode]:
        if not self.bm25 or not self.corpus:
            return []

        tokenized_query = query.lower().split(" ")
        scores = self.bm25.get_scores(tokenized_query)

        # Get top K indices
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                doc = self.corpus[idx]
                results.append(RetrievedNode(id=doc["id"], content=doc["content"], metadata=doc["metadata"], score=float(scores[idx]), source="sparse"))
        return results

    async def _dense_search(self, query: str, top_k: int = 5) -> List[RetrievedNode]:
        # Delegate to vector store
        try:
            results = await self.vector_store.search(query, limit=top_k)
            nodes = []
            for r in results:
                nodes.append(
                    RetrievedNode(
                        id=r["id"],
                        content=r["text"],
                        metadata=r["metadata"],
                        score=r["distance"],  # Assuming distance, lower is better usually, but we'll rerank anyway
                        source="dense",
                    )
                )
            return nodes
        except Exception as e:
            logger.error(f"Dense search failed: {e}")
            return []

    async def search(self, query: str, top_k: int = 5) -> List[RetrievedNode]:
        """
        Executes Hybrid Search:
        1. Fetch top K from BM25
        2. Fetch top K from Dense
        3. Deduplicate
        4. Re-rank with Cross-Encoder
        5. Return new top K
        """
        # Fetch from both pools
        sparse_results = self._sparse_search(query, top_k=top_k)
        dense_results = await self._dense_search(query, top_k=top_k)

        # Deduplicate by ID
        blended: Dict[str, RetrievedNode] = {}
        for r in sparse_results + dense_results:
            if r.id not in blended:
                blended[r.id] = r
            else:
                blended[r.id].source = "hybrid"  # Found in both

        candidate_nodes = list(blended.values())

        if not candidate_nodes:
            return []

        if not self.reranker:
            # Fallback if reranker failed to load
            logger.warning("Reranker unavailable, returning unranked blended results.")
            return candidate_nodes[:top_k]

        # Prepare pairs for Cross-Encoder: (query, document)
        pairs = [[query, node.content] for node in candidate_nodes]

        # Predict relevance scores
        rerank_scores = self.reranker.predict(pairs)

        # Update scores and sort
        for i, node in enumerate(candidate_nodes):
            node.score = float(rerank_scores[i])

        candidate_nodes.sort(key=lambda x: x.score, reverse=True)

        return candidate_nodes[:top_k]
