"""
Utility functions for hashing data.
"""
import hashlib


def calculate_sha256(data: bytes) -> str:
    """
    Calculate the SHA-256 hash of a byte string.

    Args:
        data: The byte string to hash

    Returns:
        The hex digest of the hash
    """
    hasher = hashlib.sha256()
    hasher.update(data)
    return hasher.hexdigest()
