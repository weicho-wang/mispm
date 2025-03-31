#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QAbstractItemView, QFileDialog, QGroupBox
)
from PyQt5.QtCore import Qt, pyqtSignal

class CheckRegDialog(QDialog):
    """检查配准对话框，用于选择要检查的图像"""
    
    check_started = pyqtSignal(list)  # 发送图像路径列表的信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Check Registration")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 说明标签
        info_label = QLabel(
            "Select two or more image files to check their registration.\n"
            "The images will be displayed as overlays for visual inspection."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # 图像列表组
        image_group = QGroupBox("Selected Images")
        image_layout = QVBoxLayout()
        
        # 图像列表
        self.image_list = QListWidget()
        self.image_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        image_layout.addWidget(self.image_list)
        
        # 图像列表按钮
        list_btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Add Images...")
        self.remove_btn = QPushButton("Remove Selected")
        self.clear_btn = QPushButton("Clear All")
        
        self.add_btn.clicked.connect(self.add_images)
        self.remove_btn.clicked.connect(self.remove_images)
        self.clear_btn.clicked.connect(self.clear_images)
        
        list_btn_layout.addWidget(self.add_btn)
        list_btn_layout.addWidget(self.remove_btn)
        list_btn_layout.addWidget(self.clear_btn)
        image_layout.addLayout(list_btn_layout)
        
        image_group.setLayout(image_layout)
        layout.addWidget(image_group)
        
        # 选项组
        options_group = QGroupBox("Display Options")
        options_layout = QVBoxLayout()
        
        # 这里可以添加更多选项，如显示模式、颜色方案等
        options_help = QLabel(
            "Images will be displayed using SPM's orthogonal viewer.\n"
            "You can navigate through slices using SPM's interface."
        )
        options_help.setWordWrap(True)
        options_layout.addWidget(options_help)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # 按钮组
        button_layout = QHBoxLayout()
        self.check_btn = QPushButton("Check Registration")
        self.check_btn.setEnabled(False)  # 初始禁用，直到选择了至少两个图像
        self.cancel_btn = QPushButton("Cancel")
        
        self.check_btn.clicked.connect(self.check_registration)
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.check_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)
        
        # 连接图像列表变化信号
        self.image_list.model().rowsInserted.connect(self.update_button_state)
        self.image_list.model().rowsRemoved.connect(self.update_button_state)
    
    def add_images(self):
        """添加图像到列表"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, 
            "Select Images for Registration Check",
            "",
            "NIFTI Files (*.nii *.nii.gz);;All Files (*.*)"
        )
        
        if file_paths:
            for path in file_paths:
                # 检查是否已存在于列表中
                exists = False
                for i in range(self.image_list.count()):
                    if self.image_list.item(i).data(Qt.UserRole) == path:
                        exists = True
                        break
                
                if not exists:
                    item = QLabel(os.path.basename(path))
                    item.setToolTip(path)
                    self.image_list.addItem(os.path.basename(path))
                    # 存储完整路径作为用户数据
                    self.image_list.item(self.image_list.count() - 1).setData(Qt.UserRole, path)
    
    def remove_images(self):
        """从列表中移除选中的图像"""
        selected_items = self.image_list.selectedItems()
        for item in selected_items:
            self.image_list.takeItem(self.image_list.row(item))
    
    def clear_images(self):
        """清空图像列表"""
        self.image_list.clear()
    
    def update_button_state(self):
        """更新按钮状态"""
        self.check_btn.setEnabled(self.image_list.count() >= 2)
    
    def check_registration(self):
        """执行检查配准操作"""
        # 收集图像路径
        file_paths = []
        for i in range(self.image_list.count()):
            file_paths.append(self.image_list.item(i).data(Qt.UserRole))
        
        if len(file_paths) >= 2:
            # 发送信号并关闭对话框
            self.check_started.emit(file_paths)
            self.accept()
