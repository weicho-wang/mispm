#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
NIFTI方向调试工具

这个脚本帮助诊断和解决NIFTI文件的方向和坐标系问题。
它可以可视化NIFTI文件的坐标轴，并帮助确定正确的视图映射。

用法:
python scripts/debug_nifti_orientation.py <nifti_file_path>
"""

import os
import sys
import argparse
import numpy as np
import nibabel as nib
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button

def analyze_affine(affine):
    """分析仿射矩阵，解释坐标系和排列方向"""
    # 提取旋转缩放部分
    rotation_scale = affine[:3, :3]
    translation = affine[:3, 3]
    
    # 获取每个轴的方向向量
    x_dir = rotation_scale[:, 0]
    y_dir = rotation_scale[:, 1]
    z_dir = rotation_scale[:, 2]
    
    # 计算每个轴的范数（尺度）
    x_scale = np.linalg.norm(x_dir)
    y_scale = np.linalg.norm(y_dir)
    z_scale = np.linalg.norm(z_dir)
    
    # 归一化方向向量
    x_norm = x_dir / x_scale if x_scale != 0 else x_dir
    y_norm = y_dir / y_scale if y_scale != 0 else y_dir
    z_norm = z_dir / z_scale if z_scale != 0 else z_dir
    
    # 判断坐标系方向
    coord_types = {'x': '', 'y': '', 'z': ''}
    
    # 检查x轴
    if abs(x_norm[0]) > abs(x_norm[1]) and abs(x_norm[0]) > abs(x_norm[2]):
        coord_types['x'] = 'Right' if x_norm[0] > 0 else 'Left'
    elif abs(x_norm[1]) > abs(x_norm[0]) and abs(x_norm[1]) > abs(x_norm[2]):
        coord_types['x'] = 'Anterior' if x_norm[1] > 0 else 'Posterior'
    else:
        coord_types['x'] = 'Superior' if x_norm[2] > 0 else 'Inferior'
    
    # 检查y轴
    if abs(y_norm[0]) > abs(y_norm[1]) and abs(y_norm[0]) > abs(y_norm[2]):
        coord_types['y'] = 'Right' if y_norm[0] > 0 else 'Left'
    elif abs(y_norm[1]) > abs(y_norm[0]) and abs(y_norm[1]) > abs(y_norm[2]):
        coord_types['y'] = 'Anterior' if y_norm[1] > 0 else 'Posterior'
    else:
        coord_types['y'] = 'Superior' if y_norm[2] > 0 else 'Inferior'
    
    # 检查z轴
    if abs(z_norm[0]) > abs(z_norm[1]) and abs(z_norm[0]) > abs(z_norm[2]):
        coord_types['z'] = 'Right' if z_norm[0] > 0 else 'Left'
    elif abs(z_norm[1]) > abs(z_norm[0]) and abs(z_norm[1]) > abs(z_norm[2]):
        coord_types['z'] = 'Anterior' if z_norm[1] > 0 else 'Posterior'
    else:
        coord_types['z'] = 'Superior' if z_norm[2] > 0 else 'Inferior'
    
    # 确定坐标系类型
    if (coord_types['x'] == 'Right' and 
        coord_types['y'] == 'Anterior' and 
        coord_types['z'] == 'Superior'):
        system = 'RAS+'
    elif (coord_types['x'] == 'Left' and 
          coord_types['y'] == 'Posterior' and 
          coord_types['z'] == 'Superior'):
        system = 'LPS+'
    else:
        system = '其他 (' + coord_types['x'][0] + coord_types['y'][0] + coord_types['z'][0] + ')'
    
    return {
        'system': system,
        'x_dir': x_dir,
        'y_dir': y_dir,
        'z_dir': z_dir,
        'x_scale': x_scale,
        'y_scale': y_scale,
        'z_scale': z_scale,
        'translation': translation,
        'orientation': coord_types
    }

def explore_nifti(file_path):
    """交互式探索NIFTI文件的切片和方向"""
    try:
        # 加载NIFTI文件
        img = nib.load(file_path)
        data = img.get_fdata()
        affine = img.affine
        header = img.header
        
        # 分析仿射矩阵
        affine_info = analyze_affine(affine)
        
        # 输出基本信息
        print(f"NIFTI文件: {file_path}")
        print(f"维度: {data.shape}")
        print(f"数据类型: {data.dtype}")
        print(f"坐标系统: {affine_info['system']}")
        print(f"方向映射: X->{affine_info['orientation']['x']}, "
              f"Y->{affine_info['orientation']['y']}, "
              f"Z->{affine_info['orientation']['z']}")
        print(f"仿射矩阵:\n{affine}")
        
        # 创建交互式显示
        fig, axs = plt.subplots(1, 3, figsize=(15, 5))
        plt.subplots_adjust(bottom=0.25)
        
        # 初始切片位置
        x_pos, y_pos, z_pos = [dim // 2 for dim in data.shape]
        
        # 显示初始切片
        x_slice = axs[0].imshow(np.rot90(data[x_pos, :, :]), cmap='gray')
        y_slice = axs[1].imshow(np.rot90(data[:, y_pos, :]), cmap='gray')
        z_slice = axs[2].imshow(np.rot90(data[:, :, z_pos]), cmap='gray')
        
        axs[0].set_title(f'Sagittal (X={x_pos})')
        axs[1].set_title(f'Coronal (Y={y_pos})')
        axs[2].set_title(f'Axial (Z={z_pos})')
        
        # 添加坐标轴
        for ax in axs:
            ax.set_axis_off()
        
        # 添加滑块
        ax_x = plt.axes([0.1, 0.1, 0.8, 0.03])
        ax_y = plt.axes([0.1, 0.15, 0.8, 0.03])
        ax_z = plt.axes([0.1, 0.05, 0.8, 0.03])
        
        s_x = Slider(ax_x, 'X', 0, data.shape[0]-1, valinit=x_pos, valstep=1)
        s_y = Slider(ax_y, 'Y', 0, data.shape[1]-1, valinit=y_pos, valstep=1)
        s_z = Slider(ax_z, 'Z', 0, data.shape[2]-1, valinit=z_pos, valstep=1)
        
        def update(val):
            x_pos = int(s_x.val)
            y_pos = int(s_y.val)
            z_pos = int(s_z.val)
            
            # 更新切片
            x_slice.set_data(np.rot90(data[x_pos, :, :]))
            y_slice.set_data(np.rot90(data[:, y_pos, :]))
            z_slice.set_data(np.rot90(data[:, :, z_pos]))
            
            # 更新标题
            axs[0].set_title(f'Sagittal (X={x_pos})')
            axs[1].set_title(f'Coronal (Y={y_pos})')
            axs[2].set_title(f'Axial (Z={z_pos})')
            
            # 计算物理坐标
            vox_coords = np.array([x_pos, y_pos, z_pos, 1])
            phys_coords = np.dot(affine, vox_coords)[:3]
            
            # 显示物理坐标信息
            fig.suptitle(f'体素坐标: ({x_pos}, {y_pos}, {z_pos}) | '
                         f'物理坐标: ({phys_coords[0]:.1f}, {phys_coords[1]:.1f}, {phys_coords[2]:.1f}) mm', 
                         fontsize=12)
            
            fig.canvas.draw_idle()
        
        # 初始化标题
        vox_coords = np.array([x_pos, y_pos, z_pos, 1])
        phys_coords = np.dot(affine, vox_coords)[:3]
        fig.suptitle(f'体素坐标: ({x_pos}, {y_pos}, {z_pos}) | '
                     f'物理坐标: ({phys_coords[0]:.1f}, {phys_coords[1]:.1f}, {phys_coords[2]:.1f}) mm', 
                     fontsize=12)
        
        # 连接回调
        s_x.on_changed(update)
        s_y.on_changed(update)
        s_z.on_changed(update)
        
        plt.show()
        
    except Exception as e:
        print(f"错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="调试NIFTI方向问题")
    parser.add_argument("file_path", help="NIFTI文件路径")
    
    if len(sys.argv) > 1:
        args = parser.parse_args()
        explore_nifti(args.file_path)
    else:
        # 如果没有提供参数，提示输入文件路径
        file_path = input("输入NIFTI文件路径: ")
        explore_nifti(file_path)
