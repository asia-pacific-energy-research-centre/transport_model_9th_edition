

"""Integration is the act of bringing together smaller components into a single system that functions as one. In an IT context, integration refers to the end result of a process that aims to stitch 
together different, often disparate, subsystems so that the data contained in each becomes part of a larger, more comprehensive system that, ideally, quickly and easily shares data when needed. This 
often requires that companies build a customized architecture or structure of applications to combine new or existing hardware, software and other communications."""
# this file will manage all the modules in the transport system. This is so that each module can be easily run in sequence, as well as passing common variables to each
#%%
#helper function, print lines to run python files the user might want to include in the execute script below
run = False
if run:
    import os
    for root, dirs, files in os.walk(".", topdown=False):
        #only use folders in workflow folder that arent in archive
        if 'workflow' in root and 'archive' not in root:
            for name in files:
                if name.endswith('.py'):
                    print('exec(open("{}").read())'.format(os.path.join(root, name).replace('\\', '/')))

#%%
import datetime

#set global variables
file_date = datetime.datetime.now().strftime("%Y%m%d_%H%M")
FILE_DATE_ID = '_DATE{}'.format(file_date)
FILE_DATE_ID = ''#comment me out if you want the output and archived input data to be saved with a specific date id 
print('Model run for {} starting'.format(file_date))
print('\n FILE_DATE_ID is set to {}'.format(FILE_DATE_ID))

PLOT_INPUT_DATA = False
CREATE_MODEL_CONCORDANCES = True
#%%
if CREATE_MODEL_CONCORDANCES:
    exec(open("./workflow/grooming_code/0_create_model_concordances.py").read())
#%%
exec(open("./workflow/grooming_code/1_clean_user_input.py").read())
#%%
exec(open("./workflow/grooming_code/1_import_transport_system_data.py").read())
#%%
exec(open("./workflow/grooming_code/2_aggregate_data_for_model.py").read())
if PLOT_INPUT_DATA:
    exec(open("./workflow/grooming_code/3_communicate_missing_input_data.py").read())

exec(open("./workflow/grooming_code/4_calculate_activity_growth.py").read())
#%%
exec(open("./workflow/grooming_code/4_calculate_inputs_for_model.py").read())

#%%
exec(open("./workflow/1_run_non_road_model.py").read())
exec(open("./workflow/1_run_road_model.py").read())
#%%
exec(open("./workflow/2_concatenate_model_output.py").read())
exec(open("./workflow/3_apply_fuel_mix_demand_side.py").read())
exec(open("./workflow/4_apply_fuel_mix_supply_side.py").read())
exec(open("./workflow/5_clean_model_output.py").read())
# exec(open("./workflow/6_create_osemosys_output.py").read())
#%%
ANALYSE_OUTPUT = True
if ANALYSE_OUTPUT:
    # exec(open("other_code/analysis_code/compare_8th_to_9th_by_medium.py").read())
    # exec(open("other_code/analysis_code/compare_8th_to_9th_by_fuel.py").read())
    # exec(open("other_code/analysis_code/compare_8th_to_9th_by_drive.py").read())
    exec(open("other_code/plotting/all_economy_graphs.py").read())
    exec(open("other_code/plotting/analyse_experimental.py").read())
#%%
ARCHIVE_INPUT_DATA = True
if ARCHIVE_INPUT_DATA:
    exec(open('./config/utilities/archiving_script.py').read())

#%%