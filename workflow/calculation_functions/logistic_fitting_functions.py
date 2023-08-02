
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
import plot_logistic_fitting_data
from scipy.optimize import curve_fit
#######################################################################
#######################################################################
#######################################################################
#######################################################################
#LOGISTIC FITTING FUNCTIONS
#######################################################################
#######################################################################
#######################################################################
#######################################################################
def convert_stocks_to_gompertz_adjusted_stocks(model_data,vehicle_gompertz_factors):
    
    #Convert some stocks to gompertz adjusted stocks by multiplying them by the vehicle_gompertz_factors. This is because you can expect some economies to have more or less of that vehicle type than others. These are very general estiamtes, and could be refined later.
    cols_to_sum_by = ['Economy', 'Scenario', 'Date', 'Transport Type']
    new_stocks = model_data.copy()
    for ttype in vehicle_gompertz_factors.keys():
        new_stocks.loc[(new_stocks['Vehicle Type'] == ttype), 'Stocks'] = new_stocks.loc[(new_stocks['Vehicle Type'] == ttype), 'Stocks'] * vehicle_gompertz_factors[ttype]
    #sum up new stocks and other values specific to each vehicle type
    new_stocks = new_stocks[cols_to_sum_by+['Stocks','Activity', 'Travel_km']].groupby(cols_to_sum_by).sum().reset_index()
    
    #now, as we are going to reestiamte the growth rate using adjusted stocks, and these stocks are goign to be timesed by their vehicle_gompertz_factors and summed, we need to come up with the equivalent mileage and Occupancy_or_load weighted average for each transport ytpe, using a weighting based on the amount of stocks for each vehicle type. this will prevent them from ebeing overexagerated due to the effect of rarer vehicle types which have higher values for these cols, which will increase effective activity (eg buses have high occupancy and mielsage comapred to 2w, but a fraction of the stoskcs).
    weighted_average_model_data = model_data.copy()
    weighted_average_model_data = weighted_average_model_data[cols_to_sum_by+['Mileage','Occupancy_or_load','Stocks']].drop_duplicates()
    weighted_average_model_data['Mileage'] = weighted_average_model_data['Mileage'] * weighted_average_model_data['Stocks']
    weighted_average_model_data['Occupancy_or_load'] = weighted_average_model_data['Occupancy_or_load'] * weighted_average_model_data['Stocks']
    #then sum and divide these cols by the sum of stocks
    weighted_average_model_data = weighted_average_model_data.groupby(cols_to_sum_by).sum().reset_index()
    weighted_average_model_data['Mileage'] = weighted_average_model_data['Mileage'] / weighted_average_model_data['Stocks']
    weighted_average_model_data['Occupancy_or_load'] = weighted_average_model_data['Occupancy_or_load'] / weighted_average_model_data['Stocks']
    #drop 'Stocks'
    weighted_average_model_data = weighted_average_model_data.drop(columns = ['Stocks'])
    #now merge this back into new_model_data after summing up that data's new stocks

    #extract other values we'll need but ont want to sum (because they are constant for each economy and year)
    non_summed_values = model_data.copy()
    non_summed_values = non_summed_values[cols_to_sum_by+['Population','Gompertz_gamma','Gdp_per_capita']].drop_duplicates()

    #now join all values together with a merge
    new_model_data = new_stocks.merge(non_summed_values, on = cols_to_sum_by, how = 'left')
    new_model_data = new_model_data.merge(weighted_average_model_data, on = cols_to_sum_by, how = 'left')
    #breakpoint()
    #test that activity is the same as before:
    new_model_data['Activity'] = new_model_data['Stocks'] * new_model_data['Occupancy_or_load'] * new_model_data['Travel_km']
    return new_model_data

