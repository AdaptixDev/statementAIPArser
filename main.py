
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

def get_file_type(file_path: str) -> str:
    """Determine if file is PDF or image."""
    extension = os.path.splitext(file_path)[1].lower()
    if extension == '.pdf':
        return 'pdf'
    elif extension in Config.SUPPORTED_IMAGE_FORMATS:
        return 'image'
    else:
        raise ValueError(f"Unsupported file type: {extension}")

def process_single_file(file_path: str, client: AssistantClient) -> None:
    """Process a single file (PDF or image)."""
    try:
        print(f"\nProcessing file: {os.path.basename(file_path)}")
        file_type = get_file_type(file_path)
        
        if file_type == 'pdf':
            from pdf_utils import PDFConverter
            # Convert PDF to images first
            output_dir = 'converted_images'
            image_paths = PDFConverter.pdf_to_images(file_path, output_dir)
            responses = []
            for image_path in image_paths:
                prompt = "Please analyze this bank statement image and extract all transaction details."
                response = client.process_image(image_path, prompt)
                responses.append(response)
                print(f"Successfully processed PDF page: {os.path.basename(image_path)}")
            return responses
        else:
            # Process single image directly
            prompt = "Please analyze this bank statement image and extract all transaction details."
            response = client.process_image(file_path, prompt)
            print(f"Successfully processed {os.path.basename(file_path)}")
            return response
            
    except AssistantError as e:
        print(f"Error processing {os.path.basename(file_path)}: {str(e)}")
        return None
    except Exception as e:
        print(f"Unexpected error processing {os.path.basename(file_path)}: {str(e)}")
        return None

def process_directory(directory_path: str, client: AssistantClient, max_workers: int = 10) -> None:
    """Process all supported files (PDFs and images) in a directory in parallel."""
    supported_extensions = list(Config.SUPPORTED_IMAGE_FORMATS) + ['.pdf']
    
    # Get list of supported files
    files = [
        f for f in os.listdir(directory_path)
        if os.path.isfile(os.path.join(directory_path, f))
        and os.path.splitext(f)[1].lower() in supported_extensions
    ]
    
    if not files:
        print(f"No supported files found in {directory_path}")
        return
        
    print(f"Found {len(files)} files to process")
    
    # Create full paths for files
    file_paths = [os.path.join(directory_path, f) for f in files]
    
    # Process files in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks and map them to their futures
        future_to_path = {
            executor.submit(process_single_file, path, client): path 
            for path in file_paths
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
        print("Usage: python main.py <file_or_directory_path>")
        sys.exit(1)
    
    path = sys.argv[1]
    
    try:
        # Initialize the assistant client
        client = AssistantClient(
            api_key=Config.OPENAI_API_KEY,
            assistant_id=Config.ASSISTANT_ID
        )
        
        # Check if path is file or directory
        if os.path.isfile(path):
            process_single_file(path, client)
        elif os.path.isdir(path):
            process_directory(path, client)
        else:
            print(f"Error: {path} is not a valid file or directory")
            sys.exit(1)
        
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
