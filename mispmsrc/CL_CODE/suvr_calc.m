function suvr = suvr_calc(PET_filepath,REF_img,ROI_img)
%UNTITLED Summary of this function goes here
%   Detailed explanation goes here

[x,y,z] = size(ROI_img);
[e,f,g] = ind2sub([x,y,z],find(ROI_img~=0));
NUM_ROI = length(e);

[o,p,q] = size(REF_img);
[h,i,j] = ind2sub([x,y,z],find(REF_img~=0));
NUM_REF = length(h);

PET_files = dir(fullfile(PET_filepath,'w*.nii'));

suvr = zeros(length(PET_files),1);

% calculations of SUVmean
for i=1:length(PET_files)
    PET_nii = load_nii([PET_filepath,PET_files(i).name]);
    PET_img = double(PET_nii.img);

    [x,y,z] = size(PET_img);
    [a,b,c] = ind2sub([x,y,z],find(isnan(PET_img)));
    for j=1:length(a)
        PET_img(a(j),b(j),c(j))=0;
    end

    roi = PET_img.*ROI_img;
    ref = PET_img.*REF_img;

    roi_sum = sum(sum(sum(roi)));
    ref_sum = sum(sum(sum(ref)));
    
    
    suv_roi = roi_sum/NUM_ROI;
    suv_ref = ref_sum/NUM_REF;
    
    SUVr = suv_roi/suv_ref;
    suvr(i,1) = SUVr;
    
end

end