#this will go through all the input data and add new rows if necessary. This is so that the input data covers all necessary rows, and also to get rid of NA's
#this will use concordances created in config/utilities/create_model_concordances.py to fill in the missing data
#to do:
#ewither make it so that this also loads data from the transport datas system or create a new script for that. 
#make it so that this file makes it clear that we arent doing all the transport data grooiming in the mdoel anymore.
#%%
#set working directory as one folder back so that config works
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
from runpy import run_path
exec(open("config/config.py").read())#usae this to load libraries and set variables. Feel free to edit that file as you need
#%%

#load the transport dataset
new_transport_dataset = pd.read_csv('intermediate_data/aggregated_model_inputs/{}_aggregated_model_data.csv'.format(FILE_DATE_ID))

##############################################

# Extract the data from the transport dataset by measure:
activity= new_transport_dataset.loc[new_transport_dataset['Measure'] == 'Activity']

# efficiency = new_transport_dataset.loc[new_transport_dataset['Measure'] == 'Efficiency']

energy= new_transport_dataset.loc[new_transport_dataset['Measure'] == 'Energy']

road_stocks= new_transport_dataset.loc[new_transport_dataset['Measure'] == 'Stocks']
#remove non road medium from roaad stocks
road_stocks= road_stocks.loc[road_stocks['Medium'] == 'road']

new_vehicle_efficiency= new_transport_dataset.loc[new_transport_dataset['Measure'] == 'New_vehicle_efficiency']

turnover_rate= new_transport_dataset.loc[new_transport_dataset['Measure'] == 'Turnover_rate']

occupance_load= new_transport_dataset.loc[new_transport_dataset['Measure'] == 'Occupancy_or_load']

#Extract user inputs from the dataset
Vehicle_sales_share= new_transport_dataset.loc[new_transport_dataset['Measure'] == 'Vehicle_sales_share']

Turnover_rate_growth= new_transport_dataset.loc[new_transport_dataset['Measure'] == 'Turnover_rate_growth']

New_vehicle_efficiency_growth= new_transport_dataset.loc[new_transport_dataset['Measure'] == 'New_vehicle_efficiency_growth']

OccupanceAndLoad_growth= new_transport_dataset.loc[new_transport_dataset['Measure'] == 'Occupancy_or_load_growth']

non_road_efficiency_growth= new_transport_dataset.loc[new_transport_dataset['Measure'] == 'Non_road_efficiency_growth']

#%%
#By default we can just fill missing data with 0 or 1. So where data_available is not 'data_available' set it to 0 or 1, else leave the value as is. 
Vehicle_sales_share['Value'] = Vehicle_sales_share.apply(lambda x: x['Value'] if x['Data_available'] == 'data_available' else 0, axis=1)
New_vehicle_efficiency_growth = New_vehicle_efficiency_growth.apply(lambda x: x['Value'] if x['Data_available'] == 'data_available' else 1, axis=1)
Turnover_rate_growth = Turnover_rate_growth.apply(lambda x: x['Value'] if x['Data_available'] == 'data_available' else 1, axis=1)
OccupanceAndLoad_growth = OccupanceAndLoad_growth.apply(lambda x: x['Value'] if x['Data_available'] == 'data_available' else 1, axis=1)
non_road_efficiency_growth = non_road_efficiency_growth.apply(lambda x: x['Value'] if x['Data_available'] == 'data_available' else 1, axis=1)

activity['Value'] = activity.apply(lambda x: x['Value'] if x['Data_available'] == 'data_available' else 0, axis=1)
energy['Value'] = energy.apply(lambda x: x['Value'] if x['Data_available'] == 'data_available' else 0, axis=1)
road_stocks['Value'] = road_stocks.apply(lambda x: x['Value'] if x['Data_available'] == 'data_available' else 0, axis=1)

new_vehicle_efficiency['Value'] = new_vehicle_efficiency.apply(lambda x: x['Value'] if x['Data_available'] == 'data_available' else 1, axis=1)

#%%
######################################################

#%%
#TODO HAVENT DONE THIS YET

####################################################################################################################################

#%%

