"""This file is intended to be able ot be used in the beginnning of any jupyter ntoebook to set the config variables for the model. This helps to reduce clutter, as that is a big issue for notebooks. So if you ever need to chnage conifgurations, just change this. """
#to make the code in this library clear we will name every variable that is stated in here with all caps
#%%

#import common libraries 
import pandas as pd 
import numpy as np
import glob
import os
from string import digits#is this used?
import datetime
import re
import shutil
# %config Completer.use_jedi = False#Jupiter lab specific setting to fix Auto fill bug
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
#can activate below to remove caveat warnings. but for now keep it there till confident:
# pd.options.mode.chained_assignment = None  # default='warn'
#%%
#STATE VARIABLES USER MAY CHANGE OFTEN:
NEW_SALES_SHARES = True
NEW_FUEL_MIXING_DATA = True
transport_data_system_FILE_DATE_ID ='DATE20230615' # 'DATE20230216'))

economies_to_plot_for =['19_THA', '20_USA']
#%%
#we can set FILE_DATE_ID to something other than the date here which is useful if we are running the script alone, versus through integrate.py


try:
    if FILE_DATE_ID:
       pass
except NameError:
    # FILE_DATE_ID = ''
    file_date = datetime.datetime.now().strftime("%Y%m%d")
    FILE_DATE_ID = '_{}'.format(file_date)#Note that this is not the official file date id anymore because it was interacting badly with how we should instead set it in onfig.py
   
#%%
USE_LATEST_OUTPUT_DATE_ID = False#True
#create option to set FILE_DATE_ID to the date_id of the latest created output files. this can be helpful when producing graphs and analysing output data
if USE_LATEST_OUTPUT_DATE_ID:
    list_of_files = glob.glob('./output_data/model_output/*.csv') 
    latest_file = max(list_of_files, key=os.path.getctime)
    #get file data id using regex. want to grab the firt 8 digits and then an underscore and then the next 4 digits
    FILE_DATE_ID = re.search(r'_DATE(\d{8})_(\d{4})', latest_file).group(0)

#%%
#state important modelling variables
BASE_YEAR= 2017
END_YEAR = 2100
USE_LOGISTIC_FUNCTION=True
#this is important for defining how the dataframes are used. Generally this shouldnt change unless a column name changes or the model is changed
INDEX_COLS = ['Date', 'Economy', 'Measure', 'Vehicle Type', 'Medium',
       'Transport Type','Drive', 'Scenario', 'Unit', 'Frequency']
INDEX_COLS_no_date = INDEX_COLS.copy()
INDEX_COLS_no_date.remove('Date')

model_output_file_name = 'model_output_years_{}_to_{}{}.csv'.format(BASE_YEAR, END_YEAR, FILE_DATE_ID)

gompertz_function_diagnostics_dataframe_file_name = 'gompertz_function_diagnostics_dataframe{}.csv'.format(FILE_DATE_ID)

EIGHTH_EDITION_DATA = True#this is used to determine if we are using the 8th edition data. Perhaps in the future we will determine this useing the 'dataset' columnn but for now we wexpect to be moving on from that dataset soon so we will just use this variable

#get sceanrios from scenarios_list file
SCENARIOS_LIST = pd.read_csv('config/concordances_and_config_data/scenarios_list.csv')
#grab the scenario names where 'Use' column is true and put them into a list
SCENARIOS_LIST = SCENARIOS_LIST[SCENARIOS_LIST['Use'] == True]['Scenario'].tolist()

#For graphing and analysis we sometimes will single out a scenario to look at. This is the scenario we will use for that:
SCENARIO_OF_INTEREST = 'Reference'

user_input_measures_list_ROAD = ['Vehicle_sales_share', 'Turnover_rate_growth',
       'New_vehicle_efficiency_growth', 'Occupancy_or_load_growth', 'Mileage_growth','Gompertz_gamma']#, 'Gompertz_beta''Gompertz_alpha', 
user_input_measures_list_NON_ROAD = ['Non_road_intensity_improvement']

base_year_measures_list_ROAD = ['Activity','Energy', 'Stocks', 'Occupancy_or_load', 'Turnover_rate', 'New_vehicle_efficiency', 'Efficiency','Mileage']
base_year_measures_list_NON_ROAD = ['Activity','Energy', 'Stocks', 'Intensity']

calculated_measures_ROAD = ['Travel_km','Surplus_stocks']#tinclude travel km as to be calcualted as it is not widely available publicly, so its best just to calculate it.its also kind of an intermediate measure as it is reliant on what mileage,efficiency and stocks are, but is not the goal like energy or activity really are
calculated_measures_NON_ROAD = []

#%%
#import measure to unit concordance
measure_to_unit_concordance = pd.read_csv('config/concordances_and_config_data/measure_to_unit_concordance.csv')

#import manually_defined_transport_categories
transport_categories = pd.read_csv('config/concordances_and_config_data/manually_defined_transport_categories.csv')
###################################################
#%%

## Choose which economies to import and calculate data for:
#first take in economy names file, then we will remove the economies we dont want (or if there are too many, just  choose the one you do want)
economy_codes_path = 'config/concordances_and_config_data/economy_code_to_name.csv'

ECONOMY_LIST = pd.read_csv(economy_codes_path).iloc[:,0]#get the first column

#ECONOMY REGIONS
#load the economy regions file so that we can easily merge it with a dataframe to create a region column
economy_regions_path = 'config/concordances_and_config_data/region_economy_mapping.csv'
ECONOMY_REGIONS = pd.read_csv(economy_regions_path)

###################################################
#%%
import plotly.express as px
#graphing tools:
PLOTLY_COLORS_LIST = px.colors.qualitative.Plotly

AUTO_OPEN_PLOTLY_GRAPHS = False

# %%
#state model concordances file names for concordances we create manually
model_concordances_version = FILE_DATE_ID#'20220824_1256'
model_concordances_file_name  = 'model_concordances{}.csv'.format(model_concordances_version)
model_concordances_file_name_fuels = 'model_concordances_fuels{}.csv'.format(model_concordances_version)
model_concordances_file_name_fuels_NO_BIOFUELS = 'model_concordances_fuels_NO_BIOFUELS{}.csv'.format(model_concordances_version)

#state model concordances file names for concordances we create using inputs into the model. these model concordances state what measures are used in the model
model_concordances_base_year_measures_file_name = 'model_concordances_measures{}.csv'.format(model_concordances_version)
model_concordances_user_input_and_growth_rates_file_name = 'model_concordances_user_input_and_growth_rates{}.csv'.format(model_concordances_version)
model_concordances_supply_side_fuel_mixing_file_name = 'model_concordances_supply_side_fuel_mixing{}.csv'.format(model_concordances_version)
model_concordances_demand_side_fuel_mixing_file_name = 'model_concordances_demand_side_fuel_mixing{}.csv'.format(model_concordances_version)

#AND A model_concordances_all_file_name
# model_concordances_all_file_name = 'model_concordances_all{}.csv'.format(model_concordances_version)
#%%