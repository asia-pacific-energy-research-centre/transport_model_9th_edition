

"""Integration is the act of bringing together smaller components into a single system that functions as one. In an IT context, integration refers to the end result of a process that aims to stitch 
together different, often disparate, subsystems so that the data contained in each becomes part of a larger, more comprehensive system that, ideally, quickly and easily shares data when needed. This 
often requires that companies build a customized architecture or structure of applications to combine new or existing hardware, software and other communications."""
# this file will manage all the modules in the transport system. This is so that each module can be easily run in sequence, as well as passing common variables to each 
#%%
import datetime
import sys
#set global variables
sys.path.append("./workflow/grooming_code")
sys.path.append("./workflow")
sys.path.append("./config/utilities")
sys.path.append("./workflow/plotting")
file_date_dummy = datetime.datetime.now().strftime("%Y%m%d")
FILE_DATE_ID_dummy = '_{}'.format(file_date_dummy)#Note that this is not the official file date id anymore because it was interacting badly with how we should instead set it in onfig.py

exec(open("config/config.py").read())#usae this to load libraries and set variables. Feel free to edit that file as you need

# FILE_DATE_ID = ''#comment me out if you want the output and archived input data to be saved with a specific date id 
print('Model run for {} starting'.format(file_date_dummy))
print('\n FILE_DATE_ID is set to {}'.format(FILE_DATE_ID_dummy))

PLOT_INPUT_DATA = False
CREATE_MODEL_CONCORDANCES = True
#set up archive folder:
import archiving_scripts
archiving_folder = archiving_scripts.create_archiving_folder_for_FILE_DATE_ID(FILE_DATE_ID)

#%%
if CREATE_MODEL_CONCORDANCES:
    import concordance_scripts
    concordance_scripts.create_all_concordances()
#%%
PREPARE_DATA = True
if PREPARE_DATA:
    # exec(open("./workflow/grooming_code/1_import_macro_data.py").read())
    import import_macro_data
    import_macro_data.import_macro_data()

    # exec(open("./workflow/grooming_code/1_import_transport_system_data.py").read())
    import import_transport_system_data
    import_transport_system_data.import_transport_system_data()

    
    import create_and_clean_user_input
    create_and_clean_user_input.create_and_clean_user_input()
    
    # exec(open("./workflow/grooming_code/2_aggregate_data_for_model.py").read())
    import aggregate_data_for_model
    aggregate_data_for_model.aggregate_data_for_model()

    if PLOT_INPUT_DATA:
        # exec(open("./workflow/grooming_code/3_communicate_missing_input_data.py").read())
        import communicate_missing_input_data
        communicate_missing_input_data.communicate_missing_input_data()
    
    # exec(open("./workflow/grooming_code/4_calculate_inputs_for_model.py").read())
    import calculate_inputs_for_model
    calculate_inputs_for_model.calculate_inputs_for_model(INDEX_COLS)

#%%

# exec(open("./workflow/1_run_road_model.py").read())
import run_road_model
run_road_model.run_road_model()
# exec(open("./workflow/1_run_non_road_model.py").read())
import run_non_road_model
run_non_road_model.run_non_road_model()
# exec(open("./workflow/2_concatenate_model_output.py").read())
import concatenate_model_output
concatenate_model_output.concatenate_model_output()
# exec(open("./workflow/3_apply_fuel_mix_demand_side.py").read())
#%%
import apply_fuel_mix_demand_side
apply_fuel_mix_demand_side.apply_fuel_mix_demand_side()
# exec(open("./workflow/4_apply_fuel_mix_supply_side.py").read())
import apply_fuel_mix_supply_side
apply_fuel_mix_supply_side.apply_fuel_mix_supply_side()
# exec(open("./workflow/5_clean_model_output.py").read())
import clean_model_output
clean_model_output.clean_model_output()

exec(open("./workflow/create_output_for_outlook_data_system.py").read())

#%%
import estimate_charging_requirements
estimate_charging_requirements.estimate_kw_of_required_chargers()

# exec(open("./workflow/6_create_osemosys_output.py").read())
# import create_osemosys_output
# create_osemosys_output.create_osemosys_output()
#%%
ANALYSE_OUTPUT = True
if ANALYSE_OUTPUT:
    import plot_charging_graphs
    plot_charging_graphs.plot_required_chargers()
    
    exec(open("./workflow/plotting/oil_displacement.py").read())
    
    import all_economy_graphs
    all_economy_graphs.all_economy_graphs_massive_unwieldy_function(PLOT=False)
    # exec(open("./workflow/plotting/all_economy_graphs.py").read())
    #unfortunately at the moment i have written this to be run from data formatted within all_economy_graphs.py, but that takes ages t run.
    exec(open("./workflow/plotting/create_assumptions_dashboards.py").read())
    
    exec(open("./workflow/plotting/compare_esto_energy_to_data.py").read())
    
    plot_all_economy_graphs = True
    if plot_all_economy_graphs:
        #plot:
        all_economy_graphs.all_economy_graphs_massive_unwieldy_function(PLOT=True)
    
#%%
import utility_functions
utility_functions.copy_required_output_files_to_one_folder(FILE_DATE_ID, ECONOMIES_TO_PLOT_FOR, SCENARIOS_LIST,output_folder_path='output_data/for_other_modellers')

#%%
ARCHIVE_INPUT_DATA = True
if ARCHIVE_INPUT_DATA:
    archiving_scripts.archive_lots_of_files(archiving_folder)

#%%