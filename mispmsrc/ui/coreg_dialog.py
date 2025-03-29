from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QGroupBox, QComboBox, QFileDialog, QSpinBox,
    QDoubleSpinBox, QCheckBox, QGridLayout
)
from PyQt5.QtCore import Qt, pyqtSignal

class CoregisterDialog(QDialog):
    """协配操作对话框，替代SPM batch editor功能"""
    
    coregister_started = pyqtSignal(dict)  # 发送协配参数的信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Coregistration")
        self.setMinimumWidth(600)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 图像选择组
        image_group = QGroupBox("Image Selection")
        image_layout = QGridLayout()
        
        # 参考图像
        self.ref_edit = QLineEdit()
        self.ref_btn = QPushButton("Browse...")
        self.ref_btn.clicked.connect(lambda: self._browse_image(self.ref_edit, "Reference Image"))
        image_layout.addWidget(QLabel("Reference Image:"), 0, 0)
        image_layout.addWidget(self.ref_edit, 0, 1)
        image_layout.addWidget(self.ref_btn, 0, 2)
        
        # 源图像
        self.source_edit = QLineEdit()
        self.source_btn = QPushButton("Browse...")
        self.source_btn.clicked.connect(lambda: self._browse_image(self.source_edit, "Source Image"))
        image_layout.addWidget(QLabel("Source Image:"), 1, 0)
        image_layout.addWidget(self.source_edit, 1, 1)
        image_layout.addWidget(self.source_btn, 1, 2)
        
        # 其他图像
        self.other_edit = QLineEdit()
        self.other_btn = QPushButton("Browse...")
        self.other_btn.clicked.connect(lambda: self._browse_image(self.other_edit, "Other Images", True))
        image_layout.addWidget(QLabel("Other Images:"), 2, 0)
        image_layout.addWidget(self.other_edit, 2, 1)
        image_layout.addWidget(self.other_btn, 2, 2)
        
        image_group.setLayout(image_layout)
        layout.addWidget(image_group)
        
        # 估计参数组
        estimate_group = QGroupBox("Estimation Options")
        estimate_layout = QGridLayout()
        
        # Cost function
        self.cost_combo = QComboBox()
        self.cost_combo.addItems([
            "Mutual Information",
            "Normalised Mutual Information",
            "Entropy Correlation Coefficient",
            "Normalised Cross Correlation"
        ])
        estimate_layout.addWidget(QLabel("Cost Function:"), 0, 0)
        estimate_layout.addWidget(self.cost_combo, 0, 1)
        
        # Separation
        self.sep_spin = QSpinBox()
        self.sep_spin.setRange(1, 10)
        self.sep_spin.setValue(4)
        estimate_layout.addWidget(QLabel("Separation [mm]:"), 1, 0)
        estimate_layout.addWidget(self.sep_spin, 1, 1)
        
        # Tolerance
        self.tol_spin = QDoubleSpinBox()
        self.tol_spin.setRange(0.001, 0.1)
        self.tol_spin.setSingleStep(0.001)
        self.tol_spin.setValue(0.02)
        estimate_layout.addWidget(QLabel("Tolerance:"), 2, 0)
        estimate_layout.addWidget(self.tol_spin, 2, 1)
        
        # Histogram Smoothing
        self.fwhm_spin = QSpinBox()
        self.fwhm_spin.setRange(0, 20)
        self.fwhm_spin.setValue(7)
        estimate_layout.addWidget(QLabel("Histogram Smoothing:"), 3, 0)
        estimate_layout.addWidget(self.fwhm_spin, 3, 1)
        
        estimate_group.setLayout(estimate_layout)
        layout.addWidget(estimate_group)
        
        # 重采样选项组
        reslice_group = QGroupBox("Reslice Options")
        reslice_layout = QGridLayout()
        
        # 插值方法
        self.interp_combo = QComboBox()
        self.interp_combo.addItems([
            "Nearest Neighbour",
            "Trilinear",
            "2nd Degree B-Spline",
            "3rd Degree B-Spline",
            "4th Degree B-Spline"
        ])
        self.interp_combo.setCurrentIndex(1)
        reslice_layout.addWidget(QLabel("Interpolation:"), 0, 0)
        reslice_layout.addWidget(self.interp_combo, 0, 1)
        
        # Wrapping
        self.wrap_x = QCheckBox("Wrap X")
        self.wrap_y = QCheckBox("Wrap Y")
        self.wrap_z = QCheckBox("Wrap Z")
        wrap_layout = QHBoxLayout()
        wrap_layout.addWidget(self.wrap_x)
        wrap_layout.addWidget(self.wrap_y)
        wrap_layout.addWidget(self.wrap_z)
        reslice_layout.addWidget(QLabel("Wrapping:"), 1, 0)
        reslice_layout.addLayout(wrap_layout, 1, 1)
        
        # Masking
        self.mask_check = QCheckBox("Mask images")
        reslice_layout.addWidget(QLabel("Masking:"), 2, 0)
        reslice_layout.addWidget(self.mask_check, 2, 1)
        
        # Filename Prefix
        self.prefix_edit = QLineEdit("r")
        reslice_layout.addWidget(QLabel("Filename Prefix:"), 3, 0)
        reslice_layout.addWidget(self.prefix_edit, 3, 1)
        
        reslice_group.setLayout(reslice_layout)
        layout.addWidget(reslice_group)
        
        # 按钮组
        button_layout = QHBoxLayout()
        self.run_btn = QPushButton("Run")
        self.run_btn.clicked.connect(self._run_coregistration)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.run_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)
    
    def _browse_image(self, line_edit, title, multiple=False):
        """浏览并选择图像文件"""
        if multiple:
            files, _ = QFileDialog.getOpenFileNames(
                self, f"Select {title}", "",
                "Image files (*.nii *.img);;All files (*.*)"
            )
            if files:
                line_edit.setText(";".join(files))
        else:
            filename, _ = QFileDialog.getOpenFileName(
                self, f"Select {title}", "",
                "Image files (*.nii *.img);;All files (*.*)"
            )
            if filename:
                line_edit.setText(filename)
    
    def _run_coregistration(self):
        """Execute coregistration operation"""
        # Collect all parameters
        params = {
            'ref_image': self.ref_edit.text(),
            'source_image': self.source_edit.text(),
            'other_images': self.other_edit.text().split(';') if self.other_edit.text() else [],
            'cost_function': self._get_valid_cost_function(),
            'separation': self.sep_spin.value(),
            'tolerance': self.tol_spin.value(),
            'fwhm': self.fwhm_spin.value(),
            'interpolation': self.interp_combo.currentIndex(),
            'wrap': [self.wrap_x.isChecked(), self.wrap_y.isChecked(), self.wrap_z.isChecked()],
            'mask': self.mask_check.isChecked(),
            'prefix': self.prefix_edit.text()
        }
        
        # Send signal and close dialog
        self.coregister_started.emit(params)
        self.accept()

    def _get_valid_cost_function(self):
        """Convert UI cost function selection to valid SPM parameter"""
        cost_function_map = {
            "Mutual Information": "mi",
            "Normalised Mutual Information": "nmi",
            "Entropy Correlation Coefficient": "ecc",
            "Normalised Cross Correlation": "ncc"
        }
        
        # Get the selected cost function text
        selected = self.cost_combo.currentText()
        
        # Return the mapped value or default to nmi
        return cost_function_map.get(selected, "nmi")
