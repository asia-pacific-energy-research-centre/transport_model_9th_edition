#######################################################################
#%%
#Calcualtions
#set working directory as one folder back so that config works
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
from runpy import run_path
import numpy as np
from scipy.optimize import newton
exec(open("config/config.py").read())#usae this to load libraries and set variables. Feel free to edit that file as you need
import plotly.graph_objects as go
import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.optimize import minimize
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
#######################################################################
#%%
#load in road_model_data.to_pickle('intermediate_data/archive/road_model_data_{}.pkl'.format(FILE_DATE_ID))
road_model_data = pd.read_pickle('intermediate_data/archive/road_model_data_{}.pkl'.format(FILE_DATE_ID))

#############################


#%%

def logistic(gdp_per_capita, gamma, growth_rate, midpoint):
    #gompertz funtion: gamma * np.exp(alpha * np.exp(beta * gdp_per_capita))
    #original equation: logistic(x, L, k, x0): L / (1 + np.exp(-k * (x - x0)))
    # L is the maximum limit (in your case, this would be the gamma value),
    # k is the growth rate,
    # x0​ is the x-value of the sigmoid's midpoint,
    # x is the input to the function (in your case, this could be time or GDP per capita).
    return gamma / (1 + np.exp(-growth_rate * (gdp_per_capita - midpoint)))

def logistic_derivative(gdp_per_capita, gamma, growth_rate, midpoint):
    exp_term = np.exp(-growth_rate * (gdp_per_capita - midpoint))
    return (growth_rate * gamma * exp_term) / (exp_term + 1)**2

