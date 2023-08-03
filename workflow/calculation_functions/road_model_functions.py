#######################################################################
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

#######################################################################
#%%


def run_road_model_for_year_y(year, previous_year_main_dataframe, main_dataframe, user_inputs_df_dict, growth_forecasts, change_dataframe_aggregation,  low_ram_computer_files_list, low_ram_computer, ANALYSE_CHANGE_DATAFRAME,previous_10_year_block,   turnover_rate_parameters_dict):
    print('Up to year {}'.format(year))
    # breakpoint()
    #extract the user inputs dataframes from the dictionary
    Vehicle_sales_share = user_inputs_df_dict['Vehicle_sales_share']
    Occupancy_or_load_growth = user_inputs_df_dict['Occupancy_or_load_growth']
    # Turnover_rate_growth = user_inputs_df_dict['Turnover_rate_growth']
    New_vehicle_efficiency_growth = user_inputs_df_dict['New_vehicle_efficiency_growth']
    Mileage_growth = user_inputs_df_dict['Mileage_growth']
    
    #extracts vars from turnover_rate_parameters_dict:
    turnover_rate_steepness = turnover_rate_parameters_dict['turnover_rate_steepness']

    #create change dataframe. This is like a messy notepad where we will adjust the last years values values and perform most calcualtions. 
    change_dataframe = previous_year_main_dataframe.copy()

    #change year in all rows to the next year. For now we will refer to the previous year as the original or base year. And values calculcated for the next year may sometimes be refered to as 'new'.
    change_dataframe.Date = year
    do_tests_on_road_data(change_dataframe)
    #######################################################################

    #First do adjustments:

    #######################################################################

    #CALCUALTE NEW OCCUPANCY and LOAD VALUEs BY APPLYING THE OCCUPANCY GROWTH RATE
    change_dataframe = change_dataframe.merge(Occupancy_or_load_growth, on=['Economy','Scenario','Drive','Vehicle Type', 'Transport Type', 'Date'], how='left')
    change_dataframe['Occupancy_or_load'] = change_dataframe['Occupancy_or_load'] * change_dataframe['Occupancy_or_load_growth']

    #repalce nas in change_dataframe['Average_age'] with 1, as it occurs when tehre are no stocks, and we want to set the average age to 1. Im not 100% on this fix but it seems like tis important to do as im getting 0s for stocks for all years when i dont do it.
    change_dataframe['Average_age'] = change_dataframe['Average_age'].replace(np.nan, 1)
    #and replace 0s too
    change_dataframe['Average_age'] = change_dataframe['Average_age'].replace(0, 1)
    
    def calculate_turnover_rate(df, k):
        
        # k = 0.7 #this is the steepness of the curve (increase it to speed up the turnover rate growth with age)
        # x0 = 12.5 #this is the midpoint of the curve (increase it to make the turnover rate growth start later in the life of the vehicle)
        df['Turnover_rate'] = 1 / (1 + np.exp(-k * (df['Average_age'] - df['Turnover_rate_midpoint'])))
        
        df['Turnover_rate'].fillna(0, inplace=True)
        return df

    change_dataframe = calculate_turnover_rate(change_dataframe, turnover_rate_steepness)
    #CALCULATE PREVIOUSLY AVAILABLE STOCKS AS SUM OF STOCKS AND SURPLUS STOCKS
    change_dataframe['Original_stocks'] = change_dataframe['Stocks'] + change_dataframe['Surplus_stocks']
    #calcualte stock turnover as stocks from last year * turnover rate.
    change_dataframe['Stock_turnover'] = - change_dataframe['Stocks'] * change_dataframe['Turnover_rate']
    #calculate stock turnover plus surplus
    change_dataframe['Stock_turnover_and_surplus_total'] = change_dataframe['Stock_turnover'] + change_dataframe['Surplus_stocks'] 
    #if 'Activity_growth', 'Gdp_per_capita', 'Population' is in df, drop em
    change_dataframe = change_dataframe.drop(['Activity_growth', 'Gdp_per_capita','Gdp', 'Population'], axis=1, errors='ignore')
    #join on activity growth
    change_dataframe = change_dataframe.merge(growth_forecasts[['Date', 'Transport Type', 'Economy','Scenario','Gdp','Activity_growth', 'Gdp_per_capita', 'Population']], on=['Economy', 'Date', 'Scenario','Transport Type'], how='left')#note that pop and gdp per capita are loaded on earlier.
    #######################################################################

    #Calcualtions

    ########################################################################

    #CALCUALTE ACTIVITY WORTH OF STOCK TURNOVER AND SURPLUS
    change_dataframe['Activity_worth_of_stock_turnover_and_surplus'] = change_dataframe['Stock_turnover_and_surplus_total'] * change_dataframe['Mileage'] * change_dataframe['Occupancy_or_load']

    #Stocks after turnover and surplus total 
    change_dataframe['Stocks_after_turnover_and_surplus_total'] = change_dataframe['Stocks'] + change_dataframe['Stock_turnover_and_surplus_total']

    #Activity worth of stocks after turnover and surplus total
    change_dataframe['Activity_worth_of_stocks_after_turnover_and_surplus_total'] = change_dataframe['Stocks_after_turnover_and_surplus_total'] * change_dataframe['Mileage'] * change_dataframe['Occupancy_or_load']

    #Transport type sum of activity worth of stocks after turnover and surplus total
    change_dataframe['Transport_type_sum_of_activity_worth_of_stocks_after_turnover_and_surplus_total'] = change_dataframe.groupby(['Economy', 'Scenario', 'Transport Type', 'Date'])['Activity_worth_of_stocks_after_turnover_and_surplus_total'].transform('sum')

    #######################################################################
    #Now calcualte changes as a result of growth (and other things)
    #We will be working in terms of transport type sums for this section:
    #######################################################################

    #CALCULATE NEW ACTIVITY WORTH OF STOCK SALES
    #we will apply activity growth to the sum of activity for each transport type to find the activity worth of new sales from activity growth. Note that activity growth is assumed to be the same for all vehicle types of the same transport type (and probably for all transport types in early stages of this models development!)
    #We will also calcualte total turnover and surplus activity for the transport type to be satisfied by new stock sales, based on the new sales dist.

    # Calculate sum of activity
    grouped = change_dataframe.groupby(['Economy', 'Scenario', 'Transport Type', 'Date'])
    change_dataframe['Transport_type_sum_of_activity'] = grouped['Activity'].transform('sum')

    # Calculate growth
    change_dataframe['Transport_type_sum_of_activity_growth'] = change_dataframe['Activity_growth'] * change_dataframe['Transport_type_sum_of_activity'] - change_dataframe['Transport_type_sum_of_activity']

    # Calculate the shortfall or excess of stocks based on the growth
    stock_after_turnover_and_surplus = change_dataframe['Transport_type_sum_of_activity_worth_of_stocks_after_turnover_and_surplus_total']
    sum_of_activity = change_dataframe['Transport_type_sum_of_activity']
    activity_growth = change_dataframe['Transport_type_sum_of_activity_growth']

    difference = stock_after_turnover_and_surplus - sum_of_activity - activity_growth

    change_dataframe['Transport_type_sum_of_activity_worth_of_extra_stocks_needed'] = np.where(difference < 0, -difference, 0)
    change_dataframe['Transport_type_sum_of_activity_worth_of_extra_stocks_remaining'] = np.where(difference > 0, difference, 0)

    ###############
    #% of transport type stocks worth of activity not used (transport type)
    change_dataframe['Percent_of_transport_type_stocks_worth_of_activity_not_used'] = change_dataframe['Transport_type_sum_of_activity_worth_of_extra_stocks_remaining'] / change_dataframe['Transport_type_sum_of_activity_worth_of_stocks_after_turnover_and_surplus_total']
    #replace na's where there is 0/0 above
    change_dataframe['Percent_of_transport_type_stocks_worth_of_activity_not_used'] = change_dataframe['Percent_of_transport_type_stocks_worth_of_activity_not_used'].replace(np.nan, 0)

    #TEMP TEST (trying to prevent stocks from going negative)
    #if percent of transport type stocks worth of activity not used is greater than 1, set it to 1, as if it is greater than one then the stocks will go negative, as the 'stocks not used' is greater than the stocks available!
    change_dataframe['Percent_of_transport_type_stocks_worth_of_activity_not_used'] = np.where(change_dataframe['Percent_of_transport_type_stocks_worth_of_activity_not_used'] > 1, 1, change_dataframe['Percent_of_transport_type_stocks_worth_of_activity_not_used'])
    #######################################################################
    #Now we will start working with inidivudal rows, for each vehicle type and drive combination.
    #######################################################################

    #Total surplus stocks worth of activity 
    change_dataframe['Total_surplus_stocks_worth_of_activity'] = change_dataframe['Activity_worth_of_stocks_after_turnover_and_surplus_total'] * change_dataframe['Percent_of_transport_type_stocks_worth_of_activity_not_used']

    #VEHICLE SALES SHARE(also referreed to as Sales/Stock Dist)
    #New Activity worth of sales will be satisfied by different vehicle type / drive type combinations, as specified by the Vehicle_sales_share (stock/sales dist). Each year there is a new sales share, created by the user before running the model
    #1. merge onto the main df the vehicle sales share that user has specified 
    #Also, if there is already a Vehicle_sales_share column from the prev year, remove it (we keep the vehicle sales shbare in the change dataframe because its an extra interesting output)
    if 'Vehicle_sales_share' in change_dataframe.columns:
        change_dataframe.drop(columns=['Vehicle_sales_share'], inplace=True)
    # 
    # #get change_dataframe where the vehicle type is ht and drive is bev
    # a = change_dataframe.loc[(change_dataframe['Vehicle Type'] == 'ht') & (change_dataframe['Drive'] == 'bev')]
    change_dataframe = change_dataframe.merge(Vehicle_sales_share, on=['Economy', 'Scenario', 'Drive', 'Transport Type', 'Vehicle Type', 'Date'], how='left')

    #CALCULATE STOCK SALES TO BE SATISFIED BY EACH VEHICLETYPE/DRIVETYPE COMBINATION USING THE NEW VEHICLE SALES SHARES
    #Note that if Activity worth of extra stocks needed can be 0, and if so then this will be 0 too.
    #TEMP IF Transport_type_sum_of_activity_worth_of_extra_stocks_needed IS <0 THEN PERHAPS WE NEED TO INVERSE AND NORMALISE VEHICLE SALES SHARE SO THE LEAST WANTED STOCKS ARE SOLD FIRST. THIS IS A TEMP FIX TO PREVENT STOCKS FROM GOING NEGATIVE?
    if (change_dataframe['Transport_type_sum_of_activity_worth_of_extra_stocks_needed'] < 0).any():
        breakpoint()
        print('There are negative stocks needed')
        raise ValueError('There are negative stocks needed')
    change_dataframe['Activity_worth_of_new_stock_sales'] = change_dataframe['Transport_type_sum_of_activity_worth_of_extra_stocks_needed'] * change_dataframe['Vehicle_sales_share']

    #CALCULATE NEW activity total of stocks being used as ACTIVITY
    change_dataframe['Activity'] = change_dataframe['Activity_worth_of_new_stock_sales'] + change_dataframe['Activity_worth_of_stocks_after_turnover_and_surplus_total'] - change_dataframe['Total_surplus_stocks_worth_of_activity']
    
    #CALCUALTE NEW TOTAL TRAVEL_KM PER VEHICLE/DRIVE-TYPE FROM NEW activity total of stocks being useD
    change_dataframe['Travel_km'] = change_dataframe['Activity'] / change_dataframe['Occupancy_or_load']

    #CALCUALTE NEW TOTAL TRAVEL_KM PER VEHICLE/DRIVE-TYPE FROM NEW STOCKS
    change_dataframe['Travel_km_of_new_stocks'] = change_dataframe['Activity_worth_of_new_stock_sales'] / change_dataframe['Occupancy_or_load']

    #CALCUALTE NEW TRAVEL_KM PER NEW VEHICLE/DRIVE-TYPE FROM NEW SALES WORTH OF ACTIVITY
    change_dataframe['Travel_km_of_surplus_stocks'] = change_dataframe['Total_surplus_stocks_worth_of_activity'] / change_dataframe['Occupancy_or_load']

    #CALCUALTE STOCKS BEING USED
    #Note that this is the new level of stocks in the economy
    change_dataframe['Stocks'] = change_dataframe['Travel_km'] / change_dataframe['Mileage']

    #TEMP IF Stocks IS <0 THEN PERHAPS WE NEED TO INVERSE AND NORMALISE VEHICLE SALES SHARE SO THE LEAST WANTED STOCKS ARE SOLD FIRST. THIS IS A TEMP FIX TO PREVENT STOCKS FROM GOING NEGATIVE?
    if (change_dataframe['Stocks'] < 0).any():
        breakpoint()
        raise ValueError('There are negative stocks')
    
    #CALCUALTE NEW STOCKS NEEDED AS STOCKS NEEDED TO SATISFY NEW SALES WORTH OF ACTIVITY
    change_dataframe['New_stocks_needed'] = change_dataframe['Travel_km_of_new_stocks'] / change_dataframe['Mileage']
    
    # Calculate new mean age after turnover
    change_dataframe = calculate_new_average_age_of_stocks(change_dataframe)
    
    change_dataframe['Age_denominator'] = (change_dataframe['Original_stocks'] - change_dataframe['Original_stocks'] * change_dataframe['Turnover_rate'] + change_dataframe['New_stocks_needed']).replace(0,1)
    #now calcualte verage age after adding new vehicles too:
    change_dataframe['Average_age'] = (change_dataframe['Average_age'] * (change_dataframe['Original_stocks'] - change_dataframe['Original_stocks'] * change_dataframe['Turnover_rate']) + 0 * change_dataframe['New_stocks_needed']) / change_dataframe['Age_denominator']
    #note that you times 0*change_dataframe['New_stocks_needed'] by the average age of the new stocks, as they have an average age of 0. it is there for understanding.
    #increase age by 1 year to simulate the fact that the cars are 1 year older
    change_dataframe['Average_age'] = change_dataframe['Average_age'] + 1
    
    #CALCUALTE SURPLUS STOCKS
    #If we have too many stocks these go into surplus
    change_dataframe['Surplus_stocks'] = change_dataframe['Travel_km_of_surplus_stocks'] / change_dataframe['Mileage']

    #CALCULATE STOCKS IN USE REMAINING FROM PREVIOUS YEAR
    change_dataframe['Stocks_in_use_from_last_period'] = change_dataframe['Stocks'] - change_dataframe['New_stocks_needed']

    #SET EFFICIENCY OF SURPLUS STOCKS TO PREVIOUS YEARS AVG EFF LEVEL
    #Note that we assume that the efficiency of surplus stocks is the same as the efficiency of the stocks that were in use last year
    change_dataframe['Efficiency_of_surplus_stocks'] = change_dataframe['Efficiency']

    #APPLY EFFICIENCY GROWTH TO NEW VEHICLE EFFICIENCY
    #note that this will then be split into different fuel types when we appply the fuel mix varaible later on.
    #also note that new vehicle eff is independent of the current eff level of the eocnomys stocks. it could be much higher than them
    change_dataframe = change_dataframe.merge(New_vehicle_efficiency_growth, on=['Economy', 'Scenario', 'Transport Type', 'Drive', 'Vehicle Type', 'Date'], how='left')
    change_dataframe['New_vehicle_efficiency'] = change_dataframe['New_vehicle_efficiency'] * change_dataframe['New_vehicle_efficiency_growth'] 

    #CALCUALTE WEIGHTED AVERAGE VEHICLE EFFICIENCY
    #calcaulte weighted avg vehicle eff using the number of stocks left from last year times their avg eff, then the number of new stocks needed times their new eff. Then divide these by the number of stocks left from last year plus the number of new stocks needed. 
    #however if new stocks needed is <0, but there are still stocks remaining in the economy then efficiency will remain the same as original efficiency.
    #also have to note that this is the avg eff of stocks in use, this is in case there is a large amount of surplus stocks, so that the avg eff of the economy is not skewed by the efficiency of the surplus stocks, and instead new stocks efficiency has the right effect on the avg eff of the economy.
    change_dataframe['Efficiency_numerator'] = (change_dataframe['New_stocks_needed'] * change_dataframe['New_vehicle_efficiency'] + change_dataframe['Stocks_in_use_from_last_period'] * change_dataframe['Efficiency'])

    change_dataframe['Original_efficiency'] = change_dataframe['Efficiency']
    
    change_dataframe['Efficiency'] = np.where(change_dataframe['New_stocks_needed'] <= 0, change_dataframe['Original_efficiency'], change_dataframe['Efficiency_numerator'] / change_dataframe['Stocks'])

    #if the denominator and numerator are 0 (which will occur if we dont have any stocks in this year [and therefore the last]), then efficiency ends up as nan, so we will set this to the efficiency value for new vehicles even though it doesnt really matter what it is set to, it just helps with aggregates.
    change_dataframe.loc[(change_dataframe['Stocks'] == 0), 'Efficiency'] = change_dataframe['New_vehicle_efficiency']

    #CALCUALTE NEW ENERGY CONSUMPTION. 
    #note that this is not split by fuel yet, it is just the total energy consumption for the vehicle/drive type.
    change_dataframe['Energy'] = change_dataframe['Travel_km'] / change_dataframe['Efficiency'] 
    
    #if numerator and denominator are 0, then energy ends up as nan, so we will set this to 0
    change_dataframe.loc[(change_dataframe['Travel_km'] == 0) & (change_dataframe['Efficiency'] == 0), 'Energy'] = 0
    # breakpoint()
    #######################################################################

    #finalisation processes

    #######################################################################
    
    #calcualte stocks per capita as its a useful metric
    change_dataframe['Thousand_stocks_per_capita'] = change_dataframe['Stocks']/change_dataframe['Population']
    change_dataframe['Stocks_per_thousand_capita'] = change_dataframe['Thousand_stocks_per_capita'] * 1000000

    #Now start cleaning up the changes dataframe to create the dataframe for the new year.
    addition_to_main_dataframe = change_dataframe.copy()
    
    addition_to_main_dataframe = addition_to_main_dataframe[config.ROAD_MODEL_OUTPUT_COLS].copy()
    # 
    #add new year to the main dataframe.
    main_dataframe = pd.concat([main_dataframe, addition_to_main_dataframe])
    previous_year_main_dataframe = addition_to_main_dataframe.copy()

    #if you want to analyse what is hapening in th model then set this to true and the model will output a dataframe with all the variables that are being calculated.
    if ANALYSE_CHANGE_DATAFRAME:
        if year == config.DEFAULT_BASE_YEAR+1:
            change_dataframe_aggregation = change_dataframe.copy()
        else:
            change_dataframe_aggregation = pd.concat([change_dataframe, change_dataframe_aggregation])

    #if we have a low ram computer then we will save the dataframe to a csv file at 10 year intervals. this is to save memory. during the proecss we will save a list of the file names that we have saved to, from which to stitch the new dataframe togehter from
    if low_ram_computer == True:
        year_counter = year - config.DEFAULT_BASE_YEAR
        if year_counter % 10 == 0:
            print('The year is at the end of a ten year block, in year {}, saving interemediate results to csv.'.format(year))
            low_ram_file_name = 'intermediate_data/main_dataframe_10_year_blocks/main_dataframe_years_{}_to_{}.csv'.format(previous_10_year_block, year)
            main_dataframe.to_csv(low_ram_file_name, index=False)
            low_ram_computer_files_list.append(low_ram_file_name)

            previous_10_year_block = year
            main_dataframe = pd.DataFrame(columns=main_dataframe.columns)#remove data we just saved from main datafrmae

        elif year == config.END_YEAR:
            print('The year is at the end of the simulation, saving intermediate results to csv.')
            low_ram_file_name = 'intermediate_data/main_dataframe_10_year_blocks/main_dataframe_years_{}_to_{}.csv'.format(previous_10_year_block, year)
            main_dataframe.to_csv(low_ram_file_name, index=False)
            low_ram_computer_files_list.append(low_ram_file_name)
            
    return main_dataframe,previous_year_main_dataframe, low_ram_computer_files_list, change_dataframe_aggregation,  previous_10_year_block
    
