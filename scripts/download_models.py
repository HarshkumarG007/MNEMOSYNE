import hashlib
import os
from typing import Dict

from huggingface_hub import hf_hub_download

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")

# We will define a dict of our required models and their HuggingFace GGUF paths
REQUIRED_MODELS: Dict[str, Dict[str, str]] = {
    "mistral-7b": {
        "repo_id": "MaziyarPanahi/Mistral-7B-Instruct-v0.3-GGUF",
        "filename": "Mistral-7B-Instruct-v0.3.Q4_K_M.gguf",
    },
    "llama-3.1-8b": {
        "repo_id": "lmstudio-community/Meta-Llama-3.1-8B-Instruct-GGUF",
        "filename": "Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf",
    },
    "phi-3-mini": {
        "repo_id": "microsoft/Phi-3-mini-4k-instruct-gguf",
        "filename": "Phi-3-mini-4k-instruct-q4.gguf",
    },
    "bge-m3": {"repo_id": "aari1995/BGE-M3-GGUF", "filename": "bge-m3-q4_k_m.gguf"},
}


def verify_checksum(filepath: str, expected_hash: str) -> bool:
    """Verifies the SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest() == expected_hash


def download_models() -> None:
    """Downloads all required GGUF models into the models/ directory."""
    os.makedirs(MODELS_DIR, exist_ok=True)

    print(f"Downloading models to {MODELS_DIR}...")

    for model_name, info in REQUIRED_MODELS.items():
        repo_id = info["repo_id"]
        filename = info["filename"]

        print(f"\nProcessing {model_name}...")
        print(f"Repo: {repo_id}")
        print(f"File: {filename}")

        try:
            # hf_hub_download automatically handles resumable partial downloads
            # and caches them locally. We will move/symlink it to our models dir.
            downloaded_path = hf_hub_download(
                repo_id=repo_id,
                filename=filename,
                local_dir=MODELS_DIR,
                local_dir_use_symlinks=False,
            )
            print(f"Successfully downloaded {model_name} to {downloaded_path}")
        except Exception as e:
            print(f"Error downloading {model_name}: {e}")


if __name__ == "__main__":
    download_models()
