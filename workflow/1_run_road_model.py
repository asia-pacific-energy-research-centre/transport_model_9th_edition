#generally this will all work on the grouping of economy, year, v-type, drive, transport type, and scenario. There is a model simulation excel workbook in the documentation folder to more easily understand the operations here.

#NOTE that there is still the fuel mixing operation that is not in this file of code. 
#%%
#set working directory as one folder back so that config works
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
from runpy import run_path
import numpy as np
from scipy.optimize import newton
exec(open("config/config.py").read())#usae this to load libraries and set variables. Feel free to edit that file as you need
import functions
#%%
#laod all data
road_model_input = pd.read_csv('intermediate_data/model_inputs/road_model_input_wide.csv')

growth_forecasts = pd.read_csv('intermediate_data/model_inputs/growth_forecasts.csv')
#%%
main_dataframe,previous_year_main_dataframe, low_ram_computer_files_list, change_dataframe_aggregation, gompertz_function_diagnostics_dataframe,previous_10_year_block, user_inputs_df_dict,low_ram_computer = functions.prepare_road_model_inputs(road_model_input,low_ram_computer=True)
#%%
#if you want to analyse what is hapening in th model then set this to true and the model will output a dataframe wioth all the variables that are being calculated.
ANALYSE_CHANGE_DATAFRAME = True
#######################################################################
#RUN PROCESS
#######################################################################
run_this = False#set to false if you want to skip this step and just load the results from pickle.
if run_this:
    #RUN MODEL TO GET RESULTS FOR EACH YEAR
    for year in range(BASE_YEAR+1, END_YEAR+1):
        main_dataframe,previous_year_main_dataframe, low_ram_computer_files_list, change_dataframe_aggregation, gompertz_function_diagnostics_dataframe,previous_10_year_block = functions.run_road_model_for_year_y(year, previous_year_main_dataframe, main_dataframe, user_inputs_df_dict, growth_forecasts, change_dataframe_aggregation, gompertz_function_diagnostics_dataframe, low_ram_computer_files_list, low_ram_computer, ANALYSE_CHANGE_DATAFRAME, previous_10_year_block)

    main_dataframe = functions.join_and_save_road_model_outputs(main_dataframe, low_ram_computer, low_ram_computer_files_list,ANALYSE_CHANGE_DATAFRAME,change_dataframe_aggregation, gompertz_function_diagnostics_dataframe)

    #save results as pickle for testing purposes
    main_dataframe.to_pickle('./intermediate_data/road_model/main_dataframe.pkl')
else:
    main_dataframe = pd.read_pickle('./intermediate_data/road_model/main_dataframe.pkl')

#######################################################################
#CLEAN DATA FOR NEXT RUN
#######################################################################
#%%
#join on the gompertz gamma and , 'Gdp_per_capita', 'Population' cols from growth_forecasts and gompertz_parameters. THis is because they werent calculated in the model, but are needed as inputs for the next steps
main_dataframe = main_dataframe.merge(growth_forecasts[['Economy','Date','Gdp_per_capita', 'Population']].drop_duplicates(), on=['Economy','Date'], how='left')
main_dataframe = main_dataframe.merge(user_inputs_df_dict['gompertz_parameters'][['Economy','Date', 'Scenario','Vehicle Type', 'Gompertz_gamma']].drop_duplicates(), on=['Economy','Date','Scenario','Vehicle Type'], how='left')

#%%
#PUT RESULTS THROUGH logistic_fitting_function_handler AND FIND NEW PARAMETERS TO AVOID OVERGROWTH OF PASSENGER VEHICLE STOCKS
#set gompertz gamma to 800 for all economies just to test.
main_dataframe['Gompertz_gamma'] = 800
activity_growth_estimates, parameters_estimates = functions.logistic_fitting_function_handler(main_dataframe,show_plots=False,matplotlib_bool=False, plotly_bool=True)
#set transport type to passenger for all rows
activity_growth_estimates['Transport Type'] = 'passenger'

#join all cols in growth_forecasts onto activity_growth_estimates that arent already there. this is because they werent calculated in the model, but might be needed as inputs for the next run of the model
cols_in_growth_forecasts_not_in_activity_growth_estimates = [col for col in growth_forecasts.columns if col not in activity_growth_estimates.columns]
index_cols = [col for col in INDEX_COLS if col in activity_growth_estimates.columns]
activity_growth_estimates = activity_growth_estimates.merge(growth_forecasts[cols_in_growth_forecasts_not_in_activity_growth_estimates+index_cols].drop_duplicates(), on=index_cols, how='left')

#now srt growth_forecasts to activity_growth_estimates
growth_forecasts = activity_growth_estimates.copy()

#%%
main_dataframe,previous_year_main_dataframe, low_ram_computer_files_list, change_dataframe_aggregation, gompertz_function_diagnostics_dataframe,previous_10_year_block, user_inputs_df_dict,low_ram_computer = functions.prepare_road_model_inputs(road_model_input,low_ram_computer=True)
#######################################################################
#RUN MODEL AGAIN
#######################################################################
#%%
#run model again with new growth rates for passenger vehicles (so replace growth_forecasts with activity_growth_estimates)
for year in range(BASE_YEAR+1, END_YEAR+1):
    main_dataframe,previous_year_main_dataframe, low_ram_computer_files_list, change_dataframe_aggregation, gompertz_function_diagnostics_dataframe,previous_10_year_block = functions.run_road_model_for_year_y(year, previous_year_main_dataframe, main_dataframe, user_inputs_df_dict, growth_forecasts, change_dataframe_aggregation, gompertz_function_diagnostics_dataframe, low_ram_computer_files_list, low_ram_computer, ANALYSE_CHANGE_DATAFRAME, previous_10_year_block)

#%%
#######################################################################

#finalisation processes. save results and create diagnostics plots

#######################################################################

#save parameters_estimates as pickle for testing purposes
parameters_estimates.to_pickle('./intermediate_data/road_model/parameters_estimates.pkl')

#save as csv for next step
main_dataframe = functions.join_and_save_road_model_outputs(main_dataframe, low_ram_computer, low_ram_computer_files_list,ANALYSE_CHANGE_DATAFRAME,change_dataframe_aggregation, gompertz_function_diagnostics_dataframe)

#save results as pickle for testing purposes
main_dataframe.to_pickle('./intermediate_data/road_model/main_dataframe_growth_adjusted.pkl')
#%%
#######################################################################
#######################################################################




# %%
