"""Configuration settings for the OpenAI Assistant application."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from typing import Final

# Get the absolute path to the directory containing this script
current_dir = Path(__file__).parent.absolute()

# Try to load .env from the current directory
env_path = current_dir / '.env'
if not env_path.exists():
    # If not found, try parent directory
    env_path = current_dir.parent / '.env'

if not env_path.exists():
    print(f"Warning: .env file not found in {current_dir} or its parent directory")
else:
    print(f"Loading .env from: {env_path}")
    load_dotenv(env_path)

# Configuration class to store API settings
class Config:
    # OpenAI API Key from environment variable
    OPENAI_API_KEY: Final = os.getenv('OPENAI_API_KEY')
    if not OPENAI_API_KEY:
        print("Debug: Environment variables loaded:", dict(os.environ))
        raise ValueError("OPENAI_API_KEY environment variable is not set")

    # Assistant ID from environment variable
    ASSISTANT_ID: Final = os.getenv('ASSISTANT_ID')
    if not ASSISTANT_ID:
        raise ValueError("ASSISTANT_ID environment variable is not set")

    # API request timeout in seconds (increased for vision processing)
    REQUEST_TIMEOUT: Final = 600  # 10 minutes timeout for image processing

    # Supported image formats
    SUPPORTED_IMAGE_FORMATS: Final = ('.png', '.jpg', '.jpeg', '.gif', '.webp',
                                      '.JPG', '.JPEG')

    # Maximum file size in bytes (100MB)
    MAX_FILE_SIZE: Final = 100 * 1024 * 1024
    
    # Image compression settings
    USE_IMAGE_COMPRESSION: Final = True  # Whether to compress images before upload
    MAX_IMAGE_SIZE_MB: Final = 2  # Maximum image size in MB when compression is enabled
    MIN_COMPRESSION_QUALITY: Final = 20  # Minimum compression quality (1-100)
    INITIAL_COMPRESSION_QUALITY: Final = 80  # Initial compression quality (1-100)

    # Maximum number of concurrent requests
    MAX_CONCURRENT_REQUESTS: Final = 6
