import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from glob import glob
from .suvr_calc import SUVRCalculator
from .CL_calc_test import CLCalculator

class PIBAnalyzer:
    """PIB SUVR和CL分析类"""
    
    def __init__(self):
        self.suvr_calculator = SUVRCalculator()
        self.cl_calculator = CLCalculator()
        
    def run_analysis(self, ref_path, roi_path, ad_dir, yc_dir, standard_data_path):
        """运行完整分析流程
        
        Args:
            ref_path: 参考区域mask路径
            roi_path: ROI mask路径
            ad_dir: AD组PET图像目录
            yc_dir: YC组PET图像目录
            standard_data_path: 标准数据Excel文件路径
        """
        # 加载mask
        self.suvr_calculator.load_masks(roi_path, ref_path)
        
        # 获取PET文件路径
        ad_files = sorted(glob(os.path.join(ad_dir, 'w*.nii')))
        yc_files = sorted(glob(os.path.join(yc_dir, 'w*.nii')))
        
        # 计算SUVR
        ad_suvr = self.suvr_calculator.calculate(ad_files)
        yc_suvr = self.suvr_calculator.calculate(yc_files)
        
        # 计算CL值
        ad_cl, yc_cl, suvr_yc_mean, suvr_ad_mean = self.cl_calculator.calculate(ad_suvr, yc_suvr)
        
        # 组合结果
        suvr_calc = np.concatenate([ad_suvr, yc_suvr])
        cl_calc = np.concatenate([ad_cl, yc_cl])
        
        # 加载标准数据
        std_data = pd.read_excel(standard_data_path)
        ad_suvr_std = std_data['SUVR'].values[1:45]  # 2-46行
        ad_cl_std = std_data['CL'].values[1:45]      # 2-46行
        yc_suvr_std = std_data['SUVR'].values[47:]   # 48行到最后
        yc_cl_std = std_data['CL'].values[47:]       # 48行到最后
        
        suvr_std = np.concatenate([ad_suvr_std, yc_suvr_std])
        cl_std = np.concatenate([ad_cl_std, yc_cl_std])
        
        # 计算相关性
        self._plot_correlation(
            suvr_std, suvr_calc, cl_std, cl_calc,
            ad_suvr_std, ad_suvr, yc_suvr_std, yc_suvr,
            ad_cl_std, ad_cl, yc_cl_std, yc_cl
        )
    
    def _plot_correlation(self, suvr_std, suvr_calc, cl_std, cl_calc,
                         ad_suvr_std, ad_suvr, yc_suvr_std, yc_suvr,
                         ad_cl_std, ad_cl, yc_cl_std, yc_cl):
        """绘制相关性图"""
        # SUVR相关性
        p1 = np.polyfit(suvr_std, suvr_calc, 1)
        r1 = np.corrcoef(suvr_std, suvr_calc)[0,1]
        r1_sq = r1**2
        
        plt.figure()
        plt.plot(ad_suvr_std, ad_suvr, '*r', label='AD')
        plt.plot(yc_suvr_std, yc_suvr, '*b', label='YC')
        plt.plot(suvr_std, np.polyval(p1, suvr_std), '-', 
                label=f'y={p1[0]:.3f}x+{p1[1]:.3f} & r²={r1_sq:.3f}')
        plt.xlabel('PIB SUVR GAAIN')
        plt.ylabel('PIB SUVR calc')
        plt.title('PIB SUVR TEST')
        plt.legend(loc='northwest')
        
        # CL相关性
        p2 = np.polyfit(cl_std, cl_calc, 1)
        r2 = np.corrcoef(cl_std, cl_calc)[0,1]
        r2_sq = r2**2
        
        plt.figure()
        plt.plot(ad_cl_std, ad_cl, '*r', label='AD')
        plt.plot(yc_cl_std, yc_cl, '*b', label='YC')
        plt.plot(cl_std, np.polyval(p2, cl_std), '-',
                label=f'y={p2[0]:.3f}x+{p2[1]:.3f} & r²={r2_sq:.3f}')
        plt.xlabel('PIB CL GAAIN')
        plt.ylabel('PIB CL calc')
        plt.title('PIB CL TEST')
        plt.legend(loc='northwest')
        
        plt.show()

if __name__ == "__main__":
    # set file path
    REF_PATH = './Centiloid_Std_VOI/nifti/2mm/voi_WhlCbl_2mm.nii'  # mask file of cerebellum
    ROI_PATH = './Centiloid_Std_VOI/nifti/2mm/voi_ctx_2mm.nii'  # mask file of Gray Matter Cortex
    AD_DIR = './AD-100_PET_5070/nifti/'  # PET images of AD group after preprocessing
    YC_DIR = './YC-0_PET_5070/nifti/'  # PET images of YC group
    STANDARD_DATA = './SupplementaryTable1.xlsx'  # standard data file
    
    # run analysis
    analyzer = PIBAnalyzer()
    analyzer.run_analysis(REF_PATH, ROI_PATH, AD_DIR, YC_DIR, STANDARD_DATA)
