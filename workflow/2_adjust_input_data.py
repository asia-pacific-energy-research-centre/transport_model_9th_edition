#this will go through the input data and adjust the actual values and even add new rows if necessary. This is so that the input data covers all necessary rows, and also to get rid of NA's

#%%
#set working directory as one folder back so that config works
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
execfile("config/config.py")#usae this to load libraries and set variables. Feel free to edit that file as you need
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
vehicle_sales_share_normalised = pd.read_csv('intermediate_data/cleaned_input_data/vehicle_sales_share_normalised.csv')

#load model concordances
model_concordances = pd.read_csv('config/model_concordances_20220822_1204.csv')
#%%
#MERGE ALL DATA TOGETHER
#first rename value columns
activity.rename(columns={'Value':'Activity'}, inplace=True)
efficiency.rename(columns={'Value':'Efficiency'}, inplace=True)
energy.rename(columns={'Value':'Energy'}, inplace=True)
road_stocks.rename(columns={'Value':'Road_stocks'}, inplace=True)

#create energy with no fuel column in the df
energy_no_fuel = energy.drop('Fuel', axis=1)
#sum energy
energy_no_fuel = energy_no_fuel.groupby(['Scenario', 'Economy', 'Medium', 'Transport Type', 'Vehicle Type', 'Drive', 'Year']).sum().reset_index()

#merge data
activity_efficiency = activity.merge(efficiency, on=['Scenario', 'Economy', 'Medium', 'Transport Type', 'Vehicle Type','Drive', 'Year'], how='left') 
activity_efficiency_energy = activity_efficiency.merge(energy_no_fuel, on=['Scenario', 'Economy', 'Medium', 'Transport Type', 'Vehicle Type', 'Drive', 'Year'], how='left')
activity_efficiency_energy_road_stocks = activity_efficiency_energy.merge(road_stocks, on=['Scenario', 'Economy', 'Medium', 'Transport Type', 'Vehicle Type', 'Drive', 'Year'], how='left')

#%%
#CREATE STOCKS FOR NON ROAD
#this is an adjsutment to the road stocks data from 8th edition by setting stocks to 1 for all non road vehicles that have a value >0 for activity
activity_efficiency_energy_road_stocks.loc[(activity_efficiency_energy_road_stocks['Medium'] != 'Road') & (activity_efficiency_energy_road_stocks['Activity'] > 0), 'Road_stocks'] = 1

#rename road_stocks to stocks
activity_efficiency_energy_road_stocks.rename(columns={'Road_stocks':'Stocks'}, inplace=True)

#%%
#theres an issue where we ahve NA and 0 values in the efficency data. Since we can expect that we could estiamte tehse values if we looked online, we will jsut create dummy values that are averages of teh other values for teh same vehicle type. (its also important that we just have a value for eff for all possible combinations of vehicle type and drive)
#we will do this by creating a new df that has the average values for each vehicle type and then merge this back into the original df

efficiency_vehicle_type_avgs = activity_efficiency_energy_road_stocks.copy().drop(['Activity', 'Energy'], axis=1)
#remove 0's and NA's
efficiency_vehicle_type_avgs = efficiency_vehicle_type_avgs.loc[(efficiency_vehicle_type_avgs['Efficiency'] > 0)]
efficiency_vehicle_type_avgs = efficiency_vehicle_type_avgs.dropna(subset=['Efficiency'])
#group by vehicle type and get the mean
efficiency_vehicle_type_avgs = efficiency_vehicle_type_avgs.groupby(['Scenario', 'Economy', 'Medium', 'Transport Type', 'Vehicle Type', 'Year']).mean()#will it change much if i remove scenario from grouping?
efficiency_vehicle_type_avgs.reset_index(inplace=True)
#rename
efficiency_vehicle_type_avgs.rename(columns={"Efficiency": "Efficiency_mean"}, inplace=True)
efficiency_vehicle_type_avgs = efficiency_vehicle_type_avgs[['Scenario', 'Economy', 'Medium', 'Transport Type', 'Vehicle Type', 'Year', 'Efficiency_mean']]

#%%
#join back onto original data
activity_efficiency_energy_road_stocks = activity_efficiency_energy_road_stocks.merge(efficiency_vehicle_type_avgs, on=['Scenario', 'Economy', 'Medium', 'Transport Type', 'Vehicle Type', 'Year'], how='left')
#fillna and 0s with the mean values
activity_efficiency_energy_road_stocks['Efficiency'].fillna(activity_efficiency_energy_road_stocks['Efficiency_mean'], inplace=True)
activity_efficiency_energy_road_stocks.loc[(activity_efficiency_energy_road_stocks['Efficiency'] == 0), 'Efficiency'] = activity_efficiency_energy_road_stocks['Efficiency_mean']
activity_efficiency_energy_road_stocks.drop(['Efficiency_mean'], axis=1, inplace=True)
#also, efficiency for nonspecified are nan quite often. However we will leave these as nan for now since its understandable that we dont have this data and it saeems silly to create a dummy value for this

