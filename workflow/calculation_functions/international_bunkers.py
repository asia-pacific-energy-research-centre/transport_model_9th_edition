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
    breakpoint()
    #load international bunker data from esto:
    energy_use_esto_bunkers_tall = extract_bunker_data_from_esto()
    #now extract sales/fuel share data:
    international_fuel_shares = extract_bunkers_fuel_share_inputs()
    international_supply_side_fuel_mixing=extract_supply_side_fuel_mixing()
    #calcaulte base year fuel share and fuel mixing. we will concat tehse to the international_fuel_shares and international_supply_side_fuel_mixing dfs:
    
    international_supply_side_fuel_mixing, energy_use_esto_bunkers_tall = calculate_base_year_fuel_mixing(international_supply_side_fuel_mixing, energy_use_esto_bunkers_tall)
    international_fuel_shares = calculate_base_year_fuel_shares(international_fuel_shares, energy_use_esto_bunkers_tall)#potentially need to keep more than just the base year to give the interpolation more data points to project  but we will see how it goes.
    international_fuel_shares = calculate_missing_drive_shares_from_manually_inputted_data(international_fuel_shares)
        
    #calcualte avergae growth rate from domestic non road energy use:
    non_road_energy_use = extract_non_road_energy_use()#, drive_to_fuel_mapping
    non_road_energy_use_growth_rate = calculate_non_road_energy_use_growth_rate(non_road_energy_use)
    #check for duplcaites: 
    check_for_duplicates_in_all_datasets(energy_use_esto_bunkers_tall, international_fuel_shares, non_road_energy_use_growth_rate, international_supply_side_fuel_mixing)
    #merge all data
    breakpoint()
    international_bunker_energy_use_inputs = merge_and_format_all_input_data(energy_use_esto_bunkers_tall, international_fuel_shares, non_road_energy_use_growth_rate)#y doies international_fuel_shares have nas in drive
    international_supply_side_fuel_mixing = check_and_fill_missing_fuel_mixing_dates(international_bunker_energy_use_inputs,  international_supply_side_fuel_mixing)
    #interpolate the fuel shares to get a value for every year:
    international_bunker_energy_use_inputs, international_supply_side_fuel_mixing = interpolate_bunker_shares_and_mixing(international_bunker_energy_use_inputs, international_supply_side_fuel_mixing)
    breakpoint()
    #and check it all matches wat we expect (we wont bother with international_supply_side_fuel_mixing since we checked it earlier in check_and_fill_missing_fuel_mixing_dates)
    check_all_input_data_against_concordances(international_bunker_energy_use_inputs)
    
    #calcaulte new energy use for each medium, and drive type:
    new_energy_df = project_total_bunkers_energy_use(international_bunker_energy_use_inputs)
    breakpoint()
            
    # then join to the supply side fuel mixing data and calculate the new fuel mix for any that have supply side fuel mixing:
    new_energy_df_mixed = apply_fuel_mixing_to_energy(new_energy_df, international_supply_side_fuel_mixing)
    breakpoint()
    #all done i thnk (:
            
    
# then split it into its drives using the fuel shares
def split_energy_into_drives_using_fuel_shares(international_bunker_energy_use_inputs):
    #split the energy into the drives using the fuel shares
    international_bunker_energy_use_inputs['Value'] = international_bunker_energy_use_inputs['Value'] * international_bunker_energy_use_inputs['Share']
    return international_bunker_energy_use_inputs

def apply_fuel_mixing_to_energy(international_bunker_energy_use_inputs, international_supply_side_fuel_mixing):
    #join the two, times energy by mix to get the energy for the new fuel, minus that from energy to get the energy for the old fuel then seperate the dfs and concat them:
    mixing_international_bunker_energy_use_inputs = international_bunker_energy_use_inputs.copy()
    
    mixing_international_bunker_energy_use_inputs = pd.merge(mixing_international_bunker_energy_use_inputs, international_supply_side_fuel_mixing, how='left', on=['Scenario','Medium', 'Economy', 'Drive', 'Date', 'Fuel'])
    
    mixing_international_bunker_energy_use_inputs['Energy_new'] = mixing_international_bunker_energy_use_inputs['Value'] * mixing_international_bunker_energy_use_inputs['Mix']
    #now we need to subtract the new energy from the old energy to get the energy for the old fuel:
    mixing_international_bunker_energy_use_inputs['Value'] = mixing_international_bunker_energy_use_inputs['Value'] - mixing_international_bunker_energy_use_inputs['Energy_new']
    
    new_data = mixing_international_bunker_energy_use_inputs[['Scenario','Medium', 'Economy', 'Drive', 'Date', 'New_fuel', 'Energy_new']].copy()
    new_data.rename({'New_fuel': 'Fuel', 'Energy_new': 'Value'}, axis=1, inplace=True)
    mixing_international_bunker_energy_use_inputs = mixing_international_bunker_energy_use_inputs[['Scenario','Medium', 'Economy', 'Drive', 'Date', 'Fuel', 'Value']].copy()
    
    #cocnat
    mixing_international_bunker_energy_use_inputs = pd.concat([mixing_international_bunker_energy_use_inputs, new_data])
    
    #double check that total energy use is the same as before:
    if abs(mixing_international_bunker_energy_use_inputs['Value'].sum() - international_bunker_energy_use_inputs['Value'].sum()) > 0.00000000001:
        mixing_international_bunker_energy_use_inputs.to_csv('error_{}.csv'.format(datetime.datetime.now().strftime("%Y%m%d-%H%M%S")))
        breakpoint()
        raise Exception(f'The total energy use for the international_bunker_energy_use_inputs df has changed after applying fuel mixing. Please check the data and remove duplicates, {mixing_international_bunker_energy_use_inputs}')
    
    return mixing_international_bunker_energy_use_inputs

