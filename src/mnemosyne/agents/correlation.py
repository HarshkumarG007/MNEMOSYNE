import logging
from typing import Any, Dict, List

from pydantic import BaseModel

from .base import BaseAgent

logger = logging.getLogger(__name__)


class EntityNode(BaseModel):
    id: str
    type: str
    value: str
    aliases: List[str] = []


class EvidenceEdge(BaseModel):
    source_id: str
    target_id: str
    relationship: str
    supporting_evidence: str


class CorrelationAgent(BaseAgent):
    """
    Entity resolution and pattern detection.
    """

    def __init__(self):  # type: ignore
        super().__init__(name="CorrelationAgent")

    def resolve_entities(self, entities: List[Dict[str, Any]]) -> List[EntityNode]:
        """
        Simple heuristic entity resolution.
        Merges entities if they share exact names or emails.
        """
        resolved: Dict[str, EntityNode] = {}

        for e in entities:
            # normalize for comparison
            val = e.get("value", "").lower().strip()
            if not val:
                continue

            if val in resolved:
                # Add aliases if they have any
                pass
            else:
                resolved[val] = EntityNode(id=e.get("id", f"ent_{len(resolved)}"), type=e.get("type", "unknown"), value=val)

        return list(resolved.values())

    async def _execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:  # type: ignore
        raw_entities = input_data.get("entities", [])
        raw_interactions = input_data.get("interactions", [])

        # Resolve entities
        resolved_nodes = self.resolve_entities(raw_entities)

        edges: List[EvidenceEdge] = []

        # Build communication graph
        for interaction in raw_interactions:
            source = interaction.get("source")
            target = interaction.get("target")
            evidence = interaction.get("evidence")

            if source and target and evidence:
                edges.append(
                    EvidenceEdge(source_id=source, target_id=target, relationship=interaction.get("type", "communicated_with"), supporting_evidence=evidence)
                )
            elif source and target and not evidence:
                logger.warning(f"Discarding proposed edge {source}->{target}: no supporting evidence cited.")

        return {"resolved_entities": [n.model_dump() for n in resolved_nodes], "edges": [e.model_dump() for e in edges]}
