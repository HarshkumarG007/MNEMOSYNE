import asyncio

import docx

from .base import BaseExtractor


class DocxExtractor(BaseExtractor):
    """
    Extracts text from DOCX files using python-docx.
    """

    async def extract(self, file_path: str) -> str:
        def _extract_sync() -> str:
            doc = docx.Document(file_path)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            return "\n".join(paragraphs)

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _extract_sync)
