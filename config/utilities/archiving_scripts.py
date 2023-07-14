#most important thing is to save the input and CONCORDANCES data to a folder in case we need to use that data again. 
# This saves the archived data to a folder with the date id. If the user needs to use that then they will use a separate script to extract the information they need from the data (as of 2022 this is not yet implemented)

#name folder with the FILE_DATE_ID


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
        #since FILE_DATE_ID might not be the actual day, we need to create a subfolder for the actual day
        
        if os.path.exists(archive_folder_name):
            import datetime
            new_FILE_DATE_ID = '_{}'.format(datetime.datetime.now().strftime("%Y%m%d"))#Note that this is not the official file date id anymore because it was interacting badly with how we should instead set it in onfig.py
            archive_folder_name = 'input_data/previous_run_archive/' + FILE_DATE_ID +'/'+ new_FILE_DATE_ID
        
            if not os.path.exists(archive_folder_name):
                os.mkdir(archive_folder_name)
        else:
            os.mkdir(archive_folder_name)
    return archive_folder_name

def archive_lots_of_files(archive_folder_name):
    #load data that we want to archive 
    #t omake thigns simple while we havent got a clear idea of what we need we will just load and save the model inputs and fuel mixing data

    #Major model inputs:
    activity_growth = pd.read_csv('intermediate_data/model_inputs/growth_forecasts.csv')
    non_road_model_input = pd.read_csv('intermediate_data/model_inputs/non_road_model_input_wide.csv')
    road_model_input = pd.read_csv('intermediate_data/model_inputs/road_model_input_wide.csv')

    #load user input for fuel mixing 
    demand_side_fuel_mixing = pd.read_csv('intermediate_data\model_inputs\demand_side_fuel_mixing_COMPGEN.csv')

    #load user input for fuel mixing
    supply_side_fuel_mixing = pd.read_csv('intermediate_data\model_inputs\supply_side_fuel_mixing_COMPGEN.csv')

    #load output data
    model_output_detailed = pd.read_csv('output_data/model_output_detailed/{}'.format(model_output_file_name))

    model_output_non_detailed = pd.read_csv('output_data/model_output/{}'.format(model_output_file_name))

    model_output_all_with_fuels = pd.read_csv('output_data/model_output_with_fuels/{}'.format(model_output_file_name))


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


    
    #save config file to folder
    shutil.copyfile('config/config.py', '{}/config.py'.format(archive_folder_name))

    #save all workflow files to folder, incmluding all subfolders (they are the code)
    recursively_save_file('./workflow', archive_folder_name, '.py', exclude_archive_folder=True)
    
    #save all csvs in \input_data\user_input_spreadsheets
    recursively_save_file('input_data/user_input_spreadsheets', archive_folder_name, '.csv', exclude_archive_folder=True)
    
    #and save 
    fuel_mixing_assumptions = 'input_data/fuel_mixing_assumptions.xlsx'
    shutil.copyfile(fuel_mixing_assumptions, '{}/fuel_mixing_assumptions.xlsx'.format(archive_folder_name))

    recursively_save_file('config/concordances_and_config_data/computer_generated_concordances', archive_folder_name, '.csv', exclude_archive_folder=True)

    # zip_up_folder(archive_folder_name)
    
    
def recursively_save_file(source_dir, dest_dir, file_extension, exclude_archive_folder=True):
    import os
    import shutil

    # create the destination directory if it doesn't already exist
    os.makedirs(dest_dir, exist_ok=True)

    # walk the source directory
    for dirpath, dirnames, filenames in os.walk(source_dir):
        for filename in filenames:
            if filename.endswith('.py'):
                if exclude_archive_folder:
                    if '/archive' in dirpath:
                        continue
                # construct full file path
                full_file_path = os.path.join(dirpath, filename)
                # copy file to destination directory
                shutil.copy2(full_file_path, dest_dir)

    print('Done.')

#zip up the folder and save to C drive:
def zip_up_folder(archive_folder_name):
    if os.path.exists('C:/Users/finbar.maunsell/Documents'):
        
        output_file = 'C:/Users/finbar.maunsell/Documents'#this is really cheating but it works for now
    else:
        output_file = 'C:/Users/Finbar Maunsell/Documents'

    # create a zip archive with file date id
    output_file = output_file + FILE_DATE_ID
    #if it is already there then delete it
    if os.path.exists(output_file + '.zip'):
        os.remove(output_file + '.zip')
    shutil.make_archive(output_file, 'zip', archive_folder_name)
    print(f'Zipped up {archive_folder_name} to {output_file}.zip')
