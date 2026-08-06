import asyncio
import logging
import uuid
from typing import Any, Dict, List, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from .base import AgentMessage, BaseAgent
from .bus import bus
from .correlation import CorrelationAgent
from .extraction import ExtractionAgent
from .ingestion import IngestionAgent
from .temporal import TemporalAgent

logger = logging.getLogger(__name__)


# Define LangGraph State
class SupervisorState(TypedDict):
    files: List[str]
    ingested_artifacts: List[Dict[str, Any]]
    extracted_entities: List[Dict[str, Any]]
    temporal_events: List[Dict[str, Any]]
    resolved_entities: List[Dict[str, Any]]
    correlation_edges: List[Dict[str, Any]]
    errors: List[str]


class SupervisorAgent(BaseAgent):
    """
    Orchestrates the workflow: Ingestion -> Extraction -> Temporal -> Correlation
    """

    def __init__(self):  # type: ignore
        super().__init__(name="Supervisor")
        # Global limit of 5 concurrent agents
        self._semaphore = asyncio.Semaphore(5)

        self._ingestion_agent = IngestionAgent()  # type: ignore
        self._extraction_agent = ExtractionAgent()  # type: ignore
        self._temporal_agent = TemporalAgent()  # type: ignore
        self._correlation_agent = CorrelationAgent()  # type: ignore

        # In-memory checkpointer for now. We can use AsyncSqliteSaver for persistence later.
        self._checkpointer = MemorySaver()
        self._graph = self._build_graph()  # type: ignore

    def _build_graph(self):  # type: ignore
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

    async def _node_ingestion(self, state: SupervisorState):  # type: ignore
        logger.info("[Supervisor] Routing to Ingestion")
        result = await self._ingestion_agent.run({"files": state.get("files", [])})  # type: ignore
        await bus.publish("progress", AgentMessage(id=str(uuid.uuid4()), sender="Supervisor", topic="progress", payload={"step": "ingestion"}))
        return {"ingested_artifacts": result.get("artifacts", [])}

    async def _node_extraction(self, state: SupervisorState):  # type: ignore
        logger.info("[Supervisor] Routing to Extraction")
        all_entities = []
        for artifact in state.get("ingested_artifacts", []):
            # In real system, we'd extract text from the file via content_hash.
            # For MVP, we'll pass the path as text to trigger NER.
            text_to_process = f"File {artifact.get('file_path', 'unknown')} created on 2023-01-01 by John Doe."
            res = await self._extraction_agent.run({"text": text_to_process})  # type: ignore
            all_entities.extend(res.get("entities", []))

        await bus.publish("progress", AgentMessage(id=str(uuid.uuid4()), sender="Supervisor", topic="progress", payload={"step": "extraction"}))
        return {"extracted_entities": all_entities}

    async def _node_temporal(self, state: SupervisorState):  # type: ignore
        logger.info("[Supervisor] Routing to Temporal")

        # Call TemporalAgent
        result = await self._temporal_agent.run({"raw_events": [{"start": "yesterday", "id": "1", "description": "test"}]})  # type: ignore

        await bus.publish("progress", AgentMessage(id=str(uuid.uuid4()), sender="Supervisor", topic="progress", payload={"step": "temporal"}))
        return {"temporal_events": result.get("events", [])}

    async def _node_correlation(self, state: SupervisorState):  # type: ignore
        logger.info("[Supervisor] Routing to Correlation")

        # Call CorrelationAgent
        result = await self._correlation_agent.run({"entities": state.get("extracted_entities", []), "interactions": []})  # type: ignore

        await bus.publish("progress", AgentMessage(id=str(uuid.uuid4()), sender="Supervisor", topic="progress", payload={"step": "correlation"}))
        return {"resolved_entities": result.get("resolved_entities", []), "correlation_edges": result.get("edges", [])}

    async def _execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:  # type: ignore
        """
        Executes the LangGraph workflow.
        """
        thread_id = input_data.get("thread_id", str(uuid.uuid4()))
        config = {"configurable": {"thread_id": thread_id}}

        initial_state = {"files": input_data.get("files", []), "ingested_artifacts": [], "extracted_entities": [], "temporal_events": [], "errors": []}

        logger.info(f"[Supervisor] Starting workflow for thread {thread_id}")

        # Apply concurrency limit
        async with self._semaphore:
            result = await self._graph.ainvoke(initial_state, config=config)

        return result  # type: ignore
