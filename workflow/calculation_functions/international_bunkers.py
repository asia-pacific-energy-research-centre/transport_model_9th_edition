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
    
def international_bunker_share_calculation_handler(turnover_rate=0.1):
    config.FILE_DATE_ID = '20230803'
    config.model_output_file_name = 'model_output20230803.csv'
    #load international bunker data from esto:
    energy_use_esto_bunkers_tall, energy_use_esto_mapping = extract_bunker_data_from_esto()
    #now extract sales/fuel share data:
    international_fuel_shares = extract_bunkers_fuel_share_inputs()
    international_supply_side_fuel_mixing=extract_supply_side_fuel_mixing()
    #calcaulte base year fuel share and fuel mixing. we will concat tehse to the international_fuel_shares and international_supply_side_fuel_mixing dfs:
    international_supply_side_fuel_mixing, energy_use_esto_bunkers_tall = calculate_base_year_fuel_mixing(international_supply_side_fuel_mixing, energy_use_esto_bunkers_tall)
    international_fuel_shares = calculate_base_year_fuel_shares(international_fuel_shares, energy_use_esto_bunkers_tall)#potentially need to keep more than just the base year to give the interpolation more data points to project  but we will see how it goes.
    international_fuel_shares = calculate_missing_drive_shares_from_manually_inputted_data(international_fuel_shares)
        
    #calcualte avergae growth rate from domestic non road energy use:
    non_road_activity, non_road_intensity = extract_non_road_modelled_data()#, drive_to_fuel_mapping
    non_road_activity_growth_rate = calculate_non_road_activity_growth_rate(non_road_activity)
    #check for duplcaites: 
    check_for_duplicates_in_all_datasets(energy_use_esto_bunkers_tall, international_fuel_shares, non_road_activity_growth_rate, non_road_intensity, international_supply_side_fuel_mixing)
    #merge all data
    international_bunker_inputs = merge_and_format_all_input_data(energy_use_esto_bunkers_tall, international_fuel_shares, non_road_activity_growth_rate, non_road_intensity)#y doies international_fuel_shares have nas in drive
    international_supply_side_fuel_mixing = check_and_fill_missing_fuel_mixing_dates(international_bunker_inputs,  international_supply_side_fuel_mixing)
    #interpolate the fuel shares to get a value for every year:
    international_bunker_inputs, international_supply_side_fuel_mixing = interpolate_bunker_shares_and_mixing(international_bunker_inputs, international_supply_side_fuel_mixing)
    #and check it all matches wat we expect (we wont bother with international_supply_side_fuel_mixing since we checked it earlier in check_and_fill_missing_fuel_mixing_dates)
    check_all_input_data_against_concordances(international_bunker_inputs)
    #calcaulte new energy use for each medium, and drive type:
    international_bunker_outputs = project_total_bunkers_energy_use(international_bunker_inputs, turnover_rate)
    # then join to the supply side fuel mixing data and calculate the new fuel mix for any that have supply side fuel mixing:
    international_bunker_energy = apply_fuel_mixing_to_energy(international_bunker_outputs, international_supply_side_fuel_mixing)
    
    #all done i thnk (:
    new_esto_data = remap_to_esto_mapping(international_bunker_energy, energy_use_esto_mapping)
    #plot as line graph:
    plot_international_bunker_energy(international_bunker_energy)
    plot_international_bunker_activity(international_bunker_outputs)
    plot_international_bunker_shares_and_mixing(international_fuel_shares, international_supply_side_fuel_mixing)
    #save
    save_bunkers_data(new_esto_data, international_bunker_outputs)
    
def save_bunkers_data(new_esto_data, international_bunker_outputs):
    #decapitalise the sceanrios col:
    new_esto_data['scenarios'] = new_esto_data['scenarios'].str.lower()
    #save it to csv in output
    new_esto_data.to_csv(f'output_data/for_other_modellers/output_for_outlook_data_system/international_bunker_energy_use_{config.FILE_DATE_ID}.csv', index=False)
    international_bunker_outputs.to_csv(f'output_data/international_energy_use/international_bunker_outputs_{config.FILE_DATE_ID}.csv', index=False)
    #split newesto data into ecnomies and put them all in the output folder:
    for econ in new_esto_data.economy.unique():
        new_esto_data_econ = new_esto_data.loc[new_esto_data['economy'] == econ].copy()
        new_esto_data_econ.to_csv(f'output_data/for_other_modellers/output_for_outlook_data_system/{econ}_international_bunker_energy_use_{config.FILE_DATE_ID}.csv', index=False)
    
def remap_to_esto_mapping(international_bunker_outputs, energy_use_esto_mapping):
    #first check for duplicates when we ignore Energy col
    cols = international_bunker_outputs.columns.to_list()
    cols.remove('Energy')
    dupes = international_bunker_outputs[international_bunker_outputs.duplicated(subset=cols, keep=False)]
    if len(dupes) > 0:
        dupes.to_csv('error_{}.csv'.format(datetime.datetime.now().strftime("%Y%m%d-%H%M%S")))
        breakpoint()
        raise Exception(f'There are duplicates in international_bunker_outputs. Please check the data and remove duplicates, {dupes}')
    
    new_esto_data = pd.merge(international_bunker_outputs, energy_use_esto_mapping, how='left', on=['Scenario','Medium', 'Economy', 'Drive', 'Date', 'Fuel'])
    #drop cols we dont need:
    new_esto_data = new_esto_data.drop(columns=['Medium', 'Drive', 'Fuel'])
    #since some biofuels are used in multiple drive types, we are left with duplicates of 16_07_bio_jet_kerosene specifically. so jsut sum them up:
    new_esto_data = new_esto_data.groupby(['Scenario', 'Economy', 'sectors', 'sub1sectors', 'sub2sectors','sub3sectors', 'sub4sectors', 'fuels', 'subfuels','Date'])['Energy'].sum().reset_index()
    #make economy, Date, scenario lwoercase:
    new_esto_data = new_esto_data.rename({'Economy': 'economy', 'Scenario': 'scenarios', 'Date': 'date', 'Energy': 'energy'}, axis=1)
    
    #pivot so date is in cols and value is in rows:
    new_esto_data = new_esto_data.pivot(index=['scenarios', 'economy', 'sectors', 'sub1sectors', 'sub2sectors','sub3sectors', 'sub4sectors', 'fuels', 'subfuels'], columns='date', values='energy').reset_index()
    
    #change to the inverse of this: .replace({'15_PHL': '15_RP', '17_SGP': 
    #  '17_SIN'})
    new_esto_data['economy'] = new_esto_data['economy'].replace({'15_RP': '15_PHL', '17_SIN': '17_SGP'})
    return new_esto_data     

