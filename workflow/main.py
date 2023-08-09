
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
###
#PREPARATION FUNCTIONS
sys.path.append("./workflow/preparation_functions")
import concordance_scripts
import import_macro_data
import import_transport_system_data
import create_and_clean_user_input
import aggregate_data_for_model
import filter_for_economy_and_modelling_years
#UTILITY FUNCTIONS
sys.path.append("./workflow/utility_functions")
import utility_functions
#CALCUALTION FUNCTIONS
sys.path.append("./workflow/calculation_functions")
import calculate_inputs_for_model
import run_road_model
import run_non_road_model
import apply_fuel_mix_demand_side
import apply_fuel_mix_supply_side
import estimate_charging_requirements
import international_bunkers
#FORMATTING FUNCTIONS
sys.path.append("./workflow/formatting_functions")
import concatenate_model_output
import clean_model_output
import create_output_for_outlook_data_system
#PLOTTING FUNCTIONS
sys.path.append("./workflow/plotting_functions")
import plot_all_graphs
import produce_LMDI_graphs
import plot_charging_graphs
import create_assumptions_dashboards
import calculate_and_plot_oil_displacement
import compare_esto_energy_to_data

#%%
def main():
    #Things to do once a day:
    do_these_once_a_day = False
    if do_these_once_a_day:
        concordance_scripts.create_all_concordances()
    
    PREPARE_DATA = False
    if PREPARE_DATA:
        import_macro_data.import_macro_data()
        import_transport_system_data.import_transport_system_data()
        create_and_clean_user_input.create_and_clean_user_input()
        aggregate_data_for_model.aggregate_data_for_model()
        
    #######################################################################
    #since we're going to find that some economies have better base years than 2017 to start with, lets start changing the Base year vlaue and run the model economy by economy:
    ECONOMY_BASE_YEARS_DICT = yaml.load(open('config/parameters.yml'), Loader=yaml.FullLoader)['ECONOMY_BASE_YEARS_DICT']
    ECONOMIES_TO_USE_ROAD_ACTIVITY_GROWTH_RATES_FOR_NON_ROAD_dict = yaml.load(open('config/parameters.yml'), Loader=yaml.FullLoader)['ECONOMIES_TO_USE_ROAD_ACTIVITY_GROWTH_RATES_FOR_NON_ROAD']
    
    #######################################################################
    for economy in ECONOMY_BASE_YEARS_DICT.keys():
        if economy not in ['19_THA', '20_USA', '08_JPN']:
            continue
        
        #     # breakpoint()
        # # else:
        #     continue
            
        #     pass
        # else:
        #     continue
            
        print('\nRunning model for {}\n'.format(economy))
        ECONOMY_ID = economy
        BASE_YEAR = ECONOMY_BASE_YEARS_DICT[economy]
        MODEL_RUN_1  = True
        if MODEL_RUN_1:              
            #MODEL RUN 1: (RUN MODEL FOR DATA BETWEEN AND INCLUDIONG BASE YEAR AND config.OUTLOOK_BASE_YEAR))
            PROJECT_TO_JUST_OUTLOOK_BASE_YEAR = True
            ADVANCE_BASE_YEAR = False
            #perform final filtering of data (eg for one economy only)
            
            supply_side_fuel_mixing, demand_side_fuel_mixing, road_model_input_wide, non_road_model_input_wide, growth_forecasts_wide = filter_for_economy_and_modelling_years.filter_for_economy_and_modelling_years(BASE_YEAR, ECONOMY_ID, PROJECT_TO_JUST_OUTLOOK_BASE_YEAR=PROJECT_TO_JUST_OUTLOOK_BASE_YEAR,ADVANCE_BASE_YEAR=ADVANCE_BASE_YEAR)
            calculate_inputs_for_model.calculate_inputs_for_model(road_model_input_wide,non_road_model_input_wide,growth_forecasts_wide, supply_side_fuel_mixing, demand_side_fuel_mixing, ECONOMY_ID, BASE_YEAR, ADVANCE_BASE_YEAR=ADVANCE_BASE_YEAR, adjust_data_to_match_esto_TESTING=False)
            if BASE_YEAR == config.OUTLOOK_BASE_YEAR:
                #since we wont run the model, just fill the input with requried output cols and put nans in them
                concatenate_model_output.fill_missing_output_cols_with_nans(ECONOMY_ID, road_model_input_wide, non_road_model_input_wide)
            else:
                run_road_model.run_road_model(ECONOMY_ID, USE_GOMPERTZ_ON_ONLY_PASSENGER_VEHICLES = False)
                run_non_road_model.run_non_road_model(ECONOMY_ID, USE_ROAD_ACTIVITY_GROWTH_RATES_FOR_NON_ROAD = ECONOMIES_TO_USE_ROAD_ACTIVITY_GROWTH_RATES_FOR_NON_ROAD_dict[ECONOMY_ID])
                
            model_output_all = concatenate_model_output.concatenate_model_output(ECONOMY_ID)

            model_output_with_fuel_mixing = apply_fuel_mix_demand_side.apply_fuel_mix_demand_side(model_output_all,ECONOMY_ID=ECONOMY_ID)
            model_output_with_fuel_mixing = apply_fuel_mix_supply_side.apply_fuel_mix_supply_side(model_output_with_fuel_mixing,ECONOMY_ID=ECONOMY_ID)
            clean_model_output.clean_model_output(ECONOMY_ID, model_output_with_fuel_mixing, model_output_all)
            
            PLOT_FIRST_MODEL_RUN = False
            ARCHIVE_PREVIOUS_DASHBOARDS = True
            if PLOT_FIRST_MODEL_RUN:       
                #its easier to run all these rather than skipping some out for now
                estimate_charging_requirements.estimate_kw_of_required_chargers(ECONOMY_ID)
                plot_charging_graphs.plot_required_chargers(ECONOMY_ID)
                calculate_and_plot_oil_displacement.calculate_and_plot_oil_displacement(ECONOMY_ID)     
                produce_LMDI_graphs.produce_lots_of_LMDI_charts(ECONOMY_ID, USE_LIST_OF_CHARTS_TO_PRODUCE = True, PLOTTING = False, USE_LIST_FOR_DATASETS_TO_PRODUCE=True)
                create_assumptions_dashboards.dashboard_creation_handler(ADVANCE_BASE_YEAR,ECONOMY_ID,ARCHIVE_PREVIOUS_DASHBOARDS=ARCHIVE_PREVIOUS_DASHBOARDS)
                
                # compare_esto_energy_to_data.compare_esto_energy_to_data()#UNDER DEVELOPMENT
        MODEL_RUN_2  = True
        if MODEL_RUN_2:
            #MODEL RUN 1: (RUN MODEL FOR DATA BETWEEN  AND INCLUDIONG BASE YEAR AND config.OUTLOOK_BASE_YEAR)
            PROJECT_TO_JUST_OUTLOOK_BASE_YEAR = False
            ADVANCE_BASE_YEAR = True
            #perform final filtering of data (eg for one economy only)
            supply_side_fuel_mixing, demand_side_fuel_mixing, road_model_input_wide, non_road_model_input_wide, growth_forecasts_wide = filter_for_economy_and_modelling_years.filter_for_economy_and_modelling_years(BASE_YEAR, ECONOMY_ID, PROJECT_TO_JUST_OUTLOOK_BASE_YEAR=PROJECT_TO_JUST_OUTLOOK_BASE_YEAR,ADVANCE_BASE_YEAR=ADVANCE_BASE_YEAR)
            
            calculate_inputs_for_model.calculate_inputs_for_model(road_model_input_wide,non_road_model_input_wide,growth_forecasts_wide, supply_side_fuel_mixing, demand_side_fuel_mixing, ECONOMY_ID, BASE_YEAR, ADVANCE_BASE_YEAR=ADVANCE_BASE_YEAR, adjust_data_to_match_esto_TESTING=False)
            
            run_road_model.run_road_model(ECONOMY_ID, USE_GOMPERTZ_ON_ONLY_PASSENGER_VEHICLES = False)
            
            run_non_road_model.run_non_road_model(ECONOMY_ID,USE_ROAD_ACTIVITY_GROWTH_RATES_FOR_NON_ROAD=ECONOMIES_TO_USE_ROAD_ACTIVITY_GROWTH_RATES_FOR_NON_ROAD_dict[ECONOMY_ID])
            model_output_all = concatenate_model_output.concatenate_model_output(ECONOMY_ID)

            model_output_with_fuel_mixing = apply_fuel_mix_demand_side.apply_fuel_mix_demand_side(model_output_all,ECONOMY_ID=ECONOMY_ID)
            model_output_with_fuel_mixing = apply_fuel_mix_supply_side.apply_fuel_mix_supply_side(model_output_with_fuel_mixing,ECONOMY_ID=ECONOMY_ID)
            clean_model_output.clean_model_output(ECONOMY_ID, model_output_with_fuel_mixing, model_output_all)
                
            #now concatenate all the model outputs together
            
            create_output_for_outlook_data_system.create_output_for_outlook_data_system(ECONOMY_ID)

            # exec(open("./workflow/6_create_osemosys_output.py").read())
            # import create_osemosys_output
            # create_osemosys_output.create_osemosys_output()
            # ADVANCE_BASE_YEAR=True
            ANALYSE_OUTPUT = True
            ARCHIVE_PREVIOUS_DASHBOARDS = True
            if ANALYSE_OUTPUT: 
                estimate_charging_requirements.estimate_kw_of_required_chargers(ECONOMY_ID)
                plot_charging_graphs.plot_required_chargers(ECONOMY_ID)
                calculate_and_plot_oil_displacement.calculate_and_plot_oil_displacement(ECONOMY_ID)       
                produce_LMDI_graphs.produce_lots_of_LMDI_charts(ECONOMY_ID, USE_LIST_OF_CHARTS_TO_PRODUCE = True, PLOTTING = False, USE_LIST_FOR_DATASETS_TO_PRODUCE=True)
                create_assumptions_dashboards.dashboard_creation_handler(ADVANCE_BASE_YEAR, ECONOMY_ID, ARCHIVE_PREVIOUS_DASHBOARDS=ARCHIVE_PREVIOUS_DASHBOARDS)
                # compare_esto_energy_to_data.compare_esto_energy_to_data()#UNDER DEVELOPMENT   
        
    # international_bunkers.international_bunker_share_calculation_handler()
    
    create_output_for_outlook_data_system.concatenate_outlook_data_system_outputs()
    
    clean_model_output.concatenate_output_data()

    utility_functions.copy_required_output_files_to_one_folder(output_folder_path='output_data/for_other_modellers')
    # ARCHIVE_INPUT_DATA = False
    # if ARCHIVE_INPUT_DATA:
    #     #set up archive folder:
    #     archiving_folder = archiving_scripts.create_archiving_folder_for_FILE_DATE_ID()
    #     archiving_scripts.archive_lots_of_files(archiving_folder)

    # #do this last because it takes so long, so make sure thaht everything else is working first
    run_plot_all_graphs = False
    if run_plot_all_graphs:
        #plot:
        breakpoint()
        try:
            plot_all_graphs.plot_all_graphs(PLOT=True, plot_comparisons=True)
        except:
            breakpoint()
            plot_all_graphs.plot_all_graphs(PLOT=True, plot_comparisons=True)
        # produce_LMDI_graphs.produce_lots_of_LMDI_charts(USE_LIST_OF_CHARTS_TO_PRODUCE = True, PLOTTING = True, USE_LIST_FOR_DATASETS_TO_PRODUCE=True)
        # exec(open("./workflow/plotting/produce_LMDI_graphs.py").read())
#%%
main()#python workflow/main.py > output.txt 2>&1
#%%