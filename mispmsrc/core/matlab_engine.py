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
        self._is_running = False
        self._matlab_module = None
        
    def start_engine(self, spm_path=None, timeout=None):
        """Start the MATLAB engine with SPM initialization
        
        Args:
            spm_path: Path to SPM toolbox (optional)
            timeout: Timeout in seconds for engine start (optional)
            
        Returns:
            bool: Whether the engine was started successfully
        """
        if self.is_running():
            self.logger.info("MATLAB engine is already running")
            return True
            
        self.logger.info("Starting MATLAB engine...")
        
        try:
            # Import the matlab.engine module
            try:
                import matlab.engine
                self._matlab_module = matlab.engine
            except ImportError:
                self.logger.error("Failed to import matlab.engine. Is MATLAB Engine for Python installed?")
                raise ImportError("MATLAB Engine for Python is not installed")
            
            # Start MATLAB engine asynchronously to avoid UI freezing
            future = self._matlab_module.start_matlab(background=True)
            
            # Wait for the engine to start
            if timeout:
                self._engine = future.result(timeout=timeout)
            else:
                self._engine = future.result()
                
            # Add the project paths to MATLAB path
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
            matlab_dir = os.path.join(project_root, "mispmsrc", "matlab")
            cl_dir = os.path.join(project_root, "mispmsrc", "CLRefactoring")
            
            # Ensure path separators are correct for MATLAB
            matlab_dir = self._normalize_path(matlab_dir)
            cl_dir = self._normalize_path(cl_dir)
            
            # Add directories to MATLAB path
            self._engine.addpath(matlab_dir, nargout=0)
            self._engine.addpath(cl_dir, nargout=0)
            
            # Run the startup script instead of the initialization function directly
            startup_script = os.path.join(matlab_dir, "startup.m")
            if os.path.exists(startup_script):
                startup_script = self._normalize_path(startup_script)
                self._engine.run(startup_script, nargout=0)
            else:
                self.logger.warning(f"Could not find startup script at {startup_script}")
                # If startup script doesn't exist, call initialize_matlab directly
                self._engine.initialize_matlab(nargout=0)
            
            # Add SPM to MATLAB path if provided
            if spm_path:
                spm_path = self._normalize_path(spm_path)
                self._engine.addpath(spm_path, nargout=0)
                self._engine.eval("spm('defaults', 'PET');", nargout=0)
                self._engine.eval("spm_jobman('initcfg');", nargout=0)
                
            self.logger.info("MATLAB engine started successfully")
            
            # Set flag and emit signal
            self._is_running = True
            self.engine_started.emit()
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start MATLAB engine: {str(e)}")
            self.engine_error.emit(f"Failed to start MATLAB engine: {str(e)}")
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
            self._is_running = False
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
        return self._is_running
    
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
    
    def convert_to_nifti(self, dicom_dir, output_dir):
        """Convert DICOM files to NIFTI format
        
        Args:
            dicom_dir: Directory containing DICOM files
            output_dir: Directory where NIFTI files will be saved
            
        Returns:
            bool: True if conversion successful
        """
        if not self.engine:
            self.engine_error.emit("MATLAB engine not running")
            return False
        
        try:
            # Normalize paths for MATLAB
            dicom_dir = self._normalize_path(dicom_dir)
            output_dir = self._normalize_path(output_dir)
            
            # Make sure output directory exists
            self._ensure_directory_exists(output_dir)
            
            # Emit progress signal
            self.operation_progress.emit("Starting DICOM to NIFTI conversion...", 10)
            
            # Count DICOM files (for progress reporting)
            dcm_count = self.engine.count_dicom_files(dicom_dir, nargout=1)
            if dcm_count == 0:
                self.operation_progress.emit("No DICOM files found", 100)
                self.operation_completed.emit("No DICOM files found", False)
                return False
                
            self.operation_progress.emit(f"Found {dcm_count} DICOM files", 20)
            
            # Run conversion with error handling
            try:
                # Call MATLAB function
                self.operation_progress.emit("Converting files...", 50)
                result = self.engine.convert_dicom_to_nifti(dicom_dir, output_dir, nargout=1)
                
                # Check result
                if result:
                    self.operation_progress.emit("Conversion complete", 100)
                    self.operation_completed.emit("DICOM to NIFTI conversion successful", True)
                    return True
                else:
                    self.operation_progress.emit("Conversion failed", 100)
                    self.operation_completed.emit("DICOM to NIFTI conversion failed", False)
                    return False
                    
            except Exception as e:
                self.operation_progress.emit("Error during conversion", 100)
                self.operation_completed.emit(f"DICOM to NIFTI conversion error: {str(e)}", False)
                return False
                
        except Exception as e:
            self.engine_error.emit(f"Error: {str(e)}")
            return False

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
    
    def load_nifti(self, file_path):
        """
        Load and display a NIFTI file for viewing (without MATLAB)
        
        Args:
            file_path: Path to the NIFTI image file
            
        Returns:
            bool: True if successful
        """
        try:
            # We'll use the Python viewer directly here
            from mispmsrc.ui.nifti_viewer import NiftiViewer
            from PyQt5.QtWidgets import QApplication
            
            # Create viewer and configure it for view-only mode
            viewer = NiftiViewer()
            viewer.setWindowTitle(f"NIFTI Viewer - View Only - {os.path.basename(file_path)}")
            
            # Hide save and set origin buttons
            viewer.save_btn.setVisible(False)
            viewer.set_origin_btn.setVisible(False)
            
            # Load the NIFTI file
            success = viewer.load_nifti(file_path)
            
            if success:
                # Show the viewer as a modal dialog
                viewer.exec_()
                self.operation_completed.emit("NIFTI file viewed successfully", True)
                return True
            else:
                self.operation_completed.emit("Failed to load NIFTI file", False)
                return False
                
        except Exception as e:
            error_msg = f"Error viewing NIFTI file: {str(e)}"
            self.logger.error(error_msg)
            self.engine_error.emit(error_msg)
            self.operation_completed.emit("Failed to view NIFTI file", False)
            return False

    def coregister_images(self, ref_image, source_image, cost_function="nmi"):
        """Coregister images using spm_coreg"""
        if not ref_image or not source_image:
            raise ValueError("Reference and source images must be specified")
            
        self.logger.info(f"Coregistering {source_image} to {ref_image}")
        self.operation_progress.emit("Starting coregistration...", 0)
        
        try:
            # Make sure file paths are properly formatted for MATLAB
            ref_image = self._normalize_path(ref_image)
            source_image = self._normalize_path(source_image)
            
            # First check if the coregister function exists (our custom function)
            has_custom_fn = self._engine.exist('coregister') > 0
            
            self.operation_progress.emit("Executing coregistration...", 30)
            
            if has_custom_fn:
                # Use our custom coregister function that handles all the details
                success = self._engine.coregister(ref_image, source_image, cost_function, nargout=1)
            else:
                # Fallback to direct SPM commands if our custom function isn't available
                matlab_cmd = f"""
                try
                    % Load volumes for coregistration
                    ref_vol = spm_vol('{ref_image}');
                    source_vol = spm_vol('{source_image}');
                    
                    % Set options for coregistration
                    flags = struct('cost_fun', '{cost_function}', ...
                                   'sep', [4 2], ...
                                   'tol', [0.02 0.02 0.02 0.001 0.001 0.001 0.01 0.01 0.01 0.001 0.001 0.001], ...
                                   'fwhm', [7 7]);
                    
                    % Run coregistration estimation
                    x = spm_coreg(ref_vol, source_vol, flags);
                    
                    % Apply transformation to source image
                    M = spm_matrix(x);
                    spm_get_space(source_vol.fname, source_vol.mat / M);
                    
                    % Reslice the image
                    P = {{ref_vol.fname; source_vol.fname}};
                    spm_reslice(P, struct('interp', 1, 'mask', true, 'mean', false, 'which', 1, 'prefix', 'r'));
                    
                    % Return success
                    success = true;
                catch ME
                    disp(['Error in coregistration: ' ME.message]);
                    success = false;
                end
                """
                # Execute the script and get the output
                self._engine.eval(matlab_cmd, nargout=0)
                success = self._engine.workspace['success']
            
            if success:
                self.operation_progress.emit("Coregistration completed", 100)
                self.operation_completed.emit("Coregistration completed successfully", True)
                return True
            else:
                error_msg = "Coregistration failed"
                self.operation_completed.emit(error_msg, False)
                return False
                
        except Exception as e:
            error_msg = f"Error in coregistration: {str(e)}"
            self.logger.error(error_msg)
            self.engine_error.emit(error_msg)
            self.operation_completed.emit("Coregistration failed", False)
            return False
    
    def batch_coregister_images(self, ref_image, source_files, cost_function="nmi"):  # cost_function="nmi" is default
        """Batch coregister images
        
        Args:
            ref_image: Reference image path
            source_files: List of source image paths
            cost_function: Coregistration cost function
            
        Returns:
            dict: Summary of results including success count, failure count, and failed files
        """
        if not ref_image or not source_files:
            raise ValueError("Reference image and source files must be specified")
            
        self.logger.info(f"Batch coregistering {len(source_files)} images to {ref_image}")
        
        results = {
            'total': len(source_files),
            'success': 0,
            'failed': 0,
            'failed_files': [],
            'output_files': []
        }
        
        ref_image = ref_image.replace('\\', '/')
        
        for i, source_file in enumerate(source_files):
            try:
                source_file = source_file.replace('\\', '/')
                self.logger.info(f"Coregistering {i+1}/{len(source_files)}: {os.path.basename(source_file)}")
                self.operation_progress.emit(f"Coregistering {os.path.basename(source_file)}", 
                                           int((i / len(source_files)) * 100))
                
                success = self.coregister_images(ref_image, source_file, cost_function)
                if success:
                    self.logger.info(f"Successfully coregistered {source_file}")
                    results['success'] += 1
                    source_dir = os.path.dirname(source_file)
                    source_name = os.path.basename(source_file)
                    output_file = os.path.join(source_dir, 'r' + source_name)
                    results['output_files'].append(output_file)
                else:
                    self.logger.error(f"Failed to coregister {source_file}")
                    results['failed'] += 1
                    results['failed_files'].append(source_file)
            except Exception as e:
                self.logger.error(f"Error coregistering {source_file}: {str(e)}")
                results['failed'] += 1
                results['failed_files'].append(source_file)
        
        success_message = f"Completed batch coregistration: {results['success']}/{results['total']} successful"
        self.operation_completed.emit(success_message, results['failed'] == 0)
        return results
    
    def normalize_image(self, params):
        """Execute normalization with SPM
        
        Args:
            params: Dictionary containing normalization parameters
                - source_image: Image to normalize
                - template_path: Template image path
                - source_smoothing: Smoothing for source image (default: 8)
                - template_smoothing: Smoothing for template (default: 0)
                - nonlinear_cutoff: Nonlinear frequency cutoff (default: 25)
                - nonlinear_iterations: Number of nonlinear iterations (default: 16)
                - nonlinear_reg: Nonlinear regularization (default: 1)
                - preserve: 0 for preserve concentrations, 1 for preserve amount (default: 0)
                - prefix: Prefix for output files (default: 'w')
                - bounding_box: Optional bounding box
                
        Returns:
            bool: Whether normalization was successful
        """
        if not self.is_running():
            raise RuntimeError("MATLAB engine is not running")
            
        # Validate parameters
        if not isinstance(params, dict):
            raise ValueError("Parameters must be provided as a dictionary")
            
        source_image = params.get('source_image')
        template_path = params.get('template_path')
        
        if not source_image or not os.path.exists(source_image):
            raise ValueError(f"Source image not found: {source_image}")
            
        if not template_path or not os.path.exists(template_path):
            raise ValueError(f"Template image not found: {template_path}")
            
        # Ensure output directory exists and is writeable
        output_dir = os.path.dirname(source_image)
        if not os.access(output_dir, os.W_OK):
            raise ValueError(f"No write permission for output directory: {output_dir}")
            
        # Check if output file already exists and is writeable
        prefix = params.get('prefix', 'w')
        source_name = os.path.basename(source_image)
        output_path = os.path.join(output_dir, f"{prefix}{source_name}")
        
        if os.path.exists(output_path) and not os.access(output_path, os.W_OK):
            raise ValueError(f"Output file exists but is not writeable: {output_path}")
            
        # Normalize paths for MATLAB
        source_path = self._normalize_path(source_image)
        template_path = self._normalize_path(template_path)
        
        self.logger.info(f"Normalizing {source_image} to template {template_path}")
        self.operation_progress.emit("Starting normalization...", 0)
        
        try:
            # First check image compatibility
            self._engine.eval(f"disp(['Source dimensions: ' num2str(diag(spm_get_space('{source_path}'))')])", nargout=0)
            self._engine.eval(f"disp(['Template dimensions: ' num2str(diag(spm_get_space('{template_path}'))')])", nargout=0)
            
            # Create MATLAB script for normalization
            matlab_cmd = f"""
            try
                % Load source and template volumes
                source_vol = spm_vol('{source_path}');
                template_vol = spm_vol('{template_path}');
                
                % Set up normalization parameters
                clear matlabbatch;
                matlabbatch{{1}}.spm.spatial.normalise.estwrite.subj.vol = {{source_vol.fname}};
                matlabbatch{{1}}.spm.spatial.normalise.estwrite.subj.resample = {{source_vol.fname}};
                matlabbatch{{1}}.spm.spatial.normalise.estwrite.eoptions.biasreg = 0.0001;
                matlabbatch{{1}}.spm.spatial.normalise.estwrite.eoptions.biasfwhm = 60;
                matlabbatch{{1}}.spm.spatial.normalise.estwrite.eoptions.tpm = {{template_vol.fname}};
                matlabbatch{{1}}.spm.spatial.normalise.estwrite.eoptions.affreg = 'mni';
                matlabbatch{{1}}.spm.spatial.normalise.estwrite.eoptions.reg = [{params.get('nonlinear_reg', 1)}];
                matlabbatch{{1}}.spm.spatial.normalise.estwrite.eoptions.fwhm = [{params.get('source_smoothing', 8)}];
                matlabbatch{{1}}.spm.spatial.normalise.estwrite.eoptions.samp = 3;
                matlabbatch{{1}}.spm.spatial.normalise.estwrite.woptions.bb = [-78 -112 -70; 78 76 85];
                matlabbatch{{1}}.spm.spatial.normalise.estwrite.woptions.vox = [2 2 2];
                matlabbatch{{1}}.spm.spatial.normalise.estwrite.woptions.interp = 4;
                matlabbatch{{1}}.spm.spatial.normalise.estwrite.woptions.prefix = '{params.get('prefix', 'w')}';
                
                % Custom bounding box if specified
                if {1 if 'bounding_box' in params else 0}
                    try
                        bb = {str(params.get('bounding_box', [-78, -112, -70, 78, 76, 85]))};
                        % First 3 values are min coordinates, last 3 are max coordinates
                        matlabbatch{{1}}.spm.spatial.normalise.estwrite.woptions.bb = [bb(1:3); bb(4:6)];
                        disp(['Using custom bounding box: ' mat2str(matlabbatch{{1}}.spm.spatial.normalise.estwrite.woptions.bb)]);
                    catch
                        disp('Error setting custom bounding box, using default');
                    end
                end
                
                % Run normalization
                spm_jobman('run', matlabbatch);
                
                % Verify output was created
                output_file = fullfile('{output_dir}', '{prefix}{source_name}');
                if exist(output_file, 'file')
                    disp(['Normalized image created: ' output_file]);
                    success = true;
                else
                    disp(['Warning: Expected output file not found: ' output_file]);
                    success = false;
                end
            catch ME
                disp(['Error in normalization: ' ME.message]);
                disp(getReport(ME));
                success = false;
            end
            """
            
            # Update progress
            self.operation_progress.emit("Setting up normalization parameters...", 10)
            
            # Execute normalization
            self._engine.eval("spm('defaults', 'PET');", nargout=0)
            self._engine.eval("spm_jobman('initcfg');", nargout=0)
            
            self.operation_progress.emit("Executing normalization...", 30)
            self._engine.eval(matlab_cmd, nargout=0)
            
            # Check success
            success = self._engine.workspace['success']
            
            if success:
                self.operation_progress.emit("Normalization completed", 100)
                self.operation_completed.emit("Normalization completed successfully", True)
                return True
            else:
                error_msg = "Normalization failed"
                self.operation_completed.emit(error_msg, False)
                return False
                
        except Exception as e:
            error_msg = f"Error in normalization: {str(e)}"
            self.logger.error(error_msg)
            self.engine_error.emit(error_msg)
            self.operation_completed.emit("Normalization failed", False)
            return False

    def batch_normalize_images(self, template_path, source_files, params=None):
        """Batch normalize images to a template
        
        Args:
            template_path: Path to template image
            source_files: List of source image paths
            params: Additional parameters for normalization
            
        Returns:
            dict: Summary of results including success count, failure count, and failed files
        """
        if not template_path or not source_files:
            raise ValueError("Template path and source files must be specified")
            
        self.logger.info(f"Batch normalizing {len(source_files)} images to {template_path}")
        
        results = {
            'total': len(source_files),
            'success': 0,
            'failed': 0,
            'failed_files': [],
            'output_files': []
        }
        
        # Normalize template path
        template_path = self._normalize_path(template_path)
        
        # Process each file
        for i, source_file in enumerate(source_files):
            try:
                # Normalize path
                source_file = self._normalize_path(source_file)
                
                self.logger.info(f"Normalizing {i+1}/{len(source_files)}: {os.path.basename(source_file)}")
                self.operation_progress.emit(f"Normalizing {os.path.basename(source_file)}", 
                                           int((i / len(source_files)) * 100))
                
                # Create parameters for this file
                file_params = {
                    'source_image': source_file,
                    'template_path': template_path,
                    'prefix': 'w'
                }
                
                # Add any extra parameters
                if params:
                    file_params.update(params)
                
                # Run normalization
                success = self.normalize_image(file_params)
                
                if success:
                    self.logger.info(f"Successfully normalized {source_file}")
                    results['success'] += 1
                    
                    # Add output file to results
                    source_dir = os.path.dirname(source_file)
                    source_name = os.path.basename(source_file)
                    prefix = file_params.get('prefix', 'w')
                    output_file = os.path.join(source_dir, f"{prefix}{source_name}")
                    results['output_files'].append(output_file)
                else:
                    self.logger.error(f"Failed to normalize {source_file}")
                    results['failed'] += 1
                    results['failed_files'].append(source_file)
            except Exception as e:
                self.logger.error(f"Error normalizing {source_file}: {str(e)}")
                results['failed'] += 1
                results['failed_files'].append(source_file)
        
        # Send completion signal
        success_message = f"Completed batch normalization: {results['success']}/{results['total']} successful"
        self.operation_completed.emit(success_message, results['failed'] == 0)
        
        return results
    
    def import_dicom(self, path):
        """
        Import DICOM files for processing
        
        Args:
            path (str or list): Path to DICOM directory or list of DICOM files
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.operation_progress.emit("Importing DICOM files...", 0)
            
            if isinstance(path, list):
                # Handle list of DICOM files
                self.operation_progress.emit(f"Importing {len(path)} DICOM files...", 10)
                
                # Create a temporary MATLAB cell array with the file paths
                files_cell = self.eng.cell(1, len(path))
                for i, file_path in enumerate(path):
                    files_cell[0][i] = file_path
                    
                # Call MATLAB function to import DICOM files
                result = self.eng.spm_dicom_convert(files_cell, nargout=1)
                
            else:
                # Handle directory path
                self.operation_progress.emit(f"Importing DICOM files from directory: {path}", 10)
                
                # Call MATLAB function to import DICOM files from directory
                result = self.eng.spm_dicom_convert(path, nargout=1)
            
            self.operation_progress.emit("DICOM import completed", 100)
            self.operation_completed.emit("DICOM import completed", True)
            return True
            
        except Exception as e:
            error_msg = str(e)
            self.operation_completed.emit(f"DICOM import failed: {error_msg}", False)
            self.engine_error.emit(f"Error during DICOM import: {error_msg}")
            return False
    
    def set_origin(self, image_path, coordinates=None):
        """Set the origin of a NIFTI image using Python's NiftiViewer
        
        Args:
            image_path: Path to the NIFTI image (may include parameters like "file.nii,1")
            coordinates: Optional list of 3 coordinates [x, y, z] for the origin
                If provided, sets origin directly, otherwise opens visual interface
                
        Returns:
            bool: True if successful, False otherwise
        """
        # Handle paths that may contain commas and parameters (e.g., "file.nii,1")
        # Save the original path for MATLAB if needed
        original_path = image_path
        
        # For file operations, extract just the file path without parameters
        if ',' in image_path:
            clean_path = image_path.split(',')[0]
        else:
            clean_path = image_path
        
        if not os.path.exists(clean_path):
            error_msg = f"File not found: {clean_path}"
            self.logger.error(error_msg)
            self.engine_error.emit(error_msg)
            return False
            
        self.logger.info(f"Setting origin for {clean_path}")
        self.operation_progress.emit("Opening origin setting interface...", 0)
        
        try:
            if coordinates:
                # Direct setting of origin using coordinates
                x, y, z = coordinates
                
                # Use nibabel directly to set the origin
                try:
                    import nibabel as nib
                    
                    # Load the image
                    img = nib.load(clean_path)
                    
                    # Create a new affine matrix with the updated origin
                    new_affine = img.affine.copy()
                    new_affine[:3, 3] = [x, y, z]
                    
                    # Create a new image with the updated affine
                    new_img = nib.Nifti1Image(img.get_fdata(), new_affine, img.header)
                    
                    # Save the new image
                    nib.save(new_img, clean_path)
                    
                    self.operation_progress.emit("Origin set successfully", 100)
                    self.operation_completed.emit(f"Origin set to [{x}, {y}, {z}]", True)
                    return True
                    
                except ImportError:
                    # Fall back to MATLAB if nibabel is not available
                    # Use the original path here for MATLAB
                    matlab_cmd = f"""
                    try
                        % Load the image
                        V = spm_vol('{original_path}');
                        
                        % Create transformation matrix with new origin
                        M = V.mat;
                        
                        % Set the origin (4th column, rows 1-3)
                        M(1:3, 4) = [{x}; {y}; {z}];
                        
                        % Update the header
                        spm_get_space('{original_path}', M);
                        
                        % Verify new origin was set
                        V_new = spm_vol('{original_path}');
                        new_origin = V_new.mat(1:3, 4);
                        
                        disp(['New origin set to: ' num2str(new_origin')]);
                        success = true;
                    catch ME
                        disp(['Error setting origin: ' ME.message]);
                        disp(getReport(ME));
                        success = false;
                    end
                    """
                    # Execute MATLAB command for direct setting
                    self._engine.eval(matlab_cmd, nargout=0)
                    
                    # Check success
                    success = self._engine.workspace['success']
                    
                    if success:
                        self.operation_progress.emit("Origin set successfully", 100)
                        self.operation_completed.emit(f"Origin set to [{x}, {y}, {z}]", True)
                        return True
                    else:
                        self.operation_progress.emit("Failed to set origin", 100)
                        self.operation_completed.emit("Failed to set origin", False)
                        return False
            else:
                # Open Python viewer for interactive origin setting
                try:
                    # Import necessary packages with detailed error handling
                    try:
                        import nibabel as nib
                        import matplotlib
                        from matplotlib.figure import Figure
                        from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
                        from mispmsrc.ui.nifti_viewer import NiftiViewer
                    except ImportError as e:
                        self.logger.error(f"Required package not found: {str(e)}")
                        self.operation_progress.emit(f"Missing dependency: {str(e)}", 100)
                        self.operation_completed.emit(f"Failed to import required package: {str(e)}", False)
                        return False
                    
                    # Update progress
                    self.operation_progress.emit("Opening NiftiViewer...", 50)
                    
                    # Create and show the viewer
                    viewer = NiftiViewer()
                    
                    # Connect origin set signal
                    def on_origin_set(new_origin):
                        self.logger.info(f"New origin set: {new_origin}")
                    
                    viewer.origin_set.connect(on_origin_set)
                    
                    # Load the NIFTI file with the clean path
                    load_success = viewer.load_nifti(clean_path)
                    
                    if not load_success:
                        self.logger.error(f"Failed to load NIFTI file in viewer: {clean_path}")
                        self.operation_progress.emit("Failed to load NIFTI file", 100)
                        self.operation_completed.emit("Failed to load NIFTI file", False)
                        return False
                    
                    # Show the viewer dialog - blocks until closed
                    result = viewer.exec_()
                    
                    if result == 1:  # Dialog accepted (saved)
                        self.operation_progress.emit("Origin updated successfully", 100)
                        self.operation_completed.emit("Origin updated and saved", True)
                        return True
                    else:
                        self.operation_progress.emit("Origin setting cancelled", 100)
                        self.operation_completed.emit("Origin setting cancelled", False)
                        return False
                        
                except Exception as e:
                    import traceback
                    error_details = traceback.format_exc()
                    self.logger.error(f"Error displaying NiftiViewer: {str(e)}\n{error_details}")
                    self.operation_progress.emit(f"Error displaying NiftiViewer: {str(e)}", 100)
                    self.operation_completed.emit(f"Failed to open viewer: {str(e)}", False)
                    return False
                    
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            error_msg = f"Error setting origin: {str(e)}\n{error_details}"
            self.logger.error(error_msg)
            self.engine_error.emit(error_msg)
            self.operation_completed.emit("Failed to set origin", False)
            return False
    
    def check_registration(self, file_paths):
        """Check registration of multiple images by displaying them together
        
        Args:
            file_paths: List of NIFTI file paths to check
            
        Returns:
            bool: True if displayed successfully, False otherwise
        """
        if not self.is_running():
            self.engine_error.emit("MATLAB engine not running")
            return False
            
        if not file_paths or len(file_paths) == 0:
            self.engine_error.emit("No files provided for registration check")
            return False
            
        self.logger.info(f"Checking registration for {len(file_paths)} images")
        self.operation_progress.emit(f"Opening SPM check registration for {len(file_paths)} images...", 0)
        
        try:
            # Convert file paths to MATLAB-friendly format
            matlab_paths = []
            for path in file_paths:
                # Replace backslashes with forward slashes
                matlab_path = self._normalize_path(path)
                matlab_paths.append(matlab_path)
            
            # Direct approach using eval and string formatting
            files_str = "'" + "','".join(matlab_paths) + "'"
            
            self.operation_progress.emit("Preparing to display images...", 50)
            
            # Pre-scan files to identify PET images
            self._engine.eval("""
            % Pre-scan files to identify PET images
            pet_indices = [];
            all_files = {""" + files_str + """};
            for i = 1:numel(all_files)
                try
                    vol = spm_vol(all_files{i});
                    data = spm_read_vols(vol);
                    
                    % 检查可能是PET图像的特征：
                    % 1. 最大值明显大于均值
                    % 2. 值都为正（SUV/计数）
                    % 3. 含有"PET", "PiB", "FDG"等关键词
                    
                    max_val = max(data(:));
                    mean_val = mean(data(data > 0));
                    is_positive = min(data(:)) >= 0;
                    max_mean_ratio = max_val / (mean_val + eps);
                    name_lower = lower(all_files{i});
                    
                    % 测试打印信息，帮助调试
                    fprintf('File %d: %s, max=%.2f, mean=%.2f, ratio=%.2f\\n', ...
                            i, all_files{i}, max_val, mean_val, max_mean_ratio);
                    
                    % 检查名称中是否有PET相关关键词
                    is_pet_name = contains(name_lower, 'pet') || contains(name_lower, 'pib') || ...
                                 contains(name_lower, 'fdg') || contains(name_lower, 'suvr');
                                 
                    % 典型的PET图像特征
                    if ((max_mean_ratio > 10 && is_positive) || is_pet_name)
                        pet_indices = [pet_indices, i];
                        fprintf('File %d identified as PET image\\n', i);
                    end
                catch
                    fprintf('Error analyzing file %d: %s\\n', i, all_files{i});
                end
            end
            """, nargout=0)
            
            # call MATLAB function spm_check_registration
            self._engine.eval(f"spm_check_registration({files_str});", nargout=0)
            
            # user-defined function to enhance display for PET images
            self._engine.eval("""
            % 获取SPM显示状态
            global st;
            
            % 确保st存在且有体积数据
            if exist('st', 'var') && isfield(st, 'vols') && ~isempty(st.vols)
                try
                    % 针对每个被识别为PET的图像设置增强显示
                    for i = 1:numel(pet_indices)
                        pet_idx = pet_indices(i);
                        
                        if pet_idx <= numel(st.vols) && ~isempty(st.vols{pet_idx})
                            fprintf('Enhancing display for PET volume %d\\n', pet_idx);
                            
                            % 获取体素数据
                            vol_data = spm_read_vols(st.vols{pet_idx});
                            
                            % 使用更激进的阈值裁剪获取更好的显示范围
                            sorted_vals = sort(vol_data(vol_data > 0));
                            
                            if ~isempty(sorted_vals)
                                % 使用1%和85%分位数以提高对比度
                                lower_pct = max(1, round(length(sorted_vals)*0.01));
                                upper_pct = min(length(sorted_vals), round(length(sorted_vals)*0.85));
                                
                                low_val = sorted_vals[lower_pct];
                                high_val = sorted_vals[upper_pct];
                                
                                % 设置更合适的显示窗口
                                st.vols{pet_idx}.window = [low_val high_val];
                                st.vols{pet_idx}.mapping = 'linear';
                                
                                % 可选：使用热色调更好地展示PET图像
                                st.vols{pet_idx}.cmap = hot(256);
                                
                                fprintf('Display range set to [%.2f, %.2f] for volume %d\\n', low_val, high_val, pet_idx);
                            else
                                fprintf('No positive values found in volume %d\\n', pet_idx);
                            end
                        end
                    end
                    
                    % 重绘显示
                    spm_orthviews('Redraw');
                    fprintf('Display enhancement complete\\n');
                catch ME
                    fprintf('Error enhancing display: %s\\n', ME.message);
                end
            else
                fprintf('SPM display state not properly initialized\\n');
            end
            """, nargout=0)
            
            self.operation_progress.emit("Registration check display initialized", 100)
            self.operation_completed.emit("Registration check complete", True)
            return True
            
        except Exception as e:
            error_msg = f"Error checking registration: {str(e)}"
            self.logger.error(error_msg)
            self.engine_error.emit(error_msg)
            self.operation_completed.emit("Registration check failed", False)
            return False
    
    def _normalize_path(self, path):
        """Normalize file path for MATLAB by replacing backslashes with forward slashes"""
        if path:
            return path.replace('\\', '/')
        return path