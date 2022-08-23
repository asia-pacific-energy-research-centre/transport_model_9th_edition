

"""Integration is the act of bringing together smaller components into a single system that functions as one. In an IT context, integration refers to the end result of a process that aims to stitch 
together different, often disparate, subsystems so that the data contained in each becomes part of a larger, more comprehensive system that, ideally, quickly and easily shares data when needed. This 
often requires that companies build a customized architecture or structure of applications to combine new or existing hardware, software and other communications."""
# this file will manage all the modules in the transport system. This is so that each module can be easily run in sequence, as well as passing common variables to each

#%%
import datetime
#set global variables
file_date = datetime.datetime.now().strftime("%Y%m%d_%H%M")
file_date_id = '_DATE{}'.format(file_date)

#%%
execfile("workflow/1_clean_8th_edition_data.py")
execfile("workflow/1_clean_other_input_data.py")
execfile("workflow/1_clean_user_input.py")
execfile("workflow/2_adjust_input_data.py")
execfile("workflow/2_adjust_user_input_data.py")
execfile("workflow/3_calculate_activity_growth.py")
execfile("workflow/3_calculate_data_for_model.py")
execfile("workflow/4_run_road_model.py")
execfile("workflow/5_concatenate_model_output.py")
execfile("workflow/6_apply_fuel_mix_demand_side.py")
execfile("workflow/7_apply_fuel_mix_supply_side.py")
execfile("workflow/8_clean_model_output.py")
execfile("workflow/9_create_osemosys_output.py")
# %%


#%%
#CONFIG
#Senareo 
