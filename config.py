"""Configuration settings for the OpenAI Assistant application."""

import os
from typing import Final

# Configuration class to store API settings
class Config:
    # OpenAI API Key from environment variable
    OPENAI_API_KEY: Final = os.getenv('OPENAI_API_KEY')
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY environment variable is not set")

    # Assistant ID from environment variable
    ASSISTANT_ID: Final = os.getenv('ASSISTANT_ID')
    if not ASSISTANT_ID:
        raise ValueError("ASSISTANT_ID environment variable is not set")

    # API request timeout in seconds
    REQUEST_TIMEOUT: Final = 30

    # Supported image formats
    SUPPORTED_IMAGE_FORMATS: Final = ('.png', '.jpg', '.jpeg', '.gif', '.webp')

    # Maximum file size in bytes (100MB)
    MAX_FILE_SIZE: Final = 100 * 1024 * 1024