#%%
#set working directory as one folder back so that config works

import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
execfile("config/config.py")#usae this to load libraries and set variables. Feel free to edit that file as you need

#%%
activity_efficiency_energy_road_stocks = pd.read_csv('intermediate_data/activity_efficiency_energy_road_stocks.csv')

x = activity_efficiency_energy_road_stocks[['Medium', 'Transport Type', 'Vehicle Type', 'Drive']]#to do , add fuel to this when we get it
#by default set FUEL to:
x['FUEL'] = 'd_trn_' + x['Medium'] + '_' + x['Transport Type'] + '_' + x['Vehicle Type'] + '_' + x['Drive'] # + '_' + x['Fuel']
#if Medium is not road then set FUEL to medium and transport type
x.loc[x.Medium != 'road', 'FUEL'] = 'd_trn_' + x.Medium + '_' + x['Transport Type']
#if medium is nonspecified then set FUEL to medium and fuel
x.loc[x.Medium == 'nonspecified', 'FUEL'] = 'd_trn_' + x.Medium #+ '_' + x.Fuel#TO DO

#%%
#Now do TECHNOLOGY which is the same as FUEL except that it is a different column name, used in the inputactivityratio output and has TRN at the start
# x = activity_efficiency_energy_road_stocks[['Medium', 'Transport Type', 'Vehicle Type', 'Drive']]#to 
x['TECHNOLOGY'] = 'TRN_' + x['Medium'] + '_' + x['Transport Type'] + '_' + x['Vehicle Type'] + '_' + x['Drive'] # + '_' + x['Fuel']

#by default set FUEL to:
x['TECHNOLOGY'] = 'TRN_' + x['Medium'] + '_' + x['Transport Type'] + '_' + x['Vehicle Type'] + '_' + x['Drive'] # + '_' + x['Fuel']
#if Medium is not road then set FUEL to medium and transport type
x.loc[x.Medium != 'road', 'TECHNOLOGY'] = 'TRN_' + x.Medium + '_' + x['Transport Type']
#if medium is nonspecified then set FUEL to medium and fuel
x.loc[x.Medium == 'nonspecified', 'TECHNOLOGY'] = 'TRN_' + x.Medium #+ '_' + x.Fuel#TO DO

x = x.drop_duplicates()

x.to_csv('config/OSEMOSYS_concordances.csv', index=False)

#%%