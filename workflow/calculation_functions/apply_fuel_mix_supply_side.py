#this will apply any fuel mixing on the supply side. This is currently only biofuel mixing but could include other fuel types in the future

#this will merge a fuel sharing dataframe onto the model output, by the fuel column, and apply the shares by doing that. There will be a new fuel column after this
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
def apply_fuel_mix_supply_side():
    supply_side_fuel_mixing = pd.read_csv('intermediate_data/aggregated_model_inputs/{}_supply_side_fuel_mixing.csv'.format(FILE_DATE_ID))

    model_output = pd.read_csv('intermediate_data/model_output_with_fuels/1_demand_side/{}'.format(model_output_file_name))
    
    #merge the supply side fuel mixing data on the fuel column. This will result in a new supply side fuel column which reflects the splitting of the fuel into many types. We will replace the value in the fuel column with the value in the supply side fuel column, and times the energy value by the share. and Where the suply side fuel column contains no value (an NA) then the fuel and its energy use will be unchanged.
    df_with_new_fuels = model_output.merge(supply_side_fuel_mixing, on=['Scenario', 'Economy', 'Transport Type', 'Medium', 'Vehicle Type', 'Drive', 'Fuel', 'Date'], how='left')
    
    #remove rows where New Fuel is nan
    df_with_new_fuels = df_with_new_fuels[df_with_new_fuels['New_fuel'].notna()]
    breakpoint()
    df_with_new_fuels['Energy'] = df_with_new_fuels['Energy'] * df_with_new_fuels['Supply_side_fuel_share']

    #now we will have the amount of each new fuel type being used. To find the remainign use of the original fuel we will minus the eegy of the new fuels from the original fuel. However, since some original fuels will ahve been mixed with more than one new fuel, we will need to pivot the new fuels out so that we can minus them from the original fuel, all within the same row. Then later jsut concat the rows back together.
    df_with_new_fuels_wide = df_with_new_fuels.pivot_table(index=['Scenario', 'Economy', 'Transport Type', 'Medium', 'Vehicle Type', 'Drive', 'Fuel', 'Date'], columns='New_fuel', values='Energy').reset_index()
    #get the new columns names, they will jsut be the unique values in the new fuel column
    new_fuels_cols = df_with_new_fuels.New_fuel.unique().tolist()
    #set any nas to 0 in new_fuels_cols
    df_with_new_fuels_wide[new_fuels_cols] = df_with_new_fuels_wide[new_fuels_cols].fillna(0)
    # breakpoint()
    #drop cols except new_fuels_cols and the index cols
    df_with_new_fuels_wide = df_with_new_fuels_wide[['Scenario', 'Economy', 'Transport Type', 'Medium', 'Vehicle Type', 'Drive', 'Fuel', 'Date'] + new_fuels_cols]
    
    #join the new fuel columns back to the original dataframe
    df_with_old_fuels = model_output.merge(df_with_new_fuels_wide, on=['Scenario', 'Economy', 'Transport Type', 'Medium', 'Vehicle Type', 'Drive', 'Fuel', 'Date'], how='left')
    
    #minus the New fuels from the energy to get the original fuels energy use. can use new_fuels_cols as the columns to minus
    df_with_old_fuels['Energy'] = df_with_old_fuels['Energy'] - df_with_old_fuels[new_fuels_cols].sum(axis=1)
    
    #drop those cols
    df_with_old_fuels = df_with_old_fuels.drop(new_fuels_cols, axis=1)
    
    #concat the two dataframes back together
    #first edit df_with_new_fuels a bit
    df_with_new_fuels['Fuel'] = df_with_new_fuels['New_fuel']
    df_with_new_fuels.drop(['New_fuel', 'Supply_side_fuel_share'], axis=1, inplace=True)
    df_with_all_fuels  = pd.concat([df_with_old_fuels, df_with_new_fuels], axis=0)
    breakpoint()
    #set frequency to 'Yearly'#jsut to be safe.
    df_with_all_fuels['Frequency'] = 'Yearly'
    #save data
    df_with_all_fuels.to_csv('intermediate_data/model_output_with_fuels/2_supply_side/{}'.format(model_output_file_name), index=False)

    
#%%
# apply_fuel_mix_supply_side()
#%%
# # a = pd.read_csv('intermediate_data/model_output_with_fuels/2_supply_side/{}'.format(model_output_file_name))
# # #check for dupklicates:
# # dupes = a[a.duplicated()].copy()
# # # dupes2 = a[a.duplicated(subset=['Date', 'Economy', 'Scenario', 'Transport Type', 'Vehicle Type','Drive', 'Medium', 'Fuel'], keep=False)].copy()
#  a = pd.read_csv('intermediate_data/model_output_with_fuels/1_demand_side/{}'.format(model_output_file_name))
#  dupes2 = a[a.duplicated(subset=['Date', 'Economy', 'Scenario', 'Transport Type', 'Vehicle Type','Drive', 'Medium', 'Fuel'], keep=False)].copy()
#  dupes = a[a.duplicated()].copy()
# # d = df_with_new_fuels[df_with_new_fuels .duplicated(subset=['Date', 'Economy', 'Scenario', 'Transport Type', 'Vehicle Type','Drive', 'Medium', 'Fuel', 'New_fuel'], keep=False)].copy()