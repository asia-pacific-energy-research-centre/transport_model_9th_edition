#to do. make a way of archiving input data
#most important thing is to save the input and config data to a folder in case we need to use that data again. problem is that this could become memory intensive. Perhaps this can be a function which saves the input file to a folder with the date id. it is then the users responsibility to extract the file and put it in the right place again
#
#save file to folder in input_data/previous_run_archive
#name folder with the file_date_id

#%%
#set working directory as one folder back so that config works
import os
import re
import shutil
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
execfile("config/config.py")#usae this to load libraries and set variables. Feel free to edit that file as you need
# pio.renderers.default = "browser"#allow plotting of graphs in the interactive 
# notebook in vscode #or set to notebook

#create folder
#if file data id is '' then just save the data to foler 'latest_test_run' as we assume this run isnt important enough to save the data in a unique folder
if file_date_id == '':
    folder_name = 'latest_test_run'
else:
    folder_name = file_date_id
    #if folder odesnt exist already
    if not os.path.exists('input_data/previous_run_archive/'+folder_name):
        os.mkdir('input_data/previous_run_archive/{}'.format(file_date_id))
#%%
#load data that we want to archive 
#t omake thigns simple while we havent got a clear idea of what we need we will just load and save the model inputs and fuel mixing data

#NON ROAD
non_road_efficiency_growth= pd.read_csv('intermediate_data/non_aggregated_input_data/non_road_efficiency_growth.csv')
non_road_model_input = pd.read_csv('intermediate_data/model_inputs/non_road_model_input.csv')
activity_growth = pd.read_csv('intermediate_data/model_inputs/activity_growth.csv')

#ROAD
Vehicle_sales_share = pd.read_csv('intermediate_data/non_aggregated_input_data/Vehicle_sales_share.csv')
OccupanceAndLoad_growth= pd.read_csv('intermediate_data/non_aggregated_input_data/OccupanceAndLoad_growth.csv')
Turnover_rate_growth= pd.read_csv('intermediate_data/non_aggregated_input_data/Turnover_Rate_growth.csv')
New_vehicle_efficiency_growth= pd.read_csv('intermediate_data/non_aggregated_input_data/New_vehicle_efficiency_growth.csv')
road_model_input = pd.read_csv('intermediate_data/model_inputs/road_model_input.csv')
activity_growth = pd.read_csv('intermediate_data/model_inputs/activity_growth.csv')

#load user input for fuel mixing 
demand_side_fuel_mixing = pd.read_csv('intermediate_data\model_inputs\demand_side_fuel_mixing_COMPGEN.csv')

#load model concordances with fuels
model_concordances_fuels = pd.read_csv('config/concordances/{}'.format(model_concordances_file_name_fuels))

#load user input for fuel mixing
supply_side_fuel_mixing = pd.read_csv('intermediate_data\model_inputs\supply_side_fuel_mixing_COMPGEN.csv')

#load model concordances
model_concordances = pd.read_csv('config/concordances/{}'.format(model_concordances_file_name))

#save it all to a foler with name folder_name
#%%
#save file to folder in input_data/previous_run_archive/{}.foramt(folder_name)

#save files
non_road_efficiency_growth.to_csv('input_data/previous_run_archive/{}/non_road_efficiency_growth.csv'.format(folder_name))
non_road_model_input.to_csv('input_data/previous_run_archive/{}/non_road_model_input.csv'.format(folder_name))
activity_growth.to_csv('input_data/previous_run_archive/{}/activity_growth.csv'.format(folder_name))
Vehicle_sales_share.to_csv('input_data/previous_run_archive/{}/Vehicle_sales_share.csv'.format(folder_name))
OccupanceAndLoad_growth.to_csv('input_data/previous_run_archive/{}/OccupanceAndLoad_growth.csv'.format(folder_name))
Turnover_rate_growth.to_csv('input_data/previous_run_archive/{}/Turnover_rate_growth.csv'.format(folder_name))
New_vehicle_efficiency_growth.to_csv('input_data/previous_run_archive/{}/New_vehicle_efficiency_growth.csv'.format(folder_name))
road_model_input.to_csv('input_data/previous_run_archive/{}/road_model_input.csv'.format(folder_name))
activity_growth.to_csv('input_data/previous_run_archive/{}/activity_growth.csv'.format(folder_name))

#save model concordances to folder
model_concordances.to_csv('input_data/previous_run_archive/{}/model_concordances.csv'.format(folder_name))
model_concordances_fuels.to_csv('input_data/previous_run_archive/{}/model_concordances_fuels.csv'.format(folder_name))

#save fuel mixing data
demand_side_fuel_mixing.to_csv('input_data/previous_run_archive/{}/demand_side_fuel_mixing.csv'.format(folder_name))
supply_side_fuel_mixing.to_csv('input_data/previous_run_archive/{}/supply_side_fuel_mixing.csv'.format(folder_name))

#save output data
#%%
#save config file to folder
shutil.copyfile('config/config.py', 'input_data/previous_run_archive/{}/config.py'.format(folder_name))

#copy diagnostics graphs to the folder
shutil.copytree('plotting_output/diagnostics/', 'input_data/previous_run_archive/{}/diagnostics/'.format(folder_name))
#%%
#done