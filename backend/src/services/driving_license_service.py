#!/usr/bin/env python3
"""
Integration with Gemini 2.0 for processing driving license images.
This module provides functionality to extract information from driving license images.
"""

import os
import time
import json
import logging
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types
import tempfile
import shutil

# Import prompts from the core module
from backend.src.core.prompts import GEMINI_DRIVING_LICENCE_PARSE

# Configure logging
logger = logging.getLogger(__name__)

class DrivingLicenseService:
    """
    Service for processing driving license images with Gemini.
    """
    
    def __init__(self):
        """Initialize the Gemini service with API credentials."""
        # Load environment variables
        load_dotenv()
        
        # Get API key
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")
            
        # Initialize Gemini client
        self.client = genai.Client(api_key=self.api_key)
        logger.info("Gemini client initialized successfully for driving license processing")
    
    def upload_file_to_gemini(self, file_path: str) -> object:
        """
        Uploads a file to Gemini and returns the file object.
        
        Args:
            file_path: Path to the file to upload
            
        Returns:
            The uploaded file object
        """
        logger.info(f"Uploading file \"{file_path}\" to Gemini...")
        
        # Upload the file to Gemini
        file_obj = self.client.files.upload(file=file_path)
        logger.info(f"Uploaded file '{file_obj.display_name}' as: {file_obj.uri}")
        
        return file_obj
    
    def wait_for_file_active(self, file_obj: object) -> None:
        """
        Waits for the given file to be active (state=ACTIVE).
        Raises an exception if the file fails to become ACTIVE.
        
        Args:
            file_obj: File object to wait for
        """
        logger.info("Waiting for file to become ACTIVE in Gemini...")
        current_file = self.client.files.get(name=file_obj.name)
        while current_file.state.name == "PROCESSING":
            logger.info("...still processing, waiting 5 seconds...")
            time.sleep(5)
            current_file = self.client.files.get(name=file_obj.name)
        if current_file.state.name != "ACTIVE":
            raise Exception(
                f"File {current_file.name} failed to process. "
                f"Current state: {current_file.state.name}"
            )
        logger.info("File is now ACTIVE")
    
    def parse_driving_license(self, image_path: str) -> dict:
        """
        Parse a driving license image and extract information.
        
        Args:
            image_path: Path to the driving license image
            
        Returns:
            Dictionary containing the extracted information
        """
        logger.info(f"Parsing driving license image: {image_path}")
        
        try:
            # Upload the image to Gemini
            file_obj = self.upload_file_to_gemini(image_path)
            
            # Wait for the file to be active
            self.wait_for_file_active(file_obj)
            
            # Generate content using Gemini with the driving license prompt
            logger.info("Sending prompt with image to Gemini...")
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[GEMINI_DRIVING_LICENCE_PARSE, file_obj],
                config=types.GenerateContentConfig(max_output_tokens=4000),
            )
            
            # Extract the JSON response
            response_text = response.text
            logger.debug(f"Response from Gemini: {response_text}")
            
            # Try to parse the response as JSON
            try:
                # Find JSON content in the response (it might be wrapped in markdown code blocks)
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_content = response_text[json_start:json_end]
                    result = json.loads(json_content)
                    logger.info("Successfully parsed driving license information as JSON")
                    return result
                else:
                    logger.warning("No JSON content found in the response")
                    return {"raw_response": response_text}
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse response as JSON: {str(e)}")
                return {"raw_response": response_text}
            
        except Exception as e:
            logger.exception(f"Error parsing driving license: {str(e)}")
            raise Exception(f"Error parsing driving license: {str(e)}") 