#this will apply any fuel mixing on the demand side. This is can include, the use of different fule types for each drive type, for example, electricity vs oil in phev's, or even treating rail as a drive type, and splitting demand into electricity, coal and dieel rpoprtions. 

#as such, this will merge a fuel mixing dataframe onto the model output, by the Drive column, and apply the shares by doing that, resulting in a fuel column.
#this means that the supply side fuel mixing needs to occur after this script, because it will be merging on the fuel column.

#%%
#set working directory as one folder back so that config works
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
execfile("config/config.py")#usae this to load libraries and set variables. Feel free to edit that file as you need

#%%
#load model output
model_output = pd.read_csv('intermediate_data/model_output_concatenated/{}'.format(model_output_file_name))

#load user input for fuel mixing
demand_side_fuel_mixing = pd.read_csv('intermediate_data\model_inputs\demand_side_fuel_mixing_COMPGEN.csv')

#%%
df_with_fuels = model_output.merge(demand_side_fuel_mixing, on=['Scenario', 'Economy', 'Transport Type', 'Medium', 'Vehicle Type',
       'Drive', 'Year'], how='left')

#%%
df_with_fuels['Energy'] = df_with_fuels['Energy'] * df_with_fuels['Demand_side_fuel_share']

#%%
#save data
df_with_fuels.to_csv('intermediate_data/model_output_with_fuels/1_demand_side/{}'.format(model_output_file_name), index=False)

#%%