def logistic_fitting_function_handler(model_data,vehicle_gompertz_factors,show_plots=False,matplotlib_bool=False, plotly_bool=False,ONLY_PASSENGER_VEHICLES=True):
    """Take in output of stocks,occupancy, travel_km, activity and mileage from running road model on a gdp per cpita based growth rate. Then fit a logistic curve to the stocks data with the gamma value from each economy provided. 
    Then with this curve, extract the expected activity per year based on the expected stocks per year and the expected mileage per year. Then recalculate the growth rate over time based on this. We will then use this to rerun the road model with the new growth rate.
    This was origianlly done for each economy and vehicle type in passenger vehicles, now for each economy and transport type. 
    
    This will be done for each scenario too because movement between Transport Types might change the growth rate?"""
    #grab only passenger data if`ONLY_PASSENGER_VEHICLES` is True
    if ONLY_PASSENGER_VEHICLES:
        model_data_to_edit = model_data.loc[(model_data['Transport Type'] == 'passenger')] 
    else:
        model_data_to_edit = model_data.copy()
        
    new_model_data = convert_stocks_to_gompertz_adjusted_stocks(model_data_to_edit,vehicle_gompertz_factors)
    #EXTRACT PARAMETERS FOR LOGISTIC FUNCTION:
    # breakpoint()#want to find the toal amount of stocks per year per economy per transport type, so we can compare them to the data plotted in graphs:
    # stocks = new_model_data.groupby(['Date', 'Economy', 'Scenario', 'Transport Type'])['Stocks'].sum().reset_index()
    
    parameters_estimates = find_parameters_for_logistic_function(new_model_data, show_plots, matplotlib_bool, plotly_bool)
    #some parameters will be np.nan because we dont need to fit the curve for all economies. We will drop these and not recalculate the growth rate for these economies
    parameters_estimates = parameters_estimates.dropna(subset=['Gompertz_gamma'])
    #grab only cols we need
    new_model_data = new_model_data[['Date', 'Economy', 'Scenario','Transport Type', 'Stocks', 'Occupancy_or_load', 'Mileage', 'Population', 'Gdp_per_capita','Activity', 'Travel_km']]
    #join the params on: #PLEASE NOTE THAT WE ARE ASSUMING WE HAVENT CHANGD GAMMA IN THE PARAMETERS ESTIMATES. AS SUCH WE JOIN IT IN HERE. THIS MAY CHANGE IN THE FUTURE
    new_model_data = new_model_data.merge(parameters_estimates, on=['Economy', 'Scenario','Transport Type'], how='inner')

    #sum stocks,'Activity', Travel_km, , with any NAs set to 0
    new_model_data['Stocks'] = new_model_data['Stocks'].fillna(0)
    new_model_data['Activity'] = new_model_data['Activity'].fillna(0)
    new_model_data['Travel_km'] = new_model_data['Travel_km'].fillna(0)
    
    summed_values = new_model_data.groupby(['Date','Economy', 'Scenario','Transport Type'])['Stocks','Activity', 'Travel_km'].sum().reset_index().copy()
    #join stocks with other data
    new_model_data.drop(columns=['Stocks','Activity', 'Travel_km'], inplace=True)
    new_model_data.drop_duplicates(inplace=True)
    new_model_data = new_model_data.merge(summed_values, on=['Date','Economy', 'Scenario','Transport Type'], how='left')
    # 
    model_data_logistic_predictions = create_new_dataframe_with_logistic_predictions(new_model_data)
    # # breakpoint()
    
    # stocks = model_data_logistic_predictions.groupby(['Date', 'Economy', 'Scenario', 'Transport Type'])['Stocks'].sum().reset_index()
    #find growth rate of activity as the percentage change in activity from the previous year plus 1. make sur eto group by economy and scenario BUT NOT BY VEHICLE TYPE (PLEASE NOTE THAT THIS MAY CHANGE IN THE FUTURE)
    activity_growth_estimates = model_data_logistic_predictions[['Date', 'Economy', 'Scenario', 'Activity', 'Transport Type']].drop_duplicates().groupby(['Date', 'Economy', 'Scenario', 'Transport Type'])['Activity'].sum().reset_index()

    activity_growth_estimates.sort_values(['Economy', 'Scenario', 'Date', 'Transport Type'], inplace=True)
    activity_growth_estimates['Activity_growth'] = activity_growth_estimates.groupby(['Economy', 'Scenario', 'Transport Type'])['Activity'].pct_change()+1
    #replace nan with 1
    activity_growth_estimates['Activity_growth'] = activity_growth_estimates['Activity_growth'].fillna(1)

    #if matplotlib_bool or plotly_bool:
    if matplotlib_bool or plotly_bool:
        #
        plot_logistic_fitting_data.plot_logistic_function_all_economies(model_data_logistic_predictions, activity_growth_estimates, parameters_estimates, new_model_data, show_plots, matplotlib_bool, plotly_bool)
        plot_logistic_fitting_data.plot_logistic_function_by_economy(model_data_logistic_predictions, activity_growth_estimates, parameters_estimates, new_model_data, show_plots, matplotlib_bool, plotly_bool)

    #drop Activity from activity_growth_estimates
    activity_growth_estimates.drop(columns=['Activity'], inplace=True)
    
    #fill missing activity growth estimates (because there was no need for an adjustment) with their original growth rate:
    old_activity_growth = model_data_to_edit.copy()
    if ONLY_PASSENGER_VEHICLES:
        old_activity_growth = old_activity_growth[old_activity_growth['Transport Type']=='passenger']
    old_activity_growth = old_activity_growth[['Date', 'Economy', 'Scenario', 'Activity_growth', 'Transport Type']].drop_duplicates()
    if old_activity_growth.groupby(['Date', 'Economy', 'Scenario', 'Transport Type']).size().max()!=1:
        raise ValueError('We have more than one row for each date, economy, transport type and scenario in the old_activity_growth dataframe')
    #merge old activity growth with new activity growth
    activity_growth_estimates = old_activity_growth.merge(activity_growth_estimates, on=['Date', 'Economy', 'Scenario', 'Transport Type'], how='left', suffixes=('_old', ''))
    #fill na with old activity growth
    activity_growth_estimates['Activity_growth'] = activity_growth_estimates['Activity_growth'].fillna(activity_growth_estimates['Activity_growth_old'])
    #drop old activity growth
    activity_growth_estimates.drop(columns=['Activity_growth_old'], inplace=True)

    return activity_growth_estimates, parameters_estimates

