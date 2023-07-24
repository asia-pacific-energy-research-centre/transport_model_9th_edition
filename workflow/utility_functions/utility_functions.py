

#####################################################
import os
import re
import datetime
import sys
import logging
import numpy as np
import pandas as pd
import shutil
import yaml 

def copy_required_output_files_to_one_folder(FILE_DATE_ID, ECONOMIES_TO_PLOT_FOR,SCENARIOS_LIST, output_folder_path='output_data/for_other_modellers'):
    #to make it easier to give the output to others use ths function to make it a bit easier to group the files that people find useful together, so i can quickly send them.
    useful_file_paths = []
    output_file_paths = []
    #dashboard fiels:
    for economy in ECONOMIES_TO_PLOT_FOR:
        for scenario in SCENARIOS_LIST:
          useful_file_paths.append('plotting_output/dashboards/' + economy + f'/{scenario}_assumptions_dashboard_detailed.html')
          output_file_paths.append(output_folder_path + '/' + economy + f'/{scenario}_assumptions_dashboard_detailed.html')
          useful_file_paths.append('plotting_output/dashboards/' + economy + f'/{scenario}_assumptions_dashboard_presentation.html')
          output_file_paths.append(output_folder_path + '/' + economy + f'/{scenario}_assumptions_dashboard_presentation.html')
    
    # chargers: output_data\for_other_modellers\estimated_number_of_chargers.csv
    #this one si already put there automatically so ignore it
    # useful_file_paths.append('output_data/' + 'for_other_modellers' + '/estimated_number_of_chargers.csv')
    # Energy use:
    # output_data\for_other_modellers\transport_energy_use{FILE_DATE_ID}.csv
    
    #for every file in useful file paths, copy it to its corresponding output file path
    for f in range(len(useful_file_paths)):
        try:
            #first test that the folders exist, if not create them
            if not os.path.exists(os.path.dirname(output_file_paths[f])):
                os.makedirs(os.path.dirname(output_file_paths[f]))
            shutil.copyfile(useful_file_paths[f], output_file_paths[f])
        except FileNotFoundError:
            print('File not found: ' + useful_file_paths[f])
        except shutil.Error:
            print('File already exists: ' + output_file_paths[f])
    
def get_latest_date_for_data_file(data_folder_path, file_name):
    #get list of all files in the data folder
    all_files = os.listdir(data_folder_path)
    #filter for only the files with the correct file extension
    all_files = [file for file in all_files if file_name in file]
    #drop any files with no date in the name
    all_files = [file for file in all_files if re.search(r'\d{8}', file)]
    #get the date from the file name
    all_files = [re.search(r'\d{8}', file).group() for file in all_files]
    #convert the dates to datetime objects
    all_files = [datetime.datetime.strptime(date, '%Y%m%d') for date in all_files]
    #get the latest date
    try:
        latest_date = max(all_files)
    except ValueError:
        print('No files found for ' + file_name)
        return None
    #convert the latest date to a string
    latest_date = latest_date.strftime('%Y%m%d')
    return latest_date
    
# def get_latest_date_for_data_file(data_folder_path, file_name):
#     #get list of all files in the data folder
#     all_files = os.listdir(data_folder_path)
#     #filter for only the files with the correct file extension
#     all_files = [file for file in all_files if file_name in file]
#     #drop any files with no date in the name
#     all_files = [file for file in all_files if re.search(r'\d{8}', file)]
#     #get the date from the file name
#     all_files = [re.search(r'\d{8}', file).group() for file in all_files]
#     #convert the dates to datetime objects
#     all_files = [datetime.datetime.strptime(date, '%Y%m%d') for date in all_files]
#     #get the latest date
#     try:
#         latest_date = max(all_files)
#     except ValueError:
#         print('No files found for ' + file_name)
#         return None
#     #convert the latest date to a string
#     latest_date = latest_date.strftime('%Y%m%d')
#     return latest_date