"""Main entry point for the OpenAI Assistant application (PDF processing only)."""

import sys
import os
import time
from config import Config
from assistant_client import AssistantClient
from exceptions import AssistantError
from json_merger import merge_transaction_files
from personal_merger import merge_personal_and_transactions

# Global in-memory stores when file storage is disabled.
in_memory_transactions = []  # List to collect transaction JSON responses.
in_memory_personal_info = None  # To hold the personal info extraction JSON.

def process_front_page_personal_info(front_image, client: AssistantClient) -> None:
    """
    Process the front page image (which can be a file path or an in-memory tuple)
    using the personal information extraction assistant and generate a JSON output.
    """
    personal_info_prompt = (
        "Please parse the provided front page to extract personal information, "
        "including name, address, account number, and date of birth."
    )
    try:
        if Config.ENABLE_FILE_STORAGE:
            # front_image is expected to be a file path
            print(f"[INFO] Processing personal information extraction for: {os.path.basename(front_image)}")
            with open(front_image, "rb") as f:
                file_bytes = f.read()
            file_name = os.path.basename(front_image)
            original_identifier = front_image
        else:
            # front_image is expected to be a tuple: (pseudo_filename, image_bytes)
            file_name, file_bytes = front_image
            print(f"[INFO] Processing personal information extraction for in-memory front image: {file_name}")
            original_identifier = file_name

        # IMPORTANT: Pass save_response=False so that no duplicate file is written.
        response = client.send_file_to_assistant(
            file_bytes=file_bytes,
            file_name=file_name,
            original_file_path=original_identifier,
            prompt=personal_info_prompt,
            assistant_id=Config.PERSONAL_INFO_ASSISTANT_ID,
            save_response=False
        )
        print(f"[INFO] Personal information extraction response: {response}")

        # Use the response as the parsed JSON object.
        personal_data = response

        if Config.ENABLE_FILE_STORAGE:
            base_name = os.path.splitext(file_name)[0]
            output_file = f"{base_name}_personal_info.json"
            output_path = os.path.join(Config.OUTPUT_DIR, output_file)
            with open(output_path, "w", encoding="utf-8") as out:
                import json
                json.dump(personal_data, out, indent=4, ensure_ascii=False)
            print(f"[INFO] Personal information JSON saved to {output_path}")
        else:
            global in_memory_personal_info
            in_memory_personal_info = personal_data
            print("[INFO] Personal information stored in memory for merging.")
    except Exception as e:
        print(f"[ERROR] Error extracting personal information from {file_name}: {str(e)}")

def process_single_file(file_path: str, client: AssistantClient) -> None:
    """
    Process a single PDF file by:
      1. Splitting the PDF into multiple images.
      2. Sending each image (including the front page) to OpenAI for processing in parallel batches.
      3. Collecting the resulting JSON transaction responses.
      4. Sending the front page to a separate personal information extraction assistant.
      5. Merging the final results into one JSON file (saved to disk when enabled).
    """
    global in_memory_transactions  # in-memory store for transaction responses

    try:
        print(f"\nProcessing file: {os.path.basename(file_path)}")
        _, extension = os.path.splitext(file_path)
        extension = extension.lower()
    
        if extension != ".pdf":
            print("[ERROR] The file provided must be a PDF.")
            return
    
        responses = []
        from pdf_utils import PDFConverter
        
        # If file storage is enabled, create a processing directory under ./processing/
        if Config.ENABLE_FILE_STORAGE:
            pdf_basename = os.path.splitext(os.path.basename(file_path))[0]
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            processing_dir = os.path.join("processing", f"{pdf_basename}_{timestamp}")
            os.makedirs(processing_dir, exist_ok=True)
            # Save the directory path to Config so it can be used by other modules
            Config.OUTPUT_DIR = processing_dir
            output_dir = processing_dir
            print(f"[INFO] Files will be saved under: {output_dir}")
        else:
            output_dir = None
    
        # Obtain images from PDF.
        first_page, images = PDFConverter.pdf_to_images(file_path, output_dir)
        print(f"\nPDF converted into {len(images)} image(s).")
    
        # Instead of removing the front page from the batch processing,
        # we log it so that it will now be processed as transactions as well as for personal info.
        if first_page:
            print("[INFO] Front page image detected; processing for both transactions and personal information extraction.")
    
        from concurrent.futures import ThreadPoolExecutor, as_completed
        batch_size = Config.MAX_CONCURRENT_REQUESTS
        total_batches = (len(images) + batch_size - 1) // batch_size
    
        for batch_index in range(total_batches):
            batch_start = batch_index * batch_size
            batch = images[batch_start:batch_start + batch_size]
            print(f"[INFO] Processing batch {batch_index + 1}/{total_batches} with {len(batch)} image(s) concurrently.")
    
            with ThreadPoolExecutor(max_workers=batch_size) as executor:
                future_to_image = {}
                for image_item in batch:
                    if Config.ENABLE_FILE_STORAGE:
                        future = executor.submit(client.process_image, image_item, "")
                        future_to_image[future] = image_item
                    else:
                        pseudo_filename, image_bytes = image_item
                        future = executor.submit(client.process_image_bytes, pseudo_filename, image_bytes, "")
                        future_to_image[future] = pseudo_filename
    
                for future in as_completed(future_to_image):
                    identifier = future_to_image[future]
                    try:
                        response = future.result()
                        responses.append(response)  # Collect response JSON
                        print(f"[INFO] Completed processing for image: {identifier}")
                    except Exception as e:
                        print(f"[ERROR] Error processing image {identifier}: {str(e)}")
    
        # Save transaction responses in memory if file storage is disabled.
        if not Config.ENABLE_FILE_STORAGE:
            in_memory_transactions.extend(responses)
    
        # Process the front page separately for personal information extraction.
        if first_page:
            if Config.ENABLE_FILE_STORAGE:
                identifier = os.path.basename(first_page)
            else:
                identifier = first_page[0]
            if "front" in identifier.lower():
                print("[INFO] Initiating personal information extraction for the front page...")
                process_front_page_personal_info(first_page, client)
        
        # Merge results.
        if Config.ENABLE_FILE_STORAGE:
            print("[INFO] Starting merge process for transaction files (disk)...")
            merge_transaction_files(directory=Config.OUTPUT_DIR)
            print("[INFO] Transaction merge complete.")
            print("[INFO] Starting final data merge...")
            merge_personal_and_transactions(directory=Config.OUTPUT_DIR)
        else:
            print("[INFO] Starting final data merge using in-memory JSON responses...")
            merge_personal_and_transactions(
                in_memory_transactions=in_memory_transactions,
                in_memory_personal_info=in_memory_personal_info
            )
        
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
