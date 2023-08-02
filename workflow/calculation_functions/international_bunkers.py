#%%
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
import utility_functions

#this will be a bit of an all in one file for the international bunkers calculations. Will take the data from esto to estiamte the bunker fuel use for each economy for each transport/medium type,  then use a similar method to the vehicle sales shares for non road to determine the fuel type shares for each economy, and lastly times by the average growth rate of non road fuel use to get the bunker fuel use for each economy in the future.
#%%
#%%
    
def international_bunker_share_calculation_handler():
    
    #load international bunker data from esto:
    energy_use_esto_bunkers_tall = extract_bunker_data_from_esto()
    #now extract sales/fuel share data:
    international_fuel_shares = extract_bunkers_fuel_share_inputs()
    #calcualte avergae growth rate from domestic non road energy use:
    non_road_energy_use = extract_non_road_energy_use()
    non_road_energy_use_growth_rate = calculate_non_road_energy_use_growth_rate(non_road_energy_use)
    #check for duplcaites: 
    check_for_duplicates_in_all_datasets(energy_use_esto_bunkers_tall, international_fuel_shares, non_road_energy_use_growth_rate)
    #merge all data
    international_bunker_energy_use_inputs = merge_and_format_all_input_data(energy_use_esto_bunkers_tall, international_fuel_shares, non_road_energy_use_growth_rate)
    #interpolate the fuel shares to get a value for every year:
    international_bunker_energy_use_inputs = interpolate_bunker_shares(international_bunker_energy_use_inputs)
    
    #and check it all matches wat we expect:
    check_all_input_data_against_concordances(international_bunker_energy_use_inputs)
    
def extract_bunker_data_from_esto():
        
    #load the 9th data
    date_id = utility_functions.get_latest_date_for_data_file('input_data/9th_model_inputs', 'model_df_wide_')
    energy_use_esto = pd.read_csv(f'input_data/9th_model_inputs/model_df_wide_{date_id}.csv')

    #TEMP replace 15_PHL with 15_RP and 17_SGP with 17_SIN in the eocnomy col. make sure to let user know they can klet hyguga know:
    if len(energy_use_esto.loc[energy_use_esto['economy'].isin(['15_PHL', '17_SGP'])]) > 0:
        print('########################\n\n there are some economies in the esto data that are not in the model data. we will replace 15_PHL with 15_RP and 17_SGP with 17_SIN. AKA TELL HYUGA wats up \n\n########################')
    energy_use_esto['economy'] = energy_use_esto['economy'].replace({'15_PHL': '15_RP', '17_SGP': '17_SIN'})

    #extract only bunker data. that is data for 04_international_marine_bunkers, 05_international_aviation_bunkers where aviation is air and marine is ship mediums
    energy_use_esto_bunkers = energy_use_esto.loc[energy_use_esto['sectors'].isin(['04_international_marine_bunkers', '05_international_aviation_bunkers'])]
    #drop where subfuels is x. tehese are aggregations.
    energy_use_esto_bunkers = energy_use_esto_bunkers.loc[energy_use_esto_bunkers['subfuels'] != 'x']

    #map the subfuels to the fuel types. 
    energy_use_esto_bunkers['Fuel'] =energy_use_esto_bunkers['subfuels'].map(config.temp_esto_subfuels_to_new_subfuels_mapping)
    #map 07_x_other_petroleum_products to 07_x_other_petroleum_products#this is not used in the transport system otehrwise
    energy_use_esto_bunkers.loc[energy_use_esto_bunkers['subfuels'] == '07_x_other_petroleum_products', 'Fuel'] = '07_x_other_petroleum_products'
    #map the sectors to medium:
    bunkers_mapping = {'04_international_marine_bunkers': 'ship', '05_international_aviation_bunkers': 'air'}
    energy_use_esto_bunkers['Medium'] = energy_use_esto_bunkers['sectors'].map(bunkers_mapping)

    #we will keep all the clunms since this process is simple. We can isntead drop the new cols we create here at the end of the process.
    #cols: 'scenarios', 'economy', 'sectors', 'sub1sectors', 'sub2sectors','sub3sectors', 'sub4sectors', 'fuels', 'subfuels', '1980',...2070, 'Fuel', 'Medium'
    #melt data so date is in one col and values in another
    energy_use_esto_bunkers_tall = pd.melt(energy_use_esto_bunkers, id_vars=['scenarios', 'economy', 'sectors', 'sub1sectors', 'sub2sectors','sub3sectors', 'sub4sectors', 'fuels', 'subfuels', 'Fuel', 'Medium'], var_name='Date', value_name='Value').reset_index(drop=True)
    
    #rename cols:
    energy_use_esto_bunkers_tall.rename({'scenarios':'Scenario', 'economy':'Economy'}, axis=1, inplace=True)
    
    #make Date into int64
    energy_use_esto_bunkers_tall['Date'] = energy_use_esto_bunkers_tall['Date'].astype('int64')
    #make Scenario col value start with capital letter
    energy_use_esto_bunkers_tall['Scenario'] = energy_use_esto_bunkers_tall['Scenario'].str.capitalize()

    return energy_use_esto_bunkers_tall