def plot_international_bunker_activity(international_bunker_outputs):
    #plot a line graph using plotly with the following cols: Scenario, Medium, Economy, Drive, Date, Fuel, Value. We will plot this on a single plot with facet cols for economy, then line dash for Medium, color for Fuel. 
    #sort by 'Date', 'Economy', 'Drive', 'Medium'
    for medium in international_bunker_outputs.Medium.unique():
        for scenario in international_bunker_outputs.Scenario.unique():
            international_bunker_activity_m = international_bunker_outputs.loc[(international_bunker_outputs['Medium'] == medium) & (international_bunker_outputs['Scenario'] == scenario)].copy()
            international_bunker_activity_m = international_bunker_activity_m.groupby(['Date', 'Economy', 'Drive'])['Activity'].sum().reset_index()
            #set any rows where vlaue is 0 to nan so they dont show up on the graph
            international_bunker_activity_m.loc[international_bunker_activity_m['Activity'] == 0, 'Activity'] = np.nan
            
            #drop any nas in value:
            international_bunker_activity_m = international_bunker_activity_m.dropna(subset=['Activity'])
            
            #order data by date value. so the data with higest values end up on top of the graph
            international_bunker_activity_m = international_bunker_activity_m.sort_values(by=['Date', 'Economy', 'Activity'])
            
            fig = px.area(international_bunker_activity_m, x='Date', y='Activity', facet_col='Economy', color='Drive', facet_col_wrap=3, title = f'International bunker activity for {medium} in {scenario}')
            #save to html in plotting_output/international_activity
            fig.write_html(f'plotting_output/international_energy_use/{medium}_{scenario}_international_bunker_activity_{config.FILE_DATE_ID}.html')
            
    #plot a similar graph but with the medium in it by using pattern_shape="medium" and pattern_shape_sequence=["-", "."]
    for scenario in international_bunker_outputs.Scenario.unique():
        international_bunker_activity_s = international_bunker_outputs.loc[(international_bunker_outputs['Scenario'] == scenario)].copy()
        international_bunker_activity_s = international_bunker_activity_s.groupby(['Date', 'Economy', 'Drive', 'Medium'])['Activity'].sum().reset_index()
        
        #set any rows where vlaue is 0 to nan so they dont show up on the graph
        international_bunker_activity_s.loc[international_bunker_activity_s['Activity'] == 0, 'Activity'] = np.nan
        #drop any nas in Activity:
        international_bunker_activity_s = international_bunker_activity_s.dropna(subset=['Activity'])
    
        #order data by date Activity. so the data with higest Activitys end up on top of the graph
        international_bunker_activity_s = international_bunker_activity_s.sort_values(by=['Date','Economy', 'Activity'])
        
        fig = px.area(international_bunker_activity_s, x='Date', y='Activity', facet_col='Economy', color='Drive', facet_col_wrap=3, pattern_shape="Medium", pattern_shape_sequence=["-", "."], title = f'International bunker activity for {scenario}')
        #save to html in plotting_output/international_energy_use
        fig.write_html(f'plotting_output/international_energy_use/{scenario}_international_bunker_activity_{config.FILE_DATE_ID}.html')

def plot_international_bunker_energy(international_bunker_energy):
    #plot a line graph using plotly with the following cols: Scenario, Medium, Economy, Drive, Date, Fuel, Value. We will plot this on a single plot with facet cols for economy, then line dash for Medium, color for Fuel. 
    #sort by 'Date', 'Economy', 'Drive', 'Medium'
    for medium in international_bunker_energy.Medium.unique():
        for scenario in international_bunker_energy.Scenario.unique():
            international_bunker_energy_m = international_bunker_energy.loc[(international_bunker_energy['Medium'] == medium) & (international_bunker_energy['Scenario'] == scenario)].copy()
            international_bunker_energy_m = international_bunker_energy_m.groupby(['Date', 'Economy', 'Fuel'])['Energy'].sum().reset_index()
            #set any rows where vlaue is 0 to nan so they dont show up on the graph
            international_bunker_energy_m.loc[international_bunker_energy_m['Energy'] == 0, 'Energy'] = np.nan
            
            #drop any nas in value:
            international_bunker_energy_m = international_bunker_energy_m.dropna(subset=['Energy'])
            
            #order data by date value. so the data with higest values end up on top of the graph
            international_bunker_energy_m = international_bunker_energy_m.sort_values(by=['Date','Economy', 'Energy'])
            
            fig = px.area(international_bunker_energy_m, x='Date', y='Energy', facet_col='Economy', color='Fuel', facet_col_wrap=3, title = f'International bunker energy use for {medium} in {scenario}')
            #save to html in plotting_output/international_energy_use
            fig.write_html(f'plotting_output/international_energy_use/{medium}_{scenario}_international_bunker_energy_use_{config.FILE_DATE_ID}.html')
            
    #plot a similar graph but with the medium in it by using pattern_shape="medium" and pattern_shape_sequence=["-", "."]
    for scenario in international_bunker_energy.Scenario.unique():
        international_bunker_energy_s = international_bunker_energy.loc[(international_bunker_energy['Scenario'] == scenario)].copy()
        international_bunker_energy_s = international_bunker_energy_s.groupby(['Date', 'Economy', 'Fuel', 'Medium'])['Energy'].sum().reset_index()
        
        #set any rows where vlaue is 0 to nan so they dont show up on the graph
        international_bunker_energy_s.loc[international_bunker_energy_s['Energy'] == 0, 'Energy'] = np.nan
        #drop any nas in Energy:
        international_bunker_energy_s = international_bunker_energy_s.dropna(subset=['Energy'])
    
        #order data by date Energy. so the data with higest Energys end up on top of the graph
        international_bunker_energy_s = international_bunker_energy_s.sort_values(by=['Date','Economy', 'Energy'])
        
        fig = px.area(international_bunker_energy_s, x='Date', y='Energy', facet_col='Economy', color='Fuel', facet_col_wrap=3, pattern_shape="Medium", pattern_shape_sequence=["-", "."], title = f'International bunker energy use for {scenario}')
        #save to html in plotting_output/international_energy_use
        fig.write_html(f'plotting_output/international_energy_use/BEST_{scenario}_international_bunker_energy_use_{config.FILE_DATE_ID}.html')


