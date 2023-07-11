#######################################################################
#%%
#Calcualtions
#set working directory as one folder back so that config works
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
from runpy import run_path
import numpy as np
from scipy.optimize import newton,curve_fit,minimize
exec(open("config/config.py").read())#usae this to load libraries and set variables. Feel free to edit that file as you need
import plotly.graph_objects as go
import numpy as np
import matplotlib.pyplot as plt
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
#######################################################################
#%%

def gompertz_fitting_function_handler(model_data,BASE_YEAR,future_dates=[2045, 2050], future_dates_prop_diff_from_gamma=[0.1, 0.09], INTERPOLATE_DATA = True,show_plots=False,matplotlib_bool=True, plotly_bool=False):
    """this will loop through the data inout for the road model and estimate the gompertz parameters for each economy and vehicle type"""
    #loop through economies and vehicle types
    #create empty dataframe to store results
    gompertz_parameters_estimates = pd.DataFrame()
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
                model_data_economy_scenario_vtype = model_data_economy_scenario_vtype[['Date', 'Stocks', 'Gdp_per_capita','Population', 'Gompertz_gamma', 'Gompertz_alpha', 'Gompertz_beta']].drop_duplicates()
                #sum up by Drive, with any NAs set to 0
                model_data_economy_scenario_vtype['Stocks'] = model_data_economy_scenario_vtype['Stocks'].fillna(0)
                model_data_economy_scenario_vtype = model_data_economy_scenario_vtype.groupby(['Date', 'Gdp_per_capita','Population', 'Gompertz_gamma', 'Gompertz_alpha', 'Gompertz_beta']).agg({'Stocks':'sum'}).reset_index()
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

                alpha_opt, beta_opt = gompertz_fitting_function(model_data_economy_scenario_vtype, vehicle_ownership_rates_data, gdp_per_capita_fit, date, gamma,economy_vtype_scenario,show_plots,matplotlib_bool=matplotlib_bool, plotly_bool=plotly_bool)
                gompertz_params = pd.DataFrame({'Gompertz_alpha':alpha_opt, 'Gompertz_beta':beta_opt, 'Gompertz_gamma':gamma, 'Economy': economy, 'Vehicle Type': vehicle_type, 'Scenario': scenario}, index=[0])
                #concat to gompertz_parameters_estimates
                gompertz_parameters_estimates = pd.concat([gompertz_parameters_estimates, gompertz_params], axis=0).reset_index(drop=True)
    
    return gompertz_parameters_estimates


def gompertz_stocks(gdp_per_capita, gamma, beta, alpha):
    return gamma * np.exp(alpha * np.exp(beta * gdp_per_capita))

#NOW SEND TO THE MODEL:
def gompertz_fitting_function(model_data_economy_scenario_vtype, vehicle_ownership_rates_data, gdp_per_capita_fit, date, gamma,economy_vtype_scenario,show_plots,matplotlib_bool, plotly_bool):
                        
    # Initial guess for the parameters
    initial_guess = [model_data_economy_scenario_vtype['Gompertz_alpha'].dropna().iloc[0], model_data_economy_scenario_vtype['Gompertz_beta'].dropna().iloc[0]]
        
    # Define your cost function
    def cost_function(params):
        alpha, beta = params
        vehicle_ownership_rates_fit = gompertz_stocks(gdp_per_capita_fit, gamma, beta, alpha)
        return np.sum((vehicle_ownership_rates_fit - vehicle_ownership_rates_data)**2)

    # Use scipy.optimize.minimize to find the best parameters
    result = minimize(cost_function, initial_guess,method='Nelder-Mead')
    # The optimal parameters are stored in result.x
    alpha_opt, beta_opt = result.x
    #apply checks for results that are out of bounds we want:
    #if any y from gompertz_stocks(gdp_per_capita_fit, gamma, beta_opt, alpha_opt) is >= to gamma then it didnt work
    if gompertz_stocks(gdp_per_capita_fit, gamma, beta_opt, alpha_opt).max() >= gamma:
        #set alpha_opt to nan
        alpha_opt = np.nan
        beta_opt = np.nan
        print('alpha_opt:', alpha_opt)
        print('beta_opt:', beta_opt)
        print('Message: Gompertz fit failed as gompertz_stocks(gdp_per_capita_fit, gamma, beta_opt, alpha_opt).max() >= gamma')
    else:
        print('Message:', result.message)
        print('alpha_opt:', alpha_opt)
        print('beta_opt:', beta_opt)        
        plot_gompertz_fit(date, vehicle_ownership_rates_data, gdp_per_capita_fit, gamma, beta_opt, alpha_opt, economy_vtype_scenario, show_plots,matplotlib_bool=matplotlib_bool, plotly_bool=plotly_bool)

    return alpha_opt, beta_opt


