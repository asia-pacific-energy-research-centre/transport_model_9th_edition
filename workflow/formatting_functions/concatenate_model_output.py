#this will apply any fuel mixing on the demand side. This is can include, the use of different fule types for each drive type, for example, electricity vs oil in phev's, or even treating rail as a drive type, and splitting demand into electricity, coal and dieel rpoprtions. 

#as such, this will merge a fuel mixing dataframe onto the model output, by the Drive column, and apply the shares by doing that, resulting in a fuel column.
#this means that the supply side fuel mixing needs to occur after this script, because it will be merging on the fuel column.

#%%
#set working directory as one folder back so that config works
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
from runpy import run_path
###IMPORT GLOBAL VARIABLES FROM config.py
import sys
sys.path.append("./config/utilities")
from config import *
####usae this to load libraries and set variables. Feel free to edit that file as you need
#%%
def concatenate_model_output():
    #load model output
    road_model_output = pd.read_csv('intermediate_data/road_model/{}'.format(model_output_file_name))
    non_road_model_output = pd.read_csv('intermediate_data/non_road_model/{}'.format(model_output_file_name))
    
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
    model_output_all.to_csv('intermediate_data/model_output_concatenated/{}'.format(model_output_file_name), index=False)

#%%
# concatenate_model_output()
#%%