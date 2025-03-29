"""
Thread utility functions for MISPM application
"""

import threading
import logging
import matplotlib
import sys
from PyQt5.QtCore import QObject, pyqtSignal, QThread

logger = logging.getLogger(__name__)

def configure_matplotlib_for_threading():
    """Configure matplotlib based on current thread"""
    if threading.current_thread() is not threading.main_thread():
        logger.info("Using non-interactive matplotlib backend for non-main thread")
        matplotlib.use('Agg')  # Use non-interactive backend
    else:
        # In main thread, use an interactive backend that works with Qt
        logger.info("Using Qt5Agg matplotlib backend for main thread")
        matplotlib.use('Qt5Agg')
        
class WorkerSignals(QObject):
    """Defines the signals available from a running worker thread"""
    started = pyqtSignal()
    finished = pyqtSignal()
    error = pyqtSignal(str, str)  # error message, traceback
    result = pyqtSignal(object)
    progress = pyqtSignal(str, int)  # message, percent

class Worker(QThread):
    """
    Worker thread for executing long-running tasks
    
    Attributes:
        signals (WorkerSignals): Signal emitter for communication
        
    Usage:
        worker = Worker(long_running_function, *args, **kwargs)
        worker.signals.result.connect(handle_result)
        worker.signals.finished.connect(cleanup)
        worker.start()
    """
    
    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        self.exception = None
    
    def run(self):
        """Execute the function in a separate thread"""
        try:
            # Emit started signal
            self.signals.started.emit()
            
            # Configure matplotlib for thread
            configure_matplotlib_for_threading()
            
            # Execute function
            result = self.fn(*self.args, **self.kwargs)
            
            # Return result
            self.signals.result.emit(result)
            
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            self.exception = (str(e), tb)
            self.signals.error.emit(str(e), tb)
            
        finally:
            # Always emit finished signal
            self.signals.finished.emit()
