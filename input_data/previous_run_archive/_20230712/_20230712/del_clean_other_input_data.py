#this is intended to be where all data that is used in the model is cleaned before being adjusted to be used in the model.

#CLEANING IS anything that involves changing the format of the data. The next step is filling in missing values. 

#NOTE this data only needs to be available for the base year, as it is then changed by the growth rate that is part of the user input. 
RUN_OLD_METHOD = False#Pleasse note that we are in the process of moving this to the transport datya system and once done we will remove this file from the transport model.
if RUN_OLD_METHOD:
#%%
#set working directory as one folder back so that config works
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
from runpy import run_path
exec(open("config/config.py").read())#usae this to load libraries and set variables. Feel free to edit that file as you need

#%%
#adjustments
turnover_rate = pd.read_excel('input_data/adjustments_spreadsheet.xlsx', sheet_name='Turnover_Rate')

occupance_load = pd.read_excel('input_data/adjustments_spreadsheet.xlsx', sheet_name='OccupanceAndLoad')

new_vehicle_efficiency = pd.read_excel('input_data/adjustments_spreadsheet.xlsx', sheet_name='new_vehicle_efficiency')

#load model concordances for filling in missing dates where needed
model_concordances = pd.read_csv('config/concordances_and_config_data/{}'.format(model_concordances_file_name))

#%%
#adjust adjustments data
#make Vehicle Type and Drive cols lowercase 
occupance_load['Vehicle Type'] = occupance_load['Vehicle Type'].str.lower()

new_vehicle_efficiency['Vehicle Type'] = new_vehicle_efficiency['Vehicle Type'].str.lower()
new_vehicle_efficiency['Drive'] = new_vehicle_efficiency['Drive'].str.lower()

turnover_rate['Vehicle Type'] = turnover_rate['Vehicle Type'].str.lower()


#%%
#replicate data so we have data for each scneario in the adjustments data. We can dcide later if we want to explicitly create diff data for the scenrios later or always replicate,, or even rpovdie a switch

occupance_load_CN = occupance_load.copy()
occupance_load_CN['Scenario'] = 'Carbon Neutral'
occupance_load['Scenario'] = 'Reference'
occupance_load = pd.concat([occupance_load, occupance_load_CN])

turnover_rate_CN = turnover_rate.copy()
turnover_rate_CN['Scenario'] = 'Carbon Neutral'
turnover_rate['Scenario'] = 'Reference'
turnover_rate = pd.concat([turnover_rate, turnover_rate_CN])

#create data for 2017 using the data from 2018
turnover_rate_2017 = turnover_rate[turnover_rate['Year']==2018].copy()
turnover_rate_2017['Year'] = 2017
turnover_rate = pd.concat([turnover_rate, turnover_rate_2017])

#%%
#rename cols
occupance_load.rename(columns={"Value": "Occupancy_or_load"}, inplace=True)
turnover_rate.rename(columns={"Value": "Turnover_rate"}, inplace=True)
new_vehicle_efficiency.rename(columns={"Value": "New_vehicle_efficiency"}, inplace=True)

#ideal to change spreadhseet than renae here

#%%
#SAVE
turnover_rate.to_csv('intermediate_data/cleaned_input_data/turnover_rate.csv', index=False)
occupance_load.to_csv('intermediate_data/cleaned_input_data/occupance_load.csv', index=False)

new_vehicle_efficiency.to_csv('intermediate_data/cleaned_input_data/new_vehicle_efficiency.csv', index=False)
#%%