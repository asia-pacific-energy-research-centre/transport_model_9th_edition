# STILL TO DO
#need to do fuel mixes later
# detailed_fuels = energy_base_year.merge(biofuel_blending_ratio, on=['Economy', 'Scenario', 'Drive', 'Transport Type', 'Vehicle Type', 'Year'], how='left')
#is there a better way to to the new stock dist?


#%%
#set working directory as one folder back so that config works
import os
import re
import yaml
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
from runpy import run_path
exec(open("config/config.py").read())#usae this to load libraries and set variables. Feel free to edit that file as you need
#%%
import pandas as pd
import numpy as np

def calculate_turnover_rate(df, k):
    df['Turnover_rate'] = 1 / (1 + np.exp(-k * (df['Average_age'] - df['Turnover_rate_midpoint'])))
    df['Turnover_rate'].fillna(0, inplace=True)
    return df

def load_non_road_model_data(ADVANCE_BASE_YEAR,PROJECT_TO_JUST_OUTLOOK_BASE_YEAR,OUTLOOK_BASE_YEAR,END_YEAR,BASE_YEAR):
    if ADVANCE_BASE_YEAR:
        #load all data except activity data (which is calcualteed separately to other calcualted inputs)
        growth_forecasts = pd.read_pickle('./intermediate_data/road_model/final_road_growth_forecasts_base_year_adv.pkl')
        #load all other data
        non_road_model_input = pd.read_csv('intermediate_data/model_inputs/non_road_model_input_wide_base_year_adv.csv')
    else:
        #load all data except activity data (which is calcualteed separately to other calcualted inputs)
        growth_forecasts = pd.read_pickle('./intermediate_data/road_model/final_road_growth_forecasts.pkl')
        #load all other data
        non_road_model_input = pd.read_csv('intermediate_data/model_inputs/non_road_model_input_wide.csv')

    #Merge growth forecasts with non_road_model_input:
    non_road_model_input.drop(columns=['Activity_growth'], inplace=True)
    non_road_model_input = non_road_model_input.merge(growth_forecasts[['Date', 'Economy','Scenario','Transport Type','Activity_growth']].drop_duplicates(), on=['Date', 'Economy','Scenario','Transport Type'], how='left')
    
    #load the parameters from the config file
    turnover_rate_parameters_dict = yaml.load(open('config/parameters.yml'), Loader=yaml.FullLoader)['turnover_rate_parameters_dict']
    turnover_rate_steepness = turnover_rate_parameters_dict['turnover_rate_steepness']
    std_deviation_share = turnover_rate_parameters_dict['std_deviation_share']
    
    non_road_model_input = non_road_model_input[non_road_model_input['Date']>=BASE_YEAR]
    
    if PROJECT_TO_JUST_OUTLOOK_BASE_YEAR:
        #filter all data to just the outlook base year
        non_road_model_input = non_road_model_input.loc[non_road_model_input.Date <= OUTLOOK_BASE_YEAR,:]
        
    if ADVANCE_BASE_YEAR:
        non_road_model_input = non_road_model_input.loc[non_road_model_input.Date >= OUTLOOK_BASE_YEAR,:]
        non_road_model_input = non_road_model_input.loc[non_road_model_input.Date <= END_YEAR,:]
        
    return non_road_model_input, turnover_rate_steepness, std_deviation_share
    

