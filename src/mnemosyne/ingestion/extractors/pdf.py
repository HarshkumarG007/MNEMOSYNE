import asyncio

import pypdf

from .base import BaseExtractor


class PDFExtractor(BaseExtractor):
    """
    Extracts text from PDF documents using pypdf.
    """

    async def extract(self, file_path: str) -> str:
        # pypdf doesn't natively support async, wrap in thread
        def _extract_sync() -> str:
            text_chunks = []
            with open(file_path, "rb") as f:
                reader = pypdf.PdfReader(f)
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        text_chunks.append(text)
            return "\n".join(text_chunks)

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _extract_sync)
