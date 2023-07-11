#this will go through the input data and adjust the actual values and even add new rows if necessary. This is so that the input data covers all necessary rows, and also to get rid of NA's

#%%
#set working directory as one folder back so that config works
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
from runpy import run_path
run_path("config/config.py")#usae this to load libraries and set variables. Feel free to edit that file as you need
#%%

#now save
BASE_YEAR= 2017
END_YEAR = 2050

#%%
#data
activity = pd.read_csv('intermediate_data/cleaned_input_data/activity_from_OSEMOSYS-hughslast.csv')
efficiency = pd.read_csv('intermediate_data/cleaned_input_data/efficiency_by_drive.csv')
energy = pd.read_csv('intermediate_data/cleaned_input_data/energy.csv')
road_stocks = pd.read_csv('intermediate_data/cleaned_input_data/road_stocks.csv')

#load adjsutments
turnover_rate = pd.read_csv('intermediate_data/cleaned_input_data/turnover_rate.csv')
occupance_load = pd.read_csv('intermediate_data/cleaned_input_data/occupance_load.csv')
vehicle_sales_share = pd.read_csv('intermediate_data/cleaned_input_data/vehicle_sales_share.csv')
new_vehicle_efficiency = pd.read_csv('intermediate_data/cleaned_input_data/new_vehicle_efficiency.csv')

#load model concordances
model_concordances = pd.read_csv('config/concordances/{}'.format(model_concordances_file_name))

#%%
#MERGE ALL DATA TOGETHER
#first rename value columns
activity.rename(columns={'Value':'Activity'}, inplace=True)
efficiency.rename(columns={'Value':'Efficiency'}, inplace=True)
energy.rename(columns={'Value':'Energy'}, inplace=True)


#create energy with no fuel column in the df
energy_no_fuel = energy.drop('Fuel', axis=1)
#sum energy
energy_no_fuel = energy_no_fuel.groupby(['Scenario', 'Economy', 'Medium', 'Transport Type', 'Vehicle Type', 'Drive', 'Year']).sum().reset_index()

#%%


#%%
#join back onto original data
# activity_efficiency_energy_road_stocks = activity_efficiency_energy_road_stocks.merge(efficiency_vehicle_type_avgs, on=['Scenario', 'Economy', 'Medium', 'Transport Type', 'Vehicle Type', 'Year'], how='left')
# #fillna and 0s with the mean values
# activity_efficiency_energy_road_stocks['Efficiency'].fillna(activity_efficiency_energy_road_stocks['Efficiency_mean'], inplace=True)
# activity_efficiency_energy_road_stocks.loc[(activity_efficiency_energy_road_stocks['Efficiency'] == 0), 'Efficiency'] = activity_efficiency_energy_road_stocks['Efficiency_mean']
# activity_efficiency_energy_road_stocks.drop(['Efficiency_mean'], axis=1, inplace=True)
#also, efficiency for nonspecified are nan quite often. However we will leave these as nan for now since its understandable that we dont have this data and it saeems silly to create a dummy value for this

#%%


#%%

#%%


#%%




#%%
#save data in intermediate_data/adjusted_input_data
activity_efficiency_energy_road_stocks.to_csv(os.path.join(intermediate_data_path, 'adjusted_input_data', 'activity_efficiency_energy_road_stocks.csv'), index=False)
occupance_load.to_csv(os.path.join(intermediate_data_path, 'adjusted_input_data', 'occupance_load.csv'), index=False)
turnover_rate_new.to_csv(os.path.join(intermediate_data_path, 'adjusted_input_data', 'turnover_rate.csv'), index=False)
vehicle_sales_share_normalised.to_csv(os.path.join(intermediate_data_path, 'adjusted_input_data', 'vehicle_sales_share_normalised.csv'), index=False)
new_vehicle_efficiency.to_csv(os.path.join(intermediate_data_path, 'adjusted_input_data', 'new_vehicle_eff_growth.csv'), index=False)
#%%
