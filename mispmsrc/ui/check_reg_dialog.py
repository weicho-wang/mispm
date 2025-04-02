#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QAbstractItemView, QFileDialog, QGroupBox
)
from PyQt5.QtCore import Qt, pyqtSignal

class CheckRegDialog(QDialog):
    """check registration dialog used to select images"""
    
    check_started = pyqtSignal(list)  # send signal of image paths list
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Check Registration")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # prompt label
        info_label = QLabel(
            "Select two or more image files to check their registration.\n"
            "The images will be displayed as overlays for visual inspection."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # image list group
        image_group = QGroupBox("Selected Images")
        image_layout = QVBoxLayout()
        
        # image list widget
        self.image_list = QListWidget()
        self.image_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        image_layout.addWidget(self.image_list)
        
        # image list buttons
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
        
        # options group
        options_group = QGroupBox("Display Options")
        options_layout = QVBoxLayout()
        
        # add more options here such as display mode, color scheme, etc.
        options_help = QLabel(
            "Images will be displayed using SPM's orthogonal viewer.\n"
            "You can navigate through slices using SPM's interface."
        )
        options_help.setWordWrap(True)
        options_layout.addWidget(options_help)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # buttons at the bottom
        button_layout = QHBoxLayout()
        self.check_btn = QPushButton("Check Registration")
        self.check_btn.setEnabled(False)  # not enabled untile at least two images are selected
        self.cancel_btn = QPushButton("Cancel")
        
        self.check_btn.clicked.connect(self.check_registration)
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.check_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)
        
        # connected to update button state
        self.image_list.model().rowsInserted.connect(self.update_button_state)
        self.image_list.model().rowsRemoved.connect(self.update_button_state)
    
    def add_images(self):
        """add images to the list"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, 
            "Select Images for Registration Check",
            "",
            "NIFTI Files (*.nii *.nii.gz);;All Files (*.*)"
        )
        
        if file_paths:
            for path in file_paths:
                # check whether the image is already in the list
                exists = False
                for i in range(self.image_list.count()):
                    if self.image_list.item(i).data(Qt.UserRole) == path:
                        exists = True
                        break
                
                if not exists:
                    item = QLabel(os.path.basename(path))
                    item.setToolTip(path)
                    self.image_list.addItem(os.path.basename(path))
                    # store the full path as user data
                    self.image_list.item(self.image_list.count() - 1).setData(Qt.UserRole, path)
    
    def remove_images(self):
        """remove selected images from the list"""
        selected_items = self.image_list.selectedItems()
        for item in selected_items:
            self.image_list.takeItem(self.image_list.row(item))
    
    def clear_images(self):
        """clear image list"""
        self.image_list.clear()
    
    def update_button_state(self):
        """update button state"""
        self.check_btn.setEnabled(self.image_list.count() >= 2)
    
    def check_registration(self):
        """ perform registration check"""
        # collect image paths
        file_paths = []
        for i in range(self.image_list.count()):
            file_paths.append(self.image_list.item(i).data(Qt.UserRole))
        
        if len(file_paths) >= 2:
            # send signal and close dialog
            self.check_started.emit(file_paths)
            self.accept()