def plot_international_bunker_shares_and_mixing(international_fuel_shares, international_supply_side_fuel_mixing):
    #plot a similar graph but with the medium in it by using pattern_shape="medium" and pattern_shape_sequence=["-", "."]
    for scenario in international_fuel_shares.Scenario.unique():
        international_fuel_shares_s = international_fuel_shares.loc[(international_fuel_shares['Scenario'] == scenario)].copy()
        
        #sort by date, economy
        international_fuel_shares_s = international_fuel_shares_s.sort_values(by=['Date','Economy'])
        
        fig = px.line(international_fuel_shares_s, x='Date', y='Share', facet_col='Economy', color='Drive', facet_col_wrap=3, line_dash="Medium", title = f'International bunker drive shares for {scenario}')
        #save to html in plotting_output/international_energy_use
        fig.write_html(f'plotting_output/international_energy_use/{scenario}_international_bunker_drive_shares_{config.FILE_DATE_ID}.html')

    for scenario in international_supply_side_fuel_mixing.Scenario.unique():
        international_supply_side_fuel_mixing_s = international_supply_side_fuel_mixing.loc[(international_supply_side_fuel_mixing['Scenario'] == scenario)].copy()
        international_supply_side_fuel_mixing_s = international_supply_side_fuel_mixing_s.groupby(['Date', 'Economy', 'New_fuel', 'Medium'])['Mix'].mean().reset_index()
        
        #sort by date, economy
        international_supply_side_fuel_mixing_s = international_supply_side_fuel_mixing_s.sort_values(by=['Date','Economy'])
        
        fig = px.line(international_supply_side_fuel_mixing_s, x='Date', y='Mix', facet_col='Economy', color='New_fuel', facet_col_wrap=3, line_dash="Medium", title = f'Non weighted average international bunker fuel mixes for {scenario}')
        #save to html in plotting_output/international_energy_use
        fig.write_html(f'plotting_output/international_energy_use/{scenario}_average_international_bunker_fuel_mixes_{config.FILE_DATE_ID}.html')

def apply_fuel_mixing_to_energy(international_bunker_outputs, international_supply_side_fuel_mixing):
    #join the two, times energy by mix to get the energy for the new fuel, minus that from energy to get the energy for the old fuel then seperate the dfs and concat them:
    mixing_international_bunker_outputs = international_bunker_outputs.copy()
    
    mixing_international_bunker_outputs = pd.merge(mixing_international_bunker_outputs, international_supply_side_fuel_mixing, how='left', on=['Scenario','Medium', 'Economy', 'Drive', 'Date', 'Fuel'], indicator=True)
    
    mixing_international_bunker_outputs['Energy_new'] = mixing_international_bunker_outputs['Energy'] * mixing_international_bunker_outputs['Mix']
    #repalce nas with 0
    mixing_international_bunker_outputs['Energy_new'] = mixing_international_bunker_outputs['Energy_new'].fillna(0)
    #now we need to subtract the new energy from the old energy to get the energy for the old fuel:
    mixing_international_bunker_outputs['Energy'] = mixing_international_bunker_outputs['Energy'] - mixing_international_bunker_outputs['Energy_new']
    
    #create df for new fuel. and drop where _merge is left_only. this is where there is no fuel mixing for that fuel, drive, medium combo
    new_data = mixing_international_bunker_outputs.loc[mixing_international_bunker_outputs['_merge'] != 'left_only'].copy()
    new_data = new_data[['Scenario','Medium', 'Economy', 'Drive', 'Date', 'New_fuel', 'Energy_new']]
    new_data.rename({'New_fuel': 'Fuel', 'Energy_new': 'Energy'}, axis=1, inplace=True)
    mixing_international_bunker_outputs = mixing_international_bunker_outputs[['Scenario','Medium', 'Economy', 'Drive', 'Date', 'Fuel', 'Energy']].copy()
    
    #cocnat
    international_bunker_energy = pd.concat([mixing_international_bunker_outputs, new_data])
    
    #double check that total energy use is the same as before:
    if abs(international_bunker_energy['Energy'].sum() - international_bunker_outputs['Energy'].sum()) > 0.001:
        international_bunker_energy.to_csv('error_{}.csv'.format(datetime.datetime.now().strftime("%Y%m%d-%H%M%S")))
        breakpoint()
        raise Exception('The total energy use for the international_bunker_outputs df has changed after applying fuel mixing. Please check the data and remove duplicates, {}'.format(abs(international_bunker_energy['Energy'].sum() - international_bunker_outputs['Energy'].sum())))
    
    return international_bunker_energy

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
    
    #we will keep all the clunms since this process is simple. We can isntead drop the new cols we create here at the end of the function, so we retain a df to map into.
        
    #melt data so date is in one col and values in another
    energy_use_esto_bunkers_tall = pd.melt(energy_use_esto_bunkers, id_vars=['scenarios', 'economy', 'sectors', 'sub1sectors', 'sub2sectors','sub3sectors', 'sub4sectors', 'fuels', 'subfuels', 'Fuel', 'Medium'], var_name='Date', value_name='Energy').reset_index(drop=True)
        
    #merge onto the mapping to get the drive type and whetehr or not the rows (eventual) energy use is through supply side fuel mixing:
    energy_use_esto_bunkers_tall = pd.merge(energy_use_esto_bunkers_tall, international_bunkers_mapping, how='left', on=['Medium', 'Fuel'])
    
    #find if there are any fuels that we need to map to new Drives. these must have Value >0
    other_fuels = energy_use_esto_bunkers_tall.loc[(energy_use_esto_bunkers_tall['Drive'].isnull()) & (energy_use_esto_bunkers_tall['Energy'] > 0)]
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
    energy_use_esto_bunkers_tall['Energy'] = energy_use_esto_bunkers_tall['Energy'].abs()
    #and set any nas to 0:
    energy_use_esto_bunkers_tall['Energy'] = energy_use_esto_bunkers_tall['Energy'].fillna(0)
    
    # Drop the following cols. We will join them on later:
    energy_use_esto_mapping = energy_use_esto_bunkers_tall.drop(columns=['Energy', 'Supply_side_fuel_mixing']).copy()
    energy_use_esto_bunkers_tall = energy_use_esto_bunkers_tall.drop(columns=['sectors', 'sub1sectors', 'sub2sectors','sub3sectors', 'sub4sectors', 'fuels', 'subfuels'])
    return energy_use_esto_bunkers_tall, energy_use_esto_mapping

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
    
