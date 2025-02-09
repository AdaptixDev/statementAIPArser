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

    # API request timeout in seconds (increased for vision processing)
    REQUEST_TIMEOUT: Final = 120  # Increased timeout for image processing

    # Supported image formats
    SUPPORTED_IMAGE_FORMATS: Final = ('.png', '.jpg', '.jpeg', '.gif', '.webp')

    # Maximum file size in bytes (100MB)
    MAX_FILE_SIZE: Final = 100 * 1024 * 1024

    # Model to use for vision tasks
    VISION_MODEL: Final = "gpt-4o"  # Latest model with vision capabilities