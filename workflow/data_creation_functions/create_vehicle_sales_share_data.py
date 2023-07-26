#we will take in the vehicle sales from historical data, then adjust them according to the patterns we expect to see. i.e. nz moves to 100% ev's by 2030.

#we will also create a vehicle sales distribution that replicates what each scenario in the 8th edition shows. We can use this to help also load all stocks data so that we can test the model works like the 8th edition
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
import user_input_creation_functions
sys.path.append("./workflow/plotting_functions")
import plot_user_input_data

sys.path.append("./workflow/utility_functions")
import archiving_scripts

X_ORDER = 'linear'#set me to linear or the order for the spline
#%%

def estimate_transport_data_system_sales_share(new_transport_data_system_df, YEARS_TO_KEEP_AFTER_BASE_YEAR):
  
    
    sales = new_transport_data_system_df.copy()
    #filter for Stocks in Measutre
    sales = sales.loc[sales['Measure']=='Stocks']
    cols = config.INDEX_COLS.copy()
    cols = cols + ['road']#used for allowing swithicvn between non road mediums
    cols.remove('Medium')
    cols.remove('Vehicle Type')
    cols.remove('Drive')
    total_stocks = sales.copy()
    total_stocks = sales.groupby(cols)['Value'].sum().reset_index()
    total_stocks = total_stocks.rename(columns={'Value':'Total Stocks'})
    sales = sales.merge(total_stocks, on=cols, how='left')
    sales['Sales Share'] = sales['Value']/sales['Total Stocks']
    #set measure to 'Vehicle_sales_share'
    sales['Measure'] = 'Vehicle_sales_share'
    #repalce nan with 0
    sales = sales.fillna(0)

    #now we want to find the year with the most values that arent 0. this is essentially the year with the most data and is therefor emost suitable to abse our sales shares off (data with less values may be missing values and tehrefore exaggerating sales share fr certain vehicle types)
    #we will do this by grouping by year and counting the number of non zero values. then we will sort by this count and take the year with the most non zero values
    # 
    year_with_most_values = sales.loc[sales['Value']>=0.0001].groupby('Date')['Date'].count()
    #its now a seires so get the max value and its index
    max_year = year_with_most_values.idxmax()
    
    #filter for the year with the most values
    sales = sales.loc[sales['Date']==max_year]
    plotting = False
    if plotting:
        plot_user_input_data.plot_estimated_data_system_sales_share(sales, YEARS_TO_KEEP_AFTER_BASE_YEAR)
        
    #drop Total Stocks column and Value column
    sales = sales.drop(columns=['Total Stocks', 'Value'])

    #now replicate the sales shares for each scenario and for each year between the config.DEFAULT_BASE_YEAR and the config.END_YEAR of the scenario.

    #filter for a unique scenario in the sales df
    sales = sales[sales.Scenario==sales.Scenario.unique()[0]]
    sales_dummy = sales.copy()
    new_sales = pd.DataFrame()
    for scenario in config.SCENARIOS_LIST:
        sales_dummy['Scenario'] = scenario
        new_sales = pd.concat([new_sales, sales_dummy])
    
    #now we want to replicate the df (BUT NOT THE SALES SHARE) for each year between the config.DEFAULT_BASE_YEAR and the config.END_YEAR of the scenario
    sales_dummy = new_sales.copy()
    new_sales_years = pd.DataFrame()
    for year in range(config.DEFAULT_BASE_YEAR, config.END_YEAR+1):
        sales_dummy['Date'] = year
        new_sales_years = pd.concat([new_sales_years, sales_dummy])
    
    #set sales share for all values after config.DEFAULT_BASE_YEAR+YEARS_TO_KEEP_AFTER_BASE_YEAR to np.nan (add three so that we still have a few values for the interpoaltion to go off)
    new_sales_years.loc[new_sales_years['Date']>config.DEFAULT_BASE_YEAR+YEARS_TO_KEEP_AFTER_BASE_YEAR, 'Sales Share'] = np.nan

    #set unit to %
    new_sales_years['Unit'] = '%'
    # 
    #when we get to having great data it would be better to extend the years by using something like this:
    
    
    return new_sales_years

