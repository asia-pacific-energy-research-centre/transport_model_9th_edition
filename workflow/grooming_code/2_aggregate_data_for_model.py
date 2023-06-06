#the point of this file is to calculate extra variables that may be needed by the model, for example travel_km_per_stock or nromalised stock sales etc.
#these varaibles are essentially the same varaibles which will be calcualted in the model as these variables act as the base year variables.
# 
# #to do: 
#remove scenario from data in all data for the base year as that is intended to be independent of the sceanrio. This will mean adding the scenario in the actual model.
#%%
#set working directory as one folder back so that config works
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
from runpy import run_path
exec(open("config/config.py").read())#usae this to load libraries and set variables. Feel free to edit that file as you need
#%%

#load data from transport datasystem
new_transport_dataset = pd.read_csv('intermediate_data/{}_transport_data_system_extract.csv'.format(FILE_DATE_ID))

#laod clean user input from intermediate file
user_input = pd.read_csv('intermediate_data/{}_user_inputs_and_growth_rates.csv'.format(FILE_DATE_ID))

#load activity growth data and macro data
# macro1.to_csv('intermediate_data/model_inputs/regression_based_growth_estimates.csv', index=False)
growth = pd.read_csv('intermediate_data/model_inputs/regression_based_growth_estimates.csv')
# growth.columns Index(['economy', 'date',Transport type 'GDP_per_capita', 'Population', 'GDP',
#        'GDP_times_capita', 'GDP_growth', 'Population_growth',
#        'GDP_per_capita_growth', 'GDP_times_capita_growth', 'region', 'const',
#        'gdp_per_capita_growth_coeff', 'gdp_times_capita_growth_coeff', 'r2',
#        'energy_growth_est', 'Activity_growth_est', 'Activity_growth_8th',
#        'Activity_growth_8th_index'],
#       dtype='object')
#%%

#connect user inputs with transport datassystem dataset

#create Dataset column in user input and call it 'user_input'
user_input['Dataset'] = 'user_input'
#same for growth but call it 'growth_forecasts'
growth['Dataset'] = 'growth_forecasts'

#filter fvor only nans in value col and print what measures they are from. iof they are jsut ['Activity_growth_8th' 'Activity_growth_8th_index'] then ignore, else throw an error and fix the nans
if growth.loc[growth['Value'].isna(), 'Measure'].unique().tolist() != ['Activity_growth_8th', 'Activity_growth_8th_index']:
    nans= growth.loc[growth['Value'].isna(), 'Measure'].unique().tolist()
    nans.remove('Activity_growth_8th')
    nans.remove('Activity_growth_8th_index')
    print('These measures contains nans iun the value column. They will be ignored in the model. Please check the data and fix the nans if you want to use them in the model. ' +nans)
#%%
#concat user inputs to transport dataset
aggregated_model_data = pd.concat([new_transport_dataset, user_input], sort=False)
#concat growth to transport dataset
aggregated_model_data = pd.concat([aggregated_model_data, growth], sort=False)

#%%
#make sure that the data is in the right format. We will have date as int, value as float and all others as objects. if there si an error, then something is probably wrong with the data
aggregated_model_data['Date'] = aggregated_model_data['Date'].astype(int)
aggregated_model_data['Value'] = aggregated_model_data['Value'].astype(float)
other_cols = aggregated_model_data.columns.tolist()
other_cols.remove('Date')
other_cols.remove('Value')
aggregated_model_data[other_cols] = aggregated_model_data[other_cols].astype(str)

#convert 'nan' to np.nan
aggregated_model_data = aggregated_model_data.replace('nan', np.nan)
#%%
#convert units to similar magnitudes. We might need to change the units as well.
#these are based off the units in measure_to_unit_concordance from config.py
measure_to_unit_concordance = pd.read_csv('config/concordances_and_config_data/measure_to_unit_concordance.csv')
# 	Unit	Measure	Magnitude_adjustment	Magnitude_adjusted_unit
# 	Pj	Energy	1.000000e+00	PJ
# Magnitude_adjustment is needed to convert the numbers from their Unit to their Magnitude adjusted unit. 
# eg. to convert form stocks to million stocks just itmes the vlaue by magnitude adjustment
#%%
#convert to dict
unit_to_adj_unit_concordance_dict = measure_to_unit_concordance.set_index('Unit').to_dict()['Magnitude_adjusted_unit']
value_adjustment_concordance_dict = measure_to_unit_concordance.set_index('Unit').to_dict()['Magnitude_adjustment']
#just go through the concordance and convert the units and values
for unit in unit_to_adj_unit_concordance_dict.keys():
    
    #convert values
    aggregated_model_data.loc[aggregated_model_data['Unit']==unit, 'Value'] = aggregated_model_data.loc[aggregated_model_data['Unit']==unit, 'Value'] * value_adjustment_concordance_dict[unit]

    #convert units
    aggregated_model_data.loc[aggregated_model_data['Unit']==unit, 'Unit'] = unit_to_adj_unit_concordance_dict[unit]
