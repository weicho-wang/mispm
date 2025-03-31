#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
NIFTI查看器独立程序

这个脚本提供了一个简单的NIFTI查看器，可以单独运行，
帮助用户快速测试和查看NIFTI文件，而不依赖MATLAB。

用法:
python scripts/view_nifti.py [nifti文件路径]
"""

import os
import sys
import argparse

# 添加项目根目录到路径
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

# 尝试导入必要的库
try:
    import numpy as np
    import nibabel as nib
    from PyQt5.QtWidgets import QApplication, QFileDialog, QMessageBox
    from PyQt5.QtCore import Qt
    from mispmsrc.ui.nifti_viewer import NiftiViewer
except ImportError as e:
    print(f"错误: 缺少必要的库: {e}")
    print("请确保已安装所有依赖库: pip install -r requirements.txt")
    sys.exit(1)

def view_nifti(file_path=None):
    """打开并查看NIFTI文件"""
    app = QApplication([])
    
    # 设置黑色主题样式
    dark_style = """
    QMainWindow, QDialog {
        background-color: #2D2D30;
        color: #CCCCCC;
    }
    QWidget {
        background-color: #2D2D30;
        color: #CCCCCC;
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
    QLabel {
        color: #CCCCCC;
    }
    QSlider {
        background-color: #2D2D30;
    }
    QGroupBox {
        border: 1px solid #3F3F46;
        color: #CCCCCC;
    }
    QSpinBox, QDoubleSpinBox {
        background-color: #1E1E1E;
        color: #CCCCCC;
        border: 1px solid #3F3F46;
    }
    """
    app.setStyleSheet(dark_style)
    
    # 如果没有提供文件路径，则打开文件选择对话框
    if not file_path:
        file_path, _ = QFileDialog.getOpenFileName(
            None, 
            "选择NIFTI文件", 
            "", 
            "NIFTI文件 (*.nii *.nii.gz)"
        )
        
    if not file_path:
        print("未选择文件")
        return 1
    
    print(f"打开文件: {file_path}")
    
    try:
        # 创建查看器
        print("创建NIFTI查看器...")
        viewer = NiftiViewer()
        viewer.setWindowFlags(viewer.windowFlags() | Qt.Window)
        
        # 尝试加载NIFTI文件
        print(f"尝试加载NIFTI文件: {file_path}")
        if viewer.load_nifti(file_path):
            print("NIFTI文件加载成功，显示查看器...")
            viewer.show()
            return app.exec_()
        else:
            print("无法加载NIFTI文件")
            QMessageBox.critical(None, "错误", f"无法加载NIFTI文件: {file_path}")
            return 1
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"查看NIFTI文件时出错: {str(e)}")
        print(error_details)
        QMessageBox.critical(None, "错误", f"查看NIFTI文件时出错:\n{str(e)}")
        return 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NIFTI文件查看器")
    parser.add_argument("file_path", nargs="?", help="要查看的NIFTI文件路径")
    args = parser.parse_args()
    
    sys.exit(view_nifti(args.file_path))
