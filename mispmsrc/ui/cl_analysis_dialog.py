from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QLineEdit, QFileDialog, QGroupBox, QGridLayout
)
from PyQt5.QtCore import Qt, pyqtSignal
import os
import glob
import logging

class CLAnalysisDialog(QDialog):
    """CL Analysis Parameters Selection Dialog"""
    
    analysis_started = pyqtSignal(dict)  # send signal of analysis parameters
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # Initialize logger
        self.logger = logging.getLogger(__name__)
        self.setWindowTitle("CL Analysis Parameters")
        self.setMinimumWidth(600)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # file selection group
        files_group = QGroupBox("File Selection")
        files_layout = QVBoxLayout()
        
        # REF_PATH selection
        ref_layout = QHBoxLayout()
        self.ref_edit = QLineEdit()
        self.ref_btn = QPushButton("Browse...")
        self.ref_btn.clicked.connect(lambda: self._browse_file(self.ref_edit, "Select Reference Mask"))
        ref_layout.addWidget(QLabel("Reference Mask:"))
        ref_layout.addWidget(self.ref_edit)
        ref_layout.addWidget(self.ref_btn)
        files_layout.addLayout(ref_layout)
        
        # ROI_PATH selection
        roi_layout = QHBoxLayout()
        self.roi_edit = QLineEdit()
        self.roi_btn = QPushButton("Browse...")
        self.roi_btn.clicked.connect(lambda: self._browse_file(self.roi_edit, "Select ROI Mask"))
        roi_layout.addWidget(QLabel("ROI Mask:"))
        roi_layout.addWidget(self.roi_edit)
        roi_layout.addWidget(self.roi_btn)
        files_layout.addLayout(roi_layout)
        
        # AD_DIR selection
        ad_layout = QHBoxLayout()
        self.ad_edit = QLineEdit()
        self.ad_btn = QPushButton("Browse...")
        self.ad_btn.clicked.connect(lambda: self._browse_dir(self.ad_edit, "Select AD Directory"))
        ad_layout.addWidget(QLabel("AD Directory:"))
        ad_layout.addWidget(self.ad_edit)
        ad_layout.addWidget(self.ad_btn)
        files_layout.addLayout(ad_layout)
        
        # YC_DIR selection
        yc_layout = QHBoxLayout()
        self.yc_edit = QLineEdit()
        self.yc_btn = QPushButton("Browse...")
        self.yc_btn.clicked.connect(lambda: self._browse_dir(self.yc_edit, "Select YC Directory"))
        yc_layout.addWidget(QLabel("YC Directory:"))
        yc_layout.addWidget(self.yc_edit)
        yc_layout.addWidget(self.yc_btn)
        files_layout.addLayout(yc_layout)
        
        # Standard data selection
        std_layout = QHBoxLayout()
        self.std_edit = QLineEdit()
        self.std_btn = QPushButton("Browse...")
        self.std_btn.clicked.connect(lambda: self._browse_file(
            self.std_edit, "Select Standard Data", "Excel files (*.xlsx);;All files (*.*)"))
        std_layout.addWidget(QLabel("Standard Data:"))
        std_layout.addWidget(self.std_edit)
        std_layout.addWidget(self.std_btn)
        files_layout.addLayout(std_layout)
        
        files_group.setLayout(files_layout)
        layout.addWidget(files_group)
        
        # Add patient information group
        patient_group = QGroupBox("Patient Information")
        patient_layout = QGridLayout()
        
        # Name field
        self.name_edit = QLineEdit()
        patient_layout.addWidget(QLabel("姓名:"), 0, 0)
        patient_layout.addWidget(self.name_edit, 0, 1)
        
        # Gender field
        self.gender_edit = QLineEdit()
        patient_layout.addWidget(QLabel("性别:"), 0, 2)
        patient_layout.addWidget(self.gender_edit, 0, 3)
        
        # PET ID field
        self.pet_id_edit = QLineEdit()
        patient_layout.addWidget(QLabel("PET检查号:"), 0, 4)
        patient_layout.addWidget(self.pet_id_edit, 0, 5)
        
        patient_group.setLayout(patient_layout)
        layout.addWidget(patient_group)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.run_btn = QPushButton("Run Analysis")
        self.run_btn.clicked.connect(self._run_analysis)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.run_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)
    
    def _browse_file(self, line_edit, title, filter="NIFTI files (*.nii);;All files (*.*)"):
        """view and select a file"""
        filename, _ = QFileDialog.getOpenFileName(self, title, "", filter)
        if filename:
            line_edit.setText(filename)
    
    def _browse_dir(self, line_edit, title):
        """ view and select a directory, and verify if it contains files with 'w' prefix"""
        dirname = QFileDialog.getExistingDirectory(self, title)
        if dirname:
            # check whether contain normalized files with 'w' prefix
            has_norm_files = False
            norm_file_count = 0
            for pattern in ['w*.nii', 'w*.nii.gz', 'wr*.nii', 'wr*.nii.gz']:
                norm_files = glob.glob(os.path.join(dirname, pattern))
                norm_file_count += len(norm_files)
                if norm_files:
                    has_norm_files = True
                    
            if has_norm_files:
                self.logger.info(f"Found {norm_file_count} normalized files in {dirname}")
            else:
                from PyQt5.QtWidgets import QMessageBox
                result = QMessageBox.warning(
                    self, 
                    "No Normalized Files", 
                    "No normalized files (with 'w' or 'wr' prefix) found in the selected directory.\n"
                    "CL Analysis requires normalized files.\n\n"
                    "Would you like to select a different directory?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                
                if result == QMessageBox.Yes:
                    # Try again with a different directory
                    return self._browse_dir(line_edit, title)
            
            line_edit.setText(dirname)
            
            # Also check if the directory contains required subject patterns
            basename = os.path.basename(dirname).upper()
            if 'AD' in basename:
                self.logger.info(f"Selected directory appears to be for AD group: {dirname}")
            elif 'YC' in basename or 'CONTROL' in basename:
                self.logger.info(f"Selected directory appears to be for YC group: {dirname}")
            else:
                self.logger.warning(f"Directory name does not contain expected group indicators (AD/YC): {dirname}")

    def _run_analysis(self):
        """collect parameters and start analysis"""
        params = {
            'ref_path': self.ref_edit.text(),
            'roi_path': self.roi_edit.text(),
            'ad_dir': self.ad_edit.text(),
            'yc_dir': self.yc_edit.text(),
            'standard_data': self.std_edit.text(),
            # Add patient information
            'patient_info': {
                'name': self.name_edit.text(),
                'gender': self.gender_edit.text(),
                'pet_id': self.pet_id_edit.text()
            }
        }
        
        # 检查必要的参数是否都已提供
        missing_params = []
        for param_name, param_value in params.items():
            if param_name != 'patient_info' and not param_value:
                missing_params.append(param_name)
        
        if missing_params:
            from PyQt5.QtWidgets import QMessageBox
            missing_str = ", ".join([p.replace('_', ' ').title() for p in missing_params])
            QMessageBox.warning(
                self, 
                "Missing Parameters", 
                f"Please provide all required parameters. Missing: {missing_str}"
            )
            return
        
        # Verify all paths exist
        invalid_paths = []
        for param_name, param_value in params.items():
            if param_name != 'patient_info' and not os.path.exists(param_value):
                invalid_paths.append(f"{param_name.replace('_', ' ').title()}: {param_value}")
        
        if invalid_paths:
            from PyQt5.QtWidgets import QMessageBox
            invalid_str = "\n".join(invalid_paths)
            QMessageBox.warning(
                self, 
                "Invalid Paths", 
                f"The following paths do not exist:\n\n{invalid_str}"
            )
            return
        
        # For AD and YC directories, verify they contain normalized files
        for dir_param, dir_name in [('ad_dir', 'AD Directory'), ('yc_dir', 'YC Directory')]:
            dir_path = params[dir_param]
            
            # Check for normalized files
            has_norm_files = False
            for pattern in ['w*.nii', 'w*.nii.gz', 'wr*.nii', 'wr*.nii.gz']:
                if glob.glob(os.path.join(dir_path, pattern)):
                    has_norm_files = True
                    break
            
            if not has_norm_files:
                from PyQt5.QtWidgets import QMessageBox
                result = QMessageBox.warning(
                    self, 
                    f"No Normalized Files in {dir_name}", 
                    f"No normalized files (with 'w' or 'wr' prefix) found in {dir_name}:\n{dir_path}\n\n"
                    f"CL Analysis requires normalized files.\n\n"
                    f"Do you want to proceed anyway?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if result == QMessageBox.No:
                    return
        
        # All validation passed, emit signal and close dialog
        self.analysis_started.emit(params)
        self.accept()