#%%
#IMPORTANT ERROR CHECK FOR LINE 135 OF 1_RUN_ROAD_MODEL.PY
#check that the units for stocks and populatin are in millions and thousands respectively
if aggregated_model_data.loc[aggregated_model_data['Measure']=='Stocks', 'Unit'].unique().tolist() != ['Million_stocks']:
    print('ERROR: The units for stocks are not in millions. Please fix the data')
if aggregated_model_data.loc[aggregated_model_data['Measure']=='Population', 'Unit'].unique().tolist() != ['Population_thousands']:
    print('ERROR: The units for population are not in thousands. Please fix the data')
#%%
#save
aggregated_model_data.to_csv('intermediate_data/aggregated_model_inputs/{}_aggregated_model_data.csv'.format(FILE_DATE_ID), index=False)


# #%%

#%%
# #testing:
# #plot freight tonne km for 2017 for 01_AUS
# aggregated_model_data[(aggregated_model_data['Date']=='2017') & (aggregated_model_data['Economy']=='20_USA') & (aggregated_model_data['Measure']=='Energy')].plot(x='Medium',y='Value',kind='bar')
# aggregated_model_data[(aggregated_model_data['Date']==2017) & (aggregated_model_data['Economy']=='20_USA') & (aggregated_model_data['Measure']=='passenger_km')].groupby(['Medium','Economy']).sum().reset_index().plot(x='Medium',y='Value',kind='bar') 

# #sum by medium and economy then plot
# aggregated_model_data[(aggregated_model_data['Date']==2017) & (aggregated_model_data['Economy']=='20_USA') & (aggregated_model_data['Measure']=='Energy')].groupby(['Medium']).sum().plot(y='Value',kind='bar')


#%%





# #%%
# if run:
#     #merge data
#     # activity_efficiency = activity.merge(efficiency, on=['Scenario', 'Economy', 'Medium', 'Transport Type', 'Vehicle Type','Drive', 'Year'], how='left') 
#     activity_energy = activity.merge(energy, on=['Scenario', 'Economy', 'Medium', 'Transport Type', 'Vehicle Type', 'Drive', 'Year'], how='left')
#     activity_energy_road_stocks = activity_energy.merge(road_stocks, on=['Scenario', 'Economy', 'Medium', 'Transport Type', 'Vehicle Type', 'Drive', 'Year'], how='left')

# #%%
# if run:
#     #AGGREGATE ROAD MODEL INPUT
#     #create a df for road model. We will filter for base year later
#     road_model_input = activity_energy_road_stocks.loc[(activity_energy_road_stocks['Medium'] == 'road')].drop(['Medium'], axis=1)

#     #remove data that isnt in the base year
#     road_model_input = road_model_input.loc[(road_model_input['Year'] == BASE_YEAR)]

#     #continue joining on data
#     road_model_input = road_model_input.merge(Vehicle_sales_share, on=['Economy', 'Scenario', 'Drive', 'Transport Type', 'Vehicle Type', 'Year'], how='left')
#     road_model_input = road_model_input.merge(occupance_load, on=['Economy', 'Scenario', 'Transport Type', 'Vehicle Type', 'Year'], how='left')
#     road_model_input = road_model_input.merge(turnover_rate, on=['Economy', 'Scenario', 'Transport Type', 'Drive','Vehicle Type', 'Year'], how='left')
#     road_model_input = road_model_input.merge(new_vehicle_efficiency, on=['Economy', 'Scenario', 'Transport Type', 'Drive','Vehicle Type', 'Year'], how='left')

# #%%
# if run:
#     #AGGREGATE NON ROAD MODEL INPUT
#     non_road_model_input = activity_energy_road_stocks.loc[(activity_energy_road_stocks['Medium'] != 'road')]

#     #remove data that isnt in the base year
#     non_road_model_input = non_road_model_input.loc[(non_road_model_input['Year'] == BASE_YEAR)]

