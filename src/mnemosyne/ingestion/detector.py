"""
File type detection based on magic numbers (content) rather than extensions.
"""
import os

import aiofiles
import magic

# Common extensions to MIME mapping fallback (for reference/validation)
SUPPORTED_EXTENSIONS = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".txt": "text/plain",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".mp3": "audio/mpeg",
    ".mp4": "video/mp4",
    ".eml": "message/rfc822",
    ".pst": "application/vnd.ms-outlook",
    ".e01": "application/x-ewf",
}

# Number of bytes to read for magic number detection
MAGIC_BYTES_SIZE = 2048


async def detect_file_type(path: str) -> str:
    """
    Detect the MIME type of a file based on its content (magic numbers).
    Trusts content over extension.

    Args:
        path: Path to the file to detect.

    Returns:
        The detected MIME type as a string.
    """
    if not os.path.exists(path):
        return "application/octet-stream"

    try:
        # Read a chunk of the file asynchronously
        async with aiofiles.open(path, mode="rb") as f:
            chunk = await f.read(MAGIC_BYTES_SIZE)

        if not chunk:
            return "application/x-empty"

        # Check for E01 Forensic Image format manually since libmagic doesn't reliably identify it
        if chunk.startswith(b"EVF\x09"):
            return "application/x-ewf"

        # Use python-magic to determine MIME type from buffer
        mime_type = magic.from_buffer(chunk, mime=True)

        # If magic returns a generic type, check if it's an EML or similar text format
        if mime_type == "text/plain":
            # Very basic EML heuristic if libmagic just says text/plain
            if b"From:" in chunk and b"To:" in chunk and b"Date:" in chunk:
                return "message/rfc822"
        elif mime_type == "application/octet-stream":
            # Fallback for ZIP / Office documents if libmagic fails (common on Windows)
            if chunk.startswith(b"PK\x03\x04"):
                # We return generic zip, higher level logic would need to inspect the zip contents
                # to differentiate docx/xlsx, but for now zip is sufficient to route
                # to DOCX extractor
                return "application/zip"

        return mime_type

    except Exception as e:
        print(f"Exception: {e}")
        # Graceful fallback on error
        return "application/octet-stream"