def extract_bunker_data_from_esto():
        
    #load the 9th data
    date_id = utility_functions.get_latest_date_for_data_file('input_data/9th_model_inputs', 'model_df_wide_')
    energy_use_esto = pd.read_csv(f'input_data/9th_model_inputs/model_df_wide_{date_id}.csv')
    
    #load the config\concordances_and_config_data\international_bunkers_mapping.csv
    international_bunkers_mapping = pd.read_csv('config/concordances_and_config_data/international_bunkers_mapping.csv')#cols = Medium	Drive	Fuel	Supply_side_fuel_mixing
    #note that Supply_side_fuel_mixing is a boolean

    #TEMP replace 15_PHL with 15_RP and 17_SGP with 17_SIN in the eocnomy col. make sure to let user know they can klet hyguga know:
    if len(energy_use_esto.loc[energy_use_esto['economy'].isin(['15_PHL', '17_SGP'])]) > 0:
        print('There are some economies in the esto data that need to be replaced. Please let Hyuga know')
        energy_use_esto['economy'] = energy_use_esto['economy'].replace({'15_PHL': '15_RP', '17_SGP': '17_SIN'})
    #filter for only the Economys. So use config.economy_scenario_concordance.Economy.unique.to_list() to filter. this is to rmeove the regions
    energy_use_esto = energy_use_esto.loc[energy_use_esto['economy'].isin(config.economy_scenario_concordance.Economy.unique())]
    #extract only bunker data. that is data for 04_international_marine_bunkers, 05_international_aviation_bunkers where aviation is air and marine is ship mediums
    energy_use_esto_bunkers = energy_use_esto.loc[energy_use_esto['sectors'].isin(['04_international_marine_bunkers', '05_international_aviation_bunkers'])]
    
    #drop where subfuels is x. tehese are aggregations.
    energy_use_esto_bunkers = energy_use_esto_bunkers.loc[energy_use_esto_bunkers['subfuels'] != 'x']

    #map the subfuels to the fuel types. 
    energy_use_esto_bunkers['Fuel'] =energy_use_esto_bunkers['subfuels'].map(config.temp_esto_subfuels_to_new_subfuels_mapping)
    #map 07_x_other_petroleum_products to 07_x_other_petroleum_products#this is not used in the transport system otehrwise so is not in the mapping
    energy_use_esto_bunkers.loc[energy_use_esto_bunkers['subfuels'] == '07_x_other_petroleum_products', 'Fuel'] = '07_x_other_petroleum_products'
    #map the sectors to medium:
    bunkers_mapping = {'04_international_marine_bunkers': 'ship', '05_international_aviation_bunkers': 'air'}
    energy_use_esto_bunkers['Medium'] = energy_use_esto_bunkers['sectors'].map(bunkers_mapping)
    
    #we will keep all the clunms since this process is simple. We can isntead drop the new cols we create here at the end of the process.
    #cols: 'scenarios', 'economy', 'sectors', 'sub1sectors', 'sub2sectors','sub3sectors', 'sub4sectors', 'fuels', 'subfuels', '1980',...2070, 'Fuel', 'Medium'
    #melt data so date is in one col and values in another
    energy_use_esto_bunkers_tall = pd.melt(energy_use_esto_bunkers, id_vars=['scenarios', 'economy', 'sectors', 'sub1sectors', 'sub2sectors','sub3sectors', 'sub4sectors', 'fuels', 'subfuels', 'Fuel', 'Medium'], var_name='Date', value_name='Value').reset_index(drop=True)
        
    #merge onto the mapping to get the drive type and whetehr or not the rows (eventual) energy use is through supply side fuel mixing:
    energy_use_esto_bunkers_tall = pd.merge(energy_use_esto_bunkers_tall, international_bunkers_mapping, how='left', on=['Medium', 'Fuel'])
    
    # #where Value is 0 or null, and Fuel is 16_09_other_sources, drop the row. this is because this fuel is not used ANYMORE for non road but is used for road, thats why it got into the mapping. So jsut drop it (unless its not 0)
    # energy_use_esto_bunkers_tall = energy_use_esto_bunkers_tall.loc[~((energy_use_esto_bunkers_tall['Value'] == 0) & (energy_use_esto_bunkers_tall['Fuel'] == '16_09_other_sources'))]
    # energy_use_esto_bunkers_tall = energy_use_esto_bunkers_tall.loc[~((energy_use_esto_bunkers_tall['Value'].isnull()) & (energy_use_esto_bunkers_tall['Fuel'] == '16_09_other_sources'))]
    
    #find if there are any fuels that we need to map to new Drives. these must have Value >0
    other_fuels = energy_use_esto_bunkers_tall.loc[(energy_use_esto_bunkers_tall['Drive'].isnull()) & (energy_use_esto_bunkers_tall['Value'] > 0)]
    if len(other_fuels) > 0:
        other_fuels.to_csv('error_{}.csv'.format(datetime.datetime.now().strftime("%Y%m%d-%H%M%S")))
        breakpoint()
        raise Exception(f'There are some fuels in the esto bunkers data that do not have drives mapped. Please check the data and add these to the mapping file, {other_fuels}')
    else:
        #drop where Drive is null
        energy_use_esto_bunkers_tall = energy_use_esto_bunkers_tall.loc[energy_use_esto_bunkers_tall['Drive'].notnull()]

    #rename cols:
    energy_use_esto_bunkers_tall.rename({'scenarios':'Scenario', 'economy':'Economy'}, axis=1, inplace=True)
    
    #make Date into int64
    energy_use_esto_bunkers_tall['Date'] = energy_use_esto_bunkers_tall['Date'].astype('int64')
    
    #make Scenario col value start with capital letter
    energy_use_esto_bunkers_tall['Scenario'] = energy_use_esto_bunkers_tall['Scenario'].str.capitalize()

    #make Value positive since we are treatiung it like enegry use. we can make it negative later on:
    energy_use_esto_bunkers_tall['Value'] = energy_use_esto_bunkers_tall['Value'].abs()
    #and set any nas to 0:
    energy_use_esto_bunkers_tall['Value'] = energy_use_esto_bunkers_tall['Value'].fillna(0)
    
    return energy_use_esto_bunkers_tall

