import abc
import logging
from typing import Any, Dict, Optional, TypeVar
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class AgentMessage(BaseModel):
    """
    Typed message envelope shared by every agent.
    Used for inter-agent communication and state passing.
    """
    id: str
    sender: str
    topic: str
    payload: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None

TInput = TypeVar("TInput")
TOutput = TypeVar("TOutput")

class BaseAgent(abc.ABC):
    """
    Abstract base for all agents.
    Provides standard execution and error handling flows.
    """
    
    def __init__(self, name: str):
        self.name = name

    async def run(self, input_data: TInput) -> TOutput:
        """
        Main execution entry point.
        Wraps the core logic with validation and error handling.
        """
        try:
            logger.info(f"[{self.name}] Agent started processing.")
            output = await self._execute(input_data)
            validated_output = self.validate_output(output)
            logger.info(f"[{self.name}] Agent finished processing successfully.")
            return validated_output
        except Exception as e:
            return await self.handle_error(e, input_data)

    @abc.abstractmethod
    async def _execute(self, input_data: TInput) -> TOutput:
        """Core logic to be implemented by subclasses."""
        pass

    def validate_output(self, output: TOutput) -> TOutput:
        """
        Validates the output. By default returns it as-is, 
        but can be overridden to raise ValidationErrors.
        """
        return output

    async def handle_error(self, error: Exception, input_data: TInput) -> TOutput:
        """
        Default error handler. Can be overridden.
        Logs the error and re-raises by default.
        """
        logger.error(f"[{self.name}] Error during execution: {error}", exc_info=True)
        raise error
