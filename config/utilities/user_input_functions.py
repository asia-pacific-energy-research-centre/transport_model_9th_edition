#%%
#set working directory as one folder back so that config works
from datetime import datetime
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
execfile("config/config.py")#usae this to load libraries and set variables. Feel free to edit that file as you need

#%%
#create set of categories of data that will be output by the model. 
osemosys_concordances = pd.read_csv('config/OSEMOSYS_concordances.csv')
osemosys_concordances.drop(['FUEL', 'TECHNOLOGY'], axis=1, inplace=True)
#drop duplicates
osemosys_concordances.drop_duplicates(inplace=True)

#could create concordances for each year, economy and scenario and then cross that with the osemosys_concordances to get the final concordances
model_concordances = pd.DataFrame(columns=osemosys_concordances.columns)
for year in range(BASE_YEAR, END_YEAR+1):
    for economy in Economy_list:
        for scenario in Scenario_list:
            #create concordances for each year, economy and scenario
            osemosys_concordances_year = osemosys_concordances.copy()
            osemosys_concordances_year['Year'] = str(year)
            osemosys_concordances_year['Economy'] = economy
            osemosys_concordances_year['Scenario'] = scenario
            #merge with osemosys_concordances
            model_concordances = pd.concat([model_concordances, osemosys_concordances_year])

#save model_concordances with date
model_concordances.to_csv('config/model_concordances_{}.csv'.format(datetime.datetime.now().strftime("%Y%m%d_%H%M")), index=False)

#%%
#create a user input spreadsheet using the model concordances above
#we want the year column to become wide, so we'll use pivot_table
model_concordances_wide = model_concordances.copy()
model_concordances_wide['Value'] = 1
# model_concordances_wide['Year'] = str(model_concordances_wide['Year'])
model_concordances_wide = model_concordances_wide.pivot_table(index=['Medium',	'Transport Type',	'Vehicle Type',	'Drive', 'Economy',	'Scenario'
], columns='Year', values='Value').reset_index()

#save model_concordances_wide with date
model_concordances_wide.to_csv('config/model_concordances_wide_{}.csv'.format(datetime.datetime.now().strftime("%Y%m%d_%H%M")), index=False)
#%%

#create funciton to check a dataset for whether it contains all the rows in our concordances. If it doesn't, add that row.
def check_for_missing_rows(dataset, concordances, index_cols):
    #set index
    dataset.set_index(index_cols, inplace=True)
    concordances.set_index(index_cols, inplace=True)

    missing_rows_in_dataset = concordances[~concordances.index.isin(dataset.index)]
    dataset_with_missing_rows = pd.concat([dataset, missing_rows_in_dataset])
    print('There are {} missing rows in the dataset'.format(len(missing_rows_in_dataset)))

    missing_rows_in_concordances = dataset[~dataset.index.isin(concordances.index)]
    concordances_with_missing_rows = pd.concat([concordances, missing_rows_in_concordances])
    print('There are {} missing rows in the concordances'.format(len(missing_rows_in_concordances)))

    return missing_rows_in_dataset, missing_rows_in_concordances

#%%
model_concordances =pd.read_csv('config/model_concordances_{}.csv'.format("20220822_1204"))

#laod clean user input from intermediate file
Switching_vehicle_sales_dist = pd.read_excel('intermediate_data/model_inputs/clean_user_input.xlsx', sheet_name = 'Switching_vehicle_sales_dist')
Turnover_Rate_adjustments = pd.read_excel('intermediate_data/model_inputs/clean_user_input.xlsx', sheet_name = 'Turnover_Rate_adjustments')
New_vehicle_efficiency_growth = pd.read_excel('intermediate_data/model_inputs/clean_user_input.xlsx', sheet_name = 'New_vehicle_efficiency_growth')
OccupanceAndLoad_growth = pd.read_excel('intermediate_data/model_inputs/clean_user_input.xlsx', sheet_name = 'OccupanceAndLoad_growth')


index_cols =['Transport Type', 'Vehicle Type', 'Drive', 'Economy', 'Scenario', 'Year']

dataset_with_missing_rows, concordances_with_missing_rows = check_for_missing_rows(Switching_vehicle_sales_dist,model_concordances,index_cols)

