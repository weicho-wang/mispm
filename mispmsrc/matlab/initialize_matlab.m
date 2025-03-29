% Initialize MATLAB environment for MISPM
% This script will be automatically run when the MATLAB engine starts

function initialize_matlab()
    % Display startup message
    disp('Initializing MATLAB environment for MISPM...');
    
    % Add project paths to the MATLAB path
    project_root = fileparts(fileparts(fileparts(mfilename('fullpath'))));
    addpath(genpath(fullfile(project_root, 'mispmsrc', 'matlab')));
    addpath(genpath(fullfile(project_root, 'mispmsrc', 'CLRefactoring')));
    
    % Initialize SPM if it's not already in the path
    if ~exist('spm', 'file')
        % Try to find SPM in the project directory
        spm_path = fullfile(project_root, 'spm12');
        if exist(spm_path, 'dir')
            addpath(spm_path);
            try
                spm('defaults', 'PET');
                disp('SPM initialized successfully with PET defaults');
            catch ME
                disp(['Warning: SPM initialization error: ' ME.message]);
            end
        else
            % Try using the SPM that is already on MATLAB path
            try
                spm('defaults', 'PET');
                disp('SPM found in MATLAB path and initialized with PET defaults');
            catch ME
                disp(['Warning: SPM not found or could not be initialized: ' ME.message]);
            end
        end
    else
        % SPM is already in the path, just initialize it
        try
            spm('defaults', 'PET');
            disp('SPM defaults set to PET');
        catch ME
            disp(['Warning: Could not set SPM defaults: ' ME.message]);
        end
    end
    
    disp('MATLAB environment initialization complete');
    
    % Remove the recursive call to initialize_matlab()
    % DO NOT call the function again here!
end
