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
from mispmsrc.ui.progress_manager import ProgressManager
from mispmsrc.ui.coreg_dialog import CoregisterDialog
from mispmsrc.ui.normalize_dialog import NormalizeDialog
from mispmsrc.ui.image_view import ImageView  # Add this import near other imports

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
        self.setMinimumSize(800, 700)  # 减小窗口宽度，因为移除了右侧面板
        
        # Create central widget with vertical layout (改为垂直布局)
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)  # 改为垂直布局
        main_layout.setSpacing(5)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Left panel (删除"left"，因为现在是唯一的面板)
        control_panel = QWidget()
        control_layout = QVBoxLayout(control_panel)
        control_layout.setSpacing(5)
        control_layout.setContentsMargins(2, 2, 2, 2)
        
        # Group box for MATLAB engine
        engine_group = QGroupBox("MATLAB Engine")
        engine_group.setFlat(True)  # 使分组框更扁平
        engine_layout = QVBoxLayout()
        engine_layout.setSpacing(3)  # 减小间距
        engine_layout.setContentsMargins(5, 5, 5, 5)  # 减小边距
        self.start_engine_btn = QPushButton("Start Engine")  # 简化按钮文字
        self.stop_engine_btn = QPushButton("Stop Engine")
        self.engine_status_label = QLabel("Engine: Not running")  # 简化标签文字
        
        # 设置按钮属性
        for btn in [self.start_engine_btn, self.stop_engine_btn]:
            btn.setFixedHeight(25)  # 减小按钮高度
            btn.setFixedWidth(120)  # 限制按钮宽度
        
        engine_layout.addWidget(self.engine_status_label)
        engine_layout.addWidget(self.start_engine_btn, 0, Qt.AlignLeft)  # 左对齐
        engine_layout.addWidget(self.stop_engine_btn, 0, Qt.AlignLeft)
        engine_group.setLayout(engine_layout)
        control_layout.addWidget(engine_group)
        
        # Group box for DICOM conversion
        dicom_group = QGroupBox("DICOM/NIFTI Import")
        dicom_layout = QVBoxLayout()
        self.import_dicom_btn = QPushButton("Import DICOM")
        self.import_dicom_btn.setFixedHeight(32)
        dicom_layout.addWidget(self.import_dicom_btn)
        dicom_group.setLayout(dicom_layout)
        control_layout.addWidget(dicom_group)
        
        # Group box for image manipulation
        self.image_group = QGroupBox("Image Processing")
        image_layout = QVBoxLayout()
        
        # Load NIFTI button
        self.load_nifti_btn = QPushButton("Load NIFTI")
        self.load_nifti_btn.setFixedHeight(32)
        image_layout.addWidget(self.load_nifti_btn)
        
        # Coregistration section - 移除下拉菜单，简化布局
        self.coregister_btn = QPushButton("Coregistration")
        self.coregister_btn.setFixedHeight(25)
        self.coregister_btn.setFixedWidth(120)
        image_layout.addWidget(self.coregister_btn, 0, Qt.AlignLeft)
        
        # Normalisation section - 移除下拉菜单，简化布局
        self.normalise_btn = QPushButton("Normalise")
        self.normalise_btn.setFixedHeight(25)
        self.normalise_btn.setFixedWidth(120)
        image_layout.addWidget(self.normalise_btn, 0, Qt.AlignLeft)
        
        # Other buttons
        self.set_origin_btn = QPushButton("Set Origin")
        self.check_reg_btn = QPushButton("Check Registration")
        self.set_origin_btn.setFixedHeight(32)
        self.check_reg_btn.setFixedHeight(32)
        image_layout.addWidget(self.set_origin_btn)
        image_layout.addWidget(self.check_reg_btn)
        
        self.image_group.setLayout(image_layout)
        control_layout.addWidget(self.image_group)
        
        # Add run script button
        self.run_script_btn = QPushButton("Run MATLAB Script")
        self.run_script_btn.setFixedHeight(32)
        control_layout.addWidget(self.run_script_btn)
        
        # Add log viewer
        log_group = QGroupBox("Log")
        log_layout = QVBoxLayout()
        self.log_widget = LogWidget()
        log_layout.addWidget(self.log_widget)
        log_group.setLayout(log_layout)
        control_layout.addWidget(log_group)
        
        # Add control panel to main layout
        main_layout.addWidget(control_panel)
        
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
            self.run_script_btn
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
        
        # Run MATLAB Script按钮布局修改
        control_layout.addWidget(self.run_script_btn, 0, Qt.AlignLeft)
    
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
        """启动协配对话框"""
        dialog = CoregisterDialog(self)
        dialog.coregister_started.connect(self._execute_coregistration)
        dialog.exec_()
    
    def _execute_coregistration(self, params):
        """Execute coregistration operation"""
        self.progress_manager.start_operation("Coregistration")
        steps = self.progress_manager.get_operation_steps('coregister')
        
        try:
            msg, val = steps['init']
            self.progress_manager.update_progress(msg, val)
            
            # Initialize SPM and clear existing jobs
            self.matlab_engine._engine.eval("spm('defaults','pet');", nargout=0)
            self.matlab_engine._engine.eval("spm_jobman('initcfg');", nargout=0)
            self.matlab_engine._engine.eval("clear matlabbatch;", nargout=0)
            
            # Fix paths for MATLAB
            ref_path = params['ref_image'].replace('\\', '/')
            source_path = params['source_image'].replace('\\', '/')
            
            # Create job structure step by step
            cmd = [
                "matlabbatch{1}.spm.spatial.coreg.estwrite.ref = {'" + ref_path + ",1'};",
                "matlabbatch{1}.spm.spatial.coreg.estwrite.source = {'" + source_path + ",1'};"
            ]
            
            # Handle other images
            if params['other_images'] and params['other_images'][0]:  # Check if list is not empty and first item is not empty
                other_files = ["'" + f.replace('\\', '/') + ",1'" for f in params['other_images']]
                cmd.append("matlabbatch{1}.spm.spatial.coreg.estwrite.other = {" + " ".join(other_files) + "};")
            else:
                cmd.append("matlabbatch{1}.spm.spatial.coreg.estwrite.other = {''};")
            
            # Map cost function
            cost_function_map = {
                'Mutual Information': 'mi',
                'Normalised Mutual Information': 'nmi',
                'Entropy Correlation Coefficient': 'ecc',
                'Normalised Cross Correlation': 'ncc'
            }
            cost_fun = cost_function_map.get(params['cost_function'], 'nmi')
            
            # Add estimation options
            est_cmd = [
                "matlabbatch{1}.spm.spatial.coreg.estwrite.eoptions.cost_fun = '" + cost_fun + "';",
                "matlabbatch{1}.spm.spatial.coreg.estwrite.eoptions.sep = [" + str(params['separation']) + "];",
                "matlabbatch{1}.spm.spatial.coreg.estwrite.eoptions.tol = [0.02 0.02 0.02 0.001 0.001 0.001 0.01 0.01 0.01 0.001 0.001 0.001];",
                "matlabbatch{1}.spm.spatial.coreg.estwrite.eoptions.fwhm = [" + str(params['fwhm']) + " " + str(params['fwhm']) + "];"
            ]
            cmd.extend(est_cmd)
            
            # Add reslice options
            wraps = " ".join(str(int(x)) for x in params['wrap'])
            reslice_cmd = [
                "matlabbatch{1}.spm.spatial.coreg.estwrite.roptions.interp = " + str(params['interpolation']) + ";",
                "matlabbatch{1}.spm.spatial.coreg.estwrite.roptions.wrap = [" + wraps + "];",
                "matlabbatch{1}.spm.spatial.coreg.estwrite.roptions.mask = " + str(int(params['mask'])) + ";",
                "matlabbatch{1}.spm.spatial.coreg.estwrite.roptions.prefix = '" + params['prefix'] + "';"
            ]
            cmd.extend(reslice_cmd)
            
            # Execute all commands
            for c in cmd:
                self.matlab_engine._engine.eval(c, nargout=0)
                
            # Run coregistration
            self.matlab_engine._engine.eval("spm_jobman('run',matlabbatch);", nargout=0)
            
            # Get the output file path
            source_dir = os.path.dirname(params['source_image'])
            source_name = os.path.basename(params['source_image'])
            resliced_file = os.path.join(source_dir, params['prefix'] + source_name)
            
            # Display results
            self.matlab_engine._engine.eval("spm_figure('GetWin','Graphics');", nargout=0)
            self.matlab_engine._engine.eval("spm_figure('Clear','Graphics');", nargout=0)
            display_cmd = "spm_check_registration('" + ref_path + "','" + resliced_file.replace('\\', '/') + "');"
            self.matlab_engine._engine.eval(display_cmd, nargout=0)
            
            msg, val = steps['complete']
            self.progress_manager.update_progress(msg, val)
            self.progress_manager.complete_operation("Coregistration completed successfully", True)
            
        except Exception as e:
            self.progress_manager.complete_operation(f"Coregistration failed: {str(e)}", False)
            self.log_widget.append_log(f"Error during coregistration: {str(e)}", "ERROR")
            QMessageBox.critical(self, "Error", f"Coregistration failed: {str(e)}")

    @pyqtSlot()
    def normalise_image(self):
        """启动标准化对话框"""
        dialog = NormalizeDialog(self)
        dialog.normalize_started.connect(self._execute_normalization)
        dialog.exec_()

    def _execute_normalization(self, params):
        """执行标准化操作"""
        self.progress_manager.start_operation("Normalization")
        steps = self.progress_manager.get_operation_steps('normalize')
        
        try:
            msg, val = steps['init']
            self.progress_manager.update_progress(msg, val)
            
            # Initialize SPM with defaults
            self.matlab_engine._engine.eval("clear matlabbatch;", nargout=0)
            self.matlab_engine._engine.eval("spm('defaults','pet');", nargout=0)
            self.matlab_engine._engine.eval("spm_jobman('initcfg');", nargout=0)
            
            # Fix paths for MATLAB
            source_path = params['source_image'].replace('\\', '/')
            
            # Use default template if none specified
            if not params['template']:
                template_path = os.path.join(
                    self.matlab_engine._spm_path,
                    'toolbox', 'OldNorm', 'T1.nii'
                ).replace('\\', '/')
            else:
                template_path = params['template'].replace('\\', '/')
            
            # Initialize matlabbatch structure
            self.matlab_engine._engine.eval("""
            matlabbatch = {};
            matlabbatch{1}.spm.tools.oldnorm.est = struct;
            matlabbatch{1}.spm.tools.oldnorm.est.subj.source = {''};
            matlabbatch{1}.spm.tools.oldnorm.est.subj.wtsrc = '';
            matlabbatch{1}.spm.tools.oldnorm.est.eoptions = struct('template',{{''}});
            """, nargout=0)
            
            # Set source and template
            self.matlab_engine._engine.eval(f"""
            matlabbatch{{1}}.spm.tools.oldnorm.est.subj.source = {{'{source_path},1'}};
            matlabbatch{{1}}.spm.tools.oldnorm.est.eoptions.template = {{'{template_path},1'}};
            """, nargout=0)
            
            # Set estimation options
            self.matlab_engine._engine.eval(f"""
            matlabbatch{{1}}.spm.tools.oldnorm.est.eoptions.weight = '';
            matlabbatch{{1}}.spm.tools.oldnorm.est.eoptions.smosrc = {params['source_smoothing']};
            matlabbatch{{1}}.spm.tools.oldnorm.est.eoptions.smoref = {params['template_smoothing']};
            matlabbatch{{1}}.spm.tools.oldnorm.est.eoptions.regtype = '{params['affine_regularization']}';
            matlabbatch{{1}}.spm.tools.oldnorm.est.eoptions.cutoff = {params['nonlinear_cutoff']};
            matlabbatch{{1}}.spm.tools.oldnorm.est.eoptions.nits = {params['nonlinear_iterations']};
            matlabbatch{{1}}.spm.tools.oldnorm.est.eoptions.reg = {params['nonlinear_regularization']};
            """, nargout=0)
            
            # Add optional weights if provided
            if params['source_weight']:
                weight_path = params['source_weight'].replace('\\', '/')
                self.matlab_engine._engine.eval(
                    f"matlabbatch{{1}}.spm.tools.oldnorm.est.subj.wtsrc = {{'{weight_path},1'}};"
                )
            
            if params['template_weight']:
                template_weight_path = params['template_weight'].replace('\\', '/')
                self.matlab_engine._engine.eval(
                    f"matlabbatch{{1}}.spm.tools.oldnorm.est.eoptions.weight = {{'{template_weight_path},1'}};"
                )
            
            # Run estimation
            self.matlab_engine._engine.eval("spm_jobman('run', matlabbatch);", nargout=0)
            
            # Clear batch and setup write operation
            self.matlab_engine._engine.eval("""
            clear matlabbatch;
            matlabbatch = {};
            matlabbatch{1}.spm.tools.oldnorm.write = struct;
            """, nargout=0)
            
            # Setup write parameters - handle path conversion first
            images_to_write = [source_path] + (params['other_images'] if params['other_images'] else [])
            fixed_paths = []
            for img in images_to_write:
                if img:  # Skip empty paths
                    img_fixed = img.replace('\\', '/')
                    fixed_paths.append(f"'{img_fixed},1'")
            images_list = ",".join(fixed_paths)
            
            self.matlab_engine._engine.eval(f"""
            matlabbatch{{1}}.spm.tools.oldnorm.write.subj.matname = {{'{source_path}_sn.mat'}};
            matlabbatch{{1}}.spm.tools.oldnorm.write.subj.resample = {{{images_list}}};
            matlabbatch{{1}}.spm.tools.oldnorm.write.roptions.preserve = {params['preserve']};
            matlabbatch{{1}}.spm.tools.oldnorm.write.roptions.bb = [-78 -112 -70; 78 76 85];
            matlabbatch{{1}}.spm.tools.oldnorm.write.roptions.vox = [{params['voxel_size']} {params['voxel_size']} {params['voxel_size']}];
            matlabbatch{{1}}.spm.tools.oldnorm.write.roptions.interp = {params['interpolation']};
            matlabbatch{{1}}.spm.tools.oldnorm.write.roptions.wrap = [{' '.join(str(int(x)) for x in params['wrap'])}];
            matlabbatch{{1}}.spm.tools.oldnorm.write.roptions.prefix = '{params['prefix']}';
            """, nargout=0)
            
            # Run write operation
            self.matlab_engine._engine.eval("spm_jobman('run', matlabbatch);", nargout=0)
            
            msg, val = steps['complete']
            self.progress_manager.update_progress(msg, val)
            self.progress_manager.complete_operation("Normalization completed successfully", True)
            
        except Exception as e:
            self.progress_manager.complete_operation(f"Normalization failed: {str(e)}", False)
            self.log_widget.append_log(f"Error during normalization: {str(e)}", "ERROR")
            QMessageBox.critical(self, "Error", f"Normalization failed: {str(e)}")

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
    import sys
    import signal
    import socket
    import time
    
    def run_app():
        """Run the application with proper initialization"""
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # Set application properties
        app.setOrganizationName("MISPM")
        app.setApplicationName("SPM PyQt Interface")
        
        main_window = MainWindow()
        main_window.show()
        
        return app.exec_()
    
    # Enable Ctrl+C handling
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    try:
        # Small delay to allow debugger to connect
        time.sleep(0.1)
        
        # Try running the app
        exit_code = run_app()
        sys.exit(exit_code)
        
    except socket.error:
        # Socket errors are expected when debugging is not available
        print("Notice: Running without debugger")
        exit_code = run_app()
        sys.exit(exit_code)
        
    except Exception as e:
        print(f"Fatal error during startup: {e}", file=sys.stderr)
        sys.exit(1)