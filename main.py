
"""Main entry point for the OpenAI Assistant application."""

import sys
import os
from config import Config
from assistant_client import AssistantClient
from exceptions import (
    AssistantError,
    FileUploadError,
    ImageValidationError,
    ThreadCreationError,
    MessageCreationError,
    ResponseTimeoutError
)

def process_directory(directory_path: str, client: AssistantClient) -> None:
    """Process all supported images in a directory."""
    supported_extensions = Config.SUPPORTED_IMAGE_FORMATS
    
    # Get list of image files
    image_files = [
        f for f in os.listdir(directory_path)
        if os.path.isfile(os.path.join(directory_path, f))
        and os.path.splitext(f)[1].lower() in supported_extensions
    ]
    
    if not image_files:
        print(f"No supported image files found in {directory_path}")
        return
        
    print(f"Found {len(image_files)} images to process")
    
    # Process each image
    for image_file in image_files:
        image_path = os.path.join(directory_path, image_file)
        print(f"\nProcessing image: {image_file}")
        try:
            prompt = "Please analyze this image and provide a detailed description."
            response = client.process_image(image_path, prompt)
            print(f"Successfully processed {image_file}")
        except AssistantError as e:
            print(f"Error processing {image_file}: {str(e)}")
            continue
        except Exception as e:
            print(f"Unexpected error processing {image_file}: {str(e)}")
            continue

def main():
    """Main function to run the assistant."""
    
    # Check for command line arguments
    if len(sys.argv) != 2:
        print("Usage: python main.py <directory_path>")
        sys.exit(1)
    
    directory_path = sys.argv[1]
    
    # Verify directory exists
    if not os.path.isdir(directory_path):
        print(f"Error: {directory_path} is not a valid directory")
        sys.exit(1)
    
    try:
        # Initialize the assistant client
        client = AssistantClient(
            api_key=Config.OPENAI_API_KEY,
            assistant_id=Config.ASSISTANT_ID
        )
        
        # Process all images in directory
        process_directory(directory_path, client)
        
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
