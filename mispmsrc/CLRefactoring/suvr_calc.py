import numpy as np
import nibabel as nib
from scipy.ndimage import zoom
import logging
import os

class SUVRCalculator:
    """SUVR (Standardized Uptake Value Ratio) 计算类"""
    
    def __init__(self):
        self.roi_img = None
        self.ref_img = None
        self.roi_affine = None
        self.ref_affine = None
        self.logger = logging.getLogger(__name__)
        
    def load_masks(self, roi_path, ref_path):
        """加载ROI和参考区域mask"""
        # Load mask data and affine transforms
        roi_nii = nib.load(roi_path)
        ref_nii = nib.load(ref_path)
        
        self.roi_img = roi_nii.get_fdata()
        self.ref_img = ref_nii.get_fdata()
        
        self.roi_affine = roi_nii.affine
        self.ref_affine = ref_nii.affine
        
        # 计算非零点数量
        self.num_roi = np.count_nonzero(self.roi_img)
        self.num_ref = np.count_nonzero(self.ref_img)
    
    def _resample_mask(self, mask_img, target_shape):
        """将mask重采样到目标shape"""
        if mask_img.shape == target_shape:
            return mask_img
            
        # Calculate zoom factors for each dimension
        zoom_factors = []
        for target, current in zip(target_shape, mask_img.shape):
            if current == 0:
                zoom_factors.append(1)  # Avoid division by zero
            else:
                zoom_factors.append(float(target) / current)
        
        # Add any missing dimensions
        while len(zoom_factors) < 3:
            zoom_factors.append(1)
        
        # Resample using scipy.ndimage.zoom with nearest neighbor interpolation
        resampled = zoom(mask_img, zoom_factors[:3], order=0, mode='nearest')
        
        # Ensure output shape matches target
        pad_width = []
        for target, resampled in zip(target_shape, resampled.shape):
            if target > resampled:
                pad_width.append((0, target - resampled))
            else:
                pad_width.append((0, 0))
        
        # Pad if necessary
        if any(p[1] > 0 for p in pad_width):
            resampled = np.pad(resampled, pad_width, mode='constant', constant_values=0)
            
        return resampled

    def calculate(self, pet_filepaths):
        """计算SUVR值"""
        if self.roi_img is None or self.ref_img is None:
            raise ValueError("ROI and reference masks must be loaded first")
            
        if not pet_filepaths:
            raise ValueError("No PET files provided")
            
        suvr_values = []
        processed_files = 0
        errors = []
        
        for filepath in pet_filepaths:
            try:
                # 验证文件存在
                if not os.path.exists(filepath):
                    errors.append(f"File not found: {filepath}")
                    continue
                    
                # 加载PET图像
                self.logger.info(f"Processing {filepath}")
                pet_nii = nib.load(filepath)
                pet_img = pet_nii.get_fdata()
                
                # 检查图像尺寸
                if pet_img.size == 0:
                    errors.append(f"Empty image data in {filepath}")
                    continue
                    
                # 确保PET图像是3D的
                if len(pet_img.shape) > 3:
                    self.logger.info(f"Converting 4D image to 3D in {filepath}")
                    pet_img = pet_img[:,:,:,0]
                
                # 重采样mask
                roi_resampled = self._resample_mask(self.roi_img, pet_img.shape)
                ref_resampled = self._resample_mask(self.ref_img, pet_img.shape)
                
                # 检查mask有效性
                num_roi = np.count_nonzero(roi_resampled)
                num_ref = np.count_nonzero(ref_resampled)
                
                if num_roi == 0:
                    errors.append(f"No valid ROI voxels in {filepath}")
                    continue
                if num_ref == 0:
                    errors.append(f"No valid reference voxels in {filepath}")
                    continue
                    
                # 处理NaN值
                nan_count = np.sum(np.isnan(pet_img))
                if nan_count > 0:
                    self.logger.warning(f"Found {nan_count} NaN values in {filepath}")
                    pet_img = np.nan_to_num(pet_img, 0)
                
                # 计算SUVR
                roi_sum = np.sum(pet_img * roi_resampled)
                ref_sum = np.sum(pet_img * ref_resampled)
                
                if ref_sum <= 0:
                    errors.append(f"Zero or negative reference sum in {filepath}")
                    continue
                    
                suv_roi = roi_sum / num_roi
                suv_ref = ref_sum / num_ref
                suvr = suv_roi / suv_ref
                
                if not np.isfinite(suvr):
                    errors.append(f"Invalid SUVR value in {filepath}")
                    continue
                    
                suvr_values.append(suvr)
                processed_files += 1
                self.logger.info(f"Processed {filepath}: SUVR = {suvr:.4f}")
                
            except Exception as e:
                errors.append(f"Error processing {filepath}: {str(e)}")
                continue
        
        # 如果没有成功处理任何文件，报告所有错误
        if not suvr_values:
            error_msg = f"No valid SUVR values could be calculated from {len(pet_filepaths)} files:\n"
            error_msg += "\n".join(errors)
            raise ValueError(error_msg)
        
        self.logger.info(f"Successfully processed {processed_files}/{len(pet_filepaths)} files")
        return np.array(suvr_values)