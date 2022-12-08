"""This file is intended to be able ot be used in the beginnning of any jupyter ntoebook to set the config variables for the model. This helps to reduce clutter, as that is a big issue for notebooks. So if you ever need to chnage conifgurations, just change this. """
#to make the code in this library clear we will name every variable that is stated in here with all caps
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
#we can set FILE_DATE_ID to something other than the date here which is useful if we are running the script alone, versus through integrate.py
try:
    if FILE_DATE_ID:
       pass
except NameError:
    FILE_DATE_ID = ''
   
#%%
USE_LATEST_OUTPUT_DATE_ID = True#True
#create option to set FILE_DATE_ID to the date_id of the latest created output files. this can be helpful when producing graphs and analysing output data
if USE_LATEST_OUTPUT_DATE_ID:
    list_of_files = glob.glob('./output_data/model_output/*.csv') 
    latest_file = max(list_of_files, key=os.path.getctime)
    #get file data id using regex. want to grab the firt 8 digits and then an underscore and then the next 4 digits
    FILE_DATE_ID = re.search(r'_DATE(\d{8})_(\d{4})', latest_file).group(0)

#%%
#state important modelling variables
BASE_YEAR= 2017
END_YEAR = 2050

model_output_file_name = 'model_output_years_{}_to_{}{}.csv'.format(BASE_YEAR, END_YEAR, FILE_DATE_ID)

EIGHTH_EDITION_DATA = True

#get sceanrios from scenarios_list file
SCENARIOS_LIST = pd.read_csv('config/concordances_and_config_data/scenarios_list.csv')
#grab the scenario names where 'Use' column is true and put them into a list
SCENARIOS_LIST = SCENARIOS_LIST[SCENARIOS_LIST['Use'] == True]['Scenario'].tolist()

#For graphing and analysis we sometimes will single out a scenario to look at. This is the scenario we will use for that:
SCENARIO_OF_INTEREST = 'Reference'

###################################################
#%%

## Choose which economies to import and calculate data for:
#first take in economy names file, then we will remove the economies we dont want (or if there are too many, just  choose the one you do want)
economy_codes_path = 'config/concordances_and_config_data/economy_code_to_name.csv'

ECONOMY_LIST = pd.read_csv(economy_codes_path).iloc[:,0]#get the first column
#remove economies we dont want
ECONOMY_LIST = ECONOMY_LIST[ECONOMY_LIST != 'GBR']

#ECONOMY REGIONS
#load the economy regions file so that we can easily merge it with a dataframe to create a region column
economy_regions_path = 'config/concordances_and_config_data/region_economy_mapping.csv'
ECONOMY_REGIONS = pd.read_csv(economy_regions_path)

###################################################
#%%
import plotly.express as px
#graphing tools:
PLOTLY_COLORS_LIST = px.colors.qualitative.Plotly

AUTO_OPEN_PLOTLY_GRAPHS = False

# %%

