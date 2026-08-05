from abc import ABC, abstractmethod


class BaseExtractor(ABC):
    """
    Abstract base class for all text extractors.
    """

    @abstractmethod
    async def extract(self, file_path: str) -> str:
        """
        Extract raw text from a document.

        Args:
            file_path: Absolute or relative path to the file.

        Returns:
            The extracted plain text.

        Raises:
            Exception: If extraction fails or file is unreadable.
        """
        pass
