#this will apply any fuel mixing on the supply side. This is currently only biofuel mixing but could include other fuel types in the future

#this will merge a fuel sharing dataframe onto the model output, by the fuel column, and apply the shares by doing that. There will be a new fuel column after this

#%%
#set working directory as one folder back so that config works
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
execfile("config/config.py")#usae this to load libraries and set variables. Feel free to edit that file as you need
#%%

#load user input for fuel mixing
supply_side_fuel_mixing = pd.read_csv('intermediate_data\model_inputs\supply_side_fuel_mixing_COMPGEN.csv')

model_output_file_name = 'model_output_years_{}_to_{}{}.csv'.format(BASE_YEAR, END_YEAR, file_date_id)

model_output = pd.read_csv('intermediate_data/model_output_with_fuels/1_demand_side/{}'.format(model_output_file_name))

#%%
df_with_fuels = model_output.merge(supply_side_fuel_mixing, on=['Scenario', 'Economy', 'Transport Type', 'Medium', 'Vehicle Type', 'Drive', 'Fuel', 'Year'], how='left')

#%%
df_with_fuels['Energy'] = df_with_fuels['Energy'] * df_with_fuels['Supply_side_fuel_share']

#%%
#save data
df_with_fuels.to_csv('intermediate_data/model_output_with_fuels/2_supply_side/{}'.format(model_output_file_name), index=False)

#%%