def calculate_new_average_age_of_stocks(change_dataframe):
    # Parameters
    z_score = 1.645  # for the oldest 5%

    # Calculate the standard deviation of ages
    change_dataframe['std_dev_age'] = (1/3) * change_dataframe['Average_age']

    # Calculate age threshold for the oldest cars
    change_dataframe['age_threshold'] = change_dataframe['Average_age'] + z_score * change_dataframe['std_dev_age']

    # Estimate the average age of the oldest cars
    change_dataframe['average_age_of_oldest_cars'] = change_dataframe['age_threshold']

    # Calculate the total age of all cars
    change_dataframe['total_age'] = change_dataframe['Average_age'] * change_dataframe['Stocks']

    # Calculate the number of cars to be replaced
    change_dataframe['cars_to_replace'] = change_dataframe['Stocks'] * change_dataframe['Turnover_rate']

    # Calculate the total age of cars to be replaced
    change_dataframe['age_to_replace'] = change_dataframe['average_age_of_oldest_cars'] * change_dataframe['cars_to_replace']

    # Subtract the age of the cars being replaced from the total age
    change_dataframe['new_total_age'] = change_dataframe['total_age'] - change_dataframe['age_to_replace']

    # Calculate the new average age
    change_dataframe['Average_age'] = change_dataframe['new_total_age'] / (change_dataframe['Stocks'] - change_dataframe['cars_to_replace'])

    #Replace any negative agees with 0
    change_dataframe['Average_age'] = np.where(change_dataframe['Average_age'] < 0, 0, change_dataframe['Average_age'])
    
    #drop cols
    change_dataframe = change_dataframe.drop(['std_dev_age', 'age_threshold', 'average_age_of_oldest_cars', 'total_age', 'cars_to_replace', 'age_to_replace', 'new_total_age'], axis=1)
    # Return the updated dataframe
    return change_dataframe

