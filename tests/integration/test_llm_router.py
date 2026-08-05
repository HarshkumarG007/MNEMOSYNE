from unittest.mock import MagicMock, patch

import pytest
from mnemosyne.models.llm_router import LLMRouter


@pytest.fixture
def mock_llama() -> Any:
    with patch("mnemosyne.models.llm_router.Llama") as MockLlama:
        # Setup mock behavior
        mock_instance = MagicMock()
        mock_instance.create_completion.return_value = {"choices": [{"text": "mocked response"}]}
        mock_instance.create_embedding.return_value = {"data": [{"embedding": [0.1, 0.2, 0.3]}]}
        MockLlama.return_value = mock_instance
        yield MockLlama


@pytest.fixture
def router(mock_llama) -> Any:
    # Mock os.path.exists so router doesn't fail on missing models
    with patch("os.path.exists", return_value=True):
        r = LLMRouter(idle_timeout=1)  # short timeout for testing
        yield r
        # Cleanup background task
        r._unload_task.cancel()


@pytest.mark.asyncio
async def test_router_generate(router, mock_llama) -> None:
    """Test generating text routes to the correct model."""
    response = await router.generate("test prompt", "fast_ner")

    assert response == "mocked response"
    mock_llama.assert_called_once()
    assert "Phi-3" in mock_llama.call_args[1]["model_path"]


@pytest.mark.asyncio
async def test_router_embed(router, mock_llama) -> None:
    """Test generating embeddings routes to the embedding model."""
    response = await router.embed("test prompt")

    assert response == [0.1, 0.2, 0.3]
    mock_llama.assert_called_once()
    assert "bge-m3" in mock_llama.call_args[1]["model_path"]


@pytest.mark.asyncio
async def test_router_unload(router, mock_llama) -> None:
    """Test that the router unloads models when switching or closing."""
    await router.generate("test prompt", "fast_ner")
    assert router._current_model_name == "Phi-3-mini-4k-instruct-q4.gguf"

    # Switch to reasoning model
    await router.generate("test prompt", "reasoning")
    assert router._current_model_name == "Mistral-7B-Instruct-v0.3.Q4_K_M.gguf"

    # Call close
    await router.close()
    assert router._current_model is None
