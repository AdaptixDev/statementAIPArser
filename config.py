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
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your_api_key")
    if not OPENAI_API_KEY:
        print("Debug: Environment variables loaded:", dict(os.environ))
        raise ValueError("OPENAI_API_KEY environment variable is not set")

    # Assistant ID from environment variable
    ASSISTANT_ID = os.getenv("ASSISTANT_ID", "your_default_assistant_id")
    if not ASSISTANT_ID:
        raise ValueError("ASSISTANT_ID environment variable is not set")

    # Personal Info Assistant ID from environment variable
    PERSONAL_INFO_ASSISTANT_ID = os.getenv("PERSONAL_INFO_ASSISTANT_ID", "your_personal_info_assistant_id")

    # API request timeout in seconds (increased for vision processing)
    REQUEST_TIMEOUT = 60  # Timeout in seconds

    # Supported image formats
    SUPPORTED_IMAGE_FORMATS = [".jpg", ".jpeg", ".png"]

    # Maximum file size in bytes (100MB)
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 5242880))  # Default: 5MB
    
    # Image compression settings
    USE_IMAGE_COMPRESSION = True  # Whether to compress images before upload
    MAX_IMAGE_SIZE_MB = 5  # Maximum image size in MB when compression is enabled
    MIN_COMPRESSION_QUALITY = 20  # Minimum compression quality (1-100)
    INITIAL_COMPRESSION_QUALITY = 90  # Initial compression quality (1-100)

    # Maximum number of concurrent requests
    MAX_CONCURRENT_REQUESTS = 6