def prepare_road_model_inputs(road_model_input, ECONOMY_ID, low_ram_computer=True):
    """
    Prepares the road model inputs for use in the model.

    Args:
        road_model_input (pandas.DataFrame): The road model input data.
        ECONOMY_ID (str): The ID of the economy to prepare the inputs for.
        low_ram_computer (bool): Whether the computer has low RAM. Defaults to True.

    Returns:
        pandas.DataFrame: The prepared road model input data.
    """
    # function code here
    #separate user inputs into different dataframes
    
    #GOMPERTZ PARAMETERS ARE USED TO SET A LIMIT ON STOCKS PER CPITA. WE NEED TO LOAD THEM IN HERE AND MERGE THEM ONTO THE MAIN DATAFRAME.      
    # We also need to set them to be non nan for the base year, as the base year has its values for inputs set to nan.
    gompertz_parameters = pd.read_csv('intermediate_data/model_inputs/{}/stocks_per_capita_threshold.csv'.format(config.FILE_DATE_ID))
    #filter for economy id only:
    gompertz_parameters = gompertz_parameters[gompertz_parameters['Economy']==ECONOMY_ID].copy()
    base_year = road_model_input.Date.min()
    #replace values for BASE YEAR with values from the first calculated year of the model
    BASE_YEAR_gompertz_parameters = gompertz_parameters[gompertz_parameters['Date']==gompertz_parameters['Date'].min()].copy()
    BASE_YEAR_gompertz_parameters['Date'] = base_year
    gompertz_parameters = pd.concat([gompertz_parameters[gompertz_parameters['Date']!=base_year], BASE_YEAR_gompertz_parameters], ignore_index=True)
    
    #and the rest of the user inputs:
    Vehicle_sales_share = road_model_input[['Economy','Scenario', 'Drive', 'Vehicle Type', 'Transport Type', 'Date', 'Vehicle_sales_share']].drop_duplicates().copy()
    Occupancy_or_load_growth = road_model_input[['Economy','Scenario', 'Drive','Vehicle Type', 'Transport Type', 'Date', 'Occupancy_or_load_growth']].drop_duplicates().copy()
    New_vehicle_efficiency_growth = road_model_input[['Economy','Scenario', 
    'Vehicle Type', 'Transport Type', 'Drive', 'Date', 'New_vehicle_efficiency_growth']].drop_duplicates().copy()
    Mileage_growth = road_model_input[['Economy','Scenario', 'Drive', 'Vehicle Type', 'Transport Type', 'Date', 'Mileage_growth']].drop_duplicates().copy()

    #put the dataframes into a dictionary to pass into the funciton togetehr:
    user_inputs_df_dict = {'Vehicle_sales_share':Vehicle_sales_share, 'Occupancy_or_load_growth':Occupancy_or_load_growth, 'New_vehicle_efficiency_growth':New_vehicle_efficiency_growth, 'Mileage_growth':Mileage_growth, 'gompertz_parameters':gompertz_parameters}

    #drop those cols
    road_model_input = road_model_input.drop(['Vehicle_sales_share', 'Occupancy_or_load_growth', 'New_vehicle_efficiency_growth','Mileage_growth'], axis=1)#'Gompertz_alpha', 'Gompertz_beta',

    #create main dataframe as previous Date dataframe, so that currently it only holds the base Date's data. This will have each Dates data added to it at the end of each loop.
    previous_year_main_dataframe = road_model_input.loc[road_model_input.Date == road_model_input.Date.min(),:].copy()
    main_dataframe = previous_year_main_dataframe.copy()
    change_dataframe_aggregation = pd.DataFrame()

    #give option to run the process on a low RAM computer. If True then the loop will be split into 10 year blocks, saving each block in a csv, then starting again with an empty main datafrmae for the next 10 years block. If False then the loop will be run on all years without saving intermediate results.
    if low_ram_computer:
        previous_10_year_block = road_model_input.Date.min()
        low_ram_computer_files_list = []
        #remove files from main_dataframe_10_year_blocks for previous runs
        for file in glob.glob(os.path.join('intermediate_data/main_dataframe_10_year_blocks/', '*.csv')):
            os.remove(file)
    else:
        previous_10_year_block = None
        low_ram_computer_files_list = None

    return main_dataframe,previous_year_main_dataframe, low_ram_computer_files_list, change_dataframe_aggregation,previous_10_year_block, user_inputs_df_dict,low_ram_computer