####################################################################################################################################
#%%
#join all data together again
new_transport_dataset = pd.concat([Vehicle_sales_share, New_vehicle_efficiency_growth, Turnover_rate_growth, OccupanceAndLoad_growth, non_road_efficiency_growth, activity, energy, road_stocks, new_vehicle_efficiency, turnover_rate, occupance_load])

#remove data_available col and dataset col
new_transport_dataset.drop(['data_available', 'dataset'], axis=1, inplace=True)
########################################################################################
#%%
#save to csv
new_transport_dataset.to_csv('intermediate_data/transport_dataset_missing_rows_filled.csv', index=False)

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
if run:
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


# run_this = False
# if run_this:
#     #laod clean user input from intermediate file
#     Vehicle_sales_share = pd.read_excel('intermediate_data/cleaned_input_data/clean_user_input.xlsx', sheet_name = 'Vehicle_sales_share')
#     Turnover_rate_growth = pd.read_excel('intermediate_data/cleaned_input_data/clean_user_input.xlsx', sheet_name = 'Turnover_rate_growth')
#     New_vehicle_efficiency_growth = pd.read_excel('intermediate_data/cleaned_input_data/clean_user_input.xlsx', sheet_name = 'New_vehicle_efficiency_growth')
#     OccupanceAndLoad_growth = pd.read_excel('intermediate_data/cleaned_input_data/clean_user_input.xlsx', sheet_name = 'OccupanceAndLoad_growth')
#     non_road_efficiency_growth = pd.read_excel('intermediate_data/cleaned_input_data/clean_user_input.xlsx', sheet_name = 'non_road_efficiency_growth')

# run_this = False
# if run_this:
#     #load adjsutments
#     turnover_rate = pd.read_csv('intermediate_data/cleaned_input_data/turnover_rate.csv')
#     occupance_load = pd.read_csv('intermediate_data/cleaned_input_data/occupance_load.csv')
#     new_vehicle_efficiency = pd.read_csv('intermediate_data/cleaned_input_data/new_vehicle_efficiency.csv')

#     #load 8th edition data
#     activity = pd.read_csv('intermediate_data/cleaned_input_data/activity_from_OSEMOSYS-hughslast.csv')
#     # efficiency = pd.read_csv('intermediate_data/cleaned_input_data/efficiency_by_drive.csv')
#     energy = pd.read_csv('intermediate_data/cleaned_input_data/energy.csv')
#     road_stocks = pd.read_csv('intermediate_data/cleaned_input_data/road_stocks.csv')



# #FILL IN VALUES WITH AVGs OF SIMILAR ROWS

# #the turnover rate will be set to the average of all the other values for the same vehicle type, not dependent on column. It cannot be set to 0 otherwise growth rates will be infinite. And we had to aggregate without economy because some turnover rates avergages were a bit high where they shouldnt be
# # turnover_rate.groupby(['Scenario', 'Economy','Transport Type', 'Vehicle Type', 'Year']).agg([np.mean, np.std, np.var, np.median]).reset_index()
# #create avg
# turnover_rate_avg = turnover_rate.dropna().groupby(['Scenario', 'Transport Type', 'Vehicle Type', 'Year']).mean()
# turnover_rate_avg.rename(columns={'Turnover_rate': 'Turnover Rate_mean'}, inplace=True)
# turnover_rate_avg.reset_index(inplace=True)
# turnover_rate_avg = turnover_rate_avg[['Scenario', 'Transport Type', 'Vehicle Type', 'Year', 'Turnover Rate_mean']]

# #use data_available col to identify missing rows
# turnover_rate_missing_rows = turnover_rate[turnover_rate['Data_available'] != 'data_available']

# #now merge avgs onto the dataframe
# turnover_rate_new = turnover_rate_missing_rows.merge(turnover_rate_avg, on=['Scenario', 'Transport Type', 'Vehicle Type', 'Year'], how='left')

# #where data_available is not data_available set turnover rate to the avg
# turnover_rate_new['Turnover_rate'] = turnover_rate_new.apply(lambda x: x['Turnover Rate_mean'] if x['Data_available'] != 'data_available' else x['Turnover_rate'], axis=1)

# turnover_rate = turnover_rate_new[['Economy', 'Transport Type', 'Vehicle Type', 'Drive', 'Year', 'Scenario', 'Turnover_rate']]
