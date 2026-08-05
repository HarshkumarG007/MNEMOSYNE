import aiofiles

from .base import BaseExtractor


class TextExtractor(BaseExtractor):
    """
    Extracts text from plain text files.
    """

    async def extract(self, file_path: str) -> str:
        # Try UTF-8 first, fallback to latin-1
        try:
            async with aiofiles.open(file_path, mode="r", encoding="utf-8") as f:
                return await f.read()
        except UnicodeDecodeError:
            async with aiofiles.open(file_path, mode="r", encoding="latin-1") as f:
                return await f.read()
