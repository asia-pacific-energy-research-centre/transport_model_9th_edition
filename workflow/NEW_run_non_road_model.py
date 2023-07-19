# STILL TO DO
#need to do fuel mixes later
# detailed_fuels_dataframe = energy_base_year.merge(biofuel_blending_ratio, on=['Economy', 'Scenario', 'Drive', 'Transport Type', 'Vehicle Type', 'Year'], how='left')
#is there a better way to to the new stock dist?


#%%
#set working directory as one folder back so that config works
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
from runpy import run_path
exec(open("config/config.py").read())#usae this to load libraries and set variables. Feel free to edit that file as you need
#%%

import pandas as pd
import numpy as np

def calculate_turnover_rate(df, k, midpoint):
    df['Turnover_rate'] = 1 / (1 + np.exp(-k * (df['Average_age'] - midpoint)))
    df['Turnover_rate'].fillna(0, inplace=True)
    return df

def load_non_road_model_data(ADVANCE_BASE_YEAR,PROJECT_TO_JUST_OUTLOOK_BASE_YEAR):
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
    non_road_model_input = non_road_model_input.merge(growth_forecasts[['Date', 'Economy','Scenario','Transport Type','Activity_growth']].drop_duplicates(), on=['Date', 'Economy','Scenario','Transport Type'], how='left')
    
    #load the parameters from the config file
    turnover_rate_parameters_dict = yaml.load(open('config/parameters.yml'), Loader=yaml.FullLoader)['turnover_rate_parameters_dict']
    k = turnover_rate_parameters_dict['k']
    midpoint = turnover_rate_parameters_dict['midpoint']
    std_deviation_share = turnover_rate_parameters_dict['std_deviation_share']
    
    if PROJECT_TO_JUST_OUTLOOK_BASE_YEAR:
        #filter all data to just the outlook base year
        non_road_model_input = non_road_model_input.loc[non_road_model_input.Date <= OUTLOOK_BASE_YEAR,:]
    if ADVANCE_BASE_YEAR:
        non_road_model_input = non_road_model_input.loc[non_road_model_input.Date >= OUTLOOK_BASE_YEAR,:]
        
    return non_road_model_input, k, midpoint, std_deviation_share
    

def run_non_road_model(OUTLOOK_BASE_YEAR, output_file, ADVANCE_BASE_YEAR=False, PROJECT_TO_JUST_OUTLOOK_BASE_YEAR=False):
    non_road_model_input, k, midpoint, std_deviation_share = load_non_road_model_data(ADVANCE_BASE_YEAR,PROJECT_TO_JUST_OUTLOOK_BASE_YEAR)
    non_road_model_input.sort_values(by='Date', inplace=True)

    output_df = pd.DataFrame()

    for _, group in non_road_model_input.groupby(['Economy', 'Scenario', 'Medium','Transport Type']):
        for i in range(1, len(group)):
            old_row = group.iloc[i-1].copy()
            new_row = group.iloc[i].copy()

            sum_of_new_activity = old_row['Activity'].sum() * new_row['Activity_growth']
            new_stocks_for_activity = (old_row['Activity'].sum() - sum_of_new_activity[0]) / new_row['Activity_per_Stock']

            new_row = calculate_turnover_rate(new_row, k, midpoint)
            stocks_to_replace = old_row['Stocks'] * new_row['Turnover_rate']

            total_sales_for_that_year = new_stocks_for_activity + stocks_to_replace.sum()

            total_sales_for_that_year = total_sales_for_that_year[0]

            new_row['Stocks'] = (old_row['Stocks'] - stocks_to_replace) + total_sales_for_that_year * new_row['Vehicle_sales_share']

            new_row['Activity'] = new_row['Stocks'] * new_row['Activity_per_Stock']

            if sum_of_new_activity[0] != new_row['Activity'].sum():
                raise ValueError("Sum of new activity doesn't match the calculated value.")

            new_row['Average_age'] = new_row['Average_age'] - (std_deviation_share * new_row['Average_age'] * new_row['Turnover_rate'])  

            denominator = old_row['Stocks'] - old_row['Stocks'] * new_row['Turnover_rate'] + total_sales_for_that_year

            if denominator == 0:
                raise ValueError("Division by zero encountered in Average_age calculation")
            else:
                new_row['Average_age'] = (old_row['Average_age'] * (old_row['Stocks'] - old_row['Stocks'] * new_row['Turnover_rate']) + 0 * total_sales_for_that_year) / denominator

            new_row['Average_age'] = new_row['Average_age'] + 1

            new_row['Intensity'] = old_row['Intensity'] * new_row['Vehicle_intensity_growth']

            new_row['Energy'] = new_row['Activity'] * new_row['Intensity']

            output_df = output_df.append(new_row)

    output_df.to_csv(output_file, index=False)
    