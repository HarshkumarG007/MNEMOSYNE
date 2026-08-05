import logging
from typing import Any, Dict, List

import spacy

logger = logging.getLogger(__name__)

# Global variable to cache the model so it's loaded only once
_nlp_model = None

# We map standard SpaCy labels to our simplified schema.
# You can extend this mapping based on domain requirements.
LABEL_MAP = {
    "PERSON": "PERSON",
    "ORG": "ORG",
    "GPE": "LOCATION",  # Geo-Political Entity -> LOCATION
    "LOC": "LOCATION",
    "DATE": "DATE",
    "TIME": "TIME",
    "MONEY": "MONEY",
    "FAC": "LOCATION",  # Facility
    "PRODUCT": "PRODUCT",
    "EVENT": "EVENT",
}


def get_model() -> Any:
    """
    Lazy load the SpaCy en_core_web_sm model.
    """
    global _nlp_model
    if _nlp_model is None:
        try:
            _nlp_model = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning(
                "SpaCy model 'en_core_web_sm' not found. "
                "Attempting to download it dynamically. "
                "For production, please pre-install it using: "
                "python -m spacy download en_core_web_sm"
            )
            spacy.cli.download("en_core_web_sm")  # type: ignore
            _nlp_model = spacy.load("en_core_web_sm")
    return _nlp_model


def extract_entities(text: str) -> List[Dict[str, str]]:
    """
    Extract named entities from raw text using SpaCy.

    Args:
        text: The raw text string.

    Returns:
        A list of dictionaries representing entities:
        [
            {
                "id": "normalized_name",
                "type": "MAPPED_TYPE",
                "name": "Original Name"
            },
            ...
        ]
    """
    if not text.strip():
        return []

    nlp = get_model()
    doc = nlp(text)

    entities = []
    # Use a set to track already processed normalized IDs to avoid immediate duplicates
    seen = set()

    for ent in doc.ents:
        spacy_label = ent.label_
        if spacy_label in LABEL_MAP:
            mapped_type = LABEL_MAP[spacy_label]
            name = ent.text.strip()

            # Very basic normalization for ID generation:
            # lowercase, replace spaces with underscores, strip punctuation
            normalized_id = "".join(c.lower() if c.isalnum() else "_" for c in name).strip("_")

            # Consolidate multiple underscores
            import re

            normalized_id = re.sub(r"_+", "_", normalized_id)

            if not normalized_id:
                continue

            # Create unique key based on id AND type, because "Washington"
            # might be a PERSON or a LOCATION
            unique_key = f"{mapped_type}::{normalized_id}"

            if unique_key not in seen:
                seen.add(unique_key)
                entities.append({"id": normalized_id, "type": mapped_type, "name": name})

    return entities
