#most important thing is to save the input and CONCORDANCES data to a folder in case we need to use that data again. 
# This saves the archived data to a folder with the date id. If the user needs to use that then they will use a separate script to extract the information they need from the data (as of 2022 this is not yet implemented)

#name folder with the config.FILE_DATE_ID


#set working directory as one folder back so that config works
import os
import re
import shutil
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
from runpy import run_path
exec(open("config/config.py").read())#usae this to load libraries and set variables. Feel free to edit that file as you need
# pio.renderers.default = "browser"#allow plotting of graphs in the interactive 
# notebook in vscode #or set to notebook

def create_archiving_folder_for_FILE_DATE_ID():
    #create folder
    #if file data id is '' then just save the data to foler 'latest_test_run' as we assume this run isnt important enough to save the data in a unique folder
    if config.FILE_DATE_ID == '':
        archive_folder_name = 'input_data/previous_run_archive/latest_test_run'
    else:
        archive_folder_name = 'input_data/previous_run_archive/' + config.FILE_DATE_ID
        #since config.FILE_DATE_ID might not be the actual day, we need to create a subfolder for the actual day
        
        if os.path.exists(archive_folder_name):
            import datetime
            new_FILE_DATE_ID = '_{}'.format(datetime.datetime.now().strftime("%Y%m%d"))#Note that this is not the official file date id anymore because it was interacting badly with how we should instead set it in onfig.py
            archive_folder_name = 'input_data/previous_run_archive/' + config.FILE_DATE_ID +'/'+ new_FILE_DATE_ID
        
            if not os.path.exists(archive_folder_name):
                os.mkdir(archive_folder_name)
        else:
            os.mkdir(archive_folder_name)
    return archive_folder_name

def archive_lots_of_files(archive_folder_name):
    #load data that we want to archive 
    #t omake thigns simple while we havent got a clear idea of what we need we will just load and save the model inputs and fuel mixing data

    # #Major model inputs:

    #load output data
    model_output_detailed = pd.read_csv('output_data/model_output_detailed/{}'.format(config.model_output_file_name))
    model_output_non_detailed = pd.read_csv('output_data/model_output/{}'.format(config.model_output_file_name))
    model_output_all_with_fuels = pd.read_csv('output_data/model_output_with_fuels/{}'.format(config.model_output_file_name))

    #save output data
    model_output_detailed.to_csv('{}/model_output_detailed.csv'.format(archive_folder_name))
    model_output_non_detailed.to_csv('{}/model_output_non_detailed.csv'.format(archive_folder_name))
    model_output_all_with_fuels.to_csv('{}/model_output_all_with_fuels.csv'.format(archive_folder_name))
    
    #save config file to folder
    shutil.copyfile('config/config.py', '{}/config.py'.format(archive_folder_name))

    #save all workflow files to folder, incmluding all subfolders (they are the code)
    recursively_save_file('./workflow', archive_folder_name, 'file_extension=.py', exclude_archive_folder=True)
    #save all csvs in \input_data\user_input_spreadsheets
    recursively_save_file('input_data/user_input_spreadsheets', archive_folder_name, file_extension='.csv', exclude_archive_folder=True)
    recursively_save_file('intermediate_data/model_inputs', archive_folder_name, file_extension='.csv', exclude_archive_folder=True)
    recursively_save_file('output_data/for_other_modellers', archive_folder_name, exclude_archive_folder=True)
    
    #and save individual files
    fuel_mixing_assumptions = 'input_data/fuel_mixing_assumptions.xlsx'
    shutil.copyfile(fuel_mixing_assumptions, '{}/fuel_mixing_assumptions.xlsx'.format(archive_folder_name))

    recursively_save_file('config/concordances_and_config_data/computer_generated_concordances', archive_folder_name, '.csv', exclude_archive_folder=True)

    # zip_up_folder(archive_folder_name)
    
    
def recursively_save_file(source_dir, dest_dir, file_extension='*', exclude_archive_folder=True):
    import os
    import shutil

    # create the destination directory if it doesn't already exist
    os.makedirs(dest_dir, exist_ok=True)

    # walk the source directory
    for dirpath, dirnames, filenames in os.walk(source_dir):
        for filename in filenames:
            if (filename.endswith(file_extension)) or (file_extension == '*'):
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
    # if os.path.exists('C:/Users/finbar.maunsell/Documents'):
        
    #     output_file = 'C:/Users/finbar.maunsell/Documents'#this is really cheating but it works for now
    # else:
    #     output_file = 'C:/Users/Finbar Maunsell/Documents'

    # create a zip archive with file date id
    output_file = archive_folder_name +'/'+ config.FILE_DATE_ID + '_0'
    #if it is already there then make the number at the end one higher
    while os.path.exists(output_file + '.zip'):
        output_file = output_file[:-1] + str(int(output_file[-1])+1)

    shutil.make_archive(output_file, 'zip', archive_folder_name)
    print(f'Zipped up {archive_folder_name} to {output_file}.zip')
