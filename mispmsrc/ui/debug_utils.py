"""
Debug utilities for the MISPM UI components
"""

import logging
import os
import sys
import traceback
from PyQt5.QtWidgets import QMessageBox

logger = logging.getLogger(__name__)

def setup_basic_logging():
    """Set up basic logging for debugging UI components"""
    # Create basic console logger if not already configured
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler(sys.stdout)]
        )
    
    return logging.getLogger()

def show_error_message(parent, title, message, exception=None):
    """Show an error message dialog with exception details if provided"""
    if exception:
        detail_message = f"Error: {str(exception)}\n\nTraceback:\n{traceback.format_exc()}"
        logger.error(f"{message}: {str(exception)}\n{traceback.format_exc()}")
    else:
        detail_message = None
        logger.error(message)
    
    msg_box = QMessageBox(parent)
    msg_box.setIcon(QMessageBox.Critical)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    
    if detail_message:
        msg_box.setDetailedText(detail_message)
    
    msg_box.exec_()

def debug_qt_object(obj, prefix=""):
    """Print debug information about a Qt object"""
    class_name = obj.__class__.__name__
    object_name = obj.objectName() if hasattr(obj, "objectName") else "unnamed"
    is_visible = obj.isVisible() if hasattr(obj, "isVisible") else "unknown"
    is_enabled = obj.isEnabled() if hasattr(obj, "isEnabled") else "unknown"
    
    logger.info(f"{prefix}{class_name} '{object_name}': visible={is_visible}, enabled={is_enabled}")
    
    # If it's a layout, print information about its children
    if hasattr(obj, "count"):
        for i in range(obj.count()):
            item = obj.itemAt(i)
            if item and item.widget():
                debug_qt_object(item.widget(), prefix + "  ")