def run_non_road_model(OUTLOOK_BASE_YEAR,END_YEAR,BASE_YEAR, output_file_name, ADVANCE_BASE_YEAR=False, PROJECT_TO_JUST_OUTLOOK_BASE_YEAR=False):
    non_road_model_input, turnover_rate_steepness, std_deviation_share = load_non_road_model_data(ADVANCE_BASE_YEAR,PROJECT_TO_JUST_OUTLOOK_BASE_YEAR,OUTLOOK_BASE_YEAR,END_YEAR,BASE_YEAR)
     
    #TEMP
    # #set aqcitvity per stock to 1 for all rows
    # non_road_model_input['Activity_per_Stock'] = 1
    
    non_road_model_input.sort_values(by=['Economy', 'Scenario','Transport Type','Date', 'Medium', 'Vehicle Type', 'Drive'])

    output_df = pd.DataFrame()

    for _, group in non_road_model_input.groupby(['Economy', 'Scenario','Transport Type']):
        #this group will contain categorical columns for Date, Medium, Vehicle Type and Drive. It will at times aggreagte them all (except for date, which will be looped through now)
        
        #add data for teh base year:
        previous_year = group[group.Date == non_road_model_input.Date.min()].copy().reset_index(drop=True)
        previous_year = calculate_turnover_rate(previous_year, turnover_rate_steepness)
        
        output_df = pd.concat([output_df,previous_year])
        
        for i in range(non_road_model_input.Date.min()+1, non_road_model_input.Date.max()+1):
            # previous_year = group[group.Date == i-1].copy().reset_index(drop=True)
            current_year = group[group.Date == i].copy().reset_index(drop=True)
            #set average age to the previous year's average age
            current_year['Average_age'] = previous_year['Average_age']
            
            new_activity = previous_year['Activity'] * current_year['Activity_growth']
            total_new_stocks_for_activity = ((new_activity - previous_year['Activity']) / current_year['Activity_per_Stock']).sum()
            breakpoint()#it seems turnover rate sint changing
            current_year = calculate_turnover_rate(current_year, turnover_rate_steepness)
            stocks_to_replace = previous_year['Stocks'] * current_year['Turnover_rate']

            total_sales_for_that_year = total_new_stocks_for_activity + stocks_to_replace.sum()

            new_stocks = total_sales_for_that_year * current_year['Vehicle_sales_share']

            current_year['Stocks'] = previous_year['Stocks'] - stocks_to_replace + new_stocks

            current_year['Activity'] = current_year['Stocks'] * current_year['Activity_per_Stock']

            # if abs(new_activity.sum() - current_year['Activity'].sum()) > 0.0000001:
            #     raise ValueError("Sum of new activity doesn't match the calculated value.")
            #soemthing doesnt add up in the above
            current_year['Average_age'] = current_year['Average_age'] - (std_deviation_share * current_year['Average_age'] * current_year['Turnover_rate'])  

            age_denominator = current_year['Stocks']
            #reaplce 0's in age denominator with 1's to avoid division by zero
            age_denominator = age_denominator.replace(0,1)
            #average age is: (age of old stock * old stocks remaining) + (age of new stock * new stocks) / total stocks
            #where age of new stocks is 0
            current_year['Average_age'] = (previous_year['Average_age'] * (previous_year['Stocks'] - stocks_to_replace) + 0 * new_stocks) / age_denominator
            
            #where stocks are 0, average age is 0
            current_year['Average_age'] = current_year['Average_age'].replace(np.nan,0)

            #even though this was just set to 0, it will be incremented by 1 to both reflect passing of time and also to avoid division by zero in next year
            current_year['Average_age'] = current_year['Average_age'] + 1

            current_year['Intensity'] = previous_year['Intensity'] * current_year['Non_road_intensity_improvement']

            current_year['Energy'] = current_year['Activity'] * current_year['Intensity']

            output_df = pd.concat([output_df, current_year])
            
            #set previous_year to current_year for next iteration
            previous_year = current_year.copy()

    output_df.to_csv(output_file_name, index=False)
    
#%%
# OUTLOOK_BASE_YEAR = 2020
# PROJECT_TO_JUST_OUTLOOK_BASE_YEAR=True
# output_file_name = 'intermediate_data/non_road_model/{}'.format(model_output_file_name)
# run_non_road_model(OUTLOOK_BASE_YEAR,END_YEAR,BASE_YEAR, output_file_name, ADVANCE_BASE_YEAR=False, PROJECT_TO_JUST_OUTLOOK_BASE_YEAR=False)
#%%