#CREATE NEW DATAFRAME WITH LOGISTIC FUNCTION PREDICTIONS
def create_new_dataframe_with_logistic_predictions(new_model_data):
    """ Take in the model data and the parameters estimates and create a new dataframe with the logistic function predictions for the stocks, activity and mileage basedon the parameters and the gdp per cpita. This will first calcualte the stocks, then using mileage, calcualte the travel km, then calcualte activity based on the occupancy rate"""
    #breakpoint()
    #calculate new stocks:
    model_data_logistic_predictions = new_model_data.copy()
    #apply logistic_function to each row
    model_data_logistic_predictions['Stocks_per_thousand_capita'] = model_data_logistic_predictions.apply(lambda row: logistic_function(row['Gdp_per_capita'], row['Gompertz_gamma'], row['Gompertz_beta'], row['Gompertz_alpha']), axis=1)
    #calaculte stocks
    model_data_logistic_predictions['Thousand_stocks_per_capita'] = model_data_logistic_predictions['Stocks_per_thousand_capita'] / 1000000
    model_data_logistic_predictions['Stocks'] = model_data_logistic_predictions.apply(lambda row: row['Thousand_stocks_per_capita'] * row['Population'], axis=1)
    #calculate new travel km:
    model_data_logistic_predictions['Travel_km'] = model_data_logistic_predictions.apply(lambda row: row['Stocks'] * row['Mileage'], axis=1)
    #calculate new activity:
    model_data_logistic_predictions['Activity'] = model_data_logistic_predictions.apply(lambda row: row['Travel_km'] * row['Occupancy_or_load'], axis=1)
    return model_data_logistic_predictions