def logistic_fitting_function_handler(model_data,BASE_YEAR,future_dates=[2045, 2050], future_dates_prop_diff_from_gamma=[0.1, 0.09], INTERPOLATE_DATA = True,show_plots=False,matplotlib_bool=True, plotly_bool=False):
    """this will loop through the data inout for the road model and estimate the gompertz parameters for each economy and vehicle type"""
    #loop through economies and vehicle types
    #create empty dataframe to store results
    parameters_estimates = pd.DataFrame()
    for economy in model_data['Economy'].unique():
        for scenario in model_data['Scenario'].unique():
            for vehicle_type in model_data['Vehicle Type'].unique():
                #skip anything except ldv for now
                if vehicle_type != 'ldv':
                    continue
                economy_vtype_scenario = economy + '_' + vehicle_type + '_' + scenario
                #filter for economy and vehicle type
                model_data_economy_scenario_vtype = model_data[(model_data['Economy']==economy) & (model_data['Vehicle Type']==vehicle_type) & (model_data['Scenario']==scenario)]
                #filter for cols we need:
                model_data_economy_scenario_vtype = model_data_economy_scenario_vtype[['Date', 'Stocks', 'Gdp_per_capita','Population', 'Gompertz_gamma']].drop_duplicates()
                #sum up by Drive, with any NAs set to 0
                model_data_economy_scenario_vtype['Stocks'] = model_data_economy_scenario_vtype['Stocks'].fillna(0)
                model_data_economy_scenario_vtype = model_data_economy_scenario_vtype.groupby(['Date', 'Gdp_per_capita','Population', 'Gompertz_gamma']).agg({'Stocks':'sum'}).reset_index()
                #calcualte stocks per capita
                model_data_economy_scenario_vtype['Thousand_stocks_per_capita'] = model_data_economy_scenario_vtype['Stocks']/model_data_economy_scenario_vtype['Population']
                #convert to correct uits:
                model_data_economy_scenario_vtype['Stocks_per_thousand_capita'] = model_data_economy_scenario_vtype['Thousand_stocks_per_capita'] * 1000000
                model_data_economy_scenario_vtype['Gdp_per_capita'] = model_data_economy_scenario_vtype['Gdp_per_capita'] #/ 0.001#convert from thousands to 1's

                #historical data dates <= BASE_YEAR
                input_data = model_data_economy_scenario_vtype[model_data_economy_scenario_vtype.Date <= BASE_YEAR][['Date', 'Gdp_per_capita', 'Stocks_per_thousand_capita']].drop_duplicates().dropna()
                gdp_per_capita_fit = input_data['Gdp_per_capita']
                vehicle_ownership_rates_data = input_data['Stocks_per_thousand_capita']
                date = input_data['Date']

                #calcualte the future_dates_prop_diff_from_gamma from the gamma value
                gamma = model_data_economy_scenario_vtype['Gompertz_gamma'].unique()[0]
                future_dates_stocks_per_thousand_capita =[gamma - (gamma * prop) for prop in future_dates_prop_diff_from_gamma]
                #extract gdp per capita for the future dates
                future_dates_gdp_per_capita = model_data_economy_scenario_vtype[model_data_economy_scenario_vtype.Date.isin(future_dates)]['Gdp_per_capita'].reset_index(drop=True)
                #append these to the input_data. note that some are lists not series so we need to convert them
                future_dates = pd.Series(future_dates)
                future_dates_stocks_per_thousand_capita = pd.Series(future_dates_stocks_per_thousand_capita)

                gdp_per_capita_fit = gdp_per_capita_fit.append(future_dates_gdp_per_capita)
                vehicle_ownership_rates_data = vehicle_ownership_rates_data.append(future_dates_stocks_per_thousand_capita)
                date = date.append(future_dates)

                #append to actual input data
                input_data = input_data.append(pd.DataFrame({'Date':future_dates, 'Gdp_per_capita':future_dates_gdp_per_capita, 'Stocks_per_thousand_capita':future_dates_stocks_per_thousand_capita}))
                if INTERPOLATE_DATA:
                    #interpolate between missing years using a polynomial :
                    interpolated_input_data = model_data_economy_scenario_vtype[['Date', 'Gdp_per_capita', 'Stocks_per_thousand_capita']].drop_duplicates().dropna()
                    #set Stocks_per_thousand_capita to na where date >2020
                    interpolated_input_data['Stocks_per_thousand_capita'] = interpolated_input_data.apply(lambda x: x['Stocks_per_thousand_capita'] if x['Date'] <=BASE_YEAR else np.nan, axis=1)
                    #drop where date is in input_data and then concat the input_data
                    interpolated_input_data = interpolated_input_data[~interpolated_input_data.Date.isin(input_data.Date)].append(input_data)
                    #sort by date
                    interpolated_input_data = interpolated_input_data.sort_values(by='Date').reset_index(drop=True)
                    #interpolate the missing values
                    interpolated_input_data['Stocks_per_thousand_capita'] = interpolated_input_data['Stocks_per_thousand_capita'].interpolate(method='linear')

                    #now set vehicle_ownership_rates_data and so on to the interpolated values
                    vehicle_ownership_rates_data = interpolated_input_data['Stocks_per_thousand_capita']
                    gdp_per_capita_fit = interpolated_input_data['Gdp_per_capita']
                    date = interpolated_input_data['Date']
                    # return model_data_economy_scenario_vtype, vehicle_ownership_rates_data, gdp_per_capita_fit, date, gamma,economy_vtype_scenario,show_plots
                
                gamma,growth_rate, midpoint = logistic_fitting_function(gdp_per_capita_fit, vehicle_ownership_rates_data, gamma,date, economy_vtype_scenario,show_plots,matplotlib_bool=matplotlib_bool, plotly_bool=plotly_bool)
                #note midpoint is alpha, growth is beta
                params = pd.DataFrame({'Gompertz_beta':growth_rate, 'Gompertz_alpha':midpoint, 'Gompertz_gamma':gamma, 'Economy': economy, 'Vehicle Type': vehicle_type, 'Scenario': scenario}, index=[0])
                #concat to parameters_estimates
                parameters_estimates = pd.concat([parameters_estimates, params], axis=0).reset_index(drop=True)
    
    return parameters_estimates

#NOW SEND TO THE MODEL:
def logistic_fitting_function(gdp_per_capita_fit, vehicle_ownership_rates_data, gamma,date,economy_vtype_scenario,show_plots,matplotlib_bool, plotly_bool):
    gamma_fixed = gamma  # replace this with your fixed gamma value
    def logistic_fit(gdp_per_capita, growth_rate, midpoint):
        #gompertz funtion: gamma * np.exp(alpha * np.exp(beta * gdp_per_capita))
        #original equation: logistic(x, L, k, x0): L / (1 + np.exp(-k * (x - x0)))
        # L is the maximum limit (in your case, this would be the gamma value),
        # k is the growth rate,
        # x0​ is the x-value of the sigmoid's midpoint,
        # x is the input to the function (in your case, this could be time or GDP per capita).
        return gamma_fixed / (1 + np.exp(-growth_rate * (gdp_per_capita - midpoint)))
    # Fit the logistic function to your data
    popt, pcov = curve_fit(logistic_fit, gdp_per_capita_fit, vehicle_ownership_rates_data, bounds=(0, [3., max(gdp_per_capita_fit)]))

    # Use the fitted function to calculate growth
    growth_rate, midpoint = popt
    #print gamma
    print('gamma: ', gamma)
    #print params
    print('growth_rate: ', growth_rate, 'midpoint: ', midpoint)

    projected_growth = logistic(gdp_per_capita_fit, gamma, growth_rate, midpoint)

    plot_logistic_fit(date, vehicle_ownership_rates_data, gdp_per_capita_fit, gamma, growth_rate, midpoint, economy_vtype_scenario,show_plots, matplotlib_bool=matplotlib_bool, plotly_bool=plotly_bool)

    return gamma, growth_rate, midpoint

