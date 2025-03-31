#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PET图像对比度增强工具

这个脚本可以增强PET图像的对比度，使其更容易查看和分析。
它会创建一个对比度增强的副本，原始数据不会改变。

用法:
python scripts/boost_pet_contrast.py input.nii [output.nii] [--method {percentile,histogram,adaptive}]
"""

import os
import sys
import argparse
import numpy as np
import nibabel as nib
from matplotlib import pyplot as plt

def enhance_pet_image(input_file, output_file=None, method='percentile', verbose=False):
    """增强PET图像的对比度和可视化效果
    
    Args:
        input_file: 输入NIFTI文件路径
        output_file: 输出NIFTI文件路径 (如果为None，则创建带有后缀的新文件)
        method: 增强方法，可选值：'percentile', 'histogram', 'adaptive'
        verbose: 是否显示详细信息
    
    Returns:
        bool: 操作是否成功
    """
    if not output_file:
        # 创建默认输出文件名
        base, ext = os.path.splitext(input_file)
        if ext.lower() == '.gz':
            base, _ = os.path.splitext(base)
        output_file = f"{base}_enhanced{ext}"
    
    if verbose:
        print(f"输入文件: {input_file}")
        print(f"输出文件: {output_file}")
        print(f"增强方法: {method}")
    
    try:
        # 加载NIFTI文件
        img = nib.load(input_file)
        data = img.get_fdata()
        header = img.header
        affine = img.affine
        
        if verbose:
            print(f"原始图像形状: {data.shape}")
            print(f"数据范围: {np.min(data)} - {np.max(data)}")
            print(f"均值: {np.mean(data)}")
            print(f"非零像素均值: {np.mean(data[data > 0])}")
        
        # 移除NaN或Inf值
        if np.isnan(data).any() or np.isinf(data).any():
            if verbose:
                print("修复无效值 (NaN/Inf)")
            data = np.nan_to_num(data)
        
        # 根据不同方法增强对比度
        if method == 'percentile':
            # 百分位数法 - 通常对PET图像效果较好
            pos_data = data[data > 0]  # 只考虑正值
            if len(pos_data) > 0:
                p_low = np.percentile(pos_data, 1)  # 1%分位数作为下限
                p_high = np.percentile(pos_data, 85)  # 85%分位数作为上限
                
                if verbose:
                    print(f"对比度窗口: {p_low:.2f} - {p_high:.2f}")
                
                # 对数据进行缩放，保持相对强度
                enhanced = np.clip(data, p_low, p_high)
                enhanced = (enhanced - p_low) / (p_high - p_low) * p_high
            else:
                enhanced = data
                
        elif method == 'histogram':
            # 直方图均衡化 - 增强整体对比度
            # 仅适用于2D图像，对3D图像需要逐层处理
            enhanced = np.zeros_like(data)
            # 对每个轴向切片进行直方图均衡化
            for z in range(data.shape[2]):
                slice_data = data[:, :, z]
                if np.max(slice_data) > 0:  # 确保切片有信号
                    # 计算非零像素的累积分布函数
                    hist, bins = np.histogram(slice_data[slice_data > 0], bins=1000)
                    cdf = hist.cumsum() / hist.sum()
                    
                    # 映射原始值到新范围
                    for i, b in enumerate(bins[1:]):
                        mask = (slice_data > bins[i]) & (slice_data <= b)
                        if mask.any():
                            enhanced[:, :, z][mask] = cdf[i] * np.max(slice_data)
            
        elif method == 'adaptive':
            # 自适应方法 - 基于局部强度调整
            # 使用高斯滤波估计背景，然后增强前景
            from scipy.ndimage import gaussian_filter
            
            # 对数据应用高斯滤波
            sigma = max(1, min(data.shape) / 30)  # 自适应sigma基于图像尺寸
            background = gaussian_filter(data, sigma=sigma)
            
            # 前景 = 原始数据 - 平滑背景
            foreground = data - background
            foreground[foreground < 0] = 0
            
            # 增加前景强度
            enhanced = background + 2 * foreground
            enhanced[enhanced < 0] = 0
        
        # 创建新的NIFTI图像并保存
        new_img = nib.Nifti1Image(enhanced, affine, header)
        nib.save(new_img, output_file)
        
        if verbose:
            print(f"增强图像已保存: {output_file}")
            print(f"新数据范围: {np.min(enhanced)} - {np.max(enhanced)}")
        
        # 可选：显示结果对比图
        if verbose:
            print("正在生成对比图...")
            plt.figure(figsize=(12, 6))
            
            # 选择中间切片显示
            z = data.shape[2] // 2
            
            # 原始图像
            plt.subplot(1, 2, 1)
            plt.title("原始图像")
            plt.imshow(data[:, :, z], cmap='hot')
            plt.colorbar()
            
            # 增强图像
            plt.subplot(1, 2, 2)
            plt.title("增强图像")
            plt.imshow(enhanced[:, :, z], cmap='hot')
            plt.colorbar()
            
            # 生成对比图文件
            comparison_file = os.path.join(os.path.dirname(output_file), 
                                          f"{os.path.basename(output_file).split('.')[0]}_comparison.png")
            plt.savefig(comparison_file)
            plt.close()
            
            print(f"对比图已保存: {comparison_file}")
        
        return True
        
    except Exception as e:
        import traceback
        print(f"增强PET图像时出错: {str(e)}")
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PET图像对比度增强工具")
    parser.add_argument("input_file", help="输入PET NIFTI文件")
    parser.add_argument("output_file", nargs="?", help="输出增强后的NIFTI文件")
    parser.add_argument("--method", choices=["percentile", "histogram", "adaptive"], 
                       default="percentile", help="增强方法")
    parser.add_argument("-v", "--verbose", action="store_true", help="显示详细信息")
    
    args = parser.parse_args()
    
    success = enhance_pet_image(
        args.input_file,
        args.output_file,
        method=args.method,
        verbose=args.verbose
    )
    
    sys.exit(0 if success else 1)
