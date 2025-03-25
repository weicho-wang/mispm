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

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, "core"))  # Ensure this path is correct

from mispmsrc.core.matlab_engine import MatlabEngine
from mispmsrc.utils.logger import Logger

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
        
        # Set up UI
        self.run_script_btn = QPushButton("Run MATLAB Script")
        self.setup_ui()
        
        # Connect signals
        self.connect_signals()
        
        # Start MATLAB engine
        self.start_matlab_engine()
    
    def setup_ui(self):
        """Set up the UI components"""
        # Set window properties
        self.setWindowTitle("SPM PyQt Interface")
        self.setMinimumSize(800, 800)  # Reduced width since we removed right panel
        
        # Create central widget
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        
        # Left panel - Controls (now main panel)
        main_panel = QWidget()
        layout = QVBoxLayout(main_panel)
        
        # Group box for MATLAB engine
        engine_group = QGroupBox("MATLAB Engine")
        engine_layout = QVBoxLayout()
        self.start_engine_btn = QPushButton("Start MATLAB Engine")
        self.stop_engine_btn = QPushButton("Stop MATLAB Engine")
        self.engine_status_label = QLabel("MATLAB Engine: Not running")
        engine_layout.addWidget(self.engine_status_label)
        engine_layout.addWidget(self.start_engine_btn)
        engine_layout.addWidget(self.stop_engine_btn)
        engine_group.setLayout(engine_layout)
        layout.addWidget(engine_group)
        
        # Group box for DICOM conversion
        dicom_group = QGroupBox("DICOM/NIFTI Import")
        dicom_layout = QVBoxLayout()
        self.import_dicom_btn = QPushButton("Import DICOM")
        self.import_dicom_btn.setFixedHeight(32)
        dicom_layout.addWidget(self.import_dicom_btn)
        dicom_group.setLayout(dicom_layout)
        layout.addWidget(dicom_group)
        
        # Group box for image manipulation
        self.image_group = QGroupBox("Image Processing")
        image_layout = QVBoxLayout()
        
        # Load NIFTI button
        self.load_nifti_btn = QPushButton("Load NIFTI")
        self.load_nifti_btn.setFixedHeight(32)
        image_layout.addWidget(self.load_nifti_btn)
        
        # Coregistration section
        coreg_layout = QVBoxLayout()
        self.coregister_btn = QPushButton("Coregistration")
        self.coregister_btn.setFixedHeight(32)
        self.coreg_method_combo = QComboBox()
        self.coreg_method_combo.addItems([
            "Mutual Information",
            "Normalised Mutual Information",
            "Entropy Correlation Coefficient",
            "Normalised Cross Correlation"
        ])
        self.coreg_method_combo.setFixedHeight(32)
        coreg_layout.addWidget(self.coregister_btn)
        coreg_layout.addWidget(self.coreg_method_combo)
        image_layout.addLayout(coreg_layout)
        
        # Normalisation section
        normalise_layout = QVBoxLayout()
        self.normalise_btn = QPushButton("Normalise")
        self.normalise_btn.setFixedHeight(32)
        self.norm_method_combo = QComboBox()
        self.norm_method_combo.addItems(["Standard", "Template", "Individual"])
        self.norm_method_combo.setFixedHeight(32)
        normalise_layout.addWidget(self.normalise_btn)
        normalise_layout.addWidget(self.norm_method_combo)
        image_layout.addLayout(normalise_layout)
        
        # Other buttons
        self.set_origin_btn = QPushButton("Set Origin")
        self.check_reg_btn = QPushButton("Check Registration")
        self.set_origin_btn.setFixedHeight(32)
        self.check_reg_btn.setFixedHeight(32)
        image_layout.addWidget(self.set_origin_btn)
        image_layout.addWidget(self.check_reg_btn)
        
        self.image_group.setLayout(image_layout)
        layout.addWidget(self.image_group)
        
        # Add run script button
        self.run_script_btn = QPushButton("Run MATLAB Script")
        self.run_script_btn.setFixedHeight(32)
        layout.addWidget(self.run_script_btn)
        
        # Add log viewer
        log_group = QGroupBox("Log")
        log_layout = QVBoxLayout()
        self.log_widget = LogWidget()
        log_layout.addWidget(self.log_widget)
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        # Add main panel to main layout
        main_layout.addWidget(main_panel)
        
        # Set central widget
        self.setCentralWidget(central_widget)
        
        # Create status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        
        # Add progress bar to status bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.statusBar.addPermanentWidget(self.progress_bar)
        
        # Set initial button states
        self.update_button_states(False)
    
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
            self.log_widget.append_log("DICOM import cancelled")
            return
            
        dicom_files = []
        
        if msgBox.clickedButton() == files_btn:  # Individual files
            # Get DICOM files from user
            files, _ = QFileDialog.getOpenFileNames(
                self, "Select DICOM Files", "", "DICOM Files (*.dcm *.ima);;All Files (*)"
            )
            
            if not files:
                self.log_widget.append_log("DICOM import cancelled")
                return
                
            self.log_widget.append_log(f"Selected {len(files)} DICOM files")
            dicom_files = files
            
            # Use the directory of the first file as default dicom_dir
            dicom_dir = os.path.dirname(files[0])
        else:  # Directory
            # Get DICOM directory from user
            dicom_dir = QFileDialog.getExistingDirectory(
                self, "Select DICOM Directory", "", QFileDialog.ShowDirsOnly
            )
            
            if not dicom_dir:
                self.log_widget.append_log("DICOM import cancelled")
                return
                
            self.log_widget.append_log(f"Selected DICOM directory: {dicom_dir}")
            
            # Check if directory contains DICOM files
            try:
                # Use MATLAB to check for DICOM files
                result = self.matlab_engine.call_function("spm_select", 'FPList', dicom_dir, '.*\.dcm$')
                if len(result) == 0:
                    self.log_widget.append_log("No DICOM files found in the selected directory", "ERROR")
                    QMessageBox.critical(self, "Error", "No DICOM files found in the selected directory.")
                    return
                self.log_widget.append_log(f"Found {len(result)} DICOM files in directory")
            except Exception as e:
                self.log_widget.append_log(f"Error checking for DICOM files: {str(e)}", "ERROR")
                QMessageBox.critical(self, "Error", f"Error checking for DICOM files: {str(e)}")
                return
        
        # Get output directory from user
        output_dir = QFileDialog.getExistingDirectory(
            self, "Select Output Directory", dicom_dir, QFileDialog.ShowDirsOnly
        )
        
        if not output_dir:
            # Use DICOM directory if no output directory is selected
            output_dir = dicom_dir
            self.log_widget.append_log(f"Using DICOM directory as output: {output_dir}")
        else:
            self.log_widget.append_log(f"Selected output directory: {output_dir}")
        
        # Convert DICOM to NIFTI
        try:
            if msgBox.clickedButton() == files_btn:  # Individual files
                nii_files = self.matlab_engine.convert_dicom_files_to_nifti(dicom_files, output_dir)
            else:  # Directory
                nii_files = self.matlab_engine.convert_dicom_to_nifti(dicom_dir, output_dir)
            
            if nii_files:
                self.log_widget.append_log(f"Converted {len(nii_files)} DICOM files to NIFTI", "SUCCESS")
                
                # Ask user if they want to load the first NIFTI file
                if QMessageBox.question(
                    self,
                    "Load NIFTI",
                    "Do you want to load the first NIFTI file?",
                    QMessageBox.Yes | QMessageBox.No
                ) == QMessageBox.Yes:
                    self.image_view.display_image(nii_files[0])
            else:
                self.log_widget.append_log("No NIFTI files were created", "WARNING")
                
        except Exception as e:
            self.log_widget.append_log(f"Error converting DICOM to NIFTI: {str(e)}", "ERROR")
            QMessageBox.critical(self, "Error", f"Failed to convert DICOM to NIFTI: {str(e)}")
    
    @pyqtSlot()
    def load_nifti(self):
        """Load or import a NIFTI file"""
        self.log_widget.append_log("NIFTI File Operation...")
        
        # Ask user if they want to select files or a directory
        msgBox = QMessageBox()
        msgBox.setWindowTitle("NIFTI Operation")
        msgBox.setText("Would you like to select individual NIFTI files or a directory?")
        folder_btn = msgBox.addButton("Directory", QMessageBox.ActionRole)
        files_btn = msgBox.addButton("Files", QMessageBox.ActionRole)
        msgBox.addButton(QMessageBox.Cancel)
        msgBox.exec_()
        
        if msgBox.clickedButton() == QMessageBox.Cancel:
            self.log_widget.append_log("NIFTI operation cancelled")
            return
        
        if msgBox.clickedButton() == files_btn:  # Individual files
            # Get NIFTI file from user
            nifti_file, _ = QFileDialog.getOpenFileName(
                self, "Select NIFTI File", "", "NIFTI Files (*.nii *.nii.gz *.img);;All Files (*)"
            )
            
            if not nifti_file:
                self.log_widget.append_log("NIFTI operation cancelled")
                return
                
            self.log_widget.append_log(f"Selected NIFTI file: {nifti_file}")
            
        else:  # Directory
            # Get NIFTI directory from user
            nifti_dir = QFileDialog.getExistingDirectory(
                self, "Select NIFTI Directory", "", QFileDialog.ShowDirsOnly
            )
            
            if not nifti_dir:
                self.log_widget.append_log("NIFTI operation cancelled")
                return
                
            self.log_widget.append_log(f"Selected NIFTI directory: {nifti_dir}")
            
            # Check if directory contains NIFTI files
            try:
                result = self.matlab_engine.call_function("spm_select", 'FPList', nifti_dir, '.*\.nii$')
                if len(result) == 0:
                    self.log_widget.append_log("No NIFTI files found in the selected directory", "ERROR")
                    QMessageBox.critical(self, "Error", "No NIFTI files found in the selected directory.")
                    return
                
                self.log_widget.append_log(f"Found {len(result)} NIFTI files in directory")
                
                # Ask user to select one of the found NIFTI files
                if len(result) > 1:
                    filenames = [os.path.basename(file) for file in result]
                    selected_file, ok = QInputDialog.getItem(
                        self, "Select NIFTI File", 
                        "Multiple NIFTI files found. Please select one:", 
                        filenames, 0, False
                    )
                    
                    if not ok or not selected_file:
                        self.log_widget.append_log("NIFTI file selection cancelled")
                        return
                    
                    # Find the full path of the selected file
                    for file in result:
                        if os.path.basename(file) == selected_file:
                            nifti_file = file
                            break
                else:
                    nifti_file = result[0]
                
                self.log_widget.append_log(f"Selected NIFTI file: {nifti_file}")
                
            except Exception as e:
                self.log_widget.append_log(f"Error checking for NIFTI files: {str(e)}", "ERROR")
                QMessageBox.critical(self, "Error", f"Error checking for NIFTI files: {str(e)}")
                return

        # Load the selected NIFTI file
        try:
            success = self.matlab_engine.display_image(nifti_file)
            if success:
                self.log_widget.append_log("NIFTI file loaded successfully", "SUCCESS")
            else:
                self.log_widget.append_log("Failed to load NIFTI file", "ERROR")
        except Exception as e:
            self.log_widget.append_log(f"Error loading NIFTI file: {str(e)}", "ERROR")
            QMessageBox.critical(self, "Error", f"Failed to load NIFTI file: {str(e)}")
    
    @pyqtSlot()
    def coregister_images(self):
        """Coregister two images"""
        self.log_widget.append_log("Selecting reference image...")
        
        # Get reference image from user
        ref_image, _ = QFileDialog.getOpenFileName(
            self, "Select Reference Image", "", "NIFTI Files (*.nii *.nii.gz *.img);;All Files (*)"
        )
        
        if not ref_image:
            self.log_widget.append_log("Coregistration cancelled")
            return
            
        self.log_widget.append_log(f"Selected reference image: {ref_image}")
        
        # Get source image from user
        source_image, _ = QFileDialog.getOpenFileName(
            self, "Select Source Image to Coregister", "", "NIFTI Files (*.nii *.nii.gz *.img);;All Files (*)"
        )
        
        if not source_image:
            self.log_widget.append_log("Coregistration cancelled")
            return
            
        self.log_widget.append_log(f"Selected source image: {source_image}")
        
        # Get selected cost function
        cost_function_idx = self.coreg_method_combo.currentIndex()
        cost_functions = ["mi", "nmi", "ecc", "ncc"]
        cost_function = cost_functions[cost_function_idx]
        
        self.log_widget.append_log(f"Using cost function: {self.coreg_method_combo.currentText()} ({cost_function})")
        
        # Coregister images
        try:
            success = self.matlab_engine.coregister_images(ref_image, source_image, cost_function)
            
            if success:
                self.log_widget.append_log("Coregistration completed successfully", "SUCCESS")
                
                # Get the path to the coregistered image
                source_dir = os.path.dirname(source_image)
                source_name = os.path.basename(source_image)
                coregistered_image = os.path.join(source_dir, f"r{source_name}")
                
                # Ask user if they want to load the coregistered image
                if QMessageBox.question(
                    self,
                    "Load Coregistered Image",
                    "Do you want to load the coregistered image?",
                    QMessageBox.Yes | QMessageBox.No
                ) == QMessageBox.Yes:
                    self.image_view.display_image(coregistered_image)
            else:
                self.log_widget.append_log("Coregistration failed", "ERROR")
                
        except Exception as e:
            self.log_widget.append_log(f"Error during coregistration: {str(e)}", "ERROR")
            QMessageBox.critical(self, "Error", f"Failed to coregister images: {str(e)}")
    
    @pyqtSlot()
    def normalise_image(self):
        """Normalise an image to a template"""
        self.log_widget.append_log("Selecting image to normalise...")
        
        # Get source image from user
        source_image, _ = QFileDialog.getOpenFileName(
            self, "Select Image to Normalise", "", "NIFTI Files (*.nii *.nii.gz *.img);;All Files (*)"
        )
        
        if not source_image:
            self.log_widget.append_log("Normalisation cancelled")
            return
            
        self.log_widget.append_log(f"Selected image to normalise: {source_image}")
        
        # Get normalization method
        norm_method_idx = self.norm_method_combo.currentIndex()
        norm_methods = ["standard", "template", "individual"]
        norm_method = norm_methods[norm_method_idx]
        
        self.log_widget.append_log(f"Using normalization method: {self.norm_method_combo.currentText()} ({norm_method})")
        
        template_image = None
        
        if norm_method == "template":
            # Ask user to select a template
            template_image, _ = QFileDialog.getOpenFileName(
                self, "Select Template Image", "", "NIFTI Files (*.nii *.nii.gz *.img);;All Files (*)"
            )
            
            if not template_image:
                self.log_widget.append_log("Using default SPM template")
            else:
                self.log_widget.append_log(f"Selected template image: {template_image}")
        elif norm_method == "individual":
            # For individual method, we need both a source and a reference image
            ref_image, _ = QFileDialog.getOpenFileName(
                self, "Select Reference Image for Normalization", "", "NIFTI Files (*.nii *.nii.gz *.img);;All Files (*)"
            )
            
            if not ref_image:
                self.log_widget.append_log("Normalization cancelled - reference image required for individual method")
                return
                
            self.log_widget.append_log(f"Selected reference image: {ref_image}")
            template_image = ref_image
        else:
            self.log_widget.append_log("Using default SPM template")
        
        # Normalise image
        try:
            success = self.matlab_engine.normalize_image(source_image, template_image, norm_method)
            
            if success:
                self.log_widget.append_log("Normalisation completed successfully", "SUCCESS")
                
                # Get the path to the normalised image
                source_dir = os.path.dirname(source_image)
                source_name = os.path.basename(source_image)
                normalised_image = os.path.join(source_dir, f"w{source_name}")
                
                # Ask user if they want to load the normalised image
                if QMessageBox.question(
                    self,
                    "Load Normalised Image",
                    "Do you want to load the normalised image?",
                    QMessageBox.Yes | QMessageBox.No
                ) == QMessageBox.Yes:
                    self.image_view.display_image(normalised_image)
            else:
                self.log_widget.append_log("Normalisation failed", "ERROR")
                
        except Exception as e:
            self.log_widget.append_log(f"Error during normalisation: {str(e)}", "ERROR")
            QMessageBox.critical(self, "Error", f"Failed to normalise image: {str(e)}")
    
    @pyqtSlot()
    def set_origin(self):
        """Set the origin of an image"""
        # Check if an image is already loaded
        if self.image_view.current_image:
            image_file = self.image_view.current_image
            self.log_widget.append_log(f"Using currently loaded image: {image_file}")
        else:
            self.log_widget.append_log("Selecting image to set origin...")
            
            # Get image from user
            image_file, _ = QFileDialog.getOpenFileName(
                self, "Select Image to Set Origin", "", "NIFTI Files (*.nii *.nii.gz *.img);;All Files (*)"
            )
            
            if not image_file:
                self.log_widget.append_log("Set origin cancelled")
                return
                
            self.log_widget.append_log(f"Selected image: {image_file}")
        
        # Ask for coordinates or use default
        use_custom_coords = QMessageBox.question(
            self,
            "Origin Coordinates",
            "Do you want to specify custom coordinates?\nClick 'No' to use [0, 0, 0].",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes
        
        coordinates = None
        
        if use_custom_coords:
            # TODO: Implement a dialog to get coordinates
            # For now, just use [0, 0, 0]
            self.log_widget.append_log("Custom coordinates not implemented yet, using [0, 0, 0]")
        else:
            self.log_widget.append_log("Using default coordinates [0, 0, 0]")
        
        # Set origin
        try:
            success = self.matlab_engine.set_origin(image_file, coordinates)
            
            if success:
                self.log_widget.append_log("Origin set successfully", "SUCCESS")
                
                # Reload the image
                self.image_view.display_image(image_file)
            else:
                self.log_widget.append_log("Failed to set origin", "ERROR")
                
        except Exception as e:
            self.log_widget.append_log(f"Error setting origin: {str(e)}", "ERROR")
            QMessageBox.critical(self, "Error", f"Failed to set origin: {str(e)}")
    
    @pyqtSlot()
    def check_registration(self):
        """Check registration of multiple images"""
        self.log_widget.append_log("Selecting images for registration check...")
        
        # Get images from user
        image_files, _ = QFileDialog.getOpenFileNames(
            self, "Select Images to Check Registration", "", "NIFTI Files (*.nii *.nii.gz *.img);;All Files (*)"
        )
        
        if not image_files:
            self.log_widget.append_log("Registration check cancelled")
            return
            
        self.log_widget.append_log(f"Selected {len(image_files)} images")
        
        # Check registration
        try:
            success = self.matlab_engine.check_registration(image_files)
            
            if success:
                self.log_widget.append_log("Registration check completed successfully", "SUCCESS")
            else:
                self.log_widget.append_log("Registration check failed", "ERROR")
                
        except Exception as e:
            self.log_widget.append_log(f"Error checking registration: {str(e)}", "ERROR")
            QMessageBox.critical(self, "Error", f"Failed to check registration: {str(e)}")
    
    @pyqtSlot()
    def run_matlab_script(self):
        """Run a MATLAB script"""
        self.log_widget.append_log("Selecting MATLAB script...")
        
        # Get MATLAB script file from user
        script_file, _ = QFileDialog.getOpenFileName(
            self, "Select MATLAB Script", "", "MATLAB Files (*.m);;All Files (*)"
        )
        
        if not script_file:
            self.log_widget.append_log("MATLAB script selection cancelled")
            return
            
        self.log_widget.append_log(f"Selected MATLAB script: {script_file}")
        
        # Run the MATLAB script
        try:
            success = self.matlab_engine.run_script(script_file)
            
            if success:
                self.log_widget.append_log("MATLAB script ran successfully", "SUCCESS")
            else:
                self.log_widget.append_log("Failed to run MATLAB script", "ERROR")
                
        except Exception as e:
            self.log_widget.append_log(f"Error running MATLAB script: {str(e)}", "ERROR")
            QMessageBox.critical(self, "Error", f"Failed to run MATLAB script: {str(e)}")
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Stop MATLAB engine if it's running
        if self.matlab_engine.is_running():
            self.log_widget.append_log("Stopping MATLAB engine before closing...")
            self.matlab_engine.stop_engine()
            
        event.accept()

    def show_window(self):
        """Show the main window"""
        self.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())