"""
Client for interacting with the OpenAI Assistant API 
via the beta.threads endpoint, using a file_id for images.
"""

import os
import time
import logging
import threading
from pathlib import Path
from typing import Dict, Any, Optional

import openai
from openai import OpenAI

from config import Config
from exceptions import (AssistantError, FileUploadError, ImageValidationError,
                        ThreadCreationError, MessageCreationError,
                        ResponseTimeoutError)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Reduce OpenAI package logging
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


class AssistantClient:

    def __init__(self, api_key: str, assistant_id: str):
        """Initialize the Assistant client.

        Args:
            api_key: OpenAI API key
            assistant_id: ID of the existing assistant to use
        """
        self.client = OpenAI(api_key=api_key)
        self.assistant_id = assistant_id
        self._lock = threading.Lock()

    def validate_image(self, image_path: str) -> None:
        """Validate the image file before attempting to process/upload.

        Args:
            image_path: Path to the image file

        Raises:
            ImageValidationError: If validation fails
        """
        path = Path(image_path)
        if not path.exists():
            raise ImageValidationError(f"Image file not found: {image_path}")

        file_extension = path.suffix.lower()
        if file_extension not in Config.SUPPORTED_IMAGE_FORMATS:
            logger.error(
                f"Invalid file extension: {file_extension} for file: {image_path}"
            )
            raise ImageValidationError(
                f"Unsupported image format '{file_extension}'. Supported formats: {Config.SUPPORTED_IMAGE_FORMATS}"
            )

        if path.stat().st_size > Config.MAX_FILE_SIZE:
            raise ImageValidationError(
                f"File size exceeds maximum allowed size of {Config.MAX_FILE_SIZE} bytes"
            )

    def create_thread(self) -> Any:
        """Create a new thread.

        Returns:
            Thread object from OpenAI

        Raises:
            ThreadCreationError: If thread creation fails
        """
        try:
            thread = self.client.beta.threads.create()
            print(f"Thread created successfully. Thread ID: {thread.id}")
            return thread
        except Exception as e:
            raise ThreadCreationError(f"Failed to create thread: {str(e)}")

    def send_message(self,
                     thread_id: str,
                     content: str,
                     file_id: Optional[str] = None) -> None:
        """Send a message to the thread (pure text or referencing an uploaded file).

        Args:
            thread_id: Thread ID to send message to
            content: Message content
            file_id: Optional file ID to attach

        Raises:
            MessageCreationError: If message creation fails
        """
        try:
            message_content = [{"type": "text", "text": content}]

            if file_id:
                # The beta.threads endpoint requires "file_id" if type = "image_file"
                message_content.append({
                    "type": "image_file",
                    "image_file": {
                        "file_id": file_id
                    }
                })

            logger.info(f"Sending message with content: {message_content}")
            self.client.beta.threads.messages.create(thread_id=thread_id,
                                                     role="user",
                                                     content=message_content)
            print("Message sent successfully")
        except Exception as e:
            raise MessageCreationError(f"Failed to create message: {str(e)}")

    def wait_for_response(self, thread_id: str, run_id: str, image_path: str, retry_count: int = 0, save_response: bool = True) -> dict:
        """
        Wait for and return the assistant's response.
        """
        MAX_RETRIES = 3
        start_time = time.time()
        logger.info(f"Waiting for response on thread {thread_id}, run {run_id} (Attempt {retry_count + 1}/{MAX_RETRIES})")
    
        while True:
            if time.time() - start_time > Config.REQUEST_TIMEOUT:
                raise ResponseTimeoutError("Assistant response timed out")
    
            try:
                run = self.client.beta.threads.runs.retrieve(
                    thread_id=thread_id, run_id=run_id)
                logger.debug(f"Run status: {run.status}")
    
                if run.status == "completed":
                    # Fetch the last message (descending order)
                    messages = self.client.beta.threads.messages.list(
                        thread_id=thread_id, order="desc", limit=1)
    
                    if messages.data:
                        message = messages.data[0]
                        if message.role == "assistant" and message.content:
                            content_block = message.content[0]
                            if hasattr(content_block, 'text'):
                                content = content_block.text.value
                            elif hasattr(content_block, 'value'):
                                content = content_block.value
                            else:
                                content = str(content_block)
    
                            # Determine page identifier from the image filename.
                            page_num = ""
                            if "_page_" in image_path:
                                try:
                                    page_num = image_path.split("_page_")[1].split(".")[0]
                                except IndexError:
                                    page_num = ""
                            elif "_front" in image_path:
                                page_num = "front"
    
                            timestamp = time.strftime("%Y%m%d-%H%M%S")
                            if page_num == "front":
                                json_filename = f"statement_analysis_front_{timestamp}.json"
                            else:
                                json_filename = f"statement_analysis_page{page_num}_{timestamp}.json"
    
                            # Only write the file if enabled _and_ if save_response is True.
                            if Config.ENABLE_FILE_STORAGE and save_response:
                                output_dir = getattr(Config, "OUTPUT_DIR", ".")
                                file_path_to_write = os.path.join(output_dir, json_filename)
    
                                # Attempt to prettify the JSON output.
                                import json
                                try:
                                    parsed_json = json.loads(content)
                                    formatted_content = json.dumps(parsed_json, indent=4, ensure_ascii=False)
                                except Exception as e:
                                    logger.error(f"Failed to format JSON response: {e}", exc_info=True)
                                    formatted_content = content  # fall back if not valid JSON
    
                                with open(file_path_to_write, "w", encoding="utf-8") as f:
                                    f.write(formatted_content)
                                logger.info(f"Response saved to: {file_path_to_write}")
    
                            # Attempt to parse the content as JSON before returning.
                            try:
                                parsed_content = json.loads(content)
                                # Log the number of transactions if available.
                                if isinstance(parsed_content, dict) and "Transactions" in parsed_content:
                                    num_transactions = len(parsed_content["Transactions"])
                                    logger.info(f"Assistant response contains {num_transactions} transactions.")
                            except Exception as e:
                                logger.error(f"Failed to parse response JSON: {e}", exc_info=True)
                                parsed_content = content
    
                            return parsed_content
    
                    # If no assistant message or no content
                    return "No response content"
    
                elif run.status in ["failed", "cancelled", "expired"]:
                    if retry_count < MAX_RETRIES - 1:
                        logger.warning(f"Run failed, retrying... (Attempt {retry_count + 1}/{MAX_RETRIES})")
                        new_run = self.client.beta.threads.runs.create(
                            thread_id=thread_id,
                            assistant_id=self.assistant_id,
                            instructions=(
                                "Please provide a detailed analysis of the provided image. "
                                "Describe what you see, including colors, objects, composition, and any notable details. "
                                "If you have any concerns about the image content, please explain them clearly."
                            )
                        )
                        time.sleep(5)
                        return self.wait_for_response(thread_id, new_run.id, image_path, retry_count + 1, save_response)
                    else:
                        error_msg = (f"Run failed with status: {run.status}, error: {getattr(run, 'last_error', '')}"
                                     if hasattr(run, 'last_error') and run.last_error is not None
                                     else f"Run failed with status: {run.status}")
                        raise ResponseTimeoutError(error_msg)
    
                time.sleep(2)
            except Exception as e:
                logger.error(f"Error while waiting for response: {str(e)}", exc_info=True)
                raise ResponseTimeoutError(f"Error while waiting for response: {str(e)}")

    def send_file_to_assistant(self,
                               file_bytes: bytes,
                               file_name: str,
                               original_file_path: str,
                               prompt: str = "",
                               assistant_id: Optional[str] = None,
                               mime_type: str = "image/jpeg",
                               save_response: bool = True) -> Dict[str, Any]:
        """
        Reusable logic to send a file (or any supported file type) to OpenAI.
        This method uploads the file, builds a message payload (including a prompt if provided),
        creates a thread and a run (using the configurable assistant ID), and waits for the response.

        Args:
            file_bytes: The content of the file in bytes.
            file_name: Name of the file (e.g. "image.jpg").
            original_file_path: Path to the original file (used to derive page identifiers).
            prompt: Text prompt to include (if any). If empty, no text is sent.
            assistant_id: Optional assistant ID to use; if not provided, defaults to self.assistant_id.
            mime_type: MIME type of the file (default is "image/jpeg").
            save_response: Flag indicating whether to write the assistant response to disk.
                           When False, wait_for_response skips the file write.
        Returns:
            A dictionary containing the assistant's response.
        """
        max_retries = 3
        retry_delay = 5
        uploaded_file = None

        for attempt in range(max_retries):
            try:
                uploaded_file = self.client.files.create(
                    file=(file_name, file_bytes, mime_type),
                    purpose="vision"  # or "fine-tune", etc. (kept unchanged)
                )
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    raise FileUploadError(
                        f"Failed to upload file after {max_retries} attempts: {e}"
                    )
                logger.warning(
                    f"Upload attempt {attempt+1} failed, retrying in {retry_delay}s... - Error: {e}"
                )
                time.sleep(retry_delay)

        if not uploaded_file or not hasattr(uploaded_file, "id"):
            raise FileUploadError("File upload did not return a valid file ID.")

        logger.info(f"File uploaded successfully with ID: {uploaded_file.id}")

        # Build the messages payload.
        message_payload = {"role": "user", "content": []}

        if prompt:
            message_payload["content"].append({
                "type": "text",
                "text": prompt
            })

        # Always include the file attachment with "detail": "high" to dictate image quality.
        message_payload["content"].append({
            "type": "image_file",
            "image_file": {
                "file_id": uploaded_file.id,
                "detail": "high"
            }
        })

        # Create a thread with the constructed payload.
        thread = self.client.beta.threads.create(messages=[message_payload])
        logger.info(f"Thread created with ID: {thread.id}")
        print("Message (prompt + file reference) sent successfully.")

        # Use the provided assistant_id if given, otherwise use the default.
        actual_assistant_id = assistant_id if assistant_id is not None else self.assistant_id

        # Create a run on that thread.
        run = self.client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=actual_assistant_id,
            instructions=(
                "Please provide a detailed analysis of the provided image. "
                "Describe what you see, including colors, objects, composition, and any notable details. "
                "If you have any concerns about the image content, please explain them clearly."
            )
        )
        print(f"Run created with ID: {run.id}")

        # Wait for and return the assistant's response.
        return self.wait_for_response(thread.id, run.id, original_file_path, save_response=save_response)

    def process_image(self, image_path: str, prompt: str = "") -> Dict[str, Any]:
        """Process an image by uploading it to OpenAI, creating a thread, and retrieving the result.

        Args:
            image_path: Path to the image file
            prompt: Prompt to send with the file (if any)

        Returns:
            Dict containing the assistant's response
        """
        logger.info(f"Starting image processing for: {image_path}")
        try:
            # 1. Validate presence/readability
            if not os.path.exists(image_path):
                raise FileUploadError(f"File not found: {image_path}")
            if not os.path.isfile(image_path):
                raise FileUploadError(f"Not a file: {image_path}")
            if not os.access(image_path, os.R_OK):
                raise FileUploadError(f"File not readable: {image_path}")

            # 2. Validate image format/size
            self.validate_image(image_path)
            logger.info(f"Processing image: {image_path}")

            # 3. Read file bytes and optionally compress
            with open(image_path, "rb") as file:
                file_bytes = file.read()

            if Config.USE_IMAGE_COMPRESSION:
                from PIL import Image
                import io
                quality = Config.INITIAL_COMPRESSION_QUALITY

                img = Image.open(io.BytesIO(file_bytes))
                # Compress until under size limit or quality floor
                while len(file_bytes) > Config.MAX_IMAGE_SIZE_MB * 1024 * 1024 and \
                      quality > Config.MIN_COMPRESSION_QUALITY:
                    output = io.BytesIO()
                    img.save(output, format='JPEG', quality=quality)
                    file_bytes = output.getvalue()
                    quality -= 5
                    logger.info(f"Compressed image to quality {quality}")

            # 4. Use the new reusable logic to send the file to OpenAI.
            return self.send_file_to_assistant(file_bytes, "image.jpg", image_path, prompt)

        except Exception as e:
            logger.error(f"Error in process_image: {str(e)}", exc_info=True)
            raise

    def process_image_bytes(self, file_name: str, file_bytes: bytes, prompt: str = "") -> Dict[str, Any]:
        """
        Process an in-memory image by sending its file bytes to OpenAI without disk I/O.
        The file_name (which contains our pseudo naming indicator, such as '_front' or '_page_X')
        is used when building the message payload.
    
        Args:
            file_name: Pseudo filename for the image (e.g. 'statement_front.jpg')
            file_bytes: The image data in bytes.
            prompt: Optional prompt to send with the file.
    
        Returns:
            A dictionary containing the assistant's response.
        """
        logger.info(f"Processing in-memory image: {file_name}")
    
        # Optionally compress the image if enabled.
        if Config.USE_IMAGE_COMPRESSION:
            from PIL import Image
            import io
            quality = Config.INITIAL_COMPRESSION_QUALITY
            img = Image.open(io.BytesIO(file_bytes))
            while len(file_bytes) > Config.MAX_IMAGE_SIZE_MB * 1024 * 1024 and quality > Config.MIN_COMPRESSION_QUALITY:
                output = io.BytesIO()
                img.save(output, format='JPEG', quality=quality)
                file_bytes = output.getvalue()
                quality -= 5
                logger.info(f"Compressed in-memory image to quality {quality}")
    
        # Note: We pass the pseudo filename for both file_name and original_file_path so that
        # any naming cues (like '_front' or '_page_X') can be extracted in wait_for_response.
        return self.send_file_to_assistant(file_bytes, file_name, file_name, prompt)
