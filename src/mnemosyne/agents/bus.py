import asyncio
import logging
from typing import Any, Callable, Coroutine, Dict, List

from .base import AgentMessage

logger = logging.getLogger(__name__)

# Type for message handlers
MessageHandler = Callable[[AgentMessage], Coroutine[Any, Any, None]]


class MessageBus:
    """
    AsyncIO-based inter-agent communication bus.
    Supports publish/subscribe, ordering within topics, and a dead-letter queue.
    """

    def __init__(self, max_retries: int = 3):
        self._subscribers: Dict[str, List[MessageHandler]] = {}
        self._dlq: List[AgentMessage] = []
        self.max_retries = max_retries

    def subscribe(self, topic: str, handler: MessageHandler) -> None:
        """Subscribe a handler to a specific topic."""
        if topic not in self._subscribers:
            self._subscribers[topic] = []
        self._subscribers[topic].append(handler)
        logger.debug(f"Subscribed handler to topic '{topic}'.")

    async def publish(self, topic: str, message: AgentMessage) -> None:
        """
        Publish a message to all subscribers of a topic.
        Ensures ordering by running handlers sequentially per message.
        """
        if topic not in self._subscribers or not self._subscribers[topic]:
            logger.warning(f"No subscribers for topic '{topic}'. Message dropped or ignored.")
            return

        message.topic = topic

        # Dispatch to all handlers for the topic
        for handler in self._subscribers[topic]:
            await self._dispatch_with_retry(handler, message)

    async def _dispatch_with_retry(self, handler: MessageHandler, message: AgentMessage) -> None:
        """Executes a handler with retries, routing to DLQ on failure."""
        attempts = 0
        last_error = None
        while attempts <= self.max_retries:
            try:
                await handler(message)
                return  # Success
            except Exception as e:
                last_error = e
                attempts += 1
                logger.error(f"Error handling message {message.id} on topic {message.topic}: {e}")
                if attempts <= self.max_retries:
                    logger.info(f"Retrying message {message.id} (attempt {attempts}/{self.max_retries})...")
                    await asyncio.sleep(2**attempts)  # Exponential backoff

        # If we reach here, retries exhausted
        logger.error(f"Retries exhausted for message {message.id}. Moving to DLQ.")
        message.error = f"Retries exhausted. Last error: {str(last_error)}"
        self._dlq.append(message)

    def get_dlq(self) -> List[AgentMessage]:
        """Retrieve all messages in the Dead Letter Queue."""
        return self._dlq


# Global message bus instance
bus = MessageBus()
