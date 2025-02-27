"""Logging utilities for the backend application."""

import logging
import os
import sys
from datetime import datetime

def setup_logger(name, log_file=None, level=logging.INFO):
    """
    Set up a logger with file and console handlers.
    
    Args:
        name: Name of the logger
        log_file: Path to the log file (optional)
        level: Logging level
        
    Returns:
        Logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Create file handler if log_file is provided
    if log_file:
        # Create directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_timestamp():
    """
    Get current timestamp in a formatted string.
    
    Returns:
        Formatted timestamp string
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")

# Create a default logger
default_logger = setup_logger('backend') 