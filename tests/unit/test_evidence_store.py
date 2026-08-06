import os
from typing import Any

import pytest
from cryptography.exceptions import InvalidTag
from mnemosyne.evidence.store import EvidenceStore


@pytest.fixture
def evidence_store(tmp_path) -> Any:
    # Use a temporary directory for the database
    db_path = str(tmp_path / "test_evidence.sqlite")

    # Store the original environment variable if it exists
    original_key = os.environ.get("MNEMOSYNE_EVIDENCE_KEY")

    # Force a new key generation for tests by removing it from the environment
    if "MNEMOSYNE_EVIDENCE_KEY" in os.environ:
        del os.environ["MNEMOSYNE_EVIDENCE_KEY"]

    store = EvidenceStore(db_path=db_path)
    await store.initialize()

    yield store

    # Restore the original environment variable
    if original_key is not None:
        os.environ["MNEMOSYNE_EVIDENCE_KEY"] = original_key
    else:
        if "MNEMOSYNE_EVIDENCE_KEY" in os.environ:
            del os.environ["MNEMOSYNE_EVIDENCE_KEY"]


@pytest.mark.asyncio
async def test_store_and_retrieve(evidence_store: EvidenceStore) -> None:
    test_data = b"Hello, MNEMOSYNE!"

    # Store the data
    hash_id = await evidence_store.store(test_data)

    assert hash_id is not None

    # Retrieve the data
    retrieved_data = await evidence_store.retrieve(hash_id)

    assert retrieved_data == test_data


@pytest.mark.asyncio
async def test_deduplication(evidence_store: EvidenceStore) -> None:
    test_data = b"Duplicate Data"

    # Store the data twice
    hash_id1 = await evidence_store.store(test_data)
    hash_id2 = await evidence_store.store(test_data)

    # Hashes should be identical
    assert hash_id1 == hash_id2

    # Check that there is only one entry in the database
    import aiosqlite

    async with aiosqlite.connect(evidence_store.db_path) as db:
        async with db.execute("SELECT COUNT(*) FROM evidence") as cursor:
            count = (await cursor.fetchone())[0]
            assert count == 1


@pytest.mark.asyncio
async def test_retrieve_nonexistent(evidence_store: EvidenceStore) -> None:
    with pytest.raises(KeyError):
        await evidence_store.retrieve("nonexistent_hash")


@pytest.mark.asyncio
async def test_decryption_failure_with_wrong_key(tmp_path) -> None:
    db_path = str(tmp_path / "test_wrong_key.sqlite")

    # First store with one key
    if "MNEMOSYNE_EVIDENCE_KEY" in os.environ:
        del os.environ["MNEMOSYNE_EVIDENCE_KEY"]

    store1 = EvidenceStore(db_path=db_path)
    await store1.initialize()

    hash_id = await store1.store(b"Secret Data")

    # Now try to retrieve with a different key
    if "MNEMOSYNE_EVIDENCE_KEY" in os.environ:
        del os.environ["MNEMOSYNE_EVIDENCE_KEY"]

    store2 = EvidenceStore(db_path=db_path)

    # Retrieval should fail due to InvalidTag (MAC check failure)
    with pytest.raises(InvalidTag):
        await store2.retrieve(hash_id)
