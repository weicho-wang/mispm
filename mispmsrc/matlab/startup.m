% MISPM Startup Script
% This script initializes the MATLAB environment for MISPM
% It should be added to the MATLAB path or called explicitly

try
    % Call the initialization function only once
    initialize_matlab();
    
    % Display message
    disp('MISPM environment ready');
catch ME
    % Display error if initialization fails
    disp(['Error initializing MISPM environment: ' ME.message]);
    disp(getReport(ME));
end