def interpolate_bunker_shares_and_mixing(international_bunker_inputs,international_supply_side_fuel_mixing, X_ORDER='linear'):
    #mergin the data has given us all teh dates we need to interpoalte for . so drop teh cols we dont need, interpoalte and then join back onto international_bunker_inputs.
    international_fuel_shares = international_bunker_inputs[['Scenario','Medium', 'Economy', 'Drive', 'Date', 'Share']].copy()
    international_bunker_inputs= international_bunker_inputs.drop(columns=['Share'])
    
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
    international_fuel_shares['Share'] = international_fuel_shares.groupby(['Scenario','Medium', 'Date','Economy'])['Share'].apply(lambda x: x/x.sum())
    
    #now join back on 
    international_bunker_inputs = pd.merge(international_bunker_inputs, international_fuel_shares, how='left', on=['Scenario','Medium', 'Economy', 'Drive', 'Date'])

    return international_bunker_inputs, international_supply_side_fuel_mixing
import yaml

def get_economies_to_base_energy_use_off_of():
    """
    Reads the ECONOMIES_TO_BASE_ENERGY_USE_OFF_OF parameter from the parameters.yml file and returns a list of economies that have a value of True.

    Returns:
        list: A list of economies that have a value of True in the ECONOMIES_TO_BASE_ENERGY_USE_OFF_OF parameter.
    """
    # Read the ECONOMIES_TO_BASE_ENERGY_USE_OFF_OF parameter from the parameters.yml file
    ECONOMIES_TO_BASE_ENERGY_USE_OFF_OF = yaml.load(open('config/parameters.yml'), Loader=yaml.FullLoader)['ECONOMIES_WITH_MODELLING_COMPLETE']
    # Filter for only economies with a value of True
    return [economy for economy in ECONOMIES_TO_BASE_ENERGY_USE_OFF_OF if ECONOMIES_TO_BASE_ENERGY_USE_OFF_OF[economy] == True]

