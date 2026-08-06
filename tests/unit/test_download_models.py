import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from scripts.download_models import verify_checksum  # noqa: E402


def test_verify_checksum() -> None:
    # Create a temporary file with known content
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"mnemosyne test content")
        temp_path = f.name

    try:
        # sha256 of "mnemosyne test content" is:
        expected_hash = "22f6e5db737470ca3d842b4c07d6375437a8258f17dda54c21d8edf2b3cc935c"
        assert verify_checksum(temp_path, expected_hash) is True

        # Test incorrect hash
        assert verify_checksum(temp_path, "wronghash") is False
    finally:
        os.unlink(temp_path)
