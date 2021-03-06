import numpy as np
import pandas as pd
import fillerfunctions as ff
import coolingsystems as cs
import preprocessingO as ppo
import CoolProp.CoolProp as cp
from energyanalysis import propertyCalculator
from helpers import d2df
from helpers import polyvalHelperFunction


def mainEngineProcessing(raw, processed, dict_structure, CONSTANTS, hd):
    # This script summarizes all the functions that calculate the required data for the Main Engines different flows
    # Reading existing values
    processed = readMainEnginesExistingValues(raw, processed, CONSTANTS, hd)
    processed = ppo.engineStatusCalculation("MainEngines", raw, processed, CONSTANTS, hd, dict_structure)
    processed = cs.coolingFlows(processed, CONSTANTS, "MainEngines")
    processed = ff.systemFill(processed, dict_structure, CONSTANTS, "MainEngines", "ME-1.1")
    processed = ff.systemFill(processed, dict_structure, CONSTANTS, "MainEngines", "ME-1.2")
    # Calculating the main engines fuel flows
    processed = mainEngineFuelFlowCalculation(raw, processed, CONSTANTS, hd)
    # Calculating the main engines power output
    processed = mainEnginePowerCalculation(processed, CONSTANTS)
    # Calculating engine load, that is used many times later on
    processed = ppo.engineLoadCalculation("MainEngines", raw, processed, CONSTANTS, hd)
    # Calculating air and exhaust gas flows in the main engines
    processed = mainEngineAirFlowCalculation(raw, processed, dict_structure, CONSTANTS)
    processed = ff.systemFill(processed, dict_structure, CONSTANTS, "MainEngines", "ME-2.1")
    processed = ff.systemFill(processed, dict_structure, CONSTANTS, "MainEngines", "ME-2.2")
    processed = propertyCalculator(processed, dict_structure, CONSTANTS, ["ME1", "ME2", "ME3", "ME4"])
    processed = mainEngineAirFlowPostCalculation(processed, dict_structure, CONSTANTS)
    # Calculating cooling flows
    processed = cs.engineCoolingSystemsCalculation(processed, CONSTANTS, "MainEngines")
    processed = ff.systemFill(processed, dict_structure, CONSTANTS, "MainEngines", "ME-3.1")
    processed = ff.systemFill(processed, dict_structure, CONSTANTS, "MainEngines", "ME-3.2")
    return processed


def readMainEnginesExistingValues(raw, processed, CONSTANTS, hd):
    print("Started reading main engines raw values...", end="", flush=True)
    # This function only reads existing series. It does not do any pre-processing action.
    for system in CONSTANTS["General"]["NAMES"]["MainEngines"]:
        # Reading main engines exhaust gas temperature, TC inlet and outlet
        processed[d2df(system,"Cyl","EG_out","T")] = raw[hd[system + "-TC_EG_T_IN"]] + 273.15  # Measured before mixer with flow form bypass
        processed[d2df(system,"Turbine","Mix_out","T")] = raw[hd[system + "-TC_EG_T_OUT"]] + 273.15  # Measured after mixer with waste gate
        # Reading main engines exhaust gas temperature, after HRSG. Only two of the four main engines have the HRSG
        if system=="ME2" or system=="ME3":
            processed[d2df(system,"HRSG","Mix_out","T")] = raw[hd[system + "-EGB_EG_T_OUT"]] + 273.15
            processed[d2df(system,"HRSG","Mix_in","T")] = raw[hd[system + "-TC_EG_T_OUT"]] + 273.15
        # Temperature in the engine room, i.e. inlet to the compressor of the TC
        processed[d2df(system,"Comp","Air_in","T")] = raw[hd["ER-FWD_AIR_T_"]] + 273.15
        # Reading the HT temperature before and after the main engine
        processed[d2df(system,"JWC","HTWater_in","T")] = raw[hd[system + "-HT_FW_T_IN"]] + 273.15
        #processed[d2df(system, "CAC_HT", "HTWater_out", "T")] = raw[hd[system + "-HT_FW_T_OUT"]] + 273.15
        # Reading the LT temperature before the main engine
        processed[d2df(system,"CAC_LT","LTWater_in","T")] = raw[hd[system + "-LT_FW_T_IN"]] + 273.15
        # Reading the Lubricating oil temperature before and after the Lubricating Oil Cooler (hence, In is higher)
        processed[d2df(system,"LOC","LubOil_out","T")] = raw[hd[system + "-LOC_OIL_T_OUT"]] + 273.15
        # Reading fuel oil temperature before injection
        processed[d2df(system,"Cyl","FuelPh_in","T")] = raw[hd[system + "-CYL_FUEL_T_IN"]] + 273.15
        # Reading charge air temperature, after the charge air cooler (or at cylinder inlet)
        processed[d2df(system,"CAC_LT","Air_out","T")] = raw[hd[system + "-CAC_AIR_T_OUT"]] + 273.15
        # Reading Engine rpm
        processed[d2df(system,"Cyl","Power_out","omega")] = raw[hd[system + "__RPM_"]]
        # Pressure of the charge air, at the compressor outlet (and, hence, at the cylinder inlet)
        processed[d2df(system, "Comp", "Air_out", "p")] = (raw[hd[system + "-CAC_AIR_P_OUT"]] + 1.01325) * 100000
        # Reading the pressure of the lubricating oil
        # processed[d2df(system, "LOC", "LubOil_out", "p")] = (raw[hd[system + "-LOC_OIL_P_IN"]] + 1.01325) * 100000
        # Reading the pressure in the cooling flows
        processed[d2df(system, "CAC_LT", "LTWater_in", "p")] = (raw[hd[system + "-LT-CAC_FW_P_IN"]] + 1.01325) * 100000
        processed[d2df(system, "JWC", "HTWater_in", "p")] = (raw[hd[system + "-HT-JWC_FW_P_IN"]] + 1.01325) * 100000
        # Reading turbocharger speed
        processed[d2df(system, "TCshaft", "Power_in", "omega")] = raw[hd[system+"-TC__RPM_"]]
        processed[d2df(system, "TCshaft", "Power_out", "omega")] = raw[hd[system + "-TC__RPM_"]]
        processed[d2df(system, "Turbine", "Power_out", "omega")] = raw[hd[system + "-TC__RPM_"]]
        processed[d2df(system, "Compressor", "Power_in", "omega")] = raw[hd[system + "-TC__RPM_"]]


    print("...done!")
    return processed