# #%%
# run= False
# if run:
#     #AGGREGATE USER DEFINED INPUTS AND GROWTH RATES
#     #join on user defined inputs
#     Vehicle_sales_share = pd.read_csv('intermediate_data/non_aggregated_input_data/Vehicle_sales_share.csv')
#     OccupanceAndLoad_growth= pd.read_csv('intermediate_data/non_aggregated_input_data/OccupanceAndLoad_growth.csv')
#     Turnover_Rate_growth= pd.read_csv('intermediate_data/non_aggregated_input_data/Turnover_Rate_growth.csv')
#     New_vehicle_efficiency_growth= pd.read_csv('intermediate_data/non_aggregated_input_data/New_vehicle_efficiency_growth.csv')
#     non_road_efficiency_growth= pd.read_csv('intermediate_data/non_aggregated_input_data/non_road_efficiency_growth.csv')

#     #non road:
#     non_road_user_input_growth = non_road_efficiency_growth.copy()
#     non_road_user_input_growth = non_road_user_input_growth.merge(Activity_growth, on=['Economy', 'Year', 'Scenario'], how='left')

#     #road:
#     road_user_input_growth = Vehicle_sales_share.copy()
#     road_user_input_growth = road_user_input_growth.merge(Turnover_Rate_growth, on=['Economy', 'Scenario', 'Transport Type', 'Vehicle Type', 'Year', 'Drive'], how='left')
#     road_user_input_growth = road_user_input_growth.merge(New_vehicle_efficiency_growth, on=['Economy', 'Scenario', 'Transport Type', 'Vehicle Type', 'Year', 'Drive'], how='left')
#     road_user_input_growth = road_user_input_growth.merge(OccupanceAndLoad_growth, on=['Economy', 'Scenario', 'Transport Type', 'Vehicle Type', 'Year'], how='left')
#     road_user_input_growth = road_user_input_growth.merge(Activity_growth, on=['Economy','Scenario', 'Year'], how='left')

# #%%
# #NOTE WANT TO USE THIS AT THE END OF GREOOMING
# if run:
#     #save previous_year_main_dataframe as a temporary dataframe we can load in when we want to run the process below.
#     road_model_input.to_csv('intermediate_data/aggregated_model_inputs/aggregated_road_model_input.csv', index=False)
#     non_road_model_input.to_csv('intermediate_data/aggregated_model_inputs/aggregated_non_road_model_input.csv', index=False)

#     #save activity_energy_road_stocks as it can be useful for extra analysis
#     activity_energy_road_stocks.to_csv('intermediate_data/activity_energy_road_stocks.csv', index=False)

#     #save user input growth rates
#     road_user_input_growth.to_csv('intermediate_data/aggregated_model_inputs/road_user_input_and_growth_rates.csv', index=False)
#     non_road_user_input_growth.to_csv('intermediate_data/aggregated_model_inputs/non_road_user_input_and_growth_rates.csv', index=False)
# #%%


# run = False
# if run:
#     #load 8th edition data
#     road_stocks= pd.read_csv('intermediate_data/non_aggregated_input_data/road_stocks.csv')
#     activity= pd.read_csv('intermediate_data/non_aggregated_input_data/activity.csv')
#     # efficiency= pd.read_csv('intermediate_data/non_aggregated_input_data/efficiency.csv')
#     energy= pd.read_csv('intermediate_data/non_aggregated_input_data/energy.csv')

#     #load other data
#     turnover_rate= pd.read_csv('intermediate_data/non_aggregated_input_data/turnover_rate.csv')
#     occupance_load= pd.read_csv('intermediate_data/non_aggregated_input_data/occupance_load.csv')
#     new_vehicle_efficiency = pd.read_csv('intermediate_data/non_aggregated_input_data/new_vehicle_efficiency.csv')
#     #load user input data
#     Vehicle_sales_share = pd.read_csv('intermediate_data/non_aggregated_input_data/Vehicle_sales_share.csv')
#     OccupanceAndLoad_growth= pd.read_csv('intermediate_data/non_aggregated_input_data/OccupanceAndLoad_growth.csv')
#     Turnover_Rate_growth= pd.read_csv('intermediate_data/non_aggregated_input_data/Turnover_Rate_growth.csv')
#     New_vehicle_efficiency_growth= pd.read_csv('intermediate_data/non_aggregated_input_data/New_vehicle_efficiency_growth.csv')
#     non_road_efficiency_growth= pd.read_csv('intermediate_data/non_aggregated_input_data/non_road_efficiency_growth.csv')
#     Activity_growth = pd.read_csv('intermediate_data/model_inputs/Activity_growth.csv')


#format data
# #filter for 'data_available' in Data_available column
# new_transport_dataset = new_transport_dataset.loc[new_transport_dataset['Data_available'] == 'data_available']

# #remove unnecessary columns
# new_transport_dataset.drop(['Unit', 'Final_dataset_selection_method', 'Dataset', 'Data_available'], inplace=True, axis=1)

# %%
