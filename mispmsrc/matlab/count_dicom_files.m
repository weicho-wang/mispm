function count = count_dicom_files(dicom_dir)
% COUNT_DICOM_FILES Count the number of DICOM files in a directory
%
% This function attempts to count all DICOM files in a directory by
% checking file extensions and attempting to validate DICOM format
% for files without .dcm extension.
%
% Inputs:
%   dicom_dir - Directory containing DICOM files
%
% Outputs:
%   count - Number of DICOM files found

count = 0;

try
    % Check if directory exists
    if ~exist(dicom_dir, 'dir')
        fprintf('Error: Directory not found: %s\n', dicom_dir);
        return;
    end
    
    % First, count files with .dcm extension
    dcm_files = dir(fullfile(dicom_dir, '*.dcm'));
    known_dcm_count = length(dcm_files);
    
    fprintf('Found %d files with .dcm extension\n', known_dcm_count);
    count = known_dcm_count;
    
    % If no .dcm files found, check for DICOM files without standard extension
    if known_dcm_count == 0
        % Get all files in directory
        all_files = dir(dicom_dir);
        all_files = all_files(~[all_files.isdir]); % Remove directories
        
        % If there are too many files, just sample the first few
        sample_size = min(20, length(all_files));
        
        % No need to check if there are no files
        if isempty(all_files)
            fprintf('No files found in directory\n');
            return;
        end
        
        % Check a sample of files to see if they are DICOM
        dicom_found = false;
        
        for i = 1:sample_size
            file_path = fullfile(dicom_dir, all_files(i).name);
            
            try
                % Try to read DICOM header - will throw error if not DICOM
                header = dicominfo(file_path, 'UseVRHeuristic', false);
                
                % If we get here, the file is DICOM
                dicom_found = true;
                break;
            catch
                % Not a DICOM file, continue to next one
            end
        end
        
        if dicom_found
            % If we found at least one DICOM file, count all files as potential DICOMs
            % This is an approximation, but quicker than checking every file
            count = length(all_files);
            fprintf('Found DICOM files without .dcm extension, estimating %d total files\n', count);
        else
            fprintf('No DICOM files found in directory\n');
            count = 0;
        end
    end
    
catch ME
    fprintf('Error counting DICOM files: %s\n', ME.message);
    count = 0;
end
end
