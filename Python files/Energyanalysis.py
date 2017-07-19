# Temporarily empty
import CoolProp.CoolProp as cp
import numpy as np
import pandas as pd
import preprocessingO as ppo
from helpers import d2df
import os



def energyAnalysisLauncher(processed, dict_structure, CONSTANTS):
    processed = propertyCalculator(processed, dict_structure, CONSTANTS)  # Calculates the energy and exergy flows
    processed = efficiencyCalculator(processed, dict_structure, CONSTANTS)
    return processed




def propertyCalculator(processed, dict_structure, CONSTANTS):
    print("Started calculating flow properties...", end="", flush=True)
    df_index = processed.index
    for system in dict_structure["systems"]:
        for unit in dict_structure["systems"][system]["units"]:
            for flow in dict_structure["systems"][system]["units"][unit]["flows"]:
                if processed[d2df(system,unit,flow,"Bdot")].isnull().sum() == len(processed[d2df(system,unit,flow,"Bdot")]):
                    if dict_structure["systems"][system]["units"][unit]["flows"][flow]["type"] == "CPF":
                        # Only doing the calculations if the values for p and T are not NaN
                        if processed[d2df(system,unit,flow,"T")].isnull().sum() != len(processed[d2df(system,unit,flow,"T")]) :
                            temp = processed[d2df(system,unit,flow,"T")]  # .values()
                            # If the specific enthalpy is available already, it needs to be calculated
                            if ("Air" in flow) or ("BP" in flow):
                                # print("Calculating properties for " + system + "_" + unit + "_" + flow)
                                # dh = pd.Series(cp.PropsSI('H','T',np.array(temp),'P',np.array(press), 'Air.mix'), index=df_index) - pd.Series(cp.PropsSI('H', 'T', np.array(processed["T_0"]), 'P', CONSTANTS["General"]["P_ATM"], 'Air.mix'), index=df_index)
                                # ds = pd.Series(cp.PropsSI('S', 'T', np.array(temp), 'P', np.array(press), 'Air.mix'), index=df_index) - pd.Series(cp.PropsSI('S', 'T', np.array(processed["T_0"]), 'P', CONSTANTS["General"]["P_ATM"], 'Air.mix'), index=df_index)
                                dh = pd.Series(enthalpyCalculator(np.array(temp), CONSTANTS), index=df_index) - pd.Series(enthalpyCalculator(np.array(processed["T_0"]), CONSTANTS), index=df_index)
                                ds = pd.Series(entropyCalculator(np.array(temp), CONSTANTS), index=df_index) - pd.Series(entropyCalculator(np.array(processed["T_0"]), CONSTANTS),index=df_index)
                                dh.loc[~processed[system + ":on"]] = 0
                                ds.loc[~processed[system + ":on"]] = 0
                            elif ("Mix" in flow) or ("EG" in flow):
                                #dh = pd.Series(index=processed.index)
                                #ds = pd.Series(index=processed.index)
                                mixture = ppo.mixtureCompositionNew(
                                    processed[d2df(system,unit,flow,"mdot")],
                                    processed[d2df(system,"Cyl","FuelPh_in","mdot")],
                                    processed[d2df(system, "Cyl", "FuelPh_in", "T")],
                                    CONSTANTS)
                                dh = pd.Series(enthalpyCalculator(np.array(temp), CONSTANTS, mixture), index=df_index) - pd.Series(
                                    enthalpyCalculator(np.array(processed["T_0"]), CONSTANTS, mixture), index=df_index)
                                ds = pd.Series(entropyCalculator(np.array(temp), CONSTANTS, mixture), index=df_index) - pd.Series(
                                    entropyCalculator(np.array(processed["T_0"]), CONSTANTS, mixture), index=df_index)
                                # for idx in dh.index:
                                #     if "Mix" in flow:
                                #         mixture = processed[system+":Mix_Composition"][idx]
                                #     else:
                                #         mixture = processed[system + ":EG_Composition"][idx]
                                #     if processed[system + ":on"][idx]:
                                #         #dh.loc[idx] = cp.PropsSI('H', 'T', temp[idx], 'P', press[idx], mixture) - cp.PropsSI('H', 'T', processed["T_0"][idx], 'P', CONSTANTS["General"]["P_ATM"], mixture)
                                #         #ds.loc[idx] = cp.PropsSI('S', 'T', temp[idx], 'P', press[idx], mixture) - cp.PropsSI('S', 'T', processed["T_0"][idx], 'P', CONSTANTS["General"]["P_ATM"], mixture)
                                #         dh.loc[idx] = cp.PropsSI('H', 'T', temp[idx], 'P', press[idx], mixture) - cp.PropsSI('H', 'T', CONSTANTS["General"]["T_STANDARD"], 'P', CONSTANTS["General"]["P_ATM"], mixture)
                                #         ds.loc[idx] = cp.PropsSI('S', 'T', temp[idx], 'P', press[idx], mixture) - cp.PropsSI('S', 'T', CONSTANTS["General"]["T_STANDARD"], 'P', CONSTANTS["General"]["P_ATM"], mixture)
                                #     else:
                                #         dh.loc[idx] = 0
                                #         ds.loc[idx] = 0
                                #dh = dh * (temp - processed["T_0"]) / (temp - CONSTANTS["General"]["T_STANDARD"])
                                #ds = ds * np.log(temp / processed["T_0"]) / np.log((temp - CONSTANTS["General"]["T_STANDARD"]))
                            elif "Steam" in flow:
                                if "in" in flow:
                                    dh = CONSTANTS["Steam"]["DH_STEAM"] + CONSTANTS["General"]["CP_WATER"] * (processed[d2df(system, unit, flow, "T")] - processed["T_0"])
                                    ds = CONSTANTS["Steam"]["DS_STEAM"] + CONSTANTS["General"]["CP_WATER"] * np.log((processed[d2df(system, unit, flow, "T")] / processed["T_0"]))
                                elif "out" in flow:
                                    dh = CONSTANTS["General"]["CP_WATER"] * (processed[d2df(system, unit, flow, "T")] - processed["T_0"])
                                    ds = CONSTANTS["General"]["CP_WATER"] * np.log((processed[d2df(system, unit, flow, "T")] / processed["T_0"]))
                            processed[d2df(system, unit, flow, "h")] = dh
                            processed[d2df(system, unit, flow, "b")] = dh - processed["T_0"] * ds
                            processed[d2df(system, unit, flow, "Edot")] = processed[d2df(system, unit, flow, "mdot")] * processed[d2df(system, unit, flow, "h")]
                            processed[d2df(system, unit, flow, "Bdot")] = processed[d2df(system, unit, flow, "mdot")] * processed[d2df(system, unit, flow, "b")]
                        else:
                            pass
                            # print("Couldn't calculate the properties for the {} flow, didn't have all what I needed, {}% of the values are NaN".format(system+":"+unit+":"+flow, processed[d2df(system,unit,flow,"T")].isnull().sum()/len(processed[d2df(system,unit,flow,"T")])*100))
                    elif dict_structure["systems"][system]["units"][unit]["flows"][flow]["type"] == "IPF":
                        if processed[d2df(system,unit,flow,"T")].isnull().sum() != len(processed[d2df(system,unit,flow,"T")]):
                            if "Water" in flow:
                                dh = CONSTANTS["General"]["CP_WATER"] * (processed[d2df(system, unit, flow, "T")] - processed["T_0"])
                                ds = CONSTANTS["General"]["CP_WATER"] * np.log((processed[d2df(system, unit, flow, "T")] / processed["T_0"]))
                            if "LubOil" in flow:
                                dh = CONSTANTS["General"]["CP_LO"] * (processed[d2df(system, unit, flow, "T")] - processed["T_0"])
                                ds = CONSTANTS["General"]["CP_LO"] * np.log((processed[d2df(system, unit, flow, "T")] / processed["T_0"]))
                            if "Fuel" in flow:
                                dh = CONSTANTS["General"]["CP_HFO"] * (processed[d2df(system, unit, flow, "T")] - processed["T_0"])
                                ds = CONSTANTS["General"]["CP_HFO"] * np.log((processed[d2df(system, unit, flow, "T")] / processed["T_0"]))
                            processed[d2df(system, unit, flow, "h")] = dh
                            processed[d2df(system, unit, flow, "b")] = dh - processed["T_0"] * ds
                            processed[d2df(system, unit, flow, "Edot")] = processed[d2df(system, unit, flow, "mdot")] * processed[d2df(system, unit, flow, "h")]
                            processed[d2df(system, unit, flow, "Bdot")] = processed[d2df(system, unit, flow, "mdot")] * processed[d2df(system, unit, flow, "b")]
                        else:
                            pass
                            #print("Couldn't calculate the properties for the {} flow, didn't have all what I needed, {}% of the values are NaN".format(system + ":" + unit + ":" + flow, processed[d2df(system,unit,flow,"T")].isnull().sum()/len(processed[d2df(system,unit,flow,"T")])*100))
                    elif dict_structure["systems"][system]["units"][unit]["flows"][flow]["type"] == "SF":
                        if dict_structure["systems"][system]["units"][unit]["flows"][flow]["state"] == "SL":
                            dh = CONSTANTS["Steam"]["H_STEAM_LS"] - CONSTANTS["General"]["CP_WATER"] * (processed["T_0"] - 273.15)
                            ds = CONSTANTS["Steam"]["S_STEAM_LS"] - CONSTANTS["General"]["CP_WATER"] * np.log(processed["T_0"] / 273.15)
                        elif dict_structure["systems"][system]["units"][unit]["flows"][flow]["state"] == "SV":
                            dh = CONSTANTS["Steam"]["H_STEAM_VS"] - CONSTANTS["General"]["CP_WATER"] * (processed["T_0"] - 273.15)
                            ds = CONSTANTS["Steam"]["S_STEAM_VS"] - CONSTANTS["General"]["CP_WATER"] * np.log(processed["T_0"] / 273.15)
                        else:
                            print("Steam can be either saturated liquid or saturated vapor, nothing in between")
                        processed[d2df(system, unit, flow, "h")] = dh
                        processed[d2df(system, unit, flow, "b")] = dh - processed["T_0"] * ds
                        processed[d2df(system, unit, flow, "Edot")] = processed[d2df(system, unit, flow, "mdot")] * processed[d2df(system, unit, flow, "h")]
                        processed[d2df(system, unit, flow, "Bdot")] = processed[d2df(system, unit, flow, "mdot")] * processed[d2df(system, unit, flow, "b")]
                    elif dict_structure["systems"][system]["units"][unit]["flows"][flow]["type"] == "Qdot":
                        processed[d2df(system, unit, flow, "Bdot")] = processed[d2df(system,unit,flow,"Edot")] / processed[d2df(system,unit,flow,"T")]
                    elif dict_structure["systems"][system]["units"][unit]["flows"][flow]["type"] in {"Wdot", "CEF"}:
                        processed[d2df(system, unit, flow, "Bdot")] = processed[d2df(system, unit, flow, "Edot")]
    print("...done!")
    return processed



