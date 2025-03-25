from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QProgressBar, QStatusBar

class ProgressManager(QObject):
    """管理窗口进度条的类"""
    
    progress_updated = pyqtSignal(str, int)  # 消息, 进度值
    progress_started = pyqtSignal(str)  # 开始消息
    progress_completed = pyqtSignal(str, bool)  # 完成消息, 是否成功
    
    def __init__(self, progress_bar: QProgressBar, status_bar: QStatusBar):
        super().__init__()
        self._progress_bar = progress_bar
        self._status_bar = status_bar
        self._current_operation = ""
        
        # 连接信号
        self.progress_updated.connect(self._on_progress_updated)
        self.progress_started.connect(self._on_progress_started)
        self.progress_completed.connect(self._on_progress_completed)
        
    def start_operation(self, operation_name: str):
        """开始一个操作"""
        self._current_operation = operation_name
        self._progress_bar.setVisible(True)
        self._progress_bar.setValue(0)
        self.progress_started.emit(operation_name)
    
    def update_progress(self, message: str, value: int):
        """更新进度"""
        self.progress_updated.emit(message, value)
    
    def complete_operation(self, message: str, success: bool):
        """完成操作"""
        self.progress_completed.emit(message, success)
    
    @pyqtSlot(str)
    def _on_progress_started(self, message: str):
        """处理操作开始信号"""
        self._status_bar.showMessage(f"Starting: {message}")
    
    @pyqtSlot(str, int)
    def _on_progress_updated(self, message: str, value: int):
        """处理进度更新信号"""
        self._progress_bar.setValue(value)
        self._status_bar.showMessage(message)
    
    @pyqtSlot(str, bool)
    def _on_progress_completed(self, message: str, success: bool):
        """处理操作完成信号"""
        self._progress_bar.setValue(100 if success else 0)
        self._progress_bar.setVisible(False)
        self._status_bar.showMessage(message, 5000)  # 显示5秒
        self._current_operation = ""

    def get_operation_steps(self, operation_type: str) -> dict:
        """获取操作的进度步骤定义"""
        steps = {
            'matlab_start': {
                'init': ("Initializing MATLAB engine...", 0),  # Changed order: (message, value)
                'loading': ("Loading MATLAB...", 20),
                'spm_init': ("Initializing SPM...", 40),
                'config': ("Configuring environment...", 60),
                'ready': ("Almost ready...", 80),
                'complete': ("MATLAB engine started", 100)
            },
            'coregister': {
                'init': ("Opening SPM Coregistration...", 0),
                'complete': ("SPM Coregistration window ready", 100)
            },
            'normalize': {
                'init': ("Initializing normalization...", 0),
                'load_source': ("Loading source image...", 20),
                'load_template': ("Loading template...", 40),
                'estimate': ("Estimating parameters...", 60),
                'write': ("Writing normalized image...", 80),
                'complete': ("Normalization complete", 100)
            },
            'dicom_convert': {
                'init': ("Initializing DICOM conversion...", 0),
                'scanning': ("Scanning DICOM files...", 20),
                'reading': ("Reading DICOM headers...", 40),
                'converting': ("Converting to NIFTI...", 60),
                'saving': ("Saving NIFTI files...", 80),
                'complete': ("Conversion complete", 100)
            }
        }
        return steps.get(operation_type, {})
