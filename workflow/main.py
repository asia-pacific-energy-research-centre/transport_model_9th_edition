
#%%
###IMPORT GLOBAL VARIABLES FROM config.py
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
import sys
sys.path.append("./config")
import config
###
#PREPARATION FUNCTIONS
sys.path.append("./workflow/preparation_functions")
import concordance_scripts
import import_macro_data
import import_transport_system_data
import create_and_clean_user_input
import aggregate_data_for_model
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
#FORMATTING FUNCTIONS
sys.path.append("./workflow/formatting_functions")
import concatenate_model_output
import clean_model_output
import create_output_for_outlook_data_system
#PLOTTING FUNCTIONS
sys.path.append("./workflow/plotting_functions")
import all_economy_graphs
import produce_LMDI_graphs
import plot_charging_graphs
import create_assumptions_dashboards
import calculate_and_plot_oil_displacement
import compare_esto_energy_to_data
PLOT_INPUT_DATA = False
CREATE_MODEL_CONCORDANCES = True

#%%
def main():
    
    #Things to do once a day:
    do_these_once_a_day = False
    if do_these_once_a_day:
        if CREATE_MODEL_CONCORDANCES:
            concordance_scripts.create_all_concordances()
            
    PREPARE_DATA = False
    if PREPARE_DATA:
        import_macro_data.import_macro_data()
        create_and_clean_user_input.create_and_clean_user_input()
        import_transport_system_data.import_transport_system_data()
        

        
    MODEL_RUN_1  = True
    if MODEL_RUN_1:
        #MODEL RUN 1: (RUN MODEL FOR DATA BETWEEN AND INCLUDIONG BASE YEAR AND config.OUTLOOK_BASE_YEAR))
        PROJECT_TO_JUST_OUTLOOK_BASE_YEAR = True
        ADVANCE_BASE_YEAR = False
        #aggregate and perform final filtering of data (eg for one economy only)
        aggregate_data_for_model.aggregate_data_for_model(PROJECT_TO_JUST_OUTLOOK_BASE_YEAR = PROJECT_TO_JUST_OUTLOOK_BASE_YEAR)
        
        calculate_inputs_for_model.calculate_inputs_for_model(config.INDEX_COLS,RECALCULATE_ENERGY_USING_ESTO_AND_PREVIOUS_MODEL_RUN=False,ADVANCE_BASE_YEAR=False)

        run_road_model.run_road_model(PROJECT_TO_JUST_OUTLOOK_BASE_YEAR=PROJECT_TO_JUST_OUTLOOK_BASE_YEAR, USE_GOMPERTZ_ON_ONLY_PASSENGER_VEHICLES = False)
        run_non_road_model.run_non_road_model(config.OUTLOOK_BASE_YEAR,config.END_YEAR,config.BASE_YEAR, PROJECT_TO_JUST_OUTLOOK_BASE_YEAR=PROJECT_TO_JUST_OUTLOOK_BASE_YEAR)
        concatenate_model_output.concatenate_model_output()

        apply_fuel_mix_demand_side.apply_fuel_mix_demand_side(PROJECT_TO_JUST_OUTLOOK_BASE_YEAR=PROJECT_TO_JUST_OUTLOOK_BASE_YEAR)
        apply_fuel_mix_supply_side.apply_fuel_mix_supply_side(PROJECT_TO_JUST_OUTLOOK_BASE_YEAR=PROJECT_TO_JUST_OUTLOOK_BASE_YEAR)
        clean_model_output.clean_model_output()
        
        PLOT_FIRST_MODEL_RUN = True
        if PLOT_FIRST_MODEL_RUN:            
            produce_LMDI_graphs.produce_lots_of_LMDI_charts(USE_LIST_OF_CHARTS_TO_PRODUCE = True, PLOTTING = False, USE_LIST_FOR_DATASETS_TO_PRODUCE=True)
            create_assumptions_dashboards.dashboard_creation_handler(ADVANCE_BASE_YEAR=ADVANCE_BASE_YEAR)
            
            # compare_esto_energy_to_data.compare_esto_energy_to_data()#UNDER DEVELOPMENT

    MODEL_RUN_2  = True
    if MODEL_RUN_2:
        #MODEL RUN 1: (RUN MODEL FOR DATA BETWEEN  AND INCLUDIONG BASE YEAR AND config.OUTLOOK_BASE_YEAR)
        
        ADVANCE_BASE_YEAR = True
        #aggregate and perform final filtering of data (eg for one economy only)
        aggregate_data_for_model.aggregate_data_for_model(ADVANCE_BASE_YEAR = ADVANCE_BASE_YEAR)
        # exec(open("./workflow/grooming_code/4_calculate_inputs_for_model.py").read())
        calculate_inputs_for_model.calculate_inputs_for_model(config.INDEX_COLS,RECALCULATE_ENERGY_USING_ESTO_AND_PREVIOUS_MODEL_RUN=True,ADVANCE_BASE_YEAR=ADVANCE_BASE_YEAR)
        run_road_model.run_road_model(ADVANCE_BASE_YEAR=ADVANCE_BASE_YEAR,USE_GOMPERTZ_ON_ONLY_PASSENGER_VEHICLES = False)
        run_non_road_model.run_non_road_model(config.OUTLOOK_BASE_YEAR,config.END_YEAR,config.BASE_YEAR, ADVANCE_BASE_YEAR=ADVANCE_BASE_YEAR)
        concatenate_model_output.concatenate_model_output(ADVANCE_BASE_YEAR=ADVANCE_BASE_YEAR)
        apply_fuel_mix_demand_side.apply_fuel_mix_demand_side()
        apply_fuel_mix_supply_side.apply_fuel_mix_supply_side(ADVANCE_BASE_YEAR=ADVANCE_BASE_YEAR)
        clean_model_output.clean_model_output()
        
    create_output_for_outlook_data_system.create_output_for_outlook_data_system()
    estimate_charging_requirements.estimate_kw_of_required_chargers()

    # exec(open("./workflow/6_create_osemosys_output.py").read())
    # import create_osemosys_output
    # create_osemosys_output.create_osemosys_output()
    
    ANALYSE_OUTPUT = True
    if ANALYSE_OUTPUT:
        plot_charging_graphs.plot_required_chargers()
        calculate_and_plot_oil_displacement.calculate_and_plot_oil_displacement()        
        produce_LMDI_graphs.produce_lots_of_LMDI_charts(USE_LIST_OF_CHARTS_TO_PRODUCE = True, PLOTTING = False, USE_LIST_FOR_DATASETS_TO_PRODUCE=True)
        create_assumptions_dashboards.dashboard_creation_handler()
        compare_esto_energy_to_data.compare_esto_energy_to_data()#UNDER DEVELOPMENT   
    
    utility_functions.copy_required_output_files_to_one_folder(config.FILE_DATE_ID, config.ECONOMIES_TO_PLOT_FOR, config.SCENARIOS_LIST,output_folder_path='output_data/for_other_modellers')

    
    ARCHIVE_INPUT_DATA = True
    if ARCHIVE_INPUT_DATA:
        #set up archive folder:
        archiving_folder = archiving_scripts.create_archiving_folder_for_FILE_DATE_ID(config.FILE_DATE_ID)
        archiving_scripts.archive_lots_of_files(archiving_folder)

    #do this last because it takes so long, so make sure thaht everything else is working first
    plot_all_economy_graphs = False
    if plot_all_economy_graphs:
        #plot:
        all_economy_graphs.all_economy_graphs_massive_unwieldy_function(PLOT=True)
        produce_LMDI_graphs.produce_lots_of_LMDI_charts(USE_LIST_OF_CHARTS_TO_PRODUCE = True, PLOTTING = True, USE_LIST_FOR_DATASETS_TO_PRODUCE=True)
        # exec(open("./workflow/plotting/produce_LMDI_graphs.py").read())
#%%
main()
#%%