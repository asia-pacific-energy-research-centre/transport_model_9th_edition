#this will go through all the input data and add new rows if necessary. This is so that the input data covers all necessary rows, and also to get rid of NA's
#this will use concordances created in config/utilities/create_model_concordances.py to fill in the missing data

#%%
#set working directory as one folder back so that config works
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
from runpy import run_path
exec(open("config/config.py").read())#usae this to load libraries and set variables. Feel free to edit that file as you need
#%%

#laod clean user input from intermediate file
Vehicle_sales_share = pd.read_excel('intermediate_data/cleaned_input_data/clean_user_input.xlsx', sheet_name = 'Vehicle_sales_share')
Turnover_rate_growth = pd.read_excel('intermediate_data/cleaned_input_data/clean_user_input.xlsx', sheet_name = 'Turnover_rate_growth')
New_vehicle_efficiency_growth = pd.read_excel('intermediate_data/cleaned_input_data/clean_user_input.xlsx', sheet_name = 'New_vehicle_efficiency_growth')
OccupanceAndLoad_growth = pd.read_excel('intermediate_data/cleaned_input_data/clean_user_input.xlsx', sheet_name = 'OccupanceAndLoad_growth')
non_road_efficiency_growth = pd.read_excel('intermediate_data/cleaned_input_data/clean_user_input.xlsx', sheet_name = 'non_road_efficiency_growth')

#load model concordances
model_concordances = pd.read_csv('config/concordances/{}'.format(model_concordances_file_name))

#load adjsutments
turnover_rate = pd.read_csv('intermediate_data/cleaned_input_data/turnover_rate.csv')
occupance_load = pd.read_csv('intermediate_data/cleaned_input_data/occupance_load.csv')
new_vehicle_efficiency = pd.read_csv('intermediate_data/cleaned_input_data/new_vehicle_efficiency.csv')

#load 8th edition data
activity = pd.read_csv('intermediate_data/cleaned_input_data/activity_from_OSEMOSYS-hughslast.csv')
# efficiency = pd.read_csv('intermediate_data/cleaned_input_data/efficiency_by_drive.csv')
energy = pd.read_csv('intermediate_data/cleaned_input_data/energy.csv')
road_stocks = pd.read_csv('intermediate_data/cleaned_input_data/road_stocks.csv')

#%%
#ADD MISSING ROWS TO USER INPUT DATA BY USING THE MDOEL_CONCORDANCES
Vehicle_sales_share_missing_rows = model_concordances.loc[model_concordances['Medium'] == 'road'].drop(['Medium'], axis=1)
Vehicle_sales_share_missing_rows = Vehicle_sales_share_missing_rows.merge(Vehicle_sales_share, on=['Scenario', 'Economy', 'Transport Type', 'Vehicle Type', 'Drive', 'Year'], how='left')
#fillna with 0
Vehicle_sales_share_missing_rows['Vehicle_sales_share'].fillna(0, inplace=True)

#%%
New_vehicle_efficiency_growth_missing_rows = model_concordances.loc[model_concordances['Medium'] == 'road'].drop(['Medium'], axis=1)
New_vehicle_efficiency_growth_missing_rows = New_vehicle_efficiency_growth_missing_rows.merge(New_vehicle_efficiency_growth, on=['Scenario', 'Economy', 'Transport Type', 'Vehicle Type', 'Drive', 'Year'], how='left')
#fillna with 1
New_vehicle_efficiency_growth_missing_rows['New_vehicle_efficiency_growth'].fillna(1, inplace=True)
#%%

Turnover_rate_growth_missing_rows = model_concordances.loc[model_concordances['Medium'] == 'road'].drop(['Medium'], axis=1)
Turnover_rate_growth_missing_rows = Turnover_rate_growth_missing_rows.merge(Turnover_rate_growth, on=['Scenario', 'Economy', 'Transport Type', 'Vehicle Type', 'Drive', 'Year'], how='left')
#We will have to fillna with averages from other economys
Turnover_rate_growth_missing_rows['Turnover_rate_growth'].fillna(1, inplace=True)

#%%
OccupanceAndLoad_growth_missing_rows = model_concordances.loc[model_concordances['Medium'] == 'road'].drop(['Medium', 'Drive'], axis=1).drop_duplicates()
OccupanceAndLoad_growth_missing_rows = OccupanceAndLoad_growth_missing_rows.merge(OccupanceAndLoad_growth, on=['Scenario', 'Economy', 'Transport Type', 'Vehicle Type', 'Year'], how='left')
#fillna with 0
OccupanceAndLoad_growth_missing_rows['Occupancy_or_load_growth'].fillna(1, inplace=True)