def extract_bunkers_fuel_share_inputs():
    #load data from vehicle_sales_share_inputs
    
    international_fuel_shares = pd.read_excel('input_data/vehicle_sales_share_inputs.xlsx',sheet_name='international_fuel_shares')    
    international_shares_regions = pd.read_excel('input_data/vehicle_sales_share_inputs.xlsx',sheet_name='international_shares_regions')
    
    international_fuel_shares_r = pd.merge(international_fuel_shares, international_shares_regions, how='left', on='Region')
    
    #drop Region cols
    international_fuel_shares_r = international_fuel_shares_r.drop(columns=['Region'])
    international_fuel_shares_r = international_fuel_shares_r.melt(id_vars=['Economy','Medium', 'Drive', 'Date'], var_name='Scenario', value_name='Share')
    
    return international_fuel_shares_r 
    
def interpolate_bunker_shares(international_bunker_energy_use_inputs,X_ORDER='linear'):
    #mergin the data has given us all teh dates we need to interpoalte for . so drop teh cols we dont need, interpoalte and then join back onto international_bunker_energy_use_inputs.
    international_fuel_shares = international_bunker_energy_use_inputs[['Scenario','Medium', 'Economy', 'Drive', 'Date', 'Share']]
    international_bunker_energy_use_inputs= international_bunker_energy_use_inputs.drop(columns=['Share'])
    
    #order data by year
    international_fuel_shares = international_fuel_shares.sort_values(by=['Date'])
        
    if X_ORDER == 'linear':
        # Do linear interpolation using the 'linear' method
        international_fuel_shares['Share'] = international_fuel_shares.groupby(['Scenario','Medium', 'Economy', 'Drive'], group_keys=False)['Share'].apply(lambda group: group.interpolate(method='linear'))
    else:
        # Do spline interpolation using the specified order
        international_fuel_shares['Share'] = international_fuel_shares.groupby(['Economy','Medium', 'Scenario', 'Drive'])['Share'].apply(lambda group: group.interpolate(method='spline', order=X_ORDER))
    
    #where any values are negatives or na just set them to 0
    international_fuel_shares['Share'] = international_fuel_shares['Share'].fillna(0)
    international_fuel_shares.loc[international_fuel_shares['Share'] < 0, 'Share'] = 0    
    
    #now normalise so that all values for each medium sum to 1 (so ignore drive)
    international_fuel_shares['Share'] = international_fuel_shares.groupby(['Scenario','Medium', 'Economy'])['Share'].apply(lambda x: x/x.sum())
    
    #now join back on 
    international_bunker_energy_use_inputs = pd.merge(international_bunker_energy_use_inputs, international_fuel_shares, how='left', on=['Scenario','Medium', 'Economy', 'Drive', 'Date'])
    return international_fuel_shares


# non_road_energy_use = extract_non_road_energy_use()
# non_road_energy_use_growth_rate = calculate_non_road_energy_use_growth_rate(non_road_energy_use)

def extract_non_road_energy_use():
    #get non road eneryg use projections:
    model_output_non_detailed = pd.read_csv('output_data/model_output/all_economies_{}_{}'.format(config.FILE_DATE_ID, config.model_output_file_name))
    non_road = model_output_non_detailed.loc[model_output_non_detailed['Medium'] != 'road']
    #sum by scenario, date and medium (not by economy so that we can average out domestic variations.. this is international fuel use after all)
    non_road_energy_use = non_road.groupby(['Scenario', 'Date', 'Medium'])['Energy'].sum().reset_index()
    return non_road_energy_use
    
def calculate_non_road_energy_use_growth_rate(non_road_energy_use):  
    #calculate the average growth rate for each medium 
    non_road_energy_use = non_road_energy_use.sort_values(by=['Medium','Scenario',  'Date'])
    non_road_energy_use['Growth Rate'] = non_road_energy_use.groupby(['Scenario', 'Medium'])['Energy'].pct_change()
    #drop non needed cols
    non_road_energy_use_growth_rate = non_road_energy_use[['Medium','Scenario',  'Date', 'Growth Rate']].dropna().drop_duplicates()
    return non_road_energy_use_growth_rate

