#the point of this file is to calculate extra variables that may be needed by the model, for example travel_km_per_stock or nromalised stock sales etc.
#these varaibles are essentially the same varaibles which will be calcualted in the model as these variables act as the base year variables. 

#please note that in the current state of the input data, this file has become qite messy with hte need to fill in missing data at this stage of the creation of the input data for the model. When we have good data we can make this more clean and suit the intended porupose to fthe file.
#%%
#set working directory as one folder back so that config works
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
from runpy import run_path
exec(open("config/config.py").read())#usae this to load libraries and set variables. Feel free to edit that file as you need

#%%
#load data
transport_dataset = pd.read_csv('intermediate_data/aggregated_model_inputs/{}_aggregated_model_data.csv'.format(FILE_DATE_ID))

#%%
#remove uneeded columns
unneeded_cols =['Unit','Dataset', 'Data_available', 'Frequency']
transport_dataset.drop(unneeded_cols, axis=1, inplace=True)
#remove those cols from INDEX_COLS
INDEX_COLS = [x for x in INDEX_COLS if x not in unneeded_cols]
#set index cols
# INDEX_COLS = ['Date', 'Economy', 'Vehicle Type', 'Medium','Transport Type', 'Drive', 'Scenario']

#%%
#separate into road, non road asnd everything else
road_model_input = transport_dataset.loc[transport_dataset['Medium'] == 'road']
non_road_model_input = transport_dataset.loc[transport_dataset['Medium'].isin(['air', 'rail', 'ship'])]#TODO remove nonspec from the model or at least decide wehat to do with it
growth_forecasts = transport_dataset.loc[~transport_dataset['Medium'].isin(['road', 'air', 'rail', 'ship'])]

#%%
# Make wide so each unique category of the measure col is a column with the values in the value col as the values. This is how we will use the data from now on.
#create INDEX_COLS with no measure
INDEX_COLS_NO_MEASURE = INDEX_COLS.copy()
INDEX_COLS_NO_MEASURE.remove('Measure')

#%%
# #check for duplicates when subset by INDEX_COLS_NO_MEASURE
# road_model_input[INDEX_COLS_NO_MEASURE].duplicated().sum()
# x = non_road_model_input[non_road_model_input[INDEX_COLS].duplicated(keep=False)]
#%%
road_model_input_wide = road_model_input.pivot(index=INDEX_COLS_NO_MEASURE, columns='Measure', values='Value').reset_index()
non_road_model_input_wide = non_road_model_input.pivot(index=INDEX_COLS_NO_MEASURE, columns='Measure', values='Value').reset_index()
growth_forecasts = growth_forecasts.pivot(index=INDEX_COLS_NO_MEASURE, columns='Measure', values='Value').reset_index()
################################################################################
#%%
#CALCUALTE TRAVEL KM 
road_model_input_wide['Travel_km'] = road_model_input_wide['Activity']/road_model_input_wide['Occupancy_or_load']#TRAVEL KM is not provided by transport data system atm

################################################################################
# #%%

#set surplus stocks to 0 for now
road_model_input_wide['Surplus_stocks'] = 0

# road_model_input_wide.loc[(road_model_input_wide['Vehicle_sales_share'].isna()), 'Vehicle_sales_share'] = 0#TO DO THIS SHOULD BE FIXED EARLIER IN THE PROCESS
################################################################################

#%%
#CREATE STOCKS FOR NON ROAD
#this is an adjsutment to the road stocks data from 8th edition by setting stocks to 1 for all non road vehicles that have a value >0 for Energy
non_road_model_input_wide.loc[(non_road_model_input_wide['Energy'] > 0), 'Stocks'] = 1
non_road_model_input_wide.loc[(non_road_model_input_wide['Energy'] == 0), 'Stocks'] = 0
#%%
# road_model_input_wide_new = road_model_input_wide[INDEX_COLS_NO_MEASURE + base_year_measures_list_ROAD + user_input_measures_list_ROAD + calculated_measures_ROAD]
# non_road_model_input_wide_new = non_road_model_input_wide[INDEX_COLS_NO_MEASURE + base_year_measures_list_NON_ROAD + user_input_measures_list_NON_ROAD + calculated_measures_NON_ROAD]

#%%
#save previous_year_main_dataframe as a temporary dataframe we can load in when we want to run the process below.
road_model_input_wide.to_csv('intermediate_data/model_inputs/road_model_input_wide.csv', index=False)
non_road_model_input_wide.to_csv('intermediate_data/model_inputs/non_road_model_input_wide.csv', index=False)
growth_forecasts.to_csv('intermediate_data/model_inputs/growth_forecasts.csv', index=False)
#%%

# %%