def calcaulte_missing_drive_shares_from_manually_inputted_data(new_sales_shares_pre_interp, model_concordances_user_input_and_growth_rates, passenger_drive_shares, freight_drive_shares,YEARS_TO_KEEP_AFTER_BASE_YEAR):
    #we are now only taking in data from the most important drives, to reduce the amount of time we need to spend manually writing out the drive share targets. So the follwoign funciton should take in those targets and the Base year data, and calcualte the remaining drive shares for the missing drives using the base year data's shares as a reference. 
    #the base year datas shares, for the missing drives, will be normalised to 1 so we can just times them by 1-x where x is the sum of the manully inputted shares, in each year we ahve them for. In missing years (the years we will interpoalte later), we will leave all as nan, so that we can interpolate between the values we have set and the base year values.
    #the input files for this will be:
    #new_sales_shares_pre_interp (which contains the base year data and the manually inputted data - whjich we will split at the beginning)
    #model_concordances_user_input_and_growth_rates (which contaions the set of drives, vehicle types and transport types we need to set the drive shares for)
    #passenger_drive_shares and freight_drive_shares (which only contain the manually inputted data > we will sue this to extract the data we want from new_sales_shares_pre_interp)
    #so first we need to split new_sales_shares_pre_interp into the base year data and the manually inputted data
    sales_share_BASE_YEAR = new_sales_shares_pre_interp.loc[new_sales_shares_pre_interp['Date']==config.DEFAULT_BASE_YEAR]
    sales_share_manual_input = new_sales_shares_pre_interp.loc[new_sales_shares_pre_interp['Date']>config.DEFAULT_BASE_YEAR+YEARS_TO_KEEP_AFTER_BASE_YEAR].dropna(subset=['Drive_share'])
    #extract unique drives, vehicle types and transport types from model_concordances_user_input_and_growth_rates
    # combinations = model_concordances_user_input_and_growth_rates[['Medium','Transport Type','road', 'Vehicle Type', 'Drive']].drop_duplicates()
    #find unique combiantions in passenger_drive_shares and freight_drive_shares
    p = passenger_drive_shares[['Medium','Vehicle Type','road', 'Drive']].drop_duplicates()
    p['Transport Type'] = 'passenger'
    f = freight_drive_shares[['Medium','Vehicle Type','road', 'Drive']].drop_duplicates()
    f['Transport Type'] = 'freight'
    combinations_manual_input = pd.concat([p , f])
    #dropo the combinations in sales_share_manual_input from sales_share_BASE_YEAR
    sales_share_BASE_YEAR = sales_share_BASE_YEAR[~sales_share_BASE_YEAR[['Transport Type', 'Medium','Vehicle Type','road', 'Drive']].apply(tuple,1).isin(combinations_manual_input[['Transport Type', 'road','Medium','Vehicle Type', 'Drive']].apply(tuple,1))]

    #set nas in drive share to 0
    sales_share_BASE_YEAR[ 'Drive_share'] = sales_share_BASE_YEAR[ 'Drive_share'].fillna(0)
    #find the normalised shares for the available data in the base year data
    sales_share_BASE_YEAR['Drive_share'] = sales_share_BASE_YEAR.groupby(['Economy', 'Scenario', 'Transport Type', 'road','Medium','Vehicle Type'])['Drive_share'].transform(lambda x: x/x.sum())
    #set nas in drive share to 0
    sales_share_BASE_YEAR[ 'Drive_share'] = sales_share_BASE_YEAR[ 'Drive_share'].fillna(0)
    #now get sum of manually inputted shares for each year
    sales_share_manual_input_sum = sales_share_manual_input.groupby(['Economy', 'Scenario', 'Transport Type','Medium','road', 'Vehicle Type', 'Date'])['Drive_share'].sum().reset_index()
    #1 minus it
    sales_share_manual_input_sum['Drive_share_remainder'] = 1 - sales_share_manual_input_sum['Drive_share']
    #drop drive share
    sales_share_manual_input_sum = sales_share_manual_input_sum.drop(columns=['Drive_share'])
    #chcke for any values les than 0
    if sales_share_manual_input_sum['Drive_share_remainder'].min() < 0:
        #show them and raise
        print(sales_share_manual_input_sum.loc[sales_share_manual_input_sum['Drive_share_remainder']<0])
        raise ValueError('Drive share remainder is less than 0')
    #join this to the base year data using right join
    missing_sales_shares = sales_share_BASE_YEAR[['Economy', 'Scenario', 'Transport Type','Medium', 'Vehicle Type','Drive', 'road','Drive_share']].merge(sales_share_manual_input_sum, on=['Economy','road', 'Scenario', 'Medium','Transport Type', 'Vehicle Type'], how='right')
    #times the base year data by the 1-x
    missing_sales_shares['Drive_share'] = missing_sales_shares['Drive_share'] * missing_sales_shares['Drive_share_remainder']

    #now we need to insert these rows into the  new_sales_shares_pre_interp, rmeoving their original rows (which will be nas.) so do a join and then repalce drive share with the new drive share where it is not na
    final_df = new_sales_shares_pre_interp.merge(missing_sales_shares, on=['Economy', 'Scenario','Medium', 'Transport Type','road', 'Vehicle Type','Date', 'Drive'], how='left', suffixes=('', '_y'))
    #want to replace the drive share with the new drive share where it is na (replacing nas with nas too.)
    final_df['Drive_share'] = final_df['Drive_share'].fillna(final_df['Drive_share_y'])
    #drop the y cols
    final_df = final_df.drop(columns=['Drive_share_y', 'Drive_share_remainder'])

    return final_df