def check_for_duplicates_in_all_datasets(energy_use_esto_bunkers_tall, international_fuel_shares, non_road_energy_use_growth_rate):
    
    #check for duplicates!
    dupes = energy_use_esto_bunkers_tall[energy_use_esto_bunkers_tall.duplicated(keep=False)]
    if len(dupes) > 0:
        dupes.to_csv('error.csv')
        breakpoint()
        raise Exception(f'There are duplicates in the energy_use_esto data. Please check the data and remove duplicates, {dupes}')
    dupes = international_fuel_shares[international_fuel_shares.duplicated(subset=['Scenario', 'Medium', 'Economy', 'Drive', 'Date'], keep=False)]
    if len(dupes) > 0:
        dupes.to_csv('error.csv')
        breakpoint()
        raise Exception(f'There are duplicates in the international_fuel_shares data. Please check the data and remove duplicates, {dupes}')
    dupes = non_road_energy_use_growth_rate[non_road_energy_use_growth_rate.duplicated(subset=['Scenario', 'Medium',  'Date'], keep=False)]
    if len(dupes) > 0:
        dupes.to_csv('error.csv')
        breakpoint()
        raise Exception(f'There are duplicates in the non_road_energy_use_growth_rate data. Please check the data and remove duplicates, {dupes}')
    
    
def merge_and_format_all_input_data(energy_use_esto_bunkers_tall, international_fuel_shares, non_road_energy_use_growth_rate):
    
    #merge all together beofre checking that it all mathces wat we expect (we will mege in a different order later):
    international_bunker_energy_use_inputs = pd.merge(energy_use_esto_bunkers_tall, international_fuel_shares, how='outer', on=['Medium', 'Economy', 'Scenario', 'Date'])
    international_bunker_energy_use_inputs = pd.merge(international_bunker_energy_use_inputs, non_road_energy_use_growth_rate, how='outer', on=['Medium',  'Scenario', 'Date'])
    
    #keep only data that is between OUTLOOK_BASE_YEAR and GRAPHING_END_YEAR
    international_bunker_energy_use_inputs = international_bunker_energy_use_inputs.loc[(international_bunker_energy_use_inputs['Date'] >= config.OUTLOOK_BASE_YEAR) & (international_bunker_energy_use_inputs['Date'] <= config.GRAPHING_END_YEAR)]
    
    return international_bunker_energy_use_inputs
    
def format_concordances_for_checking():  
    #laod in concordances to help check for any issues:
    model_concordances_user_input_and_growth_rates = pd.read_csv('config/concordances_and_config_data/computer_generated_concordances/{}'.format(config.model_concordances_user_input_and_growth_rates_file_name)) 
    #remove the following cols since we dont need to make sure we have them here: Transport Type	Vehicle Type		Frequency Measure	Unit
    model_concordances_user_input_and_growth_rates = model_concordances_user_input_and_growth_rates.drop(columns=['Transport Type', 'Vehicle Type', 'Frequency', 'Measure', 'Unit']).drop_duplicates()
    #and filter for only medium = air, ship
    model_concordances_user_input_and_growth_rates = model_concordances_user_input_and_growth_rates.loc[model_concordances_user_input_and_growth_rates['Medium'].isin(['air', 'ship'])]
    #and so date is btween OUTLOOK_BASE_YEAR and GRAPHING_END_YEAR
    model_concordances_user_input_and_growth_rates = model_concordances_user_input_and_growth_rates.loc[(model_concordances_user_input_and_growth_rates['Date'] >= config.OUTLOOK_BASE_YEAR) & (model_concordances_user_input_and_growth_rates['Date'] <= config.GRAPHING_END_YEAR)]
    #add ship_other_petroleum_products as a drive for ship. Just grab data for drive = ship_fuel_oil and then change the drive to ship_other_petroleum_products
    ship_other_petroleum_products = model_concordances_user_input_and_growth_rates.loc[model_concordances_user_input_and_growth_rates['Drive'] == 'ship_fuel_oil'].copy()
    ship_other_petroleum_products.Drive  = 'ship_other_petroleum_products'
    model_concordances_user_input_and_growth_rates = pd.concat([model_concordances_user_input_and_growth_rates, ship_other_petroleum_products])
    
    return model_concordances_user_input_and_growth_rates

def check_all_input_data_against_concordances(international_bunker_energy_use_inputs):
    breakpoint()
    model_concordances_user_input_and_growth_rates = format_concordances_for_checking()
    
    #now check that we have all the data we need by checking that all the remainign rows are in the international bunker energy use inputs df:
    check_df = pd.merge(model_concordances_user_input_and_growth_rates, international_bunker_energy_use_inputs, how='outer', on=['Scenario','Medium', 'Economy', 'Drive', 'Date'], indicator=True)
    #find where indicator is not both:
    check_df_errors = check_df.loc[check_df['_merge'] != 'both']
    if len(check_df_errors) > 0:
        breakpoint()
        check_df_errors.to_csv('error.csv')
        raise Exception(f'There are some rows in the model_concordances_user_input_and_growth_rates that are not in the international_bunker_energy_use_inputs df. Please check the data and remove duplicates, {check_df_errors}')

#%%
international_bunker_share_calculation_handler()
#%%