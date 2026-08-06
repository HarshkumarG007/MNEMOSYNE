import asyncio
import logging
import uuid
from typing import Any, Dict, List

from mnemosyne.ingestion.detector import detect_file_type

from .base import AgentMessage, BaseAgent
from .bus import bus

# assuming the ingestion pipeline code handles sandbox & extractors under the hood
# we will mock this or provide the core flow for now

logger = logging.getLogger(__name__)


class IngestionAgent(BaseAgent):
    """
    Coordinates file processing: detector -> sandbox -> extraction
    """

    def __init__(self):  # type: ignore
        super().__init__(name="IngestionAgent")

    async def _execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:  # type: ignore
        files: List[str] = input_data.get("files", [])
        artifacts = []

        for file_path in files:
            try:
                # 1. Detect file type
                mime_type = await detect_file_type(file_path)
                logger.info(f"[IngestionAgent] Detected {mime_type} for {file_path}")

                # 2. Run Sandboxed Extractor
                # This would integrate with M2-2 and M2-3.
                # For now, we simulate success and return a mock artifact.
                await asyncio.sleep(0.5)  # Simulate processing time

                artifact = {"file_path": file_path, "mime_type": mime_type, "status": "extracted", "content_hash": "dummy_hash_" + str(uuid.uuid4())[:8]}
                artifacts.append(artifact)

                # Publish progress for this specific file
                await bus.publish(
                    "progress", AgentMessage(id=str(uuid.uuid4()), sender=self.name, topic="progress", payload={"file": file_path, "status": "success"})
                )

            except Exception as e:
                logger.error(f"[IngestionAgent] Error processing {file_path}: {e}")
                # Error isolation: one file fails, rest continue
                await bus.publish("error", AgentMessage(id=str(uuid.uuid4()), sender=self.name, topic="error", payload={"file": file_path}, error=str(e)))

        return {"artifacts": artifacts}
