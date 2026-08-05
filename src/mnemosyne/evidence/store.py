"""
Evidence storage implementation with SQLite and AES-256-GCM encryption.
"""
import os
import secrets

import aiosqlite
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from dotenv import load_dotenv

from .hashing import calculate_sha256

# Load environment variables
load_dotenv()


class EvidenceStore:
    """Content-addressed storage backed by SQLite, with AES-256-GCM encryption."""

    def __init__(self, db_path: str = "data/evidence.sqlite"):
        self.db_path = db_path

        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        # Load or generate encryption key
        self.key = self._get_or_create_key()
        self.aesgcm = AESGCM(self.key)
        self.nonce_size = 12  # Standard for AES-GCM

    def _get_or_create_key(self) -> bytes:
        """Retrieve AES key from environment or generate and save a new one."""
        key_hex = os.getenv("MNEMOSYNE_EVIDENCE_KEY")
        if not key_hex:
            # Generate a 32-byte (256-bit) key
            key_bytes = secrets.token_bytes(32)
            key_hex = key_bytes.hex()

            # Save to .env file for future use
            with open(".env", "a") as f:
                f.write(f"\nMNEMOSYNE_EVIDENCE_KEY={key_hex}\n")

            # Set in current environment
            os.environ["MNEMOSYNE_EVIDENCE_KEY"] = key_hex
            return key_bytes

        return bytes.fromhex(key_hex)

    async def initialize(self) -> None:
        """Initialize the SQLite database schema."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS evidence (
                    hash_id TEXT PRIMARY KEY,
                    encrypted_blob BLOB NOT NULL
                )
                """
            )
            await db.commit()

    async def store(self, data: bytes) -> str:
        """
        Store data in the database with encryption. Deduplicates based on hash.

        Args:
            data: The raw byte data to store

        Returns:
            The SHA-256 hash of the unencrypted data
        """
        hash_id = calculate_sha256(data)

        async with aiosqlite.connect(self.db_path) as db:
            # Check if it already exists (deduplication)
            async with db.execute("SELECT 1 FROM evidence WHERE hash_id = ?", (hash_id,)) as cursor:
                if await cursor.fetchone():
                    return hash_id

            # Encrypt the data
            nonce = secrets.token_bytes(self.nonce_size)
            ciphertext = self.aesgcm.encrypt(nonce, data, None)

            # Prepend nonce to ciphertext for storage
            encrypted_blob = nonce + ciphertext

            await db.execute(
                "INSERT INTO evidence (hash_id, encrypted_blob) VALUES (?, ?)",
                (hash_id, encrypted_blob),
            )
            await db.commit()

        return hash_id

    async def retrieve(self, hash_id: str) -> bytes:
        """
        Retrieve and decrypt data by its hash.

        Args:
            hash_id: The SHA-256 hash of the data

        Returns:
            The unencrypted byte data

        Raises:
            KeyError: If the hash is not found in the store
        """
        async with aiosqlite.connect(self.db_path) as db:
            query = "SELECT encrypted_blob FROM evidence WHERE hash_id = ?"
            async with db.execute(query, (hash_id,)) as cursor:
                row = await cursor.fetchone()

                if not row:
                    raise KeyError(f"Evidence with hash {hash_id} not found.")

                encrypted_blob = row[0]

        nonce = encrypted_blob[: self.nonce_size]
        ciphertext = encrypted_blob[self.nonce_size :]

        # Decrypt (will raise InvalidTag if tampered or wrong key)
        data = self.aesgcm.decrypt(nonce, ciphertext, None)
        return data
