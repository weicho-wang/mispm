function success = coregister(ref_image, source_image, cost_function)
% COREGISTER Simple wrapper function for coregistration
%
% Simplifies calling from Python by handling path normalization
% and error reporting

% Default cost function if not specified
if nargin < 3 || isempty(cost_function)
    cost_function = 'nmi';
end

try
    % Ensure the paths use the right separators for the OS
    if ispc
        ref_image = strrep(ref_image, '/', '\');
        source_image = strrep(source_image, '/', '\');
    else
        ref_image = strrep(ref_image, '\', '/');
        source_image = strrep(source_image, '\', '/');
    end
    
    % Verify files exist
    if ~exist(ref_image, 'file')
        error('Reference image not found: %s', ref_image);
    end
    
    if ~exist(source_image, 'file')
        error('Source image not found: %s', source_image);
    end
    
    % Get paths for output
    [source_dir, source_name, source_ext] = fileparts(source_image);
    output_image = fullfile(source_dir, ['r' source_name source_ext]);
    
    % Display info
    fprintf('Reference image: %s\n', ref_image);
    fprintf('Source image: %s\n', source_image);
    fprintf('Output will be: %s\n', output_image);
    
    % Process cost function parameter to ensure it's valid for SPM
    % SPM accepts: 'mi', 'nmi', 'ecc', 'ncc'
    cost_function = lower(strtrim(cost_function));
    
    % Map user-friendly names to SPM's internal names
    switch cost_function
        case {'mi', 'mutual_information', 'mutual information'}
            cost_function = 'mi';
        case {'nmi', 'normalized_mutual_information', 'normalised_mutual_information', 'normalized mutual information', 'normalised mutual information'}
            cost_function = 'nmi';
        case {'ecc', 'entropy_correlation_coefficient', 'entropy correlation coefficient'}
            cost_function = 'ecc';
        case {'ncc', 'normalized_cross_correlation', 'normalised_cross_correlation', 'normalized cross correlation', 'normalised cross correlation'}
            cost_function = 'ncc';
        otherwise
            fprintf('Warning: Unknown cost function "%s", defaulting to "nmi"\n', cost_function);
            cost_function = 'nmi';
    end
    
    fprintf('Using cost function: %s\n', cost_function);
    
    % Run core coregistration
    % Stage 1: Load volumes
    fprintf('Loading image volumes...\n');
    ref_vol = spm_vol(ref_image);
    source_vol = spm_vol(source_image);
    
    % Stage 2: Calculate transformation parameters
    fprintf('Calculating transformation parameters...\n');
    flags = struct('cost_fun', cost_function, 'sep', [4 2], 'tol', [0.02 0.02 0.02 0.001 0.001 0.001 0.01 0.01 0.01 0.001 0.001 0.001], 'fwhm', [7 7]);
    x = spm_coreg(ref_vol, source_vol, flags);
    
    % Stage 3: Apply transformation to header
    fprintf('Applying transformation...\n');
    M = spm_matrix(x);
    spm_get_space(source_vol.fname, source_vol.mat / M);
    
    % Stage 4: Create resliced image
    fprintf('Reslicing image...\n');
    P = {ref_vol.fname; source_vol.fname};
    flags = struct('interp', 1, 'mask', true, 'mean', false, 'which', 1, 'prefix', 'r');
    spm_reslice(P, flags);
    
    % Check if output file was created
    if exist(output_image, 'file')
        fprintf('Coregistration completed successfully: %s\n', output_image);
        success = true;
    else
        fprintf('WARNING: Output file not found: %s\n', output_image);
        success = false;
    end
    
catch ME
    % Report error and set success flag to false
    fprintf('ERROR in coregistration: %s\n', ME.message);
    fprintf('%s\n', getReport(ME));
    success = false;
end
end
