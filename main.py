"""Main entry point for the OpenAI Assistant application (PDF processing only)."""

import sys
import os
import time
from config import Config
from assistant_client import AssistantClient
from exceptions import AssistantError
from personal_merger import merge_personal_and_transactions

def process_front_page_personal_info(front_image_path: str, client: AssistantClient) -> None:
    """
    Process the front page image with the personal information extraction assistant.
    
    This function reads the front page (denoted by "front" in its filename),
    then sends it to the OpenAI assistant specified by PERSONAL_INFO_ASSISTANT_ID,
    along with a prompt to extract personal information. The response's "content" 
    (which is expected to be a JSON string) is parsed and saved to a JSON file, 
    with the filename modified to denote personal data.
    """
    personal_info_prompt = (
        "Please parse the provided front page to extract personal information, "
        "including name, address, account number, and date of birth."
    )
    try:
        print(f"[INFO] Processing personal information extraction for: {os.path.basename(front_image_path)}")
        with open(front_image_path, "rb") as f:
            file_bytes = f.read()
        # Use the new assistantID defined in config for personal information parsing.
        response = client.send_file_to_assistant(
            file_bytes=file_bytes,
            file_name=os.path.basename(front_image_path),
            original_file_path=front_image_path,
            prompt=personal_info_prompt,
            assistant_id=Config.PERSONAL_INFO_ASSISTANT_ID
        )
        print(f"[INFO] Personal information extraction response: {response}")
        
        # Extract and parse the content field to display as structured JSON.
        import json
        try:
            personal_data = json.loads(response.get("content", "{}"))
        except Exception as e:
            print(f"[ERROR] Failed to parse response content: {e}")
            personal_data = {"error": f"Failed to parse response content: {str(e)}"}
            
        base_name = os.path.splitext(os.path.basename(front_image_path))[0]
        output_file = f"{base_name}_personal_info.json"
        with open(output_file, "w", encoding="utf-8") as out:
            json.dump(personal_data, out, indent=4, ensure_ascii=False)
        print(f"[INFO] Personal information JSON saved to {output_file}")
    except Exception as e:
        print(f"[ERROR] Error extracting personal information from {os.path.basename(front_image_path)}: {str(e)}")

def process_single_file(file_path: str, client: AssistantClient) -> None:
    """
    Process a single PDF file by:
      1. Splitting the PDF into multiple images
      2. Sending each image to OpenAI for processing in parallel batches (with an empty prompt)
      3. Merging the resulting JSON transaction files
      4. Sending the front page to a separate personal information extraction assistant
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
        
        # Process the front page separately for personal information extraction.
        if first_page and "front" in os.path.basename(first_page).lower():
            print("[INFO] Initiating personal information extraction for the front page...")
            process_front_page_personal_info(first_page, client)
        
        print("[INFO] Starting final data merge...")
        merge_personal_and_transactions()
        print("[INFO] Final data merge complete.")
        
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
