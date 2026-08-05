import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import dateparser
from pydantic import BaseModel

from .base import BaseAgent

logger = logging.getLogger(__name__)

class EventNode(BaseModel):
    id: str
    description: str
    start_time: datetime
    end_time: datetime
    is_cause: bool = False
    is_effect: bool = False
    related_event_ids: List[str] = []

class TemporalAgent(BaseAgent):
    """
    Timeline construction and temporal reasoning.
    """
    def __init__(self):
        super().__init__(name="TemporalAgent")

    def parse_time(self, time_expr: str) -> Optional[datetime]:
        """Parses temporal expressions to ISO 8601 datetime using dateparser."""
        parsed = dateparser.parse(time_expr)
        if parsed:
            # Ensure timezone awareness (default to UTC if naive)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed
        return None

    def validate_consistency(self, cause: EventNode, effect: EventNode) -> bool:
        """
        Validates temporal consistency.
        Returns False if an effect appears to precede its stated cause.
        """
        if effect.start_time < cause.start_time:
            logger.warning(f"Temporal paradox detected! Effect '{effect.id}' starts before cause '{cause.id}'")
            return False
        return True

    # Allen's interval algebra operations
    def is_before(self, a: EventNode, b: EventNode) -> bool:
        return a.end_time <= b.start_time

    def is_after(self, a: EventNode, b: EventNode) -> bool:
        return a.start_time >= b.end_time

    def is_during(self, a: EventNode, b: EventNode) -> bool:
        return a.start_time >= b.start_time and a.end_time <= b.end_time

    def overlaps(self, a: EventNode, b: EventNode) -> bool:
        return a.start_time < b.end_time and a.end_time > b.start_time

    async def _execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Takes raw temporal expressions/events and normalizes them.
        """
        raw_events = input_data.get("raw_events", [])
        events: List[EventNode] = []
        
        for raw in raw_events:
            start_expr = raw.get("start")
            end_expr = raw.get("end")
            
            start_time = self.parse_time(start_expr) if start_expr else None
            end_time = self.parse_time(end_expr) if end_expr else None
            
            # Simple assumption: point in time has start == end
            if start_time and not end_time:
                end_time = start_time
            if not start_time and end_time:
                start_time = end_time
                
            if start_time and end_time:
                event = EventNode(
                    id=raw.get("id", "unknown"),
                    description=raw.get("description", ""),
                    start_time=start_time,
                    end_time=end_time,
                    is_cause=raw.get("is_cause", False),
                    is_effect=raw.get("is_effect", False),
                    related_event_ids=raw.get("related_event_ids", [])
                )
                events.append(event)
        
        # Validate consistencies if causality is marked
        inconsistencies = []
        for e1 in events:
            if e1.is_cause:
                for e2 in events:
                    if e2.is_effect and e1.id in e2.related_event_ids:
                        if not self.validate_consistency(cause=e1, effect=e2):
                            inconsistencies.append({"cause": e1.id, "effect": e2.id})
                            
        return {
            "events": [e.model_dump() for e in events],
            "inconsistencies": inconsistencies
        }
