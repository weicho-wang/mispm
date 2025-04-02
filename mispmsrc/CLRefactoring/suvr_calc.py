import numpy as np
import nibabel as nib
from scipy.ndimage import zoom
import logging
import os

class SUVRCalculator:
    """SUVR (Standardized Uptake Value Ratio) calculator class."""
    
    def __init__(self):
        self.roi_img = None
        self.ref_img = None
        self.roi_affine = None
        self.ref_affine = None
        self.logger = logging.getLogger(__name__)
        
    def load_masks(self, roi_path, ref_path):
        """load ROI and reference masks"""
        # Load mask data and affine transforms
        self.logger.info(f"Loading ROI mask from {roi_path}")
        roi_nii = nib.load(roi_path)
        
        self.logger.info(f"Loading reference mask from {ref_path}")
        ref_nii = nib.load(ref_path)
        
        self.roi_img = roi_nii.get_fdata()
        self.ref_img = ref_nii.get_fdata()
        
        self.roi_affine = roi_nii.affine
        self.ref_affine = ref_nii.affine
        
        # calculate the number of non-zero voxels in the masks
        self.num_roi = np.count_nonzero(self.roi_img)
        self.num_ref = np.count_nonzero(self.ref_img)
        
        self.logger.info(f"ROI mask contains {self.num_roi} non-zero voxels")
        self.logger.info(f"Reference mask contains {self.num_ref} non-zero voxels")
    
    def _resample_mask(self, mask_img, target_shape):
        """Resample the mask image to match the target shape using nearest neighbor interpolation."""
        if mask_img.shape == target_shape:
            return mask_img
            
        # Calculate zoom factors for each dimension
        zoom_factors = []
        for target, current in zip(target_shape, mask_img.shape):
            if current == 0:
                zoom_factors.append(1)  # Avoid division by zero
            else:
                zoom_factors.append(float(target) / current)
                
        # Ensure zoom_factors is a list, not an int
        if not isinstance(zoom_factors, list):
            self.logger.warning(f"Invalid zoom_factors: {zoom_factors}, using default [1,1,1]")
            zoom_factors = [1, 1, 1]
        
        # Add any missing dimensions
        while len(zoom_factors) < 3:
            zoom_factors.append(1)
        
        try:
            # Resample using scipy.ndimage.zoom with nearest neighbor interpolation
            resampled = zoom(mask_img, zoom_factors[:3], order=0, mode='nearest')
            
            # Ensure output shape matches target
            pad_width = []
            for target_dim, resampled_dim in zip(target_shape, resampled.shape):
                if target_dim > resampled_dim:
                    pad_width.append((0, target_dim - resampled_dim))
                else:
                    pad_width.append((0, 0))
            
            # Pad if necessary
            if any(p[1] > 0 for p in pad_width):
                resampled = np.pad(resampled, pad_width, mode='constant', constant_values=0)
                
            return resampled
        except Exception as e:
            self.logger.error(f"Error in mask resampling: {str(e)}")
            # If resampling fails, return the original mask
            return mask_img

    def calculate(self, pet_filepaths):
        """Calculate SUVR values"""
        if self.roi_img is None or self.ref_img is None:
            raise ValueError("ROI and reference masks must be loaded first")
            
        if not pet_filepaths:
            raise ValueError("No PET files provided")
            
        suvr_values = []
        processed_files = 0
        errors = []
        filtered_files = []  # Track files that were processed successfully
        
        self.logger.info(f"Starting SUVR calculation on {len(pet_filepaths)} files")
        
        for filepath in pet_filepaths:
            try:
                # Extract base filename to prevent processing duplicates
                base_name = os.path.basename(filepath)
                
                # Validate file exists
                if not os.path.exists(filepath):
                    errors.append(f"File not found: {filepath}")
                    continue
                    
                # Load PET image
                self.logger.info(f"Processing {filepath}")
                pet_nii = nib.load(filepath)
                pet_img = pet_nii.get_fdata()
                
                # Check image dimensions
                if pet_img.size == 0:
                    errors.append(f"Empty image data in {filepath}")
                    continue
                
                # Ensure PET image is 3D
                if len(pet_img.shape) > 3:
                    self.logger.info(f"Converting 4D image to 3D in {filepath}")
                    pet_img = pet_img[:,:,:,0]
                
                # Handle NaN values
                nan_count = np.sum(np.isnan(pet_img))
                if nan_count > 0:
                    self.logger.warning(f"Found {nan_count} NaN values in {filepath} ({nan_count/pet_img.size:.2%} of voxels)")
                    # Replace NaNs with zeros
                    pet_img = np.nan_to_num(pet_img, 0)
                
                # Resample masks if dimensions don't match
                roi_resampled = self.roi_img
                ref_resampled = self.ref_img
                
                if self.roi_img.shape != pet_img.shape:
                    try:
                        roi_resampled = self._resample_mask(self.roi_img, pet_img.shape)
                    except Exception as e:
                        errors.append(f"ROI mask resampling error: {str(e)}")
                        continue
                
                if self.ref_img.shape != pet_img.shape:
                    try:
                        ref_resampled = self._resample_mask(self.ref_img, pet_img.shape)
                    except Exception as e:
                        errors.append(f"Reference mask resampling error: {str(e)}")
                        continue
                
                # Calculate ROI region values
                roi_voxels = pet_img * roi_resampled
                ref_voxels = pet_img * ref_resampled
                
                # Count non-zero voxels in masks (after multiplication)
                num_roi = np.count_nonzero(roi_voxels)
                num_ref = np.count_nonzero(ref_voxels)
                
                # Check if there are enough non-zero voxels after multiplication
                min_voxels = 10  # Minimum number of voxels considered valid
                if num_roi < min_voxels:
                    self.logger.warning(f"Too few ROI voxels ({num_roi}) in {filepath}")
                    if num_roi == 0:
                        errors.append(f"No ROI voxels in {filepath}")
                        continue
                
                if num_ref < min_voxels:
                    self.logger.warning(f"Too few reference voxels ({num_ref}) in {filepath}")
                    if num_ref == 0:
                        errors.append(f"No reference voxels in {filepath}")
                        continue
                
                # Calculate sums with robust handling
                roi_sum = np.sum(roi_voxels)
                ref_sum = np.sum(ref_voxels)
                
                # Handle edge cases with explicit error checking
                if ref_sum <= 0:
                    self.logger.warning(f"Reference region sum is zero or negative: {ref_sum}")
                    # Try a different approach - use mean value instead of sum
                    ref_mean = np.mean(pet_img[ref_resampled > 0]) if np.any(ref_resampled > 0) else 0
                    if ref_mean <= 0:
                        errors.append(f"Zero or negative reference mean in {filepath}")
                        continue
                    else:
                        self.logger.info(f"Using reference mean ({ref_mean}) instead of sum")
                        suv_roi = np.mean(pet_img[roi_resampled > 0]) if np.any(roi_resampled > 0) else 0
                        suv_ref = ref_mean
                else:
                    # Calculate average values
                    suv_roi = roi_sum / max(num_roi, 1)  # Avoid division by zero
                    suv_ref = ref_sum / max(num_ref, 1)  # Avoid division by zero
                
                # Calculate SUVR with thorough validation
                if suv_ref > 0:
                    suvr = suv_roi / suv_ref  # calculate SUVR
                else:
                    self.logger.warning(f"Reference SUV is zero, cannot calculate SUVR for {filepath}")
                    errors.append(f"Zero reference SUV in {filepath}")
                    continue
                
                # Ensure SUVR is finite and in a reasonable range
                if not np.isfinite(suvr):
                    errors.append(f"Invalid SUVR value in {filepath}")
                    continue
                    
                # Validate SUVR value is within reasonable bounds (0.5 to 3.0 for PiB)
                if not (0.5 <= suvr <= 3.0):
                    self.logger.warning(f"SUVR value ({suvr:.4f}) out of typical range for {filepath}")
                
                suvr_values.append(suvr)  # Store SUVR value
                filtered_files.append(filepath)  # Add to successful files
                processed_files += 1
                self.logger.info(f"Processed {filepath}: SUVR = {suvr:.4f}, ROI voxels: {num_roi}, REF voxels: {num_ref}")
                
            except Exception as e:
                errors.append(f"Error processing {filepath}: {str(e)}")
                self.logger.error(f"Error processing {filepath}: {str(e)}", exc_info=True)
                continue
        
        # Provide comprehensive error reporting
        if not suvr_values:
            error_msg = f"No valid SUVR values could be calculated from {len(pet_filepaths)} files"
            self.logger.error(error_msg)
            if errors:
                error_details = "\n".join(errors[:10])
                if len(errors) > 10:
                    error_details += f"\n...and {len(errors) - 10} more errors"
                self.logger.error(f"Error details:\n{error_details}")
            raise ValueError(error_msg)
        
        # Log success statistics with more detail
        self.logger.info(f"Successfully processed {processed_files}/{len(pet_filepaths)} files ({processed_files/len(pet_filepaths):.1%})")
        if errors:
            self.logger.warning(f"Encountered {len(errors)} errors during processing")
        
        # Return both the SUVR values and the list of successfully processed files
        return np.array(suvr_values), filtered_files