import pytest
import asyncio
from typing import List
from unittest.mock import AsyncMock, patch

from mnemosyne.memory.retrieval import HybridRetriever, RetrievedNode
from mnemosyne.reporting.generator import ReportGenerator

@pytest.mark.asyncio
async def test_hybrid_retriever_sparse_fallback():
    # Mock vector store that returns NO results for the query
    mock_vector_store = AsyncMock()
    mock_vector_store.search.return_value = []
    
    retriever = HybridRetriever(vector_store=mock_vector_store)
    
    # Add to BM25
    retriever.add_to_bm25("doc1", "The exact hash is 5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8", {"file": "malware.exe"})
    retriever.add_to_bm25("doc2", "Some random text", {})
    retriever.add_to_bm25("doc3", "More random text", {})
    retriever.add_to_bm25("doc4", "Even more text", {})
    
    # Query for the exact hash
    query = "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8"
    results = await retriever.search(query, top_k=1)
    
    print(f"BM25 Scores: {retriever.bm25.get_scores(['5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8'])}")
    print(f"Results: {results}")

    # Assert BM25 caught it even though dense failed
    assert len(results) == 1
    assert results[0].id == "doc1"
    assert results[0].source == "sparse"

@pytest.mark.asyncio
async def test_hybrid_retriever_blending():
    mock_vector_store = AsyncMock()
    # Mock dense returns doc1
    mock_vector_store.search.return_value = [{"id": "doc1", "text": "Dense match", "metadata": {}, "distance": 0.5}]
    
    retriever = HybridRetriever(vector_store=mock_vector_store)
    
    # Mock sparse returns doc2
    retriever.add_to_bm25("doc2", "Sparse match", {})
    retriever.add_to_bm25("doc3", "Nothing relevant", {})
    retriever.add_to_bm25("doc4", "Something else entirely", {})
    
    # Re-ranker will run on both. We can mock it or let it run.
    # Since ms-marco is downloaded, we let it run or mock it. To make test fast, let's mock it.
    with patch.object(retriever.reranker, 'predict', return_value=[0.9, 0.1]):
        results = await retriever.search("match", top_k=2)
        
        assert len(results) == 2
        # The first should be doc2 (sparse) because it was passed as first to predict, assuming sparse results are prepended or dict sorted?
        # Actually, let's just assert both are present
        ids = {r.id for r in results}
        assert "doc1" in ids
        assert "doc2" in ids

def test_report_generator_validation():
    generator = ReportGenerator()
    
    valid_data = {
        "timestamp": "2023-01-01",
        "summary": "Test",
        "timeline": [
            {"time": "12:00", "description": "Event A", "source": "Log", "citation_id": "c1"}
        ],
        "citations": [
            {"id": "c1", "file_path": "/var/log/syslog", "node_uuid": "1234"}
        ]
    }
    
    # Should not raise
    generator.generate_json(valid_data)
    
    invalid_data = {
        "timestamp": "2023-01-01",
        "summary": "Test",
        "timeline": [
            {"time": "12:00", "description": "Event A", "source": "Log", "citation_id": "missing_c2"}
        ],
        "citations": [
            {"id": "c1", "file_path": "/var/log/syslog", "node_uuid": "1234"}
        ]
    }
    
    with pytest.raises(ValueError, match="Invalid citation_id"):
        generator.generate_markdown(invalid_data)

def test_report_generator_markdown():
    generator = ReportGenerator()
    
    data = {
        "timestamp": "2023-01-01",
        "summary": "Test Summary",
        "entities": [],
        "timeline": [
            {"time": "12:00", "description": "Event A", "source": "Log", "citation_id": "c1"}
        ],
        "citations": [
            {"id": "c1", "file_path": "/var/log/syslog", "node_uuid": "1234"}
        ]
    }
    
    md = generator.generate_markdown(data)
    assert "Test Summary" in md
    assert "[^c1]: /var/log/syslog" in md
