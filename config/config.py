"""This file is intended to be able ot be used in the beginnning of any jupyter ntoebook to set the config variables for the model. This helps to reduce clutter, as that is a big issue for notebooks. So if you ever need to chnage conifgurations, just change this. """
#%%

#import common libraries 
import pandas as pd 
import numpy as np
import glob
import os
from string import digits#is this used?
import datetime
import re
import shutil
# %config Completer.use_jedi = False#Jupiter lab specific setting to fix Auto fill bug
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
#%%
#we can set file_date_id here so that if we are running the script alone, versus through integrate, we can have the variable available
try:
    if file_date_id:
       pass
except NameError:
    file_date_id = ''
   
#%%
USE_LATEST_OUTPUT_DATE_ID = True#True
#create option to set file_date_id to the date_id of the latest created output files. this can be helpful when producing graphs and analysing output data
if USE_LATEST_OUTPUT_DATE_ID:
    list_of_files = glob.glob('./output_data/model_output/*.csv') 
    latest_file = max(list_of_files, key=os.path.getctime)
    #get file data id using regex. want to grab the firt 8 digits and then an underscore and then the next 4 digits
    file_date_id = re.search(r'_DATE(\d{8})_(\d{4})', latest_file).group(0)

#%%
#state important modelling variables
BASE_YEAR= 2017
END_YEAR = 2050
Scenario_list = ['Carbon Neutral', 'Reference']

model_output_file_name = 'model_output_years_{}_to_{}{}.csv'.format(BASE_YEAR, END_YEAR, file_date_id)

EIGHTH_EDITION_DATA = True

scenario_id = 'model_development'
#%%
#state model concordances file names
model_concordances_version = file_date_id#'20220824_1256'
model_concordances_file_name  = 'model_concordances{}.csv'.format(model_concordances_version)
model_concordances_file_name_fuels = 'model_concordances_fuels{}.csv'.format(model_concordances_version)
model_concordances_file_name_fuels_NO_BIOFUELS = 'model_concordances_fuels_NO_BIOFUELS{}.csv'.format(model_concordances_version)

#%%
#ANALYSIS VARIABLES
SCENARIO_OF_INTEREST = 'Reference'
###################################################
# #%%
# #import and create common variables


# config_folder_path = 'config'#folder where all the config files are stored. these may be input data or just general config files like names of eocnomies used, or correspondances
# #have set above to config_new for now just so that its clear what is new

# output_data_path = 'output_data'#this is data that is output from the model and or other processes, at least for use outside of this project
# other_outputs_path = 'other_outputs'

# intermediate_data_path = 'intermediate_data'#this is data that is saved during the process when you reach major checkpoints, before being loaded later in assistance of creating output data. Contains subfolders to reduce the clutter

# input_data_path = 'input_data'#this data shouldnt be interacted with manually. rather it is just data you take from another source, maybe reformat, and then put here. eg. EGEDA Data

###################################################
#%%

## Choose which economies to import and calculate data for:
#first take in economy names file, then we will remove the economies we dont want (or if there are too many, just  choose the one you do want)
economy_codes_path = 'config/utilities/economy_code_to_name.csv'

Economy_list = pd.read_csv(economy_codes_path).iloc[:,0]#get the first column
#remove economies we dont want
Economy_list = Economy_list[Economy_list != 'GBR']

###################################################
#%%
import plotly.express as px
#graphing tools:
PLOTLY_COLORS_LIST = px.colors.qualitative.Plotly

AUTO_OPEN_PLOTLY_GRAPHS = False
# %%
