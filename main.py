
"""Main entry point for the OpenAI Assistant application."""

import sys
import os
import concurrent.futures
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

def process_single_image(image_path: str, client: AssistantClient) -> None:
    """Process a single image file."""
    try:
        print(f"\nProcessing image: {os.path.basename(image_path)}")
        prompt = "Please analyze this image and provide a detailed description."
        response = client.process_image(image_path, prompt)
        print(f"Successfully processed {os.path.basename(image_path)}")
        return response
    except AssistantError as e:
        print(f"Error processing {os.path.basename(image_path)}: {str(e)}")
        return None
    except Exception as e:
        print(f"Unexpected error processing {os.path.basename(image_path)}: {str(e)}")
        return None

def process_directory(directory_path: str, client: AssistantClient, max_workers: int = 6) -> None:
    """Process all supported images in a directory in parallel."""
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
    
    # Create full paths for images
    image_paths = [os.path.join(directory_path, f) for f in image_files]
    
    # Process images in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks and map them to their futures
        future_to_path = {
            executor.submit(process_single_image, path, client): path 
            for path in image_paths
        }
        
        # Process completed futures as they finish
        for future in concurrent.futures.as_completed(future_to_path):
            path = future_to_path[future]
            try:
                result = future.result()
                if result:
                    print(f"Completed processing: {os.path.basename(path)}")
            except Exception as e:
                print(f"Exception processing {os.path.basename(path)}: {str(e)}")

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