def extract_non_road_modelled_data():
    #get non road intensity and activity projections. the activity will be used to get the growth rate for energy use in the whole of apec, the intensity will be timesed by to get activity.
    #and extract intensity and activity from the model output:
    model_output_detailed = pd.read_csv('output_data/model_output_detailed/all_economies_NON_ROAD_DETAILED_{}_{}'.format(config.FILE_DATE_ID, config.model_output_file_name))
    non_road = model_output_detailed.loc[model_output_detailed['Medium'].isin(['air', 'ship'])]
    
    #drop electric planes and ships
    non_road = non_road.loc[~((non_road['Drive'] == 'air_electric') | (non_road['Drive'] == 'ship_electric'))]
    
    #extract activity to clacualte growth rate:
    non_road_activity = non_road[['Scenario', 'Date','Economy', 'Transport Type', 'Activity']].copy()
    #filter for only ECONOMIES_TO_BASE_ENERGY_USE_OFF_OF (this is because during development we ahvent prepared all economies fully yet.)
    ECONOMIES_TO_BASE_ENERGY_USE_OFF_OF = get_economies_to_base_energy_use_off_of()
    non_road_activity = non_road_activity.loc[non_road_activity['Economy'].isin(ECONOMIES_TO_BASE_ENERGY_USE_OFF_OF)]
    
    #sum by scenario, date and medium (not by economy so that we can average out domestic variations.. this is international fuel use after all)
    non_road_activity = non_road_activity.groupby(['Scenario', 'Transport Type', 'Date'])['Activity'].sum().reset_index()#keep transport type for activity until we calcualte avg growth rate
    breakpoint()
    #and get intensity:    
    non_road_intensity = non_road[['Scenario', 'Date',  'Drive', 'Activity', 'Intensity']].copy()
    non_road_intensity['Weighted_Intensity'] = non_road_intensity['Activity'] * non_road_intensity['Intensity']
    non_road_intensity = (non_road_intensity.groupby(['Scenario',  'Date', 'Drive'])['Weighted_Intensity'].sum() / non_road_intensity.groupby(['Scenario',  'Date', 'Drive'])['Activity'].sum()).reset_index()
    #reanem Weighted_Intensity to Intensity
    non_road_intensity = non_road_intensity.rename({0: 'Intensity'}, axis=1)
    # non_road_intensity = non_road_intensity.reset_index()
    
    #if there are any nas in intensity then just set them to the avg intensity for that drive type:
    non_road_intensity['Intensity'] = non_road_intensity.groupby(['Drive'])['Intensity'].apply(lambda x: x.fillna(x.mean()))
    #FIX
    #for air_fuel_oil and air_lpg, jsut set them to the intensity of air_diesel. we should get rid of them nbut this is a quick fix for now
    non_road_intensity_nas = non_road_intensity.loc[non_road_intensity['Drive'].isin(['air_fuel_oil', 'air_lpg'])].copy()
    non_road_intensity = non_road_intensity.loc[~non_road_intensity['Drive'].isin(['air_fuel_oil', 'air_lpg'])].copy()
    non_road_intensity_nas = non_road_intensity_nas.drop(columns=['Intensity'])
    non_road_intensity_nas = pd.merge(non_road_intensity_nas, non_road_intensity.loc[non_road_intensity['Drive'] == 'air_diesel'].drop(columns=['Drive']), how='left', on=['Scenario', 'Date'])
    non_road_intensity = pd.concat([non_road_intensity, non_road_intensity_nas])
    #FIX
    if len(non_road_intensity.loc[non_road_intensity['Intensity'].isnull()]) > 0:
        breakpoint()
        fuels_missing = non_road_intensity.loc[non_road_intensity['Intensity'].isnull()]['Drive'].unique()
        raise Exception(f'There are some fuels in the non_road_intensity data that do not have intensity values. Please check the data and see about creating intensity data for them, {fuels_missing}')
    
    plot_non_road_intensity(non_road_intensity)
    
    return non_road_activity, non_road_intensity

def plot_non_road_activity(non_road_activity):
    
    #quickly plot the non road eneryg use so we can tell what the growth rate will be
    fig = px.line(non_road_activity, x='Date', y='Activity',color='Scenario', line_dash = 'Transport Type')
    fig.write_html('plotting_output/international_energy_use/non_road_activity_{}.html'.format(config.FILE_DATE_ID))

def plot_non_road_activity_growth(non_road_activity_growth_rate):
    
    #quickly plot the non road Activity so we can tell what the growth rate will be
    fig = px.line(non_road_activity_growth_rate, x='Date', y='Growth Rate', color='Scenario')
    fig.write_html('plotting_output/international_energy_use/non_road_activity_growth_{}.html'.format(config.FILE_DATE_ID))

def plot_non_road_intensity(non_road_intensity):
    fig = px.line(non_road_intensity, x='Date', y='Intensity', color='Scenario', line_dash = 'Drive')
    fig.write_html('plotting_output/international_energy_use/non_road_intensity_{}.html'.format(config.FILE_DATE_ID))    
    
def calculate_non_road_activity_growth_rate(non_road_activity):  
    #calculate the average growth rate for each scenario. we will combine it bymedium rather than keepign ti separate
    plot_non_road_activity(non_road_activity)
    
    non_road_activity = non_road_activity.sort_values(by=['Scenario', 'Transport Type', 'Date'])
    non_road_activity['Growth Rate'] = non_road_activity.groupby(['Scenario', 'Transport Type'])['Activity'].pct_change()
    #drop non needed cols. we will drop transport type now that the transport types can be compared as %, where previously fregith tonne km and passenger km could not be compared
    non_road_activity_growth_rate = non_road_activity.dropna().groupby(['Scenario',  'Date'])['Growth Rate'].mean().reset_index()
    
    #and plot the growth rate
    plot_non_road_activity_growth(non_road_activity_growth_rate)
    
    return non_road_activity_growth_rate

def check_for_duplicates_in_all_datasets(energy_use_esto_bunkers_tall, international_fuel_shares, non_road_activity_growth_rate, non_road_intensity, international_supply_side_fuel_mixing):
    
    #check for duplicates!
    cols = energy_use_esto_bunkers_tall.columns.to_list()
    cols.remove('Energy')
    dupes = energy_use_esto_bunkers_tall[energy_use_esto_bunkers_tall.duplicated(subset=cols, keep=False)]
    if len(dupes) > 0:
        dupes.to_csv('error.csv')
        breakpoint()
        raise Exception(f'There are duplicates in the energy_use_esto data. Please check the data and remove duplicates, {dupes}')
    dupes = international_fuel_shares[international_fuel_shares.duplicated(subset=['Scenario', 'Medium', 'Economy', 'Drive', 'Date'], keep=False)]
    if len(dupes) > 0:
        dupes.to_csv('error.csv')
        breakpoint()
        raise Exception(f'There are duplicates in the international_fuel_shares data. Please check the data and remove duplicates, {dupes}')
    dupes = non_road_activity_growth_rate[non_road_activity_growth_rate.duplicated(subset=['Scenario', 'Date'], keep=False)]
    if len(dupes) > 0:
        dupes.to_csv('error.csv')
        breakpoint()
        raise Exception(f'There are duplicates in the non_road_activity_growth_rate data. Please check the data and remove duplicates, {dupes}')
    breakpoint()
    dupes = non_road_intensity[non_road_intensity.duplicated(subset=['Scenario', 'Date', 'Drive'], keep=False)]
    if len(dupes) > 0:
        dupes.to_csv('error.csv')
        breakpoint()
        raise Exception(f'There are duplicates in the non_road_intensity data. Please check the data and remove duplicates, {dupes}')
    dupes = international_supply_side_fuel_mixing[international_supply_side_fuel_mixing.duplicated(subset=['Scenario', 'Medium', 'Economy', 'Drive', 'Date', 'Fuel', 'New_fuel'], keep=False)]
    if len(dupes) > 0:
        dupes.to_csv('error.csv')
        breakpoint()
        raise Exception(f'There are duplicates in the international_supply_side_fuel_mixing data. Please check the data and remove duplicates, {dupes}')
    
