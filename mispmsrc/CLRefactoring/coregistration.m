function success = coregistration(ref_image, source_image, cost_function, other_images)
% COREGISTRATION Perform coregistration between reference and source images
%
% INPUTS:
%   ref_image      - Path to reference image (target)
%   source_image   - Path to source image (to be coregistered)
%   cost_function  - Cost function to use ('mi', 'nmi', 'ecc', 'ncc')
%   other_images   - Cell array of other images to coregister with same parameters (optional)
%
% OUTPUTS:
%   success        - Boolean indicating success/failure

% Initialize
success = false;

try
    % Verify inputs
    if nargin < 3 || isempty(cost_function)
        cost_function = 'nmi'; % Default to normalized mutual information
    end
    
    if nargin < 4
        other_images = {};
    elseif ~iscell(other_images)
        other_images = {other_images}; % Convert to cell array if single string
    end
    
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
    
    % Load volumes
    ref_vol = spm_vol(ref_image);
    source_vol = spm_vol(source_image);
    
    % Get file details for output
    [source_path, source_name, source_ext] = fileparts(source_image);
    
    % Set options
    flags = struct();
    flags.cost_fun = cost_function;  % Now properly validated
    flags.sep = [4 2]; % Sampling separation in mm
    flags.tol = [0.02 0.02 0.02 0.001 0.001 0.001 0.01 0.01 0.01 0.001 0.001 0.001]; % Tolerances
    flags.fwhm = [7 7]; % Smoothing for both images
    
    % Display info
    fprintf('Coregistering %s to %s using %s\n', source_image, ref_image, flags.cost_fun);
    
    % Run coregistration estimation
    fprintf('Running coregistration estimation...\n');
    x = spm_coreg(ref_vol, source_vol, flags);
    
    % Create transformation matrix
    M = inv(spm_matrix(x));
    
    % Apply transformation to source image
    fprintf('Applying transformation to source image...\n');
    MM = source_vol.mat\M*source_vol.mat;
    spm_get_space(source_vol.fname, MM\source_vol.mat);
    
    % Apply transformation to other images if provided
    if ~isempty(other_images)
        fprintf('Applying transformation to %d other images...\n', length(other_images));
        for i = 1:length(other_images)
            try
                other_vol = spm_vol(other_images{i});
                spm_get_space(other_vol.fname, MM\other_vol.mat);
                fprintf('  Applied to: %s\n', other_images{i});
            catch other_err
                fprintf('  Failed to apply to: %s (%s)\n', other_images{i}, other_err.message);
            end
        end
    end
    
    % Reslice the images
    fprintf('Reslicing images...\n');
    spm_reslice({ref_vol.fname, source_vol.fname}, struct('prefix', 'r', 'interp', 1, 'which', 1));
    
    % Display success message
    fprintf('Coregistration completed successfully\n');
    success = true;
    
catch ME
    % Display error message
    fprintf('Error during coregistration: %s\n', ME.message);
    fprintf('Error details: %s\n', getReport(ME));
    success = false;
end
end