def extract_supply_side_fuel_mixing():
    international_supply_side_fuel_mixing = pd.read_excel('input_data/fuel_mixing_assumptions.xlsx',sheet_name='international_supply_side')
    regions_mapping = pd.read_excel('input_data/fuel_mixing_assumptions.xlsx',sheet_name='int_regions')
    #map economy to region
    international_supply_side_fuel_mixing = pd.merge(international_supply_side_fuel_mixing, regions_mapping, how='left', on='Region')
    international_supply_side_fuel_mixing = international_supply_side_fuel_mixing.drop(columns=['Region'])
    
    international_supply_side_fuel_mixing = international_supply_side_fuel_mixing.melt(id_vars=['Economy','Medium', 'Drive', 'Date', 'Fuel', 'New_fuel'], var_name='Scenario', value_name='Mix')
    
    return international_supply_side_fuel_mixing
    
    
def extract_bunkers_fuel_share_inputs():
    #load data from vehicle_sales_share_inputs
    
    international_fuel_shares = pd.read_excel('input_data/vehicle_sales_share_inputs.xlsx',sheet_name='international_fuel_shares')    
    international_shares_regions = pd.read_excel('input_data/vehicle_sales_share_inputs.xlsx',sheet_name='international_shares_regions')
    
    international_fuel_shares_r = pd.merge(international_fuel_shares, international_shares_regions, how='left', on='Region')
    
    #drop Region cols
    international_fuel_shares_r = international_fuel_shares_r.drop(columns=['Region'])
    international_fuel_shares_r = international_fuel_shares_r.melt(id_vars=['Economy','Medium', 'Drive', 'Date'], var_name='Scenario', value_name='Share')
    #drop any Share values that are 'Will make up the rest'
    international_fuel_shares_r = international_fuel_shares_r.loc[international_fuel_shares_r['Share'] != 'Will make up the rest']
    
    return international_fuel_shares_r 
    
