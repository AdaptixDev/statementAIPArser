"""Client for interacting with OpenAI Assistant API."""

import os
import time
from pathlib import Path
from typing import Dict, Any, Optional, List

from openai import OpenAI

from config import Config
from exceptions import *

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
                    purpose="assistants"
                )
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
            return self.client.beta.threads.create()
        except Exception as e:
            raise ThreadCreationError(f"Failed to create thread: {str(e)}")

    def send_message(self, thread_id: str, content: str, file_id: Optional[str] = None) -> None:
        """Send a message to the thread.

        Args:
            thread_id: Thread ID to send message to
            content: Message content
            file_id: Optional file ID to attach

        Raises:
            MessageCreationError: If message creation fails
        """
        try:
            message_data = {
                "role": "user",
                "content": content
            }

            # Handle file attachments according to Assistant API specs
            if file_id:
                message_data["attachments"] = [
                    {
                        "file_id": file_id,
                        "type": "file"
                    }
                ]

            self.client.beta.threads.messages.create(
                thread_id=thread_id,
                **message_data
            )
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

        while True:
            if time.time() - start_time > Config.REQUEST_TIMEOUT:
                raise ResponseTimeoutError("Assistant response timed out")

            run = self.client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run_id
            )

            if run.status == "completed":
                messages = self.client.beta.threads.messages.list(
                    thread_id=thread_id,
                    order="desc",
                    limit=1
                )

                # Return the latest assistant message
                if messages.data:
                    message = messages.data[0]
                    if message.role == "assistant":
                        return {
                            "role": message.role,
                            "content": message.content[0].text.value if message.content else None
                        }
                return {"role": "assistant", "content": "No response content"}

            elif run.status in ["failed", "cancelled", "expired"]:
                raise ResponseTimeoutError(f"Run failed with status: {run.status}")

            time.sleep(1)  # Polling interval

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

        # Upload file
        file_id = self.upload_file(image_path)

        # Create thread
        thread = self.create_thread()

        # Send message with image
        self.send_message(thread.id, prompt, file_id)

        # Create run
        run = self.client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=self.assistant_id
        )

        # Wait for and return response
        return self.wait_for_response(thread.id, run.id)