from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QGridLayout, QDoubleSpinBox, QCheckBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QValidator  # Add this import
import math

class CustomDoubleSpinBox(QDoubleSpinBox):
    """selfdefine SpinBox Calss whcih support NaN input"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._non_nan_enabled = False
        self._default_value = 0
        self.set_nan_enabled(True)  # set default to NaN
        
    def set_default_value(self, value):
        """set default value when switching to non-NaN mode"""
        self._default_value = value
    
    def set_nan_enabled(self, enabled):
        """start or stop NaN input"""
        self._non_nan_enabled = not enabled  # inverse logic
        if not self._non_nan_enabled:
            self.lineEdit().setText('NaN')
            self._is_nan = True
        else:
            self.setValue(self._default_value)  # use default value
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
            self._default_value = value  # save user input value as new default
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
    """bounding box dialog"""
    
    def __init__(self, parent=None, current_bb=None):
        super().__init__(parent)
        self.setWindowTitle("Specify Bounding Box")
        self.current_bb = current_bb or [-78, -112, -70, 78, 76, 85]
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # create grid layout for SpinBox
        grid = QGridLayout()
        grid.setColumnStretch(1, 1)  # let value column stretch
        
        # left and right labels
        labels_left = ["Left:", "Posterior:", "Inferior:"]
        labels_right = ["Right:", "Anterior:", "Superior:"]
        
        # rearrange current bounding box values
        self.spins = []
        default_pairs = [
            (-78, 78),   # Left-Right
            (-112, 76),  # Posterior-Anterior
            (-70, 85)    # Inferior-Superior
        ]
        
        for i, (left_label, right_label, (def_left, def_right)) in enumerate(
            zip(labels_left, labels_right, default_pairs)):
            # left side label
            grid.addWidget(QLabel(left_label), i, 0)
            
            # left side value
            left_spin = CustomDoubleSpinBox()
            left_spin.setRange(float('-inf'), float('inf'))
            left_spin.set_default_value(def_left)
            left_spin.setValue(self.current_bb[i] if not math.isnan(self.current_bb[i]) else def_left)
            left_spin.setDecimals(1)
            left_spin.setSingleStep(1)
            grid.addWidget(left_spin, i, 1)
            self.spins.append(left_spin)
            
            # right side label
            grid.addWidget(QLabel(right_label), i, 2)
            
            # right side value
            right_spin = CustomDoubleSpinBox()
            right_spin.setRange(float('-inf'), float('inf'))
            right_spin.set_default_value(def_right)
            right_spin.setValue(self.current_bb[i+3] if not math.isnan(self.current_bb[i+3]) else def_right)
            right_spin.setDecimals(1)
            right_spin.setSingleStep(1)
            grid.addWidget(right_spin, i, 3)
            self.spins.append(right_spin)
        
        layout.addLayout(grid)
        
        # Enable non-NaN values checkbox
        nan_layout = QHBoxLayout()
        self.non_nan_check = QCheckBox("Enable non-NaN values")
        self.non_nan_check.setChecked(False)  # default to unchecked
        self.non_nan_check.stateChanged.connect(self._toggle_non_nan)
        nan_layout.addWidget(self.non_nan_check)
        layout.addLayout(nan_layout)
        
        # OK and Cancel buttons
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        
        layout.addLayout(btn_layout)
        
        # initialize bounding box values to NaN
        self._toggle_non_nan(Qt.Unchecked)
    
    def _toggle_non_nan(self, state):
        """switch non-NaN input feature"""
        is_non_nan = state == Qt.Checked
        for spin in self.spins:
            spin.set_nan_enabled(not is_non_nan)
    
    def get_bounding_box(self):
        """return bounding box values"""
        values = []
        # rearrange to [左,后,下,右,前,上]
        for i in range(0, 6, 2):
            values.append(self.spins[i].value())     # 左/后/下
        for i in range(1, 6, 2):
            values.append(self.spins[i].value())     # 右/前/上
        return values
