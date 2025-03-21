#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
import datetime
from logging.handlers import RotatingFileHandler


def setup_logger(level=logging.INFO):
    """
    Set up logger for the application
    
    Args:
        level: Logging level (default: logging.INFO)
    """
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Format for logging
    log_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create a unique filename with date
    date_str = datetime.datetime.now().strftime('%Y%m%d')
    log_file = os.path.join(log_dir, f'spm_interface_{date_str}.log')
    
    # Set up file handler with rotation
    file_handler = RotatingFileHandler(
        log_file, 
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(log_format)
    
    # Set up console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_format)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers if any
    for hdlr in root_logger.handlers[:]:
        root_logger.removeHandler(hdlr)
    
    # Add handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    return root_logger


class Logger:
    """
    Logger class for easy logging in different modules
    """
    @staticmethod
    def get_logger(name):
        """
        Get a logger with the specified name
        
        Args:
            name: Name for the logger, usually __name__
            
        Returns:
            logging.Logger: Logger instance
        """
        return logging.getLogger(name) 