def mainEngineFuelFlowCalculation(raw, processed, CONSTANTS, hd):
    print("Started calculating main engine fuel flows...", end="", flush=True)
    # This function calculates the engine
    for system in CONSTANTS["General"]["NAMES"]["MainEngines"]:
        # This function calculates the fuel flow of the main engines
        # In the case of the main engines, the fuel flow of an engine is calculated given its fuel
        # rack position and its rotating speed.
        fuel_rack_position = CONSTANTS["MainEngines"]["FRP_2_MFR"]["FRP_MIN"][system] + (CONSTANTS["MainEngines"]["FRP_2_MFR"]["FRP_MAX"][system]-CONSTANTS["MainEngines"]["FRP_2_MFR"]["FRP_MIN"][system]) * raw[hd[system+"__FRP_"]]/100
        # Temporarily, only the ISO fuel flow is calculated
        processed[d2df(system,"Cyl","FuelPh_in","mdot")] = CONSTANTS["MainEngines"]["MFR_FUEL_DES_ISO"] * (
            (CONSTANTS["MainEngines"]["FRP_2_MFR"]["POLY"][system][0] + CONSTANTS["MainEngines"]["FRP_2_MFR"]["POLY"][system][1] * fuel_rack_position) /
            (CONSTANTS["MainEngines"]["FRP_2_MFR"]["POLY"][system][0] + CONSTANTS["MainEngines"]["FRP_2_MFR"]["POLY"][system][1] * CONSTANTS["MainEngines"]["FRP_DES"][system])) * (
            processed[d2df(system,"Cyl","Power_out","omega")] / CONSTANTS["MainEngines"]["RPM_DES"])
    print("...done!")
    return processed


def mainEnginePowerCalculation(processed, CONSTANTS):
    print("Started calculating main engine power...", end="", flush=True)
    # This function calculates the Power of the engine starting from the efficiency of the engine,
    # which is calcualted starting from other available data
    for system in CONSTANTS["General"]["NAMES"]["MainEngines"]:
        # Calculate fuel flow-based engine load
        fuel_based_load = processed[d2df(system,"Cyl","FuelPh_in","mdot")] / CONSTANTS["MainEngines"]["MFR_FUEL_DES_ISO"]
        # Calculate ISO bsfc (break specific fuel consumption)
        bsfc_iso = fuel_based_load.apply(polyvalHelperFunction, args=(CONSTANTS["MainEngines"]["POLY_FUEL_LOAD_2_BSFC_ISO"],))
        # Corrects the bsfc from ISO conditions to "real" conditions
        (bsfc,LHV) = ppo.bsfcISOCorrection(bsfc_iso,processed[d2df(system,"CAC_LT","Air_out","T")],processed[d2df(system,"CAC_LT","LTWater_in","T")],processed[d2df(system,"Cyl","FuelPh_in","T")],CONSTANTS)
        # Calculates the real fuel flow using the ISO conversion
        processed[d2df(system,"Cyl","FuelPh_in","mdot")] = processed[d2df(system,"Cyl","FuelPh_in","mdot")] * bsfc / bsfc_iso
        # Calculates the power of the engine as mfr/bsfc, with unit conversion to get the output in kW
        # Shaft energy out
        processed[d2df(system,"Cyl","Power_out","Edot")] = processed[d2df(system,"Cyl","FuelPh_in","mdot")] / bsfc * 1000 * 3600
        # Chemical energy in the fuel
        processed[d2df(system,"Cyl","FuelCh_in","Edot")] = processed[d2df(system,"Cyl","FuelPh_in","mdot")] * LHV
    print("...done!")
    return processed





