import json
import logging
import uuid
from typing import Any, Dict

from mnemosyne.models.llm_router import router

from .base import AgentMessage, BaseAgent
from .bus import bus

logger = logging.getLogger(__name__)

NER_PROMPT = """You are an advanced digital forensics Named Entity Recognition system.
Extract entities (person, org, location, date, file) from the text.
Output MUST be valid JSON with the structure:
{{
  "entities": [
    {{"type": "person", "value": "John Doe", "confidence": 0.95}}
  ]
}}

Text: {text}
"""


class ExtractionAgent(BaseAgent):
    """
    Extracts entities and relationships using the LLMRouter (Phi-3).
    Triggers debate if confidence is low.
    """

    def __init__(self):  # type: ignore
        super().__init__(name="ExtractionAgent")

    async def _execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:  # type: ignore
        text_content: str = input_data.get("text", "")

        if not text_content:
            return {"entities": []}

        prompt = NER_PROMPT.format(text=text_content)

        logger.info(f"[ExtractionAgent] Requesting NER extraction for text of length {len(text_content)}")

        try:
            # Call LLM Router for fast_ner task
            response = await router.generate(prompt=prompt, task_type="fast_ner")

            # Parse JSON out of response (assuming well-formed for now)
            # In a robust implementation, we would extract the JSON block.
            try:
                parsed = json.loads(response)
                entities = parsed.get("entities", [])
            except json.JSONDecodeError:
                logger.error("[ExtractionAgent] Failed to parse LLM response as JSON.")
                entities = []

            # Check for low confidence
            for entity in entities:
                conf = entity.get("confidence", 1.0)
                if conf < 0.7:
                    logger.warning(f"[ExtractionAgent] Low confidence entity found ({conf}): {entity}. Triggering debate.")
                    await bus.publish(
                        "debate", AgentMessage(id=str(uuid.uuid4()), sender=self.name, topic="debate", payload={"entity": entity, "context": text_content})
                    )

            return {"entities": entities}

        except Exception as e:
            logger.error(f"[ExtractionAgent] LLM Generation failed: {e}")
            raise e
