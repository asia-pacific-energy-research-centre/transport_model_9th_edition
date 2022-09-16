#the point of this file is to calculate extra variables that may be needed by the model, for example travel_km_per_stock or nromalised stock sales etc.
#these varaibles are essentially the same varaibles which will be calcualted in the model as these variables act as the base year variables. 
#%%
#set working directory as one folder back so that config works
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
execfile("config/config.py")#usae this to load libraries and set variables. Feel free to edit that file as you need
#%%
#load user input data
Vehicle_sales_share_missing_rows = pd.read_csv('intermediate_data/non_aggregated_input_data/Vehicle_sales_share.csv')
OccupanceAndLoad_growth_missing_rows= pd.read_csv('intermediate_data/non_aggregated_input_data/OccupanceAndLoad_growth.csv')
Turnover_Rate_growth_missing_rows= pd.read_csv('intermediate_data/non_aggregated_input_data/Turnover_Rate_growth.csv')
New_vehicle_efficiency_growth_missing_rows= pd.read_csv('intermediate_data/non_aggregated_input_data/New_vehicle_efficiency_growth.csv')
non_road_efficiency_growth= pd.read_csv('intermediate_data/non_aggregated_input_data/non_road_efficiency_growth.csv')

#load 8th edition data
road_stocks= pd.read_csv('intermediate_data/non_aggregated_input_data/road_stocks.csv')
activity= pd.read_csv('intermediate_data/non_aggregated_input_data/activity.csv')
# efficiency= pd.read_csv('intermediate_data/non_aggregated_input_data/efficiency.csv')
energy= pd.read_csv('intermediate_data/non_aggregated_input_data/energy.csv')

#load other data
turnover_rate= pd.read_csv('intermediate_data/non_aggregated_input_data/turnover_rate.csv')
occupance_load= pd.read_csv('intermediate_data/non_aggregated_input_data/occupance_load.csv')
new_vehicle_efficiency = pd.read_csv('intermediate_data/non_aggregated_input_data/new_vehicle_efficiency.csv')

#%%

#merge data
# activity_efficiency = activity.merge(efficiency, on=['Scenario', 'Economy', 'Medium', 'Transport Type', 'Vehicle Type','Drive', 'Year'], how='left') 
activity_energy = activity.merge(energy, on=['Scenario', 'Economy', 'Medium', 'Transport Type', 'Vehicle Type', 'Drive', 'Year'], how='left')
activity_energy_road_stocks = activity_energy.merge(road_stocks, on=['Scenario', 'Economy', 'Medium', 'Transport Type', 'Vehicle Type', 'Drive', 'Year'], how='left')

#%%
#AGGREGATE ROAD MODEL INPUT
#create a df for road model. We will filter for base year later
road_model_input = activity_energy_road_stocks.loc[(activity_energy_road_stocks['Medium'] == 'road')].drop(['Medium'], axis=1)

#remove data that isnt in the base year
road_model_input = road_model_input.loc[(road_model_input['Year'] == BASE_YEAR)]

#continue joining on data
road_model_input = road_model_input.merge(Vehicle_sales_share_missing_rows, on=['Economy', 'Scenario', 'Drive', 'Transport Type', 'Vehicle Type', 'Year'], how='left')
road_model_input = road_model_input.merge(occupance_load, on=['Economy', 'Scenario', 'Transport Type', 'Vehicle Type', 'Year'], how='left')
road_model_input = road_model_input.merge(turnover_rate, on=['Economy', 'Scenario', 'Transport Type', 'Drive','Vehicle Type', 'Year'], how='left')
road_model_input = road_model_input.merge(new_vehicle_efficiency, on=['Economy', 'Scenario', 'Transport Type', 'Drive','Vehicle Type', 'Year'], how='left')

#%%
#AGGREGATE NON ROAD MODEL INPUT
non_road_model_input = activity_energy_road_stocks.loc[(activity_energy_road_stocks['Medium'] != 'road')]

#remove data that isnt in the base year
non_road_model_input = non_road_model_input.loc[(non_road_model_input['Year'] == BASE_YEAR)]
#%%
#save previous_year_main_dataframe as a temporary dataframe we can load in when we want to run the process below.
road_model_input.to_csv('intermediate_data/aggregated_model_inputs/aggregated_road_model_input.csv', index=False)
non_road_model_input.to_csv('intermediate_data/aggregated_model_inputs/aggregated_non_road_model_input.csv', index=False)

#save activity_energy_road_stocks as it can be useful for extra analysis
activity_energy_road_stocks.to_csv('intermediate_data/activity_energy_road_stocks.csv', index=False)

#%%