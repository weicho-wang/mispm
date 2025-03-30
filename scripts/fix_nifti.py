#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
NIFTI文件修复工具

此脚本可以帮助修复损坏或有问题的NIFTI文件，使其能够正常显示。
可以处理的问题包括：
- 修复NaN或Inf值
- 调整数据类型
- 重置仿射变换矩阵和原点

用法:
python scripts/fix_nifti.py input.nii output.nii [选项]
"""

import os
import sys
import argparse
import traceback
import numpy as np
import nibabel as nib

def fix_nifti(input_file, output_file, reset_origin=False, force_dtype=None, verbose=False):
    """修复NIFTI文件并保存

    Args:
        input_file: 输入文件路径
        output_file: 输出文件路径
        reset_origin: 是否重置原点
        force_dtype: 强制使用的数据类型
        verbose: 是否显示详细信息
    
    Returns:
        bool: 操作是否成功
    """
    if verbose:
        print(f"修复NIFTI文件: {input_file}")
        print(f"输出到: {output_file}")
    
    try:
        # 加载NIFTI文件
        if verbose:
            print("加载NIFTI文件...")
        
        img = nib.load(input_file)
        
        if verbose:
            print(f"已加载NIFTI文件。形状: {img.shape}")
            print(f"数据类型: {img.get_data_dtype()}")
            print(f"仿射矩阵:\n{img.affine}")
        
        # 加载数据
        data = img.get_fdata()
        
        # 检查数据是否有无效值
        nan_count = np.sum(np.isnan(data))
        inf_count = np.sum(np.isinf(data))
        
        if nan_count > 0 or inf_count > 0:
            if verbose:
                print(f"发现无效值: {nan_count} NaN, {inf_count} Inf")
            # 替换无效值
            data = np.nan_to_num(data)
        
        # 强制使用指定的数据类型
        if force_dtype:
            if verbose:
                print(f"转换数据类型为: {force_dtype}")
            data = data.astype(force_dtype)
        
        # 获取仿射矩阵
        affine = img.affine.copy()
        
        # 如果需要重置原点
        if reset_origin:
            if verbose:
                print("重置原点...")
            # 将原点设置为图像中心
            center = np.array(data.shape) // 2
            # 转换为物理坐标
            center_mm = np.dot(affine, np.append(center, 1))[:3]
            
            # 方法1: 在仿射矩阵中设置原点（第4列的前三行）为中心
            # affine[:3, 3] = center_mm
            
            # 方法2: 保持旋转部分不变，仅设置翻译部分
            new_origin = -np.dot(affine[:3, :3], center)
            affine[:3, 3] = new_origin
            
            if verbose:
                print(f"新原点: {affine[:3, 3]}")
        
        # 创建新的NIFTI图像
        new_img = nib.Nifti1Image(data, affine, img.header)
        
        # 保存修复后的图像
        nib.save(new_img, output_file)
        
        if verbose:
            print(f"已保存修复后的文件到: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"修复NIFTI文件时出错: {str(e)}")
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="修复损坏的NIFTI文件")
    parser.add_argument("input_file", help="输入NIFTI文件路径")
    parser.add_argument("output_file", nargs="?", help="输出NIFTI文件路径")
    parser.add_argument("--reset-origin", action="store_true", help="重置原点到图像中心")
    parser.add_argument("--dtype", choices=["float32", "float64", "int16", "uint8"], help="强制转换为指定数据类型")
    parser.add_argument("-v", "--verbose", action="store_true", help="显示详细信息")
    
    args = parser.parse_args()
    
    # 如果没有指定输出文件名，则构造一个
    if not args.output_file:
        base, ext = os.path.splitext(args.input_file)
        if ext.lower() == '.gz':
            base, _ = os.path.splitext(base)
        args.output_file = f"{base}_fixed.nii"
    
    success = fix_nifti(
        args.input_file,
        args.output_file,
        reset_origin=args.reset_origin,
        force_dtype=args.dtype,
        verbose=args.verbose
    )
    
    sys.exit(0 if success else 1)