def efficiencyCalculator(processed, dict_structure, CONSTANTS):
    text_file = open(CONSTANTS["filenames"]["consistency_check_report"], "a")
    text_file.write("\n *** CALCULATING EFFICIENCIES *** \n")
    df_index = processed.index
    for system in dict_structure["systems"]:
        for unit in dict_structure["systems"][system]["units"]:
            # Here I create eight (8) series: 4 Edot and 4 Bdot. 2 "Full" and 2 "useful".
            temp_flow_list = {"Edot_in", "Edot_in_useful", "Edot_out", "Edot_out_useful", "Bdot_in", "Bdot_in_useful", "Bdot_out", "Bdot_out_useful"}
            temp_df = pd.DataFrame(0, columns=temp_flow_list, index=df_index)
            for flow in dict_structure["systems"][system]["units"][unit]["flows"]:
                if flow[-2:] == "in":
                    temp_df['Edot_in'] = temp_df['Edot_in'] + processed[d2df(system, unit, flow, "Edot")]
                    temp_df['Bdot_in'] = temp_df['Bdot_in'] + processed[d2df(system, unit, flow, "Bdot")]
                elif flow[-3:] == "out":
                    temp_df['Edot_out'] = temp_df['Edot_out'] + processed[d2df(system, unit, flow, "Edot")]
                    temp_df['Bdot_out'] = temp_df['Bdot_out'] + processed[d2df(system, unit, flow, "Bdot")]
                else:
                    text_file.write("Flow {}:{}:{} is not recognised as either input or output \n".format(system, unit, flow))
                # The "Edot_useful" and "Bdot_useful" inputs and outputs are only assigned when defined
                if "IO" in dict_structure["systems"][system]["units"][unit]["flows"][flow]:
                    if dict_structure["systems"][system]["units"][unit]["flows"][flow]["IO"] == "input":
                        if flow[-2:] == "in":
                            temp_df['Edot_in_useful'] = temp_df['Edot_in_useful'] + processed[d2df(system, unit, flow, "Edot")]
                            temp_df['Bdot_in_useful'] = temp_df['Bdot_in_useful'] + processed[d2df(system, unit, flow, "Bdot")]
                        elif flow[-3:] == "out":
                            temp_df['Edot_in_useful'] = temp_df['Edot_in_useful'] - processed[d2df(system, unit, flow, "Edot")]
                            temp_df['Bdot_in_useful'] = temp_df['Bdot_in_useful'] - processed[d2df(system, unit, flow, "Bdot")]
                        else:
                            text_file.write("Flow {}:{}:{} is not recognised as either input or output \n".format(system, unit,flow))
                    elif dict_structure["systems"][system]["units"][unit]["flows"][flow]["IO"] == "output":
                        if flow[-2:] == "in":
                            temp_df['Edot_out_useful'] = temp_df['Edot_out_useful'] - processed[d2df(system, unit, flow, "Edot")]
                            temp_df['Bdot_out_useful'] = temp_df['Bdot_out_useful'] - processed[d2df(system, unit, flow, "Bdot")]
                        elif flow[-3:] == "out":
                            temp_df['Edot_out_useful'] = temp_df['Edot_out_useful'] + processed[d2df(system, unit, flow, "Edot")]
                            temp_df['Bdot_out_useful'] = temp_df['Bdot_out_useful'] + processed[d2df(system, unit, flow, "Bdot")]
                        else:
                            text_file.write("Flow {}:{}:{} is not recognised as either input or output \n".format(system, unit,flow))
                    else:
                        text_file.write("Flow {}:{}:{} is not recognised as either USEFEUL input or output \n".format(system, unit, flow))
            # We first calculate the energy efficiency (if possible)
            if system+":"+unit+":"+"eta" in processed.columns:
                processed[system+":"+unit+":"+"eta"] = temp_df['Edot_out_useful'] / temp_df['Edot_in_useful']
            # Then exergy efficiency (again, if possible)
            if system + ":" + unit + ":" + "eps" in processed.columns:
                processed[system + ":" + unit + ":" + "eps"] = temp_df['Bdot_out_useful'] / temp_df['Bdot_in_useful']
            # Finally, we calculate the lambda
            processed[system + ":" + unit + ":" + "lambda"] = (temp_df['Bdot_in'] - temp_df['Bdot_out']) / temp_df['Bdot_in']

            #### ADD THE CALCULATION OF THE DELTA #####
    text_file.close()
    return processed





