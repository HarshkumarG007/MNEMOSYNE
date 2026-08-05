import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from datetime import datetime, timezone

from mnemosyne.agents.temporal import TemporalAgent, EventNode
from mnemosyne.agents.correlation import CorrelationAgent
from mnemosyne.agents.osint import OsintAgent
from mnemosyne.agents.judge import JudgeAgent

@pytest.mark.asyncio
async def test_temporal_agent_parsing():
    agent = TemporalAgent()
    dt = agent.parse_time("2023-01-01T12:00:00Z")
    assert dt is not None
    assert dt.year == 2023
    assert dt.month == 1

@pytest.mark.asyncio
async def test_temporal_agent_consistency():
    agent = TemporalAgent()
    
    # Effect happens before cause
    cause = EventNode(
        id="e1", description="Cause", 
        start_time=datetime(2023, 1, 2, tzinfo=timezone.utc), 
        end_time=datetime(2023, 1, 2, tzinfo=timezone.utc),
        is_cause=True
    )
    
    effect = EventNode(
        id="e2", description="Effect", 
        start_time=datetime(2023, 1, 1, tzinfo=timezone.utc), 
        end_time=datetime(2023, 1, 1, tzinfo=timezone.utc),
        is_effect=True, related_event_ids=["e1"]
    )
    
    assert agent.validate_consistency(cause, effect) is False

@pytest.mark.asyncio
async def test_correlation_agent_resolution():
    agent = CorrelationAgent()
    
    entities = [
        {"id": "1", "type": "person", "value": "John Doe"},
        {"id": "2", "type": "person", "value": "john doe "}, # should merge
        {"id": "3", "type": "person", "value": "Jane Smith"}
    ]
    
    result = agent.resolve_entities(entities)
    assert len(result) == 2
    assert "john doe" in [r.value for r in result]
    assert "jane smith" in [r.value for r in result]

@pytest.mark.asyncio
async def test_osint_agent_methods():
    agent = OsintAgent()
    # Check that exactly these methods are public
    public_methods = {m for m in dir(agent) if callable(getattr(agent, m)) and not m.startswith("_")}
    assert "whois_lookup" in public_methods
    assert "hibp_lookup" in public_methods
    assert "geoip_lookup" in public_methods
    assert "run" in public_methods
    assert "validate_output" in public_methods
    assert "handle_error" in public_methods
    # Ensure no scope creep!
    expected = {"run", "validate_output", "handle_error", "whois_lookup", "hibp_lookup", "geoip_lookup"}
    assert public_methods == expected

@pytest.mark.asyncio
@patch("mnemosyne.agents.osint.whois")
async def test_osint_agent_whois_cache(mock_whois):
    mock_whois.whois.return_value = {"domain_name": "example.com"}
    agent = OsintAgent()
    
    # First call hits mock
    res1 = await agent.run({"type": "whois", "query": "example.com"})
    assert res1["source"] == "public WHOIS"
    assert mock_whois.whois.call_count == 1
    
    # Second call should hit cache
    res2 = await agent.run({"type": "whois", "query": "example.com"})
    assert res2["source"] == "public WHOIS"
    assert mock_whois.whois.call_count == 1

@pytest.mark.asyncio
@patch("mnemosyne.agents.judge.router")
async def test_judge_agent_human_override(mock_router):
    agent = JudgeAgent()
    
    res = await agent.run({"human_override": "Argument B is correct"})
    assert res["decision"] == "Argument B is correct"
    assert res["is_override"] is True
    assert len(agent.decisions_log) == 1
    assert mock_router.generate.call_count == 0

@pytest.mark.asyncio
@patch("mnemosyne.agents.judge.router")
async def test_judge_agent_decision(mock_router):
    mock_router.generate = AsyncMock(return_value='{"decision": "Argument A", "reasoning_chain": ["1"], "confidence": 0.9}')
    
    agent = JudgeAgent()
    res = await agent.run({"context": "C", "arg_a": "A", "arg_b": "B"})
    
    assert res["decision"] == "Argument A"
    assert res["is_override"] is False
    assert len(agent.decisions_log) == 1
