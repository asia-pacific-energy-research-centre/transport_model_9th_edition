#this will apply any fuel mixing on the demand side. This is can include, the use of different fule types for each drive type, for example, electricity vs oil in phev's, or even treating rail as a drive type, and splitting demand into electricity, coal and dieel rpoprtions. 

#as such, this will merge a fuel mixing dataframe onto the model output, by the Drive column, and apply the shares by doing that, resulting in a fuel column.
#this means that the supply side fuel mixing needs to occur after this script, because it will be merging on the fuel column.

#%%
###IMPORT GLOBAL VARIABLES FROM config.py
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
import sys
sys.path.append("./config")
import config

import pandas as pd 
import numpy as np
import yaml
import datetime
import shutil
import sys
import os 
import re
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go
import matplotlib
import matplotlib.pyplot as plt
from plotly.subplots import make_subplots
####Use this to load libraries and set variables. Feel free to edit that file as you need.
#%%
def concatenate_model_output(ECONOMY_ID):
    #load model output
    road_model_output = pd.read_csv('intermediate_data/road_model/{}_{}'.format(ECONOMY_ID, config.model_output_file_name))
    non_road_model_output = pd.read_csv('intermediate_data/non_road_model/{}_{}'.format(ECONOMY_ID, config.model_output_file_name))
    
    # check if there are any NA's in any columns in the output dataframes. If there are, print them out
    if road_model_output.isnull().values.any():
        print(road_model_output[road_model_output.isnull().any(axis=1)].loc[:, road_model_output.isnull().any(axis=0)])
        print('there are NA values in the road model output. However if they are only in the user input columns for 2017 then ignore them')
    if non_road_model_output.isnull().values.any():
        print(non_road_model_output[non_road_model_output.isnull().any(axis=1)].loc[:, non_road_model_output.isnull().any(axis=0)])
        print('there are NA values in the non road model output. However if they are only in the user input columns for 2017 then ignore them')

    #also check for duplicates
    if road_model_output.duplicated().any():
        print('there are duplicates in the road model output')
    if non_road_model_output.duplicated().any():
        print('there are duplicates in the non road model output')
    
    #set medium for road
    road_model_output['Medium'] ='road'
    #concatenate road and non road models output
    model_output_all = pd.concat([road_model_output, non_road_model_output])
    
    #save
    model_output_all.to_csv('intermediate_data/model_output_concatenated/{}_{}'.format(ECONOMY_ID, config.model_output_file_name), index=False)

    return model_output_all

def fill_missing_output_cols_with_nans(ECONOMY_ID, road_model_input_wide, non_road_model_input_wide):
    for col in config.ROAD_MODEL_OUTPUT_COLS:
        if col not in road_model_input_wide.columns:
            road_model_input_wide[col] = np.nan
    for col in config.NON_ROAD_MODEL_OUTPUT_COLS:
        if col not in non_road_model_input_wide.columns:
            non_road_model_input_wide[col] = np.nan
            
    #save to file
    road_model_input_wide.to_csv('intermediate_data/road_model/{}_{}'.format(ECONOMY_ID, config.model_output_file_name), index=False)
    non_road_model_input_wide.to_csv('intermediate_data/non_road_model/{}_{}'.format(ECONOMY_ID, config.model_output_file_name), index=False)
    

#%%
# concatenate_model_output()
#%%