def enthalpyCalculator(T, CONSTANTS, mass_composition = {"N2": 0.768, "O2": 0.232, "CO2": 0.0, "H2O": 0.0}):
    specific_enthalpy_molar = {}
    for idx in mass_composition:
        specific_enthalpy_molar[idx] = (CONSTANTS["General"]["NASA_POLY"][idx][0] * T +
                CONSTANTS["General"]["NASA_POLY"][idx][1]/2 * T**2 +
                CONSTANTS["General"]["NASA_POLY"][idx][2]/3 * T**3 +
                CONSTANTS["General"]["NASA_POLY"][idx][3]/4 * T**4 +
                CONSTANTS["General"]["NASA_POLY"][idx][4]/5 * T**5 +
                CONSTANTS["General"]["NASA_POLY"][idx][5]) * CONSTANTS["General"]["R_0"] # This result is in J/molK
    specific_enthalpy = (specific_enthalpy_molar["N2"] / CONSTANTS["General"]["MOLAR_MASSES"]["N2"] * mass_composition["N2"] +
                         specific_enthalpy_molar["O2"] / CONSTANTS["General"]["MOLAR_MASSES"]["O2"] * mass_composition["O2"] +
                         specific_enthalpy_molar["CO2"] / CONSTANTS["General"]["MOLAR_MASSES"]["CO2"] * mass_composition["CO2"] +
                         specific_enthalpy_molar["H2O"] / CONSTANTS["General"]["MOLAR_MASSES"]["H2O"] * mass_composition["H2O"])
    return specific_enthalpy