#%%
#fill in missing data in activity df
activity_missing_rows = model_concordances.merge(activity, on=['Medium', 'Transport Type', 'Vehicle Type', 'Drive', 'Year', 'Economy', 'Scenario'], how='left')
#fillna with 0
activity_missing_rows['Activity'].fillna(0, inplace=True)

#%%
#fill in missing data in energy df
energy_missing_rows = model_concordances.merge(energy, on=['Medium', 'Transport Type', 'Vehicle Type', 'Drive', 'Year', 'Economy', 'Scenario'], how='left')
#fillna with 0
energy_missing_rows['Energy'].fillna(0, inplace=True)

#%%
road_stocks_missing_years = model_concordances.loc[model_concordances['Medium'] == 'road']
road_stocks_missing_years = road_stocks_missing_years.merge(road_stocks, on=['Scenario', 'Economy', 'Transport Type', 'Vehicle Type', 'Drive', 'Year', 'Medium'], how='left')
#fillna with 0
road_stocks_missing_years['Stocks'].fillna(0, inplace=True)

#%%
new_vehicle_efficiency_missing_rows = model_concordances.loc[model_concordances['Medium'] == 'road']
new_vehicle_efficiency_missing_rows = new_vehicle_efficiency_missing_rows.merge(new_vehicle_efficiency, on=['Transport Type', 'Vehicle Type', 'Drive', 'Year', 'Economy', 'Scenario'], how='left')
#fillna with 0
new_vehicle_efficiency_missing_rows['New_vehicle_efficiency'].fillna(0, inplace=True)

#there are too many missing values for 2017 in new_vehicle_efficiency, we will jsut fill them in with the values for 2018

#filter out anny values for 2017
new_vehicle_efficiency_not_2017 = new_vehicle_efficiency_missing_rows[new_vehicle_efficiency_missing_rows['Year'] != 2017]
new_vehicle_efficiency_2017 = new_vehicle_efficiency_missing_rows.loc[new_vehicle_efficiency_missing_rows['Year'] == 2018]
#set year to 2017
new_vehicle_efficiency_2017['Year'] = 2017
#concat
new_vehicle_efficiency_missing_rows = pd.concat([new_vehicle_efficiency_not_2017, new_vehicle_efficiency_2017])

#%%
non_road_efficiency_growth_missing_rows = model_concordances.loc[model_concordances['Medium'] != 'road']
non_road_efficiency_growth_missing_rows = non_road_efficiency_growth_missing_rows.merge(non_road_efficiency_growth, on=['Scenario', 'Economy','Medium', 'Transport Type', 'Vehicle Type','Drive', 'Year'], how='left')

#fillna with 1
non_road_efficiency_growth_missing_rows['Efficiency_growth'].fillna(1, inplace=True)

########################################################################################

#%%
#FILL IN VALUES WITH AVGs OF SIMILAR ROWS

#the turnover rate will be set to the average of all the other values for the same vehicle type, not dependent on column. It cannot be set to 0 otherwise growth rates will be infinite. And we had to aggregate without economy because some turnover rates avergages were a bit high where they shouldnt be
# turnover_rate.groupby(['Scenario', 'Economy','Transport Type', 'Vehicle Type', 'Year']).agg([np.mean, np.std, np.var, np.median]).reset_index()
#create avg
turnover_rate_avg = turnover_rate.dropna().groupby(['Scenario', 'Transport Type', 'Vehicle Type', 'Year']).mean()
turnover_rate_avg.rename(columns={'Turnover_rate': 'Turnover Rate_mean'}, inplace=True)
turnover_rate_avg.reset_index(inplace=True)
turnover_rate_avg = turnover_rate_avg[['Scenario', 'Transport Type', 'Vehicle Type', 'Year', 'Turnover Rate_mean']]

#merge dataframe onto the model concordances so we can identify missing rows
turnover_rate_missing_rows = model_concordances.loc[model_concordances['Medium'] == 'road'].drop(['Medium'], axis=1).drop_duplicates()
turnover_rate_missing_rows = turnover_rate_missing_rows.merge(turnover_rate, on=['Scenario', 'Economy', 'Transport Type', 'Vehicle Type', 'Year'], how='left')

#now merge avgs onto the dataframe
turnover_rate_new = turnover_rate_missing_rows.merge(turnover_rate_avg, on=['Scenario', 'Transport Type', 'Vehicle Type', 'Year'], how='left')

