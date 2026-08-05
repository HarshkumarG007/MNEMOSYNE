"""
Merkle tree implementation for verifying evidence integrity.
"""
from typing import List, Optional

from .hashing import calculate_sha256


class MerkleTree:
    """A simple Merkle tree for cryptographic verification of inclusion."""

    def __init__(self, leaves: List[str]):
        """
        Initialize the Merkle tree with a list of leaf hashes (e.g. from EvidenceStore).

        Args:
            leaves: A list of SHA-256 hashes representing the evidence
        """
        self.leaves = leaves
        self.tree: List[List[str]] = []
        self._build_tree()

    def _build_tree(self) -> None:
        """Build the Merkle tree from the leaves."""
        if not self.leaves:
            self.tree = [[]]
            return

        current_level = list(self.leaves)
        self.tree.append(current_level)

        while len(current_level) > 1:
            next_level = []

            # Process pairs of nodes
            for i in range(0, len(current_level), 2):
                left = current_level[i]

                # If there's an odd number of nodes, duplicate the last one
                right = current_level[i + 1] if (i + 1) < len(current_level) else left

                # Combine left and right hashes and hash the result
                combined = left + right
                parent_hash = calculate_sha256(combined.encode("utf-8"))

                next_level.append(parent_hash)

            self.tree.append(next_level)
            current_level = next_level

    @property
    def root(self) -> Optional[str]:
        """Get the root hash of the Merkle tree."""
        if not self.tree or not self.tree[-1]:
            return None
        return self.tree[-1][0]

    def get_proof(self, index: int) -> List[str]:
        """
        Generate an inclusion proof for a leaf at a given index.

        Args:
            index: The index of the leaf in the original leaves list.

        Returns:
            A list of sibling hashes needed to reconstruct the root hash.
        """
        if index < 0 or index >= len(self.leaves):
            raise IndexError("Leaf index out of bounds")

        proof = []
        current_index = index

        # Traverse up the tree, excluding the root level
        for level in self.tree[:-1]:
            is_right_node = current_index % 2 == 1

            if is_right_node:
                sibling_index = current_index - 1
            else:
                # Handle odd number of nodes by duplicating the last node
                sibling_index = min(current_index + 1, len(level) - 1)

            proof.append(level[sibling_index])
            current_index //= 2

        return proof

    @staticmethod
    def verify_proof(leaf: str, index: int, proof: List[str], root: str) -> bool:
        """
        Verify an inclusion proof.

        Args:
            leaf: The hash of the leaf to verify
            index: The original index of the leaf
            proof: The list of sibling hashes
            root: The expected root hash

        Returns:
            True if the proof is valid, False otherwise
        """
        current_hash = leaf
        current_index = index

        for sibling_hash in proof:
            is_right_node = current_index % 2 == 1

            if is_right_node:
                combined = sibling_hash + current_hash
            else:
                combined = current_hash + sibling_hash

            current_hash = calculate_sha256(combined.encode("utf-8"))
            current_index //= 2

        return current_hash == root
