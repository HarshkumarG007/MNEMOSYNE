import bleach  # type: ignore
from pydantic import BaseModel, field_validator

# LLM delimiters that are forbidden in user text
# To prevent prompt injection
FORBIDDEN_DELIMITERS = ["<|im_start|>", "<|im_end|>", "[INST]", "[/INST]", "System:", "User:", "Assistant:"]


class SecureRequestModel(BaseModel):
    """Base Pydantic model for input validation across the API."""

    @classmethod
    def check_prompt_injection(cls, value: str) -> str:
        """Validates that text destined for LLMs contains no structural delimiters."""
        for delimiter in FORBIDDEN_DELIMITERS:
            if delimiter.lower() in value.lower():
                raise ValueError("Potential prompt injection detected. Forbidden delimiter used.")
        return value

    @classmethod
    def sanitize_html(cls, value: str) -> str:
        """Strips all HTML tags from the input."""
        return bleach.clean(value, tags=[], attributes={}, strip=True)  # type: ignore

    @classmethod
    def check_path_traversal(cls, value: str) -> str:
        """Ensures the path does not attempt to escape its directory."""
        if ".." in value or value.startswith("/") or "\\" in value:
            raise ValueError(f"Path traversal attempt detected in path: {value}")
        return value


class UserTextInput(SecureRequestModel):
    """Model for text provided by a user."""

    text: str

    @field_validator("text")
    def validate_text(cls, v: str) -> str:
        if len(v) > 100_000:
            raise ValueError("Text exceeds maximum allowed length of 100,000 characters.")
        v = cls.sanitize_html(v)
        v = cls.check_prompt_injection(v)
        return v


class FilePathInput(SecureRequestModel):
    """Model for file paths provided via API."""

    file_path: str

    @field_validator("file_path")
    def validate_file_path(cls, v: str) -> str:
        return cls.check_path_traversal(v)
