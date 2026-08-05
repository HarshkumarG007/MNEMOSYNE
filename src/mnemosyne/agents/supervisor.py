import asyncio
import logging
from typing import TypedDict, Annotated, Dict, Any, List
import uuid

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from .base import BaseAgent, AgentMessage
from .bus import bus

logger = logging.getLogger(__name__)

# Define LangGraph State
class SupervisorState(TypedDict):
    files: List[str]
    ingested_artifacts: List[Dict[str, Any]]
    extracted_entities: List[Dict[str, Any]]
    temporal_events: List[Dict[str, Any]]
    errors: List[str]

class SupervisorAgent(BaseAgent):
    """
    Orchestrates the workflow: Ingestion -> Extraction -> Temporal -> Correlation
    """
    def __init__(self):
        super().__init__(name="Supervisor")
        # Global limit of 5 concurrent agents
        self._semaphore = asyncio.Semaphore(5)
        
        # In-memory checkpointer for now. We can use AsyncSqliteSaver for persistence later.
        self._checkpointer = MemorySaver()
        self._graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(SupervisorState)
        
        # Add nodes
        workflow.add_node("ingestion", self._node_ingestion)
        workflow.add_node("extraction", self._node_extraction)
        workflow.add_node("temporal", self._node_temporal)
        workflow.add_node("correlation", self._node_correlation)
        
        # Define edges
        workflow.add_edge(START, "ingestion")
        workflow.add_edge("ingestion", "extraction")
        workflow.add_edge("extraction", "temporal")
        workflow.add_edge("temporal", "correlation")
        workflow.add_edge("correlation", END)
        
        return workflow.compile(checkpointer=self._checkpointer)

    async def _node_ingestion(self, state: SupervisorState):
        logger.info("[Supervisor] Routing to Ingestion")
        # Will call IngestionAgent logic here
        await bus.publish("progress", AgentMessage(id=str(uuid.uuid4()), sender="Supervisor", topic="progress", payload={"step": "ingestion"}))
        return {"ingested_artifacts": [{"status": "dummy_ingested"}]}

    async def _node_extraction(self, state: SupervisorState):
        logger.info("[Supervisor] Routing to Extraction")
        # Will call ExtractionAgent logic here
        await bus.publish("progress", AgentMessage(id=str(uuid.uuid4()), sender="Supervisor", topic="progress", payload={"step": "extraction"}))
        return {"extracted_entities": [{"status": "dummy_extracted"}]}

    async def _node_temporal(self, state: SupervisorState):
        logger.info("[Supervisor] Routing to Temporal")
        # Pending M5 implementation
        await bus.publish("progress", AgentMessage(id=str(uuid.uuid4()), sender="Supervisor", topic="progress", payload={"step": "temporal"}))
        return {"temporal_events": []}

    async def _node_correlation(self, state: SupervisorState):
        logger.info("[Supervisor] Routing to Correlation")
        # Pending M5 implementation
        await bus.publish("progress", AgentMessage(id=str(uuid.uuid4()), sender="Supervisor", topic="progress", payload={"step": "correlation"}))
        return {}

    async def _execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the LangGraph workflow.
        """
        thread_id = input_data.get("thread_id", str(uuid.uuid4()))
        config = {"configurable": {"thread_id": thread_id}}
        
        initial_state = {
            "files": input_data.get("files", []),
            "ingested_artifacts": [],
            "extracted_entities": [],
            "temporal_events": [],
            "errors": []
        }
        
        logger.info(f"[Supervisor] Starting workflow for thread {thread_id}")
        
        # Apply concurrency limit
        async with self._semaphore:
            result = await self._graph.ainvoke(initial_state, config=config)
            
        return result