def find_parameters_for_logistic_function(new_model_data, show_plots, matplotlib_bool, plotly_bool, proportion_below_gamma= 0.05):
    
    #loop through economies and transport types and perform the clacualtions ti find the parameters for the logistic function
    #create empty dataframe to store results
    parameters_estimates = pd.DataFrame(columns=['Gompertz_gamma', 'Economy', 'Transport Type', 'Scenario'])
    for economy in new_model_data['Economy'].unique():
        for scenario in new_model_data['Scenario'].unique():
            for transport_type in new_model_data['Transport Type'].unique():

                economy_ttype_scenario = economy + '_' + transport_type + '_' + scenario
                
                #filter for economy and transport type
                new_model_data_economy_scenario_ttype = new_model_data[(new_model_data['Economy']==economy) & (new_model_data['Transport Type']==transport_type) & (new_model_data['Scenario']==scenario)]

                #filter for cols we need:
                new_model_data_economy_scenario_ttype = new_model_data_economy_scenario_ttype[['Date', 'Transport Type', 'Stocks', 'Gdp_per_capita','Population', 'Gompertz_gamma', 'Travel_km', 'Mileage', 'Activity']].drop_duplicates()

                #sum stocks,'Activity', Travel_km, , with any NAs set to 0
                new_model_data_economy_scenario_ttype['Stocks'] = new_model_data_economy_scenario_ttype['Stocks'].fillna(0)
                new_model_data_economy_scenario_ttype['Activity'] = new_model_data_economy_scenario_ttype['Activity'].fillna(0)
                new_model_data_economy_scenario_ttype['Travel_km'] = new_model_data_economy_scenario_ttype['Travel_km'].fillna(0)

                summed_values = new_model_data_economy_scenario_ttype.groupby(['Date', 'Transport Type'])['Stocks','Activity', 'Travel_km'].sum().reset_index()
                #join summed values with other data that didnt need to be summed
                new_model_data_economy_scenario_ttype.drop(columns=['Stocks','Activity', 'Travel_km'], inplace=True)
                new_model_data_economy_scenario_ttype.drop_duplicates(inplace=True)
                new_model_data_economy_scenario_ttype = new_model_data_economy_scenario_ttype.merge(summed_values, on=['Date', 'Transport Type'], how='left')

                #calcualte stocks per capita
                new_model_data_economy_scenario_ttype['Thousand_stocks_per_capita'] = new_model_data_economy_scenario_ttype['Stocks']/new_model_data_economy_scenario_ttype['Population']
                #convert to more readable units. We will convert back later if we need to #todo do we need to?
                new_model_data_economy_scenario_ttype['Stocks_per_thousand_capita'] = new_model_data_economy_scenario_ttype['Thousand_stocks_per_capita'] * 1000000

                #find date where stocks per cpaita passes gamma, then find a proportion below that and set that as the point where we plot remaining stocks per capita, going linearly to gamma by the end of the time period
                #find the date where stocks per capita passes gamma
                gamma = new_model_data_economy_scenario_ttype['Gompertz_gamma'].unique()[0]
                date_where_stocks_per_capita_passes_gamma = new_model_data_economy_scenario_ttype[new_model_data_economy_scenario_ttype['Stocks_per_thousand_capita'] > gamma]['Date'].min()

                #sometimes the date is not found. in which case we ahve no issue with the stocks per capita going aobve gamma. So we dont need to adjsut growth rates for this economy. i.e. skip
                if np.isnan(date_where_stocks_per_capita_passes_gamma):
                    #set parameters to nan so that we can filter them out later
                    params = pd.DataFrame({'Gompertz_beta':np.nan, 'Gompertz_alpha':np.nan, 'Gompertz_gamma':np.nan, 'Economy': economy, 'Transport Type': transport_type, 'Scenario': scenario}, index=[0])
                    #concat to parameters_estimates
                    parameters_estimates = pd.concat([parameters_estimates, params], axis=0).reset_index(drop=True)
                    continue

                #extract data after this date and set the stocks per capita to be a linear line from the gamma - gamma*proportion_below_gamma to gamma over the time period
                data_to_change = new_model_data_economy_scenario_ttype[new_model_data_economy_scenario_ttype['Date'] >= date_where_stocks_per_capita_passes_gamma]
                
                data_to_change.loc[:, 'Stocks_per_thousand_capita'] = [gamma - (gamma * proportion_below_gamma) + ((gamma * proportion_below_gamma) / len(data_to_change['Stocks_per_thousand_capita'])) * i for i in range(len(data_to_change['Stocks_per_thousand_capita']))]
                
                #add this back to the main dataframe
                new_model_data_economy_scenario_ttype[new_model_data_economy_scenario_ttype['Date'] >= date_where_stocks_per_capita_passes_gamma] = data_to_change

                #fit a logistic curve to the stocks per capita data
                gamma, growth_rate, midpoint = logistic_fitting_function(new_model_data_economy_scenario_ttype, gamma, economy_ttype_scenario, show_plots,matplotlib_bool=matplotlib_bool, plotly_bool=plotly_bool)
                
                #note midpoint is alpha, growth is beta
                params = pd.DataFrame({'Gompertz_beta':growth_rate, 'Gompertz_alpha':midpoint, 'Gompertz_gamma':gamma, 'Economy': economy, 'Transport Type': transport_type, 'Scenario': scenario}, index=[0])
                #concat to parameters_estimates
                parameters_estimates = pd.concat([parameters_estimates, params], axis=0).reset_index(drop=True)

    return parameters_estimates

def logistic_function(gdp_per_capita,gamma, growth_rate, midpoint):
    #gompertz funtion: gamma * np.exp(alpha * np.exp(beta * gdp_per_capita))
    #note midpoint is alpha, growth is beta e.g.  logistic_function(gdp_per_capita,gamma, beta, alpha)
    #original equation: logistic_function(x, L, k, x0): L / (1 + np.exp(-k * (x - x0)))
    # L is the maximum limit (in your case, this would be the gamma value),
    # k is the growth rate,
    # x0​ is the x-value of the sigmoid's midpoint,
    # x is the input to the function (in your case, this could be time or GDP per capita).
    return gamma / (1 + np.exp(-growth_rate * (gdp_per_capita - midpoint)))
    
