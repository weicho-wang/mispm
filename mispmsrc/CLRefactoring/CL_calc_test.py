import numpy as np
import logging

class CLCalculator:
    """Centiloid (CL) 计算类"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def calculate(self, ad_suvr, yc_suvr):
        """Calculate Centiloid values
        
        Args:
            ad_suvr: AD group SUVR values array
            yc_suvr: YC group SUVR values array
            
        Returns:
            tuple: (AD group CL values, YC group CL values, YC group SUVR mean, AD group SUVR mean)
        """
        # Calculate means
        suvr_yc_mean = np.mean(yc_suvr)
        suvr_ad_mean = np.mean(ad_suvr)
        
        self.logger.info(f"AD group SUVR mean: {suvr_ad_mean:.4f}")
        self.logger.info(f"YC group SUVR mean: {suvr_yc_mean:.4f}")
        
        # Avoid division by zero
        if abs(suvr_ad_mean - suvr_yc_mean) < 0.001:
            self.logger.warning("Difference between AD and YC means is too small, using default slope of 100")
            slope = 100
        else:
            # Calculate slope
            slope = 100 / (suvr_ad_mean - suvr_yc_mean)
            
        self.logger.info(f"Calculated slope: {slope:.4f}")
        
        # Calculate CL values
        # Note: YC mean will be 0 by definition in the Centiloid scale
        ad_cl = slope * (ad_suvr - suvr_yc_mean)
        yc_cl = slope * (yc_suvr - suvr_yc_mean)
        
        # Log summary statistics for calculated CL values
        self.logger.info(f"AD group CL mean: {np.mean(ad_cl):.2f}, min: {np.min(ad_cl):.2f}, max: {np.max(ad_cl):.2f}")
        self.logger.info(f"YC group CL mean: {np.mean(yc_cl):.2f}, min: {np.min(yc_cl):.2f}, max: {np.max(yc_cl):.2f}")
        self.logger.info("Note: YC group CL values are 0 by definition in the Centiloid scale")
        self.logger.info("This is because the CL scale sets the YC group mean as the reference point (0)")
        
        return ad_cl, yc_cl, suvr_yc_mean, suvr_ad_mean