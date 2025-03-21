#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from ui.main_window import MainWindow
from utils.logger import setup_logger


def main():
    """Main entry point for the application"""
    # Setup logger
    setup_logger()
    logger = logging.getLogger(__name__)
    logger.info("Starting SPM PyQt Interface")

    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("SPM PyQt Interface")
    app.setStyle("Fusion")  # Use Fusion style for a modern look
    
    # Set stylesheet for a modern look
    with open(os.path.join(os.path.dirname(__file__), 'resources/style.qss'), 'r') as f:
        app.setStyleSheet(f.read())
    
    # Create main window
    window = MainWindow()
    window.show()
    
    # Start event loop
    sys.exit(app.exec_())


if __name__ == "__main__":
    main() 