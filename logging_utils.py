"""Utilities for safe logging that prevents binary data from being logged."""

import logging
from typing import Any

def safe_str(obj: Any) -> str:
    """
    Safely convert any object to string, handling binary data appropriately.
    
    Args:
        obj: Any object to convert to string
        
    Returns:
        A safe string representation of the object
    """
    if isinstance(obj, (bytes, bytearray)):
        return f"<binary data of length {len(obj)}>"
    if isinstance(obj, dict):
        # Handle dictionaries that might contain binary data
        safe_dict = {}
        for k, v in obj.items():
            if k in ('image_bytes', 'file_bytes', 'content'):
                safe_dict[k] = f"<binary data of length {len(v)}>" if isinstance(v, (bytes, bytearray)) else str(v)
            else:
                safe_dict[k] = safe_str(v)
        return str(safe_dict)
    return str(obj)

class SafeLogger:
    """Logger wrapper that ensures binary data is not logged."""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def info(self, msg: str, *args, **kwargs):
        self.logger.info(safe_str(msg), *args, **kwargs)
    
    def error(self, msg: str, *args, **kwargs):
        if 'exc_info' in kwargs:
            # Handle exception info specially to avoid binary data in traceback
            kwargs['exc_info'] = False
            self.logger.error(f"{safe_str(msg)} (exception details omitted)", *args, **kwargs)
        else:
            self.logger.error(safe_str(msg), *args, **kwargs)
    
    def debug(self, msg: str, *args, **kwargs):
        self.logger.debug(safe_str(msg), *args, **kwargs)
    
    def warning(self, msg: str, *args, **kwargs):
        self.logger.warning(safe_str(msg), *args, **kwargs) 