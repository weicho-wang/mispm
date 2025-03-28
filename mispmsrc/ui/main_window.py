#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import logging
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFileDialog, QMessageBox, QGroupBox, QStatusBar, QProgressBar,
    QTextEdit, QApplication, QComboBox, QInputDialog
)
from PyQt5.QtCore import Qt, pyqtSlot, QSize
from PyQt5.QtGui import QFont

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(project_root)

from mispmsrc.core.matlab_engine import MatlabEngine
from mispmsrc.utils.logger import Logger
from mispmsrc.ui.progress_manager import ProgressManager
from mispmsrc.ui.coreg_dialog import CoregisterDialog
from mispmsrc.ui.normalize_dialog import NormalizeDialog
from mispmsrc.ui.image_view import ImageView
from mispmsrc.ui.cl_analysis_dialog import CLAnalysisDialog
from mispmsrc.CLRefactoring.PIB_SUVr_CLs_calc import PIBAnalyzer

class LogWidget(QTextEdit):
    """Widget to display log messages"""
    
    def __init__(self, parent=None):
        super(LogWidget, self).__init__(parent)
        self.setReadOnly(True)
        self.setLineWrapMode(QTextEdit.NoWrap)
        self.setFont(QFont("Consolas", 9))
        
    def append_log(self, message, level="INFO"):
        """
        Append a log message with color based on level
        
        Args:
            message: Log message to append
            level: Log level (INFO, WARNING, ERROR)
        """
        color = "black"
        if level == "WARNING":
            color = "orange"
        elif level == "ERROR":
            color = "red"
        elif level == "SUCCESS":
            color = "green"
            
        self.append(f'<span style="color:{color};">{message}</span>')


