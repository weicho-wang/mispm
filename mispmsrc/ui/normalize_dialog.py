from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QGroupBox, QComboBox, QFileDialog, QSpinBox,
    QDoubleSpinBox, QCheckBox, QGridLayout, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal

class NormalizeDialog(QDialog):
    """标准化操作对话框，替代SPM batch editor功能"""
    
    normalize_started = pyqtSignal(dict)  # 发送标准化参数的信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Normalise: Estimate & Write")
        self.setMinimumWidth(700)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 图像选择组
        image_group = QGroupBox("Image Selection")
        image_layout = QGridLayout()
        
        # 源图像
        self.source_edit = QLineEdit()
        self.source_btn = QPushButton("Browse...")
        self.source_btn.clicked.connect(lambda: self._browse_image(self.source_edit, "Source Image"))
        image_layout.addWidget(QLabel("Source Image:"), 0, 0)
        image_layout.addWidget(self.source_edit, 0, 1)
        image_layout.addWidget(self.source_btn, 0, 2)
        
        # 源图像权重（可选）
        self.weight_edit = QLineEdit()
        self.weight_btn = QPushButton("Browse...")
        self.weight_btn.clicked.connect(lambda: self._browse_image(self.weight_edit, "Source Weighting Image"))
        image_layout.addWidget(QLabel("Source Weighting Image (optional):"), 1, 0)
        image_layout.addWidget(self.weight_edit, 1, 1)
        image_layout.addWidget(self.weight_btn, 1, 2)
        
        # 需要标准化的图像
        self.images_edit = QLineEdit()
        self.images_btn = QPushButton("Browse...")
        self.images_btn.clicked.connect(lambda: self._browse_image(self.images_edit, "Images to Write", True))
        image_layout.addWidget(QLabel("Images to Write:"), 2, 0)
        image_layout.addWidget(self.images_edit, 2, 1)
        image_layout.addWidget(self.images_btn, 2, 2)
        
        image_group.setLayout(image_layout)
        layout.addWidget(image_group)
        
        # 估计参数组
        estimate_group = QGroupBox("Estimation Options")
        estimate_layout = QGridLayout()
        
        # Template
        self.template_edit = QLineEdit()
        self.template_btn = QPushButton("Browse...")
        self.template_btn.clicked.connect(lambda: self._browse_image(self.template_edit, "Template Image"))
        estimate_layout.addWidget(QLabel("Template Image:"), 0, 0)
        estimate_layout.addWidget(self.template_edit, 0, 1)
        estimate_layout.addWidget(self.template_btn, 0, 2)
        
        # Template weighting
        self.template_weight_edit = QLineEdit()
        self.template_weight_btn = QPushButton("Browse...")
        self.template_weight_btn.clicked.connect(
            lambda: self._browse_image(self.template_weight_edit, "Template Weighting Image"))
        estimate_layout.addWidget(QLabel("Template Weighting Image (optional):"), 1, 0)
        estimate_layout.addWidget(self.template_weight_edit, 1, 1)
        estimate_layout.addWidget(self.template_weight_btn, 1, 2)
        
        # Source Image Smoothing
        self.source_smooth = QSpinBox()
        self.source_smooth.setRange(0, 32)
        self.source_smooth.setValue(8)
        estimate_layout.addWidget(QLabel("Source Image Smoothing (mm FWHM):"), 2, 0)
        estimate_layout.addWidget(self.source_smooth, 2, 1)
        
        # Template Image Smoothing
        self.template_smooth = QSpinBox()
        self.template_smooth.setRange(0, 32)
        self.template_smooth.setValue(0)
        estimate_layout.addWidget(QLabel("Template Image Smoothing (mm FWHM):"), 3, 0)
        estimate_layout.addWidget(self.template_smooth, 3, 1)
        
        # Affine Regularization
        self.affine_reg = QComboBox()
        self.affine_reg.addItems(['ICBM space template', 'Average sized template', 'No regularization'])
        estimate_layout.addWidget(QLabel("Affine Regularization:"), 4, 0)
        estimate_layout.addWidget(self.affine_reg, 4, 1)
        
        # Nonlinear Frequency Cutoff
        self.cutoff = QSpinBox()
        self.cutoff.setRange(0, 50)
        self.cutoff.setValue(25)
        estimate_layout.addWidget(QLabel("Nonlinear Frequency Cutoff:"), 5, 0)
        estimate_layout.addWidget(self.cutoff, 5, 1)
        
        # Nonlinear Iterations
        self.iterations = QSpinBox()
        self.iterations.setRange(0, 32)
        self.iterations.setValue(16)
        estimate_layout.addWidget(QLabel("Nonlinear Iterations:"), 6, 0)
        estimate_layout.addWidget(self.iterations, 6, 1)
        
        # Nonlinear Regularization
        self.nonlinear_reg = QDoubleSpinBox()
        self.nonlinear_reg.setRange(0, 10)
        self.nonlinear_reg.setValue(1)
        self.nonlinear_reg.setSingleStep(0.1)
        estimate_layout.addWidget(QLabel("Nonlinear Regularization:"), 7, 0)
        estimate_layout.addWidget(self.nonlinear_reg, 7, 1)
        
        estimate_group.setLayout(estimate_layout)
        layout.addWidget(estimate_group)
        
        # 写入选项组
        write_group = QGroupBox("Writing Options")
        write_layout = QGridLayout()
        
        # Preserve
        self.preserve = QComboBox()
        self.preserve.addItems(['Preserve Concentrations', 'Preserve Amount'])
        write_layout.addWidget(QLabel("Preserve:"), 0, 0)
        write_layout.addWidget(self.preserve, 0, 1)
        
        # Bounding box
        self.bb_custom = QCheckBox("Custom Bounding Box")
        write_layout.addWidget(QLabel("Bounding Box:"), 1, 0)
        write_layout.addWidget(self.bb_custom, 1, 1)
        
        # Voxel sizes
        self.voxel_size = QDoubleSpinBox()
        self.voxel_size.setRange(0.1, 10)
        self.voxel_size.setValue(2)
        self.voxel_size.setSingleStep(0.1)
        write_layout.addWidget(QLabel("Voxel Sizes (mm):"), 2, 0)
        write_layout.addWidget(self.voxel_size, 2, 1)
        
        # Interpolation
        self.interpolation = QComboBox()
        self.interpolation.addItems([
            'Nearest Neighbour',
            'Trilinear',
            '2nd Degree B-Spline',
            '3rd Degree B-Spline',
            '4th Degree B-Spline',
            '5th Degree B-Spline',
            '6th Degree B-Spline',
            '7th Degree B-Spline'
        ])
        self.interpolation.setCurrentIndex(1)
        write_layout.addWidget(QLabel("Interpolation:"), 3, 0)
        write_layout.addWidget(self.interpolation, 3, 1)
        
        # Wrapping
        self.wrap_x = QCheckBox("Wrap X")
        self.wrap_y = QCheckBox("Wrap Y")
        self.wrap_z = QCheckBox("Wrap Z")
        wrap_layout = QHBoxLayout()
        wrap_layout.addWidget(self.wrap_x)
        wrap_layout.addWidget(self.wrap_y)
        wrap_layout.addWidget(self.wrap_z)
        write_layout.addWidget(QLabel("Wrapping:"), 4, 0)
        write_layout.addLayout(wrap_layout, 4, 1)
        
        # Filename Prefix
        self.prefix_edit = QLineEdit("w")
        write_layout.addWidget(QLabel("Filename Prefix:"), 5, 0)
        write_layout.addWidget(self.prefix_edit, 5, 1)
        
        write_group.setLayout(write_layout)
        layout.addWidget(write_group)
        
        # 按钮组
        button_layout = QHBoxLayout()
        self.run_btn = QPushButton("Run")
        self.run_btn.clicked.connect(self._run_normalization)
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
    
    def _run_normalization(self):
        """Execute normalization with parameter validation"""
        source_image = self.source_edit.text()
        if not source_image:
            QMessageBox.critical(self, "Error", "Source image must be specified")
            return
            
        # Collect parameters with validation
        params = {
            'source_image': source_image,
            'template': self.template_edit.text() or None,
            'source_weight': self.weight_edit.text() or None,
            'other_images': [img.strip() for img in self.images_edit.text().split(';') if img.strip()],
            'template_weight': self.template_weight_edit.text() or None,
            'source_smoothing': max(0, self.source_smooth.value()),
            'template_smoothing': max(0, self.template_smooth.value()),
            'affine_regularization': self.affine_reg.currentText().lower().replace(' ', '_'),
            'nonlinear_cutoff': max(0, self.cutoff.value()),
            'nonlinear_iterations': max(1, self.iterations.value()),
            'nonlinear_regularization': max(0, self.nonlinear_reg.value()),
            'preserve': self.preserve.currentIndex(),
            'voxel_size': max(0.1, self.voxel_size.value()),
            'interpolation': self.interpolation.currentIndex(),
            'wrap': [self.wrap_x.isChecked(), self.wrap_y.isChecked(), self.wrap_z.isChecked()],
            'prefix': self.prefix_edit.text() or 'w'
        }
        
        # Emit signal and close dialog
        self.normalize_started.emit(params)
        self.accept()
