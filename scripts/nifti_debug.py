#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
NIFTI File Debugging Script

This script helps diagnose issues with NIFTI files that are difficult to load.
"""

import os
import sys
import nibabel as nib
import numpy as np
import argparse

def inspect_nifti(nifti_path):
    """Inspect a NIFTI file and print detailed information about it."""
    print(f"Inspecting NIFTI file: {nifti_path}")
    print(f"File exists: {os.path.exists(nifti_path)}")
    
    if not os.path.exists(nifti_path):
        print("ERROR: File does not exist!")
        return
    
    try:
        print(f"File size: {os.path.getsize(nifti_path)} bytes")
        
        # Try to load the header directly first
        print("\nAttempting to load header...")
        try:
            nifti_header = nib.load(nifti_path).header
            print(f"Header successfully loaded")
            print(f"NIFTI version: {nifti_header.get_value_label('sizeof_hdr')}")
            print(f"Data dimensions: {nifti_header.get_data_shape()}")
            print(f"Data type: {nifti_header.get_data_dtype()}")
            print(f"Voxel dimensions: {nifti_header.get_zooms()}")
            print(f"Header info:")
            for field in nifti_header:
                print(f"  {field}: {nifti_header[field]}")
        except Exception as e:
            print(f"Error loading header: {str(e)}")
        
        # Try to load the full image
        print("\nAttempting to load full image...")
        nifti_img = nib.load(nifti_path)
        print(f"Image successfully loaded: {nifti_img}")
        print(f"Image shape: {nifti_img.shape}")
        print(f"Affine matrix:")
        print(nifti_img.affine)
        
        # Try to load the data
        print("\nAttempting to load data...")
        try:
            data = nifti_img.get_fdata()
            print(f"Data successfully loaded")
            print(f"Data shape: {data.shape}")
            print(f"Data type: {data.dtype}")
            print(f"Data range: {np.min(data)} to {np.max(data)}")
            print(f"Data statistics:")
            print(f"  Mean: {np.mean(data)}")
            print(f"  Std: {np.std(data)}")
            print(f"  NaN values: {np.isnan(data).sum()}")
            print(f"  Inf values: {np.isinf(data).sum()}")
        except Exception as e:
            print(f"Error loading data: {str(e)}")
        
        # If 4D or higher, show info about each volume
        if len(nifti_img.shape) > 3:
            print(f"\nThis is a {len(nifti_img.shape)}D dataset with {nifti_img.shape[3]} volumes")
            try:
                for vol_idx in range(min(nifti_img.shape[3], 10)):  # Show up to 10 volumes
                    vol_data = nifti_img.dataobj[..., vol_idx]
                    print(f"  Volume {vol_idx}:")
                    print(f"    Range: {np.min(vol_data)} to {np.max(vol_data)}")
                    print(f"    Mean: {np.mean(vol_data)}")
            except Exception as e:
                print(f"Error analyzing volumes: {str(e)}")
        
    except Exception as e:
        print(f"Error inspecting NIFTI file: {str(e)}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inspect NIFTI files for debugging purposes")
    parser.add_argument("nifti_path", help="Path to the NIFTI file to inspect")
    
    if len(sys.argv) > 1:
        args = parser.parse_args()
        inspect_nifti(args.nifti_path)
    else:
        # If no arguments provided, ask for file path
        nifti_path = input("Enter path to NIFTI file: ")
        inspect_nifti(nifti_path)
