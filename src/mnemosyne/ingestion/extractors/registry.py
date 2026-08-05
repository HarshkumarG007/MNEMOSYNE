from typing import Dict, Type

from .base import BaseExtractor
from .docx import DocxExtractor
from .image import ImageExtractor
from .pdf import PDFExtractor
from .txt import TextExtractor


class UnsupportedFormatError(Exception):
    """Exception raised when a requested MIME type is not supported."""

    pass


class ExtractorRegistry:
    """
    Registry for text extractors based on MIME type.
    """

    _registry: Dict[str, Type[BaseExtractor]] = {
        "application/pdf": PDFExtractor,
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": DocxExtractor,
        "text/plain": TextExtractor,
        "image/png": ImageExtractor,
        "image/jpeg": ImageExtractor,
        # Add aliases or common fallbacks if needed
        "application/msword": DocxExtractor,  # Older DOC not fully supported by docx, but we can try
        "application/zip": DocxExtractor,  # Fallback for DOCX on Windows
    }

    @classmethod
    def get_extractor(cls, mime_type: str) -> BaseExtractor:
        """
        Get the appropriate text extractor for a MIME type.

        Args:
            mime_type: The detected MIME type of the file.

        Returns:
            An instantiated Extractor object.

        Raises:
            UnsupportedFormatError: If no extractor is registered for the MIME type.
        """
        extractor_cls = cls._registry.get(mime_type)
        if not extractor_cls:
            raise UnsupportedFormatError(f"No text extractor available for MIME type: {mime_type}")

        return extractor_cls()
