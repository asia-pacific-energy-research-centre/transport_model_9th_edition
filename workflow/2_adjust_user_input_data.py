#this will go through the input data and adjust the actual values and even add new rows if necessary. This is so that the input data covers all necessary rows, and also to get rid of NA's

#%%
#set working directory as one folder back so that config works
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
execfile("config/config.py")#usae this to load libraries and set variables. Feel free to edit that file as you need
#%%

#laod clean user input from intermediate file
Switching_vehicle_sales_dist = pd.read_excel('intermediate_data/model_inputs/clean_user_input.xlsx', sheet_name = 'Switching_vehicle_sales_dist')
Turnover_Rate_adjustments = pd.read_excel('intermediate_data/model_inputs/clean_user_input.xlsx', sheet_name = 'Turnover_Rate_adjustments')
New_vehicle_efficiency_growth = pd.read_excel('intermediate_data/model_inputs/clean_user_input.xlsx', sheet_name = 'New_vehicle_efficiency_growth')
OccupanceAndLoad_growth = pd.read_excel('intermediate_data/model_inputs/clean_user_input.xlsx', sheet_name = 'OccupanceAndLoad_growth')


#%%
#load model concordances for filling in missing dates where needed
model_concordances = pd.read_csv('config/model_concordances_20220822_1204.csv')

#%%
#add missing rows to Switching_vehicle_sales_dist by using the mdoel_concordances
Switching_vehicle_sales_dist_missing_years = model_concordances.loc[model_concordances['Medium'] == 'road'].drop(['Medium'], axis=1)
Switching_vehicle_sales_dist_missing_years = Switching_vehicle_sales_dist_missing_years.merge(Switching_vehicle_sales_dist, on=['Scenario', 'Economy', 'Transport Type', 'Vehicle Type', 'Drive', 'Year'], how='left')
#fillna with 0
Switching_vehicle_sales_dist_missing_years['Sales_adjustment'].fillna(0, inplace=True)

#%%
New_vehicle_efficiency_growth_missing_years = model_concordances.loc[model_concordances['Medium'] == 'road'].drop(['Medium'], axis=1)
New_vehicle_efficiency_growth_missing_years = New_vehicle_efficiency_growth_missing_years.merge(New_vehicle_efficiency_growth, on=['Scenario', 'Economy', 'Transport Type', 'Vehicle Type', 'Drive', 'Year'], how='left')
#fillna with 1
New_vehicle_efficiency_growth_missing_years['New_vehicle_efficiency_growth'].fillna(1, inplace=True)

#%%
#add missing rows to Turnover_Rate_adjustments by using the mdoel_concordances
Turnover_Rate_adjustments_missing_years = model_concordances.loc[model_concordances['Medium'] == 'road'].drop(['Medium'], axis=1)
Turnover_Rate_adjustments_missing_years = Turnover_Rate_adjustments_missing_years.merge(Turnover_Rate_adjustments, on=['Scenario', 'Economy', 'Transport Type', 'Vehicle Type', 'Drive', 'Year'], how='left')
#fillna with 0
Turnover_Rate_adjustments_missing_years['Turnover_rate_adjustment'].fillna(0, inplace=True)

#%%
OccupanceAndLoad_growth_missing_years = model_concordances.loc[model_concordances['Medium'] == 'road'].drop(['Medium', 'Drive'], axis=1).drop_duplicates()
OccupanceAndLoad_growth_missing_years = OccupanceAndLoad_growth_missing_years.merge(OccupanceAndLoad_growth, on=['Scenario', 'Economy', 'Transport Type', 'Vehicle Type', 'Year'], how='left')
#fillna with 0
OccupanceAndLoad_growth_missing_years['Occupancy_or_load_adjustment'].fillna(0, inplace=True)

#%%
#save data to adjusted_input_data
Switching_vehicle_sales_dist_missing_years.to_csv('intermediate_data/model_inputs/Switching_vehicle_sales_dist.csv', index=False)
OccupanceAndLoad_growth_missing_years.to_csv('intermediate_data/model_inputs/OccupanceAndLoad_growth.csv', index=False)
Turnover_Rate_adjustments_missing_years.to_csv('intermediate_data/model_inputs/Turnover_Rate_adjustments.csv', index=False)
New_vehicle_efficiency_growth_missing_years.to_csv('intermediate_data/model_inputs/New_vehicle_efficiency_growth.csv', index=False)


