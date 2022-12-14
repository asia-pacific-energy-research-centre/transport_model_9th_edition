"""This file is intended to be able ot be used in the beginnning of any jupyter ntoebook to set the config variables for the model. This helps to reduce clutter, as that is a big issue for notebooks. So if you ever need to chnage conifgurations, just change this. """
#%%

#import common libraries 
import pandas as pd 
import numpy as np
import glob
import os
from string import digits
import datetime
import re
# %config Completer.use_jedi = False#Jupiter lab specific setting to fix Auto fill bug


#we can set file_date_id here so that if we are running the script alone, versus through integrate, we can have the variable available
try:
    if file_date_id:
       pass
except NameError:
    file_date_id = ''
    
#%%
BASE_YEAR= 2017
END_YEAR = 2050
Scenario_list = ['Carbon Neutral', 'Reference']

model_output_file_name = 'model_output_years_{}_to_{}{}.csv'.format(BASE_YEAR, END_YEAR, file_date_id)

EIGHTH_EDITION_DATA = True
#%%
#state model concordances
model_concordances_version = file_date_id#'20220824_1256'
model_concordances_file_name  = 'model_concordances{}.csv'.format(model_concordances_version)
model_concordances_file_name_fuels = 'model_concordances_fuels{}.csv'.format(model_concordances_version)
model_concordances_file_name_fuels_NO_BIOFUELS = 'model_concordances_fuels_NO_BIOFUELS{}.csv'.format(model_concordances_version)

#%%
#ANALYSIS VARIABLES
SCENARIO_OF_INTEREST = 'Reference'
###################################################
#%%
#import and create common variables


config_folder_path = 'config'#folder where all the config files are stored. these may be input data or just general config files like names of eocnomies used, or correspondances
#have set above to config_new for now just so that its clear what is new

output_data_path = 'output_data'#this is data that is output from the model and or other processes, at least for use outside of this project
other_outputs_path = 'other_outputs'

intermediate_data_path = 'intermediate_data'#this is data that is saved during the process when you reach major checkpoints, before being loaded later in assistance of creating output data. Contains subfolders to reduce the clutter

input_data_path = 'input_data'#this data shouldnt be interacted with manually. rather it is just data you take from another source, maybe reformat, and then put here. eg. EGEDA Data

###################################################
#%%

## Choose which economies to import and calculate data for:
#first take in economy names file, then we will remove the economies we dont want (or if there are too many, just  choose the one you do want)
economy_codes_path = '{}/utilities/economy_code_to_name.csv'.format(config_folder_path)#have set above to config_new for now just so that its clear what is new

Economy_list = pd.read_csv(economy_codes_path).iloc[:,0]#get the first column
#remove economies we dont want
Economy_list = Economy_list[Economy_list != 'GBR']

###################################################
#%%
#SET VARIABLES

# Senareo = "Reference"  #can fix spelling of all things later. 
Senareo = "Net-zero"  
BASE_YEAR = 2017
MAX_YEAR = 2070

#until i aa confident about the the use of this value, it will have this name. Once i am conifdent that the use of this is correct, then i can just change the use of this value in the file non_specifed_transport.py to Base_year + 2
NON_SPEC_TRANSPORT_BASE_YEAR = BASE_YEAR + 2
NON_SPEC_TRANSPORT_MAX_YEAR = 2051#i have serious concerns about use of 2051 here and not 2070

###################################################
#%%
import plotly.express as px
#graphing tools:
PLOTLY_COLORS_LIST = px.colors.qualitative.Plotly
# %%
