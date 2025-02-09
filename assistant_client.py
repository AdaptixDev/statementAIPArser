"""Client for interacting with OpenAI Assistant API."""

import os
import time
from pathlib import Path
from typing import Dict, Any, Optional, List

from openai import OpenAI

from config import Config


class AssistantClient:

    def __init__(self, api_key: str, assistant_id: str):
        """Initialize the Assistant client.

        Args:
            api_key: OpenAI API key
            assistant_id: ID of the existing assistant to use
        """
        self.client = OpenAI(api_key=api_key)
        self.assistant_id = assistant_id

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

        if path.suffix.lower() not in Config.SUPPORTED_IMAGE_FORMATS:
            raise ImageValidationError(
                f"Unsupported image format. Supported formats: {Config.SUPPORTED_IMAGE_FORMATS}"
            )

        if path.stat().st_size > Config.MAX_FILE_SIZE:
            raise ImageValidationError(
                f"File size exceeds maximum allowed size of {Config.MAX_FILE_SIZE} bytes"
            )

    def upload_file(self, file_path: str) -> str:
        """Upload a file to OpenAI.

        Args:
            file_path: Path to the file to upload

        Returns:
            str: File ID from OpenAI

        Raises:
            FileUploadError: If file upload fails
        """
        try:
            with open(file_path, "rb") as file:
                response = self.client.files.create(
                    file=file,
                    purpose="vision"  # Using vision for image files
                )
                print(f"File uploaded successfully. File ID: {response.id}")
                return response.id
        except Exception as e:
            raise FileUploadError(f"Failed to upload file: {str(e)}")

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

    def wait_for_response(self, thread_id: str, run_id: str) -> Dict[str, Any]:
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
                                # Debug log
                                print(
                                    f"Content block type: {type(content_block)}"
                                )
                                print(
                                    f"Content block attributes: {dir(content_block)}"
                                )

                                # Try to extract content based on block type
                                if hasattr(content_block, 'text'):
                                    content = content_block.text.value
                                elif hasattr(content_block, 'value'):
                                    content = content_block.value
                                else:
                                    content = str(content_block)

                                print(f"Received response: {content}")
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
        # Validate image
        self.validate_image(image_path)
        print(f"Image validated successfully: {image_path}")

        # Upload file
        file_id = self.upload_file(image_path)
        print(f"File uploaded with ID: {file_id}")

        # Create thread
        thread = self.create_thread()
        print(f"Thread created with ID: {thread.id}")

        # Send message with image
        self.send_message(thread.id, prompt, file_id)
        print("Message sent successfully")

        # Create run with vision-specific configuration
        run = self.client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=self.assistant_id,
            model=Config.VISION_MODEL,  # Explicitly set the vision model
            instructions=
            "Please provide a detailed analysis of the provided image. Describe what you see, including colors, objects, composition, and any notable details. If you have any concerns about the image content, please explain them clearly."
        )
        print(f"Run created with ID: {run.id}")

        # Wait for and return response
        return self.wait_for_response(thread.id, run.id)
