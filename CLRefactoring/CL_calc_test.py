import numpy as np

class CLCalculator:
    """Centiloid (CL) 计算类"""
    
    @staticmethod
    def calculate(ad_suvr, yc_suvr):
        """计算Centiloid值
        
        Args:
            ad_suvr: AD组SUVR值数组
            yc_suvr: YC组SUVR值数组
            
        Returns:
            tuple: (AD组CL值, YC组CL值, YC组SUVR均值, AD组SUVR均值)
        """
        # 计算均值
        suvr_yc_mean = np.mean(yc_suvr)
        suvr_ad_mean = np.mean(ad_suvr)
        
        # 计算斜率
        slope = 100 / (suvr_ad_mean - suvr_yc_mean)
        
        # 计算CL值
        ad_cl = slope * (ad_suvr - suvr_yc_mean)
        yc_cl = slope * (yc_suvr - suvr_yc_mean)
        
        return ad_cl, yc_cl, suvr_yc_mean, suvr_ad_mean
