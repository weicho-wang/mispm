from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import Qt

class ImageView(QWidget):
    """Widget for displaying SPM image views"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_image = None
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.setStyleSheet("background-color: white;")
        
    def display_image(self, image_path):
        """Display an image using SPM's display functionality"""
        self.current_image = image_path
        # The actual display is handled by the MATLAB engine
        return True
