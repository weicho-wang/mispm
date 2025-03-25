clc
clear all

% filepath_mask_whole Cerebellum
REF_nii = load_nii('./Centiloid_Std_VOI/Centiloid_Std_VOI/nifti/2mm/voi_WhlCbl_2mm.nii');
REF_img = double(REF_nii.img);

% filepath_mask_ROI
ROI_nii = load_nii('./Centiloid_Std_VOI/Centiloid_Std_VOI/nifti/2mm/voi_ctx_2mm.nii');
ROI_img = double(ROI_nii.img);


% filepath_nii_PET
% filepath_nii_PET_AD
ad_PET_filepath = ('./AD-100_PET_5070/AD-100_PET_5070/nifti/');

% filepath_nii_PET_YC
yc_PET_filepath = ('./YC-0_PET_5070/YC-0_PET_5070/nifti/');

% calculations of SUVr & CLs (11C-PIB)
% FOR Verifying the method
ad_SUVr = suvr_calc(ad_PET_filepath,REF_img,ROI_img);
yc_SUVr = suvr_calc(yc_PET_filepath,REF_img,ROI_img);
[ad_CL, yc_CL,SUVr_yc_mean,SUVr_ad_mean] = CL_calc_test(ad_SUVr,yc_SUVr);

SUVr_ = [ad_SUVr;yc_SUVr];
CL_ = [ad_CL;yc_CL];


% Verifying the calculated data with standard data

% load the standard data
standard_data = readtable('./SupplementaryTable1.xlsx');
AD_SUVR = standard_data.Var3(2:46);
AD_CL = standard_data.Var7(2:46);

YC_SUVR = standard_data.Var3(48:end);
YC_CL = standard_data.Var7(48:end);

SUVR = [AD_SUVR;YC_SUVR];
CL = [AD_CL;YC_CL];

% linear 
p1 = polyfit(SUVR,SUVr_,1);
p2 = polyfit(CL,CL_,1);

% correlation
r1 = corrcoef(SUVR,SUVr_);
r2 = corrcoef(CL,CL_);

r1_sq = r1(1,2)^2;
r2_sq = r2(1,2)^2;

% plot 
figure;
plot(AD_SUVR,ad_SUVr,'*r',YC_SUVR,yc_SUVr,'*b',SUVR,polyval(p1,SUVR),'-');
legend('AD', 'YC',['y=',num2str(p1(1)),'x+',num2str(p1(2)),' & r^2=',num2str(r1_sq)],'Location','northwest')
xlabel('PIB SUVR GAAIN');
ylabel('PIB SUVR calc');
title('PIB SUVR TEST');

figure;
plot(AD_CL,ad_CL,'*r',YC_CL,yc_CL,'*b',CL,polyval(p2,CL),'-');
legend('AD', 'YC',['y=',num2str(p2(1)),'x+',num2str(p2(2)),' & r^2=',num2str(r1_sq)],'Location','northwest')
xlabel('PIB CL GAAIN');
ylabel('PIB CL calc');
title('PIB CL TEST');
