import os
import tempfile

import pytest
from mnemosyne.evidence.store import EvidenceStore
from mnemosyne.graph.manager import GraphIngestionManager
from mnemosyne.graph.memgraph_client import MemgraphClient

# Try to use a test database if available, else just rely on the mock/local instance
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")


@pytest.fixture
def evidence_store():
    # Use a temporary directory for evidence storage to keep tests isolated
    with tempfile.TemporaryDirectory() as temp_dir:
        store = EvidenceStore(storage_dir=temp_dir)
        yield store


@pytest.fixture
async def memgraph_client():
    client = MemgraphClient(uri=NEO4J_URI, user=NEO4J_USER, password=NEO4J_PASSWORD)
    try:
        await client.connect()
        # Clear the database for testing
        await client.execute_query("MATCH (n) DETACH DELETE n")
        await client.initialize()
        yield client
    except Exception as e:
        pytest.skip(f"Could not connect to Memgraph: {e}")
    finally:
        try:
            if client.driver:
                await client.execute_query("MATCH (n) DETACH DELETE n")
        except Exception:
            pass
        await client.close()


@pytest.mark.asyncio
async def test_graph_ingestion_manager(memgraph_client, evidence_store):
    manager = GraphIngestionManager(memgraph_client, evidence_store)

    # We will create a dummy text file to ingest
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
        f.write(b"Apple Inc. announced today that Steve Jobs visited Cupertino.")
        temp_path = f.name

    try:
        # Run the manager process
        result = await manager.process_file(temp_path)

        # Verify result dictionary
        assert result["mime_type"] == "text/plain"
        assert result["entity_count"] >= 4
        assert "evidence_hash" in result

        ev_hash = result["evidence_hash"]

        # Verify the database state directly

        # 1. Evidence node should exist
        evidence_nodes = await memgraph_client.execute_query(
            "MATCH (e:Evidence) RETURN e.hash as hash, e.mime_type as mime_type"
        )
        assert len(evidence_nodes) == 1
        assert evidence_nodes[0]["hash"] == ev_hash
        assert evidence_nodes[0]["mime_type"] == "text/plain"

        # 2. Entity nodes should exist
        entity_nodes = await memgraph_client.execute_query(
            "MATCH (en:Entity) RETURN en.id as id, en.type as type, en.name as name"
        )
        assert len(entity_nodes) >= 4

        names = [en["name"] for en in entity_nodes]
        assert "Apple Inc." in names
        assert "Steve Jobs" in names

        # 3. Relationships should exist
        relations = await memgraph_client.execute_query(
            """
            MATCH (en:Entity)-[r:EXTRACTED_FROM]->(ev:Evidence)
            RETURN en.id as entity_id, ev.hash as evidence_hash
        """
        )
        assert len(relations) >= 4

        for rel in relations:
            assert rel["evidence_hash"] == ev_hash

    finally:
        os.remove(temp_path)
