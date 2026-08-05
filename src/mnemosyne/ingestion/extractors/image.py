import asyncio
import logging

# We import pytesseract, but we need to handle the case where the binary is missing gracefully
import pytesseract  # type: ignore
from PIL import Image
from pytesseract import TesseractNotFoundError

from .base import BaseExtractor

logger = logging.getLogger(__name__)


class ImageExtractor(BaseExtractor):
    """
    Extracts text from images using Tesseract OCR.
    """

    async def extract(self, file_path: str) -> str:
        def _extract_sync() -> str:
            try:
                img = Image.open(file_path)
                text = pytesseract.image_to_string(img)
                return str(text).strip()
            except TesseractNotFoundError:
                logger.warning(
                    "Tesseract binary is not installed or not in PATH. "
                    f"OCR text extraction for {file_path} failed gracefully."
                )
                return ""
            except Exception as e:
                logger.error(f"Failed to process image {file_path}: {e}")
                return ""

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _extract_sync)
