"""
Module for plotting SUVR and CL analysis results
This provides visualization capabilities similar to the original MATLAB code.
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.colors import LinearSegmentedColormap
import logging
from scipy import stats
import pandas as pd
import datetime
from .chinese_font_utils import setup_matplotlib_chinese, add_chinese_text, find_chinese_font

class AnalysisPlotter:
    """Class for creating various plots for SUVR and CL analysis"""
    
    def __init__(self, output_dir=None):
        """Initialize plotter with output directory"""
        self.logger = logging.getLogger(__name__)
        if output_dir:
            self.output_dir = output_dir
        else:
            # Default to results folder in same directory as this module
            self.output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Set default style
        plt.style.use('default')
        
        # Configure matplotlib for non-interactive backend if running in non-main thread
        import threading
        if threading.current_thread() is not threading.main_thread():
            self.logger.info("Using Agg backend for matplotlib in non-main thread")
            import matplotlib
            matplotlib.use('Agg')  # Use non-interactive backend for non-main threads
        
        # Configure matplotlib for Chinese characters
        setup_matplotlib_chinese()
        
        # Generate timestamp for filenames
        self.timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def plot_correlation(self, suvr_std, suvr_calc, cl_std, cl_calc,
                         ad_suvr_std, ad_suvr, yc_suvr_std, yc_suvr,
                         ad_cl_std, ad_cl, yc_cl_std, yc_cl, show_plots=True):
        """
        Plot correlation between calculated and standard values
        
        Creates subplots for:
        1. SUVR correlation (calculated vs standard)
        2. CL correlation (calculated vs standard)
        3. AD/YC group comparison as boxplots
        
        Args:
            suvr_std: Standard SUVR values for all subjects
            suvr_calc: Calculated SUVR values for all subjects
            cl_std: Standard CL values for all subjects
            cl_calc: Calculated CL values for all subjects
            ad_suvr_std: Standard SUVR values for AD group
            ad_suvr: Calculated SUVR values for AD group
            yc_suvr_std: Standard SUVR values for YC group
            yc_suvr: Calculated SUVR values for YC group
            ad_cl_std: Standard CL values for AD group
            ad_cl: Calculated CL values for AD group
            yc_cl_std: Standard CL values for YC group
            yc_cl: Calculated CL values for YC group
            show_plots: Whether to display the plots (default: True)
        
        Returns:
            dict: Dictionary with plot information including:
                - 'suvr_correlation': r-squared for SUVR correlation
                - 'cl_correlation': r-squared for CL correlation
                - 'figure_paths': Paths to saved figure files
        """
        try:
            # Create figure with subplots in grid layout
            fig = plt.figure(figsize=(18, 12))
            gs = gridspec.GridSpec(2, 2, figure=fig)
            
            # Prepare data - clean NaN values
            # Fix broadcasting issue by ensuring arrays have the same shape
            if len(suvr_std) != len(suvr_calc):
                self.logger.warning(f"Array size mismatch: suvr_std({len(suvr_std)}) != suvr_calc({len(suvr_calc)})")
                # Pad the smaller array or trim the larger one
                if len(suvr_std) > len(suvr_calc):
                    self.logger.info(f"Trimming suvr_std from {len(suvr_std)} to {len(suvr_calc)}")
                    suvr_std = suvr_std[:len(suvr_calc)]
                else:
                    self.logger.info(f"Trimming suvr_calc from {len(suvr_calc)} to {len(suvr_std)}")
                    suvr_calc = suvr_calc[:len(suvr_std)]
            
            if len(cl_std) != len(cl_calc):
                self.logger.warning(f"Array size mismatch: cl_std({len(cl_std)}) != cl_calc({len(cl_calc)})")
                # Pad the smaller array or trim the larger one
                if len(cl_std) > len(cl_calc):
                    self.logger.info(f"Trimming cl_std from {len(cl_std)} to {len(cl_calc)}")
                    cl_std = cl_std[:len(cl_calc)]
                else:
                    self.logger.info(f"Trimming cl_calc from {len(cl_calc)} to {len(cl_std)}")
                    cl_calc = cl_calc[:len(cl_std)]
            
            # Fix array size mismatch for AD and YC groups as well
            if len(ad_suvr_std) != len(ad_suvr):
                self.logger.warning(f"AD SUVR size mismatch: std({len(ad_suvr_std)}) != calc({len(ad_suvr)})")
                min_len = min(len(ad_suvr_std), len(ad_suvr))
                ad_suvr_std = ad_suvr_std[:min_len]
                ad_suvr = ad_suvr[:min_len]
                
            if len(yc_suvr_std) != len(yc_suvr):
                self.logger.warning(f"YC SUVR size mismatch: std({len(yc_suvr_std)}) != calc({len(yc_suvr)})")
                min_len = min(len(yc_suvr_std), len(yc_suvr))
                yc_suvr_std = yc_suvr_std[:min_len]
                yc_suvr = yc_suvr[:min_len]
                
            if len(ad_cl_std) != len(ad_cl):
                self.logger.warning(f"AD CL size mismatch: std({len(ad_cl_std)}) != calc({len(ad_cl)})")
                min_len = min(len(ad_cl_std), len(ad_cl))
                ad_cl_std = ad_cl_std[:min_len]
                ad_cl = ad_cl[:min_len]
                
            if len(yc_cl_std) != len(yc_cl):
                self.logger.warning(f"YC CL size mismatch: std({len(yc_cl_std)}) != calc({len(yc_cl)})")
                min_len = min(len(yc_cl_std), len(yc_cl))
                yc_cl_std = yc_cl_std[:min_len]
                yc_cl = yc_cl[:min_len]
                
            suvr_std = np.array(suvr_std, dtype=float)
            suvr_calc = np.array(suvr_calc, dtype=float)
            cl_std = np.array(cl_std, dtype=float)
            cl_calc = np.array(cl_calc, dtype=float)
            
            # Ensure all group arrays are properly converted to numpy arrays
            ad_suvr_std = np.array(ad_suvr_std, dtype=float)
            ad_suvr = np.array(ad_suvr, dtype=float)
            yc_suvr_std = np.array(yc_suvr_std, dtype=float)
            yc_suvr = np.array(yc_suvr, dtype=float)
            ad_cl_std = np.array(ad_cl_std, dtype=float)
            ad_cl = np.array(ad_cl, dtype=float)
            yc_cl_std = np.array(yc_cl_std, dtype=float)
            yc_cl = np.array(yc_cl, dtype=float)
            
            # Filter out NaNs
            mask = ~(np.isnan(suvr_std) | np.isnan(suvr_calc))
            suvr_std_clean = suvr_std[mask]
            suvr_calc_clean = suvr_calc[mask]
            
            mask = ~(np.isnan(cl_std) | np.isnan(cl_calc))
            cl_std_clean = cl_std[mask]
            cl_calc_clean = cl_calc[mask]
            
            result = {
                'suvr_correlation': 0,
                'cl_correlation': 0,
                'figure_paths': []
            }
            
            # 1. SUVR Correlation Plot
            if len(suvr_std_clean) > 1 and len(suvr_calc_clean) > 1:
                # Create regression model
                slope, intercept, r, p, _ = stats.linregress(suvr_std_clean, suvr_calc_clean)
                r_sq = r**2
                result['suvr_correlation'] = r_sq
                
                # Create plot
                ax1 = fig.add_subplot(gs[0, 0])
                
                # Plot data points with different colors for AD/YC
                ax1.scatter(ad_suvr_std, ad_suvr, c='red', marker='o', s=60, label='AD')
                ax1.scatter(yc_suvr_std, yc_suvr, c='blue', marker='o', s=60, label='YC')
                
                # Add regression line
                x_range = np.linspace(min(suvr_std_clean), max(suvr_std_clean), 100)
                ax1.plot(x_range, slope*x_range + intercept, 'k-', 
                        label=f'y = {slope:.3f}x + {intercept:.3f}, r² = {r_sq:.3f}')
                
                # Add identity line (y=x) as reference
                ax1.plot(x_range, x_range, 'k--', alpha=0.5, label='y = x (Identity)')
                
                # Add text with regression details
                ax1.text(0.05, 0.95, f'Slope: {slope:.3f}\nIntercept: {intercept:.3f}\nr²: {r_sq:.3f}',
                        transform=ax1.transAxes, fontsize=10, verticalalignment='top',
                        bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
                
                # Label and style
                ax1.set_xlabel('PIB SUVR Standard', fontsize=12)
                ax1.set_ylabel('PIB SUVR Calculated', fontsize=12)
                ax1.set_title('PIB SUVR Correlation Analysis', fontsize=14, fontweight='bold')
                ax1.legend(fontsize=10, loc='best')
                ax1.grid(True, alpha=0.3)
                
                # Add equal aspect ratio
                x_min, x_max = ax1.get_xlim()
                y_min, y_max = ax1.get_ylim()
                ax1.set_xlim(min(x_min, y_min), max(x_max, y_max))
                ax1.set_ylim(min(x_min, y_min), max(x_max, y_max))
            
            # 2. CL Correlation Plot
            if len(cl_std_clean) > 1 and len(cl_calc_clean) > 1:
                # Create regression model
                slope, intercept, r, p, _ = stats.linregress(cl_std_clean, cl_calc_clean)
                r_sq = r**2
                result['cl_correlation'] = r_sq
                
                # Create plot
                ax2 = fig.add_subplot(gs[0, 1])
                
                # Plot data points with different colors for AD/YC
                ax2.scatter(ad_cl_std, ad_cl, c='red', marker='o', s=60, label='AD')
                ax2.scatter(yc_cl_std, yc_cl, c='blue', marker='o', s=60, label='YC')
                
                # Add regression line
                x_range = np.linspace(min(cl_std_clean), max(cl_std_clean), 100)
                ax2.plot(x_range, slope*x_range + intercept, 'k-', 
                        label=f'y = {slope:.3f}x + {intercept:.3f}, r² = {r_sq:.3f}')
                
                # Add identity line (y=x) as reference
                ax2.plot(x_range, x_range, 'k--', alpha=0.5, label='y = x (Identity)')
                
                # Add text with regression details
                ax2.text(0.05, 0.95, f'Slope: {slope:.3f}\nIntercept: {intercept:.3f}\nr²: {r_sq:.3f}',
                        transform=ax2.transAxes, fontsize=10, verticalalignment='top',
                        bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
                
                # Label and style
                ax2.set_xlabel('PIB CL Standard', fontsize=12)
                ax2.set_ylabel('PIB CL Calculated', fontsize=12)
                ax2.set_title('PIB Centiloid Correlation Analysis', fontsize=14, fontweight='bold')
                ax2.legend(fontsize=10, loc='best')
                ax2.grid(True, alpha=0.3)
                
                # Add equal aspect ratio
                x_min, x_max = ax2.get_xlim()
                y_min, y_max = ax2.get_ylim()
                ax2.set_xlim(min(x_min, y_min), max(x_max, y_max))
                ax2.set_ylim(min(x_min, y_min), max(x_max, y_max))
            
            # Final figure adjustments
            plt.tight_layout()
            
            # Save figures - both individually and combined with timestamps
            suvr_corr_path = os.path.join(self.output_dir, f'suvr_correlation_{self.timestamp}.pdf')
            cl_corr_path = os.path.join(self.output_dir, f'cl_correlation_{self.timestamp}.pdf')
            combined_path = os.path.join(self.output_dir, f'suvr_cl_analysis_{self.timestamp}.pdf')
            
            fig.savefig(combined_path, dpi=300, bbox_inches='tight', format='pdf')
            result['figure_paths'].append(combined_path)
            
            if show_plots:
                plt.show()
            else:
                plt.close('all')
            
            self.logger.info(f"Saved plots to: {self.output_dir}")
            return result
        
        except Exception as e:
            self.logger.error(f"Error creating correlation plots: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return {'suvr_correlation': 0, 'cl_correlation': 0, 'figure_paths': []}
    
    def create_summary_report(self, ad_suvr, yc_suvr, ad_cl, yc_cl, file_info=None, patient_info=None):
        """
        Create a visual summary report with basic statistics for AD and YC groups
        
        Args:
            ad_suvr: SUVR values for AD group
            yc_suvr: SUVR values for YC group
            ad_cl: CL values for AD group
            yc_cl: CL values for YC group
            file_info: Optional dictionary with file information
            patient_info: Optional dictionary with patient information
            
        Returns:
            list: Paths to saved summary report files (two pages)
        """
        try:
            self.logger.info(f"Creating summary report with: AD SUVR({len(ad_suvr)}), YC SUVR({len(yc_suvr)}), AD CL({len(ad_cl)}), YC CL({len(yc_cl)})")
            
            # Verify data is valid before proceeding
            if len(ad_suvr) == 0 or len(yc_suvr) == 0:
                self.logger.error("Cannot create report: Empty AD or YC SUVR data")
                return None
                
            # First try to create PDF reports
            try:
                self.logger.info("Attempting to create PDF report...")
                page1_path = self._create_report_page1(ad_suvr, yc_suvr, ad_cl, yc_cl, file_info, patient_info, format='pdf')
                page2_path = self._create_report_page2(ad_suvr, yc_suvr, ad_cl, yc_cl, file_info, patient_info, format='pdf')
                
                # Verify the files were actually created
                if page1_path and os.path.exists(page1_path) and page2_path and os.path.exists(page2_path):
                    self.logger.info(f"Created PDF report pages successfully")
                    return [page1_path, page2_path]
                else:
                    self.logger.warning("PDF report files not found, falling back to PNG format")
                    raise Exception("PDF report generation failed")
                    
            except Exception as e:
                # If PDF fails, fall back to PNG
                self.logger.warning(f"Error creating PDF report: {str(e)}, trying PNG format")
                page1_path = self._create_report_page1(ad_suvr, yc_suvr, ad_cl, yc_cl, file_info, patient_info, format='png')
                page2_path = self._create_report_page2(ad_suvr, yc_suvr, ad_cl, yc_cl, file_info, patient_info, format='png')
                
                # Verify the files were actually created
                if page1_path and os.path.exists(page1_path) and page2_path and os.path.exists(page2_path):
                    self.logger.info(f"Created PNG report pages successfully")
                    return [page1_path, page2_path]
                else:
                    self.logger.error("Failed to create report in both PDF and PNG formats")
                    return None
            
        except Exception as e:
            self.logger.error(f"Error creating summary report: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            
            # Create emergency report with minimal content
            try:
                self.logger.info("Attempting to create emergency report with minimal content...")
                emergency_path = self._create_emergency_report(ad_suvr, yc_suvr, ad_cl, yc_cl)
                if emergency_path:
                    self.logger.info(f"Created emergency report: {emergency_path}")
                    return [emergency_path]
            except Exception as em_err:
                self.logger.error(f"Even emergency report failed: {str(em_err)}")
            
            return None

    def _create_report_page1(self, ad_suvr, yc_suvr, ad_cl, yc_cl, file_info=None, patient_info=None, format='pdf'):
        """Create first page of the report with statistics tables"""
        try:
            # Set exact A4 size in portrait orientation - 210x297mm (8.27x11.69 inches)
            # The figure size is critical for fitting properly on A4 paper
            fig = plt.figure(figsize=(8.27, 11.69), dpi=100)
            
            # Ensure content fills the entire page vertically
            # Use a smaller margin to maximize space
            fig.subplots_adjust(left=0.1, right=0.9, top=0.95, bottom=0.05, hspace=0.4)
            
            # Use a GridSpec with more rows for better vertical distribution
            gs = plt.GridSpec(50, 2)  # Increased from 40 to 50 rows for better vertical distribution
            
            # ----- REPORT HEADER -----
            # Create and apply the header (common function for both pages)
            self._create_report_header(gs, patient_info)
            
            # ----- SECTION 2: SUVR & CENTILOID ANALYSIS -----
            # Draw a horizontal line to separate sections
            plt.subplot(gs[5:6, :])
            plt.axis('off')
            plt.plot([0.05, 0.95], [0.5, 0.5], 'k-', linewidth=1)
            
            # Section title: SUVR & Centiloid Analysis
            plt.subplot(gs[6:7, :])
            plt.axis('off')
            add_chinese_text(plt, 0.05, 0.5, "SUVR & Centiloid 分析结果", fontsize=12, fontweight='bold', ha='left')
            
            # SUVR Statistics Table - Make it taller to fill more vertical space
            plt.subplot(gs[7:17, :])  # Increased height (was 7:15)
            plt.axis('off')
            
            suvr_table_data = [
                ['Group', 'Mean', 'SD', 'Min', 'Max', 'CV%'],
                ['AD', f"{np.mean(ad_suvr):.3f}", f"{np.std(ad_suvr):.3f}", 
                 f"{np.min(ad_suvr):.3f}", f"{np.max(ad_suvr):.3f}", 
                 f"{(np.std(ad_suvr)/np.mean(ad_suvr))*100:.1f}%"],
                ['YC', f"{np.mean(yc_suvr):.3f}", f"{np.std(yc_suvr):.3f}", 
                 f"{np.min(yc_suvr):.3f}", f"{np.max(yc_suvr):.3f}", 
                 f"{(np.std(yc_suvr)/np.mean(yc_suvr))*100:.1f}%"]
            ]
            
            # Create a more compact table
            table = plt.table(cellText=suvr_table_data, loc='center', cellLoc='center',
                         colWidths=[0.12, 0.12, 0.12, 0.12, 0.12, 0.12],
                         bbox=[0.1, 0.3, 0.8, 0.6])  # Make table larger and taller (was [0.1, 0.4, 0.8, 0.5])
            
            # Style the table
            table.auto_set_font_size(False)
            table.set_fontsize(10)
            table.scale(1, 2.0)  # Make rows even taller for better vertical distribution (was 1.5)
            
            # Add heading above the table
            plt.text(0.5, 0.95, "SUVR Statistics", fontsize=12, fontweight='bold', ha='center')
            
            # Centiloid Statistics Table - Also make it taller
            plt.subplot(gs[17:27, :])  # Increased height (was 15:23)
            plt.axis('off')
            
            cl_table_data = [
                ['Group', 'Mean', 'SD', 'Min', 'Max', 'CV%'],
                ['AD', f"{np.mean(ad_cl):.1f}", f"{np.std(ad_cl):.1f}", 
                 f"{np.min(ad_cl):.1f}", f"{np.max(ad_cl):.1f}", 
                 f"{(np.std(ad_cl)/np.mean(ad_cl))*100:.1f}%" if np.mean(ad_cl) != 0 else "N/A"],
                ['YC', f"{np.mean(yc_cl):.1f}", f"{np.std(yc_cl):.1f}", 
                 f"{np.min(yc_cl):.1f}", f"{np.max(yc_cl):.1f}", 
                 f"{(np.std(yc_cl)/np.mean(yc_cl))*100:.1f}%" if np.mean(yc_cl) != 0 else "N/A"]
            ]
            
            # Create table
            table = plt.table(cellText=cl_table_data, loc='center', cellLoc='center',
                         colWidths=[0.12, 0.12, 0.12, 0.12, 0.12, 0.12],
                         bbox=[0.1, 0.3, 0.8, 0.6])  # Make table larger and taller (was [0.1, 0.4, 0.8, 0.5])
            
            # Style the table
            table.auto_set_font_size(False)
            table.set_fontsize(10)
            table.scale(1, 2.0)  # Make rows taller (was 1.5)
            
            # Add heading above the table
            plt.text(0.5, 0.95, "Centiloid Statistics", fontsize=12, fontweight='bold', ha='center')
            
            # ----- SECTION 3: PET IMAGES -----
            # Draw a horizontal line to separate sections
            plt.subplot(gs[27:28, :])  # Adjusted position (was 23:24)
            plt.axis('off')
            plt.plot([0.05, 0.95], [0.5, 0.5], 'k-', linewidth=1)
            
            # Section title: PET Images
            plt.subplot(gs[28:29, :])  # Adjusted position (was 24:25)
            plt.axis('off')
            add_chinese_text(plt, 0.05, 0.5, "PET 图像", fontsize=12, fontweight='bold', ha='left')
            
            # PET images placeholder - Make it taller to fill the page
            plt.subplot(gs[29:45, :])  # Significantly increased height (was 25:34)
            plt.axis('off')
            # Draw a light box to indicate where the images will go
            import matplotlib.patches as patches
            rect = patches.Rectangle((0.1, 0.1), 0.8, 0.8, linewidth=1, 
                                    edgecolor='gray', facecolor='whitesmoke', alpha=0.3)
            plt.gca().add_patch(rect)
            plt.text(0.5, 0.5, "PET 图像将在此显示", ha='center', va='center', fontsize=12, color='gray')
            
            # Add page number and disclaimer - Move to bottom of page
            self._add_page_footer(gs, page_number=1)
            
            # Don't use tight_layout as it can interfere with our precise layout
            # Instead, use our carefully crafted GridSpec layout
            
            # Save the report with appropriate format
            file_ext = f".{format}"
            summary_path = os.path.join(self.output_dir, f'analysis_summary_p1_{self.timestamp}{file_ext}')
            
            # Use different save parameters based on format
            if format == 'pdf':
                try:
                    plt.savefig(summary_path, dpi=300, format=format, papertype='a4', orientation='portrait')
                except Exception as pdf_err:
                    self.logger.error(f"Error saving as PDF: {str(pdf_err)}")
                    plt.savefig(summary_path, dpi=300, format=format)
            else:
                plt.savefig(summary_path, dpi=300, format=format)
                    
            plt.close(fig)
            
            # Verify the file was created
            if os.path.exists(summary_path):
                file_size = os.path.getsize(summary_path)
                self.logger.info(f"Created report page 1: {summary_path} ({file_size} bytes)")
                return summary_path
            else:
                self.logger.error(f"Failed to create report page 1: File not found: {summary_path}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error creating summary report page 1: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None

    def _create_report_page2(self, ad_suvr, yc_suvr, ad_cl, yc_cl, file_info=None, patient_info=None, format='pdf'):
        """Create second page of the report with charts"""
        try:
            # Set exact A4 size in portrait orientation - 210x297mm (8.27x11.69 inches)
            fig = plt.figure(figsize=(8.27, 11.69), dpi=100)
            
            # Ensure content fills the entire page vertically
            fig.subplots_adjust(left=0.1, right=0.9, top=0.95, bottom=0.05, hspace=0.4)
            
            # Use a GridSpec with more rows for better vertical distribution
            gs = plt.GridSpec(50, 2)  # Increased from 40 to 50 rows
            
            # ----- REPORT HEADER -----
            # Create and apply the header (common function for both pages)
            self._create_report_header(gs, patient_info)
            
            # ----- SECTION 2: SUVR & CENTILOID ANALYSIS CHARTS -----
            # Draw a horizontal line to separate sections
            plt.subplot(gs[5:6, :])
            plt.axis('off')
            plt.plot([0.05, 0.95], [0.5, 0.5], 'k-', linewidth=1)
            
            # Section title: SUVR & Centiloid Analysis
            plt.subplot(gs[6:7, :])
            plt.axis('off')
            add_chinese_text(plt, 0.05, 0.5, "SUVR & Centiloid 分析图表", fontsize=12, fontweight='bold', ha='left')
            
            # Make charts larger to fill more vertical space
            # SUVR Distribution - Larger chart
            plt.subplot(gs[8:19, 0])  # Increased height (was 9:16)
            plt.hist(ad_suvr, bins=10, alpha=0.7, color='red', label='AD')
            plt.hist(yc_suvr, bins=10, alpha=0.7, color='blue', label='YC')
            plt.xlabel('SUVR Value')
            plt.ylabel('Frequency')
            plt.title('SUVR Distribution')
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            # Centiloid Distribution - Larger chart
            plt.subplot(gs[8:19, 1])  # Increased height (was 9:16)
            plt.hist(ad_cl, bins=10, alpha=0.7, color='red', label='AD')
            plt.hist(yc_cl, bins=10, alpha=0.7, color='blue', label='YC')
            plt.xlabel('Centiloid Value')
            plt.ylabel('Frequency')
            plt.title('Centiloid Distribution')
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            # SUVR Boxplot - Larger chart
            plt.subplot(gs[20:31, 0])  # Increased height and moved down (was 18:25)
            bp = plt.boxplot([ad_suvr, yc_suvr], notch=True, patch_artist=True, 
                          labels=['AD', 'YC'])
            
            # Customize box colors
            for box, color in zip(bp['boxes'], ['red', 'blue']):
                box.set(facecolor=color, alpha=0.6)
                
            plt.ylabel('SUVR Value')
            plt.title('SUVR by Group')
            plt.grid(True, axis='y', alpha=0.3)
            
            # Centiloid Boxplot - Larger chart
            plt.subplot(gs[20:31, 1])  # Increased height and moved down (was 18:25)
            bp = plt.boxplot([ad_cl, yc_cl], notch=True, patch_artist=True, 
                          labels=['AD', 'YC'])
            
            # Customize box colors
            for box, color in zip(bp['boxes'], ['red', 'blue']):
                box.set(facecolor=color, alpha=0.6)
                
            plt.ylabel('Centiloid Value')
            plt.title('Centiloid by Group')
            plt.grid(True, axis='y', alpha=0.3)

            # Add a third row of plots to fill the vertical space
            # SUVR Density Plot
            plt.subplot(gs[32:43, 0])  # New plot to fill space
            try:
                from scipy import stats as scipy_stats
                x_range = np.linspace(min(min(ad_suvr), min(yc_suvr)), max(max(ad_suvr), max(yc_suvr)), 1000)
                ad_kde = scipy_stats.gaussian_kde(ad_suvr)
                yc_kde = scipy_stats.gaussian_kde(yc_suvr)
                plt.plot(x_range, ad_kde(x_range), 'r-', linewidth=2, label='AD')
                plt.plot(x_range, yc_kde(x_range), 'b-', linewidth=2, label='YC')
                plt.fill_between(x_range, ad_kde(x_range), alpha=0.3, color='red')
                plt.fill_between(x_range, yc_kde(x_range), alpha=0.3, color='blue')
                plt.xlabel('SUVR Value')
                plt.ylabel('Density')
                plt.title('SUVR Density Distribution')
                plt.legend()
                plt.grid(True, alpha=0.3)
            except Exception as e:
                # If density plot fails, show a simple bar chart
                self.logger.warning(f"Could not create density plot: {e}, falling back to bar chart")
                plt.bar(['AD', 'YC'], [np.mean(ad_suvr), np.mean(yc_suvr)], 
                       yerr=[np.std(ad_suvr), np.std(yc_suvr)],
                       color=['red', 'blue'], alpha=0.7)
                plt.ylabel('Mean SUVR (±SD)')
                plt.title('SUVR Comparison')
                plt.grid(True, axis='y', alpha=0.3)
            
            # Centiloid Density Plot
            plt.subplot(gs[32:43, 1])  # New plot to fill space
            try:
                x_range = np.linspace(min(min(ad_cl), min(yc_cl)), max(max(ad_cl), max(yc_cl)), 1000)
                ad_kde = scipy_stats.gaussian_kde(ad_cl)
                yc_kde = scipy_stats.gaussian_kde(yc_cl)
                plt.plot(x_range, ad_kde(x_range), 'r-', linewidth=2, label='AD')
                plt.plot(x_range, yc_kde(x_range), 'b-', linewidth=2, label='YC')
                plt.fill_between(x_range, ad_kde(x_range), alpha=0.3, color='red')
                plt.fill_between(x_range, yc_kde(x_range), alpha=0.3, color='blue')
                plt.xlabel('Centiloid Value')
                plt.ylabel('Density')
                plt.title('Centiloid Density Distribution')
                plt.legend()
                plt.grid(True, alpha=0.3)
            except Exception as e:
                # If density plot fails, show a simple bar chart
                self.logger.warning(f"Could not create density plot: {e}, falling back to bar chart")
                plt.bar(['AD', 'YC'], [np.mean(ad_cl), np.mean(yc_cl)], 
                       yerr=[np.std(ad_cl), np.std(yc_cl)],
                       color=['red', 'blue'], alpha=0.7)
                plt.ylabel('Mean Centiloid (±SD)')
                plt.title('Centiloid Comparison')
                plt.grid(True, axis='y', alpha=0.3)
                
            # Add page number and disclaimer at the bottom
            self._add_page_footer(gs, page_number=2)
            
            # Don't use tight_layout as it can interfere with our precise layout
            
            # Save the report with appropriate format
            file_ext = f".{format}"
            summary_path = os.path.join(self.output_dir, f'analysis_summary_p2_{self.timestamp}{file_ext}')
            
            # Use different save parameters based on format
            if format == 'pdf':
                try:
                    plt.savefig(summary_path, dpi=300, format=format, papertype='a4', orientation='portrait')
                except Exception as pdf_err:
                    self.logger.error(f"Error saving as PDF: {str(pdf_err)}")
                    plt.savefig(summary_path, dpi=300, format=format)
            else:
                plt.savefig(summary_path, dpi=300, format=format)
                    
            plt.close(fig)
            
            # Verify the file was created
            if os.path.exists(summary_path):
                file_size = os.path.getsize(summary_path)
                self.logger.info(f"Created report page 2: {summary_path} ({file_size} bytes)")
                return summary_path
            else:
                self.logger.error(f"Failed to create report page 2: File not found: {summary_path}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error creating summary report page 2: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None

    def _add_page_footer(self, gs, page_number=1):
        """Add footer with disclaimer and reviewer signature to report pages"""
        # Move footer elements to the bottom of the page
        # Disclaimer at the bottom
        plt.subplot(gs[45:46, :])  # Moved further down (was 34:35)
        plt.axis('off')
        disclaimer_text = "本报告仅供参考，不用于最终的临床诊断"
        add_chinese_text(plt, 0.5, 0.5, disclaimer_text, fontsize=10, style='italic', ha='center')
        
        # Reviewer signature line - moved completely to the right and down
        plt.subplot(gs[47:48, :])  # Moved further down (was 36:37)
        plt.axis('off')
        reviewer_text = "审阅医生:"  # Added colon after the text
        # Position the reviewer text further right
        add_chinese_text(plt, 0.9, 0.5, reviewer_text, fontsize=10, ha='right')
        
        # Add page number
        plt.text(0.05, 0.3, f"第{page_number}页", fontsize=9, ha='left')

    def _create_emergency_report(self, ad_suvr, yc_suvr, ad_cl, yc_cl, additional_info=None):
        """Create a minimal emergency report when normal report generation fails"""
        try:
            # Create a simple figure with just the essential stats
            plt.figure(figsize=(10, 8))
            
            # Title
            plt.title("Analysis Results (Emergency Report)", fontsize=16, color='darkred')
            
            # Create summary text
            text_content = [
                "ANALYSIS SUMMARY (Emergency Report)",
                "--------------------------------",
                f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "",
                "AD Group SUVR Statistics:",
                f"  Count: {len(ad_suvr)}",
                f"  Mean: {np.mean(ad_suvr):.3f}",
                f"  Std Dev: {np.std(ad_suvr):.3f}",
                f"  Min: {np.min(ad_suvr):.3f}",
                f"  Max: {np.max(ad_suvr):.3f}",
                "",
                "YC Group SUVR Statistics:",
                f"  Count: {len(yc_suvr)}",
                f"  Mean: {np.mean(yc_suvr):.3f}",
                f"  Std Dev: {np.std(yc_suvr):.3f}",
                f"  Min: {np.min(yc_suvr):.3f}",
                f"  Max: {np.max(yc_suvr):.3f}",
                "",
                "AD Group CL Statistics:",
                f"  Mean: {np.mean(ad_cl):.1f}",
                f"  Std Dev: {np.std(ad_cl):.1f}",
                "",
                "YC Group CL Statistics:",
                f"  Mean: {np.mean(yc_cl):.1f}",
                f"  Std Dev: {np.std(yc_cl):.1f}",
                "",
                "Note: This is an emergency report generated when",
                "the standard report generation failed."
            ]
            
            # Add error information if provided
            if additional_info:
                text_content.extend(["", "Additional Information:", additional_info])
            
            # Display text
            plt.text(0.05, 0.95, '\n'.join(text_content), fontsize=12, 
                     va='top', ha='left', family='monospace',
                     transform=plt.gca().transAxes,
                     bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.5))
            
            # Add a small reference plot if possible
            try:
                if len(ad_suvr) > 0 and len(yc_suvr) > 0:
                    # Add small histogram in bottom right
                    ax_hist = plt.axes([0.55, 0.15, 0.4, 0.3])
                    ax_hist.hist([ad_suvr, yc_suvr], label=['AD', 'YC'], alpha=0.7, bins=10)
                    ax_hist.set_title('SUVR Distribution')
                    ax_hist.legend()
            except Exception:
                # If plotting fails, just continue
                pass
                
            # Turn off main axes
            plt.gca().axis('off')
            
            # Create a timestamped filename for uniqueness
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            emergency_path = os.path.join(self.output_dir, f'emergency_report_{timestamp}.png')
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(emergency_path), exist_ok=True)
            
            # Save to file, falling back to different formats if needed
            try:
                plt.savefig(emergency_path, dpi=100, bbox_inches='tight')
            except Exception as e:
                self.logger.warning(f"Failed to save PNG, trying PDF: {str(e)}")
                emergency_path = emergency_path.replace('.png', '.pdf')
                try:
                    plt.savefig(emergency_path, dpi=100, bbox_inches='tight')
                except Exception as e2:
                    self.logger.warning(f"Failed to save PDF, using SVG: {str(e2)}")
                    emergency_path = emergency_path.replace('.pdf', '.svg')
                    plt.savefig(emergency_path, dpi=100, bbox_inches='tight')
            
            plt.close()
            
            # Verify file was created
            if os.path.exists(emergency_path):
                file_size = os.path.getsize(emergency_path)
                self.logger.info(f"Created emergency report: {emergency_path} ({file_size} bytes)")
                return emergency_path
            else:
                self.logger.error(f"Failed to create emergency report - file not found")
                return None
            
        except Exception as e:
            self.logger.error(f"Failed to create emergency report: {str(e)}")
            return None

    def _create_report_header(self, gs, patient_info):
        """Create the common header for report pages"""
        # Title at the top of the report
        plt.subplot(gs[0:2, :])
        plt.axis('off')
        
        # First line title - huashan hospital text
        title_text_line1 = "复旦大学附属华山医院核医学/PET中心"
        add_chinese_text(plt, 0.5, 0.8, title_text_line1, fontsize=16, fontweight='bold', ha='center')
        
        # Second line title - beta-amyloid text, moved further down
        title_text_line2 = "β-淀粉样蛋白PET报告"
        add_chinese_text(plt, 0.5, 0.2, title_text_line2, fontsize=14, fontweight='bold', ha='center')
        
        # ----- SECTION 1: PATIENT INFORMATION -----
        # Draw a horizontal line to separate sections
        plt.subplot(gs[2:3, :])
        plt.axis('off')
        plt.plot([0.05, 0.95], [0.5, 0.5], 'k-', linewidth=1)
        
        # Section title: Patient Information
        plt.subplot(gs[3:4, :])
        plt.axis('off')
        add_chinese_text(plt, 0.05, 0.5, "患者信息", fontsize=12, fontweight='bold', ha='left')
        
        # Patient info content with vertical centering
        plt.subplot(gs[4:5, :])
        plt.axis('off')
        
        if patient_info:
            name = patient_info.get('name', 'N/A')
            gender = patient_info.get('gender', 'N/A')
            pet_id = patient_info.get('pet_id', 'N/A')
            
            # Create a light orange background for the patient info
            import matplotlib.patches as patches
            rect = patches.Rectangle((0.05, 0.2), 0.9, 0.6, linewidth=1, 
                                    edgecolor='orange', facecolor='bisque', alpha=0.2)
            plt.gca().add_patch(rect)
            
            # Add patient information text centered vertically
            add_chinese_text(plt, 0.15, 0.5, f"姓名: {name}", fontsize=11, ha='left', va='center')
            add_chinese_text(plt, 0.5, 0.5, f"性别: {gender}", fontsize=11, ha='center', va='center')
            add_chinese_text(plt, 0.85, 0.5, f"PET检查号: {pet_id}", fontsize=11, ha='right', va='center')

    def plot_bland_altman(self, suvr_std, suvr_calc, cl_std, cl_calc):
        """
        Create Bland-Altman plots to assess agreement between standard and calculated values
        
        Args:
            suvr_std: Standard SUVR values
            suvr_calc: Calculated SUVR values
            cl_std: Standard CL values
            cl_calc: Calculated CL values
            
        Returns:
            str: Path to saved figure
        """
        try:
            # Create a figure with two subplots side by side
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
            
            # Process arrays to ensure equal lengths and valid values
            if len(suvr_std) != len(suvr_calc):
                min_len = min(len(suvr_std), len(suvr_calc))
                self.logger.warning(f"Bland-Altman: Trimming SUVR arrays to match ({min_len} points)")
                suvr_std = suvr_std[:min_len]
                suvr_calc = suvr_calc[:min_len]
                
            if len(cl_std) != len(cl_calc):
                min_len = min(len(cl_std), len(cl_calc))
                self.logger.warning(f"Bland-Altman: Trimming CL arrays to match ({min_len} points)")
                cl_std = cl_std[:min_len]
                cl_calc = cl_calc[:min_len]
                
            # Remove any NaN values
            suvr_mask = ~(np.isnan(suvr_std) | np.isnan(suvr_calc))
            suvr_std_clean = suvr_std[suvr_mask]
            suvr_calc_clean = suvr_calc[suvr_mask]
            
            cl_mask = ~(np.isnan(cl_std) | np.isnan(cl_calc))
            cl_std_clean = cl_std[cl_mask]
            cl_calc_clean = cl_calc[cl_mask]
            
            # Create Bland-Altman for SUVR
            if len(suvr_std_clean) > 2 and len(suvr_calc_clean) > 2:
                # Calculate mean and difference for each point
                means_suvr = (suvr_std_clean + suvr_calc_clean) / 2
                diffs_suvr = suvr_calc_clean - suvr_std_clean
                
                # Calculate statistics
                mean_diff_suvr = np.mean(diffs_suvr)
                std_diff_suvr = np.std(diffs_suvr)
                upper_loa_suvr = mean_diff_suvr + 1.96 * std_diff_suvr
                lower_loa_suvr = mean_diff_suvr - 1.96 * std_diff_suvr
                
                # Create plot
                ax1.scatter(means_suvr, diffs_suvr, alpha=0.7)
                ax1.axhline(mean_diff_suvr, color='k', linestyle='-', label=f'Mean: {mean_diff_suvr:.3f}')
                ax1.axhline(upper_loa_suvr, color='r', linestyle='--', label=f'+1.96 SD: {upper_loa_suvr:.3f}')
                ax1.axhline(lower_loa_suvr, color='r', linestyle='--', label=f'-1.96 SD: {lower_loa_suvr:.3f}')
                
                # Labels and title
                ax1.set_xlabel('Mean of Standard and Calculated SUVR')
                ax1.set_ylabel('Difference (Calculated - Standard)')
                ax1.set_title('Bland-Altman Plot: SUVR')
                ax1.legend(loc='best')
                ax1.grid(True, alpha=0.3)
            else:
                ax1.text(0.5, 0.5, 'Insufficient data for Bland-Altman plot', 
                        ha='center', va='center', transform=ax1.transAxes)
                ax1.set_title('SUVR: Not enough valid data points')
                
            # Create Bland-Altman for CL
            if len(cl_std_clean) > 2 and len(cl_calc_clean) > 2:
                # Calculate mean and difference for each point
                means_cl = (cl_std_clean + cl_calc_clean) / 2
                diffs_cl = cl_calc_clean - cl_std_clean
                
                # Calculate statistics
                mean_diff_cl = np.mean(diffs_cl)
                std_diff_cl = np.std(diffs_cl)
                upper_loa_cl = mean_diff_cl + 1.96 * std_diff_cl
                lower_loa_cl = mean_diff_cl - 1.96 * std_diff_cl
                
                # Create plot
                ax2.scatter(means_cl, diffs_cl, alpha=0.7, color='green')
                ax2.axhline(mean_diff_cl, color='k', linestyle='-', label=f'Mean: {mean_diff_cl:.3f}')
                ax2.axhline(upper_loa_cl, color='r', linestyle='--', label=f'+1.96 SD: {upper_loa_cl:.3f}')
                ax2.axhline(lower_loa_cl, color='r', linestyle='--', label=f'-1.96 SD: {lower_loa_cl:.3f}')
                
                # Labels and title
                ax2.set_xlabel('Mean of Standard and Calculated CL')
                ax2.set_ylabel('Difference (Calculated - Standard)')
                ax2.set_title('Bland-Altman Plot: Centiloid')
                ax2.legend(loc='best')
                ax2.grid(True, alpha=0.3)
            else:
                ax2.text(0.5, 0.5, 'Insufficient data for Bland-Altman plot', 
                        ha='center', va='center', transform=ax2.transAxes)
                ax2.set_title('Centiloid: Not enough valid data points')
            
            # Adjust layout and save
            try:
                plt.tight_layout(pad=1.0, h_pad=1.0, w_pad=1.0)
            except Exception as e:
                self.logger.warning(f"Layout adjustment error in Bland-Altman plot: {str(e)}")
            
            # Save the figure
            ba_path = os.path.join(self.output_dir, f'bland_altman_{self.timestamp}.png')
            try:
                fig.savefig(ba_path, dpi=300, bbox_inches='tight')
                plt.close(fig)
                return ba_path
            except Exception as e:
                self.logger.error(f"Error saving Bland-Altman plot: {str(e)}")
                # Try saving with different format if PNG fails
                try:
                    ba_path = ba_path.replace('.png', '.pdf')
                    fig.savefig(ba_path, dpi=300)
                    plt.close(fig)
                    return ba_path
                except Exception as e2:
                    self.logger.error(f"Error saving Bland-Altman plot as PDF: {str(e2)}")
                    plt.close(fig)
                    return None
                
        except Exception as e:
            self.logger.error(f"Error creating Bland-Altman plots: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None
