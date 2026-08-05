from unittest.mock import patch

import pytest
from mnemosyne.memory.vector_store import VectorStore


@pytest.fixture
def store() -> Any:
    # Because VectorStore persists to disk, in tests we might want to mock chroma or use EphemeralClient.
    # We will patch the client initialization to use EphemeralClient for testing.
    with patch("chromadb.PersistentClient") as mock_client:
        import chromadb

        mock_client.return_value = chromadb.EphemeralClient()
        yield VectorStore()


@pytest.mark.asyncio
@patch("mnemosyne.memory.vector_store.embed")
async def test_vector_store_isolation(mock_embed, store) -> None:
    """Test that cases are isolated in ChromaDB."""

    # Mock embed to just return dummy vectors
    mock_embed.return_value = [[0.1, 0.2, 0.3]]

    await store.add(
        case_id="case_A", documents=["secret doc A"], metadatas=[{"source": "A"}], ids=["doc_1"]
    )

    await store.add(
        case_id="case_B", documents=["public doc B"], metadatas=[{"source": "B"}], ids=["doc_2"]
    )

    # Search in case A
    results_A = await store.search(case_id="case_A", query="secret", k=10)
    assert len(results_A) == 1
    assert results_A[0]["document"] == "secret doc A"

    # Search in case B
    results_B = await store.search(case_id="case_B", query="secret", k=10)
    assert len(results_B) == 1
    assert results_B[0]["document"] == "public doc B"


@pytest.mark.asyncio
@patch("mnemosyne.memory.vector_store.embed")
async def test_vector_store_metadata_filter(mock_embed, store) -> None:
    """Test metadata filtering."""

    mock_embed.side_effect = [[[0.1, 0.1], [0.2, 0.2]], [[0.1, 0.1], [0.2, 0.2]]]

    await store.add(
        case_id="case_C",
        documents=["doc 1", "doc 2"],
        metadatas=[{"type": "email"}, {"type": "pdf"}],
        ids=["id_1", "id_2"],
    )

    # Filter by type=email
    results = await store.search(
        case_id="case_C", query="doc", k=10, filter_metadata={"type": "email"}
    )
    assert len(results) == 1
    assert results[0]["id"] == "id_1"