def interpolate_bunker_shares_and_mixing(international_bunker_energy_use_inputs,international_supply_side_fuel_mixing, X_ORDER='linear'):
    #mergin the data has given us all teh dates we need to interpoalte for . so drop teh cols we dont need, interpoalte and then join back onto international_bunker_energy_use_inputs.
    international_fuel_shares = international_bunker_energy_use_inputs[['Scenario','Medium', 'Economy', 'Drive', 'Date', 'Share']].copy()
    international_bunker_energy_use_inputs= international_bunker_energy_use_inputs.drop(columns=['Share'])
    
    #order data by year
    international_fuel_shares = international_fuel_shares.sort_values(by=['Date'])
    international_supply_side_fuel_mixing = international_supply_side_fuel_mixing.sort_values(by=['Date'])
        
    if X_ORDER == 'linear':
        # Do linear interpolation using the 'linear' method
        international_fuel_shares['Share'] = international_fuel_shares.groupby(['Scenario','Medium', 'Economy', 'Drive'], group_keys=False)['Share'].apply(lambda group: group.interpolate(method='linear'))
        international_supply_side_fuel_mixing['Mix'] = international_supply_side_fuel_mixing.groupby(['Scenario','Medium', 'Economy', 'Drive', 'Fuel', 'New_fuel'], group_keys=False)['Mix'].apply(lambda group: group.interpolate(method='linear'))
    else:
        # Do spline interpolation using the specified order
        international_fuel_shares['Share'] = international_fuel_shares.groupby(['Economy','Medium', 'Scenario', 'Drive'])['Share'].apply(lambda group: group.interpolate(method='spline', order=X_ORDER))
        international_supply_side_fuel_mixing['Mix'] = international_supply_side_fuel_mixing.groupby(['Economy','Medium', 'Scenario', 'Drive', 'Fuel', 'New_fuel'])['Mix'].apply(lambda group: group.interpolate(method='spline', order=X_ORDER))
    
    #where any values are negatives or na just set them to 0
    international_fuel_shares['Share'] = international_fuel_shares['Share'].fillna(0)
    international_fuel_shares.loc[international_fuel_shares['Share'] < 0, 'Share'] = 0    
    international_supply_side_fuel_mixing['Mix'] = international_supply_side_fuel_mixing['Mix'].fillna(0)
    international_supply_side_fuel_mixing.loc[international_supply_side_fuel_mixing['Mix'] < 0, 'Mix'] = 0
    
    #now normalise so that all values for each medium sum to 1 (so ignore drive)
    international_fuel_shares['Share'] = international_fuel_shares.groupby(['Scenario','Medium', 'Economy'])['Share'].apply(lambda x: x/x.sum())
    
    #now join back on 
    international_bunker_energy_use_inputs = pd.merge(international_bunker_energy_use_inputs, international_fuel_shares, how='left', on=['Scenario','Medium', 'Economy', 'Drive', 'Date'])

    return international_bunker_energy_use_inputs, international_supply_side_fuel_mixing

def extract_non_road_energy_use():
    #get non road eneryg use projections. this will be used to get the growth rate for energy use in the whole of apec
    model_output_all_with_fuels = pd.read_csv('output_data/model_output_with_fuels/all_economies_NON_ROAD_DETAILED_20230802_model_output20230802.csv')
    # model_output_all_with_fuels = pd.read_csv('output_data/model_output_with_fuels/all_economies_NON_ROAD_DETAILED_{}_{}'.format(config.FILE_DATE_ID, config.model_output_file_name))
    non_road = model_output_all_with_fuels.loc[model_output_all_with_fuels['Medium'].isin(['air', 'ship'])]
    #drop electric planes and ships
    non_road = non_road.loc[~((non_road['Drive'] == 'air_electric') | (non_road['Drive'] == 'ship_electric'))]
    #sum by scenario, date and medium (not by economy so that we can average out domestic variations.. this is international fuel use after all)
    non_road_energy_use = non_road.groupby(['Scenario', 'Date', 'Medium'])['Energy'].sum().reset_index()
    
    # #and extract Drive and Fuel, Medium cols for mapping:
    # drive_to_fuel_mapping = non_road[['Drive', 'Medium', 'Fuel']].drop_duplicates()
    # #add in the mapping for ship_other_petroleum_products
    # drive_to_fuel_mapping = drive_to_fuel_mapping.append({'Drive': 'ship_other_petroleum_products', 'Fuel': '07_x_other_petroleum_products', 'Medium': 'ship'}, ignore_index=True)
    return non_road_energy_use#, drive_to_fuel_mapping
    
def calculate_non_road_energy_use_growth_rate(non_road_energy_use):  
    #calculate the average growth rate for each medium 
    non_road_energy_use = non_road_energy_use.sort_values(by=['Medium','Scenario',  'Date'])
    non_road_energy_use['Growth Rate'] = non_road_energy_use.groupby(['Scenario', 'Medium'])['Energy'].pct_change()
    #drop non needed cols
    non_road_energy_use_growth_rate = non_road_energy_use[['Medium','Scenario',  'Date', 'Growth Rate']].dropna().drop_duplicates()
    return non_road_energy_use_growth_rate

