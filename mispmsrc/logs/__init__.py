"""
Logging configuration for MISPM
"""

import os
import logging
import datetime
import sys

def setup_logging(log_dir=None, log_level=logging.INFO):
    """
    Configure logging for the MISPM application
    
    Args:
        log_dir: Directory where log files will be stored (default: project_root/logs)
        log_level: Logging level to use (default: INFO)
        
    Returns:
        str: Path to the created log file
    """
    # Determine log directory
    if log_dir is None:
        # Default to logs directory in project root
        project_root = os.path.abspath(os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
        log_dir = os.path.join(project_root, 'logs')
    
    # Create log directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)
    
    # Generate timestamped log filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f'mispm_{timestamp}.log')
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(log_level)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers to the root logger
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Set specific log levels for noisy libraries
    logging.getLogger('matplotlib').setLevel(logging.WARNING)
    logging.getLogger('PIL').setLevel(logging.WARNING)
    
    # Log startup message
    root_logger.info(f"Logging initialized, writing to: {log_file}")
    
    return log_file
