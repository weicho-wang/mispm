function show_coregister_help()
% SHOW_COREGISTER_HELP Display help information for coregistration parameters
%
% This function provides information about valid cost functions and other
% parameters for coregistration in SPM.

disp('===== SPM Coregistration Helper =====');
disp('Valid cost functions for spm_coreg:');
disp('  ''mi''  - Mutual Information');
disp('  ''nmi'' - Normalized Mutual Information (default, recommended)');
disp('  ''ecc'' - Entropy Correlation Coefficient');
disp('  ''ncc'' - Normalized Cross Correlation');
disp('');
disp('Common User-Friendly Names (all will be mapped to proper SPM names):');
disp('  ''mutual information'', ''mutual_information'' -> ''mi''');
disp('  ''normalized mutual information'', ''normalised mutual information'' -> ''nmi''');
disp('  ''entropy correlation coefficient'', ''entropy_correlation_coefficient'' -> ''ecc''');
disp('  ''normalized cross correlation'', ''normalised cross correlation'' -> ''ncc''');
disp('');
disp('Default Values:');
disp('  cost_function - ''nmi'' (Normalized Mutual Information)');
disp('  separation    - [4 2] (mm)');
disp('  tolerance     - [0.02 0.02 0.02 0.001 0.001 0.001 0.01 0.01 0.01 0.001 0.001 0.001]');
disp('  smoothing     - [7 7] (mm FWHM)');
disp('');
disp('For debugging cost function issues:');
disp('  1. Make sure you''re using one of the valid cost functions listed above');
disp('  2. Check that the reference and source images are valid NIFTI files');
disp('  3. Try the default ''nmi'' if other cost functions fail');
disp('=======================================');
end
