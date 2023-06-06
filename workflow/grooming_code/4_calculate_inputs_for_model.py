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
import gompertz_parameters_estimation_function
import logistic_parameters_estimation_function
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
#do estiamtion of the parameters for gomperz curve for the road stocks:
#separate gompertz inputs
gompertz_parameters = road_model_input_wide[['Economy','Scenario','Date', 'Transport Type'] + [col for col in road_model_input_wide.columns if 'Gompertz_' in col]].drop_duplicates().dropna()
road_model_data = road_model_input_wide[['Date', 'Economy', 'Vehicle Type', 'Medium', 'Transport Type', 'Drive', 'Scenario','Stocks']].drop_duplicates()
macro_data = growth_forecasts[['Date','Scenario', 'Economy', 'Gdp_per_capita','Population']].drop_duplicates()
#join the two datasets on Date and economy
road_model_data = road_model_data.merge(macro_data, on=['Date', 'Scenario','Economy'], how='left')
road_model_data = road_model_data.merge(gompertz_parameters, on=['Date', 'Economy', 'Scenario', 'Transport Type'], how='left')
save_to_pickle = True
if save_to_pickle:
    road_model_data.to_pickle('intermediate_data/archive/road_model_data_{}.pkl'.format(FILE_DATE_ID))
#%%
estimate_gompertz_parameters = False
if estimate_gompertz_parameters:
    if USE_LOGISTIC_FUNCTION:
        gompertz_parameters = logistic_parameters_estimation_function.logistic_fitting_function_handler(road_model_data, BASE_YEAR = 2020,future_dates=[2045, 2050], future_dates_prop_diff_from_gamma=[0.1, 0.09], INTERPOLATE_DATA = True,show_plots=False,matplotlib_bool=True, plotly_bool=False)
    else:
        #now attempt estimation 
        gompertz_parameters = gompertz_parameters_estimation_function.gompertz_fitting_function_handler(road_model_data,BASE_YEAR+3,future_dates=[2045, 2050], future_dates_prop_diff_from_gamma=[0.1, 0.09], INTERPOLATE_DATA = True, show_plots=False,matplotlib_bool=True, plotly_bool=False)

    gompertz_parameters['Transport Type'] = 'passenger'

    #save params to pickle
    gompertz_parameters.to_pickle('intermediate_data/archive/gompertz_parameters_TEST.pkl')
    #drop the gompertz parameters from the main dataset
    road_model_input_wide.drop([col for col in road_model_input_wide.columns if 'Gompertz_' in col], axis=1, inplace=True)
    #join the gompertz parameters back to the main dataset
    road_model_input_wide = road_model_input_wide.merge(gompertz_parameters, on=['Economy', 'Scenario', 'Transport Type', 'Vehicle Type'], how='left')
else:
    #maybe we ont use these so jsut load some old ones and join them to the main dataset
    gompertz_parameters = pd.read_pickle('intermediate_data/archive/gompertz_parameters_TEST.pkl')
    #drop the gompertz parameters from the main dataset
    road_model_input_wide.drop([col for col in road_model_input_wide.columns if 'Gompertz_' in col], axis=1, inplace=True)
    #join the gompertz parameters back to the main dataset
    road_model_input_wide = road_model_input_wide.merge(gompertz_parameters, on=['Economy', 'Scenario', 'Transport Type', 'Vehicle Type'], how='left')

#%%

# #join population and gdp per cpita to road model input
# gdp_cap = growth_forecasts[['Date', 'Economy', 'Transport Type', 'Population', 'Gdp_per_capita']].drop_duplicates()

# road_model_input_wide =  pd.merge(road_model_input_wide, gdp_cap, how='left', on=['Date', 'Transport Type', 'Economy'])

#%%
#save previous_year_main_dataframe as a temporary dataframe we can load in when we want to run the process below.
road_model_input_wide.to_csv('intermediate_data/model_inputs/road_model_input_wide.csv', index=False)
non_road_model_input_wide.to_csv('intermediate_data/model_inputs/non_road_model_input_wide.csv', index=False)
growth_forecasts.to_csv('intermediate_data/model_inputs/growth_forecasts.csv', index=False)
#%%

# %%
