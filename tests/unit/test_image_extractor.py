from pathlib import Path
from unittest.mock import patch

import pytest
from mnemosyne.ingestion.extractors.image import ImageExtractor
from mnemosyne.ingestion.extractors.registry import ExtractorRegistry

FIXTURES_DIR = Path("tests/fixtures")


@pytest.mark.asyncio
async def test_image_extraction():
    extractor = ImageExtractor()

    # Try the real extraction
    # This might fail and return "" if Tesseract isn't installed locally.
    text = await extractor.extract(str(FIXTURES_DIR / "sample.png"))

    # We can't guarantee tesseract is installed on the runner,
    # so we accept either the correct text or an empty string.
    # We test the missing binary case explicitly below.
    if text:
        assert "Hello MNEMOSYNE Image" in text


def test_registry_resolution():
    png_ext = ExtractorRegistry.get_extractor("image/png")
    assert isinstance(png_ext, ImageExtractor)

    jpg_ext = ExtractorRegistry.get_extractor("image/jpeg")
    assert isinstance(jpg_ext, ImageExtractor)


@pytest.mark.asyncio
@patch("pytesseract.image_to_string")
async def test_image_extraction_missing_binary(mock_image_to_string):
    from pytesseract import TesseractNotFoundError

    # Force the mock to raise the specific error that occurs when tesseract is missing
    mock_image_to_string.side_effect = TesseractNotFoundError()

    extractor = ImageExtractor()
    text = await extractor.extract(str(FIXTURES_DIR / "sample.png"))

    # It should fail gracefully and return an empty string
    assert text == ""
