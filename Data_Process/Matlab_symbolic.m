clc; clearvars

syms T_turb_in mdot_bp cp_air T_comp_out mdot_eg cp_eg T_cyl_out eta_mech mdot_air T_comp_in mdot_fuel cp_mix T_0 T_turb_out

eqns = [
    (mdot_air + mdot_bp) * cp_air * (T_comp_out - T_comp_in) - (mdot_air + mdot_bp + mdot_fuel) * cp_mix * (T_turb_in - T_turb_out) * eta_mech == 0, cp_mix * (mdot_air + mdot_fuel + mdot_bp) - cp_eg * (mdot_air + mdot_fuel) - cp_air * mdot_bp == 0 , (mdot_air + mdot_bp + mdot_fuel) * cp_mix * (T_turb_in - T_0) - (mdot_air + mdot_fuel) * cp_eg * (T_cyl_out - T_0) - mdot_bp * cp_air * (T_comp_out - T_0) == 0
    ];

S = solve(eqns,[mdot_bp , T_turb_in, cp_mix]) ;

S.mdot_bp
S.T_turb_in


% -(T_comp_in*cp_air*mdot_air - T_comp_out*cp_air*mdot_air + T_cyl_out*cp_eg*eta_mech*mdot_air + T_cyl_out*cp_eg*eta_mech*mdot_fuel - T_turb_out*cp_eg*eta_mech*mdot_air - T_turb_out*cp_eg*eta_mech*mdot_fuel)/
% (T_comp_in*cp_air - T_comp_out*cp_air + T_comp_out*cp_air*eta_mech - T_turb_out*cp_air*eta_mech)

% cp_air * mdot_air * (T_comp_out - T_comp_in) + (mdot_air + mdot_fuel) * cp_eg*eta_mech (T_turb_out - T_cyl_out)