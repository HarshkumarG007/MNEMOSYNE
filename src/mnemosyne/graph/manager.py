import logging
from pathlib import Path
from typing import Any, Dict

from mnemosyne.evidence.store import EvidenceStore
from mnemosyne.graph.memgraph_client import MemgraphClient
from mnemosyne.graph.nlp import extract_entities
from mnemosyne.ingestion.detector import detect_file_type
from mnemosyne.ingestion.extractors.registry import ExtractorRegistry, UnsupportedFormatError

logger = logging.getLogger(__name__)


class GraphIngestionManager:
    """
    Orchestrates the ingestion pipeline:
    File -> Detection -> Evidence Store -> Text Extraction -> NLP -> Graph Database.
    """

    def __init__(self, memgraph_client: MemgraphClient, evidence_store: EvidenceStore):
        self.memgraph = memgraph_client
        self.evidence_store = evidence_store

    async def process_file(self, file_path: str) -> Dict[str, Any]:
        """
        Process a file completely through the pipeline.

        Args:
            file_path: Absolute or relative path to the file to ingest.

        Returns:
            A dictionary containing the results of the ingestion (e.g. evidence hash, entity count).
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        logger.info(f"Starting ingestion for file: {file_path}")

        # 1. Detect File Type
        mime_type = await detect_file_type(str(path))
        logger.info(f"Detected MIME type: {mime_type}")

        # 2. Store in EvidenceStore
        with open(path, "rb") as f:
            file_data = f.read()

        evidence_hash = await self.evidence_store.store(file_data)
        logger.info(f"Stored evidence securely with hash: {evidence_hash}")

        # 3. Create Evidence Node in Graph
        await self.memgraph.create_evidence(evidence_hash, mime_type)
        logger.info("Created Evidence node in Graph")

        # 4. Extract Text
        try:
            extractor = ExtractorRegistry.get_extractor(mime_type)
            text = await extractor.extract(str(path))
        except UnsupportedFormatError:
            logger.warning(f"No text extractor available for {mime_type}. Stopping NLP extraction.")
            text = ""
        except Exception as e:
            logger.error(f"Text extraction failed for {file_path}: {e}")
            text = ""

        # 5. Entity Extraction (NLP)
        entities = extract_entities(text) if text else []
        logger.info(f"Extracted {len(entities)} entities via NLP")

        # 6. Graph Storage (Entities and Relationships)
        for entity in entities:
            # Create/Merge the entity node
            await self.memgraph.create_entity(
                entity["id"], entity["type"], {"name": entity["name"]}
            )
            # Link it to the evidence
            await self.memgraph.create_extracted_from_relationship(entity["id"], evidence_hash)

        return {
            "evidence_hash": evidence_hash,
            "mime_type": mime_type,
            "entity_count": len(entities),
        }
