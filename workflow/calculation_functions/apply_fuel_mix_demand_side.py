#TODO implement data coverage plotting for this and supply side fuel mixing

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
def apply_fuel_mix_demand_side(ECONOMY_ID):
    
    #load model output
    model_output = pd.read_csv('intermediate_data/model_output_concatenated/{}_{}'.format(ECONOMY_ID, config.model_output_file_name))

    #load user input for fuel mixing 
    demand_side_fuel_mixing = pd.read_csv('intermediate_data/model_inputs/{}/{}_demand_side_fuel_mixing.csv'.format(config.FILE_DATE_ID, ECONOMY_ID))
    #load model concordances with fuels
    model_concordances_fuels = pd.read_csv('config/concordances_and_config_data/computer_generated_concordances/{}'.format(config.model_concordances_file_name_fuels))
    
    supply_side_fuel_mixing_fuels =  pd.read_csv('intermediate_data/model_inputs/{}/{}_supply_side_fuel_mixing.csv'.format(config.FILE_DATE_ID, ECONOMY_ID))['New_fuel'].unique().tolist()
    #drop supply_side_fuel_mixing_fuels from model_concordances_fuels
    model_concordances_fuels = model_concordances_fuels[~model_concordances_fuels['Fuel'].isin(supply_side_fuel_mixing_fuels)]
    
    
    model_output = model_output.merge(model_concordances_fuels[['Fuel','Drive']].drop_duplicates(), on='Drive', how='left')

    model_output_to_mix = model_output[model_output['Drive'].isin(demand_side_fuel_mixing['Drive'].unique().tolist())]
    # #and now drop those demand side fuel mixing rows from the model output
    model_output = model_output[~model_output['Drive'].isin(demand_side_fuel_mixing['Drive'].unique().tolist())]
    #join the fuel mixing data to the model output. This will result in a new fuel column. Note that there can be multiple fuels per drive, so this could also create new rows for each drive. 
    df_with_fuels = model_output_to_mix.merge(demand_side_fuel_mixing, on=['Scenario', 'Economy', 'Transport Type', 'Medium', 'Vehicle Type','Drive', 'Date','Fuel'], how='left')
    
    #identify any nas in Demand_side_fuel_share column. If so make the user add them to other_code\create_user_inputs\create_demand_side_fuel_mix_input.py.
    #this is because the user needs to specify what the fuel share is for each medium/vehicletype/drive type, and if it is not specified it will cause an error.
    if df_with_fuels['Demand_side_fuel_share'].isna().sum() > 0:
        breakpoint()
        print('There are {} rows with a missing fuel share. Please add them to other_code\create_user_inputs\create_demand_side_fuel_mix_input.py'.format(df_with_fuels['Demand_side_fuel_share'].isna().sum()))
        raise Exception('Missing fuel shares')
    
    #times teh fuel sahres by energy. This will result in a new energy value, reflecting the share of fuel used in each drive type.
    df_with_fuels['Energy'] = df_with_fuels['Energy'] * df_with_fuels['Demand_side_fuel_share']

    
    #remove the demand side fuel share column, as it is no longer needed
    df_with_fuels = df_with_fuels.drop(columns=['Demand_side_fuel_share'])
    
    new_df_with_fuels = pd.concat([df_with_fuels, model_output], axis=0)
    #save data
    new_df_with_fuels.to_csv('intermediate_data/model_output_with_fuels/1_demand_side/{}_{}'.format(ECONOMY_ID, config.model_output_file_name), index=False)

    
#%%
# apply_fuel_mix_demand_side('19_THA')
#%%
