from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QLineEdit, QFileDialog, QGroupBox
)
from PyQt5.QtCore import Qt, pyqtSignal

class CLAnalysisDialog(QDialog):
    """CL分析参数选择对话框"""
    
    analysis_started = pyqtSignal(dict)  # 发送分析参数的信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("CL Analysis Parameters")
        self.setMinimumWidth(600)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 文件选择组
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
        """浏览并选择文件"""
        filename, _ = QFileDialog.getOpenFileName(self, title, "", filter)
        if filename:
            line_edit.setText(filename)
    
    def _browse_dir(self, line_edit, title):
        """浏览并选择目录"""
        dirname = QFileDialog.getExistingDirectory(self, title)
        if dirname:
            line_edit.setText(dirname)
    
    def _run_analysis(self):
        """收集参数并启动分析"""
        params = {
            'ref_path': self.ref_edit.text(),
            'roi_path': self.roi_edit.text(),
            'ad_dir': self.ad_edit.text(),
            'yc_dir': self.yc_edit.text(),
            'standard_data': self.std_edit.text()
        }
        
        # 检查必要的参数是否都已提供
        if all(params.values()):
            self.analysis_started.emit(params)
            self.accept()
        else:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Missing Parameters", 
                              "Please provide all required parameters.")
