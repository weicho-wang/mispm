function success = convert_dicom_to_nifti(dicom_dir, output_dir)
% CONVERT_DICOM_TO_NIFTI Convert DICOM files to NIFTI format
%
% Inputs:
%   dicom_dir - Directory containing DICOM files
%   output_dir - Directory where NIFTI files will be stored
%
% Outputs:
%   success - Boolean indicating if conversion was successful

% Initialize variables
success = false;
n_converted = 0;
n_failed = 0;

try
    % Validate inputs
    if ~exist(dicom_dir, 'dir')
        fprintf('Error: DICOM directory not found: %s\n', dicom_dir);
        return;
    end
    
    % Create output directory if it doesn't exist
    if ~exist(output_dir, 'dir')
        fprintf('Creating output directory: %s\n', output_dir);
        mkdir(output_dir);
    end
    
    % Get all DICOM files
    dcm_files = spm_select('FPList', dicom_dir, '.*\.dcm$');
    
    % If no specific .dcm files found, try to get all files (some DICOM files don't have .dcm extension)
    if isempty(dcm_files)
        fprintf('No .dcm files found, trying to find DICOM files without extension...\n');
        all_files = dir(dicom_dir);
        all_files = all_files(~[all_files.isdir]); % Remove directories
        
        % Create a cell array of file paths
        file_paths = cell(length(all_files), 1);
        for i = 1:length(all_files)
            file_paths{i} = fullfile(dicom_dir, all_files(i).name);
        end
        
        % Convert to char array for spm_dicom_headers
        if ~isempty(file_paths)
            dcm_files = char(file_paths);
        end
    end
    
    % Check if we found any files
    if isempty(dcm_files)
        fprintf('No DICOM files found in directory: %s\n', dicom_dir);
        return;
    end
    
    fprintf('Found %d potential DICOM files\n', size(dcm_files, 1));
    
    % Try to read DICOM headers
    fprintf('Reading DICOM headers...\n');
    try
        dcm_headers = spm_dicom_headers(dcm_files);
    catch ME
        fprintf('Error reading DICOM headers: %s\n', ME.message);
        
        % Try a more robust approach, checking each file individually
        fprintf('Attempting to find valid DICOM files individually...\n');
        valid_files = {};
        
        for i = 1:size(dcm_files, 1)
            file = deblank(dcm_files(i, :));
            try
                % Try to read as DICOM
                header = spm_dicom_headers(file);
                if ~isempty(header)
                    valid_files{end+1} = file;
                end
            catch
                % Skip this file
            end
        end
        
        if isempty(valid_files)
            fprintf('No valid DICOM files found in directory: %s\n', dicom_dir);
            return;
        end
        
        fprintf('Found %d valid DICOM files\n', length(valid_files));
        dcm_files = char(valid_files);
        dcm_headers = spm_dicom_headers(dcm_files);
    end
    
    fprintf('Read %d DICOM headers\n', length(dcm_headers));
    
    % Convert to NIFTI
    fprintf('Converting to NIFTI...\n');
    
    % Set output prefix - empty for no prefix
    output_prefix = '';
    
    % Create local function handle to determine output filename
    % This maintains the original filename structure while ensuring
    % a valid and unique output filename
    function nifti_filename = create_output_filename(header)
        try
            % Try to use the series description as base
            if isfield(header, 'SeriesDescription')
                base_name = header.SeriesDescription;
            elseif isfield(header, 'StudyDescription')
                base_name = header.StudyDescription;
            elseif isfield(header, 'PatientName')
                % Use PatientName and add SeriesNumber if available
                base_name = header.PatientName;
                if isfield(header, 'SeriesNumber')
                    base_name = sprintf('%s_Series%d', base_name, header.SeriesNumber);
                end
            else
                % Use a generic name with timestamp
                base_name = sprintf('dicom_series_%s', datestr(now, 'yyyymmdd_HHMMSS'));
            end
            
            % Clean the filename to make it valid
            base_name = regexprep(base_name, '\W', '_'); % Replace non-alphanumeric with underscores
            base_name = regexprep(base_name, '__+', '_'); % Replace multiple underscores with single
            base_name = strtrim(base_name); % Remove leading/trailing whitespace
            
            % Make sure the name starts with a letter
            if ~isletter(base_name(1))
                base_name = ['S_' base_name];
            end
            
            % Make sure it's not too long
            if length(base_name) > 50
                base_name = base_name(1:50);
            end
            
            % Add SeriesNumber to the end to ensure uniqueness if available
            if isfield(header, 'SeriesNumber')
                base_name = sprintf('%s_S%d', base_name, header.SeriesNumber);
            end
            
            % Add InstanceNumber if available
            if isfield(header, 'InstanceNumber')
                base_name = sprintf('%s_I%d', base_name, header.InstanceNumber);
            end
            
            % Create the full output filename
            nifti_filename = fullfile(output_dir, [output_prefix base_name '.nii']);
        catch
            % In case of any error, use a generic filename with timestamp
            timestamp = datestr(now, 'yyyymmdd_HHMMSS_FFF');
            nifti_filename = fullfile(output_dir, [output_prefix 'dicom_series_' timestamp '.nii']);
        end
    end
    
    % Process each unique series
    unique_series = spm_dicom_sortcond(dcm_headers);
    
    for i = 1:numel(unique_series)
        try
            series_headers = dcm_headers(unique_series{i});
            
            % Get output filename
            nifti_filename = create_output_filename(series_headers{1});
            
            % Log the conversion
            fprintf('Converting series %d/%d to: %s\n', i, numel(unique_series), nifti_filename);
            
            % Convert the series
            conversion_result = spm_dicom_convert(series_headers, 'all', 'flat', 'nii', output_dir, output_prefix);
            
            % Verify conversion success - check if files were created
            if ~isempty(conversion_result.files)
                n_converted = n_converted + 1;
                fprintf('Successfully converted series %d/%d\n', i, numel(unique_series));
            else
                n_failed = n_failed + 1;
                fprintf('Failed to convert series %d/%d\n', i, numel(unique_series));
            end
        catch ME
            n_failed = n_failed + 1;
            fprintf('Error converting series %d/%d: %s\n', i, numel(unique_series), ME.message);
        end
    end
    
    % Report results
    fprintf('Conversion complete: %d series converted, %d series failed\n', n_converted, n_failed);
    
    % Set success if at least one series was converted
    success = (n_converted > 0);
    
catch ME
    fprintf('Error in DICOM to NIFTI conversion: %s\n', ME.message);
    fprintf('Error details: %s\n', getReport(ME));
    success = false;
end
end
