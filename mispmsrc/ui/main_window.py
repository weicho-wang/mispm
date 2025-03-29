#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import logging
import glob
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFileDialog, QMessageBox, QGroupBox, QStatusBar, QProgressBar,
    QTextEdit, QApplication, QComboBox, QInputDialog, QDialog, QGridLayout, QDoubleSpinBox
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
        
        # 新增批处理按钮
        self.batch_coregister_btn = QPushButton("Batch Coregister")
        self.batch_normalise_btn = QPushButton("Batch Normalise")
        self.batch_set_origin_btn = QPushButton("Batch Set Origin")
        
        # 添加按钮到布局，让它们左对齐
        for btn in [self.load_nifti_btn, self.coregister_btn, self.normalise_btn, 
                   self.set_origin_btn, self.check_reg_btn, self.run_script_btn,
                   self.batch_coregister_btn, self.batch_normalise_btn, self.batch_set_origin_btn]:
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
            self.convert_nifti_btn,  # 新增按钮
            self.batch_coregister_btn,
            self.batch_normalise_btn,
            self.batch_set_origin_btn
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
        self.run_script_btn.clicked.connect(self.show_cl_analysis_dialog)
        self.convert_nifti_btn.clicked.connect(self.convert_to_nifti)  # 新增信号连接
        
        # 新增批处理按钮信号连接
        self.batch_coregister_btn.clicked.connect(self.batch_coregister_images)
        self.batch_normalise_btn.clicked.connect(self.batch_normalise_images)
        self.batch_set_origin_btn.clicked.connect(self.batch_set_origin)
    
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
        
        # 批处理按钮
        self.batch_coregister_btn.setEnabled(engine_running)
        self.batch_normalise_btn.setEnabled(engine_running)
        self.batch_set_origin_btn.setEnabled(engine_running)
    
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
    def show_cl_analysis_dialog(self):
        """Show CL analysis parameters dialog"""
        try:
            self.log_widget.append_log("Opening CL analysis dialog...")
            
            # Import here to avoid circular imports
            from mispmsrc.ui.cl_analysis_dialog import CLAnalysisDialog
            
            # Initialize dialog with properly configured logger
            dialog = CLAnalysisDialog(self)
            
            # Connect the signal
            dialog.analysis_started.connect(self.run_cl_analysis)
            
            # Show the dialog
            if dialog.exec_() == QDialog.Accepted:
                self.log_widget.append_log("CL analysis parameters set", "INFO")
            else:
                self.log_widget.append_log("CL analysis canceled", "INFO")
        
        except Exception as e:
            self.log_widget.append_log(f"Error showing CL analysis dialog: {str(e)}", "ERROR")
            self.logger.error(f"Error in CL analysis dialog: {str(e)}", exc_info=True)
            
            # Import and use the error dialog
            from mispmsrc.utils.error_reporter import handle_exception
            handle_exception(e, "Failed to open CL analysis dialog", self, self.logger)

    def run_cl_analysis(self, params):
        """Execute CL analysis with the given parameters"""
        self.log_widget.append_log("Starting CL analysis...")
        try:
            # Add progress tracking
            self.progress_manager.start_operation("CL Analysis")
            self.progress_manager.update_progress("Loading mask files...", 10)
            
            # Prepare analyzer object
            from mispmsrc.CLRefactoring.PIB_SUVr_CLs_calc import PIBAnalyzer
            analyzer = PIBAnalyzer()
            
            # Validate input parameters
            for param_name, param_value in params.items():
                if param_name != 'patient_info' and not os.path.exists(param_value):
                    self.log_widget.append_log(f"Error: {param_name} path not found: {param_value}", "ERROR")
                    self.progress_manager.complete_operation(f"Error: {param_name} path not found", False)
                    return
            
            self.progress_manager.update_progress("Analyzing PET images...", 30)
            
            # Run analysis with progress updates using a thread
            from PyQt5.QtCore import QThread, pyqtSignal
            
            class AnalysisThread(QThread):
                finished = pyqtSignal(bool, str)
                progress = pyqtSignal(str, int)
                
                def __init__(self, analyzer, params):
                    super().__init__()
                    self.analyzer = analyzer
                    self.params = params
                    self.exception = None
                    
                def run(self):
                    try:
                        # Setup log capture for progress updates
                        import logging
                        class ProgressHandler(logging.Handler):
                            def __init__(self, progress_signal):
                                super().__init__()
                                self.progress_signal = progress_signal
                                self.steps = {
                                    'mask': 30,
                                    'suvr': 40,
                                    'cl': 60,
                                    'standard': 70,
                                    'correlation': 80,
                                    'report': 90
                                }
                                
                            def emit(self, record):
                                msg = self.format(record)
                                progress = None
                                
                                # Determine progress percentage based on message content
                                for key, value in self.steps.items():
                                    if key in msg.lower():
                                        progress = value
                                        break
                                        
                                if progress:
                                    self.progress_signal.emit(msg, progress)
                        
                        # Add our handler to the logger
                        handler = ProgressHandler(self.progress)
                        handler.setLevel(logging.INFO)
                        logging.getLogger().addHandler(handler)
                        
                        # Run the analysis
                        result = self.analyzer.run_analysis(
                            self.params['ref_path'],
                            self.params['roi_path'],
                            self.params['ad_dir'],
                            self.params['yc_dir'],
                            self.params['standard_data'],
                            self.params.get('patient_info')
                        )
                        
                        # Remove our custom handler
                        logging.getLogger().removeHandler(handler)
                        
                        # Get output directory for finding reports
                        output_dir = self.analyzer.plotter.output_dir
                        self.finished.emit(result, output_dir)
                        
                    except Exception as e:
                        import traceback
                        self.exception = (str(e), traceback.format_exc())
                        self.finished.emit(False, "")
                        
                        # Remove our custom handler in case of error
                        try:
                            logging.getLogger().removeHandler(handler)
                        except:
                            pass
            
            # Create and connect thread
            self.analysis_thread = AnalysisThread(analyzer, params)
            self.analysis_thread.progress.connect(self.progress_manager.update_progress)
            self.analysis_thread.finished.connect(self._on_analysis_finished)
            
            # Start thread
            self.analysis_thread.start()
            
        except Exception as e:
            self.log_widget.append_log(f"Error in CL analysis: {str(e)}", "ERROR")
            self.progress_manager.complete_operation("CL Analysis failed", False)
            import traceback
            self.logger.error(traceback.format_exc())

    def _on_analysis_finished(self, success, output_dir):
        """Handle analysis thread completion"""
        if success:
            self.log_widget.append_log("CL analysis completed successfully", "SUCCESS")
            self.progress_manager.complete_operation("CL Analysis completed", True)
            
            # Get the report files
            report_files = self._get_latest_report_files(output_dir)
            
            if report_files:
                self.log_widget.append_log(f"Generated {len(report_files)} report files", "SUCCESS")
                
                # Optional: Give the UI time to update before displaying files
                from PyQt5.QtCore import QTimer
                QTimer.singleShot(500, lambda: self._display_report_files(report_files))
            else:
                self.log_widget.append_log("No report files were generated", "WARNING")
        else:
            # Check if we have exception details
            if hasattr(self.analysis_thread, 'exception') and self.analysis_thread.exception:
                error_msg, traceback_text = self.analysis_thread.exception
                self.log_widget.append_log(f"Error in CL analysis: {error_msg}", "ERROR")
                self.logger.error(traceback_text)
            else:
                self.log_widget.append_log("CL analysis failed", "ERROR")
                
            self.progress_manager.complete_operation("CL Analysis failed", False)

    def _get_latest_report_files(self, output_dir):
        """Get the latest report files generated in the output directory
        
        Returns:
            list: Paths to the latest report files
        """
        import glob
        import time
        
        if not output_dir or not os.path.exists(output_dir):
            self.log_widget.append_log(f"Output directory not found: {output_dir}", "ERROR")
            return []
            
        self.log_widget.append_log(f"Searching for report files in {output_dir}...", "INFO")
        
        # Get all output files with recognized extensions in the output directory
        all_files = []
        for ext in ['*.pdf', '*.png', '*.jpg', '*.svg']:
            all_files.extend(glob.glob(os.path.join(output_dir, ext)))
        
        if not all_files:
            self.log_widget.append_log("No report files found in output directory", "WARNING")
            return []
            
        # Filter files generated in the last minute (assuming reports were just created)
        current_time = time.time()
        recent_files = [f for f in all_files if os.path.getmtime(f) > current_time - 60]
        
        # Sort by modification time (newest first)
        recent_files.sort(key=os.path.getmtime, reverse=True)
        
        if recent_files:
            self.log_widget.append_log(f"Found {len(recent_files)} recent report files", "INFO")
            for f in recent_files[:5]:  # Log first 5 files
                ext = os.path.splitext(f)[1].lower()
                file_size = os.path.getsize(f)
                self.log_widget.append_log(f"  {os.path.basename(f)} ({ext}, {file_size} bytes)", "INFO")
        else:
            # If no recent files found, return oldest files as fallback
            self.log_widget.append_log("No recent report files found, using oldest files as fallback", "WARNING")
            all_files.sort(key=os.path.getmtime)  # Sort by time (oldest first)
            recent_files = all_files[:5]  # Take up to 5 oldest files
        
        # Return up to 5 most recent files
        return recent_files[:5]

    def _display_report_files(self, file_paths):
        """Display the report files using the system's default viewer
        
        Args:
            file_paths: List of paths to report files
        """
        if not file_paths:
            self.log_widget.append_log("No report files to display", "WARNING")
            return
        
        self.log_widget.append_log(f"Opening report files...", "SUCCESS")
        
        # Choose which file to open - prefer summary report if available
        files_to_open = []
        summary_file = next((f for f in file_paths if 'summary' in f.lower() or 'report' in f.lower()), None)
        
        if summary_file:
            self.log_widget.append_log(f"Found summary report: {os.path.basename(summary_file)}", "INFO")
            # Add summary report first
            files_to_open.append(summary_file)
            # Add other reports (up to 2 more)
            files_to_open.extend([f for f in file_paths[:2] if f != summary_file])
        else:
            # Just use the first 3 files
            self.log_widget.append_log("No summary report found, using available files", "INFO")
            files_to_open = file_paths[:3]
        
        # Open files with system viewer
        for file_path in files_to_open:
            try:
                # Check if file exists and has non-zero size
                if not os.path.exists(file_path):
                    self.log_widget.append_log(f"File not found: {file_path}", "ERROR")
                    continue
                    
                if os.path.getsize(file_path) == 0:
                    self.log_widget.append_log(f"Empty file: {file_path}", "ERROR")
                    continue
                    
                ext = os.path.splitext(file_path)[1].lower()
                file_size = os.path.getsize(file_path)
                self.log_widget.append_log(f"Opening file: {os.path.basename(file_path)} ({ext} format, {file_size} bytes)", "INFO")
                
                # Use platform-specific methods to open file
                if sys.platform == 'win32':
                    os.startfile(file_path)
                elif sys.platform == 'darwin':  # macOS
                    os.system(f'open "{file_path}"')
                else:  # Linux
                    os.system(f'xdg-open "{file_path}"')
            except Exception as e:
                self.log_widget.append_log(f"Error opening file: {str(e)}", "ERROR")
        
        # Inform user about report location
        if file_paths:
            report_dir = os.path.dirname(file_paths[0])
            self.log_widget.append_log(f"All reports saved in: {report_dir}", "SUCCESS")
            
            # Determine report format from files
            formats = set(os.path.splitext(f)[1].lower() for f in file_paths)
            format_str = ", ".join(f.replace('.', '').upper() for f in formats)
            self.log_widget.append_log(f"Report format(s): {format_str}", "INFO")

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
    
    @pyqtSlot()
    def batch_coregister_images(self):
        """批量协配图像"""
        self.log_widget.append_log("Batch coregistering images...")
        
        # 选择参考图像
        ref_image, _ = QFileDialog.getOpenFileName(self, "Select Reference Image", "", "NIFTI Files (*.nii *.nii.gz)")
        if not ref_image:
            return
            
        # 选择源图像目录
        source_dir = QFileDialog.getExistingDirectory(self, "Select Directory with Source Images")
        if not source_dir:
            return
            
        # 获取目录中的所有NIFTI文件
        source_files = []
        for ext in ['*.nii', '*.nii.gz']:
            source_files.extend(glob.glob(os.path.join(source_dir, ext)))
            
        if not source_files:
            self.log_widget.append_log("No NIFTI files found in selected directory", "WARNING")
            return
            
        self.log_widget.append_log(f"Found {len(source_files)} NIFTI files to coregister")
        self.log_widget.append_log(f"Reference image: {ref_image}")
        
        # 选择协配参数
        cost_function = self._select_cost_function()
        
        # 处理每个文件
        success_count = 0
        error_count = 0
        
        for i, source_file in enumerate(source_files):
            try:
                self.log_widget.append_log(f"Coregistering {i+1}/{len(source_files)}: {os.path.basename(source_file)}")
                self.progress_manager.update_progress(f"Coregistering {os.path.basename(source_file)}", 
                                                     int((i / len(source_files)) * 100))
                                                     
                success = self.matlab_engine.coregister_images(ref_image, source_file, cost_function)
                
                if success:
                    success_count += 1
                else:
                    error_count += 1
                    self.log_widget.append_log(f"Failed to coregister {source_file}", "ERROR")
            except Exception as e:
                error_count += 1
                self.log_widget.append_log(f"Error coregistering {source_file}: {str(e)}", "ERROR")
        
        # 完成后的汇总信息
        self.progress_manager.complete_operation(
            f"Completed batch coregistration: {success_count} successful, {error_count} failed", 
            error_count == 0
        )
    
    def _select_cost_function(self):
        """选择协配的代价函数"""
        options = ["Mutual Information", "Normalised Mutual Information", 
                  "Entropy Correlation Coefficient", "Normalised Cross Correlation"]
        cost_function, ok = QInputDialog.getItem(
            self, "Select Cost Function", "Cost Function:", options, 1, False
        )
        if ok and cost_function:
            return cost_function.lower().replace(' ', '_')
        return "nmi"  # 默认返回标准化互信息
    
    @pyqtSlot()
    def batch_normalise_images(self):
        """批量标准化图像 - 只处理文件夹中带r前缀的图像"""
        self.log_widget.append_log("Batch normalizing images...")
        
        # 选择模板图像
        template_path, _ = QFileDialog.getOpenFileName(
            self, "Select Template Image", "", "NIFTI Files (*.nii *.nii.gz)"
        )
        if not template_path:
            return
            
        # 选择源图像目录
        source_dir = QFileDialog.getExistingDirectory(self, "Select Directory with Source Images")
        if not source_dir:
            return
            
        # 获取目录中的所有带r前缀的NIFTI文件
        source_files = []
        for ext in ['r*.nii', 'r*.nii.gz']:
            source_files.extend(glob.glob(os.path.join(source_dir, ext)))
            
        if not source_files:
            self.log_widget.append_log("No coregistered files (with 'r' prefix) found in selected directory", "WARNING")
            return
            
        self.log_widget.append_log(f"Found {len(source_files)} coregistered files to normalize")
        self.log_widget.append_log(f"Template image: {template_path}")
        
        # 处理每个文件
        success_count = 0
        error_count = 0
        
        # 构建基本参数
        params = {
            'template_path': template_path,
            'source_smoothing': 8,
            'template_smoothing': 0,
            'nonlinear_cutoff': 25,
            'nonlinear_iterations': 16,
            'nonlinear_reg': 1,
            'preserve': 0,
            'prefix': 'w'
        }
        
        for i, source_file in enumerate(source_files):
            try:
                # 只处理以r开头的文件
                filename = os.path.basename(source_file)
                if not filename.startswith('r'):
                    self.log_widget.append_log(f"Skipping non-coregistered file: {filename}", "INFO")
                    continue
                    
                self.log_widget.append_log(f"Normalizing {i+1}/{len(source_files)}: {filename}")
                self.progress_manager.update_progress(f"Normalizing {filename}", 
                                                     int((i / len(source_files)) * 100))
                                                     
                # 更新源图像路径
                current_params = params.copy()
                current_params['source_image'] = source_file
                
                success = self.matlab_engine.normalize_image(current_params)
                
                if success:
                    success_count += 1
                else:
                    error_count += 1
                    self.log_widget.append_log(f"Failed to normalize {source_file}", "ERROR")
            except Exception as e:
                error_count += 1
                self.log_widget.append_log(f"Error normalizing {source_file}: {str(e)}", "ERROR")
        
        # 完成后的汇总信息
        self.progress_manager.complete_operation(
            f"Completed batch normalization: {success_count} successful, {error_count} failed", 
            error_count == 0
        )
    
    @pyqtSlot()
    def batch_set_origin(self):
        """批量设置图像原点"""
        self.log_widget.append_log("Batch setting image origins...")
        
        # 选择图像目录
        image_dir = QFileDialog.getExistingDirectory(self, "Select Directory with Images")
        if not image_dir:
            return
            
        # 获取目录中的所有NIFTI文件
        image_files = []
        for ext in ['*.nii', '*.nii.gz']:
            image_files.extend(glob.glob(os.path.join(image_dir, ext)))
            
        if not image_files:
            self.log_widget.append_log("No NIFTI files found in selected directory", "WARNING")
            return
            
        self.log_widget.append_log(f"Found {len(image_files)} NIFTI files to process")
        
        # 获取坐标
        coordinates = self._get_origin_coordinates()
        if not coordinates:
            return
            
        # 处理每个文件
        success_count = 0
        error_count = 0
        
        for i, image_file in enumerate(image_files):
            try:
                self.log_widget.append_log(f"Setting origin {i+1}/{len(image_files)}: {os.path.basename(image_file)}")
                self.progress_manager.update_progress(f"Setting origin for {os.path.basename(image_file)}", 
                                                     int((i / len(image_files)) * 100))
                                                     
                success = self.matlab_engine.set_origin(image_file, coordinates)
                
                if success:
                    success_count += 1
                else:
                    error_count += 1
                    self.log_widget.append_log(f"Failed to set origin for {image_file}", "ERROR")
            except Exception as e:
                error_count += 1
                self.log_widget.append_log(f"Error setting origin for {image_file}: {str(e)}", "ERROR")
        
        # 完成后的汇总信息
        self.progress_manager.complete_operation(
            f"Completed batch origin setting: {success_count} successful, {error_count} failed", 
            error_count == 0
        )
    
    def _get_origin_coordinates(self):
        """获取原点坐标"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Set Origin Coordinates")
        layout = QVBoxLayout(dialog)
        
        # 添加坐标输入
        coord_layout = QGridLayout()
        coord_layout.addWidget(QLabel("X:"), 0, 0)
        coord_layout.addWidget(QLabel("Y:"), 1, 0)
        coord_layout.addWidget(QLabel("Z:"), 2, 0)
        
        x_spin = QDoubleSpinBox()
        y_spin = QDoubleSpinBox()
        z_spin = QDoubleSpinBox()
        
        for spin in [x_spin, y_spin, z_spin]:
            spin.setRange(-1000, 1000)
            spin.setValue(0)
            spin.setDecimals(1)
            spin.setSingleStep(1)
        
        coord_layout.addWidget(x_spin, 0, 1)
        coord_layout.addWidget(y_spin, 1, 1)
        coord_layout.addWidget(z_spin, 2, 1)
        
        layout.addLayout(coord_layout)
        
        # 添加按钮
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        
        ok_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)
        
        layout.addLayout(btn_layout)
        
        # 执行对话框
        if dialog.exec_():
            return [x_spin.value(), y_spin.value(), z_spin.value()]
        return None
        
    @pyqtSlot()
    def batch_convert_to_nifti(self):
        """批量转换DICOM到NIFTI"""
        try:
            # 选择包含多个DICOM目录的父目录
            parent_dir = QFileDialog.getExistingDirectory(
                self, 
                "Select Parent Directory Containing Multiple DICOM Folders",
                "",
                QFileDialog.ShowDirsOnly
            )
            if not parent_dir:
                return

            # 选择输出目录
            output_dir = QFileDialog.getExistingDirectory(
                self, 
                "Select Output Directory",
                "",
                QFileDialog.ShowDirsOnly
            )
            if not output_dir:
                return

            # 获取所有子目录
            dicom_dirs = [d for d in os.listdir(parent_dir) 
                         if os.path.isdir(os.path.join(parent_dir, d))]
            
            if not dicom_dirs:
                self.log_widget.append_log(f"No subdirectories found in {parent_dir}", "WARNING")
                return
                
            self.log_widget.append_log(f"Found {len(dicom_dirs)} subdirectories to process")
            
            # 处理每个子目录
            success_count = 0
            error_count = 0
            
            for i, dicom_dir_name in enumerate(dicom_dirs):
                dicom_dir = os.path.join(parent_dir, dicom_dir_name)
                subject_output_dir = os.path.join(output_dir, dicom_dir_name)
                
                try:
                    # 创建输出子目录
                    os.makedirs(subject_output_dir, exist_ok=True)
                    
                    self.log_widget.append_log(f"Converting {i+1}/{len(dicom_dirs)}: {dicom_dir_name}")
                    self.progress_manager.update_progress(
                        f"Converting {dicom_dir_name}", 
                        int((i / len(dicom_dirs)) * 100)
                    )
                    
                    # 执行转换
                    result_files = self.matlab_engine.convert_to_nifti(dicom_dir, subject_output_dir)
                    
                    if result_files:
                        success_count += 1
                        self.log_widget.append_log(
                            f"Successfully converted {len(result_files)} files from {dicom_dir_name}"
                        )
                    else:
                        error_count += 1
                        self.log_widget.append_log(f"No files were converted from {dicom_dir_name}", "WARNING")
                        
                except Exception as e:
                    error_count += 1
                    self.log_widget.append_log(f"Error converting {dicom_dir_name}: {str(e)}", "ERROR")
            
            # 完成报告
            self.progress_manager.complete_operation(
                f"Completed batch conversion: {success_count} successful, {error_count} failed",
                error_count == 0
            )
            
        except Exception as e:
            self.log_widget.append_log(f"Error during batch conversion: {str(e)}", "ERROR")
            self.progress_bar.setVisible(False)

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