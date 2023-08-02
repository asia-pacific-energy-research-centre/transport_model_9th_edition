#generally this will all work on the grouping of economy, year, v-type, drive, transport type, and scenario. There is a model simulation excel workbook in the documentation folder to more easily understand the operations here.

#NOTE that there is still the fuel mixing operation that is not in this file of code. 
#%%
###IMPORT GLOBAL VARIABLES FROM config.py
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
import sys
sys.path.append("./config")
import config

import pandas as pd 
import numpy as np
import yaml
import datetime
import shutil
import sys
import os 
import re
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go
import matplotlib
import matplotlib.pyplot as plt
from plotly.subplots import make_subplots
####Use this to load libraries and set variables. Feel free to edit that file as you need.
import road_model_functions
import logistic_fitting_functions
#%%
def run_road_model(ECONOMY_ID, USE_GOMPERTZ_ON_ONLY_PASSENGER_VEHICLES = False):
    
    #laod all data
    road_model_input = pd.read_csv('intermediate_data/model_inputs/{}/{}_road_model_input_wide.csv'.format(config.FILE_DATE_ID, ECONOMY_ID))
    growth_forecasts = pd.read_csv('intermediate_data/model_inputs/{}/{}_growth_forecasts_wide.csv'.format(config.FILE_DATE_ID, ECONOMY_ID))
        
    #grab from the paramters.yml file:
    vehicle_gompertz_factors = yaml.load(open('config/parameters.yml'), Loader=yaml.FullLoader)['vehicle_gompertz_factors']
    turnover_rate_parameters_dict = yaml.load(open('config/parameters.yml'), Loader=yaml.FullLoader)['turnover_rate_parameters_dict']
    
    main_dataframe,previous_year_main_dataframe, low_ram_computer_files_list, change_dataframe_aggregation, previous_10_year_block, user_inputs_df_dict,low_ram_computer = road_model_functions.prepare_road_model_inputs(road_model_input,ECONOMY_ID,low_ram_computer=False)
    
    #if you want to analyse what is hapening in th model then set this to true and the model will output a dataframe wioth all the variables that are being calculated.
    ANALYSE_CHANGE_DATAFRAME = True
    #######################################################################
    #RUN PROCESS
    #######################################################################
    # #breakpoint()
    #RUN MODEL TO GET RESULTS FOR EACH YEAR
    print('Running model up to year ' + str(road_model_input.Date.max()))
    for year in range(road_model_input.Date.min()+1, road_model_input.Date.max()+1):
        main_dataframe,previous_year_main_dataframe, low_ram_computer_files_list, change_dataframe_aggregation,previous_10_year_block = road_model_functions.run_road_model_for_year_y(year, previous_year_main_dataframe, main_dataframe, user_inputs_df_dict, growth_forecasts, change_dataframe_aggregation, low_ram_computer_files_list, low_ram_computer, ANALYSE_CHANGE_DATAFRAME, previous_10_year_block,turnover_rate_parameters_dict) 

    main_dataframe = road_model_functions.join_and_save_road_model_outputs(ECONOMY_ID, main_dataframe, low_ram_computer, low_ram_computer_files_list,ANALYSE_CHANGE_DATAFRAME,change_dataframe_aggregation, first_model_run_bool=True)

    #######################################################################
    #CLEAN DATA FOR NEXT RUN
    #######################################################################
    
    #PUT RESULTS THROUGH logistic_fitting_function_handler AND FIND NEW PARAMETERS TO AVOID OVERG
    # ROWTH OF PASSENGER and perhaps freight VEHICLE STOCKS
    main_dataframe = main_dataframe.merge(user_inputs_df_dict['gompertz_parameters'][['Economy','Date', 'Scenario', 'Gompertz_gamma']].drop_duplicates(), on=['Economy','Date','Scenario'], how='left')
    activity_growth_estimates, parameters_estimates = logistic_fitting_functions.logistic_fitting_function_handler(main_dataframe,show_plots=False,matplotlib_bool=False, plotly_bool=True, ONLY_PASSENGER_VEHICLES=USE_GOMPERTZ_ON_ONLY_PASSENGER_VEHICLES,vehicle_gompertz_factors = vehicle_gompertz_factors)
    
    growth_forecasts = incorporate_logisitc_fitting_functions_new_growth_rates(growth_forecasts, activity_growth_estimates)
    growth_forecasts.to_pickle(f'./intermediate_data/road_model/{ECONOMY_ID}_final_road_growth_forecasts.pkl')#save them sincewe will use them for non road
    
    #######################################################################
    main_dataframe,previous_year_main_dataframe, low_ram_computer_files_list, change_dataframe_aggregation,previous_10_year_block, user_inputs_df_dict,low_ram_computer = road_model_functions.prepare_road_model_inputs(road_model_input,ECONOMY_ID,low_ram_computer=False)
    #######################################################################
    #RUN MODEL AGAIN
    ####################################################################### 
    print('Running model up to year ' + str(road_model_input.Date.max()))
    #run model again with new growth rates for passenger vehicles (so replace growth_forecasts with activity_growth_estimates)
    for year in range(road_model_input.Date.min()+1, road_model_input.Date.max()+1):
        main_dataframe,previous_year_main_dataframe, low_ram_computer_files_list, change_dataframe_aggregation, previous_10_year_block = road_model_functions.run_road_model_for_year_y(year, previous_year_main_dataframe, main_dataframe, user_inputs_df_dict, growth_forecasts, change_dataframe_aggregation, low_ram_computer_files_list, low_ram_computer, ANALYSE_CHANGE_DATAFRAME, previous_10_year_block, turnover_rate_parameters_dict)
    #######################################################################

    #finalisation processes. save results and create diagnostics plots

    #######################################################################

    #save as csv for next step
    main_dataframe = road_model_functions.join_and_save_road_model_outputs(ECONOMY_ID, main_dataframe, low_ram_computer, low_ram_computer_files_list,ANALYSE_CHANGE_DATAFRAME,change_dataframe_aggregation, first_model_run_bool=False)