def plot_gompertz_fit(date, vehicle_ownership_rates_data, gdp_per_capita_fit, gamma, beta_opt, alpha_opt, economy_vtype_scenario,show_plots, matplotlib_bool, plotly_bool):
    if plotly_bool:
        #now plot the results with x = date, y = stocks per capita
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=date, y=vehicle_ownership_rates_data, mode='markers', name='data'))
        fig.add_trace(go.Scatter(x=date, y=gompertz_stocks(gdp_per_capita_fit, gamma, beta_opt, alpha_opt), mode='lines', name='fit'))
        fig.update_layout(title='Gompertz fit for 01_AUS', xaxis_title='Year', yaxis_title='Stocks per capita')
        #plot gamma as its own value for every date
        fig.add_trace(go.Scatter(x=date, y=[gamma]*len(date), mode='lines', name='gamma'))
        #write to png and open it
        fig.write_image(f'plotting_output/input_exploration/gompertz/gompertz_fit_{economy_vtype_scenario}.png')

        #and plot the same but wth gdp per capita in x
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=gdp_per_capita_fit, y=vehicle_ownership_rates_data, mode='markers', name='data'))
        fig.add_trace(go.Scatter(x=gdp_per_capita_fit, y=gompertz_stocks(gdp_per_capita_fit, gamma, beta_opt, alpha_opt), mode='lines', name='fit'))
        fig.update_layout(title='Gompertz fit for 01_AUS', xaxis_title='Gdp per capita', yaxis_title='Stocks per capita')
        #plot gamma as its own value for every date
        fig.add_trace(go.Scatter(x=gdp_per_capita_fit, y=[gamma]*len(gdp_per_capita_fit), mode='lines', name='gamma'))
        #write to html
        fig.write_html(f'plotting_output/input_exploration/gompertz/gompertz_fit_time_{economy_vtype_scenario}.html')

    if matplotlib_bool:
        
        if not show_plots:
            plt.ioff()
        # Create a new figure
        plt.figure()

        # Plot the original data
        plt.scatter(date, vehicle_ownership_rates_data, label='data')

        # Plot the fitted function
        plt.plot(date, gompertz_stocks(gdp_per_capita_fit, gamma, beta_opt, alpha_opt), label='fit')

        # Plot the gamma value
        plt.plot(date, [gamma]*len(date), label='gamma')

        # Add labels and title
        plt.xlabel('Year')
        plt.ylabel('Stocks per capita')
        plt.title(f'Gompertz fit for {economy_vtype_scenario}')

        # Add a legend
        plt.legend()

        #save to png
        plt.savefig(f'plotting_output/input_exploration/gompertz/gompertz_fit_time_{economy_vtype_scenario}.png')

        #and plot the same but wth gdp per capita in x
        plt.figure()

        # Plot the original data
        plt.scatter(gdp_per_capita_fit, vehicle_ownership_rates_data, label='data')
        
        # Plot the fitted function
        plt.plot(gdp_per_capita_fit, gompertz_stocks(gdp_per_capita_fit, gamma, beta_opt, alpha_opt), label='fit')

        # Plot the gamma value
        plt.plot(gdp_per_capita_fit, [gamma]*len(gdp_per_capita_fit), label='gamma')

        # Add labels and title
        plt.xlabel('Gdp per capita')
        plt.ylabel('Stocks per capita')
        plt.title(f'Gompertz fit for {economy_vtype_scenario}')

        # Add a legend
        plt.legend()

        plt.savefig(f'plotting_output/input_exploration/gompertz/gompertz_fit_gdp_per_capita_{economy_vtype_scenario}.png')

#%%

#theres a hance it may be better just to stop the stocks per cap from passing gamma, rather than applying a line too.
# %%
#functions used in model:
def gompertz_stocks(gdp_per_capita, gamma, beta, alpha):
    
    return gamma * np.exp(alpha * np.exp(beta * gdp_per_capita))
    #orioginal equation, just for reference
    # Here's a breakdown of the function:

    # gdp_per_capita: This is the per capita Gross Domestic Product (GDP), which is often used as a measure of economic development. It's typically a key factor influencing vehicle ownership rates.

    # gamma, beta, and alpha are parameters of the Gompertz function:

    # gamma: This is often referred to as the upper asymptote or saturation level. In the context of vehicle ownership rates, it represents the maximum level of vehicle ownership that the model predicts can be achieved.

    # beta: This parameter is related to the displacement along the x-axis. In this context, it could be interpreted as a factor that shifts the vehicle ownership curve along the GDP per capita axis.

    # alpha: This parameter is related to the growth rate. It determines how quickly vehicle ownership rates increase as GDP per capita increases.

def gompertz_stocks_derivative(gdp_per_capita, gamma, beta, alpha):
    return alpha * beta * gamma * np.exp(alpha * np.exp(beta * gdp_per_capita) + beta * gdp_per_capita)

#Estimate Gdp per capita
def solve_for_gdp_per_capita(stocks_per_capita, current_Gdp_per_capita,gamma, beta, alpha):
    # Define the function for which we want to find the root
    #the "root" is the value of gdp_per_capita that makes the function gompertz_stocks(gdp_per_capita, gamma, beta, alpha) - stocks_per_capita equal to zero
    func = lambda gdp_per_capita: gompertz_stocks(gdp_per_capita, gamma, beta, alpha) - stocks_per_capita
    # Initial guess for the root
    initial_guess = current_Gdp_per_capita
    # Use the Newton-Raphson method to find the root
    gdp_per_capita = newton(func, initial_guess)
    return gdp_per_capita