def check_for_duplicates_in_all_datasets(energy_use_esto_bunkers_tall, international_fuel_shares, non_road_energy_use_growth_rate, international_supply_side_fuel_mixing):
    
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
    dupes = international_supply_side_fuel_mixing[international_supply_side_fuel_mixing.duplicated(subset=['Scenario', 'Medium', 'Economy', 'Drive', 'Date', 'Fuel', 'New_fuel'], keep=False)]
    if len(dupes) > 0:
        dupes.to_csv('error.csv')
        breakpoint()
        raise Exception(f'There are duplicates in the international_supply_side_fuel_mixing data. Please check the data and remove duplicates, {dupes}')
    
def merge_and_format_all_input_data(energy_use_esto_bunkers_tall, international_fuel_shares, non_road_energy_use_growth_rate):#, drive_to_fuel_mapping):
    # #merge esto data with the drive to fuel mapping:
    # energy_use_esto_bunkers_tall = pd.merge(energy_use_esto_bunkers_tall, drive_to_fuel_mapping, how='left', on=['Fuel', 'Medium'])
    # #check for any nulls in Drive col:
    # nulls = energy_use_esto_bunkers_tall.loc[energy_use_esto_bunkers_tall['Drive'].isnull()]
    # if len(nulls) > 0:
    #     nulls.to_csv('error.csv')
    #     breakpoint()
    #     raise Exception(f'There are nulls in the Drive col in the energy_use_esto_bunkers_tall data. Please check the data and remove nulls, {nulls}')
        
    #merge all together beofre checking that it all mathces wat we expect (we will mege in a different order later):
    international_bunker_energy_use_inputs = pd.merge(energy_use_esto_bunkers_tall, international_fuel_shares, how='outer', on=['Medium', 'Economy', 'Scenario','Drive', 'Date'])
    international_bunker_energy_use_inputs = pd.merge(international_bunker_energy_use_inputs, non_road_energy_use_growth_rate, how='outer', on=['Medium',  'Scenario', 'Date'])
    #keep only data that is between OUTLOOK_BASE_YEAR and GRAPHING_END_YEAR
    international_bunker_energy_use_inputs = international_bunker_energy_use_inputs.loc[(international_bunker_energy_use_inputs['Date'] >= config.OUTLOOK_BASE_YEAR) & (international_bunker_energy_use_inputs['Date'] <= config.GRAPHING_END_YEAR)]
    
    
    #dont check for nas yet. we know that we have nas in the fuel share data and we will interpolate them later. We could have nas in the esto data too. we will check for them later.
    
    return international_bunker_energy_use_inputs
    
def check_and_fill_missing_fuel_mixing_dates(international_bunker_energy_use_inputs, international_supply_side_fuel_mixing):
    #we wont merge international_supply_side_fuel_mixing on international_supply_side_fuel_mixing because if there are two new fuels for a fuel, then it would create duplicates. instead we will double check that all the Fuels, Drive, Medium combos in international_supply_side_fuel_mixing are in the international_bunker_energy_use_inputs df. And then we will join the international_supply_side_fuel_mixing onto the Date col in international_bunker_energy_use_inputs, so we have all required dates, so we can interpoalte the mixing data.
    unique_fuel_drive_medium_combos = international_supply_side_fuel_mixing[['Fuel', 'Drive', 'Medium']].drop_duplicates()
    combos = unique_fuel_drive_medium_combos.merge(international_bunker_energy_use_inputs[['Fuel', 'Drive', 'Medium', 'Date']].drop_duplicates(), how = 'outer', on=['Fuel', 'Drive', 'Medium'], indicator=True)
    left_only = combos.loc[combos['_merge'] == 'left_only']
    if len(left_only) > 0:
        left_only.to_csv('error_{}.csv'.format(datetime.datetime.now().strftime("%Y%m%d-%H%M%S")))
        breakpoint()
        raise Exception(f'There are some rows in the international_supply_side_fuel_mixing that are not in the international_bunker_energy_use_inputs df. Please check the data and remove duplicates, {left_only}')
    #and finally join on teh missing dates:
    #firs grab the dates we need as a df:
    dates = international_bunker_energy_use_inputs[['Date']].drop_duplicates()
    #then merge it onto a version of international_supply_side_fuel_mixing wihtout the Date or Mix cols:
    dates = pd.merge(dates, international_supply_side_fuel_mixing[['Scenario','Medium', 'Economy', 'Drive', 'Fuel', 'New_fuel']], how='cross')
    #now merge this onto the international_supply_side_fuel_mixing to fill in data where we have it and na where we dont:
    international_supply_side_fuel_mixing = pd.merge(dates, international_supply_side_fuel_mixing, how='left', on=['Date', 'Scenario','Medium', 'Economy', 'Drive', 'Fuel', 'New_fuel'])
    
    return international_supply_side_fuel_mixing

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
    # we also need to remove electric planes and ships from bunkers because these arent expected to ever be recorded in there:
    model_concordances_user_input_and_growth_rates = model_concordances_user_input_and_growth_rates.loc[~((model_concordances_user_input_and_growth_rates['Drive'] == 'air_electric') | (model_concordances_user_input_and_growth_rates['Drive'] == 'ship_electric'))]
    return model_concordances_user_input_and_growth_rates

