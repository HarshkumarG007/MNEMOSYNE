import pytest
import asyncio
from unittest.mock import patch, MagicMock

from mnemosyne.agents.ingestion import IngestionAgent
from mnemosyne.agents.extraction import ExtractionAgent
from mnemosyne.agents.bus import bus

@pytest.mark.asyncio
@patch("mnemosyne.agents.ingestion.detect_file_type")
async def test_ingestion_agent(mock_detect) -> None:
    mock_detect.return_value = "application/pdf"
    
    agent = IngestionAgent()
    result = await agent.run({"files": ["dummy.pdf"]})
    
    assert "artifacts" in result
    assert len(result["artifacts"]) == 1
    artifact = result["artifacts"][0]
    assert artifact["file_path"] == "dummy.pdf"
    assert artifact["mime_type"] == "application/pdf"
    assert artifact["status"] == "extracted"

@pytest.mark.asyncio
@patch("mnemosyne.agents.extraction.router")
async def test_extraction_agent_high_confidence(mock_router) -> None:
    # Mock LLM returning valid high confidence JSON
    mock_router.generate = AsyncMock(return_value='{"entities": [{"type": "person", "value": "Alice", "confidence": 0.9}]}')
    
    agent = ExtractionAgent()
    result = await agent.run({"text": "Alice went to the store."})
    
    assert "entities" in result
    assert len(result["entities"]) == 1
    assert result["entities"][0]["value"] == "Alice"

@pytest.mark.asyncio
@patch("mnemosyne.agents.extraction.router")
async def test_extraction_agent_low_confidence_debate(mock_router) -> None:
    # Mock LLM returning low confidence, should trigger debate
    mock_router.generate = AsyncMock(return_value='{"entities": [{"type": "org", "value": "UnknownCorp", "confidence": 0.5}]}')
    
    received_debates = []
    async def debate_handler(msg):
        received_debates.append(msg)
        
    bus.subscribe("debate", debate_handler)
    
    agent = ExtractionAgent()
    result = await agent.run({"text": "UnknownCorp might be involved."})
    
    assert len(result["entities"]) == 1
    # Check that debate was fired
    # Give the bus a moment to process background tasks if needed, though publish is awaited
    assert len(received_debates) == 1
    assert received_debates[0].payload["entity"]["value"] == "UnknownCorp"

# Create a helper for AsyncMock in python <3.8, though we use 3.11+
class AsyncMock(MagicMock):
    async def __call__(self, *args, **kwargs):
        return super(AsyncMock, self).__call__(*args, **kwargs)
