"""
Error reporting and handling utilities for MISPM
"""

import logging
import os
import sys
import traceback
import datetime
from PyQt5.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt

class ErrorLogger:
    """Static class for logging errors and creating error reports"""
    
    @staticmethod
    def setup_logging(log_dir=None):
        """Set up logging configuration"""
        if log_dir is None:
            # Default to logs directory in project root
            log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'logs')
        
        # Create log directory if it doesn't exist
        os.makedirs(log_dir, exist_ok=True)
        
        # Generate timestamped log filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f'mispm_{timestamp}.log')
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        # Set matplotlib logging to WARNING to reduce noise
        logging.getLogger('matplotlib').setLevel(logging.WARNING)
        
        return log_file
    
    @staticmethod
    def log_exception(e, logger=None):
        """Log an exception with traceback"""
        if logger is None:
            logger = logging.getLogger(__name__)
            
        logger.error(f"Exception: {str(e)}")
        logger.error("Traceback: " + traceback.format_exc())
        
    @staticmethod
    def create_error_report(exception, context=None):
        """Create a detailed error report"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report = [
            f"=== MISPM Error Report ===",
            f"Timestamp: {timestamp}",
            f"",
            f"Error: {str(exception)}",
            f"",
            f"Python: {sys.version}",
            f"Platform: {sys.platform}",
            f""
        ]
        
        # Add context information if provided
        if context:
            report.extend([
                f"Context:",
                f"{context}",
                f""
            ])
        
        # Add traceback
        report.extend([
            f"Traceback:",
            traceback.format_exc(),
            f"",
            f"=== End of Error Report ==="
        ])
        
        return "\n".join(report)

class ErrorDialog(QDialog):
    """Dialog for displaying error information"""
    
    def __init__(self, title, message, details=None, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle(title)
        self.setMinimumSize(600, 400)
        
        layout = QVBoxLayout(self)
        
        # Error icon and message
        message_layout = QHBoxLayout()
        icon_label = QLabel()
        icon_label.setPixmap(self.style().standardIcon(self.style().SP_MessageBoxCritical).pixmap(32, 32))
        message_layout.addWidget(icon_label)
        message_layout.addWidget(QLabel(message))
        layout.addLayout(message_layout)
        
        # Details section (collapsible)
        if details:
            details_edit = QTextEdit()
            details_edit.setReadOnly(True)
            details_edit.setPlainText(details)
            details_edit.setLineWrapMode(QTextEdit.NoWrap)
            layout.addWidget(details_edit)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        copy_btn = QPushButton("Copy to Clipboard")
        copy_btn.clicked.connect(lambda: self._copy_to_clipboard(details if details else message))
        
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        ok_btn.setDefault(True)
        
        button_layout.addWidget(copy_btn)
        button_layout.addStretch()
        button_layout.addWidget(ok_btn)
        
        layout.addLayout(button_layout)
    
    def _copy_to_clipboard(self, text):
        """Copy text to clipboard"""
        from PyQt5.QtGui import QGuiApplication
        QGuiApplication.clipboard().setText(text)

def show_error_dialog(title, message, details=None, parent=None):
    """Show error dialog with details"""
    dialog = ErrorDialog(title, message, details, parent)
    return dialog.exec_()

def format_error_for_user(e, context=None):
    """Format error message for user display"""
    # Get the error type name
    error_type = type(e).__name__
    
    # Get a user-friendly message
    user_message = str(e)
    
    # For empty messages, use the error type
    if not user_message:
        user_message = f"An error of type {error_type} occurred"
    
    # Add context if provided
    if context:
        user_message = f"{context}: {user_message}"
    
    return user_message

def handle_exception(e, context=None, parent=None, logger=None):
    """Handle exception with logging and user notification"""
    if logger is None:
        logger = logging.getLogger(__name__)
    
    # Log the exception
    ErrorLogger.log_exception(e, logger)
    
    # Create detailed error report
    details = ErrorLogger.create_error_report(e, context)
    
    # Format user-friendly message
    message = format_error_for_user(e, context)
    
    # Show error dialog
    show_error_dialog("Error", message, details, parent)