class MainWindow(QMainWindow):
    """Main window for the SPM PyQt Interface"""
    
    def __init__(self):
        super(MainWindow, self).__init__()
        
        # Setup logger
        self.logger = logging.getLogger(__name__)
        
        # Initialize MATLAB engine
        self.matlab_engine = MatlabEngine()
        
        # Add ImageView instance
        self.image_view = ImageView(self)
        
        # Set up UI
        # self.run_script_btn = QPushButton("Run MATLAB Script")
        self.run_script_btn = QPushButton("LC Analysis")
        self.setup_ui()
        
        # Connect signals
        self.connect_signals()
        
        # Start MATLAB engine
        self.start_matlab_engine()
    
    def setup_ui(self):
        """Set up the UI components"""
        # Set window properties
        self.setWindowTitle("SPM PyQt Interface")
        self.setMinimumSize(1000, 700)
        
        # Create central widget with horizontal split layout
        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(5)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Left panel for controls
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(5)
        left_layout.setContentsMargins(2, 2, 2, 2)
        
        # Engine controls group
        engine_group = QGroupBox("MATLAB Engine")
        engine_layout = QVBoxLayout()
        self.engine_status_label = QLabel("Engine: Not running")
        self.start_engine_btn = QPushButton("Start Engine")
        self.stop_engine_btn = QPushButton("Stop Engine")
        engine_layout.addWidget(self.engine_status_label)
        engine_layout.addWidget(self.start_engine_btn)
        engine_layout.addWidget(self.stop_engine_btn)
        engine_group.setLayout(engine_layout)
        left_layout.addWidget(engine_group)
        
        # DICOM/NIFTI group
        dicom_group = QGroupBox("Convert DICOM To NIFTI")
        dicom_layout = QVBoxLayout()
        self.import_dicom_btn = QPushButton("Import DICOM")
        self.convert_nifti_btn = QPushButton("Convert To NiFTI")
        dicom_layout.addWidget(self.import_dicom_btn)
        dicom_layout.addWidget(self.convert_nifti_btn)
        dicom_group.setLayout(dicom_layout)
        left_layout.addWidget(dicom_group)
        
        # Image processing group
        image_group = QGroupBox("Image Processing")
        image_layout = QVBoxLayout()

        # 创建所有按钮
        self.load_nifti_btn = QPushButton("Load NIFTI")
        self.coregister_btn = QPushButton("Coregistration")
        self.normalise_btn = QPushButton("Normalise")
        self.set_origin_btn = QPushButton("Set Origin")
        self.check_reg_btn = QPushButton("Check Registration")
        self.run_script_btn = QPushButton("LC Analysis")  # LC Analysis 按钮
        
        # 添加按钮到布局，让它们左对齐
        for btn in [self.load_nifti_btn, self.coregister_btn, self.normalise_btn, 
                   self.set_origin_btn, self.check_reg_btn, self.run_script_btn]:
            btn_layout = QHBoxLayout()
            btn_layout.addWidget(btn)
            btn_layout.addStretch()
            image_layout.addLayout(btn_layout)
        
        image_group.setLayout(image_layout)
        left_layout.addWidget(image_group)
        
        # Add stretch to push everything up
        left_layout.addStretch()
        
        # Right panel for log
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        log_group = QGroupBox("Log")
        log_layout = QVBoxLayout()
        self.log_widget = LogWidget()
        log_layout.addWidget(self.log_widget)
        log_group.setLayout(log_layout)
        right_layout.addWidget(log_group)
        
        # Add panels to main layout with equal width
        main_layout.addWidget(left_panel, 1)  # stretch factor 1
        main_layout.addWidget(right_panel, 1)  # stretch factor 1
        
        # Set central widget
        self.setCentralWidget(central_widget)
        
        # Create status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        
        # Add progress bar to status bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(15)  # 减小进度条高度
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)  # 显示进度文字
        self.statusBar.addPermanentWidget(self.progress_bar)
        
        # Set initial button states
        self.update_button_states(False)
        
        # 创建进度管理器
        self.progress_manager = ProgressManager(self.progress_bar, self.statusBar)
        
        # 创建按钮列表以统一设置样式
        all_buttons = [
            self.start_engine_btn, 
            self.stop_engine_btn,
            self.import_dicom_btn,
            self.load_nifti_btn,
            self.coregister_btn,
            self.normalise_btn,
            self.set_origin_btn,
            self.check_reg_btn,
            self.run_script_btn,
            self.convert_nifti_btn  # 新增按钮
        ]
        
        # 统一设置所有按钮的样式
        for btn in all_buttons:
            btn.setFixedHeight(25)  # 统一高度
            btn.setFixedWidth(120)  # 统一宽度
        
        # 修改布局对齐方式
        engine_layout.addWidget(self.engine_status_label)
        engine_layout.addWidget(self.start_engine_btn, 0, Qt.AlignLeft)
        engine_layout.addWidget(self.stop_engine_btn, 0, Qt.AlignLeft)
        
        # DICOM转换布局修改
        dicom_layout.addWidget(self.import_dicom_btn, 0, Qt.AlignLeft)
        
        # Load NIFTI按钮布局修改
        image_layout.addWidget(self.load_nifti_btn, 0, Qt.AlignLeft)
        
        # Coregistration布局修改
        coreg_layout = QHBoxLayout()
        coreg_layout.addWidget(self.coregister_btn, 0)
        coreg_layout.addStretch(1)
        image_layout.addLayout(coreg_layout)
        
        # Normalisation布局修改
        normalise_layout = QHBoxLayout()
        normalise_layout.addWidget(self.normalise_btn, 0)
        normalise_layout.addStretch(1)
        image_layout.addLayout(normalise_layout)
        
        # Set Origin和Check Registration按钮布局修改
        other_btns_layout = QHBoxLayout()
        other_btns_layout.addWidget(self.set_origin_btn, 0)
        other_btns_layout.addWidget(self.check_reg_btn, 0)
        other_btns_layout.addStretch(1)
        image_layout.addLayout(other_btns_layout)
        
        # LC Analysis Script按钮布局修改
        left_layout.addWidget(self.run_script_btn, 0, Qt.AlignLeft)
    
    def connect_signals(self):
        """Connect UI signals to slots"""
        # MATLAB engine signals
        self.start_engine_btn.clicked.connect(self.start_matlab_engine)
        self.stop_engine_btn.clicked.connect(self.stop_matlab_engine)
        
        # Connect MATLAB engine signals
        self.matlab_engine.engine_started.connect(self.on_engine_started)
        self.matlab_engine.engine_error.connect(self.on_engine_error)
        self.matlab_engine.operation_progress.connect(self.on_operation_progress)
        self.matlab_engine.operation_completed.connect(self.on_operation_completed)
        
        # Button signals
        self.import_dicom_btn.clicked.connect(self.import_dicom)
        self.load_nifti_btn.clicked.connect(self.load_nifti)  # This will now handle both loading and importing
        self.coregister_btn.clicked.connect(self.coregister_images)
        self.normalise_btn.clicked.connect(self.normalise_image)
        self.set_origin_btn.clicked.connect(self.set_origin)
        self.check_reg_btn.clicked.connect(self.check_registration)
        self.run_script_btn.clicked.connect(self.run_matlab_script)
        self.convert_nifti_btn.clicked.connect(self.convert_to_nifti)  # 新增信号连接
    
    def update_button_states(self, engine_running):
        """
        Update button states based on MATLAB engine status
        
        Args:
            engine_running: Whether the MATLAB engine is running
        """
        self.start_engine_btn.setEnabled(not engine_running)
        self.stop_engine_btn.setEnabled(engine_running)
        
        # Image processing buttons
        self.import_dicom_btn.setEnabled(engine_running)
        self.load_nifti_btn.setEnabled(engine_running)
        self.coregister_btn.setEnabled(engine_running)
        self.normalise_btn.setEnabled(engine_running)
        self.set_origin_btn.setEnabled(engine_running)
        self.check_reg_btn.setEnabled(engine_running)
        self.convert_nifti_btn.setEnabled(engine_running)  # 新增按钮状态控制
    
    @pyqtSlot()
    def start_matlab_engine(self):
        """Start the MATLAB engine"""
        self.log_widget.append_log("Starting MATLAB engine...")
        self.engine_status_label.setText("MATLAB Engine: Starting...")
        
        try:
            # Start engine in a separate thread to avoid UI freezing
            success = self.matlab_engine.start_engine()  # Remove the timeout argument
            
            if not success:
                self.log_widget.append_log("Failed to start MATLAB engine", "ERROR")
                self.engine_status_label.setText("MATLAB Engine: Failed to start")
        except KeyboardInterrupt:
            self.log_widget.append_log("MATLAB engine start interrupted", "ERROR")
            self.engine_status_label.setText("MATLAB Engine: Start interrupted")
        except Exception as e:
            self.log_widget.append_log(f"Error starting MATLAB engine: {str(e)}", "ERROR")
            self.engine_status_label.setText("MATLAB Engine: Error starting")
    
    @pyqtSlot()
    def stop_matlab_engine(self):
        """Stop the MATLAB engine"""
        self.log_widget.append_log("Stopping MATLAB engine...")
        
        success = self.matlab_engine.stop_engine()
        
        if success:
            self.log_widget.append_log("MATLAB engine stopped")
            self.engine_status_label.setText("MATLAB Engine: Not running")
            self.update_button_states(False)
        else:
            self.log_widget.append_log("Failed to stop MATLAB engine", "ERROR")
    
    @pyqtSlot()
    def on_engine_started(self):
        """Handle MATLAB engine started signal"""
        self.log_widget.append_log("MATLAB engine started successfully", "SUCCESS")
        self.engine_status_label.setText("MATLAB Engine: Running")
        self.update_button_states(True)
    
    @pyqtSlot(str)
    def on_engine_error(self, error_message):
        """
        Handle MATLAB engine error signal
        
        Args:
            error_message: Error message from MATLAB engine
        """
        self.log_widget.append_log(f"MATLAB engine error: {error_message}", "ERROR")
    
    @pyqtSlot(str, int)
    def on_operation_progress(self, message, progress):
        """
        Handle operation progress signal
        
        Args:
            message: Progress message
            progress: Progress percentage (0-100)
        """
        self.log_widget.append_log(f"Progress: {message} ({progress}%)")
        self.statusBar.showMessage(message)
        
        # Update progress bar
        self.progress_bar.setValue(progress)
        self.progress_bar.setVisible(True)
        
        # Force UI update
        QApplication.processEvents()
    
    @pyqtSlot(str, bool)
    def on_operation_completed(self, message, success):
        """
        Handle operation completed signal
        
        Args:
            message: Completion message
            success: Whether the operation was successful
        """
        level = "SUCCESS" if success else "ERROR"
        self.log_widget.append_log(f"Operation completed: {message}", level)
        
        # Hide progress bar
        self.progress_bar.setVisible(False)
        
        # Show completion message
        self.statusBar.showMessage(message, 5000)  # Show for 5 seconds
    
    @pyqtSlot()
    def import_dicom(self):
        """Import DICOM files and convert to NIFTI"""
        self.log_widget.append_log("Importing DICOM files...")
        
        # Ask user if they want to select files or a directory
        msgBox = QMessageBox()
        msgBox.setWindowTitle("Import DICOM")
        msgBox.setText("Would you like to select individual DICOM files or a directory?")
        folder_btn = msgBox.addButton("Directory", QMessageBox.ActionRole)
        files_btn = msgBox.addButton("Files", QMessageBox.ActionRole)
        msgBox.addButton(QMessageBox.Cancel)
        msgBox.exec_()
        
        if msgBox.clickedButton() == QMessageBox.Cancel:
            return
        
        if msgBox.clickedButton() == folder_btn:
            # Select directory
            directory = QFileDialog.getExistingDirectory(self, "Select DICOM Directory")
            if directory:
                self.log_widget.append_log(f"Selected DICOM directory: {directory}")
                self.matlab_engine.import_dicom(directory)
        elif msgBox.clickedButton() == files_btn:
            # Select files
            files, _ = QFileDialog.getOpenFileNames(self, "Select DICOM Files", "", "DICOM Files (*.dcm)")
            if files:
                self.log_widget.append_log(f"Selected DICOM files: {', '.join(files)}")
                self.matlab_engine.import_dicom(files)
    
    @pyqtSlot()
    def load_nifti(self):
        """Load NIFTI file"""
        self.log_widget.append_log("Loading NIFTI file...")
        
        file_path, _ = QFileDialog.getOpenFileName(self, "Select NIFTI File", "", "NIFTI Files (*.nii *.nii.gz)")
        if file_path:
            self.log_widget.append_log(f"Selected NIFTI file: {file_path}")
            self.matlab_engine.load_nifti(file_path)
    
    @pyqtSlot()
    def coregister_images(self):
        """Coregister images"""
        self.log_widget.append_log("Coregistering images...")
        
        dialog = CoregisterDialog(self)
        dialog.coregister_started.connect(self._handle_coregistration)  # Changed
        dialog.exec_()
        
    def _handle_coregistration(self, params):
        """Handle coregistration parameters and call engine"""
        try:
            # Validate input files exist
            ref_image = params['ref_image']
            source_image = params['source_image']
            
            if not os.path.exists(ref_image):
                raise ValueError(f"Reference image not found: {ref_image}")
            if not os.path.exists(source_image):
                raise ValueError(f"Source image not found: {source_image}")
                
            self.log_widget.append_log(f"Starting coregistration with:")
            self.log_widget.append_log(f"Reference: {ref_image}")
            self.log_widget.append_log(f"Source: {source_image}")
            
            success = self.matlab_engine.coregister_images(
                ref_image,
                source_image,
                params.get('cost_function', 'nmi').lower().replace(' ', '_')
            )
            
            if not success:
                self.log_widget.append_log("Coregistration failed", "ERROR")
                
        except Exception as e:
            self.log_widget.append_log(f"Coregistration error: {str(e)}", "ERROR")

    @pyqtSlot()
    def normalise_image(self):
        """Normalise image"""
        self.log_widget.append_log("Normalising image...")
        
        dialog = NormalizeDialog(self)
        dialog.normalise_started.connect(self._handle_normalization)
        dialog.exec_()

    @pyqtSlot(dict)
    def _handle_normalization(self, params):
        """Handle normalization parameters and report errors"""
        try:
            self.log_widget.append_log("Starting normalization...")
            if not self.matlab_engine.normalize_image(params):
                self.log_widget.append_log(
                    "Normalization failed - check MATLAB console for details",
                    "ERROR"
                )
                QMessageBox.critical(
                    self,
                    "Normalization Error",
                    "Failed to complete normalization.\n\n"
                    "Common causes:\n"
                    "- Invalid source image\n"
                    "- Missing write permissions\n"
                    "- SPM estimation failure\n\n"
                    "Check the log for details."
                )
            else:
                self.log_widget.append_log(
                    "Normalization completed successfully",
                    "SUCCESS"
                )
                
        except Exception as e:
            self.log_widget.append_log(
                f"Normalization error: {str(e)}",
                "ERROR"
            )
            QMessageBox.critical(
                self,
                "Normalization Error",
                f"Error during normalization:\n\n{str(e)}"
            )
    
    @pyqtSlot()
    def set_origin(self):
        """Set origin of the image"""
        self.log_widget.append_log("Setting origin of the image...")
        
        file_path, _ = QFileDialog.getOpenFileName(self, "Select NIFTI File", "", "NIFTI Files (*.nii *.nii.gz)")
        if file_path:
            self.log_widget.append_log(f"Selected NIFTI file: {file_path}")
            self.matlab_engine.set_origin(file_path)
    
    @pyqtSlot()
    def check_registration(self):
        """Check registration of images"""
        self.log_widget.append_log("Checking registration of images...")
        
        file_paths, _ = QFileDialog.getOpenFileNames(self, "Select NIFTI Files", "", "NIFTI Files (*.nii *.nii.gz)")
        if file_paths:
            self.log_widget.append_log(f"Selected NIFTI files: {', '.join(file_paths)}")
            self.matlab_engine.check_registration(file_paths)
    
    @pyqtSlot()
    def run_matlab_script(self):
        """Run CL analysis dialog"""
        try:
            dialog = CLAnalysisDialog(self)
            dialog.analysis_started.connect(self.run_cl_analysis)
            dialog.exec_()
        except Exception as e:
            self.log_widget.append_log(f"Error opening CL Analysis dialog: {str(e)}", "ERROR")

    def run_cl_analysis(self, params):
        """Execute CL analysis with the given parameters"""
        self.log_widget.append_log("Starting CL analysis...")
        try:
            analyzer = PIBAnalyzer()
            analyzer.run_analysis(
                params['ref_path'],
                params['roi_path'], 
                params['ad_dir'],
                params['yc_dir'],
                params['standard_data']
            )
            self.log_widget.append_log("CL analysis completed successfully", "SUCCESS")
        except Exception as e:
            self.log_widget.append_log(f"Error during CL analysis: {str(e)}", "ERROR")
    
    @pyqtSlot()
    def convert_to_nifti(self):
        """Convert DICOM to NIFTI with improved error handling and progress feedback"""
        try:
            # Select DICOM directory
            dicom_dir = QFileDialog.getExistingDirectory(
                self, 
                "Select DICOM Directory",
                "",
                QFileDialog.ShowDirsOnly
            )
            if not dicom_dir:
                return

            # Select output directory
            output_dir = QFileDialog.getExistingDirectory(
                self, 
                "Select Output Directory",
                "",
                QFileDialog.ShowDirsOnly
            )
            if not output_dir:
                return

            # Log the selected directories
            self.log_widget.append_log(f"Selected DICOM directory: {dicom_dir}")
            self.log_widget.append_log(f"Selected output directory: {output_dir}")

            # Show progress
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            QApplication.processEvents()  # Allow GUI update

            # Convert files
            result_files = self.matlab_engine.convert_to_nifti(dicom_dir, output_dir)

            # Check results
            if result_files:
                self.log_widget.append_log(
                    f"Successfully created {len(result_files)} NIFTI files:",
                    "SUCCESS"
                )
                for f in result_files:
                    self.log_widget.append_log(f"  {f}")
            else:
                self.log_widget.append_log(
                    "No NIFTI files were created. Check the DICOM files and try again.",
                    "ERROR"
                )

        except Exception as e:
            self.log_widget.append_log(f"Error during conversion: {str(e)}", "ERROR")
            self.progress_bar.setVisible(False)
        finally:
            self.progress_bar.setVisible(False)
            QApplication.processEvents()

if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Start event loop
    sys.exit(app.exec_())