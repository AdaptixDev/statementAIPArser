"""Client for interacting with OpenAI Assistant API."""

import os
import time
import logging
import threading
from pathlib import Path
from typing import Dict, Any, Optional, List

from openai import OpenAI

from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
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
        """Validate the image file.

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
            logger.error(f"Invalid file extension: {file_extension} for file: {image_path}")
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
        """Send a message to the thread.

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
                message_content.append({
                    "type": "image_file",
                    "image_file": {
                        "file_id": file_id
                    }
                })

            print(f"Sending message with content: {message_content}")
            self.client.beta.threads.messages.create(thread_id=thread_id,
                                                     role="user",
                                                     content=message_content)
            print("Message sent successfully")
        except Exception as e:
            raise MessageCreationError(f"Failed to create message: {str(e)}")

    def wait_for_response(self, thread_id: str, run_id: str, image_path: str) -> Dict[str, Any]:
        """Wait for and return the assistant's response.

        Args:
            thread_id: Thread ID
            run_id: Run ID to wait for

        Returns:
            Dict containing the assistant's response

        Raises:
            ResponseTimeoutError: If response times out
        """
        start_time = time.time()
        print(f"Waiting for response on thread {thread_id}, run {run_id}")

        while True:
            if time.time() - start_time > Config.REQUEST_TIMEOUT:
                raise ResponseTimeoutError("Assistant response timed out")

            try:
                run = self.client.beta.threads.runs.retrieve(
                    thread_id=thread_id, run_id=run_id)
                print(f"Run status: {run.status}")

                if run.status == "completed":
                    messages = self.client.beta.threads.messages.list(
                        thread_id=thread_id, order="desc", limit=1)

                    if messages.data:
                        message = messages.data[0]
                        if message.role == "assistant":
                            # Handle different content types
                            if message.content:
                                content_block = message.content[0]
                                # Try to extract content based on block type
                                if hasattr(content_block, 'text'):
                                    content = content_block.text.value
                                elif hasattr(content_block, 'value'):
                                    content = content_block.value
                                else:
                                    content = str(content_block)

                                # Get response content
                                content = content

                                # Extract page number from thread_id if it exists
                                page_num = image_path.split('_page_')[1].split('.')[0] if '_page_' in image_path else ''
                                timestamp = time.strftime("%Y%m%d-%H%M%S")
                                json_filename = f"statement_analysis_page{page_num}_{timestamp}.json"

                                # Save JSON response to file
                                with open(json_filename, "w") as f:
                                    f.write(content)

                                try:
                                    # Parse content as dict and check for empty transactions
                                    import json
                                    response_dict = json.loads(content)
                                    if "Transactions" in response_dict and len(response_dict["Transactions"]) == 0:
                                        print(f"ERROR: Empty transactions received for file: {thread_id}")
                                except json.JSONDecodeError:
                                    print(f"Warning: Response is not valid JSON for file: {thread_id}")
                                except Exception as e:
                                    print(f"Error processing response: {str(e)}")

                                print(f"\nResponse saved to: {json_filename}")
                                return {
                                    "role": message.role,
                                    "content": content
                                }
                    return {
                        "role": "assistant",
                        "content": "No response content"
                    }

                elif run.status in ["failed", "cancelled", "expired"]:
                    if hasattr(run, 'last_error'):
                        error_msg = f"Run failed with status: {run.status}, error: {run.last_error}"
                    else:
                        error_msg = f"Run failed with status: {run.status}"
                    raise ResponseTimeoutError(error_msg)

                time.sleep(2)  # Increased polling interval to reduce API load
            except Exception as e:
                logger.error(f"Error while waiting for response: {str(e)}", exc_info=True)
                raise ResponseTimeoutError(
                    f"Error while waiting for response: {str(e)}")

    def process_image(self, image_path: str, prompt: str) -> Dict[str, Any]:
        """Process an image through the assistant.

        Args:
            image_path: Path to the image file
            prompt: Prompt to send with the image

        Returns:
            Dict containing the assistant's response
        """
        logger.info(f"Starting image processing for: {image_path}")
        try:
            # Validate image
            # Validate image
            if not os.path.exists(image_path):
                raise FileUploadError(f"File not found: {image_path}")
            if not os.path.isfile(image_path):
                raise FileUploadError(f"Not a file: {image_path}")
            if not os.access(image_path, os.R_OK):
                raise FileUploadError(f"File not readable: {image_path}")

            self.validate_image(image_path)
            logger.info(f"Processing image: {image_path}")

            try:
                import base64
                from PIL import Image
                import io
                
                # Open and compress image
                with Image.open(image_path) as img:
                    # Convert to RGB if needed
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                        
                    # Compress image
                    output = io.BytesIO()
                    quality = Config.INITIAL_COMPRESSION_QUALITY
                    img.save(output, format='JPEG', quality=quality)
                    while output.tell() > Config.MAX_IMAGE_SIZE_MB * 1024 * 1024 and quality > Config.MIN_COMPRESSION_QUALITY:
                        output = io.BytesIO()
                        img.save(output, format='JPEG', quality=quality)
                        quality -= 5
                        logger.info(f"Compressed image to quality {quality}")
                    
                    # Convert to base64
                    image_base64 = base64.b64encode(output.getvalue()).decode('utf-8')
                    logger.info("Image converted to base64")
            except Exception as e:
                raise FileUploadError(f"Failed to upload file: {str(e)}")

            # Create thread with message containing image
            logger.debug("Creating thread with image message...")
            # Extract page number from image filename
            page_num = ""
            if "_page_" in image_path:
                page_num = image_path.split("_page_")[1].split(".")[0]

            # Create thread with base64 image
            thread = self.client.beta.threads.create(
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}",
                                "detail": "high"
                            }
                        }
                    ]
                }]
            )
            logger.info(f"Thread created with ID: {thread.id}")
            print("Message sent successfully")
        except Exception as e:
            logger.error(f"Error in process_image: {str(e)}", exc_info=True)
            raise

        # Create run
        run = self.client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=self.assistant_id,
            instructions=
            "Please provide a detailed analysis of the provided image. Describe what you see, including colors, objects, composition, and any notable details. If you have any concerns about the image content, please explain them clearly."
        )
        print(f"Run created with ID: {run.id}")

        # Wait for and return response
        return self.wait_for_response(thread.id, run.id, image_path)

from exceptions import (
    AssistantError,
    FileUploadError,
    ImageValidationError,
    ThreadCreationError,
    MessageCreationError,
    ResponseTimeoutError
)