#take in output data and do basic visualisationh and analysis

#%%
#set working directory as one folder back so that config works
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
from runpy import run_path
run_path("config/config.py")#usae this to load libraries and set variables. Feel free to edit that file as you need

#%%
# model_output_file_name = 'model_output_Dates_2017_to_2050_DATE20220823_1701.csv'
#load data in
model_output_all = pd.read_csv('output_data/model_output/{}'.format(model_output_file_name))

#%%
#analysis
#check for duplicates
duplicates = model_output_all.duplicated().sum()
if duplicates > 0:
    print('There are {} duplicates in the model output'.format(duplicates))
#check for missing values
NAs = model_output_all.isna().sum().sum()
if NAs > 0:
    print('There are {} missing values in the model output'.format(NAs))

#%%