#%%
#Note that i used the below to check all user input had the cocordances in them, which was true.
model_concordances =pd.read_csv('config/model_concordances_{}.csv'.format("20220822_1204"))
#test when filtering coocrdances for only medium == road
# dataset = OccupanceAndLoad_growth.copy()
dataset = Switching_vehicle_sales_dist.copy()
# dataset = dataset[dataset['Medium'] == 'Road']
concordances = model_concordances[model_concordances['Medium'] == 'road']
# index_cols =['Transport Type', 'Vehicle Type',  'Economy', 'Scenario', 'Year']
index_cols =['Transport Type', 'Vehicle Type',  'Economy', 'Scenario', 'Year','Drive']
dataset.set_index(index_cols, inplace=True)
concordances.set_index(index_cols, inplace=True)

missing_rows_in_dataset = concordances[~concordances.index.isin(dataset.index)]
dataset_with_missing_rows = pd.concat([dataset, missing_rows_in_dataset])
print('There are {} missing rows in the dataset'.format(len(missing_rows_in_dataset)))

# dataset_with_missing_rows, concordances_with_missing_rows = check_for_missing_rows(dataset,concordances,index_cols)

#%%
road_model_input = pd.read_csv('intermediate_data/model_inputs/road_model_input.csv')
activity_growth = pd.read_csv('intermediate_data/model_inputs/activity_growth.csv')
dataset = road_model_input.copy()
# dataset = Switching_vehicle_sales_dist.copy()#[Switching_vehicle_sales_dist['Medium'] == 'Road']
model_concordances_road = model_concordances[model_concordances['Medium'] == 'road']
index_cols =['Transport Type', 'Vehicle Type',  'Economy', 'Scenario', 'Year','Drive']

dataset_with_missing_rows, concordances_with_missing_rows = check_for_missing_rows(dataset,model_concordances_road,index_cols)
#%%
#fill in user input
#we want to provide some functions so that if the user wants to only provide some data in the user input, we can fill in the rest:

#first an option for interpolating between values using eitehr linear or logarithmic interpolation
def interpolate_between_values(dataset, concordances, index_cols, interpolation_type='linear'):
    #set index
    dataset.set_index(index_cols, inplace=True)

    #interpolate between values
    if interpolation_type == 'linear':
        dataset = dataset.interpolate(method='linear')
    elif interpolation_type == 'logarithmic':
        print(' logarithmic interpolation type doesnt work yet. Here is the error you would get (ValueError: Only `method=linear` interpolation is supported on MultiIndexes.) ') 
        # dataset_with_missing_rows = dataset_with_missing_rows.interpolate(method='logarithmic')
    else:
        print('Please select either linear or logarithmic for the interpolation type')
    
    return dataset
    
#%%
# eg.
x = Switching_vehicle_sales_dist[Switching_vehicle_sales_dist['Year'].isin([2017, 2018, 2019, 2020])]
x.loc[x['Year'] == 2018, 'Sales_adjustment'] = np.nan
x.set_index(index_cols, inplace=True)
y = x.interpolate(method='linear').reset_index()
y = x.interpolate(method='spline').reset_index()
#using function
index_cols =['Transport Type', 'Vehicle Type',  'Economy', 'Scenario', 'Year']#'Drive',

Switching_vehicle_sales_dist_interpolated = interpolate_between_values(Switching_vehicle_sales_dist, model_concordances, index_cols)
#%%



# missing_rows1.reset_index(inplace=True)
# missing_rows1[(missing_rows1['Vehicle Type'] == 'lv' & missing_rows1['Drive'] == 'phevg' & missing_rows1['Economy'] == '21_VN'), :]
# #####################################################################
#%%

# #This one will take a long while because of the amount of iterations
# #It will run through the data in user input and make sure that it covers for the unique combinations of rows that are needed for the model.
# #it will load the data that is outputted by clean_user_input.py 

# #laod clean user input from intermediate file
# Switching_vehicle_sales_dist = pd.read_excel('intermediate_data/model_inputs/clean_user_input.xlsx', sheet_name = 'Switching_vehicle_sales_dist')
# Turnover_Rate_adjustments = pd.read_excel('intermediate_data/model_inputs/clean_user_input.xlsx', sheet_name = 'Turnover_Rate_adjustments')
# New_vehicle_efficiency_growth = pd.read_excel('intermediate_data/model_inputs/clean_user_input.xlsx', sheet_name = 'New_vehicle_efficiency_growth')
# OccupanceAndLoad_growth = pd.read_excel('intermediate_data/model_inputs/clean_user_input.xlsx', sheet_name = 'OccupanceAndLoad_growth')

