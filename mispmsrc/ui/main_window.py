#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import logging
import glob
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFileDialog, QMessageBox, QGroupBox, QStatusBar, QProgressBar,
    QTextEdit, QApplication, QComboBox, QInputDialog, QDialog, QGridLayout, QDoubleSpinBox
)
from PyQt5.QtCore import Qt, pyqtSlot, QSize
from PyQt5.QtGui import QFont

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(project_root)

from mispmsrc.core.matlab_engine import MatlabEngine
from mispmsrc.utils.logger import Logger
from mispmsrc.ui.progress_manager import ProgressManager
from mispmsrc.ui.coreg_dialog import CoregisterDialog
from mispmsrc.ui.normalize_dialog import NormalizeDialog
from mispmsrc.ui.image_view import ImageView
from mispmsrc.ui.cl_analysis_dialog import CLAnalysisDialog
from mispmsrc.CLRefactoring.PIB_SUVr_CLs_calc import PIBAnalyzer

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
        color = "white"  # 将默认颜色从"black"改为"white"
        if level == "WARNING":
            color = "orange"
        elif level == "ERROR":
            color = "red"
        elif level == "SUCCESS":
            color = "lightgreen"  # 将成功信息的颜色调整为更亮的绿色
            
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
        self.run_script_btn = QPushButton("LC Analysis")
        self.setup_ui()
        
        # 设置黑色主题样式
        self.setup_dark_theme()
        
        # Connect signals
        self.connect_signals()
        
        # Start MATLAB engine
        self.start_matlab_engine()
    
    def setup_ui(self):
        """Set up the UI components"""
        # Set window properties
        self.setWindowTitle("SPM PyQt Interface")
        self.setMinimumSize(1200, 800)
        
        # Create central widget with horizontal split layout (two columns)
        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(5)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Left panel for controls (approximately 1/4 of width)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(5)
        left_layout.setContentsMargins(2, 2, 2, 2)
        
        # Right panel (approximately 3/4 of width)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(5)
        right_layout.setContentsMargins(2, 2, 2, 2)
        
        # Engine controls group
        engine_group = QGroupBox("MATLAB Engine")
        engine_layout = QVBoxLayout()
        self.engine_status_label = QLabel("Engine: Not running")
        self.start_engine_btn = QPushButton("Start Engine")
        self.stop_engine_btn = QPushButton("Stop Engine")
        engine_layout.addWidget(self.engine_status_label)
        engine_layout.addWidget(self.start_engine_btn, 0, Qt.AlignLeft)
        engine_layout.addWidget(self.stop_engine_btn, 0, Qt.AlignLeft)
        engine_group.setLayout(engine_layout)
        left_layout.addWidget(engine_group)
        
        # DICOM/NIFTI group
        dicom_group = QGroupBox("Convert DICOM To NIFTI")
        dicom_layout = QVBoxLayout()
        self.import_dicom_btn = QPushButton("Import DICOM")
        self.convert_nifti_btn = QPushButton("Convert To NiFTI")
        dicom_layout.addWidget(self.import_dicom_btn, 0, Qt.AlignLeft)
        dicom_layout.addWidget(self.convert_nifti_btn, 0, Qt.AlignLeft)
        dicom_group.setLayout(dicom_layout)
        left_layout.addWidget(dicom_group)
        
        # Image processing group
        image_group = QGroupBox("Image Processing")
        image_layout = QVBoxLayout()

        # Create all buttons
        self.load_nifti_btn = QPushButton("Load NIFTI")
        self.set_origin_btn = QPushButton("Set Origin")
        self.coregister_btn = QPushButton("Coregistration")
        self.check_reg_btn = QPushButton("Check Registration")
        self.normalise_btn = QPushButton("Normalise")
        self.run_script_btn = QPushButton("LC Analysis")
        
        # Batch processing buttons
        self.batch_set_origin_btn = QPushButton("Batch Set Origin")
        self.batch_coregister_btn = QPushButton("Batch Coregister")
        self.batch_normalise_btn = QPushButton("Batch Normalise")
        
        # 重新排列按钮顺序 - 按照要求排列
        button_order = [
            self.load_nifti_btn,        # 1. Load NIFTI
            self.set_origin_btn,        # 2. Set Origin
            self.coregister_btn,        # 3. Coregistration
            self.check_reg_btn,         # 4. Check Registration
            self.normalise_btn,         # 5. Normalise
            self.run_script_btn,        # 6. LC Analysis
            self.batch_set_origin_btn,  # 7. Batch Set Origin
            self.batch_coregister_btn,  # 8. Batch Coregister
            self.batch_normalise_btn    # 9. Batch Normalise
        ]
        
        # Add buttons to layout, left-aligned
        for btn in button_order:
            btn_layout = QHBoxLayout()
            btn_layout.addWidget(btn)
            btn_layout.addStretch()
            image_layout.addLayout(btn_layout)
        
        image_group.setLayout(image_layout)
        left_layout.addWidget(image_group)
        
        # Add stretch to push everything up
        left_layout.addStretch()
        
        # Right panel - upper part: Image Visualization
        image_view_group = QGroupBox("Image Visualization")
        self.image_view_layout = QVBoxLayout()  # 保存引用，以便后续更改内容
        self.image_view_layout.addWidget(self.image_view)
        image_view_group.setLayout(self.image_view_layout)
        right_layout.addWidget(image_view_group, 7)  # 70% of right panel height
        
        # 创建NIFTI查看器实例，但一开始不显示
        self.nifti_viewer = None
        self.is_nifti_viewer_showing = False
        
        # Right panel - lower part: Log
        log_group = QGroupBox("Log")
        log_layout = QVBoxLayout()
        self.log_widget = LogWidget()
        log_layout.addWidget(self.log_widget)
        log_group.setLayout(log_layout)
        right_layout.addWidget(log_group, 3)  # 30% of right panel height
        
        # Add panels to main layout with proportional width
        main_layout.addWidget(left_panel, 1)  # 25% of width
        main_layout.addWidget(right_panel, 3)  # 75% of width
        
        # Set central widget
        self.setCentralWidget(central_widget)
        
        # Create status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        
        # Add progress bar to status bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(15)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        self.statusBar.addPermanentWidget(self.progress_bar)
        
        # Set initial button states
        self.update_button_states(False)
        
        # Create progress manager
        self.progress_manager = ProgressManager(self.progress_bar, self.statusBar)
        
        # Create button list for uniform styling
        all_buttons = [
            self.start_engine_btn, 
            self.stop_engine_btn,
            self.import_dicom_btn,
            self.load_nifti_btn,
            self.coregister_btn,
            self.normalise_btn,
            self.set_origin_btn,
            self.check_reg_btn,
            self.run_script_btn,
            self.convert_nifti_btn,
            self.batch_coregister_btn,
            self.batch_normalise_btn,
            self.batch_set_origin_btn
        ]
        
        # Apply uniform styling to all buttons
        for btn in all_buttons:
            btn.setFixedHeight(25)
            btn.setFixedWidth(120)
    
    def setup_dark_theme(self):
        """设置黑色主题样式"""
        # 定义黑色主题样式
        dark_style = """
        QMainWindow, QDialog {
            background-color: #2D2D30;
            color: #CCCCCC;
        }
        QWidget {
            background-color: #2D2D30;
            color: #CCCCCC;
        }
        QGroupBox {
            border: 1px solid #3F3F46;
            border-radius: 4px;
            margin-top: 8px;
            font-weight: bold;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 3px;
        }
        QPushButton {
            background-color: #3F3F46;
            color: #CCCCCC;
            border: 1px solid #555555;
            border-radius: 3px;
            padding: 5px;
        }
        QPushButton:hover {
            background-color: #505056;
        }
        QPushButton:pressed {
            background-color: #4080C0;
        }
        QPushButton:disabled {
            background-color: #2D2D30;
            color: #666666;
            border: 1px solid #3F3F46;
        }
        QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
            background-color: #1E1E1E;
            color: #CCCCCC;
            border: 1px solid #3F3F46;
            border-radius: 2px;
            padding: 2px;
        }
        QComboBox::drop-down {
            border: none;
            width: 20px;
        }
        QComboBox QAbstractItemView {
            background-color: #1E1E1E;
            selection-background-color: #3F3F46;
        }
        QTextEdit, QListView {
            background-color: #1E1E1E;
            color: #CCCCCC;
            border: 1px solid #3F3F46;
        }
        QMenuBar {
            background-color: #2D2D30;
            color: #CCCCCC;
        }
        QMenuBar::item:selected {
            background-color: #3F3F46;
        }
        QMenu {
            background-color: #2D2D30;
            color: #CCCCCC;
        }
        QMenu::item:selected {
            background-color: #3F3F46;
        }
        QLabel {
            color: #CCCCCC;
        }
        QStatusBar {
            background-color: #1E1E1E;
            color: #CCCCCC;
        }
        QProgressBar {
            border: 1px solid #3F3F46;
            border-radius: 2px;
            background-color: #1E1E1E;
            text-align: center;
            color: #CCCCCC;
        }
        QProgressBar::chunk {
            background-color: #4080C0;
        }
        QTabWidget::pane {
            border: 1px solid #3F3F46;
        }
        QTabBar::tab {
            background-color: #2D2D30;
            color: #CCCCCC;
            border: 1px solid #3F3F46;
            border-bottom: none;
            padding: 5px 10px;
        }
        QTabBar::tab:selected {
            background-color: #3F3F46;
        }
        QScrollBar:vertical {
            border: none;
            background-color: #2D2D30;
            width: 12px;
            margin: 12px 0 12px 0;
        }
        QScrollBar::handle:vertical {
            background-color: #3F3F46;
            min-height: 20px;
            border-radius: 3px;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            border: none;
            background: none;
            height: 12px;
        }
        QScrollBar:horizontal {
            border: none;
            background-color: #2D2D30;
            height: 12px;
            margin: 0 12px 0 12px;
        }
        QScrollBar::handle:horizontal {
            background-color: #3F3F46;
            min-width: 20px;
            border-radius: 3px;
        }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            border: none;
            background: none;
            width: 12px;
        }
        """
        # 应用样式表到应用程序
        QApplication.instance().setStyleSheet(dark_style)
        self.setStyleSheet(dark_style)
        
        # 将样式应用到LogWidget - 修改文本颜色为白色
        self.log_widget.setStyleSheet("""
        QTextEdit {
            background-color: #1E1E1E;
            color: white;  /* 修改默认文本颜色为白色 */
            border: 1px solid #3F3F46;
            font-family: Consolas, Monospace;
            font-size: 9pt;
        }
        """)
    
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
        self.load_nifti_btn.clicked.connect(self.load_nifti)  # Now calls our new method for viewing only
        self.coregister_btn.clicked.connect(self.coregister_images)
        self.normalise_btn.clicked.connect(self.normalise_image)
        self.set_origin_btn.clicked.connect(self.set_origin)
        self.check_reg_btn.clicked.connect(self.check_registration)
        self.run_script_btn.clicked.connect(self.show_cl_analysis_dialog)
        self.convert_nifti_btn.clicked.connect(self.convert_to_nifti)  # 新增信号连接
        
        # 新增批处理按钮信号连接
        self.batch_coregister_btn.clicked.connect(self.batch_coregister_images)
        self.batch_normalise_btn.clicked.connect(self.batch_normalise_images)
        self.batch_set_origin_btn.clicked.connect(self.batch_set_origin)
    
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
        self.convert_nifti_btn.setEnabled(engine_running)  # 新增按钮状态控制
        
        # 批处理按钮
        self.batch_coregister_btn.setEnabled(engine_running)
        self.batch_normalise_btn.setEnabled(engine_running)
        self.batch_set_origin_btn.setEnabled(engine_running)
    
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
            return
        
        # Get output directory
        output_dir = QFileDialog.getExistingDirectory(
            self, 
            "Select Output Directory for NIFTI Files",
            "",
            QFileDialog.ShowDirsOnly
        )
        if not output_dir:
            self.log_widget.append_log("No output directory selected, canceling import", "WARNING")
            return
        
        if msgBox.clickedButton() == folder_btn:
            # Select directory
            directory = QFileDialog.getExistingDirectory(self, "Select DICOM Directory")
            if directory:
                self.log_widget.append_log(f"Selected DICOM directory: {directory}")
                result_files = self.matlab_engine.convert_to_nifti(directory, output_dir)
                if result_files:
                    self.log_widget.append_log(f"Successfully converted {len(result_files)} DICOM files to NIFTI", "SUCCESS")
                else:
                    self.log_widget.append_log("No NIFTI files were created", "ERROR")
        elif msgBox.clickedButton() == files_btn:
            # Select files
            files, _ = QFileDialog.getOpenFileNames(self, "Select DICOM Files", "", "DICOM Files (*.dcm)")
            if files:
                # For individual files, we need a temporary directory
                import tempfile
                temp_dir = tempfile.mkdtemp()
                self.log_widget.append_log(f"Selected {len(files)} DICOM files")
                
                # Copy files to temp directory
                import shutil
                for file_path in files:
                    shutil.copy(file_path, temp_dir)
                
                # Convert from temp directory
                result_files = self.matlab_engine.convert_to_nifti(temp_dir, output_dir)
                
                # Clean up temp directory
                shutil.rmtree(temp_dir, ignore_errors=True)
                
                if result_files:
                    self.log_widget.append_log(f"Successfully converted {len(result_files)} DICOM files to NIFTI", "SUCCESS")
                else:
                    self.log_widget.append_log("No NIFTI files were created", "ERROR")
    
    @pyqtSlot()
    def load_nifti(self):
        """Load NIFTI file for viewing only (without setting origin)"""
        self.log_widget.append_log("Loading NIFTI file for viewing...")
        
        file_path, _ = QFileDialog.getOpenFileName(self, "Select NIFTI File", "", "NIFTI Files (*.nii *.nii.gz)")
        if file_path:
            self.log_widget.append_log(f"Selected NIFTI file: {file_path}")
            
            # 添加简洁的提示
            self.log_widget.append_log("Loading NIFTI viewer in visualization panel...")
            
            try:
                # 尝试导入所需包
                import nibabel
                import matplotlib
                from matplotlib.figure import Figure
                
                # 如果导入成功，在主窗口中显示NIFTI查看器
                self.view_nifti_image(file_path)
                    
            except ImportError as e:
                # 优雅地处理缺少依赖项
                self.log_widget.append_log(f"Missing required packages: {str(e)}", "ERROR")
                QMessageBox.critical(
                    self,
                    "Missing Dependencies",
                    f"Could not open NIFTI viewer due to missing dependencies:\n\n{str(e)}\n\n"
                    "Please install the required packages by running:\n"
                    "pip install -r requirements.txt"
                )
            except Exception as e:
                # 处理其他错误
                self.log_widget.append_log(f"Error: {str(e)}", "ERROR")
                QMessageBox.critical(
                    self,
                    "Error",
                    f"An error occurred while opening the viewer:\n\n{str(e)}"
                )

    def view_nifti_image(self, file_path):
        """View NIFTI image in the visualization panel instead of a separate window"""
        try:
            # 导入NIFTI查看器类
            from mispmsrc.ui.nifti_viewer import NiftiViewer
            
            # 如果已经有查看器，先移除它
            self.hide_nifti_viewer()
            
            # 创建查看器实例
            self.nifti_viewer = NiftiViewer(self)
            
            # 将查看器设置为嵌入式模式 - 隐藏操作按钮
            self.nifti_viewer.save_btn.setVisible(False)
            self.nifti_viewer.set_origin_btn.setVisible(False)
            self.nifti_viewer.close_btn.setText("Return to Main View")
            self.nifti_viewer.close_btn.clicked.disconnect()  # 移除原有连接
            self.nifti_viewer.close_btn.clicked.connect(self.hide_nifti_viewer)  # 添加新连接
            
            # 加载NIFTI文件
            success = self.nifti_viewer.load_nifti(file_path)
            
            if success:
                # 隐藏图像查看器
                self.image_view.setVisible(False)
                
                # 将NIFTI查看器添加到图像查看布局中
                self.image_view_layout.addWidget(self.nifti_viewer)
                self.nifti_viewer.setVisible(True)
                self.is_nifti_viewer_showing = True
                
                # 添加状态信息
                self.log_widget.append_log("NIFTI viewer displayed in visualization panel")
            else:
                self.log_widget.append_log("Failed to load NIFTI file in viewer", "ERROR")
                self.nifti_viewer = None
        except Exception as e:
            import traceback
            self.log_widget.append_log(f"Error viewing NIFTI file: {str(e)}", "ERROR")
            self.logger.error(traceback.format_exc())
            
    def hide_nifti_viewer(self):
        """隐藏NIFTI查看器，恢复主界面图像查看器"""
        if self.nifti_viewer and self.is_nifti_viewer_showing:
            # 从布局中移除NIFTI查看器
            self.image_view_layout.removeWidget(self.nifti_viewer)
            self.nifti_viewer.setVisible(False)
            self.nifti_viewer = None
            self.is_nifti_viewer_showing = False
            
            # 显示回原图像查看器
            self.image_view.setVisible(True)
            self.log_widget.append_log("Returned to main view")

    @pyqtSlot()
    def set_origin(self):
        """Set origin of the image using Python's NIFTI viewer embedded in main window"""
        self.log_widget.append_log("Opening origin setting interface...")
        
        file_path, _ = QFileDialog.getOpenFileName(self, "Select NIFTI File", "", "NIFTI Files (*.nii *.nii.gz)")
        if file_path:
            self.log_widget.append_log(f"Selected NIFTI file: {file_path}")
            
            # 添加提示
            self.log_widget.append_log("Loading origin setting interface in visualization panel...")
            
            try:
                # 尝试导入所需包
                import nibabel
                import matplotlib
                from matplotlib.figure import Figure
                from mispmsrc.ui.nifti_viewer import NiftiViewer
                
                # 如果已经有查看器，先移除它
                self.hide_nifti_viewer()
                
                # 创建查看器实例
                self.nifti_viewer = NiftiViewer(self)
                
                # 添加信号连接，处理原点设置
                self.nifti_viewer.origin_set.connect(self.on_origin_set)
                
                # 修改关闭按钮行为
                self.nifti_viewer.close_btn.setText("Return to Main View")
                self.nifti_viewer.close_btn.clicked.disconnect()  # 移除原有连接
                self.nifti_viewer.close_btn.clicked.connect(self.hide_nifti_viewer)  # 添加新连接
                
                # 加载NIFTI文件
                success = self.nifti_viewer.load_nifti(file_path)
                
                if success:
                    # 隐藏图像查看器
                    self.image_view.setVisible(False)
                    
                    # 将NIFTI查看器添加到图像查看布局中
                    self.image_view_layout.addWidget(self.nifti_viewer)
                    self.nifti_viewer.setVisible(True)
                    self.is_nifti_viewer_showing = True
                    
                    # 添加状态信息
                    self.log_widget.append_log("Origin setting interface displayed in visualization panel")
                else:
                    self.log_widget.append_log("Failed to load NIFTI file", "ERROR")
                    self.nifti_viewer = None
                    
            except ImportError as e:
                # 优雅地处理缺少依赖项
                self.log_widget.append_log(f"Missing required packages: {str(e)}", "ERROR")
                QMessageBox.critical(
                    self,
                    "Missing Dependencies",
                    f"Could not open NIFTI viewer due to missing dependencies:\n\n{str(e)}\n\n"
                    "Please install the required packages by running:\n"
                    "pip install -r requirements.txt"
                )
            except Exception as e:
                # 处理其他错误
                self.log_widget.append_log(f"Error: {str(e)}", "ERROR")
                QMessageBox.critical(
                    self,
                    "Error",
                    f"An error occurred while setting origin:\n\n{str(e)}"
                )
    
    def on_origin_set(self, coordinates):
        """当用户在NIFTI查看器中设置原点时调用"""
        try:
            x, y, z = coordinates
            self.log_widget.append_log(f"New origin set: X={x:.2f}, Y={y:.2f}, Z={z:.2f}", "SUCCESS")
            
            # 可以在这里添加调用MATLAB引擎设置原点的代码
            if self.nifti_viewer and hasattr(self.nifti_viewer, 'image_file'):
                success = self.matlab_engine.set_origin(self.nifti_viewer.image_file, coordinates)
                if success:
                    self.log_widget.append_log("Origin coordinates saved successfully", "SUCCESS")
                else:
                    self.log_widget.append_log("Failed to save origin coordinates", "ERROR")
        except Exception as e:
            self.log_widget.append_log(f"Error processing origin coordinates: {str(e)}", "ERROR")
    
    @pyqtSlot()
    def check_registration(self):
        """Check registration of images using a dialog interface"""
        self.log_widget.append_log("Opening registration check dialog...")
        
        try:
            # Import dialog here to prevent circular imports
            from mispmsrc.ui.check_reg_dialog import CheckRegDialog
            
            dialog = CheckRegDialog(self)
            dialog.setStyleSheet(QApplication.instance().styleSheet())
            
            # Connect the signal from dialog to our handler
            dialog.check_started.connect(self._perform_registration_check)
            
            # Show the dialog
            if dialog.exec_() == QDialog.Rejected:
                self.log_widget.append_log("Registration check cancelled", "INFO")
        except Exception as e:
            self.log_widget.append_log(f"Error opening registration check dialog: {str(e)}", "ERROR")
            import traceback
            self.logger.error(traceback.format_exc())

    def _perform_registration_check(self, file_paths):
        """Execute the actual registration check with the selected files
        
        Args:
            file_paths: List of file paths to check
        """
        try:
            if file_paths:
                self.log_widget.append_log(f"Selected {len(file_paths)} NIFTI files for registration check")
                self.log_widget.append_log(f"Files: {', '.join([os.path.basename(f) for f in file_paths])}")
                
                # Call MATLAB engine to check registration
                self.matlab_engine.check_registration(file_paths)
        except Exception as e:
            self.log_widget.append_log(f"Error checking registration: {str(e)}", "ERROR")
            import traceback
            self.logger.error(traceback.format_exc())
    
    @pyqtSlot()
    def show_cl_analysis_dialog(self):
        """Show CL analysis parameters dialog"""
        try:
            self.log_widget.append_log("Opening CL analysis dialog...")
            
            # Import here to avoid circular imports
            from mispmsrc.ui.cl_analysis_dialog import CLAnalysisDialog
            
            # Initialize dialog with properly configured logger
            dialog = CLAnalysisDialog(self)
            dialog.setStyleSheet(QApplication.instance().styleSheet())
            
            # Connect the signal
            dialog.analysis_started.connect(self.run_cl_analysis)
            
            # Show the dialog
            if dialog.exec_() == QDialog.Accepted:
                self.log_widget.append_log("CL analysis parameters set", "INFO")
            else:
                self.log_widget.append_log("CL analysis canceled", "INFO")
        except Exception as e:
            self.log_widget.append_log(f"Error showing CL analysis dialog: {str(e)}", "ERROR")
            self.logger.error(f"Error in CL analysis dialog: {str(e)}", exc_info=True)
            # Import and use the error dialogs
            from mispmsrc.utils.error_reporter import handle_exception
            handle_exception(e, "Failed to open CL analysis dialog", self, self.logger)
    
    def run_cl_analysis(self, params):
        """Execute CL analysis with the given parameters"""
        self.log_widget.append_log("Starting CL analysis...")
        try:
            # Add progress tracking
            self.progress_manager.start_operation("CL Analysis")
            self.progress_manager.update_progress("Loading mask files...", 10)
            
            # Prepare analyzer object
            from mispmsrc.CLRefactoring.PIB_SUVr_CLs_calc import PIBAnalyzer
            analyzer = PIBAnalyzer()
            
            # Validate input parameters
            for param_name, param_value in params.items():
                if param_name != 'patient_info' and not os.path.exists(param_value):
                    self.log_widget.append_log(f"Error: {param_name} path not found: {param_value}", "ERROR")
                    self.progress_manager.complete_operation(f"Error: {param_name} path not found", False)
                    return
            
            self.progress_manager.update_progress("Analyzing PET images...", 30)
            
            # Run analysis with progress updates using a thread
            from PyQt5.QtCore import QThread, pyqtSignal
            
            class AnalysisThread(QThread):
                finished = pyqtSignal(bool, str)
                progress = pyqtSignal(str, int)
                
                def __init__(self, analyzer, params):
                    super().__init__()
                    self.analyzer = analyzer
                    self.params = params
                    self.exception = None
                
                def run(self):
                    try:
                        # Setup log capture for progress updates
                        import logging
                        class ProgressHandler(logging.Handler):
                            def __init__(self, progress_signal):
                                super().__init__()
                                self.progress_signal = progress_signal
                                self.steps = {
                                    'mask': 30,
                                    'suvr': 40,
                                    'cl': 60,
                                    'standard': 70,
                                    'correlation': 80,
                                    'report': 90
                                }
                                
                            def emit(self, record):
                                msg = self.format(record)
                                progress = None
                                
                                # Determine progress percentage based on message content
                                for key, value in self.steps.items():
                                    if key in msg.lower():
                                        progress = value
                                        break
                                
                                if progress:
                                    self.progress_signal.emit(msg, progress)
                        
                        # Add our handler to the logger
                        handler = ProgressHandler(self.progress)
                        handler.setLevel(logging.INFO)
                        logging.getLogger().addHandler(handler)
                        
                        # Run the analysis
                        result = self.analyzer.run_analysis(
                            self.params['ref_path'],
                            self.params['roi_path'],
                            self.params['ad_dir'],
                            self.params['yc_dir'],
                            self.params['standard_data'],
                            self.params.get('patient_info')
                        )
                        
                        # Remove our custom handler
                        logging.getLogger().removeHandler(handler)
                        
                        # Get output directory for finding reports
                        output_dir = self.analyzer.plotter.output_dir
                        self.finished.emit(result, output_dir)
                        
                    except Exception as e:
                        import traceback
                        self.exception = (str(e), traceback.format_exc())
                        self.finished.emit(False, "")
                        # Remove our custom handler in case of error
                        try:
                            logging.getLogger().removeHandler(handler)
                        except:
                            pass
            
            # Create and connect thread
            self.analysis_thread = AnalysisThread(analyzer, params)
            self.analysis_thread.progress.connect(self.progress_manager.update_progress)
            self.analysis_thread.finished.connect(self._on_analysis_finished)
            
            # Start thread
            self.analysis_thread.start()
            
        except Exception as e:
            self.log_widget.append_log(f"Error in CL analysis: {str(e)}", "ERROR")
            self.progress_manager.complete_operation("CL Analysis failed", False)
            import traceback
            self.logger.error(traceback.format_exc())
    
    def _on_analysis_finished(self, success, output_dir):
        """Handle analysis thread completion"""
        if success:
            self.log_widget.append_log("CL analysis completed successfully", "SUCCESS")
            self.progress_manager.complete_operation("CL Analysis completed", True)
            
            # Get the report files
            report_files = self._get_latest_report_files(output_dir)
            
            if report_files:
                self.log_widget.append_log(f"Generated {len(report_files)} report files", "SUCCESS")
                
                # Optional: Give the UI time to update before displaying files
                from PyQt5.QtCore import QTimer
                QTimer.singleShot(500, lambda: self._display_report_files(report_files))
            else:
                self.log_widget.append_log("No report files were generated", "WARNING")
        else:
            # Check if we have exception details
            if hasattr(self.analysis_thread, 'exception') and self.analysis_thread.exception:
                error_msg, traceback_text = self.analysis_thread.exception
                self.log_widget.append_log(f"Error in CL analysis: {error_msg}", "ERROR")
                self.logger.error(traceback_text)
            else:
                self.log_widget.append_log("CL analysis failed", "ERROR")
            self.progress_manager.complete_operation("CL Analysis failed", False)

    def _get_latest_report_files(self, output_dir):
        """Get the latest report files generated in the output directory
        
        Returns:
            list: Paths to the latest report files
        """
        import glob
        import time
        
        if not output_dir or not os.path.exists(output_dir):
            self.log_widget.append_log(f"Output directory not found: {output_dir}", "ERROR")
            return []
        
        self.log_widget.append_log(f"Searching for report files in {output_dir}...", "INFO")
        
        # Get all output files with recognized extensions in the output directory
        all_files = []
        for ext in ['*.pdf', '*.png', '*.jpg', '*.svg']:
            all_files.extend(glob.glob(os.path.join(output_dir, ext)))
            
        if not all_files:
            self.log_widget.append_log("No report files found in output directory", "WARNING")
            return []
        
        # Filter files generated in the last minute (assuming reports were just created)
        current_time = time.time()
        recent_files = [f for f in all_files if os.path.getmtime(f) > current_time - 60]
        
        # Sort by modification time (newest first)
        recent_files.sort(key=os.path.getmtime, reverse=True)
        
        if recent_files:
            self.log_widget.append_log(f"Found {len(recent_files)} recent report files", "INFO")
            for f in recent_files[:5]:  # Log first 5 files
                ext = os.path.splitext(f)[1].lower()
                file_size = os.path.getsize(f)
                self.log_widget.append_log(f"  {os.path.basename(f)} ({ext}, {file_size} bytes)", "INFO")
        else:
            # If no recent files found, return oldest files as fallback
            self.log_widget.append_log("No recent report files found, using oldest files as fallback", "WARNING")
            all_files.sort(key=os.path.getmtime)  # Sort by time (oldest first)
            recent_files = all_files[:5]  # Take up to 5 oldest files
        
        # Return up to 5 most recent files
        return recent_files[:5]

    def _display_report_files(self, file_paths):
        """Display the report files using the system's default viewer
        
        Args:
            file_paths: List of paths to report files
        """
        if not file_paths:
            self.log_widget.append_log("No report files to display", "WARNING")
            return
            
        self.log_widget.append_log(f"Opening report files...", "SUCCESS")
        
        # Choose which file to open - prefer summary report if available
        files_to_open = []
        summary_file = next((f for f in file_paths if 'summary' in f.lower() or 'report' in f.lower()), None)
        if summary_file:
            self.log_widget.append_log(f"Found summary report: {os.path.basename(summary_file)}", "INFO")
            # Add summary report first
            files_to_open.append(summary_file)
            # Add other reports (up to 2 more)
            files_to_open.extend([f for f in file_paths[:2] if f != summary_file])
        else:
            # Just use the first 3 files
            self.log_widget.append_log("No summary report found, using available files", "INFO")
            files_to_open = file_paths[:3]
        
        # Open files with system viewer
        for file_path in files_to_open:
            try:
                # Check if file exists and has non-zero size
                if not os.path.exists(file_path):
                    self.log_widget.append_log(f"File not found: {file_path}", "ERROR")
                    continue
                if os.path.getsize(file_path) == 0:
                    self.log_widget.append_log(f"Empty file: {file_path}", "ERROR")
                    continue
                    
                ext = os.path.splitext(file_path)[1].lower()
                file_size = os.path.getsize(file_path)
                self.log_widget.append_log(f"Opening file: {os.path.basename(file_path)} ({ext} format, {file_size} bytes)", "INFO")
                
                # Use platform-specific methods to open file
                if sys.platform == 'win32':
                    os.startfile(file_path)
                elif sys.platform == 'darwin':  # macOS
                    os.system(f'open "{file_path}"')
                else:  # Linux
                    os.system(f'xdg-open "{file_path}"')
            except Exception as e:
                self.log_widget.append_log(f"Error opening file: {str(e)}", "ERROR")
        
        # Inform user about report location
        if file_paths:
            report_dir = os.path.dirname(file_paths[0])
            self.log_widget.append_log(f"All reports saved in: {report_dir}", "SUCCESS")
            
            # Determine report format from files
            formats = set(os.path.splitext(f)[1].lower() for f in file_paths)
            format_str = ", ".join(f.replace('.', '').upper() for f in formats)
            self.log_widget.append_log(f"Report format(s): {format_str}", "INFO")
    
    @pyqtSlot()
    def convert_to_nifti(self):
        """Convert DICOM to NIFTI with improved error handling and progress feedback"""
        try:
            # Select DICOM directory
            dicom_dir = QFileDialog.getExistingDirectory(
                self, 
                "Select DICOM Directory",
                "",
                QFileDialog.ShowDirsOnly
            )
            if not dicom_dir:
                return

            # Select output directory
            output_dir = QFileDialog.getExistingDirectory(
                self, 
                "Select Output Directory",
                "",
                QFileDialog.ShowDirsOnly
            )
            if not output_dir:
                return
            
            # Log the selected directories
            self.log_widget.append_log(f"Selected DICOM directory: {dicom_dir}")
            self.log_widget.append_log(f"Selected output directory: {output_dir}")

            # Show progress
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            QApplication.processEvents()  # Allow GUI update

            # Convert files
            result_files = self.matlab_engine.convert_to_nifti(dicom_dir, output_dir)

            # Check results
            if result_files:
                self.log_widget.append_log(
                    f"Successfully created {len(result_files)} NIFTI files:",
                    "SUCCESS"
                )
                for f in result_files:
                    self.log_widget.append_log(f"  {f}")
            else:
                self.log_widget.append_log(
                    "No NIFTI files were created. Check the DICOM files and try again.",
                    "ERROR"
                )

        except Exception as e:
            self.log_widget.append_log(f"Error during conversion: {str(e)}", "ERROR")
            self.progress_bar.setVisible(False)
        finally:
            self.progress_bar.setVisible(False)
            QApplication.processEvents()
    
    @pyqtSlot()
    def batch_coregister_images(self):
        """Batch coregister multiple images"""
        self.log_widget.append_log("Batch coregistering images...")
        
        # Select reference image
        ref_image, _ = QFileDialog.getOpenFileName(self, "Select Reference Image", "", "NIFTI Files (*.nii *.nii.gz)")
        if not ref_image:
            return
            
        # Select source image directory
        source_dir = QFileDialog.getExistingDirectory(self, "Select Directory with Source Images")
        if not source_dir:
            return
            
        # Get all NIFTI files in the directory
        source_files = []
        for ext in ['*.nii', '*.nii.gz']:
            source_files.extend(glob.glob(os.path.join(source_dir, ext)))
            
        if not source_files:
            self.log_widget.append_log("No NIFTI files found in selected directory", "WARNING")
            return
            
        self.log_widget.append_log(f"Found {len(source_files)} NIFTI files to coregister")
        self.log_widget.append_log(f"Reference image: {ref_image}")
        
        # Select cost function for coregistration
        cost_function = self._select_cost_function()
        
        # Execute batch coregistration
        try:
            self.progress_manager.start_operation("Batch Coregistration")
            results = self.matlab_engine.batch_coregister_images(ref_image, source_files, cost_function)
            
            # Display results
            self.log_widget.append_log(f"Coregistration completed: {results['success']}/{results['total']} successful", 
                                      "SUCCESS" if results['failed'] == 0 else "WARNING")
            
            if results['failed'] > 0:
                self.log_widget.append_log(f"Failed to coregister {results['failed']} files:", "WARNING")
                for failed_file in results['failed_files']:
                    self.log_widget.append_log(f"  - {os.path.basename(failed_file)}", "WARNING")
            
            self.progress_manager.complete_operation(
                f"Batch coregistration completed: {results['success']}/{results['total']} successful",
                results['failed'] == 0
            )
        except Exception as e:
            self.log_widget.append_log(f"Error during batch coregistration: {str(e)}", "ERROR")
            self.progress_manager.complete_operation("Batch coregistration failed", False)
    
    def _select_cost_function(self):
        """Select cost function for coregistration"""
        options = ["Mutual Information", "Normalised Mutual Information", 
                   "Entropy Correlation Coefficient", "Normalised Cross Correlation"]
        cost_function, ok = QInputDialog.getItem(
            self, "Select Cost Function", "Cost Function:", options, 1, False
        )
        if ok and cost_function:
            return cost_function.lower().replace(' ', '_')
        return "nmi"  # Default to normalised mutual information

    @pyqtSlot()
    def batch_normalise_images(self):
        """Batch normalize multiple images to a template"""
        self.log_widget.append_log("Batch normalizing images...")
        
        # Select template image
        template_path, _ = QFileDialog.getOpenFileName(self, "Select Template Image", "", "NIFTI Files (*.nii *.nii.gz)")
        if not template_path:
            return
            
        # Select source image directory
        source_dir = QFileDialog.getExistingDirectory(self, "Select Directory with Source Images")
        if not source_dir:
            return
            
        # Get all NIFTI files in the directory - focusing on coregistered files ('r' prefix)
        source_files = []
        for ext in ['r*.nii', 'r*.nii.gz']:
            source_files.extend(glob.glob(os.path.join(source_dir, ext)))
            
        if not source_files:
            self.log_widget.append_log("No coregistered NIFTI files (with 'r' prefix) found in selected directory", "WARNING")
            return
            
        self.log_widget.append_log(f"Found {len(source_files)} NIFTI files to normalize")
        self.log_widget.append_log(f"Template image: {template_path}")
        
        # Set parameters for normalization
        params = {
            'template_path': template_path,
            'source_smoothing': 8,
            'template_smoothing': 0,
            'nonlinear_cutoff': 25,
            'nonlinear_iterations': 16,
            'nonlinear_reg': 1,
            'preserve': 0,
            'prefix': 'w'
        }
        
        # Execute batch normalization
        try:
            self.progress_manager.start_operation("Batch Normalization")
            
            # Process each file separately since normalization requires specific parameters per file
            success_count = 0
            error_count = 0
            
            for i, source_file in enumerate(source_files):
                try:
                    # Update parameters for this file
                    current_params = params.copy()
                    current_params['source_image'] = source_file
                    
                    self.log_widget.append_log(f"Normalizing {i+1}/{len(source_files)}: {os.path.basename(source_file)}")
                    self.progress_manager.update_progress(f"Normalizing {os.path.basename(source_file)}", 
                                                        int((i / len(source_files)) * 100))
                    
                    # Execute normalization
                    success = self.matlab_engine.normalize_image(current_params)
                    
                    if success:
                        success_count += 1
                    else:
                        error_count += 1
                        self.log_widget.append_log(f"Failed to normalize {source_file}", "ERROR")
                except Exception as e:
                    error_count += 1
                    self.log_widget.append_log(f"Error normalizing {source_file}: {str(e)}", "ERROR")
            
            # Complete operation
            self.progress_manager.complete_operation(
                f"Batch normalization completed: {success_count}/{len(source_files)} successful", 
                error_count == 0
            )
        except Exception as e:
            self.log_widget.append_log(f"Error during batch normalization: {str(e)}", "ERROR")
            self.progress_manager.complete_operation("Batch normalization failed", False)

    @pyqtSlot()
    def batch_set_origin(self):
        """Batch set origin for multiple images"""
        self.log_widget.append_log("Batch setting image origins...")
        
        # Select image directory
        image_dir = QFileDialog.getExistingDirectory(self, "Select Directory with Images")
        if not image_dir:
            return
            
        # Get all NIFTI files in the directory
        image_files = []
        for ext in ['*.nii', '*.nii.gz']:
            image_files.extend(glob.glob(os.path.join(image_dir, ext)))
            
        if not image_files:
            self.log_widget.append_log("No NIFTI files found in selected directory", "WARNING")
            return
            
        self.log_widget.append_log(f"Found {len(image_files)} NIFTI files to process")
        
        # Get origin coordinates
        coordinates = self._get_origin_coordinates()
        if not coordinates:
            return
            
        # Process files
        try:
            self.progress_manager.start_operation("Batch Set Origin")
            
            success_count = 0
            error_count = 0
            
            for i, image_file in enumerate(image_files):
                try:
                    self.log_widget.append_log(f"Setting origin {i+1}/{len(image_files)}: {os.path.basename(image_file)}")
                    self.progress_manager.update_progress(f"Setting origin for {os.path.basename(image_file)}", 
                                                        int((i / len(image_files)) * 100))
                    
                    # Call set_origin method
                    success = self.matlab_engine.set_origin(image_file, coordinates)
                    
                    if success:
                        success_count += 1
                    else:
                        error_count += 1
                        self.log_widget.append_log(f"Failed to set origin for {image_file}", "ERROR")
                except Exception as e:
                    error_count += 1
                    self.log_widget.append_log(f"Error setting origin for {image_file}: {str(e)}", "ERROR")
            
            # Complete operation
            self.progress_manager.complete_operation(
                f"Batch origin setting completed: {success_count}/{len(image_files)} successful", 
                error_count == 0
            )
        except Exception as e:
            self.log_widget.append_log(f"Error during batch origin setting: {str(e)}", "ERROR")
            self.progress_manager.complete_operation("Batch origin setting failed", False)

    def _get_origin_coordinates(self):
        """Get origin coordinates from user"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Set Origin Coordinates")
        dialog.setStyleSheet(QApplication.instance().styleSheet())
        layout = QVBoxLayout(dialog)
        
        # Add coordinate inputs
        coord_layout = QGridLayout()
        coord_layout.addWidget(QLabel("X:"), 0, 0)
        coord_layout.addWidget(QLabel("Y:"), 1, 0)
        coord_layout.addWidget(QLabel("Z:"), 2, 0)
        
        x_spin = QDoubleSpinBox()
        y_spin = QDoubleSpinBox()
        z_spin = QDoubleSpinBox()
        
        for spin in [x_spin, y_spin, z_spin]:
            spin.setRange(-1000, 1000)
            spin.setValue(0)
            spin.setDecimals(1)
            spin.setSingleStep(1)
        
        coord_layout.addWidget(x_spin, 0, 1)
        coord_layout.addWidget(y_spin, 1, 1)
        coord_layout.addWidget(z_spin, 2, 1)
        
        layout.addLayout(coord_layout)
        
        # Add buttons
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        
        ok_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)
        
        layout.addLayout(btn_layout)
        
        # Execute dialog
        if dialog.exec_():
            return [x_spin.value(), y_spin.value(), z_spin.value()]
        return None

    @pyqtSlot()
    def coregister_images(self):
        """Coregister images using SPM"""
        self.log_widget.append_log("Opening coregistration dialog...")
        
        # Create and show the coregistration dialog
        try:
            # Import dialog here to prevent circular imports
            from mispmsrc.ui.coreg_dialog import CoregisterDialog
            
            dialog = CoregisterDialog(self)
            dialog.setStyleSheet(QApplication.instance().styleSheet())
            
            # Show the dialog and handle the result
            if dialog.exec_():
                # Get the parameters from the dialog
                params = dialog.get_parameters()
                
                # Double-check if parameters are valid
                if not params.get('reference') or not params.get('source'):
                    self.log_widget.append_log("Reference or source image not selected", "ERROR")
                    QMessageBox.warning(
                        self, 
                        "Missing Parameters", 
                        "Reference and source images are required for coregistration."
                    )
                    return
                    
                # Show progress information
                self.log_widget.append_log(f"Coregistering {os.path.basename(params['source'])} to "
                                         f"{os.path.basename(params['reference'])}")
                
                # Call the MATLAB engine to perform coregistration
                self.progress_manager.start_operation("Coregistration")
                self.progress_manager.update_progress("Setting up coregistration...", 10)
                
                success = self.matlab_engine.coregister_images(
                    params['reference'], 
                    params['source'],
                    params.get('cost_function', 'nmi')
                )
                
                if success:
                    self.log_widget.append_log("Coregistration completed successfully", "SUCCESS")
                    self.progress_manager.complete_operation("Coregistration completed successfully", True)
                else:
                    self.log_widget.append_log("Coregistration failed", "ERROR")
                    self.progress_manager.complete_operation("Coregistration failed", False)
                    
            else:
                self.log_widget.append_log("Coregistration cancelled", "INFO")
                
        except Exception as e:
            self.log_widget.append_log(f"Error in coregistration: {str(e)}", "ERROR")
            import traceback
            self.logger.error(traceback.format_exc())

    @pyqtSlot()
    def normalise_image(self):
        """Normalize an image to a template using SPM"""
        self.log_widget.append_log("Opening normalization dialog...")
        
        try:
            # Import dialog here to prevent circular imports
            from mispmsrc.ui.normalize_dialog import NormalizeDialog
            
            dialog = NormalizeDialog(self)
            dialog.setStyleSheet(QApplication.instance().styleSheet())
            
            # Show the dialog and handle the result
            if dialog.exec_():
                # Get the parameters from the dialog
                params = dialog.get_parameters()
                
                # Check if parameters are valid
                if not params.get('source_image') or not params.get('template_path'):
                    self.log_widget.append_log("Source image or template not selected", "ERROR")
                    return
                    
                # Show progress information
                self.log_widget.append_log(f"Normalizing {os.path.basename(params['source_image'])} to "
                                        f"{os.path.basename(params['template_path'])}")
                
                # Call the MATLAB engine to perform normalization
                success = self.matlab_engine.normalize_image(params)
                
                if success:
                    self.log_widget.append_log("Normalization completed successfully", "SUCCESS")
                    
                    # Show the output file information
                    output_dir = os.path.dirname(params['source_image'])
                    prefix = params.get('prefix', 'w')
                    source_name = os.path.basename(params['source_image'])
                    output_path = os.path.join(output_dir, f"{prefix}{source_name}")
                    
                    if os.path.exists(output_path):
                        self.log_widget.append_log(f"Created normalized file: {output_path}", "SUCCESS")
                    
                else:
                    self.log_widget.append_log("Normalization failed", "ERROR")
                    
            else:
                self.log_widget.append_log("Normalization cancelled", "INFO")
                
        except Exception as e:
            self.log_widget.append_log(f"Error in normalization: {str(e)}", "ERROR")
            import traceback
            self.logger.error(traceback.format_exc())

if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # 保留 Fusion 风格，只改变颜色
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Start event loop
    sys.exit(app.exec_())