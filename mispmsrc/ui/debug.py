#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import logging
import glob
import matplotlib
matplotlib.use('Qt5Agg')  # Use Qt5 backend for matplotlib

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QObject, pyqtSignal
from mispmsrc.core.matlab_engine import MatlabEngine

try:
    from mispmsrc.CLRefactoring.PIB_SUVr_CLs_calc import PIBAnalyzer
except ImportError:
    PIBAnalyzer = None

class DebugProcessor(QObject):
    """SPM processing class without GUI, for debugging and batch processing"""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.matlab_engine = MatlabEngine()
        self.analyzer = PIBAnalyzer() if PIBAnalyzer else None
        
        # Connect MATLAB engine signals
        self.matlab_engine.engine_started.connect(self._on_engine_started)
        self.matlab_engine.engine_error.connect(self._on_engine_error)
        self.matlab_engine.operation_progress.connect(self._on_operation_progress)
        self.matlab_engine.operation_completed.connect(self._on_operation_completed)
    
    def start_matlab(self, spm_path=None):
        """Start MATLAB engine"""
        self.logger.info("Starting MATLAB engine...")
        return self.matlab_engine.start_engine(spm_path)
    
    def process_files(self, params):
        """Process files based on operation type"""
        operation = params.get('operation', '').lower()
        if not operation:
            raise ValueError("Operation type must be specified")

        if operation == 'normalise':
            return self._run_normalization(params)
        elif operation == 'coregister':
            return self._run_coregistration(params)
        elif operation == 'cl_analysis':
            return self._run_cl_analysis(params)
        elif operation == 'set_origin':
            return self._run_set_origin(params)
        elif operation == 'check_registration':
            return self._run_check_registration(params)
        elif operation == 'convert_dicom':
            return self._run_convert_dicom(params)
        elif operation == 'load_nifti':
            return self._run_load_nifti(params)
        # Add batch operation handlers
        elif operation == 'batch_coregister':
            return self._run_batch_coregistration(params)
        elif operation == 'batch_normalise':
            return self._run_batch_normalization(params)
        elif operation == 'batch_set_origin':
            return self._run_batch_set_origin(params)
        elif operation == 'batch_convert':
            return self._run_batch_convert_dicom(params)
        else:
            raise ValueError(f"Unknown operation: {operation}")

    def _run_normalization(self, params):
        """Execute normalization with parameter validation"""
        try:
            # Validate required parameters
            source_image = params.get('source_image')
            template_path = params.get('template_path')
            
            if not source_image:
                raise ValueError("Source image must be specified")
                
            if not os.path.exists(source_image):
                raise ValueError(f"Source image not found: {source_image}")
                
            if not template_path:
                # Try to use default template
                default_templates = [
                    os.path.join('canonical', 'avg152T1.nii'),
                    os.path.join('templates', 'T1.nii')
                ]
                
                for rel_path in default_templates:
                    abs_path = os.path.join(os.path.dirname(source_image), rel_path)
                    if os.path.exists(abs_path):
                        template_path = abs_path
                        self.logger.info(f"Using default template: {template_path}")
                        break
                        
                if not template_path:
                    raise ValueError("Template path must be specified")
                
            if not os.path.exists(template_path):
                raise ValueError(f"Template not found: {template_path}")
            
            # Update params with validated paths
            params['source_image'] = source_image
            params['template_path'] = template_path
            
            self.logger.info("Starting normalization...")
            self.logger.info(f"Source: {source_image}")
            self.logger.info(f"Template: {template_path}")
            
            return self.matlab_engine.normalize_image(params)
        
        except Exception as e:
            self.logger.error(f"Normalization error: {str(e)}")
            raise

    def _run_coregistration(self, params):
        """Execute coregistration"""
        self.logger.info("Starting coregistration...")
        try:
            # Validate input files exist
            ref_image = params.get('ref_image')
            source_image = params.get('source_image')
            
            if not ref_image or not os.path.exists(ref_image):
                raise ValueError(f"Reference image not found: {ref_image}")
                
            if not source_image or not os.path.exists(source_image):
                raise ValueError(f"Source image not found: {source_image}")
                
            self.logger.info(f"Coregistering {source_image} to {ref_image}")
            
            return self.matlab_engine.coregister_images(
                ref_image,
                source_image,
                params.get('cost_function', 'nmi')
            )
        except Exception as e:
            self.logger.error(f"Coregistration error: {str(e)}")
            raise

    def _run_cl_analysis(self, params):
        """Execute CL analysis"""
        self.logger.info("Starting CL analysis...")
        if not self.analyzer:
            self.logger.error("PIBAnalyzer not available")
            return False
            
        try:
            # Validate input parameters
            ref_path = params.get('ref_path')
            roi_path = params.get('roi_path')
            ad_dir = params.get('ad_dir')
            yc_dir = params.get('yc_dir')
            standard_data = params.get('standard_data')
            
            if not all([ref_path, roi_path, ad_dir, yc_dir, standard_data]):
                raise ValueError("All CL analysis parameters must be specified")
                
            if not all(os.path.exists(p) for p in [ref_path, roi_path, ad_dir, yc_dir, standard_data]):
                raise ValueError("One or more specified paths do not exist")
                
            self.analyzer.run_analysis(
                ref_path,
                roi_path,
                ad_dir,
                yc_dir,
                standard_data
            )
            return True
        except Exception as e:
            self.logger.error(f"CL analysis failed: {str(e)}")
            raise

    def _run_set_origin(self, params):
        """Set origin of an image"""
        self.logger.info("Setting image origin...")
        try:
            image_file = params.get('image_file')
            coordinates = params.get('coordinates', [0, 0, 0])
            
            if not image_file or not os.path.exists(image_file):
                raise ValueError(f"Image file not found: {image_file}")
                
            return self.matlab_engine.set_origin(image_file, coordinates)
        except Exception as e:
            self.logger.error(f"Error setting origin: {str(e)}")
            raise
    
    def _run_check_registration(self, params):
        """Check registration of multiple images"""
        self.logger.info("Checking registration...")
        try:
            image_files = params.get('image_files', [])
            
            if not image_files:
                raise ValueError("No image files specified")
                
            for img in image_files:
                if not os.path.exists(img):
                    raise ValueError(f"Image file not found: {img}")
                    
            return self.matlab_engine.check_registration(image_files)
        except Exception as e:
            self.logger.error(f"Error checking registration: {str(e)}")
            raise

    def _run_convert_dicom(self, params):
        """Convert DICOM to NIFTI"""
        self.logger.info("Converting DICOM to NIFTI...")
        try:
            dicom_dir = params.get('dicom_dir')
            output_dir = params.get('output_dir')
            
            if not dicom_dir or not os.path.exists(dicom_dir):
                raise ValueError(f"DICOM directory not found: {dicom_dir}")
                
            if not output_dir:
                raise ValueError("Output directory must be specified")
                
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                
            return self.matlab_engine.convert_to_nifti(dicom_dir, output_dir)
        except Exception as e:
            self.logger.error(f"Error converting DICOM: {str(e)}")
            raise
    
    def _run_load_nifti(self, params):
        """Load and display NIFTI image"""
        self.logger.info("Loading NIFTI file...")
        try:
            image_file = params.get('image_file')
            
            if not image_file or not os.path.exists(image_file):
                raise ValueError(f"Image file not found: {image_file}")
                
            return self.matlab_engine.display_image(image_file)
        except Exception as e:
            self.logger.error(f"Error loading NIFTI: {str(e)}")
            raise

    # Batch operation methods
    def _run_batch_coregistration(self, params):
        """Execute batch coregistration"""
        self.logger.info("Starting batch coregistration...")
        try:
            ref_image = params.get('ref_image')
            source_files = params.get('source_files')
            cost_function = params.get('cost_function', 'nmi')
            
            if not ref_image or not source_files:
                raise ValueError("Reference image and source files must be specified")
                
            if not os.path.exists(ref_image):
                raise ValueError(f"Reference image not found: {ref_image}")
                
            self.logger.info(f"Coregistering {len(source_files)} images to {ref_image}")
            
            return self.matlab_engine.batch_coregister_images(ref_image, source_files, cost_function)
        except Exception as e:
            self.logger.error(f"Batch coregistration error: {str(e)}")
            raise
    
    def _run_batch_normalization(self, params):
        """Execute batch normalization"""
        self.logger.info("Starting batch normalization...")
        try:
            template_path = params.get('template_path')
            source_files = params.get('source_files')
            
            if not template_path or not source_files:
                raise ValueError("Template path and source files must be specified")
                
            if not os.path.exists(template_path):
                raise ValueError(f"Template image not found: {template_path}")
                
            self.logger.info(f"Normalizing {len(source_files)} images using template {template_path}")
            
            # Extract additional parameters if provided
            extra_params = {k: v for k, v in params.items() 
                           if k not in ['operation', 'template_path', 'source_files']}
            
            return self.matlab_engine.batch_normalize_images(template_path, source_files, extra_params)
        except Exception as e:
            self.logger.error(f"Batch normalization error: {str(e)}")
            raise
    
    def _run_batch_set_origin(self, params):
        """Execute batch set origin"""
        self.logger.info("Starting batch origin setting...")
        try:
            image_files = params.get('image_files')
            coordinates = params.get('coordinates', [0, 0, 0])
            
            if not image_files:
                raise ValueError("Image files must be specified")
                
            self.logger.info(f"Setting origin for {len(image_files)} images to {coordinates}")
            
            return self.matlab_engine.batch_set_origin(image_files, coordinates)
        except Exception as e:
            self.logger.error(f"Batch origin setting error: {str(e)}")
            raise
    
    def _run_batch_convert_dicom(self, params):
        """Execute batch DICOM to NIFTI conversion"""
        self.logger.info("Starting batch DICOM to NIFTI conversion...")
        try:
            dicom_dirs = params.get('dicom_dirs')
            output_dir = params.get('output_dir')
            
            if not dicom_dirs or not output_dir:
                raise ValueError("DICOM directories and output directory must be specified")
                
            self.logger.info(f"Converting {len(dicom_dirs)} DICOM directories to NIFTI")
            
            return self.matlab_engine.batch_convert_dicom_to_nifti(dicom_dirs, output_dir)
        except Exception as e:
            self.logger.error(f"Batch DICOM conversion error: {str(e)}")
            raise

    # Signal handlers
    def _on_engine_started(self):
        """MATLAB engine start callback"""
        self.logger.info("MATLAB engine started successfully")

    def _on_engine_error(self, error_msg):
        """MATLAB engine error callback"""
        self.logger.error(f"MATLAB engine error: {error_msg}")

    def _on_operation_progress(self, message, progress):
        """Operation progress callback"""
        self.logger.info(f"Progress ({progress}%): {message}")

    def _on_operation_completed(self, message, success):
        """Operation completion callback"""
        level = logging.INFO if success else logging.ERROR
        self.logger.log(level, f"Operation completed: {message}")

