from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QGridLayout, QDoubleSpinBox, QCheckBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QValidator  # Add this import
import math

class CustomDoubleSpinBox(QDoubleSpinBox):
    """支持NaN输入的自定义SpinBox"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._non_nan_enabled = False
        self._default_value = 0
        self.set_nan_enabled(True)  # 默认启用NaN
        
    def set_default_value(self, value):
        """设置默认值，用于切换到非NaN模式时"""
        self._default_value = value
    
    def set_nan_enabled(self, enabled):
        """启用或禁用NaN输入"""
        self._non_nan_enabled = not enabled  # 反转逻辑
        if not self._non_nan_enabled:
            self.lineEdit().setText('NaN')
            self._is_nan = True
        else:
            self.setValue(self._default_value)  # 使用保存的默认值
            self.lineEdit().setReadOnly(False)
            
    def validate(self, text, pos):
        if not self._non_nan_enabled:
            return (QValidator.Acceptable, 'NaN', pos)
        return super().validate(text, pos)
    
    def valueFromText(self, text):
        if not self._non_nan_enabled:
            return float('nan')
        try:
            value = float(text)
            self._default_value = value  # 保存用户输入的值作为新的默认值
            return value
        except ValueError:
            return self._default_value
    
    def textFromValue(self, value):
        if not self._non_nan_enabled or math.isnan(value):
            return 'NaN'
        return super().textFromValue(value)
    
    def value(self):
        if not self._non_nan_enabled:
            return float('nan')
        return super().value()

class BoundingBoxDialog(QDialog):
    """边界框设置对话框"""
    
    def __init__(self, parent=None, current_bb=None):
        super().__init__(parent)
        self.setWindowTitle("Specify Bounding Box")
        self.current_bb = current_bb or [-78, -112, -70, 78, 76, 85]
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 创建网格布局用于SpinBox
        grid = QGridLayout()
        grid.setColumnStretch(1, 1)  # 让值列变宽
        
        # 左侧标签和值
        labels_left = ["Left:", "Posterior:", "Inferior:"]
        labels_right = ["Right:", "Anterior:", "Superior:"]
        
        # 重新排列控件
        self.spins = []
        default_pairs = [
            (-78, 78),   # Left-Right
            (-112, 76),  # Posterior-Anterior
            (-70, 85)    # Inferior-Superior
        ]
        
        for i, (left_label, right_label, (def_left, def_right)) in enumerate(
            zip(labels_left, labels_right, default_pairs)):
            # 左侧标签
            grid.addWidget(QLabel(left_label), i, 0)
            
            # 左侧值
            left_spin = CustomDoubleSpinBox()
            left_spin.setRange(float('-inf'), float('inf'))
            left_spin.set_default_value(def_left)
            left_spin.setValue(self.current_bb[i] if not math.isnan(self.current_bb[i]) else def_left)
            left_spin.setDecimals(1)
            left_spin.setSingleStep(1)
            grid.addWidget(left_spin, i, 1)
            self.spins.append(left_spin)
            
            # 右侧标签
            grid.addWidget(QLabel(right_label), i, 2)
            
            # 右侧值
            right_spin = CustomDoubleSpinBox()
            right_spin.setRange(float('-inf'), float('inf'))
            right_spin.set_default_value(def_right)
            right_spin.setValue(self.current_bb[i+3] if not math.isnan(self.current_bb[i+3]) else def_right)
            right_spin.setDecimals(1)
            right_spin.setSingleStep(1)
            grid.addWidget(right_spin, i, 3)
            self.spins.append(right_spin)
        
        layout.addLayout(grid)
        
        # Enable non-NaN values复选框
        nan_layout = QHBoxLayout()
        self.non_nan_check = QCheckBox("Enable non-NaN values")
        self.non_nan_check.setChecked(False)  # 默认不勾选，即默认使用NaN
        self.non_nan_check.stateChanged.connect(self._toggle_non_nan)
        nan_layout.addWidget(self.non_nan_check)
        layout.addLayout(nan_layout)
        
        # 按钮
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        
        layout.addLayout(btn_layout)
        
        # 初始化所有SpinBox为NaN状态
        self._toggle_non_nan(Qt.Unchecked)
    
    def _toggle_non_nan(self, state):
        """切换非NaN输入功能"""
        is_non_nan = state == Qt.Checked
        for spin in self.spins:
            spin.set_nan_enabled(not is_non_nan)
    
    def get_bounding_box(self):
        """返回边界框值"""
        values = []
        # 按照原始顺序重新排列值：[左,后,下,右,前,上]
        for i in range(0, 6, 2):
            values.append(self.spins[i].value())     # 左/后/下
        for i in range(1, 6, 2):
            values.append(self.spins[i].value())     # 右/前/上
        return values
