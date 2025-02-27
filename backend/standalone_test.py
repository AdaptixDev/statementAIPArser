#!/usr/bin/env python3
"""
Standalone script to test the Gemini API directly.
"""

import os
import sys
import logging
import json
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Check for the Gemini API key
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logger.error("GEMINI_API_KEY is not set in the environment.")
    sys.exit(1)

def main():
    """Test the Gemini API directly."""
    try:
        # Initialize the Gemini client
        logger.info("Initializing Gemini client...")
        client = genai.Client(api_key=GEMINI_API_KEY)
        logger.info("Gemini client initialized successfully.")
        
        # Test a simple prompt
        logger.info("Testing a simple prompt...")
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=["Hello, Gemini! Please analyze this statement: 'The sky is blue.'"],
            config=types.GenerateContentConfig(max_output_tokens=400000),
        )
        logger.info(f"Response: {response.text}")
        
        logger.info("Test completed successfully.")
    
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 