def validate_path(path, is_dir=False):
    """Validate a path before running operations"""
    if not os.path.exists(path):
        print(f"WARNING: Path does not exist: {path}")
        return False
    
    if is_dir and not os.path.isdir(path):
        print(f"WARNING: Not a directory: {path}")
        return False
    
    if not is_dir and not os.path.isfile(path):
        print(f"WARNING: Not a file: {path}")
        return False
    
    return True

def main():
    """Debug main function with file paths organized by function"""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create QApplication instance
    app = QApplication(sys.argv)
    
    # Create processor instance
    processor = DebugProcessor()
    
    # Check for dependencies needed for CL analysis
    missing_deps = []
    try:
        import openpyxl
    except ImportError:
        missing_deps.append("openpyxl")
    
    if missing_deps:
        print(f"WARNING: Missing dependencies required for CL analysis: {', '.join(missing_deps)}")
        print(f"Please install with: pip install {' '.join(missing_deps)}")
        install_choice = input("Would you like to attempt to install missing dependencies now? (y/n): ")
        if install_choice.lower() == 'y':
            try:
                import subprocess
                for dep in missing_deps:
                    print(f"Installing {dep}...")
                    subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
                print("Dependencies installed successfully. Reloading modules...")
                # Try importing again after installation
                import importlib
                if "openpyxl" in missing_deps:
                    try:
                        import openpyxl
                        print("openpyxl loaded successfully")
                    except ImportError:
                        print("Failed to load openpyxl, may need to restart the program")
            except Exception as e:
                print(f"Error installing dependencies: {str(e)}")
                print("Please run 'pip install openpyxl' manually")
    
    # Set up default file paths organized by functionality
    PATHS = {
        # Load NIFTI paths
        'load_nifti': {
            'image_file': r'D:\DataLibrary\PiBTest\AD01_MR.nii'
        },
        
        # Coregistration paths
        'coregister': {
            'ref_image': r'D:\DataLibrary\PiBTest\AD01_MR.nii',
            'source_image': r'D:\DataLibrary\PiBTest\AD01_PET.nii',
            'cost_function': 'nmi'
        },
        
        # Normalization paths
        'normalise': {
            'source_image': r'D:\DataLibrary\PiBTest\AD01_MR.nii',
            'template_path': r'D:\mispm\canonical\avg152T1.nii',
            'source_smoothing': 8,
            'template_smoothing': 0,
            'nonlinear_cutoff': 25,
            'nonlinear_iterations': 16,
            'nonlinear_reg': 1,
            'preserve': 0,
            'prefix': 'w'
        },
        
        # Set Origin paths
        'set_origin': {
            'image_file': r'D:\DataLibrary\PiBTest\AD01_MR.nii',
            'coordinates': [0, 0, 0]  # Default to center
        },
        
        # Check Registration paths
        'check_registration': {
            'image_files': [
                r'D:\DataLibrary\PiBTest\AD01_MR.nii',
                r'D:\DataLibrary\PiBTest\AD01_PET.nii'
            ]
        },
        
        # Convert DICOM paths
        'convert_dicom': {
            'dicom_dir': r'D:\DataLibrary\DICOM',
            'output_dir': r'D:\DataLibrary\Output'
        },
        
        # CL Analysis paths
        'cl_analysis': {
            'ref_path': r'D:\DataLibrary\PiB\Centiloid_Std_VOI\Centiloid_Std_VOI\nifti\2mm\voi_WhlCbl_2mm.nii',
            'roi_path': r'D:\DataLibrary\PiB\Centiloid_Std_VOI\Centiloid_Std_VOI\nifti\2mm\voi_ctx_2mm.nii',
            'ad_dir': r'D:\DataLibrary\PiB\AD-100_PET_5070\AD-100_PET_5070\nifti',
            'yc_dir': r'D:\DataLibrary\PiB\YC-0_PET_5070\YC-0_PET_5070\nifti',
            'standard_data': r'D:\DataLibrary\PiB\SupplementaryTable1.xlsx'
        },
        
        # Batch processing paths
        'batch_coregister': {
            'ref_image': r'D:\DataLibrary\PiBTest\AD01_MR.nii',
            # 'source_dir': r'D:\DataLibrary\PiB\AD-100_PET_5070\AD-100_PET_5070\nifti'  # AD group
            'source_dir': r'D:\DataLibrary\PiB\YC-0_PET_5070\YC-0_PET_5070\nifti'  # YC group
        },
        
        'batch_normalise': {
            'template_path': r'D:\mispm\canonical\avg152T1.nii',
            # 'source_dir': r'D:\DataLibrary\PiB\AD-100_PET_5070\AD-100_PET_5070\nifti'  # AD group
            'source_dir': r'D:\DataLibrary\PiB\YC-0_PET_5070\YC-0_PET_5070\nifti'  # YC group
        },
        
        'batch_set_origin': {
            'image_dir': r'D:\DataLibrary\PiBTest\batch',
            'coordinates': [0, 0, 0]
        },
        
        'batch_convert': {
            'parent_dir': r'D:\DataLibrary\DICOM_parent',
            'output_dir': r'D:\DataLibrary\Output_batch'
        }
    }
    
    # Start MATLAB engine
    print("Starting MATLAB engine...")
    if not processor.start_matlab():
        sys.exit("Failed to start MATLAB engine")
    
    # Display menu options
    print("\nSPM Debug Interface - Available operations:")
    print("1. Load NIFTI")
    print("2. Coregistration")
    print("3. Normalisation")
    print("4. Set Origin")
    print("5. Check Registration")
    print("6. Convert DICOM to NIFTI")
    print("7. CL Analysis")
    print("8. Batch Coregistration")
    print("9. Batch Normalisation")
    print("10. Batch Set Origin")
    print("11. Batch Convert DICOM to NIFTI")
    print("0. Exit")
    
    choice = input("\nSelect operation (0-11): ")
    
    try:
        if choice == '0':
            sys.exit("Exiting program")
            
        elif choice == '1':
            # Load NIFTI
            config = PATHS['load_nifti']
            print(f"Loading NIFTI file: {config['image_file']}")
            params = {'operation': 'load_nifti', **config}
            processor.process_files(params)
            
        elif choice == '2':
            # Coregistration
            config = PATHS['coregister']
            print(f"Coregistering {config['source_image']} to {config['ref_image']}")
            params = {'operation': 'coregister', **config}
            processor.process_files(params)
            
        elif choice == '3':
            # Normalisation
            config = PATHS['normalise']
            print(f"Normalizing {config['source_image']} with template {config['template_path']}")
            params = {'operation': 'normalise', **config}
            processor.process_files(params)
            
        elif choice == '4':
            # Set Origin
            config = PATHS['set_origin']
            print(f"Setting origin for: {config['image_file']}")
            params = {'operation': 'set_origin', **config}
            processor.process_files(params)
            
        elif choice == '5':
            # Check Registration
            config = PATHS['check_registration']
            print(f"Checking registration for: {', '.join(config['image_files'])}")
            params = {'operation': 'check_registration', **config}
            processor.process_files(params)
            
        elif choice == '6':
            # Convert DICOM to NIFTI
            config = PATHS['convert_dicom']
            print(f"Converting DICOM from {config['dicom_dir']} to {config['output_dir']}")
            params = {'operation': 'convert_dicom', **config}
            processor.process_files(params)
            
        elif choice == '7':
            # CL Analysis with path validation
            config = PATHS['cl_analysis']
            
            # Validate all paths before proceeding
            valid_paths = all([
                validate_path(config['ref_path']),
                validate_path(config['roi_path']),
                validate_path(config['ad_dir'], is_dir=True),
                validate_path(config['yc_dir'], is_dir=True),
                validate_path(config['standard_data'])
            ])
            
            if not valid_paths:
                print("\nWARNING: Some paths are invalid. Please check the paths in the 'cl_analysis' section.")
                proceed = input("Do you want to proceed anyway? (y/n): ")
                if proceed.lower() != 'y':
                    sys.exit("Operation cancelled")
            
            # Check if there are normalized files (w prefix) in the directories
            ad_has_norm = False
            yc_has_norm = False
            
            for ext in ['w*.nii', 'w*.nii.gz', 'wr*.nii', 'wr*.nii.gz']:
                if glob.glob(os.path.join(config['ad_dir'], ext)):
                    ad_has_norm = True
                if glob.glob(os.path.join(config['yc_dir'], ext)):
                    yc_has_norm = True
            
            if not ad_has_norm or not yc_has_norm:
                print("\nWARNING: One or both directories may not contain normalized files (with 'w' or 'wr' prefix).")
                print("AD directory has normalized files:", "Yes" if ad_has_norm else "No")
                print("YC directory has normalized files:", "Yes" if yc_has_norm else "No")
                proceed = input("CL analysis requires normalized files. Proceed anyway? (y/n): ")
                if proceed.lower() != 'y':
                    sys.exit("Operation cancelled")
            
            print(f"\nRunning CL analysis with:")
            print(f"  Reference mask: {config['ref_path']}")
            print(f"  ROI mask: {config['roi_path']}")
            print(f"  AD directory: {config['ad_dir']}")
            print(f"  YC directory: {config['yc_dir']}")
            print(f"  Standard data: {config['standard_data']}")
            
            print("\nNote: In the Centiloid method, YC group has a mean of 0 by definition.")
            print("This is expected and follows the standardization approach for Centiloid scale.")
            
            params = {'operation': 'cl_analysis', **config}
            processor.process_files(params)
            
            print("\nAnalysis complete. Results are saved in the 'results' folder with timestamps.")
            
        elif choice == '8':
            # Batch Coregistration
            config = PATHS['batch_coregister']
            ref_image = config['ref_image']
            source_dir = config['source_dir']
            
            if not os.path.exists(ref_image):
                print(f"Reference image not found: {ref_image}")
                return
                
            if not os.path.exists(source_dir):
                print(f"Source directory not found: {source_dir}")
                return
                
            print(f"Batch coregistering images from {source_dir} to {ref_image}")
            
            # Collect source files
            source_files = []
            for ext in ['*.nii', '*.nii.gz']:
                source_files.extend(glob.glob(os.path.join(source_dir, ext)))
            
            if not source_files:
                print("No NIFTI files found in source directory")
                return
                
            print(f"Found {len(source_files)} NIFTI files to process")
            
            params = {
                'operation': 'batch_coregister',
                'ref_image': ref_image,
                'source_files': source_files,
                'cost_function': 'nmi'
            }
            
            processor.process_files(params)
            
        elif choice == '9':
            # Batch Normalisation - only process r* files
            config = PATHS['batch_normalise']
            template_path = config['template_path']
            source_dir = config['source_dir']
            
            if not os.path.exists(template_path):
                print(f"Template image not found: {template_path}")
                sys.exit("Operation cancelled")
                
            if not os.path.exists(source_dir):
                print(f"Source directory not found: {source_dir}")
                sys.exit("Operation cancelled")
                
            print(f"Batch normalizing coregistered images from {source_dir} with template {template_path}")
            
            # Collect coregistered source files (r prefix)
            source_files = []
            for ext in ['r*.nii', 'r*.nii.gz']:
                source_files.extend(glob.glob(os.path.join(source_dir, ext)))
            
            if not source_files:
                print("No coregistered files (with 'r' prefix) found in source directory")
                
                # Show available files to help debugging
                all_files = []
                for ext in ['*.nii', '*.nii.gz']:
                    all_files.extend(glob.glob(os.path.join(source_dir, ext)))
                    
                if all_files:
                    print(f"Directory contains {len(all_files)} NIFTI files, but none start with 'r':")
                    for f in all_files[:5]:  # Show first 5 files
                        print(f"  {os.path.basename(f)}")
                    if len(all_files) > 5:
                        print(f"  ...and {len(all_files)-5} more")
                        
                sys.exit("Operation cancelled")
            
            # Sort files by name to ensure consistent processing order
            source_files.sort()
            
            print(f"Found {len(source_files)} coregistered files to process:")
            for f in source_files[:5]:  # Show first 5 files
                print(f"  {os.path.basename(f)}")
            if len(source_files) > 5:
                print(f"  ...and {len(source_files)-5} more")
            
            # Customize template based on what files we're processing
            if 'AD-100_PET_5070' in source_dir:
                print("Processing AD files - using specific template settings")
            elif 'YC-0_PET_5070' in source_dir:
                print("Processing YC files - using specific template settings")
            
            # Add more parameters for better normalization
            params = {
                'operation': 'batch_normalise',
                'template_path': template_path,
                'source_files': source_files,
                'source_smoothing': 8,        # Default for PET data
                'template_smoothing': 0,      # Template is already smooth
                'nonlinear_cutoff': 25,       # Standard SPM setting
                'nonlinear_iterations': 16,   # Standard SPM setting
                'nonlinear_reg': 1,           # Standard regularization
                'preserve': 0,                # Preserve concentration (0) not amount (1)
                'prefix': 'w'                 # Prefix for normalized files
            }
            
            try:
                result = processor.process_files(params)
                if isinstance(result, dict):
                    print(f"\nNormalization completed:")
                    print(f"  Total files: {result.get('total', 0)}")
                    print(f"  Successfully processed: {result.get('success', 0)}")
                    print(f"  Failed: {result.get('failed', 0)}")
                    
                    if result.get('failed', 0) > 0 and result.get('failed_files'):
                        print("\nFiles that failed:")
                        for f in result['failed_files'][:5]:  # Show first 5 failures
                            print(f"  {os.path.basename(f)}")
                        if len(result['failed_files']) > 5:
                            print(f"  ...and {len(result['failed_files'])-5} more")
            except Exception as e:
                print(f"Error during batch normalization: {str(e)}")
            
        elif choice == '10':
            # Batch Set Origin
            config = PATHS['batch_set_origin']
            image_dir = config['image_dir']
            coordinates = config['coordinates']
            
            if not os.path.exists(image_dir):
                print(f"Image directory not found: {image_dir}")
                return
                
            print(f"Batch setting origin for images in {image_dir} to {coordinates}")
            
            # Collect image files
            image_files = []
            for ext in ['*.nii', '*.nii.gz']:
                image_files.extend(glob.glob(os.path.join(image_dir, ext)))
            
            if not image_files:
                print("No NIFTI files found in image directory")
                return
                
            print(f"Found {len(image_files)} NIFTI files to process")
            
            params = {
                'operation': 'batch_set_origin',
                'image_files': image_files,
                'coordinates': coordinates
            }
            
            processor.process_files(params)
            
        elif choice == '11':
            # Batch Convert DICOM to NIFTI
            config = PATHS['batch_convert']
            parent_dir = config['parent_dir']
            output_dir = config['output_dir']
            
            if not os.path.exists(parent_dir):
                print(f"Parent directory not found: {parent_dir}")
                return
                
            print(f"Batch converting DICOM directories in {parent_dir} to NIFTI in {output_dir}")
            
            # Get all subdirectories
            dicom_dirs = {}
            for dir_name in os.listdir(parent_dir):
                dir_path = os.path.join(parent_dir, dir_name)
                if os.path.isdir(dir_path):
                    dicom_dirs[dir_name] = dir_path
            
            if not dicom_dirs:
                print("No subdirectories found in parent directory")
                return
                
            print(f"Found {len(dicom_dirs)} directories to process")
            
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            params = {
                'operation': 'batch_convert',
                'dicom_dirs': dicom_dirs,
                'output_dir': output_dir
            }
            
            processor.process_files(params)
            
        else:
            print("Invalid choice!")
            
    except Exception as e:
        print(f"Error during processing: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up before exiting
        app.quit()

if __name__ == '__main__':
    main()
