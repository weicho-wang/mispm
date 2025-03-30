#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import numpy as np
import nibabel as nib
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFileDialog, QMessageBox, QSlider, QSpinBox, QDoubleSpinBox,
    QGroupBox, QDialog, QGridLayout, QSplitter
)
from PyQt5.QtCore import Qt, pyqtSlot, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen, QColor

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class SliceCanvas(FigureCanvas):
    """Canvas for displaying a single NIFTI slice view (axial, coronal, or sagittal)"""
    
    # Signal emitted when canvas is clicked
    slice_clicked = pyqtSignal(str, int, int)  # view_type, x, y
    
    def __init__(self, parent=None, width=5, height=5, dpi=100, view_type='axial'):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        super(SliceCanvas, self).__init__(self.fig)
        
        self.view_type = view_type  # 'axial', 'coronal', or 'sagittal'
        self.nifti_data = None
        self.affine = None
        self.current_slice = 0
        self.crosshair_pos = [0, 0, 0]  # x, y, z in voxel coordinates
        self.setParent(parent)
        
        # Set up the figure
        self.axes.set_axis_off()
        self.fig.tight_layout()
        self.fig.subplots_adjust(left=0, right=1, top=1, bottom=0, wspace=0, hspace=0)
        
        # Connect mouse events
        self.mpl_connect('button_press_event', self.on_click)
        
        # Set title based on view type
        title_map = {'axial': 'Axial View', 'coronal': 'Coronal View', 'sagittal': 'Sagittal View'}
        self.fig.suptitle(title_map.get(view_type, view_type.capitalize()), fontsize=10)
    
    def on_click(self, event):
        """Handle mouse click event"""
        if event.inaxes != self.axes or self.nifti_data is None:
            return
            
        x, y = int(event.xdata), int(event.ydata)
        self.slice_clicked.emit(self.view_type, x, y)
    
    def update_slice(self, nifti_data, affine, crosshair_pos, current_slice=None):
        """Update the slice display with new data or position"""
        self.nifti_data = nifti_data
        self.affine = affine
        self.crosshair_pos = crosshair_pos
        
        if current_slice is not None:
            self.current_slice = current_slice
            
        self.update_display()
    
    def update_display(self):
        """Update the display with the current slice and crosshair"""
        if self.nifti_data is None:
            return
            
        try:
            self.axes.clear()
            
            # Get the slice data and crosshair position based on view type
            slice_data, crosshair_x, crosshair_y = self._get_slice_data()
            
            # Replace invalid values
            if np.isnan(slice_data).any() or np.isinf(slice_data).any():
                slice_data = np.nan_to_num(slice_data)
            
            # Calculate data range for better display
            try:
                valid_data = slice_data[~np.isnan(slice_data) & ~np.isinf(slice_data)]
                if len(valid_data) > 0:
                    vmin, vmax = np.percentile(valid_data, (1, 99))
                else:
                    vmin, vmax = 0, 1
            except Exception:
                vmin, vmax = np.nanmin(slice_data), np.nanmax(slice_data)
                if np.isinf(vmin) or np.isinf(vmax):
                    vmin, vmax = 0, 1
            
            # Display the slice
            self.axes.imshow(slice_data, cmap='gray', aspect='equal', vmin=vmin, vmax=vmax)
            
            # Draw crosshair
            self.axes.axhline(y=crosshair_y, color='r', linestyle='-', alpha=0.5)
            self.axes.axvline(x=crosshair_x, color='r', linestyle='-', alpha=0.5)
            
            # Add slice number as text
            self.axes.text(0.02, 0.98, f"Slice: {self.current_slice}", 
                          transform=self.axes.transAxes, 
                          color='white', fontsize=8,
                          verticalalignment='top',
                          bbox=dict(boxstyle='round', facecolor='black', alpha=0.5))
            
            self.axes.set_axis_off()
            self.draw()
            
        except Exception as e:
            import traceback
            print(f"Error updating display for {self.view_type} view: {str(e)}")
            print(traceback.format_exc())
    
    def _get_slice_data(self):
        """Get the slice data and crosshair position based on view type"""
        # Default values
        slice_data = None
        crosshair_x, crosshair_y = 0, 0
        
        # Get appropriate slice based on view type
        if self.view_type == 'axial':
            # Make sure current slice is within bounds
            if self.current_slice >= self.nifti_data.shape[2]:
                self.current_slice = self.nifti_data.shape[2] - 1
                
            # Get axial slice (showing X-Y plane at Z position)
            slice_data = self.nifti_data[:, :, self.current_slice]
            slice_data = np.rot90(slice_data)  # Rotate to ensure correct radiological orientation (RAS+)
            crosshair_x, crosshair_y = self.crosshair_pos[0], self.crosshair_pos[1]
            
        elif self.view_type == 'coronal':
            # Make sure current slice is within bounds
            if self.current_slice >= self.nifti_data.shape[1]:
                self.current_slice = self.nifti_data.shape[1] - 1
                
            # Get coronal slice (showing X-Z plane at Y position)
            slice_data = self.nifti_data[:, self.current_slice, :]
            slice_data = np.rot90(slice_data, k=1)  # Explicitly specify rotation count
            crosshair_x, crosshair_y = self.crosshair_pos[0], self.crosshair_pos[2]
            
        elif self.view_type == 'sagittal':
            # Make sure current slice is within bounds
            if self.current_slice >= self.nifti_data.shape[0]:
                self.current_slice = self.nifti_data.shape[0] - 1
                
            # Get sagittal slice (showing Y-Z plane at X position)
            slice_data = self.nifti_data[self.current_slice, :, :]
            slice_data = np.rot90(slice_data, k=1)  # Adjust rotation count
            crosshair_x, crosshair_y = self.crosshair_pos[1], self.crosshair_pos[2]
        
        print(f"{self.view_type} view: slice={self.current_slice}, "
              f"crosshair=({crosshair_x},{crosshair_y}), "
              f"slice_shape={slice_data.shape if slice_data is not None else 'None'}")
        
        if slice_data is not None:
            # Ensure consistent display proportions for all views
            if slice_data.shape[0] != slice_data.shape[1]:
                max_dim = max(slice_data.shape)
                padded_data = np.zeros((max_dim, max_dim), dtype=slice_data.dtype)
                
                pad_x = (max_dim - slice_data.shape[1]) // 2
                pad_y = (max_dim - slice_data.shape[0]) // 2
                
                padded_data[pad_y:pad_y+slice_data.shape[0], 
                           pad_x:pad_x+slice_data.shape[1]] = slice_data
                
                crosshair_x += pad_x
                crosshair_y += pad_y
                
                slice_data = padded_data
        
        return slice_data, crosshair_x, crosshair_y
        
    def set_slice(self, slice_num):
        """Set the current slice number"""
        if self.nifti_data is None:
            return
            
        # Get maximum slice number for this view
        max_slice = 0
        if self.view_type == 'axial':
            max_slice = self.nifti_data.shape[2] - 1
        elif self.view_type == 'coronal':
            max_slice = self.nifti_data.shape[1] - 1
        elif self.view_type == 'sagittal':
            max_slice = self.nifti_data.shape[0] - 1
            
        # Ensure slice is within bounds
        self.current_slice = max(0, min(slice_num, max_slice))
        self.update_display()


