

###########################################################################
#
###########		ENERGY AND EXERGY ANALYSIS OF A CRUISE SHIP		###########
#
###########################################################################

# This is the main script of the project "Energy and Exergy analysis of a cruise ship"

# The main objective of this project is to analyze the energy and exergy flows of the cruise ship "MS Birka", selected as case study. 

# The main objective of this library of Python scripts is, therefore;
# - Load the data
# - Appropriately filter and clean the dataset
# - Process data so to generate the variables of interest: in particular, energy and exergy flows
# - Statistically analyze the data so to produce appropriate results



# The Main.py script calls other scripts and functions. It is divided in the following sections:
# - INPUT
# - DATA READING
# - DATA CLEANING
# - DATA PROCESSING
# - EXPLORATORY DATA ANALYSIS
# - ENERGY ANALYSIS
# - EXERGY ANALYSIS





######################################
## INPUT			##
######################################

# Loading appropriate modules
import pandas
import input 

filenames = input.filenames() # Note: this is just a test






######################################
## DATA READING			##
######################################

# Responsible: FA

import constants
CONSTANTS_GENERAL = constants.general() # loading dictionary with general, physical constants
CONSTANTS_STEAM = constants.steamProperties() # loading dictionary with steam properties constants
CONSTANTS_MAIN_ENGINES = constants.mainEngines(CONSTANTS_GENERAL) # loading dictionary with main-engine related constants
CONSTANTS_AUX_ENGINES = constants.auxiliaryEngines(CONSTANTS_GENERAL,CONSTANTS_MAIN_ENGINES) # loading dictionary with auxiliary-engine related constants
N_POINTS = 319*4*24
temp = constants.monthLimits(N_POINTS)
MONTH_LIMIT_IDX = temp[0]
DAY_LIMIT_IDX = temp[1]



######################################
## DATA CLEANING			##
######################################

# Responsible: FA





######################################
## DATA PROCESSING		##
######################################

# Responsible: FB




######################################
## EXPLORATORY DATA ANALYSIS	##
######################################

# Responsible: FB



######################################
## ENERGY ANALYSIS		##
######################################

# Responsible: FB



######################################
## EXERGY ANALYSIS		##
######################################

# Responsible: FB