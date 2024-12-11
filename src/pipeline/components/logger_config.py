"""
Centralized logging configuration for the story generation pipeline.
"""

import logging
import logging.handlers
from pathlib import Path
from datetime import datetime

def setup_logger(name: str = None) -> logging.Logger:
    """
    Set up a logger with both console and file output.
    File output uses RotatingFileHandler to manage log size and backup count.
    
    Args:
        name: Logger name (defaults to root logger if None)
        
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    if logger.handlers:  # Return existing logger if already configured
        return logger
        
    logger.setLevel(logging.INFO)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    
    # Console handler (less detailed, for user feedback)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    
    # File handler (more detailed, for debugging)
    log_dir = Path(__file__).parent.parent.parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / "story_generation.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=5*1024*1024,  # 5MB per file
        backupCount=3,  # Keep 3 backup files
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(detailed_formatter)
    
    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

# Create default logger
default_logger = setup_logger('gpt_storytale') 