def check_all_input_data_against_concordances(international_bunker_energy_use_inputs):
    model_concordances_user_input_and_growth_rates = format_concordances_for_checking()
    
    #now check that we have all the data we need by checking that all the remainign rows are in the international bunker energy use inputs df:
    check_df = pd.merge(model_concordances_user_input_and_growth_rates, international_bunker_energy_use_inputs, how='outer', on=['Scenario','Medium', 'Economy', 'Drive', 'Date'], indicator=True)
    #find where indicator is not both:
    check_df_errors = check_df.loc[check_df['_merge'] != 'both']
    if len(check_df_errors) > 0:
        check_df_errors.to_csv('error_{}.csv'.format(datetime.datetime.now().strftime("%Y%m%d-%H%M%S")))
        breakpoint()
        raise Exception(f'There are some rows in the model_concordances_user_input_and_growth_rates that are not in the international_bunker_energy_use_inputs df. Please check the data and remove duplicates, {check_df_errors}')

    check_df.drop(columns=['_merge'], inplace=True)
    #check for dupes:
    cols = check_df.columns.to_list()
    cols.remove('Value')
    cols.remove('Share')
    cols.remove('Growth Rate')
    dupes = international_bunker_energy_use_inputs[international_bunker_energy_use_inputs.duplicated(subset=cols, keep=False)]
    if len(dupes) > 0:
        dupes.to_csv('error_{}.csv'.format(datetime.datetime.now().strftime("%Y%m%d-%H%M%S")))
        breakpoint()
        raise Exception(f'There are some duplicates in the international_bunker_energy_use_inputs df. Please check the data and remove duplicates, {dupes}')
    
    #now we have made sure we have no missing data or dupes we can begin calculating!
    

def project_total_bunkers_energy_use(international_bunker_energy_use_inputs):
    #first sum energy use for each medium
    total_energy = international_bunker_energy_use_inputs.groupby(['Scenario', 'Economy', 'Date', 'Drive', 'Fuel', 'Medium'])['Value'].sum().reset_index().copy()
    
    new_energy_df = pd.DataFrame()
    #itl be easiest to just loop through the years to apply growth:
    base_year_energy = total_energy.loc[international_bunker_energy_use_inputs['Date'] == config.OUTLOOK_BASE_YEAR].copy()
    new_energy_df = pd.concat([new_energy_df, base_year_energy])
    for year in range(config.OUTLOOK_BASE_YEAR+1, config.GRAPHING_END_YEAR+1):
        previous_year_energy = total_energy.loc[total_energy['Date'] == year-1].copy()
        #join on the growth rate for that year:
        growth = international_bunker_energy_use_inputs.loc[international_bunker_energy_use_inputs['Date'] == year, ['Scenario', 'Economy', 'Date', 'Medium', 'Growth Rate']].copy()
        current_year_energy = pd.merge(previous_year_energy, growth, how='left', on=['Scenario', 'Economy', 'Date', 'Medium']).copy()
        current_year_energy['Total Energy'] = current_year_energy['Value'] * (1 + current_year_energy['Growth Rate'])
        new_energy_df = pd.concat([new_energy_df, current_year_energy])
    
    return new_energy_df

