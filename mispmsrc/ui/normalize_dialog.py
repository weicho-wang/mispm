import os
import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QGroupBox, QComboBox, QFileDialog, QSpinBox,
    QDoubleSpinBox, QCheckBox, QGridLayout, QMessageBox, QFormLayout
)
from PyQt5.QtCore import Qt, pyqtSignal
from .bounding_box_dialog import BoundingBoxDialog  # 添加到文件顶部的导入部分

class NormalizeDialog(QDialog):
    """标准化操作对话框"""
    
    normalise_started = pyqtSignal(dict)  # 修正拼写，与 main_window.py 保持一致
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)  # Add logger initialization
        self.setWindowTitle("Normalise: Estimate & Write")
        self.setMinimumWidth(700)
        
        # Store parameters
        self.source_image = None
        self.template_path = None
        self.params = {
            'source_smoothing': 8,
            'template_smoothing': 0,
            'nonlinear_cutoff': 25,
            'nonlinear_iterations': 16,
            'nonlinear_reg': 1,
            'preserve': 0,
            'prefix': 'w'
        }
        
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
        self.source_smooth.setValue(self.params['source_smoothing'])
        self.source_smooth.valueChanged.connect(lambda v: self.update_param('source_smoothing', v))
        estimate_layout.addWidget(QLabel("Source Image Smoothing (mm FWHM):"), 2, 0)
        estimate_layout.addWidget(self.source_smooth, 2, 1)
        
        # Template Image Smoothing
        self.template_smooth = QSpinBox()
        self.template_smooth.setRange(0, 32)
        self.template_smooth.setValue(self.params['template_smoothing'])
        self.template_smooth.valueChanged.connect(lambda v: self.update_param('template_smoothing', v))
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
        self.cutoff.setValue(self.params['nonlinear_cutoff'])
        self.cutoff.valueChanged.connect(lambda v: self.update_param('nonlinear_cutoff', v))
        estimate_layout.addWidget(QLabel("Nonlinear Frequency Cutoff:"), 5, 0)
        estimate_layout.addWidget(self.cutoff, 5, 1)
        
        # Nonlinear Iterations
        self.iterations = QSpinBox()
        self.iterations.setRange(0, 32)
        self.iterations.setValue(self.params['nonlinear_iterations'])
        self.iterations.valueChanged.connect(lambda v: self.update_param('nonlinear_iterations', v))
        estimate_layout.addWidget(QLabel("Nonlinear Iterations:"), 6, 0)
        estimate_layout.addWidget(self.iterations, 6, 1)
        
        # Nonlinear Regularization
        self.nonlinear_reg = QDoubleSpinBox()
        self.nonlinear_reg.setRange(0, 10)
        self.nonlinear_reg.setValue(self.params['nonlinear_reg'])
        self.nonlinear_reg.setSingleStep(0.1)
        self.nonlinear_reg.valueChanged.connect(lambda v: self.update_param('nonlinear_reg', v))
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
        self.preserve.setCurrentIndex(self.params['preserve'])
        self.preserve.currentIndexChanged.connect(lambda i: self.update_param('preserve', i))
        write_layout.addWidget(QLabel("Preserve:"), 0, 0)
        write_layout.addWidget(self.preserve, 0, 1)
        
        # Bounding box
        bb_layout = QHBoxLayout()
        self.bb_custom = QCheckBox("Custom Bounding Box")
        self.bb_btn = QPushButton("Edit Box")
        self.bb_btn.setEnabled(False)
        self.bb_btn.clicked.connect(self._edit_bounding_box)
        self.bb_custom.toggled.connect(self.bb_btn.setEnabled)
        bb_layout.addWidget(self.bb_custom)
        bb_layout.addWidget(self.bb_btn)
        bb_layout.addStretch()
        write_layout.addWidget(QLabel("Bounding Box:"), 1, 0)
        write_layout.addLayout(bb_layout, 1, 1)
        
        # 存储当前边界框值
        self.current_bb = [-78, -112, -70, 78, 76, 85]
        
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
        self.prefix_edit = QLineEdit(self.params['prefix'])
        self.prefix_edit.setMaxLength(4)
        self.prefix_edit.textChanged.connect(lambda t: self.update_param('prefix', t))
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
    
    def _edit_bounding_box(self):
        """打开边界框编辑对话框"""
        dialog = BoundingBoxDialog(self, self.current_bb)
        if dialog.exec_():
            self.current_bb = dialog.get_bounding_box()
    
    def _run_normalization(self):
        """Collect and validate parameters"""
        try:
            source_image = self.source_edit.text()
            if not source_image:
                raise ValueError("Source image must be specified")
                
            if not os.path.exists(source_image):
                raise ValueError(f"Source image not found: {source_image}")
                
            template = self.template_edit.text()
            if not template:
                # Try to use default template
                default_templates = [
                    os.path.join('canonical', 'avg152T1.nii'),
                    os.path.join('templates', 'T1.nii')
                ]
                
                for rel_path in default_templates:
                    abs_path = os.path.join(os.path.dirname(source_image), rel_path)
                    if os.path.exists(abs_path):
                        template = abs_path
                        self.logger.info(f"Using default template: {template}")
                        break
                        
                if not template:
                    raise ValueError("Template image must be specified")
                
            if not os.path.exists(template):
                raise ValueError(f"Template image not found: {template}")
                
            params = self.get_parameters()
            
            if self.bb_custom.isChecked():
                params['bounding_box'] = self.current_bb
                
            self.normalise_started.emit(params)
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Parameter Error",
                f"Invalid parameters: {str(e)}\n\nPlease check your inputs."
            )
    
    def update_param(self, param, value):
        """Update a parameter value"""
        self.params[param] = value
    
    def get_parameters(self):
        """Get the normalization parameters selected by the user
        
        Returns:
            dict: Dictionary containing the selected parameters
        """
        params = self.params.copy()
        params['source_image'] = self.source_edit.text()
        params['template_path'] = self.template_edit.text()
        return params
