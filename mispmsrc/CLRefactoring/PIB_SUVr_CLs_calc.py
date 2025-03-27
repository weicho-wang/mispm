import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from glob import glob
import logging
from mispmsrc.CLRefactoring.suvr_calc import SUVRCalculator
from mispmsrc.CLRefactoring.CL_calc_test import CLCalculator

class PIBAnalyzer:
    """PIB SUVR和CL分析类"""
    
    def __init__(self):
        self.suvr_calculator = SUVRCalculator()
        self.cl_calculator = CLCalculator()
        self.logger = logging.getLogger(__name__)
    
    def run_analysis(self, ref_path, roi_path, ad_dir, yc_dir, standard_data_path):
        """运行完整分析流程
        
        Args:
            ref_path: 参考区域mask路径
            roi_path: ROI mask路径
            ad_dir: AD组PET图像目录
            yc_dir: YC组PET图像目录
            standard_data_path: 标准数据Excel文件路径
        """
        try:
            # 验证输入文件和目录是否存在
            if not os.path.exists(ref_path):
                raise FileNotFoundError(f"Reference mask not found: {ref_path}")
            if not os.path.exists(roi_path):
                raise FileNotFoundError(f"ROI mask not found: {roi_path}")
            if not os.path.exists(ad_dir):
                raise FileNotFoundError(f"AD directory not found: {ad_dir}")
            if not os.path.exists(yc_dir):
                raise FileNotFoundError(f"YC directory not found: {yc_dir}")
            if not os.path.exists(standard_data_path):
                raise FileNotFoundError(f"Standard data file not found: {standard_data_path}")
            
            # 加载mask
            self.logger.info("Loading mask files...")
            self.suvr_calculator.load_masks(roi_path, ref_path)
            
            # 获取PET文件路径（修改搜索模式）
            ad_pattern = os.path.join(ad_dir, '*.nii')
            yc_pattern = os.path.join(yc_dir, '*.nii')
            
            self.logger.info(f"Searching for PET files in AD directory: {ad_pattern}")
            ad_files = sorted([f for f in glob(ad_pattern) if os.path.isfile(f)])
            
            self.logger.info(f"Searching for PET files in YC directory: {yc_pattern}")
            yc_files = sorted([f for f in glob(yc_pattern) if os.path.isfile(f)])
            
            # 增加详细的日志
            self.logger.info(f"AD directory contents: {os.listdir(ad_dir)}")
            self.logger.info(f"YC directory contents: {os.listdir(yc_dir)}")
            
            if not ad_files:
                raise FileNotFoundError(
                    f"No NIFTI files found in AD directory: {ad_dir}\n"
                    f"Expected pattern: {ad_pattern}"
                )
            if not yc_files:
                raise FileNotFoundError(
                    f"No NIFTI files found in YC directory: {yc_dir}\n"
                    f"Expected pattern: {yc_pattern}"
                )
                
            self.logger.info(f"Found {len(ad_files)} AD files:")
            for f in ad_files:
                self.logger.info(f"  {f}")
            self.logger.info(f"Found {len(yc_files)} YC files:")
            for f in yc_files:
                self.logger.info(f"  {f}")
            
            # 计算SUVR
            self.logger.info("Calculating SUVR values for AD group...")
            ad_suvr = self.suvr_calculator.calculate(ad_files)
            self.logger.info("Calculating SUVR values for YC group...")
            yc_suvr = self.suvr_calculator.calculate(yc_files)
            
            if len(ad_suvr) == 0 or len(yc_suvr) == 0:
                raise ValueError("No valid SUVR values calculated for one or both groups")
            
            # 计算CL值
            self.logger.info("Calculating CL values...")
            ad_cl, yc_cl, suvr_yc_mean, suvr_ad_mean = self.cl_calculator.calculate(ad_suvr, yc_suvr)
            
            # 组合结果
            suvr_calc = np.concatenate([ad_suvr, yc_suvr])
            cl_calc = np.concatenate([ad_cl, yc_cl])
            
            # 加载标准数据
            self.logger.info("Loading standard data...")
            try:
                std_data = pd.read_excel(standard_data_path)
            except Exception as e:
                raise ValueError(f"Error reading standard data file: {str(e)}")
            
            try:
                ad_suvr_std = std_data['SUVR'].values[1:45]
                ad_cl_std = std_data['CL'].values[1:45]
                yc_suvr_std = std_data['SUVR'].values[47:]
                yc_cl_std = std_data['CL'].values[47:]
            except Exception as e:
                raise ValueError(f"Invalid standard data format: {str(e)}")
            
            suvr_std = np.concatenate([ad_suvr_std, yc_suvr_std])
            cl_std = np.concatenate([ad_cl_std, yc_cl_std])
            
            # 计算相关性并绘图
            self.logger.info("Plotting correlation analysis...")
            self._plot_correlation(
                suvr_std, suvr_calc, cl_std, cl_calc,
                ad_suvr_std, ad_suvr, yc_suvr_std, yc_suvr,
                ad_cl_std, ad_cl, yc_cl_std, yc_cl
            )
            
            self.logger.info("Analysis completed successfully")
            
        except Exception as e:
            self.logger.error(f"Error during analysis: {str(e)}")
            raise
    
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