

"""Integration is the act of bringing together smaller components into a single system that functions as one. In an IT context, integration refers to the end result of a process that aims to stitch 
together different, often disparate, subsystems so that the data contained in each becomes part of a larger, more comprehensive system that, ideally, quickly and easily shares data when needed. This 
often requires that companies build a customized architecture or structure of applications to combine new or existing hardware, software and other communications."""
# this file will manage all the modules in the transport system. This is so that each module can be easily run in sequence, as well as passing common variables to each


#%%
import datetime
#set global variables
file_date = datetime.datetime.now().strftime("%Y%m%d_%H%M")
file_date_id = '_DATE{}'.format(file_date)
# file_date_id = ''#comment me out if you want the output and archived input data to be saved with a specific date id
print('Model run for {} starting'.format(file_date))
print('\n file_date_id is set to {}'.format(file_date_id))
#%%
execfile('./config/utilities/create_model_concordances.py')#currently tehse are vbased off osemosys_concordances = pd.read_csv('config/concordances/OSEMOSYS_concordances.csv')

#%%
execfile("workflow/1_clean_8th_edition_data.py")
execfile("workflow/1_clean_other_input_data.py")
execfile("workflow/1_clean_user_input.py")
execfile("workflow/2_fill_missing_input_data.py")
execfile("workflow/2_calculate_activity_growth.py")

#%%
execfile("workflow/3a_aggregate_data_for_model.py")
execfile("workflow/3b_calculate_input_for_model.py")

#%%
execfile("workflow/4_run_non_road_model.py")
execfile("workflow/4_run_road_model.py")
#%%
execfile("workflow/5_concatenate_model_output.py")
execfile("workflow/6_apply_fuel_mix_demand_side.py")
execfile("workflow/7_apply_fuel_mix_supply_side.py")
execfile("workflow/8_clean_model_output.py")
execfile("workflow/9_create_osemosys_output.py")
#%%

execfile("other_code/analysis_code/print_diagnostics.py")

#%%
ANALYSE_OUTPUT = False#True
if ANALYSE_OUTPUT:
    # execfile("other_code/analysis_code/compare_8th_to_9th_by_medium.py")
    # execfile("other_code/analysis_code/compare_8th_to_9th_by_fuel.py")
    # execfile("other_code/analysis_code/compare_8th_to_9th_by_drive.py")
    execfile("other_code/analysis_code/plot_input_data.py")
    execfile("other_code/analysis_code/analyse_experimental.py")
    execfile("other_code/analysis_code/plot_data_for_others.py")

#%%
ARCHIVE_INPUT_DATA = True
if ARCHIVE_INPUT_DATA:
    execfile('./config/utilities/archiving_script.py')

#%%   