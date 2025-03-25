function [ad_CL, yc_CL,SUVr_yc_mean,SUVr_ad_mean] = CL_calc_test(ad_SUVr,yc_SUVr)
%UNTITLED2 Summary of this function goes here
%   Detailed explanation goes here

SUVr_ad_mean = mean(ad_SUVr);
SUVr_yc_mean = mean(yc_SUVr);
ad_CL = ad_SUVr;
yc_CL = yc_SUVr;

for i=1:length(ad_SUVr)
    CL = (ad_SUVr(i)-SUVr_yc_mean)/(SUVr_ad_mean-SUVr_yc_mean)*100;
    ad_CL(i) = CL;
end

for i=1:length(yc_SUVr)
    CL = (yc_SUVr(i)-SUVr_yc_mean)/(SUVr_ad_mean-SUVr_yc_mean)*100;
    yc_CL(i) = CL;
end

end