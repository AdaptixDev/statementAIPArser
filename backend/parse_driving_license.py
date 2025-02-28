#!/usr/bin/env python3
"""
Script to test the driving license parser.
"""

import os
import sys
import json
import argparse
import logging

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.src.services.driving_license_service import DrivingLicenseService
from backend.src.utils.logging_utils import setup_logger

# Set up logging
logger = setup_logger("driving_license_parser", level=logging.INFO)

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Parse driving license images using Gemini.")
    parser.add_argument("--image", type=str, help="Path to the driving license image to process")
    parser.add_argument("--output", type=str, help="Path to save the output JSON file")
    
    args = parser.parse_args()
    
    # Use default image path if not provided
    image_path = args.image if args.image else "C:\\Users\\cbyro\\OneDrive\\cursorWorkspace\\statementAIParser\\backend\\data\\DLCHRIS.jpg"
    
    # Check if the image file exists
    if not os.path.exists(image_path):
        logger.error(f"Image file not found: {image_path}")
        return
    
    # Set default output file if not provided
    output_file = args.output if args.output else os.path.join(os.path.dirname(image_path), "driving_license_info.json")
    
    # Create the output directory if it doesn't exist
    output_dir = os.path.dirname(output_file)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    try:
        # Initialize the driving license service
        service = DrivingLicenseService()
        
        # Parse the driving license image
        logger.info(f"Parsing driving license image: {image_path}")
        result = service.parse_driving_license(image_path)
        
        # Print the result
        logger.info("Parsing result:")
        print(json.dumps(result, indent=2))
        
        # Save the result to a JSON file
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2)
        logger.info(f"Result saved to: {output_file}")
        
    except Exception as e:
        logger.error(f"Error parsing driving license: {str(e)}")

if __name__ == "__main__":
    main() 