# #adjsut user input values
# Switching_vehicle_sales_dist.rename(columns={"Sales_adjustment": "Value"}, inplace=True)
# Turnover_Rate_adjustments.rename(columns={"Turnover_rate_adjustment": "Value"}, inplace=True)
# New_vehicle_efficiency_growth.rename(columns={"New_vehicle_efficiency_growth": "Value"}, inplace=True)
# OccupanceAndLoad_growth.rename(columns={"Occupancy_or_load_adjustment": "Value"}, inplace=True)

# #%%
# #change the labels of data column t have nme 'Value'
# check_user_input = True
# if check_user_input:
        
#     #fill in user input where we are nissing data

#     #to do this we need to know all the possble rows of user input that are needed. To do this we will get the unique combinations of transport type, vehicle type and drive
#     #load osemosy concordances and remove FUEL and TECHNOLOGY cols
#     osemosys_concordances = pd.read_csv('config/OSEMOSYS_concordances.csv')
#     osemosys_concordances.drop(['FUEL', 'TECHNOLOGY'], axis=1, inplace=True)
#     #drop duplicates
#     osemosys_concordances.drop_duplicates(inplace=True)
#     #check that the user inputs have the above combinations for each year, economy and scenario, except where those columns are not available, eg. occupancy and load growth doesnt have drive
#     add_rows = True
#     END_YEAR = 2018
#     #go through possible combinations of scneario, year and economy
#     for year in range(BASE_YEAR, END_YEAR+1):
#         for economy in Economy_list:
#             for scenario in Scenario_list:
#                 for df in [Switching_vehicle_sales_dist, Turnover_Rate_adjustments, New_vehicle_efficiency_growth, OccupanceAndLoad_growth]:
#                     #get unique combinations of transport type, vehicle type and drive
#                     if df.columns.str.contains('Drive').any():#if there is a drive column do this part
#                         unique_combinations = df.loc[(df['Year'] == year) & (df['Economy'] == economy) & (df['Scenario'] == scenario), ['Transport Type', 'Vehicle Type', 'Drive']]
#                         #check these combinations are in the osmosys concordances and all the ones in osemosys concordances are in the user input
#                         for combination in unique_combinations.itertuples(index=False):
#                             if combination not in osemosys_concordances.itertuples(index=False):
#                                 print('{} {} {} {} is not in the osmosys concordances'.format(year, economy, scenario, combination[0], combination[1], combination[2]))
#                             if combination not in df.itertuples():
#                                 print('{} {} {} {} is not in the user input'.format(year, economy, scenario, combination[0], combination[1], combination[2]))
#                                 if add_rows:
#                                     #add the missing combination to the user input and set the values to 0
#                                     print('added the row \n')
#                                     df = df.append({'Year': year, 'Economy': economy, 'Scenario': scenario, 'Transport Type': combination[0], 'Vehicle Type': combination[1], 'Drive': combination[2], 'Value': 0}, ignore_index=True)
#                     else:#if there is no drive column do this part
#                         unique_combinations = df.loc[(df['Year'] == year) & (df['Economy'] == economy) & (df['Scenario'] == scenario), ['Transport Type', 'Vehicle Type']]
#                         #check these combinations are in the osmosys concordances and all the ones in osemosys concordances are in the user input
#                         for combination in unique_combinations.itertuples():
#                             if combination not in osemosys_concordances.drop(['Drive'], axis=1).itertuples(index=False):
#                                 print('{} {} {} {} is not in the osmosys concordances'.format(year, economy, scenario, combination[0], combination[1]))
#                             if combination not in df.itertuples(index=False):
#                                 print('{} {} {} {} is not in the user input'.format(year, economy, scenario, combination[0], combination[1]))
#                                 if add_rows:
#                                     #add the missing combination to the user input and set the values to 0
#                                     print('added the row \n')
#                                     df = df.append({'Year': year, 'Economy': economy, 'Scenario': scenario, 'Transport Type': combination[0], 'Vehicle Type': combination[1],'Value': 0}, ignore_index=True)

# #%%
# %%