def plot_logistic_fit(date, vehicle_ownership_rates_data, gdp_per_capita_fit, gamma, growth_rate, midpoint, economy_vtype_scenario,show_plots, matplotlib_bool, plotly_bool):

    if plotly_bool:
        #now plot the results with x = date, y = stocks per capita
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=date, y=vehicle_ownership_rates_data, mode='markers', name='data'))
        fig.add_trace(go.Scatter(x=date, y=logistic(gdp_per_capita_fit, gamma, growth_rate, midpoint), mode='lines', name='fit'))
        fig.update_layout(title=f'Log fit for {economy_vtype_scenario}', xaxis_title='Year', yaxis_title='Stocks per capita')
        #plot gamma as its own value for every date
        fig.add_trace(go.Scatter(x=date, y=[gamma]*len(date), mode='lines', name='gamma'))
        #write to png and open it
        write_to_img = False
        if write_to_img:
            fig.write_image(f'plotting_output/input_exploration/gompertz/log_fit_{economy_vtype_scenario}.png')
        #write to html
        fig.write_html(f'plotting_output/input_exploration/gompertz/log_fit_{economy_vtype_scenario}.html')

        #and plot the same but wth gdp per capita in x
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=gdp_per_capita_fit, y=vehicle_ownership_rates_data, mode='markers', name='data'))
        fig.add_trace(go.Scatter(x=gdp_per_capita_fit, y=logistic(gdp_per_capita_fit, gamma, growth_rate, midpoint), mode='lines', name='fit'))
        fig.update_layout(title=f'Log fit for {economy_vtype_scenario}', xaxis_title='Gdp per capita', yaxis_title='Stocks per capita')
        #plot gamma as its own value for every date
        fig.add_trace(go.Scatter(x=gdp_per_capita_fit, y=[gamma]*len(gdp_per_capita_fit), mode='lines', name='gamma'))
        if write_to_img:
            fig.write_image(f'plotting_output/input_exploration/gompertz/log_fit_time_{economy_vtype_scenario}.png')
        fig.write_html(f'plotting_output/input_exploration/gompertz/logistic_fit_time_{economy_vtype_scenario}.html')
        

    if matplotlib_bool:
        
        if not show_plots:
            plt.ioff()
        # Create a new figure
        plt.figure()

        # Plot the original data
        plt.scatter(date, vehicle_ownership_rates_data, label='data')

        # Plot the fitted function
        plt.plot(date, logistic(gdp_per_capita_fit, gamma, growth_rate, midpoint), label='fit')

        # Plot the gamma value
        plt.plot(date, [gamma]*len(date), label='gamma')

        # Add labels and title
        plt.xlabel('Year')
        plt.ylabel('Stocks per capita')
        plt.title(f'logistic fit for {economy_vtype_scenario}')

        # Add a legend
        plt.legend()

        #save to png
        plt.savefig(f'plotting_output/input_exploration/gompertz/logistic_fit_time_{economy_vtype_scenario}.png')

        #and plot the same but wth gdp per capita in x
        plt.figure()

        # Plot the original data
        plt.scatter(gdp_per_capita_fit, vehicle_ownership_rates_data, label='data')
        
        # Plot the fitted function
        plt.plot(gdp_per_capita_fit, logistic(gdp_per_capita_fit, gamma, growth_rate, midpoint), label='fit')

        # Plot the gamma value
        plt.plot(gdp_per_capita_fit, [gamma]*len(gdp_per_capita_fit), label='gamma')

        # Add labels and title
        plt.xlabel('Gdp per capita')
        plt.ylabel('Stocks per capita')
        plt.title(f'logistic fit for {economy_vtype_scenario}')

        # Add a legend
        plt.legend()

        plt.savefig(f'plotting_output/input_exploration/gompertz/logistic_fit_gdp_per_capita_{economy_vtype_scenario}.png')
