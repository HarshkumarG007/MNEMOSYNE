"""
Memgraph client with connection pooling and async support.
"""
import logging
from typing import Any, Dict, List, Optional

from neo4j import AsyncDriver, AsyncGraphDatabase
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from .schema import initialize_schema

logger = logging.getLogger(__name__)


class MemgraphClient:
    """Async client for interacting with Memgraph."""

    def __init__(self, uri: str = "bolt://localhost:7687", user: str = "", password: str = ""):
        self.uri = uri
        self.user = user
        self.password = password
        self.driver: Optional[AsyncDriver] = None

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(5),
        retry=retry_if_exception_type(Exception),
    )
    async def connect(self) -> None:
        """Connect to Memgraph with retry logic."""
        logger.info(f"Connecting to Memgraph at {self.uri}...")
        self.driver = AsyncGraphDatabase.driver(
            self.uri, auth=(self.user, self.password) if self.user else None
        )

        # Verify connectivity
        await self.driver.verify_connectivity()
        logger.info("Successfully connected to Memgraph.")

    async def initialize(self) -> None:
        """Initialize schema constraints and indexes."""
        if not self.driver:
            raise RuntimeError("Driver not connected. Call connect() first.")

        async with self.driver.session() as session:
            await initialize_schema(session)

    async def close(self) -> None:
        """Close the database driver connection."""
        if self.driver:
            await self.driver.close()
            logger.info("Closed Memgraph connection.")

    async def execute_query(
        self, query: str, parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a Cypher query and return the results.

        Args:
            query: The Cypher query string
            parameters: Dictionary of query parameters

        Returns:
            List of dictionaries representing the records
        """
        if not self.driver:
            raise RuntimeError("Driver not connected. Call connect() first.")

        async with self.driver.session() as session:
            result = await session.run(query, parameters or {})
            records = await result.data()
            return records