def incorporate_logisitc_fitting_functions_new_growth_rates(growth_forecasts, activity_growth_estimates):
    
    #note that activity_growth_estimates will contain new growth rates for only some econmies where their stocks per cpita passed their threshold. For the others, the growth rates will be the same as they were previously.
    #so do a merge and only keep the new growth rates for the economies that have them
    new_growth_forecasts = growth_forecasts.copy()
    similar_cols = [col for col in growth_forecasts.columns if col in activity_growth_estimates.columns]
    config.INDEX_COLS = ['Economy', 'Scenario', 'Date', 'Transport Type']
    new_growth_forecasts = new_growth_forecasts.merge(activity_growth_estimates.drop_duplicates(), on=config.INDEX_COLS, how='left', suffixes=('', '_new'))
    #######################################################################
    CLEAN_UP_GROWTH = False
    if CLEAN_UP_GROWTH:
        new_growth_forecasts = logistic_fitting_functions.average_out_growth_rate_using_cagr(new_growth_forecasts, economies_to_avg_growth_over_all_years_in_freight_for = ['19_THA'])
        USE_FREIGHT_GROWTH_FOR_PASSENGER = False
        if USE_FREIGHT_GROWTH_FOR_PASSENGER:
            #also, since we have currently estomated growth to be too high, set passneger transport growth to be the sae as the new freight growth
            new_growth_forecasts_passenger = new_growth_forecasts.loc[new_growth_forecasts['Transport Type']=='freight'].copy()
            new_growth_forecasts_passenger['Transport Type'] = 'passenger'
            new_growth_forecasts =new_growth_forecasts.loc[new_growth_forecasts['Transport Type']!='passenger'].copy()
            new_growth_forecasts = pd.concat([new_growth_forecasts, new_growth_forecasts_passenger])
    #######################################################################
    #now where there is a new growth rate, use that, otherwise use the old one
    new_growth_forecasts['Activity_growth'] = new_growth_forecasts['Activity_growth_new'].fillna(new_growth_forecasts['Activity_growth'])
    #drop the cols with _new suffix
    new_growth_forecasts = new_growth_forecasts[[col for col in new_growth_forecasts.columns if not col.endswith('_new')]]
    
    #now srt growth_forecasts to new_growth_forecasts
    growth_forecasts = new_growth_forecasts.copy()
    
    return growth_forecasts