def merge_and_format_all_input_data(energy_use_esto_bunkers_tall, international_fuel_shares, non_road_activity_growth_rate, non_road_intensity):
    #merge all together beofre checking that it all mathces wat we expect (we will mege in a different order later):
    international_bunker_inputs = pd.merge(energy_use_esto_bunkers_tall, international_fuel_shares, how='left', on=['Medium', 'Economy', 'Scenario','Drive', 'Date'])
    international_bunker_inputs = pd.merge(international_bunker_inputs, non_road_activity_growth_rate, how='left', on=['Scenario', 'Date'])
    international_bunker_inputs = pd.merge(international_bunker_inputs, non_road_intensity, how='left', on=['Scenario', 'Date', 'Drive'])
    #keep only data that is between OUTLOOK_BASE_YEAR and GRAPHING_END_YEAR
    international_bunker_inputs = international_bunker_inputs.loc[(international_bunker_inputs['Date'] >= config.OUTLOOK_BASE_YEAR) & (international_bunker_inputs['Date'] <= config.GRAPHING_END_YEAR)]
    
    
    #dont check for nas yet. we know that we have nas in the fuel share data and we will interpolate them later. We could have nas in the esto data too. we will check for them later.
    
    return international_bunker_inputs
    
def check_and_fill_missing_fuel_mixing_dates(international_bunker_inputs, international_supply_side_fuel_mixing):
    #we wont merge international_supply_side_fuel_mixing on international_supply_side_fuel_mixing because if there are two new fuels for a fuel, then it would create duplicates. instead we will double check that all the Fuels, Drive, Medium combos in international_supply_side_fuel_mixing are in the international_bunker_inputs df. And then we will join the international_supply_side_fuel_mixing onto the Date col in international_bunker_inputs, so we have all required dates, so we can interpoalte the mixing data.
    unique_fuel_drive_medium_combos = international_supply_side_fuel_mixing[['Fuel', 'Drive', 'Medium']].drop_duplicates()
    combos = unique_fuel_drive_medium_combos.merge(international_bunker_inputs[['Fuel', 'Drive', 'Medium', 'Date']].drop_duplicates(), how = 'outer', on=['Fuel', 'Drive', 'Medium'], indicator=True)
    left_only = combos.loc[combos['_merge'] == 'left_only']
    if len(left_only) > 0:
        left_only.to_csv('error_{}.csv'.format(datetime.datetime.now().strftime("%Y%m%d-%H%M%S")))
        breakpoint()
        raise Exception(f'There are some rows in the international_supply_side_fuel_mixing that are not in the international_bunker_inputs df. Please check the data and remove duplicates, {left_only}')
    #and finally join on teh missing dates:
    #firs grab the dates we need as a df:
    dates = international_bunker_inputs[['Date']].drop_duplicates()
    #then merge it onto a version of international_supply_side_fuel_mixing wihtout the Date or Mix cols:
    dates = pd.merge(dates, international_supply_side_fuel_mixing[['Scenario','Medium', 'Economy', 'Drive', 'Fuel', 'New_fuel']].drop_duplicates(), how='cross')
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

def check_all_input_data_against_concordances(international_bunker_inputs):
    model_concordances_user_input_and_growth_rates = format_concordances_for_checking()
    
    #now check that we have all the data we need by checking that all the remainign rows are in the international bunker energy use inputs df:
    check_df = pd.merge(model_concordances_user_input_and_growth_rates, international_bunker_inputs, how='outer', on=['Scenario','Medium', 'Economy', 'Drive', 'Date'], indicator=True)
    #find where indicator is not both:
    check_df_errors = check_df.loc[check_df['_merge'] != 'both']
    if len(check_df_errors) > 0:
        check_df_errors.to_csv('error_{}.csv'.format(datetime.datetime.now().strftime("%Y%m%d-%H%M%S")))
        breakpoint()
        raise Exception(f'There are some rows in the model_concordances_user_input_and_growth_rates that are not in the international_bunker_inputs df. Please check the data and remove duplicates, {check_df_errors}')
    check_df.drop(columns=['_merge'], inplace=True)
    #check for dupes:
    cols = check_df.columns.to_list()
    cols.remove('Energy')
    cols.remove('Share')
    cols.remove('Growth Rate')
    cols.remove('Intensity')
    dupes = international_bunker_inputs[international_bunker_inputs.duplicated(subset=cols, keep=False)]
    if len(dupes) > 0:
        dupes.to_csv('error_{}.csv'.format(datetime.datetime.now().strftime("%Y%m%d-%H%M%S")))
        breakpoint()
        raise Exception(f'There are some duplicates in the international_bunker_inputs df. Please check the data and remove duplicates, {dupes}')
    
    #now we have made sure we have no missing data or dupes we can begin calculating!
    

