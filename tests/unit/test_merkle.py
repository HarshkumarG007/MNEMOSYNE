import pytest
from mnemosyne.evidence.hashing import calculate_sha256
from mnemosyne.evidence.merkle import MerkleTree


def test_empty_tree() -> None:
    tree = MerkleTree([])
    assert tree.root is None


def test_single_leaf_tree() -> None:
    leaf = calculate_sha256(b"Leaf 1")
    tree = MerkleTree([leaf])

    assert tree.root is not None
    # Root of a single leaf tree is just the leaf itself in our implementation
    expected_root = leaf
    assert tree.root == expected_root


def test_even_leaves_tree() -> None:
    leaf1 = calculate_sha256(b"Leaf 1")
    leaf2 = calculate_sha256(b"Leaf 2")

    tree = MerkleTree([leaf1, leaf2])

    expected_root = calculate_sha256((leaf1 + leaf2).encode("utf-8"))
    assert tree.root == expected_root


def test_odd_leaves_tree() -> None:
    leaf1 = calculate_sha256(b"Leaf 1")
    leaf2 = calculate_sha256(b"Leaf 2")
    leaf3 = calculate_sha256(b"Leaf 3")

    tree = MerkleTree([leaf1, leaf2, leaf3])

    # leaf1 + leaf2 -> node_a
    # leaf3 + leaf3 -> node_b
    # node_a + node_b -> root
    node_a = calculate_sha256((leaf1 + leaf2).encode("utf-8"))
    node_b = calculate_sha256((leaf3 + leaf3).encode("utf-8"))
    expected_root = calculate_sha256((node_a + node_b).encode("utf-8"))

    assert tree.root == expected_root


def test_inclusion_proof_valid() -> None:
    leaves = [calculate_sha256(f"Leaf {i}".encode("utf-8")) for i in range(8)]
    tree = MerkleTree(leaves)

    # Test proof for leaf at index 3
    index = 3
    leaf = leaves[index]
    proof = tree.get_proof(index)

    assert MerkleTree.verify_proof(leaf, index, proof, tree.root)


def test_inclusion_proof_invalid_leaf() -> None:
    leaves = [calculate_sha256(f"Leaf {i}".encode("utf-8")) for i in range(8)]
    tree = MerkleTree(leaves)

    index = 3
    # Use a tampered leaf
    tampered_leaf = calculate_sha256(b"Tampered Data")
    proof = tree.get_proof(index)

    assert not MerkleTree.verify_proof(tampered_leaf, index, proof, tree.root)


def test_inclusion_proof_invalid_proof() -> None:
    leaves = [calculate_sha256(f"Leaf {i}".encode("utf-8")) for i in range(8)]
    tree = MerkleTree(leaves)

    index = 3
    leaf = leaves[index]
    proof = tree.get_proof(index)

    # Tamper with the proof
    proof[0] = calculate_sha256(b"Tampered Proof Element")

    assert not MerkleTree.verify_proof(leaf, index, proof, tree.root)


def test_inclusion_proof_invalid_index() -> None:
    leaves = [calculate_sha256(f"Leaf {i}".encode("utf-8")) for i in range(8)]
    tree = MerkleTree(leaves)

    with pytest.raises(IndexError):
        tree.get_proof(10)