def mainEngineAirFlowCalculation(raw, processed, dict_structure, CONSTANTS):
    print("Started calculating main engine air and exhaust flows...", end="", flush=True)
    # This function calculates the different air and exhaust gas flows in the main engines, taking into account the
    # presence of air bypass and exhaust wastegate valves
    for system in CONSTANTS["General"]["NAMES"]["MainEngines"]:
        # Calculating the compressor's compression ratio
        beta_comp = processed[d2df(system,"Comp","Air_out","p")] / processed[d2df(system,"Comp","Air_in","p")]
        # Calculating the turbocharger's mechancial efficiency based on the regression
        eta_tc = (processed[d2df(system, "TCshaft", "Power_in", "omega")]/CONSTANTS["MainEngines"]["RPM_TC_DES"]).apply(polyvalHelperFunction,args=(CONSTANTS["MainEngines"]["POLY_TC_RPM_2_ETA_MECH"],))
        #  Calculating the compressor isentropic efficiency
        comp_isentropic_efficiency = beta_comp.apply(polyvalHelperFunction,args=(CONSTANTS["MainEngines"]["POLY_PIN_2_ETA_IS"],))
        # Calculating the temperature after the compressor, based on ideal gas assumption
        T_Comp_out_iso = processed[d2df(system,"Comp","Air_in","T")] * beta_comp**((CONSTANTS["General"]["K_AIR"]-1)/CONSTANTS["General"]["K_AIR"])
        T_Comp_out = processed[d2df(system,"Comp","Air_in","T")] + (T_Comp_out_iso - processed[d2df(system,"Comp","Air_in","T")]) / comp_isentropic_efficiency
        #### NOTE: HERE WE MAKE THE ASSUMPTION THAT THE COMPRESSOR OUTLET TEMPERATURE CANNOT BE LOWER THAN THE CYLINDER INLET TEMPERATURE
        T_Comp_out[T_Comp_out < processed[d2df(system, "Cyl", "Air_in", "T")]] = processed.loc[T_Comp_out < processed[d2df(system, "Cyl", "Air_in", "T")], d2df(system, "Cyl", "Air_in", "T")]
        processed[d2df(system, "Comp", "Air_out", "T")] = T_Comp_out
        # Calculating the air inflow aspired by the cylinder: calculated as inlet air density times the maximum volume,
        # times the engine speed
        processed[d2df(system,"Cyl","Air_in","mdot")] = CONSTANTS["MainEngines"]["AIR_FLOW_MULT"] * CONSTANTS["MainEngines"]["V_MAX"] * (
            processed[d2df(system,"Comp","Air_out","p")]) / (
            CONSTANTS["General"]["R_AIR"] * processed[d2df(system,"Cyl","Air_in","T")]) * (
            processed[d2df(system,"Cyl","Power_out","omega")] / 60 / 2 * CONSTANTS["General"]["ETA_VOL"]) * (
            CONSTANTS["MainEngines"]["N_CYL"])
        processed[d2df(system,"Cyl","EG_out","mdot")] = processed[d2df(system,"Cyl","Air_in","mdot")] + processed[d2df(system,"Cyl",
            "FuelPh_in","mdot")]
        # Calculating the bypass flow
        #processed[d2df(system,"BPsplit","BP_out","mdot")] = (
        #    CONSTANTS["General"]["CP_AIR"] * processed[d2df(system,"Cyl","Air_in","mdot")] * (processed[d2df(system,"Comp","Air_out","T")] - processed[d2df(system,"Comp","Air_in","T")]) +
        #   CONSTANTS["General"]["CP_EG"] * CONSTANTS["MainEngines"]["ETA_MECH_TC"] * (processed[d2df(system,"Cyl","Air_in","mdot")] + processed[d2df(system,"Cyl","FuelPh_in","mdot")]) *
        #    (processed[d2df(system,"Turbine","Mix_out","T")] - processed[d2df(system,"Cyl","EG_out","T")])) / (
        #    CONSTANTS["General"]["CP_AIR"] * (
        #        processed[d2df(system,"Comp","Air_in","T")] - CONSTANTS["MainEngines"]["ETA_MECH_TC"] * processed[d2df(system,"Turbine","Mix_out","T")] -
        #        (CONSTANTS["MainEngines"]["ETA_MECH_TC"] - 1) * processed[d2df(system,"Comp","Air_out","T")]))
        num1 = eta_tc * processed[d2df(system,"Cyl","EG_out","mdot")] * CONSTANTS["General"]["CP_EG"] * (processed[d2df(system,"Cyl","EG_out","T")] - processed[d2df(system,"Turbine","Mix_out","T")])
        num2 = processed[d2df(system, "Cyl", "Air_in", "mdot")] * CONSTANTS["General"]["CP_AIR"] * (processed[d2df(system, "Comp", "Air_out", "T")] - processed[d2df(system, "Comp", "Air_in", "T")])
        den1 = CONSTANTS["General"]["CP_AIR"] * (processed[d2df(system, "Comp", "Air_out", "T")] - processed[d2df(system, "Comp", "Air_in", "T")])
        den2 = eta_tc * CONSTANTS["General"]["CP_AIR"] * (processed[d2df(system, "Turbine", "Mix_out", "T")] - processed[d2df(system, "Comp", "Air_out", "T")])
        processed[d2df(system, "BPsplit", "BP_out", "mdot")] = (num1 - num2) / (den1 + den2)
        # Calculating the temperature of the mixture after the merge between bypass and exhaust gas from the cylinders
        processed[d2df(system,"Turbine","Mix_in","T")] = (
            processed[d2df(system,"BPsplit","BP_out","mdot")] * CONSTANTS["General"]["CP_AIR"] * processed[d2df(system,"Comp","Air_out","T")] +
            processed[d2df(system,"Cyl","EG_out","mdot")] * CONSTANTS["General"]["CP_EG"] * processed[d2df(system,"Cyl","EG_out","T")]) / (
            processed[d2df(system,"Cyl","EG_out","mdot")] * CONSTANTS["General"]["CP_EG"] +
            processed[d2df(system,"BPsplit","BP_out","mdot")] * CONSTANTS["General"]["CP_AIR"])
        # The air mass flow going through the compressor is equal to the sum of the air flow through the bypass valve and to the cylinders
        processed[d2df(system, "BPsplit", "Air_in", "mdot")] = processed[d2df(system,"BPsplit","BP_out","mdot")] + processed[d2df(system,"Cyl","Air_in","mdot")]
        # The flow through the turbine is equal to the sum of the bypass flow and the exhaust coming from the cylinders
        processed[d2df(system,"BPmerge","Mix_out","mdot")] = processed[d2df(system,"BPsplit","BP_out","mdot")] + processed[d2df(system,"Cyl","EG_out","mdot")]
        # Assiging the mass flow values for the HRSGs otherwise it makes a mess
        if system in {"ME2", "ME3"}:
            processed[d2df(system, "HRSG", "Mix_in", "mdot")] = processed[d2df(system,"BPmerge","Mix_out","mdot")]
            processed[d2df(system, "HRSG", "Mix_out", "mdot")] = processed[d2df(system, "BPmerge", "Mix_out", "mdot")]

    print("...done!")
    return processed

def mainEngineAirFlowPostCalculation(processed, dict_structure, CONSTANTS):
    # This function does the post-analysis after the various properties have been calculated
    print("Started calculating main engine air and exhaust flows...", end="", flush=True)
    for system in CONSTANTS["General"]["NAMES"]["MainEngines"]:
        # Calculating the turbine's power output to the compressor
        processed[d2df(system, "Turbine", "Power_out", "Edot")] = processed[d2df(system,"BPmerge","Mix_out","mdot")] * (
            processed[d2df(system, "Turbine", "Mix_in", "h")] - processed[d2df(system,"Turbine","Mix_out","h")])
        # Calculating the compressor's power input.
        processed[d2df(system, "Comp", "Power_in", "Edot")] = processed[d2df(system, "BPsplit", "Air_in", "mdot")] * (
            processed[d2df(system, "Comp", "Air_out", "h")] - processed[d2df(system, "Comp", "Air_in", "h")])
        # Losses at the TC shaft level are calculated
        processed[d2df(system, "TCshaft", "Losses_out", "Edot")] = processed[d2df(system, "Turbine", "Power_out", "Edot")] - processed[d2df(system, "Comp", "Power_in", "Edot")]
    return processed