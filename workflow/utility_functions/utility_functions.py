

#####################################################

###IMPORT GLOBAL VARIABLES FROM config.py
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
import sys
sys.path.append("./config")
import config

import pandas as pd 
import numpy as np
import yaml
import datetime
import shutil
import sys
import os 
import re
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go
import matplotlib
import matplotlib.pyplot as plt
from plotly.subplots import make_subplots
####Use this to load libraries and set variables. Feel free to edit that file as you need.

def copy_required_output_files_to_one_folder(output_folder_path='output_data/for_other_modellers'):
    #to make it easier to give the output to others use ths function to make it a bit easier to group the files that people find useful together, so i can quickly send them.
    useful_file_paths = []
    output_file_paths = []
    #dashboard fiels:
    for economy in config.ECONOMY_LIST:
        for scenario in config.SCENARIOS_LIST:
            useful_file_paths.append('plotting_output/dashboards/' + economy + f'/{economy}_{scenario}_assumptions_dashboard_detailed.html')
            output_file_paths.append(output_folder_path + '/' + economy + f'/{economy}_{scenario}_assumptions_dashboard_detailed.html')
            useful_file_paths.append('plotting_output/dashboards/' + economy + f'/{economy}_{scenario}_assumptions_dashboard_presentation.html')
            output_file_paths.append(output_folder_path + '/' + economy + f'/{economy}_{scenario}_assumptions_dashboard_presentation.html')
            
            useful_file_paths.append(f'output_data/for_other_modellers/output_for_outlook_data_system/{economy}_{config.FILE_DATE_ID}_transport_energy_use.csv')
            output_file_paths.append(output_folder_path + '/' + economy + f'/{economy}_transport_energy_use.csv')
    
    # chargers: output_data\for_other_modellers\estimated_number_of_chargers.csv
    #this one si already put there automatically so ignore it
    # useful_file_paths.append('output_data/' + 'for_other_modellers' + '/estimated_number_of_chargers.csv')
    # Energy use:
    # output_data\for_other_modellers\transport_energy_use{config.FILE_DATE_ID}.csv
    
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