def calculate_base_year_fuel_mixing(international_supply_side_fuel_mixing, energy_use_esto_bunkers_tall):
    #firstly, seperate data into fuels that are mixed into other fuels and those that are not. do this by grabbing fuels that are in New_fuel col in international_supply_side_fuel_mixing:
    energy_use_esto_bunkers_tall_base_year = energy_use_esto_bunkers_tall.loc[energy_use_esto_bunkers_tall['Date'] == config.OUTLOOK_BASE_YEAR].copy()
    
    fuels_added_in_mixing = energy_use_esto_bunkers_tall_base_year.loc[energy_use_esto_bunkers_tall_base_year.Supply_side_fuel_mixing].copy()
    original_fuels_in_mixing = energy_use_esto_bunkers_tall_base_year.loc[energy_use_esto_bunkers_tall_base_year.Supply_side_fuel_mixing != True].copy()
    #join the two on the medium and drive cols:
    fuel_mixing_base_year_original = pd.merge(original_fuels_in_mixing, fuels_added_in_mixing, how='outer', on=['Scenario','Date', 'Medium', 'Drive', 'Economy'], indicator=True)
    #drop left_only cols
    fuel_mixing_base_year = fuel_mixing_base_year_original.loc[fuel_mixing_base_year_original['_merge'] != 'left_only'].copy()
    #if theres any right only cols, raise an error
    right_only = fuel_mixing_base_year_original.loc[fuel_mixing_base_year_original['_merge'] == 'right_only'].copy()
    if len(right_only) > 0:
        print(right_only)
        raise Exception('There are some fuels in the fuel mixing data that are not in the esto data. Please check the data and add these to the mapping file')
    #drop _merge col
    fuel_mixing_base_year = fuel_mixing_base_year.drop(columns=['_merge'])
    #rename cols so Fuel_x is Fuel and Fuel_y is New_fuel
    fuel_mixing_base_year.rename({'Fuel_x': 'Fuel', 'Fuel_y': 'New_fuel'}, axis=1, inplace=True)
    #then calcualte fuel mix as Value_y / (Value_x + Value_y)
    fuel_mixing_base_year['Mix'] = fuel_mixing_base_year['Value_y'] / (fuel_mixing_base_year['Value_x'] + fuel_mixing_base_year['Value_y'])
    #drop any nulls in Mix col
    fuel_mixing_base_year = fuel_mixing_base_year.loc[fuel_mixing_base_year['Mix'].notnull()]
    #keep only the cols we need:
    cols = international_supply_side_fuel_mixing.columns.tolist()
    fuel_mixing_base_year = fuel_mixing_base_year[cols]
    #now concat to international_supply_side_fuel_mixing after removing those dates form international_supply_side_fuel_mixing
    international_supply_side_fuel_mixing = international_supply_side_fuel_mixing.loc[~international_supply_side_fuel_mixing['Date'].isin(fuel_mixing_base_year['Date'].unique().tolist())]
    international_supply_side_fuel_mixing = pd.concat([international_supply_side_fuel_mixing, fuel_mixing_base_year])
    
    #now we have the base year fuel mixing!
    
    #and now for the new fuels we actually want to set them to equal the origianl fuel in energy_use_esto_bunkers_tall_base_year. this is so that when we calcualte the fuel shares it will consider the indirect fact that these fuels arelater mixed in!
    fuel_mixing_base_year_original['Value_x'] = fuel_mixing_base_year_original['Value_x'] + fuel_mixing_base_year_original['Value_y'].replace(np.nan, 0)
    #drop any cols ending with _y and also 'New_fuel', '_merge'
    fuel_mixing_base_year_original = fuel_mixing_base_year_original.drop(columns=[col for col in fuel_mixing_base_year_original.columns if col.endswith('_y')]+[ '_merge'])
    #set all x cols to just be the x cols
    fuel_mixing_base_year_original.rename({col: col.replace('_x', '') for col in fuel_mixing_base_year_original.columns if col.endswith('_x')}, axis=1, inplace=True)
    #to check that this worked, double check that the sum of Value is equal to the sum of Value in energy_use_esto_bunkers_tall_base_year
    if abs(fuel_mixing_base_year_original['Value'].sum() - energy_use_esto_bunkers_tall_base_year['Value'].sum()) -1 > 0.0000001:
        breakpoint()
        raise Exception('The sum of Value in fuel_mixing_base_year_original is not equal to the sum of Value in energy_use_esto_bunkers_tall_base_year. Please check the data. diff is {}'.format(abs(fuel_mixing_base_year_original['Value'].sum() - energy_use_esto_bunkers_tall_base_year['Value'].sum())))
    return international_supply_side_fuel_mixing, fuel_mixing_base_year_original


def calculate_base_year_fuel_shares(international_fuel_shares, energy_use_esto_bunkers_tall):
    #we need to calculate the base year fuel shares. we will do this by taking the fuel use for each medium and drive type, and dividing it by the total fuel use for that medium and drive type. 
    fuel_shares = energy_use_esto_bunkers_tall.copy()
    fuel_shares['Total fuel use'] = fuel_shares.groupby(['Economy', 'Medium', 'Drive', 'Date'])['Value'].transform('sum')
    
    #now divide the Value by the Total fuel use to get the share:
    fuel_shares['Share'] = fuel_shares['Value'] / fuel_shares['Total fuel use']
    
    #grab only the cols we need. that is the cols that are in international_fuel_shares
    cols = international_fuel_shares.columns.tolist()
    fuel_shares = fuel_shares[cols]
    
    #now look at attaching it to the international_fuel_shares df. 
    international_fuel_shares = international_fuel_shares.loc[~international_fuel_shares['Date'].isin(fuel_shares['Date'].unique().tolist())]
    international_fuel_shares = pd.concat([international_fuel_shares, fuel_shares])

    return international_fuel_shares
    

