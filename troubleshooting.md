# MISPM Troubleshooting Guide

This document contains solutions for common issues you may encounter while using MISPM.

## 1. Application Startup Issues

### Python Environment Problems

**Symptom**: The application fails to start with errors about missing modules.

**Solution**: 
1. Make sure you have activated the Python environment:
   ```
   conda activate mispmenv   # or your environment name
   ```
2. Reinstall dependencies:
   ```
   pip install -r requirements.txt
   ```

### MATLAB Engine Issues

**Symptom**: "Error starting MATLAB engine" message.

**Solution**:
1. Make sure MATLAB is installed and the Python engine is properly set up
2. Check the environment variable PYTHONPATH includes the MATLAB engine path
3. Try restarting your computer

## 2. CL Analysis Issues

### No Logger Attribute Error

**Symptom**: Error message like `'CLAnalysisDialog' object has no attribute 'logger'`

**Solution**:
1. Update to the latest version of the code which includes logger initialization
2. If using older code, add the logger initialization in `__init__` method:
   ```python
   def __init__(self, parent=None):
       super().__init__(parent)
       self.logger = logging.getLogger(__name__)
       # ...rest of code
   ```

### Directory Selection Problems

**Symptom**: The application crashes when selecting directories.

**Solution**:
1. Make sure the directories actually exist and are accessible
2. Check that you have read permissions for the selected directories
3. Try using the absolute path instead of a relative path

### No Normalized Files Found

**Symptom**: Warning that "No normalized files found" in the selected directory.

**Solution**:
1. Ensure the directory contains files with 'w' or 'wr' prefix
2. You may need to normalize the images first using the Normalize tool
3. Check that the files have the correct extension (.nii or .nii.gz)

## 3. File Format Issues

### NIFTI Format Problems

**Symptom**: "Failed to read NIFTI file" error.

**Solution**:
1. Verify the file is a valid NIFTI file using another tool
2. Try converting the file again from the original DICOM
3. Check the file extension matches the actual format (.nii or .nii.gz)

### DICOM Conversion Issues

**Symptom**: DICOM to NIFTI conversion fails.

**Solution**:
1. Ensure the DICOM files are valid and complete
2. Try a different directory with fewer files first
3. Check disk space and permissions in the output directory

## 4. Reporting and Debugging

If you encounter issues not covered in this guide:

1. Check the log files in the 'logs' directory
2. Run the application in debug mode:
   ```
   python -m pdb mispmsrc/ui/main_window.py
   ```
3. Contact support with:
   - The exact error message
   - Steps to reproduce
   - Log files
   - Screenshots of the error
