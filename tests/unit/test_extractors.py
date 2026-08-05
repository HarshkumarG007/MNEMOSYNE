from pathlib import Path

import pytest
from mnemosyne.ingestion.extractors.docx import DocxExtractor
from mnemosyne.ingestion.extractors.pdf import PDFExtractor
from mnemosyne.ingestion.extractors.registry import ExtractorRegistry, UnsupportedFormatError
from mnemosyne.ingestion.extractors.txt import TextExtractor

FIXTURES_DIR = Path("tests/fixtures")


@pytest.mark.asyncio
async def test_pdf_extraction() -> None:
    extractor = PDFExtractor()
    text = await extractor.extract(str(FIXTURES_DIR / "sample.pdf"))
    assert "Hello MNEMOSYNE PDF" in text


@pytest.mark.asyncio
async def test_docx_extraction() -> None:
    extractor = DocxExtractor()
    text = await extractor.extract(str(FIXTURES_DIR / "sample.docx"))
    assert "Hello MNEMOSYNE DOCX" in text


@pytest.mark.asyncio
async def test_txt_extraction() -> None:
    extractor = TextExtractor()
    text = await extractor.extract(str(FIXTURES_DIR / "sample.txt"))
    assert "This is a plain text file." in text


def test_registry_resolution() -> None:
    pdf_ext = ExtractorRegistry.get_extractor("application/pdf")
    assert isinstance(pdf_ext, PDFExtractor)

    docx_mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    docx_ext = ExtractorRegistry.get_extractor(docx_mime)
    assert isinstance(docx_ext, DocxExtractor)

    txt_ext = ExtractorRegistry.get_extractor("text/plain")
    assert isinstance(txt_ext, TextExtractor)


def test_registry_unsupported() -> None:
    with pytest.raises(UnsupportedFormatError):
        ExtractorRegistry.get_extractor("application/x-made-up-format")