#%%
#We also have a lot of nan's for road stocks. Best just to set these to 0's
activity_efficiency_energy_road_stocks['Stocks'].fillna(0, inplace=True)

#%%
#TEMP FIX
#we only have pre-2017 data for occ_load.
#first we will set all values for 2017 to 2050 to the values for 2016 in occupance_load. In future it would be better to work out how to either treat this column as historical data clearly, or forecsat it clearly
occupance_load_2016 = occupance_load.loc[occupance_load.Year == 2016,:]
occupance_load_2016.drop(columns=['Year'], axis=1, inplace=True)

#create empty dataframe andd add values for occupance load for 2016 to it
occ_model_concordances = model_concordances[model_concordances['Medium'] == 'road']
occupance_load_missing_years = occ_model_concordances.drop(['Drive', 'Medium'], axis=1)
occupance_load = occupance_load_missing_years.merge(occupance_load_2016, on=['Scenario', 'Economy', 'Transport Type', 'Vehicle Type'], how='left')


#%%
#TEMPORARY FIXES
#turnover rate doesnt have some rows, for most of these  we will just set the vlaues in these to 0
# however there may be cases where stocks are > 0 for these rows, in which case the turnover rate will be set to the average of all the other values for the same vehicle type
#first merge with the stocks data
turnover_rate_stocks = activity_efficiency_energy_road_stocks[activity_efficiency_energy_road_stocks['Medium'] == 'road']
turnover_rate_stocks = turnover_rate_stocks.merge(turnover_rate, on=['Scenario', 'Economy', 'Transport Type', 'Vehicle Type', 'Drive', 'Year'], how='left')
#create avg
turnover_rate_stocks_avg = turnover_rate_stocks.groupby(['Scenario', 'Economy', 'Transport Type', 'Vehicle Type', 'Year']).mean()
turnover_rate_stocks_avg.rename(columns={'Turnover_rate': 'Turnover Rate_mean'}, inplace=True)
turnover_rate_stocks_avg.reset_index(inplace=True)
turnover_rate_stocks_avg = turnover_rate_stocks_avg[['Scenario', 'Economy', 'Transport Type', 'Vehicle Type', 'Year', 'Turnover Rate_mean']]

#now merge back onto the original dataframe
turnover_rate_stocks = turnover_rate_stocks.merge(turnover_rate_stocks_avg, on=['Scenario', 'Economy', 'Transport Type', 'Vehicle Type', 'Year'], how='left')
#where stocks > 0 set turnover rate to the avg
turnover_rate_stocks.loc[(turnover_rate_stocks['Turnover_rate'].isna() & turnover_rate_stocks['Stocks'] > 0), 'Turnover_rate'] = turnover_rate_stocks['Turnover Rate_mean']
#else set it to 0 for now (turnover rate adjustment from user input will probably increase it)
turnover_rate_stocks['Turnover_rate'].fillna(0, inplace=True)

#%%
turnover_rate_new = turnover_rate_stocks[['Economy', 'Transport Type', 'Vehicle Type', 'Drive', 'Year',
       'Scenario', 'Turnover_rate']]

#%%
#add missing rows to vehicle_sales_share_normalised by using the mdoel_concordances
vehicle_sales_share_normalised_missing_years = model_concordances.loc[model_concordances['Medium'] == 'road'].drop(['Medium'], axis=1)
vehicle_sales_share_normalised = vehicle_sales_share_normalised_missing_years.merge(vehicle_sales_share_normalised, on=['Scenario', 'Economy', 'Transport Type', 'Vehicle Type', 'Drive', 'Year'], how='left')
#fillna with 0
vehicle_sales_share_normalised['Vehicle_sales_share_normalised'].fillna(0, inplace=True)

#%%
#save data in intermediate_data/adjusted_input_data
activity_efficiency_energy_road_stocks.to_csv(os.path.join(intermediate_data_path, 'adjusted_input_data', 'activity_efficiency_energy_road_stocks.csv'), index=False)
occupance_load.to_csv(os.path.join(intermediate_data_path, 'adjusted_input_data', 'occupance_load.csv'), index=False)
turnover_rate_new.to_csv(os.path.join(intermediate_data_path, 'adjusted_input_data', 'turnover_rate.csv'), index=False)
vehicle_sales_share_normalised.to_csv(os.path.join(intermediate_data_path, 'adjusted_input_data', 'vehicle_sales_share_normalised.csv'), index=False)

#%%
