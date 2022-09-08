#%%
#set working directory as one folder back so that config works
from datetime import datetime
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
execfile("config/config.py")#usae this to load libraries and set variables. Feel free to edit that file as you need
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
model_concordances_file_name = 'model_concordances_20220824_1256.csv'

model_concordances = pd.read_csv('config/concordances/{}'.format(model_concordances_file_name))
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
model_concordances_file_name = 'model_concordances_20220824_1256.csv'

model_concordances = pd.read_csv('config/concordances/{}'.format(model_concordances_file_name))

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
#Create a new non raod efficiency growth rate user input file. 
#usae the model concordances, filter for vehicle type is air, rail or ship and then create a column for the efficiency growth rate. for now set it to 1. 

model_concordances_file_name = 'model_concordances_20220824_1256.csv'

model_concordances = pd.read_csv('config/concordances/{}'.format(model_concordances_file_name))

#filter for non road
non_road_efficiency_growth = model_concordances[model_concordances['Medium'] != 'road']

#add a column for the efficiency growth rate
non_road_efficiency_growth['Efficiency_growth_rate'] = 1

#save to csv
non_road_efficiency_growth.to_csv('intermediate_data/model_inputs/non_road_efficiency_growth_COMPGEN.csv', index=False)


#%%

#create new cvvehicle efficiency for road user input file from hughs files called New_vehicle_efficiency_NZS and New_vehicle_efficiency
#first read in the files. note that the first 3 rows are multindex rows and the first two columns are multiindex cols too
New_vehicle_efficiency_NZS = pd.read_csv('input_data/from_8th/raw_data/New_vehicle_efficiency_NZS.csv', header=[0,1,2], index_col=[0,1])
New_vehicle_efficiency = pd.read_csv('input_data/from_8th/raw_data/New_vehicle_efficiency.csv', header=[0,1,2], index_col=[0,1])

New_vehicle_efficiency_NZS_tall = New_vehicle_efficiency_NZS.stack().stack().stack().reset_index()
New_vehicle_efficiency_NZS_tall = New_vehicle_efficiency_NZS_tall.rename(columns={0:'Value'})
New_vehicle_efficiency_NZS_tall['Scenario'] = 'Carbon Neutral'
New_vehicle_efficiency_tall = New_vehicle_efficiency.stack().stack().stack().reset_index()
New_vehicle_efficiency_tall = New_vehicle_efficiency_tall.rename(columns={0:'Value'})
New_vehicle_efficiency_tall['Scenario'] = 'Reference'

#merge the two files
New_vehicle_efficiency_tall = pd.concat([New_vehicle_efficiency_NZS_tall, New_vehicle_efficiency_tall])

#FOR SOM REASON THE EFFICIENCY IS INVERSED, LIKE IT WOULD BE IF IT WAS THE AMOUNT OF ENERGY USED PER KM this is equivalent to input activity ratio, but the data is specified by drive type, so its a bit weigrd. sO THE HIGHER THE EFFICIENCY VALUE, THE LESS EFFICIENT THE VEHICLE. SO WE NEED TO INVERSE THE VALUES. After that, teh growth rates will reflect the growth in efficiency, as in thew amount of km per unit of energy, not the growth in energy use per km.
New_vehicle_efficiency_tall['Value'] = 1/New_vehicle_efficiency_tall['Value']

#sort by year and everything else in ascending order
New_vehicle_efficiency_tall = New_vehicle_efficiency_tall.sort_values(by=['Transport Type', 'Vehicle Type', 'Economy', 'Scenario', 'Drive', 'Year'])

#calcualte the efficiency growth rate from the values (since the values are jsut efficiency)
New_vehicle_efficiency_tall_growth = New_vehicle_efficiency_tall.set_index(['Transport Type', 'Vehicle Type', 'Economy', 'Scenario', 'Drive', 'Year']).pct_change()

#add 1 to all values so that the percentage change is now the growth rate
New_vehicle_efficiency_tall_growth = New_vehicle_efficiency_tall_growth.add(1)

#replace NAN with 1 so that any efficiency times 1 is still the same
New_vehicle_efficiency_tall_growth = New_vehicle_efficiency_tall_growth.fillna(1)

#reset index
New_vehicle_efficiency_tall_growth = New_vehicle_efficiency_tall_growth.reset_index()

#save
New_vehicle_efficiency_tall_growth.to_csv('input_data/from_8th/reformatted/New_vehicle_efficiency_tall_growth.csv', index=False)
New_vehicle_efficiency_tall.to_csv('input_data/from_8th/reformatted/New_vehicle_efficiency_tall.csv', index=False)
#%%


#laod








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
