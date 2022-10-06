#this will apply any fuel mixing on the demand side. This is can include, the use of different fule types for each drive type, for example, electricity vs oil in phev's, or even treating rail as a drive type, and splitting demand into electricity, coal and dieel rpoprtions. 

#as such, this will merge a fuel mixing dataframe onto the model output, by the Drive column, and apply the shares by doing that, resulting in a fuel column.
#this means that the supply side fuel mixing needs to occur after this script, because it will be merging on the fuel column.

#%%
#set working directory as one folder back so that config works
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
from runpy import run_path
exec(open("config/config.py").read())#usae this to load libraries and set variables. Feel free to edit that file as you need

#%%
# model_output_file_name = 'model_output_years_2017_to_2050_DATE20220824_1043.csv'
#load model output
model_output = pd.read_csv('intermediate_data/model_output_concatenated/{}'.format(model_output_file_name))

#load user input for fuel mixing 
demand_side_fuel_mixing = pd.read_csv('intermediate_data\model_inputs\demand_side_fuel_mixing_COMPGEN.csv')

#load model concordances with fuels
model_concordances_fuels = pd.read_csv('config/concordances/{}'.format(model_concordances_file_name_fuels))

#%%
#join the fuel mixing data to the model output. This will result in a new fuel column. Note that there can be multiple fuels per drive, so this could also create new rows for each drive. 
df_with_fuels = model_output.merge(demand_side_fuel_mixing, on=['Scenario', 'Economy', 'Transport Type', 'Medium', 'Vehicle Type',
       'Drive', 'Year'], how='left')

#%%

#where we are missing fuels, fill them in with what is in the mdoel concordances, based on the drive type
model_concordances_fuels = model_concordances_fuels[['Drive', 'Fuel']].drop_duplicates().rename(columns={'Fuel': 'Fuel_Concordance'})
df_with_fuels = df_with_fuels.merge(model_concordances_fuels, on='Drive', how='left')
df_with_fuels['Fuel'].fillna(df_with_fuels.Fuel_Concordance, inplace=True)
df_with_fuels.drop(['Fuel_Concordance'], axis=1, inplace=True)
df_with_fuels.drop_duplicates(inplace=True)#its important to drop duplicates here because the model concordances doubles up what was done by fuels covered by demand_side_fuel mixing.

#%%
#fill NA's in the Demand side fuel share with 1's as these are where there is no share to make *note that we have handled where the fuels may be biodiesel or gas, since we set them to just gas in the file create_demand_side_fuel_mix_input.py
df_with_fuels.loc[df_with_fuels.Demand_side_fuel_share.isna(), 'Demand_side_fuel_share'] = 1
#%%
#times teh fuel sahres by energy. This will result in a new energy value, reflecting the share of fuel used in each drive type.
df_with_fuels['Energy'] = df_with_fuels['Energy'] * df_with_fuels['Demand_side_fuel_share']

#%%
#remove the demand side fuel share column, as it is no longer needed
df_with_fuels = df_with_fuels.drop(columns=['Demand_side_fuel_share'])

#%%
#save data
df_with_fuels.to_csv('intermediate_data/model_output_with_fuels/1_demand_side/{}'.format(model_output_file_name), index=False)

#%%
