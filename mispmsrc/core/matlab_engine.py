#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import logging
import matlab.engine
import numpy as np
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
import tqdm

class MatlabEngine(QObject):
    """
    MATLAB Engine wrapper for Python to interact with SPM MATLAB functions.
    Implements singleton pattern for global access to the MATLAB engine.
    """
    # Signals for async operations and notifications
    engine_started = pyqtSignal()
    engine_error = pyqtSignal(str)
    operation_progress = pyqtSignal(str, int)  # message, progress percentage
    operation_completed = pyqtSignal(str, bool)  # message, success status
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MatlabEngine, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        super(MatlabEngine, self).__init__()
        self.logger = logging.getLogger(__name__)
        self._engine = None
        self._spm_path = None
        self._initialized = True
        
    def start_engine(self, spm_path=None, timeout=None):
        """
        Start the MATLAB engine and initialize SPM
        
        Args:
            spm_path: Path to SPM installation directory
            timeout: Timeout for starting the MATLAB engine
        
        Returns:
            bool: True if successful, False otherwise
        """
        self.logger.info("Starting MATLAB engine...")
        
        try:
            with tqdm.tqdm(total=100, desc="Starting MATLAB engine") as pbar:
                self._engine = matlab.engine.start_matlab()
                pbar.update(20)
                
                # Wait for the engine to start with a timeout
                if timeout:
                    self._engine.eval("disp('MATLAB engine started')", nargout=0)
                pbar.update(20)
                
                # Set SPM path (default to parent directory if not specified)
                if spm_path is None:
                    # Assuming SPM is in the parent directory of the current script
                    self._spm_path = os.path.abspath(os.path.join(
                        os.path.dirname(os.path.dirname(__file__)), '..'
                    ))
                else:
                    self._spm_path = spm_path
                pbar.update(20)
                    
                self.logger.info(f"Using SPM path: {self._spm_path}")
                
                # Add SPM to MATLAB path
                self._engine.addpath(self._spm_path)
                self._engine.addpath(os.path.join(self._spm_path, 'toolbox'))
                pbar.update(20)
                
                # Initialize SPM
                self._engine.eval("spm('defaults', 'PET');", nargout=0)
                self._engine.eval("spm_jobman('initcfg');", nargout=0)
                pbar.update(20)
                
                self.logger.info("MATLAB engine started successfully")
                self.engine_started.emit()
                return True
                
        except Exception as e:
            error_msg = f"Failed to start MATLAB engine: {str(e)}"
            self.logger.error(error_msg)
            self.engine_error.emit(error_msg)
            return False
    
    def stop_engine(self):
        """
        Stop the MATLAB engine
        
        Returns:
            bool: True if successful, False otherwise
        """
        if self._engine is None:
            self.logger.warning("MATLAB engine is not running")
            return True
            
        try:
            self._engine.quit()
            self._engine = None
            self.logger.info("MATLAB engine stopped successfully")
            return True
        except Exception as e:
            error_msg = f"Failed to stop MATLAB engine: {str(e)}"
            self.logger.error(error_msg)
            self.engine_error.emit(error_msg)
            return False
    
    def is_running(self):
        """
        Check if the MATLAB engine is running
        
        Returns:
            bool: True if running, False otherwise
        """
        return self._engine is not None
    
    def call_function(self, func_name, *args, **kwargs):
        """
        Call a MATLAB function
        
        Args:
            func_name: Name of the MATLAB function to call
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
        
        Returns:
            The result of the MATLAB function call
        
        Raises:
            RuntimeError: If MATLAB engine is not running
        """
        if not self.is_running():
            raise RuntimeError("MATLAB engine is not running")
            
        self.logger.info(f"Calling MATLAB function: {func_name}")
        
        try:
            # Get the function from the MATLAB engine
            func = getattr(self._engine, func_name)
            
            # Call the function
            result = func(*args, **kwargs)
            return result
            
        except Exception as e:
            error_msg = f"Error calling MATLAB function {func_name}: {str(e)}"
            self.logger.error(error_msg)
            self.engine_error.emit(error_msg)
            raise
    
    def convert_dicom_to_nifti(self, dicom_dir, output_dir=None):
        """
        Convert DICOM files to NIFTI format using SPM
        
        Args:
            dicom_dir: Directory containing DICOM files
            output_dir: Output directory for NIFTI files (default: same as dicom_dir)
        
        Returns:
            list: List of paths to the created NIFTI files
        """
        if not output_dir:
            output_dir = dicom_dir
            
        self.logger.info(f"Converting DICOM files from {dicom_dir} to NIFTI format")
        self.operation_progress.emit("Starting DICOM to NIFTI conversion...", 0)
        
        try:
            # Get DICOM files
            self._engine.eval(f"dicom_files = spm_select('FPList', '{dicom_dir}', '.*');", nargout=0)
            
            # Convert DICOM files to NIFTI
            self._engine.eval("dicom_headers = spm_dicom_headers(dicom_files);", nargout=0)
            self.operation_progress.emit("Processing DICOM headers...", 30)
            
            # Use 'patid' as RootDirectory to organize files by patient ID
            self._engine.eval(f"nii_files = spm_dicom_convert(dicom_headers, 'all', 'patid', 'nii', '{output_dir}', true);", nargout=0)
            self.operation_progress.emit("Converting files...", 80)
            
            # Get the paths of the created NIFTI files
            nii_files = self._engine.eval("nii_files.files;")
            
            # Convert MATLAB cell array to Python list
            nii_files_list = []
            for i in range(len(nii_files)):
                nii_files_list.append(nii_files[i])
                
            self.operation_progress.emit("Conversion completed", 100)
            self.operation_completed.emit(f"Successfully converted {len(nii_files_list)} files", True)
            
            return nii_files_list
            
        except Exception as e:
            error_msg = f"Error in DICOM to NIFTI conversion: {str(e)}"
            self.logger.error(error_msg)
            self.engine_error.emit(error_msg)
            self.operation_completed.emit("Conversion failed", False)
            return []
            
    def display_image(self, image_file):
        """
        Display a NIFTI image using spm_image and spm_orthviews
        
        Args:
            image_file: Path to the NIFTI image file
        
        Returns:
            bool: True if successful, False otherwise
        """
        self.logger.info(f"Displaying image: {image_file}")
        
        try:
            # Display the image using spm_image
            self._engine.eval(f"spm_image('Display', '{image_file}');", nargout=0)
            return True
            
        except Exception as e:
            error_msg = f"Error displaying image: {str(e)}"
            self.logger.error(error_msg)
            self.engine_error.emit(error_msg)
            return False
            
    def coregister_images(self, ref_image, source_image, cost_function="nmi"):
        """
        Coregister images using spm_coreg and spm_run_coreg
        
        Args:
            ref_image: Path to the reference image file
            source_image: Path to the source image file to be coregistered
            cost_function: Cost function to use for coregistration (mi, nmi, ecc, ncc)
        
        Returns:
            bool: True if successful, False otherwise
        """
        self.logger.info(f"Coregistering {source_image} to {ref_image} using cost function {cost_function}")
        self.operation_progress.emit("Starting coregistration...", 0)
        
        try:
            # Setup job structure for coregistration
            self._engine.eval("matlabbatch = {};", nargout=0)
            self._engine.eval("matlabbatch{1}.spm.spatial.coreg.estwrite.ref = {};", nargout=0)
            self._engine.eval("matlabbatch{1}.spm.spatial.coreg.estwrite.source = {};", nargout=0)
            self._engine.eval(f"matlabbatch{{1}}.spm.spatial.coreg.estwrite.ref = {{'{ref_image}'}};", nargout=0)
            self._engine.eval(f"matlabbatch{{1}}.spm.spatial.coreg.estwrite.source = {{'{source_image}'}};", nargout=0)
            
            # Set default parameters
            self._engine.eval("matlabbatch{1}.spm.spatial.coreg.estwrite.other = {''};", nargout=0)
            self._engine.eval(f"matlabbatch{{1}}.spm.spatial.coreg.estwrite.eoptions.cost_fun = '{cost_function}';", nargout=0)
            self._engine.eval("matlabbatch{1}.spm.spatial.coreg.estwrite.eoptions.sep = [4 2];", nargout=0)
            self._engine.eval("matlabbatch{1}.spm.spatial.coreg.estwrite.eoptions.tol = [0.02 0.02 0.02 0.001 0.001 0.001 0.01 0.01 0.01 0.001 0.001 0.001];", nargout=0)
            self._engine.eval("matlabbatch{1}.spm.spatial.coreg.estwrite.eoptions.fwhm = [7 7];", nargout=0)
            self._engine.eval("matlabbatch{1}.spm.spatial.coreg.estwrite.roptions.interp = 4;", nargout=0)
            self._engine.eval("matlabbatch{1}.spm.spatial.coreg.estwrite.roptions.wrap = [0 0 0];", nargout=0)
            self._engine.eval("matlabbatch{1}.spm.spatial.coreg.estwrite.roptions.mask = 0;", nargout=0)
            self._engine.eval("matlabbatch{1}.spm.spatial.coreg.estwrite.roptions.prefix = 'r';", nargout=0)
            
            self.operation_progress.emit("Executing coregistration...", 30)
            
            # Run coregistration
            self._engine.eval("spm_jobman('run', matlabbatch);", nargout=0)
            
            self.operation_progress.emit("Coregistration completed", 100)
            self.operation_completed.emit("Coregistration completed successfully", True)
            
            return True
            
        except Exception as e:
            error_msg = f"Error in coregistration: {str(e)}"
            self.logger.error(error_msg)
            self.engine_error.emit(error_msg)
            self.operation_completed.emit("Coregistration failed", False)
            return False

    def _validate_spm_paths(self, source_path, template_path=None):
        """Validate paths for SPM operations"""
        if not os.path.exists(source_path):
            raise ValueError(f"Source image not found: {source_path}")
        if template_path and not os.path.exists(template_path):
            if not template_path.startswith(self._spm_path):
                raise ValueError(f"Template image not found: {template_path}")

    def normalize_image(self, source_image, template_image=None, method="standard"):
        """Execute normalization with enhanced error handling"""
        self.logger.info(f"Normalizing image: {source_image} using method: {method}")
        self.operation_progress.emit("Starting normalization...", 0)
        
        try:
            # Validate paths
            self._validate_spm_paths(source_image, template_image)
            
            # Initialize SPM defaults and clear batch
            self._engine.eval("clear matlabbatch;", nargout=0)
            self._engine.eval("spm('defaults','pet');", nargout=0)
            self._engine.eval("spm_jobman('initcfg');", nargout=0)
            
            # Use default template if none specified
            if not template_image:
                template_image = os.path.join(self._spm_path, 'canonical', 'T1.nii')
                self.logger.info(f"Using default template: {template_image}")
                
            # Fix paths for MATLAB
            source_path = source_image.replace('\\', '/').replace('//', '/')
            template_path = template_image.replace('\\', '/').replace('//', '/')
            
            # Set up the normalization batch structure step by step
            self._engine.eval("""
            matlabbatch = {};
            matlabbatch{1}.spm.tools.oldnorm.est = struct;
            matlabbatch{1}.spm.tools.oldnorm.est.subj.source = {''};
            matlabbatch{1}.spm.tools.oldnorm.est.eoptions = struct;
            """, nargout=0)
            
            # Set source and template
            self._engine.eval(f"""
            matlabbatch{{1}}.spm.tools.oldnorm.est.subj.source = {{'{source_path},1'}};
            matlabbatch{{1}}.spm.tools.oldnorm.est.eoptions.template = {{'{template_path},1'}};
            """, nargout=0)
            
            # Set estimation parameters
            self._engine.eval("""
            matlabbatch{1}.spm.tools.oldnorm.est.eoptions.weight = '';
            matlabbatch{1}.spm.tools.oldnorm.est.eoptions.smosrc = 8;
            matlabbatch{1}.spm.tools.oldnorm.est.eoptions.smoref = 0;
            matlabbatch{1}.spm.tools.oldnorm.est.eoptions.regtype = 'mni';
            matlabbatch{1}.spm.tools.oldnorm.est.eoptions.cutoff = 25;
            matlabbatch{1}.spm.tools.oldnorm.est.eoptions.nits = 16;
            matlabbatch{1}.spm.tools.oldnorm.est.eoptions.reg = 1;
            """, nargout=0)
            
            # Run estimation
            self.operation_progress.emit("Estimating normalization parameters...", 30)
            try:
                self._engine.eval("spm_jobman('run', matlabbatch);", nargout=0)
            except Exception as e:
                raise RuntimeError(f"Normalization estimation failed: {str(e)}")
            
            # Set up the write batch
            self._engine.eval("""
            clear matlabbatch;
            matlabbatch = {};
            matlabbatch{1}.spm.tools.oldnorm.write = struct;
            """, nargout=0)
            
            # Configure write options
            self._engine.eval(f"""
            matlabbatch{{1}}.spm.tools.oldnorm.write.subj.matname = {{'{source_path}_sn.mat'}};
            matlabbatch{{1}}.spm.tools.oldnorm.write.subj.resample = {{'{source_path},1'}};
            matlabbatch{{1}}.spm.tools.oldnorm.write.roptions.preserve = 0;
            matlabbatch{{1}}.spm.tools.oldnorm.write.roptions.bb = [-78 -112 -70; 78 76 85];
            matlabbatch{{1}}.spm.tools.oldnorm.write.roptions.vox = [2 2 2];
            matlabbatch{{1}}.spm.tools.oldnorm.write.roptions.interp = 1;
            matlabbatch{{1}}.spm.tools.oldnorm.write.roptions.wrap = [0 0 0];
            matlabbatch{{1}}.spm.tools.oldnorm.write.roptions.prefix = 'w';
            """, nargout=0)
            
            # Run write operation
            self.operation_progress.emit("Writing normalized image...", 70)
            try:
                self._engine.eval("spm_jobman('run', matlabbatch);", nargout=0)
            except Exception as e:
                raise RuntimeError(f"Failed to write normalized image: {str(e)}")
            
            self.operation_progress.emit("Normalization completed", 100)
            self.operation_completed.emit("Normalization completed successfully", True)
            return True
                
        except Exception as e:
            error_msg = f"Error in normalization: {str(e)}"
            self.logger.error(error_msg)
            self.engine_error.emit(error_msg)
            self.operation_completed.emit("Normalization failed", False)
            return False
    
    def set_origin(self, image_file, coordinates=None):
        """
        Set the origin of an image using spm_image's setorigin function
        
        Args:
            image_file: Path to the image file
            coordinates: List of x, y, z coordinates for the origin (default: [0, 0, 0])
        
        Returns:
            bool: True if successful, False otherwise
        """
        self.logger.info(f"Setting origin for image: {image_file}")
        
        try:
            # If coordinates are not specified, use [0, 0, 0]
            if coordinates is None:
                coordinates = [0, 0, 0]
                
            # Display the image first (required for setorigin)
            self._engine.eval(f"spm_image('Display', '{image_file}');", nargout=0)
            
            # Set the origin
            coord_str = f"{coordinates[0]} {coordinates[1]} {coordinates[2]}"
            self._engine.eval(f"spm_image('SetOrigin', '{coord_str}');", nargout=0)
            
            # Apply the changes
            self._engine.eval("spm_image('Reorient');", nargout=0)
            
            self.operation_completed.emit("Origin set successfully", True)
            return True
            
        except Exception as e:
            error_msg = f"Error setting origin: {str(e)}"
            self.logger.error(error_msg)
            self.engine_error.emit(error_msg)
            self.operation_completed.emit("Failed to set origin", False)
            return False
    
    def check_registration(self, image_files):
        """
        Check registration of multiple images using spm_check_registration
        
        Args:
            image_files: List of paths to image files
        
        Returns:
            bool: True if successful, False otherwise
        """
        self.logger.info(f"Checking registration for {len(image_files)} images")
        
        try:
            # Convert Python list to MATLAB cell array of strings
            images_cell = "{"
            for i, img in enumerate(image_files):
                images_cell += f"'{img}'"
                if i < len(image_files) - 1:
                    images_cell += ", "
            images_cell += "}"
            
            # Run check registration
            self._engine.eval(f"spm_check_registration({images_cell});", nargout=0)
            
            self.operation_completed.emit("Registration check completed", True)
            return True
            
        except Exception as e:
            error_msg = f"Error checking registration: {str(e)}"
            self.logger.error(error_msg)
            self.engine_error.emit(error_msg)
            self.operation_completed.emit("Failed to check registration", False)
            return False
    
    def convert_dicom_files_to_nifti(self, dicom_files, output_dir):
        """
        Convert individual DICOM files to NIFTI format using SPM
        
        Args:
            dicom_files: List of paths to DICOM files
            output_dir: Output directory for NIFTI files
        
        Returns:
            list: List of paths to the created NIFTI files
        """
        self.logger.info(f"Converting {len(dicom_files)} DICOM files to NIFTI format")
        self.operation_progress.emit("Starting DICOM to NIFTI conversion...", 0)
        
        try:
            # Create a MATLAB cell array with the dicom files
            dicom_cell = "{"
            for i, dicom_file in enumerate(dicom_files):
                dicom_cell += f"'{dicom_file}'"
                if i < len(dicom_files) - 1:
                    dicom_cell += ", "
            dicom_cell += "}"
            
            # Set the files in MATLAB
            self._engine.eval(f"dicom_files = {dicom_cell};", nargout=0)
            
            # Convert DICOM files to NIFTI
            self._engine.eval("dicom_headers = spm_dicom_headers(dicom_files);", nargout=0)
            self.operation_progress.emit("Processing DICOM headers...", 30)
            
            # Use 'patid' as RootDirectory to organize files by patient ID
            self._engine.eval(f"nii_files = spm_dicom_convert(dicom_headers, 'all', 'patid', 'nii', '{output_dir}', true);", nargout=0)
            self.operation_progress.emit("Converting files...", 80)
            
            # Get the paths of the created NIFTI files
            nii_files = self._engine.eval("nii_files.files;")
            
            # Convert MATLAB cell array to Python list
            nii_files_list = []
            for i in range(len(nii_files)):
                nii_files_list.append(nii_files[i])
                
            self.operation_progress.emit("Conversion completed", 100)
            self.operation_completed.emit(f"Successfully converted {len(nii_files_list)} files", True)
            
            return nii_files_list
            
        except Exception as e:
            error_msg = f"Error in DICOM to NIFTI conversion: {str(e)}"
            self.logger.error(error_msg)
            self.engine_error.emit(error_msg)
            self.operation_completed.emit("Conversion failed", False)
            return []