def join_and_save_road_model_outputs(ECONOMY_ID, main_dataframe, low_ram_computer, low_ram_computer_files_list,ANALYSE_CHANGE_DATAFRAME,change_dataframe_aggregation, first_model_run_bool):
    if first_model_run_bool:
        new_output_file = 'intermediate_data/road_model/first_run_{}_{}'.format(ECONOMY_ID, config.model_output_file_name)
    else:
        #this will be the name of the output file
        new_output_file = 'intermediate_data/road_model/{}_{}'.format(ECONOMY_ID, config.model_output_file_name)

    #now, we will save the main dataframe to a csv file. if the computer is low ram, we will create the file from the already saved 10 year block interval files
    if low_ram_computer == True:
        main_dataframe = pd.DataFrame()
        print('The computer is low ram, stitching together the main dataframe from the 10 year block files.')

        #first check the file we will be writing to doesnt already exist, if so, delete it
        if os.path.exists(new_output_file):
            os.remove(new_output_file)

        for file_i in low_ram_computer_files_list:
            print('Reading file {}'.format(file_i))
            low_ram_dataframe = pd.read_csv(file_i)
            #write to csv
            low_ram_dataframe.to_csv(new_output_file,mode='a', header=not os.path.exists(new_output_file),index=False)
            #remove file 
            os.remove(file_i)
            main_dataframe = pd.concat([main_dataframe,low_ram_dataframe])

        # main_dataframe.to_csv(new_output_file, index=False)
        print('The main dataframe has been written to {}'.format(new_output_file))
    else:
        print('The computer is not low ram, saving the main dataframe to a csv.')
        main_dataframe.to_csv(new_output_file, index=False)

    if ANALYSE_CHANGE_DATAFRAME:
        #save dataframe
        change_dataframe_aggregation.to_csv('intermediate_data/road_model/change_dataframe_aggregation.csv', index=False)

    return main_dataframe



