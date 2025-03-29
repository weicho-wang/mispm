#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MISPM - Main application entry point
"""

import sys
import os
import logging
from PyQt5.QtWidgets import QApplication
from mispmsrc.ui.main_window import MainWindow
from mispmsrc.logs import setup_logging
from mispmsrc.utils.error_reporter import handle_exception

def main():
    """Main function to start the MISPM application"""
    # Set up exception hook to catch unhandled exceptions
    sys._excepthook = sys.excepthook
    
    def exception_hook(exctype, value, traceback):
        """Custom exception hook to handle uncaught exceptions"""
        # Log the exception
        logging.error("Unhandled exception", exc_info=(exctype, value, traceback))
        
        # Show a user-friendly error dialog
        if app:  # Only try to show dialog if app exists
            handle_exception(value, "Unhandled exception", None, logging.getLogger())
            
        # Call the original exception hook
        sys._excepthook(exctype, value, traceback)
    
    # Replace the default exception hook
    sys.excepthook = exception_hook
    
    # Configure logging
    log_file = setup_logging()
    
    # Create QApplication instance - note it's defined in the outer scope 
    # so it can be referenced in the exception hook
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Log system information
    logging.info(f"Python version: {sys.version}")
    logging.info(f"Platform: {sys.platform}")
    logging.info(f"PyQt5 version: {app.applicationVersion()}")
    logging.info(f"Log file: {log_file}")
    
    try:
        # Create and show main window
        window = MainWindow()
        window.show()
        
        # Start event loop
        return_code = app.exec_()
        logging.info(f"Application exited with code: {return_code}")
        return return_code
        
    except Exception as e:
        # Handle any exceptions during startup
        logging.error("Error during application startup", exc_info=True)
        handle_exception(e, "Application startup failed", None, logging.getLogger())
        return 1

if __name__ == '__main__':
    sys.exit(main())
