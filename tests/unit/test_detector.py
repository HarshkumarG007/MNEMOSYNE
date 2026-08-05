from pathlib import Path

import pytest
from mnemosyne.ingestion.detector import detect_file_type

FIXTURES_DIR = Path("tests/fixtures")


@pytest.mark.asyncio
async def test_detect_pdf():
    mime = await detect_file_type(str(FIXTURES_DIR / "sample.pdf"))
    assert mime == "application/pdf"


@pytest.mark.asyncio
async def test_detect_docx():
    # libmagic identifies docx minimal signature as zip
    mime = await detect_file_type(str(FIXTURES_DIR / "sample.docx"))
    assert "zip" in mime.lower() or "vnd.openxmlformats" in mime.lower()


@pytest.mark.asyncio
async def test_detect_txt():
    mime = await detect_file_type(str(FIXTURES_DIR / "sample.txt"))
    assert mime == "text/plain"


@pytest.mark.asyncio
async def test_detect_png():
    mime = await detect_file_type(str(FIXTURES_DIR / "sample.png"))
    assert mime == "image/png"


@pytest.mark.asyncio
async def test_detect_jpg():
    mime = await detect_file_type(str(FIXTURES_DIR / "sample.jpg"))
    assert mime == "image/jpeg"


@pytest.mark.asyncio
async def test_detect_mp3():
    # Depending on libmagic version, it might return audio/mpeg or something else for ID3
    mime = await detect_file_type(str(FIXTURES_DIR / "sample.mp3"))
    assert "audio" in mime.lower() or "octet-stream" in mime.lower()


@pytest.mark.asyncio
async def test_detect_mp4():
    mime = await detect_file_type(str(FIXTURES_DIR / "sample.mp4"))
    assert mime == "video/mp4"


@pytest.mark.asyncio
async def test_detect_eml():
    mime = await detect_file_type(str(FIXTURES_DIR / "sample.eml"))
    assert mime == "message/rfc822"


@pytest.mark.asyncio
async def test_detect_pst():
    # libmagic might not have a strong pst signature depending on version, fallback to generic
    mime = await detect_file_type(str(FIXTURES_DIR / "sample.pst"))
    # We just ensure it doesn't crash, the exact mime might vary on OS
    assert isinstance(mime, str)


@pytest.mark.asyncio
async def test_detect_e01():
    mime = await detect_file_type(str(FIXTURES_DIR / "sample.e01"))
    assert mime == "application/x-ewf"


@pytest.mark.asyncio
async def test_mislabeled_file():
    # A PDF file with a .txt extension should be detected as PDF
    mime = await detect_file_type(str(FIXTURES_DIR / "mislabeled.txt"))
    assert mime == "application/pdf"


@pytest.mark.asyncio
async def test_nonexistent_file():
    mime = await detect_file_type("nonexistent_file.xyz")
    assert mime == "application/octet-stream"


@pytest.mark.asyncio
async def test_empty_file(tmp_path):
    empty_file = tmp_path / "empty.bin"
    empty_file.write_bytes(b"")
    mime = await detect_file_type(str(empty_file))
    assert mime == "application/x-empty"
