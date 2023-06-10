#most important thing is to save the input and CONCORDANCES data to a folder in case we need to use that data again. 
# This saves the archived data to a folder with the date id. If the user needs to use that then they will use a separate script to extract the information they need from the data (as of 2022 this is not yet implemented)

#name folder with the FILE_DATE_ID

#%%
#set working directory as one folder back so that config works
import os
import re
import shutil
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
from runpy import run_path
exec(open("config/config.py").read())#usae this to load libraries and set variables. Feel free to edit that file as you need
# pio.renderers.default = "browser"#allow plotting of graphs in the interactive 
# notebook in vscode #or set to notebook

def create_archiving_folder_for_FILE_DATE_ID(FILE_DATE_ID):
    #create folder
    #if file data id is '' then just save the data to foler 'latest_test_run' as we assume this run isnt important enough to save the data in a unique folder
    if FILE_DATE_ID == '':
        archive_folder_name = 'input_data/previous_run_archive/latest_test_run'
    else:
        archive_folder_name = 'input_data/previous_run_archive/' + FILE_DATE_ID
        #if folder odesnt exist already
        if not os.path.exists(archive_folder_name):
            os.mkdir(archive_folder_name)
    return archive_folder_name
#%%
def archive_lots_of_files(archive_folder_name):
    #load data that we want to archive 
    #t omake thigns simple while we havent got a clear idea of what we need we will just load and save the model inputs and fuel mixing data

    #Major model inputs:
    activity_growth = pd.read_csv('intermediate_data/model_inputs/activity_growth.csv')
    non_road_model_input = pd.read_csv('intermediate_data/model_inputs/non_road_model_input.csv')
    road_model_input = pd.read_csv('intermediate_data/model_inputs/road_model_input.csv')

    #load user input for fuel mixing 
    demand_side_fuel_mixing = pd.read_csv('intermediate_data\model_inputs\demand_side_fuel_mixing_COMPGEN.csv')

    #load user input for fuel mixing
    supply_side_fuel_mixing = pd.read_csv('intermediate_data\model_inputs\supply_side_fuel_mixing_COMPGEN.csv')

    #load output data
    model_output_detailed = pd.read_csv('output_data/model_output_detailed/{}'.format(model_output_file_name))

    model_output_non_detailed = pd.read_csv('output_data/model_output/{}'.format(model_output_file_name))

    model_output_all_with_fuels = pd.read_csv('output_data/model_output_with_fuels/{}'.format(model_output_file_name))


    #%%

    #save it all to a foler with name archive_folder_name
    #save file to folder in {}.foramt(archive_folder_name)

    #save files
    non_road_model_input.to_csv('{}/non_road_model_input.csv'.format(archive_folder_name), index=False)
    road_model_input.to_csv('{}/road_model_input.csv'.format(archive_folder_name))

    activity_growth.to_csv('{}/activity_growth.csv'.format(archive_folder_name))

    #save fuel mixing data
    demand_side_fuel_mixing.to_csv('{}/demand_side_fuel_mixing.csv'.format(archive_folder_name))
    supply_side_fuel_mixing.to_csv('{}/supply_side_fuel_mixing.csv'.format(archive_folder_name))

    #save output data
    model_output_detailed.to_csv('{}/model_output_detailed.csv'.format(archive_folder_name))

    model_output_non_detailed.to_csv('{}/model_output_non_detailed.csv'.format(archive_folder_name))

    model_output_all_with_fuels.to_csv('{}/model_output_all_with_fuels.csv'.format(archive_folder_name))


    #%%
    #save config file to folder
    shutil.copyfile('config/config.py', '{}/config.py'.format(archive_folder_name))

    #save all concordances data in concordances_and_config_data/computer_generated_concordances to folder
    #first get all files in folder
    config_files = os.listdir('config/concordances_and_config_data/computer_generated_concordances')
    for file in config_files:
        #if file contains FILE_DATE_ID then copy it to folder
        if FILE_DATE_ID in file:
            shutil.copyfile('config/concordances_and_config_data/computer_generated_concordances/{}'.format(file), '{}/{}'.format(archive_folder_name,file))
        
    #copy diagnostics graphs to the folder
    shutil.copytree('plotting_output/diagnostics/', '{}/diagnostics/'.format(archive_folder_name),dirs_exist_ok=True)
    #%%
    #done