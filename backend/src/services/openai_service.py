"""OpenAI Assistant service for interacting with OpenAI's API."""

import os
import json
import time
import logging
from typing import Dict, Any, Optional, List, Tuple, Union
import openai

from backend.src.config.settings import Settings
from backend.src.utils.exceptions import AssistantError

logger = logging.getLogger(__name__)

class OpenAIAssistantService:
    """Service for interacting with OpenAI's Assistant API."""
    
    def __init__(self):
        """Initialize the OpenAI client with API key from settings."""
        self.client = openai.OpenAI(api_key=Settings.OPENAI_API_KEY)
        self.timeout = Settings.REQUEST_TIMEOUT
        
    def send_file_to_assistant(
        self,
        file_bytes: bytes,
        file_name: str,
        original_file_path: str,
        prompt: str,
        assistant_id: str = None,
        save_response: bool = True
    ) -> Dict[str, Any]:
        """
        Send a file to an OpenAI Assistant and get the response.
        
        Args:
            file_bytes: The bytes of the file to send
            file_name: The name of the file
            original_file_path: The original path of the file (for reference)
            prompt: The prompt to send to the assistant
            assistant_id: The ID of the assistant to use (defaults to Settings.ASSISTANT_ID)
            save_response: Whether to save the response to a file
            
        Returns:
            The assistant's response as a dictionary
        """
        if not assistant_id:
            assistant_id = Settings.ASSISTANT_ID
            
        try:
            # Upload the file to OpenAI
            file_obj = self.client.files.create(
                file=file_bytes,
                purpose="assistants"
            )
            file_id = file_obj.id
            logger.info(f"Uploaded file {file_name} with ID: {file_id}")
            
            # Create a thread
            thread = self.client.beta.threads.create()
            thread_id = thread.id
            logger.info(f"Created thread with ID: {thread_id}")
            
            # Add a message to the thread
            message = self.client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=prompt,
                file_ids=[file_id]
            )
            logger.info(f"Added message to thread: {message.id}")
            
            # Run the assistant
            run = self.client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=assistant_id
            )
            run_id = run.id
            logger.info(f"Started run with ID: {run_id}")
            
            # Wait for the run to complete
            start_time = time.time()
            while True:
                run = self.client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run_id
                )
                
                if run.status == "completed":
                    logger.info(f"Run completed in {time.time() - start_time:.2f} seconds")
                    break
                    
                if run.status in ["failed", "cancelled", "expired"]:
                    error_message = f"Run failed with status: {run.status}"
                    if hasattr(run, "last_error") and run.last_error:
                        error_message += f", Error: {run.last_error}"
                    logger.error(error_message)
                    raise AssistantError(error_message)
                    
                if time.time() - start_time > self.timeout:
                    logger.error(f"Run timed out after {self.timeout} seconds")
                    raise AssistantError(f"Run timed out after {self.timeout} seconds")
                    
                logger.info(f"Run status: {run.status}, waiting...")
                time.sleep(1)
                
            # Get the messages
            messages = self.client.beta.threads.messages.list(
                thread_id=thread_id
            )
            
            # Get the assistant's response
            assistant_messages = [msg for msg in messages.data if msg.role == "assistant"]
            if not assistant_messages:
                raise AssistantError("No assistant messages found in the thread")
                
            latest_message = assistant_messages[0]
            
            # Extract the text content
            text_content = ""
            for content_item in latest_message.content:
                if content_item.type == "text":
                    text_content += content_item.text.value
            
            # Try to parse the response as JSON
            try:
                response_json = json.loads(text_content)
            except json.JSONDecodeError:
                logger.warning("Response is not valid JSON, returning as text")
                response_json = {"text": text_content}
                
            # Save the response to a file if requested
            if save_response and Settings.ENABLE_FILE_STORAGE:
                output_dir = os.path.dirname(original_file_path)
                base_name = os.path.splitext(os.path.basename(original_file_path))[0]
                output_path = os.path.join(output_dir, f"{base_name}_response.json")
                
                with open(output_path, "w") as f:
                    json.dump(response_json, f, indent=2)
                logger.info(f"Saved response to: {output_path}")
                
            # Clean up
            self.client.files.delete(file_id=file_id)
            logger.info(f"Deleted file with ID: {file_id}")
            
            return response_json
            
        except Exception as e:
            logger.error(f"Error in send_file_to_assistant: {str(e)}")
            raise AssistantError(f"Error in send_file_to_assistant: {str(e)}")
            
    def send_message_to_assistant(
        self,
        message: str,
        assistant_id: str = None
    ) -> Dict[str, Any]:
        """
        Send a message to an OpenAI Assistant and get the response.
        
        Args:
            message: The message to send to the assistant
            assistant_id: The ID of the assistant to use (defaults to Settings.ASSISTANT_ID)
            
        Returns:
            The assistant's response as a dictionary
        """
        if not assistant_id:
            assistant_id = Settings.ASSISTANT_ID
            
        try:
            # Create a thread
            thread = self.client.beta.threads.create()
            thread_id = thread.id
            logger.info(f"Created thread with ID: {thread_id}")
            
            # Add a message to the thread
            message_obj = self.client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=message
            )
            logger.info(f"Added message to thread: {message_obj.id}")
            
            # Run the assistant
            run = self.client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=assistant_id
            )
            run_id = run.id
            logger.info(f"Started run with ID: {run_id}")
            
            # Wait for the run to complete
            start_time = time.time()
            while True:
                run = self.client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run_id
                )
                
                if run.status == "completed":
                    logger.info(f"Run completed in {time.time() - start_time:.2f} seconds")
                    break
                    
                if run.status in ["failed", "cancelled", "expired"]:
                    error_message = f"Run failed with status: {run.status}"
                    if hasattr(run, "last_error") and run.last_error:
                        error_message += f", Error: {run.last_error}"
                    logger.error(error_message)
                    raise AssistantError(error_message)
                    
                if time.time() - start_time > self.timeout:
                    logger.error(f"Run timed out after {self.timeout} seconds")
                    raise AssistantError(f"Run timed out after {self.timeout} seconds")
                    
                logger.info(f"Run status: {run.status}, waiting...")
                time.sleep(1)
                
            # Get the messages
            messages = self.client.beta.threads.messages.list(
                thread_id=thread_id
            )
            
            # Get the assistant's response
            assistant_messages = [msg for msg in messages.data if msg.role == "assistant"]
            if not assistant_messages:
                raise AssistantError("No assistant messages found in the thread")
                
            latest_message = assistant_messages[0]
            
            # Extract the text content
            text_content = ""
            for content_item in latest_message.content:
                if content_item.type == "text":
                    text_content += content_item.text.value
            
            # Try to parse the response as JSON
            try:
                response_json = json.loads(text_content)
            except json.JSONDecodeError:
                logger.warning("Response is not valid JSON, returning as text")
                response_json = {"text": text_content}
                
            return response_json
            
        except Exception as e:
            logger.error(f"Error in send_message_to_assistant: {str(e)}")
            raise AssistantError(f"Error in send_message_to_assistant: {str(e)}") 