def calculate_missing_drive_shares_from_manually_inputted_data(international_fuel_shares, YEARS_TO_KEEP_AFTER_BASE_YEAR=5):
    #this process is also done in the create_vehicle_sales_sahre_scrip for non bunkers data.
    #Since we only take data from the drives that are most important to specify shares for, we need to fill in any leftover shares such that the sum of shares for each year adds to 1. for example if we ahve set the manually inputted sshare for electricity such that it is expected to ake up 0.5 of the market in 2030, then we need to set the remaining 0.5 to be split between the other drives. this split will be determined by the base years splits. so if the base year had 0.5 cng and 0.5 diesel, then we will set the remaining 0.5 to be split 0.25 cng and 0.25 diesel.
    
    #but important to note that the data that we use for the base year will not include any (medium, drive) pairs that are in the manually inputted data. this si to prevent double counting them. 
    #Note that it has a little weakness where the user needs to make sure that for every date that they record a drive share in teh manually inputted data, they must record the drive share forf all other shares they have already been reocrding for that medium, drive pair. otherwise, those missing drives will have their shares filled in using the drives from the base year data. then when wqe do interpolation and normalisation, it will result in the shares for that missing drive being lower than what the user was probably intending. eg. if user reocrded shares constasnt in 2027, and 2029 for electricity (0.5) and phev (0.25), and then in 2028 they only recorded shares for electricity(0.5) then the shares for phev in 2028 will probably be lower than 0.25 as the base year data will be used to fill in the missing shares, then in normalisation, the shares will be normalised to 1, so the shares for phev in 2028 will be lower than 0.25, even though they were still interpoalted before nomralisation.
    
    fuel_share_BASE_YEAR = international_fuel_shares.loc[international_fuel_shares['Date']==config.DEFAULT_BASE_YEAR]
    fuel_share_manual_input = international_fuel_shares.loc[international_fuel_shares['Date']>config.DEFAULT_BASE_YEAR+YEARS_TO_KEEP_AFTER_BASE_YEAR].dropna(subset=['Share'])
    #find unique combiantions of medium, drive:
    combos = fuel_share_manual_input[['Medium', 'Drive']].drop_duplicates()
    #drop the combinations in fuel_share_manual_input from fuel_share_BASE_YEAR
    fuel_share_BASE_YEAR = fuel_share_BASE_YEAR[~fuel_share_BASE_YEAR[['Medium', 'Drive']].apply(tuple,1).isin(combos[['Medium', 'Drive']].apply(tuple,1))]
    #set nas in drive share to 0
    fuel_share_BASE_YEAR[ 'Share'] = fuel_share_BASE_YEAR[ 'Share'].fillna(0)
    #find the normalised shares for the available data in the base year data
    fuel_share_BASE_YEAR['Share'] = fuel_share_BASE_YEAR.groupby(['Economy', 'Scenario','Medium'])['Share'].transform(lambda x: x/x.sum())
    #set nas in drive share to 0
    fuel_share_BASE_YEAR[ 'Share'] = fuel_share_BASE_YEAR[ 'Share'].fillna(0)
    #now get sum of manually inputted shares for each year
    fuel_share_manual_input_sum = fuel_share_manual_input.groupby(['Economy', 'Scenario', 'Medium', 'Date'])['Share'].sum().reset_index()
    #1 minus it
    fuel_share_manual_input_sum['Share_remainder'] = 1 - fuel_share_manual_input_sum['Share']
    #drop drive share
    fuel_share_manual_input_sum = fuel_share_manual_input_sum.drop(columns=['Share'])
    #chcke for any values les than 0
    if fuel_share_manual_input_sum['Share_remainder'].min() < 0:
        #show them and raise
        print(fuel_share_manual_input_sum.loc[fuel_share_manual_input_sum['Share_remainder']<0])
        raise ValueError('Drive share remainder is less than 0')
    #join this to the base year data using right join
    missing_fuel_shares = fuel_share_BASE_YEAR[['Economy', 'Scenario','Medium','Drive','Share']].merge(fuel_share_manual_input_sum, on=['Economy', 'Scenario', 'Medium'], how='right')
    breakpoint()#check that this repicated rows wgere we had two new drives for the same medium infuel_share_BASE_YEAR that we were trying to add into fuel_share_manual_input_sum
    #times the base year data by the 1-x
    missing_fuel_shares['Share'] = missing_fuel_shares['Share'] * missing_fuel_shares['Share_remainder']

    missing_fuel_shares = missing_fuel_shares.drop(columns=['Share_remainder'])
    #now we need to insert these rows into the  international_fuel_shares. since its jsut a df of the manually inputted data right now we can jsut concat them together
    international_fuel_shares = pd.concat([international_fuel_shares, missing_fuel_shares])
    
    return international_fuel_shares
        
#%%
international_bunker_share_calculation_handler()
#%%