#where turnover rate is NA set turnover rate to the avg
turnover_rate_new['Turnover_rate'].fillna(turnover_rate_new['Turnover Rate_mean'], inplace=True)

turnover_rate_new = turnover_rate_new[['Economy', 'Transport Type', 'Vehicle Type', 'Drive', 'Year', 'Scenario', 'Turnover_rate']]

####################################################################################################################################

#%%

#TEMP FIX
#WE ONLY HAVE PRE-2017 DATA FOR OCC_LOAD.
#first we will set all values for 2017 to 2050 to the values for 2016 in occupance_load. In future it would be better to work out how to either treat this column as historical data clearly, or forecsat it clearly
occupance_load_2016 = occupance_load.loc[occupance_load.Year == 2016,:]
occupance_load_2016.drop(columns=['Year'], axis=1, inplace=True)

#create empty dataframe andd add values for occupance load for 2016 to it
occ_model_concordances = model_concordances[model_concordances['Medium'] == 'road']
occupance_load_missing_years = occ_model_concordances.drop(['Drive', 'Medium'], axis=1).drop_duplicates()
occupance_load_missing_years = occupance_load_missing_years.merge(occupance_load_2016, on=['Scenario', 'Economy', 'Transport Type', 'Vehicle Type'], how='left')

########################################################################################

# #%%
# #TEMP FIX
# #FILL IN MISSING EFFICIENCY VALUES WITH AVGS OF SIMILAR ROWS
# #theres an issue where we ahve NA and 0 values in the efficency data. Since we can expect that we could estiamte tehse values if we looked online, we will jsut create dummy values that are averages of teh other values for teh same vehicle type. (its also important that we just have a value for eff for all possible combinations of vehicle type and drive)
# #we will do this by creating a new df that has the average values for each vehicle type and then merge this back into the original df

# efficiency_vehicle_type_avgs = efficiency.copy()
# #remove 0's and NA's
# efficiency_vehicle_type_avgs = efficiency_vehicle_type_avgs.loc[(efficiency_vehicle_type_avgs['Efficiency'] > 0)]
# efficiency_vehicle_type_avgs = efficiency_vehicle_type_avgs.dropna(subset=['Efficiency'])
# #group by vehicle type and get the mean
# efficiency_vehicle_type_avgs = efficiency_vehicle_type_avgs.groupby(['Scenario', 'Economy', 'Medium', 'Transport Type', 'Vehicle Type', 'Year']).mean()#will it change much if i remove scenario from grouping?
# efficiency_vehicle_type_avgs.reset_index(inplace=True)
# #rename
# efficiency_vehicle_type_avgs.rename(columns={"Efficiency": "Efficiency_mean"}, inplace=True)
# efficiency_vehicle_type_avgs = efficiency_vehicle_type_avgs[['Scenario', 'Economy', 'Medium', 'Transport Type', 'Vehicle Type', 'Year', 'Efficiency_mean']]

########################################################################################

#%%
#save user input data
Vehicle_sales_share_missing_rows.to_csv('intermediate_data/non_aggregated_input_data/Vehicle_sales_share.csv', index=False)
OccupanceAndLoad_growth_missing_rows.to_csv('intermediate_data/non_aggregated_input_data/OccupanceAndLoad_growth.csv', index=False)
Turnover_rate_growth_missing_rows.to_csv('intermediate_data/non_aggregated_input_data/Turnover_rate_growth.csv', index=False)
New_vehicle_efficiency_growth_missing_rows.to_csv('intermediate_data/non_aggregated_input_data/New_vehicle_efficiency_growth.csv', index=False)
non_road_efficiency_growth_missing_rows.to_csv('intermediate_data/non_aggregated_input_data/non_road_efficiency_growth.csv', index=False)

#SAVE 8th edition data
road_stocks_missing_years.to_csv('intermediate_data/non_aggregated_input_data/road_stocks.csv', index=False)
activity_missing_rows.to_csv('intermediate_data/non_aggregated_input_data/activity.csv', index=False)
energy_missing_rows.to_csv('intermediate_data/non_aggregated_input_data/energy.csv', index=False)

#save other data
turnover_rate_new.to_csv('intermediate_data/non_aggregated_input_data/turnover_rate.csv', index=False)
occupance_load_missing_years.to_csv('intermediate_data/non_aggregated_input_data/occupance_load.csv', index=False)
new_vehicle_efficiency_missing_rows.to_csv('intermediate_data/non_aggregated_input_data/new_vehicle_efficiency.csv', index=False)
# %%
