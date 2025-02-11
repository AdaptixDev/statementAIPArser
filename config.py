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
    REQUEST_TIMEOUT: Final = 360  # Increased timeout for image processing

    # Supported image formats
    SUPPORTED_IMAGE_FORMATS: Final = ('.png', '.jpg', '.jpeg', '.gif', '.webp',
                                      '.JPG', '.JPEG')

    # Maximum file size in bytes (100MB)
    MAX_FILE_SIZE: Final = 100 * 1024 * 1024

    # Model to use for vision tasks
    VISION_MODEL: Final = "gpt-4o"  # Latest model with vision capabilities
    
    # Image compression settings
    USE_IMAGE_COMPRESSION: Final = False  # Whether to compress images before upload
    MAX_IMAGE_SIZE_MB: Final = 4  # Maximum image size in MB when compression is enabled
    MIN_COMPRESSION_QUALITY: Final = 5  # Minimum compression quality (1-100)
    INITIAL_COMPRESSION_QUALITY: Final = 95  # Initial compression quality (1-100)
