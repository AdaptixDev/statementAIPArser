"""Main entry point for the OpenAI Assistant application (PDF processing only)."""

import sys
import os
import time
from config import Config
from assistant_client import AssistantClient
from exceptions import AssistantError

def process_single_file(file_path: str, client: AssistantClient) -> None:
    """
    Process a single PDF file by:
      1. Splitting the PDF into multiple images
      2. Sending each image to OpenAI for processing in parallel batches (with an empty prompt)
      3. Merging the resulting JSON transaction files
    """
    try:
        print(f"\nProcessing file: {os.path.basename(file_path)}")
        _, extension = os.path.splitext(file_path)
        extension = extension.lower()
        
        # Only process PDF files.
        if extension != ".pdf":
            print("[ERROR] The file provided must be a PDF.")
            return
        
        responses = []
        from pdf_utils import PDFConverter
        output_dir = "converted_images"
        first_page, image_paths = PDFConverter.pdf_to_images(file_path, output_dir)
        print(f"\nPDF converted into {len(image_paths)} images.")
        
        # Since the AI assistant is already pre-configured, we pass an empty prompt.
        prompt = ""
        
        # Process images in parallel batches using ThreadPoolExecutor
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        batch_size = Config.MAX_CONCURRENT_REQUESTS  # Number of concurrent requests defined in config
        total_batches = (len(image_paths) + batch_size - 1) // batch_size
        for batch_index in range(total_batches):
            batch_start = batch_index * batch_size
            batch = image_paths[batch_start:batch_start + batch_size]
            print(f"[INFO] Processing batch {batch_index + 1}/{total_batches} with {len(batch)} image(s) concurrently.")
            
            with ThreadPoolExecutor(max_workers=batch_size) as executor:
                future_to_image = {
                    executor.submit(client.process_image, image, prompt): image
                    for image in batch
                }
                for future in as_completed(future_to_image):
                    image = future_to_image[future]
                    try:
                        response = future.result()
                        responses.append(response)
                        print(f"[INFO] Completed processing for image: {os.path.basename(image)}")
                    except Exception as e:
                        print(f"[ERROR] Error processing image {os.path.basename(image)}: {str(e)}")
        
        # Once all images have been processed, merge the resulting JSON responses.
        from json_merger import merge_transaction_files
        print("[INFO] Starting merge process for transaction files...")
        merge_transaction_files()  # Uses default glob pattern and output file in the current directory.
        print("[INFO] Merge process complete.")
        
        return responses

    except AssistantError as e:
        print(f"Error processing {os.path.basename(file_path)}: {str(e)}")
        return None
    except Exception as e:
        print(f"Unexpected error processing {os.path.basename(file_path)}: {str(e)}")
        return None

def main():
    """Main function to run the assistant for a single PDF file."""
    start_time = time.time()

    # Expect exactly one command line argument: the file path.
    if len(sys.argv) != 2:
        print("Usage: python main.py <file_path>")
        sys.exit(1)

    path = sys.argv[1]

    # Ensure the provided path is a file.
    if not os.path.isfile(path):
        print(f"Error: {path} is not a valid file")
        sys.exit(1)

    try:
        # Initialize the assistant client using credentials from Config.
        client = AssistantClient(
            api_key=Config.OPENAI_API_KEY,
            assistant_id=Config.ASSISTANT_ID
        )
        process_single_file(path, client)

    except AssistantError as e:
        print(f"Error processing file: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        sys.exit(1)
    finally:
        elapsed_time = time.time() - start_time
        print(f"\nTotal processing time: {elapsed_time:.2f} seconds")

if __name__ == "__main__":
    main()