def logistic_fitting_function(new_model_data_economy_scenario_ttype, gamma, economy_ttype_scenario, show_plots, matplotlib_bool, plotly_bool):
    #grab data we need
    date = new_model_data_economy_scenario_ttype['Date']
    stocks_per_capita = new_model_data_economy_scenario_ttype['Stocks_per_thousand_capita']
    #TODO NOT SURE IF WE WANT TO GRAB GDP PER CPITA OR FIT THE MODEL TO THE YEAR NOW? IM GOING TO TRY USING GDP PER CPAITA SO THAT AT ELAST THE PARAMETER ESTIMATES CAN BE SHARED BETWEEN ECONOMIES IN TERMS OF GDP PER CAPITA
    gdp_per_capita = new_model_data_economy_scenario_ttype['Gdp_per_capita']
    # 
    def logistic_function_curve_fit(gdp_per_capita, growth_rate, midpoint):
        #need a new function so we can pass in gamma (i couldnt work out how to do it in curve fit function ): 
        #gompertz funtion: gamma * np.exp(alpha * np.exp(beta * gdp_per_capita))
        #original equation: logistic_function(x, L, k, x0): L / (1 + np.exp(-k * (x - x0)))
        # L is the maximum limit (in your case, this would be the gamma value),
        # k is the growth rate,
        # x0​ is the x-value of the sigmoid's midpoint,
        # x is the input to the function (in your case, this could be time or GDP per capita).
        return gamma / (1 + np.exp(-growth_rate * (gdp_per_capita - midpoint)))
    try:
        # Fit the logistic function to your data
        popt, pcov = curve_fit(logistic_function_curve_fit, gdp_per_capita, stocks_per_capita, bounds=(0, [3., max(gdp_per_capita)]))
    except:
        breakpoint()
        raise ValueError('Could not fit logistic function to data for economy: ', economy_ttype_scenario)
    # Use the fitted function to calculate growth
    growth_rate, midpoint = popt
    
    if show_plots:
        #print gamma
        print('gamma: ', gamma)
        #print params
        print('growth_rate: ', growth_rate, 'midpoint: ', midpoint)

    projected_growth = logistic_function_curve_fit(gdp_per_capita, growth_rate, midpoint)

    plot_logistic_fitting_data.plot_logistic_fit(date, stocks_per_capita, gdp_per_capita, gamma, growth_rate, midpoint, economy_ttype_scenario,show_plots, matplotlib_bool=matplotlib_bool, plotly_bool=plotly_bool)

    return gamma, growth_rate, midpoint

                    
#theres a hance it may be better just to stop the stocks per cap from passing gamma, rather than applying a line too.
# %%

def average_out_growth_rate_using_cagr(new_growth_forecasts, economies_to_avg_growth_over_all_years_in_freight_for = ['19_THA']):

    def calculate_cagr_from_factors(factors):
        # Multiply all factors together
        total_growth = factors.product()
        
        # Take the Nth root and subtract 1
        return total_growth ** (1.0 / len(factors)) - 1

    new_freight_growth_economies = new_growth_forecasts.loc[new_growth_forecasts['Economy'].isin(economies_to_avg_growth_over_all_years_in_freight_for)].copy()

    # apply cagr on the growth factors, grouped by economy, transport type and scenario:
    cagr = new_freight_growth_economies.groupby(['Economy', 'Scenario', 'Transport Type'])['Activity_growth_new'].apply(calculate_cagr_from_factors)
    new_freight_growth_economies = pd.merge(new_freight_growth_economies.drop(columns=['Activity_growth_new']), cagr, on=['Economy', 'Scenario', 'Transport Type'], how='left')
    
                                            
    #############
    early_period = range(new_growth_forecasts.Date.min()+1, new_growth_forecasts.Date.min()+7)
    other_economies_early_growth = new_growth_forecasts.loc[~new_growth_forecasts['Economy'].isin(economies_to_avg_growth_over_all_years_in_freight_for) & (new_growth_forecasts['Date'].isin(early_period))].copy()
    
    # apply cagr on the growth factors, grouped by economy, transport type and scenario:
    cagr = other_economies_early_growth.groupby(['Economy', 'Scenario', 'Transport Type'])['Activity_growth_new'].apply(calculate_cagr_from_factors)
    other_economies_early_growth = pd.merge(other_economies_early_growth.drop(columns=['Activity_growth_new']), cagr, on=['Economy', 'Scenario', 'Transport Type'], how='left')
    
    #############
    other_data = new_growth_forecasts.loc[~new_growth_forecasts['Economy'].isin(economies_to_avg_growth_over_all_years_in_freight_for) & (~new_growth_forecasts['Date'].isin(early_period))].copy()
    all_economies_data = pd.concat([new_freight_growth_economies, other_economies_early_growth, other_data], axis=0)
    new_growth_forecasts = all_economies_data.copy()
    
    return new_growth_forecasts