def project_total_bunkers_energy_use(international_bunker_inputs, turnover_rate):
    #one day would be good to drop these loops and favour something like indexing. but for now its ok
    new_df = pd.DataFrame()
    #repalce Value nas with 0
    international_bunker_inputs['Energy'] = international_bunker_inputs['Energy'].fillna(0)
    
    #calcaulte activity for each row using itneisty and energy:
    international_bunker_inputs['Activity'] = international_bunker_inputs['Energy'] / international_bunker_inputs['Intensity']
    
    for medium in international_bunker_inputs.Medium.unique():
        for scenario in international_bunker_inputs.Scenario.unique():
            for economy in international_bunker_inputs.Economy.unique():
                    
                international_bunker_inputs_medium = international_bunker_inputs.loc[(international_bunker_inputs['Medium'] == medium) &(international_bunker_inputs['Scenario'] == scenario)&(international_bunker_inputs['Economy'] == economy)].copy()
                
                new_df_medium = pd.DataFrame()
                #itl be easiest to just loop through the years to apply growth:
                activity =  international_bunker_inputs_medium[['Scenario', 'Economy', 'Date', 'Drive', 'Fuel', 'Medium','Energy', 'Activity']].copy()
                base_year_activity = activity.loc[activity['Date'] == config.OUTLOOK_BASE_YEAR].copy()
                #need growth and shares sep to enegry since you use the growth_and_shares for year and activity from year -1
                model_inputs = international_bunker_inputs_medium[['Scenario', 'Economy', 'Date', 'Medium', 'Drive', 'Growth Rate', 'Share', 'Intensity']].drop_duplicates().copy()
                new_df_medium = pd.concat([new_df_medium, base_year_activity])
                for year in range(config.OUTLOOK_BASE_YEAR+1, config.GRAPHING_END_YEAR+1):
                    
                    #grab previous years activity (would have been calcualted in the previous loop or is from the base year activity df):
                    previous_year_activity = new_df_medium.loc[new_df_medium['Date'] == year-1].copy()
                    #set date to year
                    previous_year_activity['Date'] = year
                    #join on the growth rate and shares for that year:
                    current_year = pd.merge(previous_year_activity, model_inputs, how='left', on=['Scenario', 'Economy', 'Date', 'Drive', 'Medium']).copy()
                    #if the growth rate is less than 0 then breakpount, we want to see whats happening:
                    if current_year['Growth Rate'].iloc[0] < 0:
                        breakpoint()
                        
                    new_activity_growth_sum = current_year['Activity'].sum() * current_year['Growth Rate'].iloc[0]
                    #take away 0.03 from activity use in all rows. this is to replicate the turnover of stocks so that old fuel types can go to zero. then the lost enegry use will be added to the new activity requried and distributed via the fuel shares: (note that we make sure not to take away activity before we find the sum of new activity use for that year - this is what we do in the otehr models)
                    turnover_of_activity = current_year['Activity'].sum() * turnover_rate
                    #take away the turnover of stocks from the sum of activity use for that year:
                    current_year['Activity'] = current_year['Activity'] - (current_year['Activity'] * turnover_rate)
                    #calculate nadditional_activity_total as  new_activity_growth_sum + turnover
                    current_year['additional_activity_total'] = new_activity_growth_sum + turnover_of_activity
                    if current_year['additional_activity_total'].any() < 0:
                        #we dont want to decrease activity use of the fuel with highest fuel share. instead, jsut make Share = to the proportion of the drive comapred to the rest:
                        current_year['Share'] = current_year['Activity'] / current_year['Activity'].sum()
                    #distribute this additional_activity_total via the fuel shares:
                    current_year['Activity'] = current_year['Activity'] + (current_year['additional_activity_total'] * current_year['Share'])
                    
                    #if any activity is less than 0 then set it to 0
                    current_year.loc[current_year['Activity'] < 0, 'Activity'] = 0
                    
                    #now clacualte energy using intenisty:
                    current_year['Energy'] = current_year['Activity'] * current_year['Intensity']
                    
                    #drop cols we dont need:
                    current_year = current_year.drop(columns=['Growth Rate', 'additional_activity_total', 'Share', 'Intensity'])
                    
                    new_df_medium = pd.concat([new_df_medium, current_year])
     
                new_df = pd.concat([new_df, new_df_medium])
            
    return new_df

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
    fuel_mixing_base_year['Mix'] = fuel_mixing_base_year['Energy_y'] / (fuel_mixing_base_year['Energy_x'] + fuel_mixing_base_year['Energy_y'])
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
    fuel_mixing_base_year_original['Energy_x'] = fuel_mixing_base_year_original['Energy_x'] + fuel_mixing_base_year_original['Energy_y'].replace(np.nan, 0)
    #drop any cols ending with _y and also 'New_fuel', '_merge'
    fuel_mixing_base_year_original = fuel_mixing_base_year_original.drop(columns=[col for col in fuel_mixing_base_year_original.columns if col.endswith('_y')]+[ '_merge'])
    #set all x cols to just be the x cols
    fuel_mixing_base_year_original.rename({col: col.replace('_x', '') for col in fuel_mixing_base_year_original.columns if col.endswith('_x')}, axis=1, inplace=True)
    #to check that this worked, double check that the sum of Value is equal to the sum of Value in energy_use_esto_bunkers_tall_base_year
    if abs(fuel_mixing_base_year_original['Energy'].sum() - energy_use_esto_bunkers_tall_base_year['Energy'].sum()) -1 > 0.0000001:
        breakpoint()
        raise Exception('The sum of Value in fuel_mixing_base_year_original is not equal to the sum of Value in energy_use_esto_bunkers_tall_base_year. Please check the data. diff is {}'.format(abs(fuel_mixing_base_year_original['Energy'].sum() - energy_use_esto_bunkers_tall_base_year['Energy'].sum())))
    
    #now join the fuel mixing base year original onto the energy_use_esto_bunkers_tall without its value column. so essentially we are replacing the values:
    energy_use_esto_bunkers_tall = energy_use_esto_bunkers_tall.drop(columns=['Energy','Supply_side_fuel_mixing'])
    fuel_mixing_base_year_original = fuel_mixing_base_year_original.drop(columns=['Supply_side_fuel_mixing'])
    energy_use_esto_bunkers_tall = pd.merge(energy_use_esto_bunkers_tall, fuel_mixing_base_year_original, how='left', on=['Scenario','Date', 'Medium', 'Drive', 'Economy', 'Fuel'])
    #and drop teh fuel mixing fuels. they will become a part of this df by being mixed into the other fuels after projection
    energy_use_esto_bunkers_tall = energy_use_esto_bunkers_tall.loc[~energy_use_esto_bunkers_tall['Fuel'].isin(fuels_added_in_mixing['Fuel'].unique().tolist())]
    
    return international_supply_side_fuel_mixing, energy_use_esto_bunkers_tall


