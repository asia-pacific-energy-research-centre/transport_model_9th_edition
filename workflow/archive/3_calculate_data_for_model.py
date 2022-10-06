#the point of this file is to calculate extra variables that may be needed by the model, for example travel_km_per_stock or nromalised stock sales etc.

#%%
#set working directory as one folder back so that config works
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
from runpy import run_path
run_path("config/config.py")#usae this to load libraries and set variables. Feel free to edit that file as you need


#%%
#load data
activity_efficiency_energy_road_stocks = pd.read_csv(os.path.join(intermediate_data_path, 'adjusted_input_data', 'activity_efficiency_energy_road_stocks.csv'))
occupance_load = pd.read_csv(os.path.join(intermediate_data_path, 'adjusted_input_data', 'occupance_load.csv'))
turnover_rate = pd.read_csv(os.path.join(intermediate_data_path, 'adjusted_input_data', 'turnover_rate.csv'))
vehicle_sales_share_normalised = pd.read_csv(os.path.join(intermediate_data_path, 'adjusted_input_data', 'vehicle_sales_share_normalised.csv'))

#%%
##calcualte travel km by merging stocks with occupancy
travel_km_per_stock = activity_efficiency_energy_road_stocks.merge(occupance_load, on=['Economy', 'Scenario','Transport Type', 'Vehicle Type', 'Year'], how='left')

travel_km_per_stock['Travel_km'] = travel_km_per_stock['Activity']/travel_km_per_stock['Occupancy_or_load']

travel_km_per_stock['Travel_km_per_stock'] = travel_km_per_stock['Travel_km']/travel_km_per_stock['Stocks']

#if deonminator and numerator are 0 then of course we get NAn, so we will fill these with the average of other values for the same vehicle type, using stocks as the denominator for the average

#first calc mean
#note this is probably not the right way to do this, but can fix later
average_travel_km_per_stock_of_vehicle_type = travel_km_per_stock.dropna().groupby(['Economy', 'Scenario', 'Transport Type', 'Vehicle Type', 'Year']).mean()
average_travel_km_per_stock_of_vehicle_type.reset_index(inplace=True)
average_travel_km_per_stock_of_vehicle_type.rename(columns={"Travel_km_per_stock": "Travel_km_per_stock_mean"}, inplace=True)
average_travel_km_per_stock_of_vehicle_type.drop(['Activity', 'Occupancy_or_load', 'Travel_km', 'Stocks'], axis=1, inplace=True)

travel_km_per_stock_new = travel_km_per_stock.merge(average_travel_km_per_stock_of_vehicle_type, on=['Economy', 'Scenario', 'Transport Type', 'Vehicle Type', 'Year'], how='left')

#replace any na's with 0's in travel_km and stocks cols
travel_km_per_stock_new['Travel_km'].fillna(0, inplace=True)
travel_km_per_stock_new['Stocks'].fillna(0, inplace=True)

travel_km_per_stock_new.loc[(travel_km_per_stock_new['Travel_km'] == 0) & (travel_km_per_stock_new['Stocks'] == 0), 'Travel_km_per_stock'] = travel_km_per_stock_new['Travel_km_per_stock_mean']

#remove unneeded cols. while these could be useful, it is more simple to keep dfs that arent central, being as simple as possible to make creating the central dfs more easy
travel_km_per_stock_new = travel_km_per_stock_new[['Economy', 'Scenario', 'Transport Type', 'Vehicle Type', 'Drive','Year', 'Travel_km_per_stock', 'Travel_km']]


#%%
#create a df for road model. We will filter for base year only at the start of modelling process rather than here, for simplicity for the user (so they dont need to change so many variables)
road_model_input = activity_efficiency_energy_road_stocks.loc[(activity_efficiency_energy_road_stocks['Medium'] == 'road')]

#now merge all other data (except user input) onto the dataframe
road_model_input = road_model_input.merge(travel_km_per_stock_new, on=['Economy', 'Scenario', 'Drive', 'Transport Type', 'Vehicle Type', 'Year'], how='left')
road_model_input = road_model_input.merge(vehicle_sales_share_normalised, on=['Economy', 'Scenario', 'Drive', 'Transport Type', 'Vehicle Type', 'Year'], how='left')
road_model_input = road_model_input.merge(occupance_load, on=['Economy', 'Scenario', 'Transport Type', 'Vehicle Type', 'Year'], how='left')
road_model_input = road_model_input.merge(turnover_rate, on=['Economy', 'Scenario', 'Transport Type', 'Drive','Vehicle Type', 'Year'], how='left')


road_model_input.loc[(road_model_input['Vehicle_sales_share_normalised'].isna()), 'Vehicle_sales_share_normalised'] = 0
#%%
#set surplus stocks to 0 for now
road_model_input['Surplus_stocks'] = 0

#filter for cols we need
road_model_input = road_model_input[['Economy', 'Scenario', 'Transport Type','Vehicle Type', 'Year', 'Drive', 'Activity', 'Stocks', 'Efficiency', 'Energy', 'Surplus_stocks', 'Travel_km', 'Travel_km_per_stock', 'Occupancy_or_load', 'Vehicle_sales_share_normalised','Turnover_rate']]#'Activity_per_stock', 

#%%
non_road_model_input = activity_efficiency_energy_road_stocks.loc[(activity_efficiency_energy_road_stocks['Medium'] != 'road')]
#%%
#save previous_year_main_dataframe as a temporary dataframe we can load in when we want to run the process below.
road_model_input.to_csv('intermediate_data/model_inputs/road_model_input.csv', index=False)
non_road_model_input.to_csv('intermediate_data/model_inputs/non_road_model_input.csv', index=False)

#save activity_efficiency_energy_road_stocks as it can be useful for extra analysis
activity_efficiency_energy_road_stocks.to_csv('intermediate_data/activity_efficiency_energy_road_stocks.csv', index=False)
#%%


