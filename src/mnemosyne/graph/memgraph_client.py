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

    async def create_evidence(self, hash_id: str, mime_type: str) -> None:
        """Create an Evidence node in the graph."""
        query = """
        MERGE (e:Evidence {hash: $hash})
        SET e.mime_type = $mime_type
        """
        await self.execute_query(query, {"hash": hash_id, "mime_type": mime_type})

    async def create_entity(
        self, entity_id: str, entity_type: str, properties: Dict[str, Any]
    ) -> None:
        """Create an Entity node in the graph."""
        # Note: Cypher doesn't allow dynamic labels easily in parameterized MERGE without APOC.
        # So we merge on the generic 'Entity' label and add properties.
        query = """
        MERGE (e:Entity {id: $id})
        SET e.type = $type
        SET e += $props
        """
        await self.execute_query(query, {"id": entity_id, "type": entity_type, "props": properties})

    async def create_extracted_from_relationship(self, entity_id: str, evidence_hash: str) -> None:
        """
        Creates an EXTRACTED_FROM relationship from an Entity to an Evidence node.
        """
        query = """
        MATCH (en:Entity {id: $entity_id})
        MATCH (ev:Evidence {hash: $evidence_hash})
        MERGE (en)-[r:EXTRACTED_FROM]->(ev)
        """
        await self.execute_query(query, {"entity_id": entity_id, "evidence_hash": evidence_hash})

    async def search_entities(self, query_string: str) -> List[Dict[str, Any]]:
        """
        Search for entities by name using a case-insensitive substring match.
        Returns the entity info and a list of related evidence hashes.
        """
        query = """
        MATCH (en:Entity)-[:EXTRACTED_FROM]->(ev:Evidence)
        WHERE toLower(en.name) CONTAINS toLower($q)
        RETURN en.id AS id, en.type AS type, en.name AS name, collect(ev.hash) as evidence_hashes
        """
        records = await self.execute_query(query, {"q": query_string})

        results = []
        for r in records:
            results.append(
                {
                    "id": r["id"],
                    "type": r["type"],
                    "name": r["name"],
                    "evidence_hashes": r["evidence_hashes"],
                }
            )
        return results