def create_vehicle_sales_share_input():
    YEARS_TO_KEEP_AFTER_BASE_YEAR= 3
    # new_sales_shares = pd.read_csv('input_data/from_8th/reformatted/vehicle_stocks_change_share_normalised.csv')
    #load groomed data from transport data system
    
    transport_data_system_df = pd.read_csv('intermediate_data/model_inputs/transport_data_system_extract.csv')
    new_transport_data_system_df = transport_data_system_df.copy() 
    
    # #filter for only 19_THA in reference scenario, for years 2017-2030
    # new_transport_data_system_df = new_transport_data_system_df.loc[(new_transport_data_system_df['Economy']=='19_THA') & (new_transport_data_system_df['Scenario']=='Reference') & (new_transport_data_system_df['Date']>=2017) & (new_transport_data_system_df['Date']<=2030)]
    
    
    #drop non road
    new_transport_data_system_df = new_transport_data_system_df.loc[new_transport_data_system_df['Medium']=='road']
    #calcualte nomral;ised sales share for each transport type. so for each economy,  transport type and date, we want to know the share of sales for each row.

    #insert stocks data for non road. do this by copying the activity data and setting stocks to be the same (i.e. the activity per stock is 1)
    non_road_stocks = transport_data_system_df.copy()
    non_road_stocks = non_road_stocks.loc[(non_road_stocks['Measure']=='Activity') & (non_road_stocks['Medium']!='road')].copy()
    non_road_stocks['Measure'] = 'Stocks'
    non_road_stocks['Unit'] = 'Stocks'
    #now concat again
    new_transport_data_system_df = pd.concat([new_transport_data_system_df, non_road_stocks])
        
    #this means we ahve to calcualte the sales by finding the difference between the stock in the current year and the stock in the previous year.
    #this could rersult in issues because we may have gaps in our data. but for now we will just assume that we have data for every year and see how it goes:
    new_transport_data_system_df['road'] = new_transport_data_system_df['Medium']=='road'
    sales = estimate_transport_data_system_sales_share(new_transport_data_system_df,YEARS_TO_KEEP_AFTER_BASE_YEAR)
    #drop 'road' for now (it wont work with the concordances)
    sales = sales.drop(columns=['road'])
    
    #extract dictionary from csv
    #for later, load in vehicle_type_growth_regions sheet and vehicle_type_growth sheet
    vehicle_type_growth_regions = pd.read_excel('input_data/vehicle_sales_share_inputs.xlsx',sheet_name='vehicle_type_growth_regions')
    vehicle_type_growth = pd.read_excel('input_data/vehicle_sales_share_inputs.xlsx',sheet_name='vehicle_type_growth')

    passenger_drive_shares = pd.read_excel('input_data/vehicle_sales_share_inputs.xlsx',sheet_name='passenger_drive_shares')
    freight_drive_shares = pd.read_excel('input_data/vehicle_sales_share_inputs.xlsx',sheet_name='freight_drive_shares')    
    
    regions_passenger = pd.read_excel('input_data/vehicle_sales_share_inputs.xlsx',sheet_name='regions_passenger')
    regions_freight = pd.read_excel('input_data/vehicle_sales_share_inputs.xlsx',sheet_name='regions_freight')


    ######################################
    #TESTING
    #check the regions in regions_passenger and regions_freight are the same as in passenger_drive_shares and freight_drive_shares, also check that the regions in vehicle_type_growth_regions are the same as in vehicle_type_growth
    
    user_input_creation_functions.check_region(regions_passenger, passenger_drive_shares)
    user_input_creation_functions.check_region(regions_freight, freight_drive_shares)
    user_input_creation_functions.check_region(vehicle_type_growth_regions, vehicle_type_growth)

    #####################################
    #PREPARE INPUT DATA
    #####################################

    #first we need to separate the sales share of vehicle types from the sales share of drives, by transport type. Since the way the values were created was simply mutliplication, we can jsut reverse that, i think.
    #so sum by vehicle type to get the total sales share of each vehicle type
    #then if we divide this by the final sales share values for each v-type/drive we can recreate the shares by drive type, witihin each vehicle type.
    #now for shares by drive type, witihin each vehicle type, we can create the shares we want.
    #sum by vtype economy year and scenario
    new_sales_shares_sum = sales.copy()

    #Identify duplicates in case we have multiple rows for the same economy, vehicle type, drive type, transport type and date
    # #todo for some reason we need to do this and i htink its
    new_sales_shares_sum_dupes = new_sales_shares_sum[new_sales_shares_sum.duplicated(subset=['Economy', 'Scenario', 'Medium','Vehicle Type', 'Transport Type','Drive', 'Date','Medium'])]
    if len(new_sales_shares_sum_dupes)>0:#somehow getting dupes. 
        raise ValueError('new_sales_shares_sum_dupes is not empty. This should not happen. Investigate')
        
    #now doulbe check we have therequired categories that are in the concordances
    model_concordances_user_input_and_growth_rates = pd.read_csv('config/concordances_and_config_data/computer_generated_concordances/{}'.format(config.model_concordances_user_input_and_growth_rates_file_name))
    #drop all measures that are not vehicle sales share
    model_concordances_user_input_and_growth_rates = model_concordances_user_input_and_growth_rates[model_concordances_user_input_and_growth_rates['Measure']=='Vehicle_sales_share']
    #drop any cols not in the new_sales_shares_sum
    cols = [col for col in model_concordances_user_input_and_growth_rates.columns if col in new_sales_shares_sum.columns]
    model_concordances_user_input_and_growth_rates = model_concordances_user_input_and_growth_rates[cols]
    model_concordances_user_input_and_growth_rates.drop_duplicates(inplace=True)
    new_INDEX_COLS = [col for col in config.INDEX_COLS if col in model_concordances_user_input_and_growth_rates.columns]

    #add BASE YEAR to the concordances which canb be a copy of the config.DEFAULT_BASE_YEAR +1
    model_concordances_user_input_and_growth_rates_base = model_concordances_user_input_and_growth_rates.loc[model_concordances_user_input_and_growth_rates['Date']==config.DEFAULT_BASE_YEAR+1].copy()
    model_concordances_user_input_and_growth_rates_base['Date'] = config.DEFAULT_BASE_YEAR
    model_concordances_user_input_and_growth_rates = pd.concat([model_concordances_user_input_and_growth_rates,model_concordances_user_input_and_growth_rates_base])

    #set index for both dfs
    new_sales_shares_sum.set_index(new_INDEX_COLS, inplace=True)
    model_concordances_user_input_and_growth_rates.set_index(new_INDEX_COLS, inplace=True)

    # use the difference method to find:
    #missing_index_values1 :  the index values that are missing from the new_sales_shares_sum 
    # #missing_index_values2 : and also the index values that are present in the new_sales_shares_sum but not in the concordance 
    # this method is a lot faster than looping through each index row in the concordance and checking if it is in the new_sales_shares_sum
    missing_index_values1 = model_concordances_user_input_and_growth_rates.index.difference(new_sales_shares_sum.index)
    missing_index_values2 = new_sales_shares_sum.index.difference(model_concordances_user_input_and_growth_rates.index)

    if missing_index_values1.empty:
        print('All rows are present in the user input')
    else:
        #add these rows to the new_sales_shares_sum and set them to row_and_data_not_available
        missing_index_values1 = pd.DataFrame(index=missing_index_values1).reset_index()
        missing_index_values1['Value'] = np.nan
        #then append to transport_data_system_df
        new_sales_shares_sum = new_sales_shares_sum.reset_index()
        new_sales_shares_sum = pd.concat([missing_index_values1, new_sales_shares_sum], sort=False)
        print('Missing rows in our user input dataset when we compare it to the concordance:', missing_index_values1)
        new_sales_shares_sum.set_index(new_INDEX_COLS, inplace=True)

    if missing_index_values2.empty:
        pass#this is to be expected as the cocnordance should always have everything we need in it!
    else:
        #we want to make sure user is aware of this as we will be removing rows from the user input
        #remove these rows from the new_sales_shares_sum
        new_sales_shares_sum.drop(missing_index_values2, inplace=True)
        #convert missing_index_values to df
        missing_index_values2 = pd.DataFrame(index=missing_index_values2).reset_index()
        print('Missing rows in the user input concordance: {}'.format(missing_index_values2))
        print('We will remove these rows from the user input dataset. If you intended to have data for these rows, please add them to the concordance table.')

        # #print the unique Vehicle types and drives that are missing
        # print('Unique Vehicle types and drives that are missing: {}'.format(missing_index_values2[['Vehicle Type', 'Drive']].drop_duplicates()))#as of /4 we ha

    #replace all nan values with 0 now
    # new_sales_shares_sum.fillna(0, inplace=True)

    #reset index
    new_sales_shares_sum.reset_index(inplace=True)
    model_concordances_user_input_and_growth_rates.reset_index(inplace=True)
    #####################################
    #CALCAULTE CURRENT SHARES  
    #####################################
    #before doing anything, create new col called 'road' that is True or False based on the medium. That way we can easily handle switching between non road types by treating any transport type share sums, as also having to be grouped by 'road'.
    new_sales_shares_sum['road'] = new_sales_shares_sum['Medium']=='road'
    
    #PLEASE NOTE THAT VALUE IS THE % OF THE TRANSPORT TYPE FOR THAT VEHICLE TYPE AND DRIVE TYPE. SO IF WE SUM BY VEHICLE TYPE WE GET THE TOTAL SHARE OF EACH VEHICLE TYPE. IF WE DIVIDE BY THIS WE GET THE SHARE OF EACH DRIVE TYPE WITHIN EACH VEHICLE TYPE
    #reaplce Value with Transport_type_share
    new_sales_shares_sum = new_sales_shares_sum.rename(columns={'Sales Share':'Transport_type_share'})
    new_sales_shares_sum['Vehicle_type_share_sum'] = new_sales_shares_sum.groupby(['Economy', 'Scenario', 'Vehicle Type','road', 'Medium','Transport Type', 'Date'])['Transport_type_share'].transform('sum')

    new_sales_shares_sum['Drive_share'] = new_sales_shares_sum['Transport_type_share']/new_sales_shares_sum['Vehicle_type_share_sum']

    #now we can create the shares we want


    
    #first create a clean dataframe with all values set to NA for every year after the base year
    new_sales_shares_sum_clean = new_sales_shares_sum[['Economy', 'Scenario','Medium', 'road', 'Transport Type', 'Date', 'Vehicle Type', 'Drive', 'Drive_share']].drop_duplicates()

    new_sales_shares_sum_0 = new_sales_shares_sum_clean.copy()

    new_sales_shares_sum_0.loc[new_sales_shares_sum_0['Date']>config.DEFAULT_BASE_YEAR+YEARS_TO_KEEP_AFTER_BASE_YEAR, 'Drive_share'] = np.nan

    #sort
    new_sales_shares_sum_0 = new_sales_shares_sum_0.sort_values(by=['Economy', 'Scenario', 'Date', 'Vehicle Type','Medium','road', 'Transport Type', 'Drive'])

    #were getting no values fro Drive_share for <=config.DEFAULT_BASE_YEAR
    ########################################################################################################################################################
    #BEGIN INCORPORATING USER INPUTTED SALES SHARES
    ########################################################################################################################################################
    
    #for this we will perfrom the hcanges on passenger and freight separately. So here we will separate them and then combine them at the end
    new_sales_shares_passenger_0 = new_sales_shares_sum_0[new_sales_shares_sum_0['Transport Type']=='passenger']
    new_sales_shares_freight_0 = new_sales_shares_sum_0[new_sales_shares_sum_0['Transport Type']=='freight']

    #CHANGE ALL PHEVD AND PHEVG TO PHEV. FOR NOW THIS IS NEEDED AS WE ARE CONVERTING PHEV TO G OR D IN DEMAND MIXING

    #for all values we wil interpolate between them with a spline. To set values we will just set the value for the year we want to the value we want, then interpolate between the values we have set and the values in 2017, 2018, 2019. At the end of this we will also normalise all values by vehicle type to sum to 1. Then we will apply growth rates to define how much of each vehicle type we see growth in compared to the others for that transport type
    #join regions to new_sales_shares_sum_0
    new_sales_shares_passenger_0 = pd.merge(new_sales_shares_passenger_0, regions_passenger, how='left', on='Economy')
    new_sales_shares_freight_0 = pd.merge(new_sales_shares_freight_0, regions_freight, how='left', on='Economy')

    def df_to_nested_dict(df):
        outer_dict = {}
        for i, row in df.iterrows():
            scenario_dict = outer_dict.setdefault(row['Scenario'], {})
            inner_dict = scenario_dict.setdefault(row['Region'], {})
            medium_dict = inner_dict.setdefault(row['Medium'], {})
            vehicle_dict = medium_dict.setdefault(row['Vehicle Type'], {})
            if row['Drive'] in vehicle_dict:
                vehicle_dict[row['Drive']].append((row['Share'], row['Date']))
            else:
                vehicle_dict[row['Drive']] = [(row['Share'], row['Date'])]
        return outer_dict

    passenger_drive_shares = passenger_drive_shares.melt(id_vars=['Region', 'Medium','Vehicle Type', 'Drive', 'Date'],var_name='Scenario', value_name='Share')
    freight_drive_shares = freight_drive_shares.melt(id_vars=['Region', 'Medium','Vehicle Type', 'Drive', 'Date'],var_name='Scenario', value_name='Share')
    
    #drop any rows with 'Will make up the rest' in the Drive_share col. These are just pllaceholders to let the user know they can ignore that row
    passenger_drive_shares = passenger_drive_shares.loc[passenger_drive_shares['Share']!='Will make up the rest']
    freight_drive_shares = freight_drive_shares.loc[freight_drive_shares['Share']!='Will make up the rest']
    
    drive_shares_passenger_dict = df_to_nested_dict(passenger_drive_shares)
    drive_shares_freight_dict = df_to_nested_dict(freight_drive_shares)


    def create_drive_shares_df(df, drive_shares_dict):
        for scenario, regions in drive_shares_dict.items():
            for region, mediums in regions.items():
                for mediums, veh_types in mediums.items():
                    for veh_type, drives in veh_types.items():
                        for drive, shares in drives.items():
                            for share in shares:
                                year = share[1]
                                share_ = share[0]
                                df.loc[(df['Region'] == region) & (df['Vehicle Type'] == veh_type) & (df['Drive'] == drive) & (df['Date'] == year) & (df['Scenario'] == scenario)& (df['Medium'] == mediums), 'Drive_share'] = share_
        return df

    #using the drive shares we laoded in, create a df with which to set the drive shares
    new_sales_shares_passenger_1 = create_drive_shares_df(new_sales_shares_passenger_0, drive_shares_passenger_dict) 
    new_sales_shares_freight_1 = create_drive_shares_df(new_sales_shares_freight_0, drive_shares_freight_dict)
    ############################################################################

    #concatenate transport types
    new_sales_shares_pre_interp = pd.concat([new_sales_shares_passenger_1, new_sales_shares_freight_1])
    #drop regions
    new_sales_shares_pre_interp = new_sales_shares_pre_interp.drop(columns=['Region'])
    
    #TODO NOT SURE IF NECESSARY
    passenger_drive_shares['road'] = passenger_drive_shares['Medium']=='road'
    freight_drive_shares['road'] = freight_drive_shares['Medium']=='road'
    ################################################################################

    new_sales_shares_pre_interp = calcaulte_missing_drive_shares_from_manually_inputted_data(new_sales_shares_pre_interp, model_concordances_user_input_and_growth_rates, passenger_drive_shares, freight_drive_shares,YEARS_TO_KEEP_AFTER_BASE_YEAR)

    #thewn plot the new sales shares before inteproaltions:
    plotting=True
    if plotting:
        plot_user_input_data.plot_input_sales_shares_before_interpolation(new_sales_shares_pre_interp)
    
   
   
  
    ################################################################################################################################################################
    #INTERPOLATE BETWEEN SALES SHARES
    ################################################################################################################################################################
    
    #for each group in new_sales_shares_pre_interp check that there is at least 4 sales share values for the group, so that the interpolation can be done
    new_sales_shares_test = new_sales_shares_pre_interp.copy()
    #drop na in Drive Share col
    new_sales_shares_test = new_sales_shares_test.dropna(subset=['Drive_share'])
    new_sales_shares_test = new_sales_shares_test.groupby(['Economy', 'Scenario','Medium', 'road','Transport Type', 'Vehicle Type', 'Drive']).count().reset_index()
    #where we have very few sales shares to interpoalte by, we can just set the sales share to 0, but tell teh user.
    new_sales_shares_test = new_sales_shares_test.loc[new_sales_shares_test['Date']<=4]
    
    if len(new_sales_shares_test) > 0:
        #get unique groups
        new_sales_shares_test = new_sales_shares_test[['Economy', 'Scenario', 'Transport Type','Medium','road', 'Vehicle Type', 'Drive']].drop_duplicates()
        #print unique groups when you ignore scenario and economy
        new_sales_shares_test_unique = new_sales_shares_test[['Transport Type', 'Medium','Vehicle Type', 'Drive']].drop_duplicates()
        print('#####\nWARNING: The following groups have less than 4 sales shares to interpolate by. Sales shares for these groups will be set to 0 for beginnig years.\n Please check the data and rerun the model if this is not what you want\n#####')
        print(new_sales_shares_test_unique)

        #set sales share to 0 in the begbinning years for these groups by retrievinmg them by index. So set index of both to [['Economy', 'Scenario', 'Transport Type', 'Vehicle Type', 'Drive']] and then set the sales share to 0 for the index of the groups in new_sales_shares_test
        new_sales_shares_test = new_sales_shares_test.set_index(['Economy', 'Scenario', 'Transport Type','Medium','road', 'Vehicle Type', 'Drive'])
        new_sales_shares_pre_interp = new_sales_shares_pre_interp.set_index(['Economy', 'Scenario', 'Transport Type','Medium','road', 'Vehicle Type', 'Drive'])

        common_indices = new_sales_shares_test.index.intersection(new_sales_shares_pre_interp.index)

        new_sales_shares_pre_interp.loc[(new_sales_shares_pre_interp.index.isin(common_indices))&(new_sales_shares_pre_interp['Date']<=config.DEFAULT_BASE_YEAR + YEARS_TO_KEEP_AFTER_BASE_YEAR), 'Drive_share'] = 0

        
        # new_sales_shares_pre_interp.loc[(new_sales_shares_test.index)&(new_sales_shares_pre_interp['Date']<=config.config.DEFAULT_BASE_YEAR + YEARS_TO_KEEP_AFTER_config.config.DEFAULT_BASE_YEAR), 'Drive_share'] = 0
        #reset index
        new_sales_shares_pre_interp = new_sales_shares_pre_interp.reset_index()
    
    ################################################################################
    
    
    #NOW DO INTERPOLATION
    #check for duplicates on the cols we will group by
    new_sales_shares_concat_interp_dupes = new_sales_shares_pre_interp[new_sales_shares_pre_interp.duplicated(subset=['Economy', 'Scenario', 'Date', 'Transport Type','Medium','road', 'Vehicle Type', 'Drive'], keep=False)]
    if len(new_sales_shares_concat_interp_dupes) > 0:
        raise Exception(f'ERROR: DUPLICATES IN NEW SALES SHARES CONCAT INTERP {new_sales_shares_concat_interp_dupes}')
    
    #order data by year
    new_sales_shares_concat_interp = new_sales_shares_pre_interp.sort_values(by=['Economy', 'Scenario', 'Date','road', 'Transport Type', 'Medium','Vehicle Type', 'Drive']).copy()
    
    if X_ORDER == 'linear':
        #do interpolation using spline and order = X
        
        new_sales_shares_concat_interp['Drive_share'] = new_sales_shares_concat_interp.groupby(['Economy', 'Scenario', 'Transport Type','Medium','road', 'Vehicle Type', 'Drive'], group_keys=False)['Drive_share'].apply(lambda group: group.interpolate(method='linear'))
    else:
        #do interpolation using spline and order = X
        
        new_sales_shares_concat_interp['Drive_share'] = new_sales_shares_concat_interp.groupby(['Economy', 'Scenario', 'Transport Type', 'Medium','road','Vehicle Type', 'Drive'])['Drive_share'].apply(lambda group: group.interpolate(method='spline', order=X_ORDER))
    
    #where any values are negatives or na just set them to 0
    
    new_sales_shares_concat_interp.loc[new_sales_shares_concat_interp['Drive_share'].isna(), 'Drive_share'] = 0
    new_sales_shares_concat_interp.loc[new_sales_shares_concat_interp['Drive_share']<0, 'Drive_share'] = 0

    #now we just need to normalise by vehicle type so that the drive share for each vehicle type sums to 1
    new_sales_shares_concat_interp['Drive_sum'] = new_sales_shares_concat_interp.groupby(['Economy', 'Scenario','road', 'Transport Type','Medium', 'Vehicle Type', 'Date'])['Drive_share'].transform('sum')

    new_sales_shares_concat_interp['Drive_share'] = new_sales_shares_concat_interp['Drive_share']/new_sales_shares_concat_interp['Drive_sum']

    #Prepare sum of vehicle type share for each economy, scenario, transport type, vehicle type and date. THis will be used to normalise the drive share for each vehicle type
    new_sales_shares_interp_by_drive = new_sales_shares_concat_interp.drop(['Drive_sum'], axis=1)
    original_new_sales_shares_by_vehicle = new_sales_shares_sum.drop(['Transport_type_share', 'Drive_share'], axis=1)
    #ffill the vehicle type share sum col so that we can times it by the drive share for new years. currently 0 for all new years.
    # #first set all years where all values are 0 to nan so they can be filled
    all_zero_years = original_new_sales_shares_by_vehicle.groupby(['Economy', 'Date','Transport Type', 'road'])['Vehicle_type_share_sum'].apply(lambda group: group.sum()==0).reset_index()
    all_zero_years = all_zero_years.loc[all_zero_years['Vehicle_type_share_sum']==True][['Economy', 'Date','Transport Type', 'road']].drop_duplicates()
    all_zero_years['Vehicle_type_share_sum_nas'] = True
    original_new_sales_shares_by_vehicle = original_new_sales_shares_by_vehicle.merge(all_zero_years, on=['Economy', 'Date','Transport Type', 'road'], how='left')
    original_new_sales_shares_by_vehicle['Vehicle_type_share_sum'] = np.where(original_new_sales_shares_by_vehicle['Vehicle_type_share_sum_nas']==True, np.nan, original_new_sales_shares_by_vehicle['Vehicle_type_share_sum'])
    #original_new_sales_shares_by_vehicle.loc[original_new_sales_shares_by_vehicle['Date'].isin(all_zero_years), 'Vehicle_type_share_sum'] = np.nan
    # original_new_sales_shares_by_vehicle = original_new_sales_shares_by_vehicle
    #now sort by date then ffill
    original_new_sales_shares_by_vehicle = original_new_sales_shares_by_vehicle.sort_values(by=['Economy', 'Scenario', 'Date','road', 'Transport Type','Medium', 'Vehicle Type', 'Drive'])
    original_new_sales_shares_by_vehicle['Vehicle_type_share_sum'] = original_new_sales_shares_by_vehicle.groupby(['Economy', 'Scenario', 'Transport Type','Medium','road', 'Vehicle Type'], group_keys=False)['Vehicle_type_share_sum'].apply(lambda group: group.ffill())

    #now merge the values onto the oroginal df and times by the vehicle type shares
    new_sales_shares_all = new_sales_shares_interp_by_drive.merge(original_new_sales_shares_by_vehicle, on=['Economy', 'Scenario', 'Date', 'Transport Type', 'Vehicle Type', 'Medium','road','Drive'], how='left')

    #times the values to get the final values so that they sum to 1 by transport type
    new_sales_shares_all['Transport_type_share'] = new_sales_shares_all['Vehicle_type_share_sum']*new_sales_shares_all['Drive_share']

    #set any nas to 0
    new_sales_shares_all.loc[new_sales_shares_all['Transport_type_share'].isna(), 'Transport_type_share'] = 0
    ################################################################################################################################################################
    #PLOT INTERPOLATED DATA
    ################################################################################################################################################################
    
    # 
    plotting = True
    
    if plotting:
        plot_user_input_data.plot_new_sales_shares(new_sales_shares_all)
    
    ################################################################################################################################################################
    #APPLY VEHICLE TYPE GROWTH RATES TO SALES SHARES TO FIND SALES SHARE WITHIN EACH TRANSPORT TYPE
    ################################################################################################################################################################
    
    #now apply vehicle_type_growth. 
    # first calcualte teh compound gorwth rate from the xlsx sheet=vehicle_type_growth, (it should be the growth rate . cumprod()) 
    # times that by each Transport_type_share to adjust them for the growth rate
    #then normalise all to 1 by transport type
    vehicle_type_growth_regions = pd.read_excel('input_data/vehicle_sales_share_inputs.xlsx', sheet_name='vehicle_type_growth_regions')
    vehicle_type_growth = pd.read_excel('input_data/vehicle_sales_share_inputs.xlsx', sheet_name='vehicle_type_growth')
    vehicle_type_growth['road'] = vehicle_type_growth['Medium']=='road'
    new_sales_shares_all_new= new_sales_shares_all.copy()
    #use vehicle_type_growth_regions to merge regions to econmy
    new_sales_shares_all_new = new_sales_shares_all_new.merge(vehicle_type_growth_regions, on=['Economy'], how='left')
    #merge vehicle_type_growth to new_sales_shares_all_new
    new_sales_shares_all_new = new_sales_shares_all_new.merge(vehicle_type_growth, on=['Region', 'Scenario', 'Transport Type', 'Medium','road','Vehicle Type'], how='left')
    #cumprod the growth rate (Growth) when grouping by Economy, Scenario, Transport Type, Vehicle Type and drive # but first sort by date
    new_sales_shares_all_new = new_sales_shares_all_new.sort_values(by=['Economy', 'Scenario', 'Transport Type','Medium', 'Vehicle Type','road', 'Drive', 'Date'])
    new_sales_shares_all_new['Compound_growth_rate'] = new_sales_shares_all_new.groupby(['Economy', 'Scenario', 'Transport Type', 'Medium','Vehicle Type','road', 'Drive'])['Growth'].cumprod()
    #apply the growth rate to the Transport_type_share
    new_sales_shares_all_new['Transport_type_share_new'] = new_sales_shares_all_new['Transport_type_share'] * new_sales_shares_all_new['Compound_growth_rate']
    #normalise the Transport_type_share_new to 1
    new_sales_shares_all_new['Transport_type_share_new'] = new_sales_shares_all_new.groupby(['Economy', 'Scenario', 'Date','road','Transport Type'])['Transport_type_share_new'].transform(lambda x: x/x.sum())

    plotting=True
    if plotting:
        plot_user_input_data.plot_new_sales_shares_normalised_by_transport_type(new_sales_shares_all, new_sales_shares_sum,new_sales_shares_all_new)


    #rename Transport_type_share_new to Vehicle^sales_share
    new_sales_shares_all_new = new_sales_shares_all_new.rename(columns={'Transport_type_share_new':'Vehicle_sales_share'})
    #drop cols
    new_sales_shares_all_new = new_sales_shares_all_new.drop(columns=[ 'Drive_share', 'Vehicle_type_share_sum',
        'Transport_type_share', 'Region', 'Growth', 'Compound_growth_rate','road','Vehicle_type_share_sum_nas'])
    #drop dupes
    new_sales_shares_all_new = new_sales_shares_all_new.drop_duplicates()

    
    ###########################################################################
    
    #archive previous results:
    archiving_folder = archiving_scripts.create_archiving_folder_for_FILE_DATE_ID()
    #save previous sales shares
    shutil.copy('input_data/user_input_spreadsheets/Vehicle_sales_share.csv', archiving_folder + '/Vehicle_sales_share.csv')
    #save the variables we used to calculate the data by savinbg the 'input_data/vehicle_sales_share_inputs.xlsx' file
    shutil.copy('input_data/vehicle_sales_share_inputs.xlsx', archiving_folder + '/vehicle_sales_share_inputs.xlsx')

    
    #before saving data to user input spreadsheety we will do some formatting:
    #add cols for Unit,Medium,Data_available, frequency and Measure
    new_sales_shares_all_new['Unit'] = '%'
    new_sales_shares_all_new['Data_available'] = 'data_available'
    new_sales_shares_all_new['Measure'] = 'Vehicle_sales_share'
    new_sales_shares_all_new['Frequency'] = 'Yearly'
    #rename 'Vehicle_sales_share' to 'Value'
    new_sales_shares_all_new = new_sales_shares_all_new.rename(columns={'Vehicle_sales_share':'Value'})

    #final check before saving:
    a = new_sales_shares_all_new.loc[(new_sales_shares_all_new['Measure']=='Vehicle_sales_share') & (new_sales_shares_all_new['Transport Type']=='passenger') & (new_sales_shares_all_new['Date']==2023) & (new_sales_shares_all_new['Economy']=='01_AUS') & (new_sales_shares_all_new['Scenario']=='Reference') &(new_sales_shares_all_new['Medium']=='road')].copy()
    
    if abs(a.Value.sum() - 1) > 0.0001: 
        breakpoint()
        raise ValueError(f'The sum of the vehicle sales share for passenger vehicles in 2019 is not 1, it is {a.Value.sum()}. Please check the user input data and fix this.')
    
    #lastly, as a quick fgix, see if all vlaues for 02_BD non road are na. if so, set them to 0. this is because bd doesnt ahve any non road transport! This seems like the easiest way to make sure they haev no sales but no errors also pop up related to it:
    bandai_non_road = new_sales_shares_all_new.loc[(new_sales_shares_all_new['Economy']=='02_BD')&(new_sales_shares_all_new['Medium']!='road')].copy()
    if bandai_non_road.Value.isna().all():
        new_sales_shares_all_new.loc[(new_sales_shares_all_new['Economy']=='02_BD')&(new_sales_shares_all_new['Medium']!='road'), 'Value'] = 0
    
    #also save the data to the user_input_spreadsheets folder as csv
    new_sales_shares_all_new.to_csv('input_data/user_input_spreadsheets/Vehicle_sales_share.csv', index = False)

#%%


#%%