class NiftiViewer(QDialog):
    """Dialog for viewing and setting the origin of NIFTI files with 3 synchronized views"""
    
    origin_set = pyqtSignal(list)  # Signal emitted when origin is set
    
    def __init__(self, parent=None):
        try:
            super(NiftiViewer, self).__init__(parent)
            self.setWindowTitle("NIFTI Viewer - Triple View")
            
            # 设置为非模态对话框，这样当嵌入到主窗口时可以更好地工作
            self.setModal(False)
            
            # 当作为独立窗口时的合适大小
            if parent is None or isinstance(parent, QMainWindow):
                self.resize(1200, 800)
            
            self.image_file = None
            self.nifti_data = None
            self.affine = None
            self.crosshair_pos = [0, 0, 0]  # x, y, z in voxel coordinates
            
            self.setup_ui()
            
            # 作为独立窗口时设置窗口属性，确保始终在顶部显示
            if parent is None or isinstance(parent, QMainWindow):
                self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        except Exception as e:
            import traceback
            print(f"Error initializing NiftiViewer: {str(e)}")
            print(traceback.format_exc())
            raise
    
    # 方法接受，允许以嵌入方式使用（不自动显示）
    def exec_(self):
        """如果是嵌入在主窗口中，则不需要模态对话框行为"""
        if self.parent() is None or isinstance(self.parent(), QMainWindow):
            return super(NiftiViewer, self).exec_()
        else:
            # 如果是嵌入式使用，直接返回True
            return True
    
    def setup_ui(self):
        """Set up the UI components"""
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Create splitter for resizable views
        self.splitter = QSplitter(Qt.Horizontal)
        
        # Create the three view canvases
        self.axial_canvas = SliceCanvas(self, width=5, height=5, view_type='axial')
        self.coronal_canvas = SliceCanvas(self, width=5, height=5, view_type='coronal')
        self.sagittal_canvas = SliceCanvas(self, width=5, height=5, view_type='sagittal')
        
        # Connect signals from canvases
        self.axial_canvas.slice_clicked.connect(self.on_slice_clicked)
        self.coronal_canvas.slice_clicked.connect(self.on_slice_clicked)
        self.sagittal_canvas.slice_clicked.connect(self.on_slice_clicked)
        
        # Add canvases to splitter with containers
        for canvas in [self.axial_canvas, self.coronal_canvas, self.sagittal_canvas]:
            container = QWidget()
            layout = QVBoxLayout(container)
            layout.setContentsMargins(2, 2, 2, 2)
            layout.addWidget(canvas)
            self.splitter.addWidget(container)
        
        # Make the views take equal space initially
        width = self.width() // 3
        self.splitter.setSizes([width, width, width])
        
        # Set stretch factors to ensure equal resizing
        for i in range(3):
            self.splitter.setStretchFactor(i, 1)
        
        # Add splitter to main layout
        main_layout.addWidget(self.splitter, 7)  # 70% of height
        
        # Add coordinate display
        self.coords_label = QLabel("坐标: X=0, Y=0, Z=0")
        self.coords_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.coords_label)
        
        # Controls layout (horizontal)
        controls_layout = QHBoxLayout()
        
        # Origin controls
        origin_group = QGroupBox("Origin")
        origin_layout = QVBoxLayout(origin_group)
        
        # Coordinates layout
        coords_layout = QGridLayout()
        coords_layout.addWidget(QLabel("X (mm):"), 0, 0)
        coords_layout.addWidget(QLabel("Y (mm):"), 1, 0)
        coords_layout.addWidget(QLabel("Z (mm):"), 2, 0)
        
        self.x_spinbox = QDoubleSpinBox()
        self.y_spinbox = QDoubleSpinBox()
        self.z_spinbox = QDoubleSpinBox()
        
        for spinbox in [self.x_spinbox, self.y_spinbox, self.z_spinbox]:
            spinbox.setRange(-1000, 1000)
            spinbox.setDecimals(1)
            spinbox.setSingleStep(1)
            spinbox.setValue(0)
        
        coords_layout.addWidget(self.x_spinbox, 0, 1)
        coords_layout.addWidget(self.y_spinbox, 1, 1)
        coords_layout.addWidget(self.z_spinbox, 2, 1)
        
        origin_layout.addLayout(coords_layout)
        
        # Origin buttons
        origin_btn_layout = QHBoxLayout()
        self.get_pos_btn = QPushButton("Get Position")
        self.set_origin_btn = QPushButton("Set as Origin")
        
        self.get_pos_btn.clicked.connect(self.get_crosshair_position)
        self.set_origin_btn.clicked.connect(self.set_origin)
        
        origin_btn_layout.addWidget(self.get_pos_btn)
        origin_btn_layout.addWidget(self.set_origin_btn)
        origin_layout.addLayout(origin_btn_layout)
        
        controls_layout.addWidget(origin_group)
        
        # Slice Controls
        slice_group = QGroupBox("Slice Controls")
        slice_layout = QGridLayout(slice_group)
        
        # Create slice sliders for each view
        self.create_slice_controls(slice_layout, 'Axial (Z):', 0, self.on_axial_slice_changed)
        self.create_slice_controls(slice_layout, 'Coronal (Y):', 1, self.on_coronal_slice_changed)
        self.create_slice_controls(slice_layout, 'Sagittal (X):', 2, self.on_sagittal_slice_changed)
        
        controls_layout.addWidget(slice_group)
        
        # Action buttons
        action_group = QGroupBox("Actions")
        action_layout = QVBoxLayout(action_group)
        
        self.save_btn = QPushButton("Save Changes")
        self.close_btn = QPushButton("Close")
        
        self.save_btn.clicked.connect(self.save_changes)
        self.close_btn.clicked.connect(self.reject)
        
        action_layout.addWidget(self.save_btn)
        action_layout.addWidget(self.close_btn)
        
        controls_layout.addWidget(action_group)
        
        # Add controls to main layout
        main_layout.addLayout(controls_layout, 3)  # 30% of height
    
    def resizeEvent(self, event):
        """Handle window resize event to ensure equal view sizes"""
        super(NiftiViewer, self).resizeEvent(event)
        if hasattr(self, 'splitter'):
            width = self.splitter.width() // 3
            self.splitter.setSizes([width, width, width])
    
    def create_slice_controls(self, parent_layout, label_text, row, slot_function):
        """Create a set of slider and spinbox controls for a slice view"""
        parent_layout.addWidget(QLabel(label_text), row, 0)
        
        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(0)
        slider.setMaximum(100)
        slider.setValue(50)
        slider.setTickPosition(QSlider.TicksBelow)
        slider.setTickInterval(10)
        
        spinbox = QSpinBox()
        spinbox.setMinimum(0)
        spinbox.setMaximum(100)
        spinbox.setValue(50)
        
        # Connect signals
        slider.valueChanged.connect(lambda value: self.on_slider_changed(spinbox, value, slot_function))
        spinbox.valueChanged.connect(lambda value: self.on_spinbox_changed(slider, value, slot_function))
        
        parent_layout.addWidget(slider, row, 1)
        parent_layout.addWidget(spinbox, row, 2)
        
        # Store references to controls
        if row == 0:  # Axial
            self.axial_slider = slider
            self.axial_spinbox = spinbox
        elif row == 1:  # Coronal
            self.coronal_slider = slider
            self.coronal_spinbox = spinbox
        elif row == 2:  # Sagittal
            self.sagittal_slider = slider
            self.sagittal_spinbox = spinbox
    
    def on_slider_changed(self, spinbox, value, slot_function):
        """Generic handler for slider value changes"""
        spinbox.blockSignals(True)
        spinbox.setValue(value)
        spinbox.blockSignals(False)
        slot_function(value)
    
    def on_spinbox_changed(self, slider, value, slot_function):
        """Generic handler for spinbox value changes"""
        slider.blockSignals(True)
        slider.setValue(value)
        slider.blockSignals(False)
        slot_function(value)
    
    def on_axial_slice_changed(self, value):
        """Handle axial slice change"""
        if self.nifti_data is None:
            return
            
        self.crosshair_pos[2] = value
        self.update_all_views()
    
    def on_coronal_slice_changed(self, value):
        """Handle coronal slice change"""
        if self.nifti_data is None:
            return
            
        self.crosshair_pos[1] = value
        self.update_all_views()
    
    def on_sagittal_slice_changed(self, value):
        """Handle sagittal slice change"""
        if self.nifti_data is None:
            return
            
        self.crosshair_pos[0] = value
        self.update_all_views()
    
    def on_slice_clicked(self, view_type, x, y):
        """Handle click on a slice"""
        if self.nifti_data is None:
            return
        
        original_x, original_y = x, y
        
        dims = self.nifti_data.shape
            
        if view_type == 'axial':
            self.crosshair_pos[0] = max(0, min(x, dims[0]-1))
            self.crosshair_pos[1] = max(0, min(y, dims[1]-1))
        elif view_type == 'coronal':
            self.crosshair_pos[0] = max(0, min(x, dims[0]-1))
            self.crosshair_pos[2] = max(0, min(y, dims[2]-1))
        elif view_type == 'sagittal':
            self.crosshair_pos[1] = max(0, min(x, dims[1]-1))
            self.crosshair_pos[2] = max(0, min(y, dims[2]-1))
        
        print(f"点击视图: {view_type}, 坐标: ({original_x},{original_y}), "
              f"调整后坐标: ({x},{y}), "
              f"更新后十字线位置: {self.crosshair_pos}")
        
        self.update_all_views(update_controls=True)
    
    def update_all_views(self, update_controls=False):
        """Update all slice views"""
        if self.nifti_data is None:
            return
            
        dims = self.nifti_data.shape
        for i in range(3):
            self.crosshair_pos[i] = max(0, min(self.crosshair_pos[i], dims[i]-1))
            
        self.axial_canvas.current_slice = self.crosshair_pos[2]
        self.coronal_canvas.current_slice = self.crosshair_pos[1]
        self.sagittal_canvas.current_slice = self.crosshair_pos[0]
        
        self.axial_canvas.update_slice(
            self.nifti_data, self.affine, self.crosshair_pos
        )
        self.coronal_canvas.update_slice(
            self.nifti_data, self.affine, self.crosshair_pos
        )
        self.sagittal_canvas.update_slice(
            self.nifti_data, self.affine, self.crosshair_pos
        )
        
        if update_controls:
            self.axial_slider.blockSignals(True)
            self.axial_spinbox.blockSignals(True)
            self.coronal_slider.blockSignals(True)
            self.coronal_spinbox.blockSignals(True)
            self.sagittal_slider.blockSignals(True)
            self.sagittal_spinbox.blockSignals(True)
            
            self.axial_slider.setValue(self.crosshair_pos[2])
            self.axial_spinbox.setValue(self.crosshair_pos[2])
            self.coronal_slider.setValue(self.crosshair_pos[1])
            self.coronal_spinbox.setValue(self.crosshair_pos[1])
            self.sagittal_slider.setValue(self.crosshair_pos[0])
            self.sagittal_spinbox.setValue(self.crosshair_pos[0])
            
            status_text = f"坐标: X={self.crosshair_pos[0]}, Y={self.crosshair_pos[1]}, Z={self.crosshair_pos[2]}"
            self.setWindowTitle(f"NIFTI Viewer - {os.path.basename(self.image_file)} - {status_text}")
            
            self.axial_slider.blockSignals(False)
            self.axial_spinbox.blockSignals(False)
            self.coronal_slider.blockSignals(False)
            self.coronal_spinbox.blockSignals(False)
            self.sagittal_slider.blockSignals(False)
            self.sagittal_spinbox.blockSignals(False)
    
    def load_nifti(self, file_path):
        """Load a NIFTI file for viewing"""
        try:
            if ',' in file_path:
                original_path = file_path
                file_path = file_path.split(',')[0]
                print(f"Detected parameter path, using base path: {file_path}")
            
            self.image_file = file_path
            
            print(f"Starting to load NIFTI file: {file_path}")
            print(f"File exists: {os.path.exists(file_path)}")
            
            if not os.path.exists(file_path):
                print(f"Error: File does not exist: {file_path}")
                QMessageBox.critical(self, "Error", f"File does not exist: {file_path}")
                return False
                
            print(f"File size: {os.path.getsize(file_path)} bytes")
            
            try:
                nifti_img = nib.load(file_path)
                print(f"NIFTI loaded successfully: {nifti_img}")
                print(f"NIFTI shape: {nifti_img.shape}")
                
                try:
                    self.nifti_data = nifti_img.get_fdata()
                except Exception as e:
                    print(f"Error using get_fdata(): {str(e)}")
                    try:
                        self.nifti_data = nifti_img.get_data()
                    except Exception as e2:
                        print(f"Error using get_data(): {str(e2)}")
                        self.nifti_data = np.array(nifti_img.dataobj)
                
                self.affine = nifti_img.affine
                
                if len(self.nifti_data.shape) < 3:
                    if len(self.nifti_data.shape) == 2:
                        h, w = self.nifti_data.shape
                        self.nifti_data = self.nifti_data.reshape(h, w, 1)
                    else:
                        raise ValueError(f"Unsupported NIFTI dimensions: {self.nifti_data.shape}")
                elif len(self.nifti_data.shape) > 3:
                    self.nifti_data = self.nifti_data[..., 0]
                
                if np.isnan(self.nifti_data).any() or np.isinf(self.nifti_data).any():
                    print("Warning: Data contains NaN or Inf values, replacing with valid values")
                    self.nifti_data = np.nan_to_num(self.nifti_data)
                
                dims = self.nifti_data.shape
                self.crosshair_pos = [dim // 2 for dim in dims[:3]]
                
                self.setWindowTitle(f"NIFTI Viewer - {os.path.basename(file_path)} - {dims[0]}x{dims[1]}x{dims[2]}")
                
                self.update_slice_controls(dims)
                
                self.update_origin_display()
                
                self.update_all_views(update_controls=True)
                
                return True
                
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                print(f"Error loading NIFTI: {str(e)}\n{error_details}")
                QMessageBox.critical(self, "Error", f"Failed to load NIFTI: {str(e)}")
                return False
                
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Error in load_nifti: {str(e)}\n{error_details}")
            QMessageBox.critical(self, "Error", f"Error loading NIFTI file: {str(e)}")
            return False
    
    def update_slice_controls(self, dims):
        """Update the slice control ranges based on image dimensions"""
        self.axial_slider.setMaximum(dims[2] - 1)
        self.axial_spinbox.setMaximum(dims[2] - 1)
        self.coronal_slider.setMaximum(dims[1] - 1)
        self.coronal_spinbox.setMaximum(dims[1] - 1)
        self.sagittal_slider.setMaximum(dims[0] - 1)
        self.sagittal_spinbox.setMaximum(dims[0] - 1)
        
        center = [dim // 2 for dim in dims[:3]]
        self.axial_slider.setValue(center[2])
        self.axial_spinbox.setValue(center[2])
        self.coronal_slider.setValue(center[1])
        self.coronal_spinbox.setValue(center[1])
        self.sagittal_slider.setValue(center[0])
        self.sagittal_spinbox.setValue(center[0])
    
    def get_crosshair_position(self):
        """Get the current crosshair position in mm"""
        if self.nifti_data is None or self.affine is None:
            return
            
        x, y, z = self.crosshair_pos
        vox_coords = np.array([x, y, z, 1])
        mm_coords = np.dot(self.affine, vox_coords)[:3]
        
        self.x_spinbox.setValue(mm_coords[0])
        self.y_spinbox.setValue(mm_coords[1])
        self.z_spinbox.setValue(mm_coords[2])
    
    def update_origin_display(self):
        """Update the origin display from the NIFTI file"""
        if self.affine is not None:
            origin = self.affine[:3, 3]
            self.x_spinbox.setValue(origin[0])
            self.y_spinbox.setValue(origin[1])
            self.z_spinbox.setValue(origin[2])
    
    def set_origin(self):
        """Set the origin to the current crosshair position"""
        if self.nifti_data is None or self.affine is None:
            return
        
        try:
            x, y, z = self.crosshair_pos
            vox_coords = np.array([x, y, z, 1])
            mm_coords = np.dot(self.affine, vox_coords)[:3]
            
            # 更新显示
            self.x_spinbox.setValue(mm_coords[0])
            self.y_spinbox.setValue(mm_coords[1])
            self.z_spinbox.setValue(mm_coords[2])
            
            # 发出信号并显示消息
            self.origin_set.emit(mm_coords.tolist())
            
            # 当嵌入到主窗口中时，不显示消息框（避免干扰主界面）
            if self.parent() is None or isinstance(self.parent(), QMainWindow):
                QMessageBox.information(self, "Origin Updated", 
                                        f"Origin set to: [{mm_coords[0]:.1f}, {mm_coords[1]:.1f}, {mm_coords[2]:.1f}]")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to set origin: {str(e)}")
    
    def save_changes(self):
        """Save changes to the NIFTI file"""
        if self.nifti_data is None or self.affine is None or self.image_file is None:
            return
            
        try:
            new_origin = [
                self.x_spinbox.value(),
                self.y_spinbox.value(),
                self.z_spinbox.value()
            ]
            
            nifti_img = nib.load(self.image_file)
            
            new_affine = nifti_img.affine.copy()
            new_affine[:3, 3] = new_origin
            
            new_img = nib.Nifti1Image(nifti_img.get_fdata(), new_affine, nifti_img.header)
            
            nib.save(new_img, self.image_file)
            
            # 显示状态消息
            QMessageBox.information(self, "Success", "Origin updated and saved successfully.")
            
            # 更新本地数据
            self.affine = new_affine
            self.update_all_views()
            
            # 发出信号通知新设置的原点
            self.origin_set.emit(new_origin)
            
            # 完成对话框
            if self.parent() is None or isinstance(self.parent(), QMainWindow):
                self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save changes: {str(e)}")