def calculate_base_year_fuel_shares(international_fuel_shares, energy_use_esto_bunkers_tall):#, international_supply_side_fuel_mixing
    #we need to calculate the base year fuel shares. we will do this by taking the fuel use for each medium and drive type, and dividing it by the total fuel use for that medium and drive type. 
    fuel_shares = energy_use_esto_bunkers_tall.loc[energy_use_esto_bunkers_tall['Date'] == config.OUTLOOK_BASE_YEAR].copy()
    # #remove the fuel mixing fuels. Even though we set these to 0 in calculate_base_year_fuel_mixing, its safer to remove them manully here so they dont get into the fuel shares data
    # fuel_shares = fuel_shares.loc[~fuel_shares.Fuel.isin(international_supply_side_fuel_mixing['New_fuel'].unique().tolist())]
    fuel_shares['Total fuel use'] = fuel_shares.groupby(['Economy', 'Medium', 'Drive', 'Date'])['Energy'].transform('sum')
    
    #now divide the Value by the Total fuel use to get the share:
    fuel_shares['Share'] = fuel_shares['Energy'] / fuel_shares['Total fuel use']
    #repalce nan with 0s
    fuel_shares['Share'] = fuel_shares['Share'].fillna(0)
    #grab only the cols we need. that is the cols that are in international_fuel_shares
    cols = international_fuel_shares.columns.tolist()
    fuel_shares = fuel_shares[cols]
    #double check for dupes here since we jsut removed some cols
    cols = cols.remove('Share')
    dupes = fuel_shares[fuel_shares.duplicated(subset=cols, keep=False)]
    if len(dupes) > 0:
        dupes.to_csv('error_{}.csv'.format(datetime.datetime.now().strftime("%Y%m%d-%H%M%S")))
        breakpoint()
        raise Exception(f'There are some duplicates in the fuel_shares df. Please check the data and remove duplicates, {dupes}')
    
    #now look at attaching it to the international_fuel_shares df. 
    international_fuel_shares = international_fuel_shares.loc[~international_fuel_shares['Date'].isin(fuel_shares['Date'].unique().tolist())]
    international_fuel_shares = pd.concat([international_fuel_shares, fuel_shares])

    return international_fuel_shares
    

def calculate_missing_drive_shares_from_manually_inputted_data(international_fuel_shares, YEARS_TO_KEEP_AFTER_BASE_YEAR=5):
    #this process is also done in the create_vehicle_sales_sahre_scrip for non bunkers data.
    #Since we only take data from the drives that are most important to specify shares for, we need to fill in any leftover shares such that the sum of shares for each year adds to 1. for example if we ahve set the manually inputted sshare for electricity such that it is expected to ake up 0.5 of the market in 2030, then we need to set the remaining 0.5 to be split between the other drives. this split will be determined by the base years splits. so if the base year had 0.5 cng and 0.5 diesel, then we will set the remaining 0.5 to be split 0.25 cng and 0.25 diesel.
    
    #but important to note that the data that we use for the base year will not include any (medium, drive) pairs that are in the manually inputted data. this si to prevent double counting them. 
    #Note that it has a little weakness where the user needs to make sure that for every date that they record a drive share in teh manually inputted data, they must record the drive share forf all other shares they have already been reocrding for that medium, drive pair. otherwise, those missing drives will have their shares filled in using the drives from the base year data. then when wqe do interpolation and normalisation, it will result in the shares for that missing drive being lower than what the user was probably intending. eg. if user reocrded shares constasnt in 2027, and 2029 for electricity (0.5) and phev (0.25), and then in 2028 they only recorded shares for electricity(0.5) then the shares for phev in 2028 will probably be lower than 0.25 as the base year data will be used to fill in the missing shares, then in normalisation, the shares will be normalised to 1, so the shares for phev in 2028 will be lower than 0.25, even though they were still interpoalted before nomralisation.
    fuel_share_BASE_YEAR = international_fuel_shares.loc[international_fuel_shares['Date']==config.OUTLOOK_BASE_YEAR].copy()
    fuel_share_manual_input = international_fuel_shares.loc[international_fuel_shares['Date']>config.OUTLOOK_BASE_YEAR+YEARS_TO_KEEP_AFTER_BASE_YEAR].dropna(subset=['Share']).copy()
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
        breakpoint()
        raise ValueError('Drive share remainder is less than 0. You probably need to make sure they add up to 1 in the manually inputted data (vehicle_Sales_share_inputs.xlsx)')
    #join this to the base year data using right join
    missing_fuel_shares = fuel_share_BASE_YEAR[['Economy', 'Scenario','Medium','Drive','Share']].merge(fuel_share_manual_input_sum, on=['Economy', 'Scenario', 'Medium'], how='right')
    #times the base year data by the 1-x
    missing_fuel_shares['Share'] = missing_fuel_shares['Share'] * missing_fuel_shares['Share_remainder']

    missing_fuel_shares = missing_fuel_shares.drop(columns=['Share_remainder'])
    #now we need to insert these rows into the  international_fuel_shares. since its jsut a df of the manually inputted data right now we can jsut concat them together
    international_fuel_shares = pd.concat([international_fuel_shares, missing_fuel_shares])
    
    return international_fuel_shares
        
#%%
international_bunker_share_calculation_handler()#project_total_bunkers_energy_use
#%%