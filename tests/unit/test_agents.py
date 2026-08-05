import pytest
import asyncio
from mnemosyne.agents.base import BaseAgent, AgentMessage
from mnemosyne.agents.bus import MessageBus
from mnemosyne.agents.supervisor import SupervisorAgent

class DummyAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="Dummy")
        self.state = 0
    
    async def _execute(self, input_data: dict) -> dict:
        if input_data.get("fail"):
            raise ValueError("Intentional failure")
        self.state += 1
        return {"result": "success", "state": self.state}

@pytest.mark.asyncio
async def test_base_agent_success() -> None:
    agent = DummyAgent()
    res = await agent.run({"fail": False})
    assert res["result"] == "success"
    assert res["state"] == 1

@pytest.mark.asyncio
async def test_base_agent_failure() -> None:
    agent = DummyAgent()
    with pytest.raises(ValueError):
        await agent.run({"fail": True})

@pytest.mark.asyncio
async def test_message_bus_pubsub() -> None:
    bus = MessageBus()
    received = []
    
    async def handler(msg: AgentMessage):
        received.append(msg.payload["value"])
        
    bus.subscribe("test_topic", handler)
    
    await bus.publish("test_topic", AgentMessage(
        id="1", sender="test", topic="test_topic", payload={"value": "A"}
    ))
    
    assert received == ["A"]

@pytest.mark.asyncio
async def test_message_bus_dlq() -> None:
    bus = MessageBus(max_retries=1)
    
    async def fail_handler(msg: AgentMessage):
        raise RuntimeError("Fail")
        
    bus.subscribe("fail_topic", fail_handler)
    
    # Should not raise, but move to DLQ
    await bus.publish("fail_topic", AgentMessage(
        id="2", sender="test", topic="fail_topic", payload={}
    ))
    
    dlq = bus.get_dlq()
    assert len(dlq) == 1
    assert dlq[0].id == "2"

@pytest.mark.asyncio
async def test_supervisor_workflow() -> None:
    supervisor = SupervisorAgent()
    
    # Run the workflow graph with dummy initial state
    result = await supervisor.run({"files": ["test1.txt"]})
    
    # Just checking it completes and returns dict
    assert isinstance(result, dict)
    assert "ingested_artifacts" in result
    assert "extracted_entities" in result
    assert "temporal_events" in result