def entropyCalculator(T, CONSTANTS, mass_composition = {"N2": 0.768, "O2": 0.232, "CO2": 0.0, "H2O": 0.0}):
    specific_entropy_molar = {}
    for idx in mass_composition:
        specific_entropy_molar[idx] = (CONSTANTS["General"]["NASA_POLY"][idx][0] * np.log(T) +
                CONSTANTS["General"]["NASA_POLY"][idx][1] * T +
                CONSTANTS["General"]["NASA_POLY"][idx][2]/2 * T**2 +
                CONSTANTS["General"]["NASA_POLY"][idx][3]/3 * T**3 +
                CONSTANTS["General"]["NASA_POLY"][idx][4]/4 * T**4 +
                CONSTANTS["General"]["NASA_POLY"][idx][6]) * CONSTANTS["General"]["R_0"] # This result is in J/molK
    specific_entropy = (specific_entropy_molar["N2"] / CONSTANTS["General"]["MOLAR_MASSES"]["N2"] * mass_composition["N2"] +
                         specific_entropy_molar["O2"] / CONSTANTS["General"]["MOLAR_MASSES"]["O2"] * mass_composition["O2"] +
                         specific_entropy_molar["CO2"] / CONSTANTS["General"]["MOLAR_MASSES"]["CO2"] * mass_composition["CO2"] +
                         specific_entropy_molar["H2O"] / CONSTANTS["General"]["MOLAR_MASSES"]["H2O"] * mass_composition["H2O"])
    return specific_entropy