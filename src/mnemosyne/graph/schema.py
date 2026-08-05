"""
Schema definitions and cypher queries for Memgraph initialization.
"""
import logging

import neo4j

logger = logging.getLogger(__name__)

# Memgraph doesn't have a strict schema definition like relational databases,
# but we can enforce constraints and create indexes for performance.
# In Memgraph, we use CREATE INDEX for properties.

INIT_QUERIES = [
    # Create indexes on node labels
    "CREATE INDEX ON :Entity;",
    "CREATE INDEX ON :Evidence;",
    "CREATE INDEX ON :Event;",
    # Create property indexes for temporal queries
    "CREATE INDEX ON :Entity(valid_from);",
    "CREATE INDEX ON :Entity(valid_to);",
    "CREATE INDEX ON :Relationship(valid_from);",
    "CREATE INDEX ON :Relationship(valid_to);",
    "CREATE INDEX ON :Event(start_time);",
    "CREATE INDEX ON :Event(end_time);",
]


async def initialize_schema(session: neo4j.AsyncSession) -> None:
    """
    Run initialization queries to set up indexes.

    Args:
        session: An active neo4j.AsyncSession
    """
    for query in INIT_QUERIES:
        try:
            await session.run(query)
        except Exception as e:
            logger.warning(f"Failed to execute schema query '{query}': {e}")
    logger.info("Schema initialization complete.")
