import numpy as np
import nibabel as nib

class SUVRCalculator:
    """SUVR (Standardized Uptake Value Ratio) 计算类"""
    
    def __init__(self):
        self.roi_img = None
        self.ref_img = None
        
    def load_masks(self, roi_path, ref_path):
        """加载ROI和参考区域mask"""
        self.roi_img = nib.load(roi_path).get_fdata()
        self.ref_img = nib.load(ref_path).get_fdata()
        
        # 计算非零点数量
        self.num_roi = np.count_nonzero(self.roi_img)
        self.num_ref = np.count_nonzero(self.ref_img)
    
    def calculate(self, pet_filepaths):
        """计算SUVR值
        
        Args:
            pet_filepaths: PET图像文件路径列表
            
        Returns:
            np.ndarray: SUVR值数组
        """
        if self.roi_img is None or self.ref_img is None:
            raise ValueError("请先加载ROI和参考区域mask")
            
        suvr_values = []
        
        for filepath in pet_filepaths:
            # 加载PET图像
            pet_img = nib.load(filepath).get_fdata()
            
            # 将NaN值替换为0
            pet_img = np.nan_to_num(pet_img, 0)
            
            # 计算ROI和参考区域的值
            roi = pet_img * self.roi_img
            ref = pet_img * self.ref_img
            
            # 计算总和
            roi_sum = np.sum(roi)
            ref_sum = np.sum(ref)
            
            # 计算平均值
            suv_roi = roi_sum / self.num_roi
            suv_ref = ref_sum / self.num_ref
            
            # 计算SUVR
            suvr = suv_roi / suv_ref
            suvr_values.append(suvr)
        
        return np.array(suvr_values)