def do_tests_on_road_data(change_dataframe):
    test_data_frame = change_dataframe.copy()
    test_data_frame['Activity_check'] = test_data_frame['Mileage'] * test_data_frame['Occupancy_or_load'] * test_data_frame['Stocks']
    #why dont all othese equal each otehr???
    # #also check test_data_frame['Activity'] the other way
    test_data_frame['Activity_check2'] = test_data_frame['Energy'] *  test_data_frame['Efficiency'] * test_data_frame['Occupancy_or_load']
    test_data_frame['Activity_check_diff'] = test_data_frame['Activity_check'] - test_data_frame['Activity_check2']
    

    if not np.allclose(test_data_frame['Activity_check'], test_data_frame['Activity']) or not np.allclose(test_data_frame['Activity_check2'], test_data_frame['Activity']):
        throw_error=True
        a_check = sum(test_data_frame['Activity_check'].dropna())+1
        a_original = 1+sum(test_data_frame['Activity'].dropna())
        percent_difference = ((a_check - a_original) / a_original)*100
        
        a_check2 = sum(test_data_frame['Activity_check2'].dropna())+1
        a_original2 = 1+sum(test_data_frame['Activity'].dropna())
        percent_difference2 = ((a_check2 - a_original2) / a_original2)*100
        # #extract the rows where the activity is not equal to Activity_check
        # bad_rows = test_data_frame[test_data_frame['Activity_check'] != test_data_frame['Activity']]
        # #find the diff in each row
        # bad_rows['diff'] = bad_rows['Activity_check'] - bad_rows['Activity']
        if abs(percent_difference) > 0.5 or abs(percent_difference2) > 0.5:
            breakpoint()
            if throw_error:
                raise ValueError('ERROR: Activity does not match sum of activity. percent_difference = {}'.format(percent_difference)) 
            else:
                print('ERROR: Activity does not match sum of activity. percent_difference = {}'.format(percent_difference)) 





