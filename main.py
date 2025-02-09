"""Main entry point for the OpenAI Assistant application."""

import sys
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

def main():
    """Main function to run the assistant."""
    
    # Check for command line arguments
    if len(sys.argv) != 2:
        print("Usage: python main.py <image_path>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    try:
        # Initialize the assistant client
        client = AssistantClient(
            api_key=Config.OPENAI_API_KEY,
            assistant_id=Config.ASSISTANT_ID
        )
        
        # Process the image with a default prompt
        prompt = "Please analyze this image and provide a detailed description."
        
        print(f"Processing image: {image_path}")
        print("Waiting for assistant response...")
        
        # Get response from assistant
        response = client.process_image(image_path, prompt)
        
        # Print response
        print("\nAssistant Response:")
        print("==================")
        print(response.get("content", "No content received"))
        
    except AssistantError as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
