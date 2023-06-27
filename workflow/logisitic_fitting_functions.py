
#######################################################################
#%%
#Calcualtions
#set working directory as one folder back so that config works
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
from runpy import run_path
import numpy as np
from scipy.optimize import newton, curve_fit, minimize
exec(open("config/config.py").read())#usae this to load libraries and set variables. Feel free to edit that file as you need
import plotly.graph_objects as go
import numpy as np

    
#######################################################################
#######################################################################
#######################################################################
#######################################################################
#LOGISTIC FITTING FUNCTIONS
#######################################################################
#######################################################################
#######################################################################
#######################################################################
def convert_passenger_to_gompertz_index(model_data,vehicle_gompertz_factors, cols_to_sum_by):
    
    #we will come up with a kind of index for the sum of of passenger vehicles and transalate that to what was intended by the gompertz model (i think it was based on cars).abs
    #for now lets treat it as: car/ldv/suv = 1 vehicle
    #bus = 5 vehicles
    # 2w = 0.5
    #that way, people can still have a car and a 2w and it will be counted as 1.5 vehicles
    #it will; be importatnt ot come backl and check on this cocasionaly.
    #grab passenger data
    model_data_passenger = model_data.loc[(model_data['Transport Type'] == 'passenger')]
    #where vehicle type is bus, multiply stocks by 5
    model_data_passenger.loc[(model_data_passenger['Vehicle Type'] == 'bus'), 'Stocks'] = model_data_passenger['Stocks'] * vehicle_gompertz_factors['bus']
    #where vehicle type is 2w, multiply stocks by 0.5
    model_data_passenger.loc[(model_data_passenger['Vehicle Type'] == '2w'), 'Stocks'] = model_data_passenger['Stocks'] * vehicle_gompertz_factors['2w']
    #where vehicle type is suv/ldv/car, multiply stocks by 1
    model_data_passenger.loc[(model_data_passenger['Vehicle Type'].isin(['suv','ldv','car'])), 'Stocks'] = model_data_passenger['Stocks'] * vehicle_gompertz_factors['car']
    breakpoint()#check resulkt
    #now call all 'passenger_vehicle' and then sum
    model_data_passenger['Vehicle Type'] = 'passenger_vehicle'
    model_data_passenger = model_data_passenger.groupby(cols_to_sum_by).sum().reset_index()

    return model_data_passenger

def logistic_fitting_function_handler(model_data,show_plots=False,matplotlib_bool=False, plotly_bool=False,
    vehicle_gompertz_factors = {'car':1,'ldv':1,'suv':1,'bus':5,'2w':0.5}):
    """Take in output of stocks,occupancy, travel_km, activity and mileage from running road model on a gdp per cpita based growth rate. Then fit a logistic curve to the stocks data with the gamma value from each economy provided. 
    Then with this curve, extract the expected activity per year based on the expected stocks per year and the expected mileage per year. Then recalculate the growth rate over time based on this. We will then use this to rerun the road model with the new growth rate.
    This will be done for each economy and vehicle type in passenger vehicles. 
    
    Perhaps the simplest case will be to calcualte it for only the ldv's and then use the same growth rate for the other vehicle types in passenger transport. 
    This will be done for each scenario too because movement between vehicle types might change the growth rate."""
    #grab only passenger data 

    model_data_passenger = convert_passenger_to_gompertz_index(model_data,vehicle_gompertz_factors, cols_to_sum_by = ['Scenario','Economy','Vehicle Type','Date'])
    #EXTRACT PARAMETERS FOR LOGISTIC FUNCTION:
    parameters_estimates = find_parameters_for_logistic_function(model_data_passenger, show_plots, matplotlib_bool, plotly_bool)
    #some parameters will be np.nan because we dont need to fit the curve for all economies. We will drop these and not recalculate the growth rate for these economies
    parameters_estimates = parameters_estimates.dropna(subset=['Gompertz_gamma'])

    #CREATE NEW DATAFRAME WITH LOGISTIC FUNCTION PREDICTIONS
    

    #grab only cols we need
    model_data_passenger = model_data_passenger[['Date', 'Economy', 'Scenario','Vehicle Type', 'Stocks', 'Occupancy_or_load', 'Mileage', 'Population', 'Gdp_per_capita','Activity', 'Travel_km']]
    #join the params on: #PLEASE NOTE THAT WE ARE ASSUMING WE HAVENT CHANGD GAMMA IN THE PARAMETERS ESTIMATES. AS SUCH WE JOIN IT IN HERE. THIS MAY CHANGE IN THE FUTURE
    model_data_passenger = model_data_passenger.merge(parameters_estimates, on=['Economy', 'Scenario','Vehicle Type'], how='inner')

    #sum stocks,'Activity', Travel_km, , with any NAs set to 0
    model_data_passenger['Stocks'] = model_data_passenger['Stocks'].fillna(0)
    model_data_passenger['Activity'] = model_data_passenger['Activity'].fillna(0)
    model_data_passenger['Travel_km'] = model_data_passenger['Travel_km'].fillna(0)
    
    summed_values = model_data_passenger.groupby(['Date','Economy', 'Vehicle Type'])['Stocks','Activity', 'Travel_km'].sum().reset_index()
    #join stocks with other data
    model_data_passenger.drop(columns=['Stocks','Activity', 'Travel_km'], inplace=True)
    model_data_passenger.drop_duplicates(inplace=True)
    model_data_passenger = model_data_passenger.merge(summed_values, on=['Date','Economy', 'Vehicle Type'], how='left')
    # breakpoint()
    model_data_logistic_predictions = create_new_dataframe_with_logistic_predictions(model_data_passenger)

    #find growth rate of activity as the percentage change in activity from the previous year plus 1. make sur eto group by economy and scenario BUT NOT BY VEHICLE TYPE (PLEASE NOTE THAT THIS MAY CHANGE IN THE FUTURE)
    activity_growth_estimates = model_data_logistic_predictions[['Date', 'Economy', 'Scenario', 'Activity']].drop_duplicates().groupby(['Date', 'Economy', 'Scenario'])['Activity'].sum().reset_index()

    activity_growth_estimates.sort_values(['Economy', 'Scenario', 'Date'], inplace=True)
    activity_growth_estimates['Activity_growth'] = activity_growth_estimates.groupby(['Economy', 'Scenario'])['Activity'].pct_change()+1
    #replace nan with 1
    activity_growth_estimates['Activity_growth'] = activity_growth_estimates['Activity_growth'].fillna(1)

    #if matplotlib_bool or plotly_bool:
    if matplotlib_bool or plotly_bool:
        plot_logistic_function_all_economies(model_data_logistic_predictions, activity_growth_estimates, parameters_estimates, model_data_passenger, show_plots, matplotlib_bool, plotly_bool)
        plot_logistic_function_by_economy(model_data_logistic_predictions, activity_growth_estimates, parameters_estimates, model_data_passenger, show_plots, matplotlib_bool, plotly_bool)

    #drop Activity from activity_growth_estimates
    activity_growth_estimates.drop(columns=['Activity'], inplace=True)
    
    return activity_growth_estimates, parameters_estimates

#CREATE NEW DATAFRAME WITH LOGISTIC FUNCTION PREDICTIONS
def create_new_dataframe_with_logistic_predictions(model_data_passenger):
    """ Take in the model data and the parameters estimates and create a new dataframe with the logistic function predictions for the stocks, activity and mileage basedon the parameters and the gdp per cpita. This will first calcualte the stocks, then using mileage, calcualte the travel km, then calcualte activity based on the occupancy rate"""
    #calculate new stocks:
    model_data_logistic_predictions = model_data_passenger.copy()
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

def find_parameters_for_logistic_function(model_data_passenger, show_plots, matplotlib_bool, plotly_bool, proportion_below_gamma= 0.05):
    
    #loop through economies and vehicle types
    #create empty dataframe to store results
    parameters_estimates = pd.DataFrame(columns=['Gompertz_beta', 'Gompertz_alpha', 'Gompertz_gamma', 'Economy', 'Vehicle Type', 'Scenario'])
    for economy in model_data_passenger['Economy'].unique():
        for scenario in model_data_passenger['Scenario'].unique():
            for vehicle_type in model_data_passenger['Vehicle Type'].unique():

                economy_vtype_scenario = economy + '_' + vehicle_type + '_' + scenario

                #filter for economy and vehicle type
                model_data_passenger_economy_scenario_vtype = model_data_passenger[(model_data_passenger['Economy']==economy) & (model_data_passenger['Vehicle Type']==vehicle_type) & (model_data_passenger['Scenario']==scenario)]

                #filter for cols we need:
                model_data_passenger_economy_scenario_vtype = model_data_passenger_economy_scenario_vtype[['Date', 'Vehicle Type', 'Stocks', 'Gdp_per_capita','Population', 'Gompertz_gamma', 'Travel_km', 'Mileage', 'Activity']].drop_duplicates()

                #sum stocks,'Activity', Travel_km, , with any NAs set to 0
                model_data_passenger_economy_scenario_vtype['Stocks'] = model_data_passenger_economy_scenario_vtype['Stocks'].fillna(0)
                model_data_passenger_economy_scenario_vtype['Activity'] = model_data_passenger_economy_scenario_vtype['Activity'].fillna(0)
                model_data_passenger_economy_scenario_vtype['Travel_km'] = model_data_passenger_economy_scenario_vtype['Travel_km'].fillna(0)

                summed_values = model_data_passenger_economy_scenario_vtype.groupby(['Date', 'Vehicle Type'])['Stocks','Activity', 'Travel_km'].sum().reset_index()
                #join stocks with other data
                model_data_passenger_economy_scenario_vtype.drop(columns=['Stocks','Activity', 'Travel_km'], inplace=True)
                model_data_passenger_economy_scenario_vtype.drop_duplicates(inplace=True)
                model_data_passenger_economy_scenario_vtype = model_data_passenger_economy_scenario_vtype.merge(summed_values, on=['Date', 'Vehicle Type'], how='left')

                #calcualte stocks per capita
                model_data_passenger_economy_scenario_vtype['Thousand_stocks_per_capita'] = model_data_passenger_economy_scenario_vtype['Stocks']/model_data_passenger_economy_scenario_vtype['Population']
                #convert to more readable units. We will convert back later if we need to #todo do we need to?
                model_data_passenger_economy_scenario_vtype['Stocks_per_thousand_capita'] = model_data_passenger_economy_scenario_vtype['Thousand_stocks_per_capita'] * 1000000

                #find date where stocks per cpaita passes gamma, then find a proportion below that and set that as the point where we plot remaining stocks per capita, going linearly to gamma by the end of the time period
                #find the date where stocks per capita passes gamma
                gamma = model_data_passenger_economy_scenario_vtype['Gompertz_gamma'].unique()[0]
                date_where_stocks_per_capita_passes_gamma = model_data_passenger_economy_scenario_vtype[model_data_passenger_economy_scenario_vtype['Stocks_per_thousand_capita'] > gamma]['Date'].min()

                #sometimes the date is not found. in which case we ahve no issue with the stocks per capita going aobve gamma. So we dont need to adjsut growth rates for this economy. 
                if np.isnan(date_where_stocks_per_capita_passes_gamma):
                    #set parameters to nan so that we can filter them out later
                    params = pd.DataFrame({'Gompertz_beta':np.nan, 'Gompertz_alpha':np.nan, 'Gompertz_gamma':np.nan, 'Economy': economy, 'Vehicle Type': vehicle_type, 'Scenario': scenario}, index=[0])
                    #concat to parameters_estimates
                    parameters_estimates = pd.concat([parameters_estimates, params], axis=0).reset_index(drop=True)

                else:
                    #extract data after this date and set the stocks per capita to be a linear line from the gamma - gamma*proportion_below_gamma to gamma over the time period
                    data_to_change = model_data_passenger_economy_scenario_vtype[model_data_passenger_economy_scenario_vtype['Date'] >= date_where_stocks_per_capita_passes_gamma]
                    data_to_change['Stocks_per_thousand_capita'] = [gamma - (gamma * proportion_below_gamma) + ((gamma * proportion_below_gamma) / len(data_to_change['Stocks_per_thousand_capita'])) * i for i in range(len(data_to_change['Stocks_per_thousand_capita']))]#todo check this is correct

                    #add this back to the main dataframe
                    model_data_passenger_economy_scenario_vtype[model_data_passenger_economy_scenario_vtype['Date'] >= date_where_stocks_per_capita_passes_gamma] = data_to_change

                    #fit a logistic curve to the stocks per capita data
                    gamma, growth_rate, midpoint = logistic_fitting_function(model_data_passenger_economy_scenario_vtype, gamma, economy_vtype_scenario, show_plots,matplotlib_bool=matplotlib_bool, plotly_bool=plotly_bool)
                    
                    #note midpoint is alpha, growth is beta
                    params = pd.DataFrame({'Gompertz_beta':growth_rate, 'Gompertz_alpha':midpoint, 'Gompertz_gamma':gamma, 'Economy': economy, 'Vehicle Type': vehicle_type, 'Scenario': scenario}, index=[0])
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
    
def logistic_fitting_function(model_data_passenger_economy_scenario_vtype, gamma, economy_vtype_scenario, show_plots, matplotlib_bool, plotly_bool):
    #grab data we need
    date = model_data_passenger_economy_scenario_vtype['Date']
    stocks_per_capita = model_data_passenger_economy_scenario_vtype['Stocks_per_thousand_capita']
    #TODO NOT SURE IF WE WANT TO GRAB GDP PER CPITA OR FIT THE MODEL TO THE YEAR NOW? IM GOING TO TRY USING GDP PER CPAITA SO THAT AT ELAST THE PARAMETER ESTIMATES CAN BE SHARED BETWEEN ECONOMIES IN TERMS OF GDP PER CAPITA
    gdp_per_capita = model_data_passenger_economy_scenario_vtype['Gdp_per_capita']
    # breakpoint()
    def logistic_function_curve_fit(gdp_per_capita, growth_rate, midpoint):
        #need a new function so we can pass in gamma (i couldnt work out how to do it in curve fit function ): 
        #gompertz funtion: gamma * np.exp(alpha * np.exp(beta * gdp_per_capita))
        #original equation: logistic_function(x, L, k, x0): L / (1 + np.exp(-k * (x - x0)))
        # L is the maximum limit (in your case, this would be the gamma value),
        # k is the growth rate,
        # x0​ is the x-value of the sigmoid's midpoint,
        # x is the input to the function (in your case, this could be time or GDP per capita).
        return gamma / (1 + np.exp(-growth_rate * (gdp_per_capita - midpoint)))
    
    # Fit the logistic function to your data
    popt, pcov = curve_fit(logistic_function_curve_fit, gdp_per_capita, stocks_per_capita, bounds=(0, [3., max(gdp_per_capita)]))

    # Use the fitted function to calculate growth
    growth_rate, midpoint = popt
    
    if show_plots:
        #print gamma
        print('gamma: ', gamma)
        #print params
        print('growth_rate: ', growth_rate, 'midpoint: ', midpoint)

    projected_growth = logistic_function_curve_fit(gdp_per_capita, growth_rate, midpoint)

    plot_logistic_fit(date, stocks_per_capita, gdp_per_capita, gamma, growth_rate, midpoint, economy_vtype_scenario,show_plots, matplotlib_bool=matplotlib_bool, plotly_bool=plotly_bool)

    return gamma, growth_rate, midpoint

def plot_logistic_fit(date, stocks_per_capita, gdp_per_capita, gamma, growth_rate, midpoint, economy_vtype_scenario,show_plots, matplotlib_bool, plotly_bool):
    if plotly_bool:
        #now plot the results with x = date, y = stocks per capita
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=date, y=stocks_per_capita, mode='markers', name='data'))
        fig.add_trace(go.Scatter(x=date, y=logistic_function(gdp_per_capita, gamma, growth_rate, midpoint), mode='lines', name='fit'))
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
        fig.add_trace(go.Scatter(x=gdp_per_capita, y=stocks_per_capita, mode='markers', name='data'))
        fig.add_trace(go.Scatter(x=gdp_per_capita, y=logistic_function(gdp_per_capita, gamma, growth_rate, midpoint), mode='lines', name='fit'))
        fig.update_layout(title=f'Log fit for {economy_vtype_scenario}', xaxis_title='Gdp per capita', yaxis_title='Stocks per capita')
        #plot gamma as its own value for every date
        fig.add_trace(go.Scatter(x=gdp_per_capita, y=[gamma]*len(gdp_per_capita), mode='lines', name='gamma'))
        if write_to_img:
            fig.write_image(f'plotting_output/input_exploration/gompertz/log_fit_time_{economy_vtype_scenario}.png')
        fig.write_html(f'plotting_output/input_exploration/gompertz/logistic_fit_time_{economy_vtype_scenario}.html')
        
def plot_logistic_function_all_economies(model_data_logistic_predictions, activity_growth_estimates, parameters_estimates, model_data_passenger, show_plots, matplotlib_bool, plotly_bool):
    #we will plot the results of the logistic function fit. To cut down on the number of plots we will facet by economy and onily plot the first scenario
    #we will also plot the gamma value for each economy as a horizontal line if the data is on stock per capita
    #extact model_data that will be used. so grab passenger transport type, times by the 
    #calcualte stocks per capita
    model_data_passenger['Thousand_stocks_per_capita'] = model_data_passenger['Stocks']/model_data_passenger['Population']
    #convert to more readable units. We will convert back later if we need to #todo do we need to?
    model_data_passenger['Stocks_per_thousand_capita'] = model_data_passenger['Thousand_stocks_per_capita'] * 1000000
    model_data_passenger = model_data_passenger[['Date', 'Economy', 'Scenario', 'Vehicle Type', 'Stocks_per_thousand_capita', 'Activity']].drop_duplicates()
    #sum up
    model_data_passenger = model_data_passenger.groupby(['Date', 'Economy', 'Scenario', 'Vehicle Type']).sum().reset_index()

    #join the dataframes together
    all_data = pd.merge(model_data_logistic_predictions, model_data_passenger, on=['Date', 'Economy', 'Scenario', 'Vehicle Type'], how='left', suffixes=('_logistic', '_previous'))
    #join on activity_growth_estimates. Note that this ISNT BY VEHIcle type
    all_data = pd.merge(all_data, activity_growth_estimates, on=['Date','Economy', 'Scenario'], how='left')
    
    all_data = all_data.loc[(all_data['Scenario'] == SCENARIO_OF_INTEREST)]

    if plotly_bool:
        #first plot will be on the comparitive stocks per capita
        #filter for that data then melt
        all_data_stocks_per_capita = all_data[['Date','Scenario','Vehicle Type','Gdp_per_capita', 'Economy', 'Stocks_per_thousand_capita_logistic', 'Stocks_per_thousand_capita_previous']]
        all_data_stocks_per_capita = all_data_stocks_per_capita.melt(id_vars=['Date', 'Economy', 'Scenario','Vehicle Type', 'Gdp_per_capita'], value_vars=['Stocks_per_thousand_capita_logistic', 'Stocks_per_thousand_capita_previous'], var_name='Stocks_per_thousand_capita', value_name='Stocks_per_thousand_capita_value')

        fig = px.line(all_data_stocks_per_capita, x='Date', y='Stocks_per_thousand_capita_value', color='Vehicle Type',line_dash='Stocks_per_thousand_capita', facet_col='Economy', facet_col_wrap=3, title='Comparitive stocks per capita', markers=True)

        #write to html
        fig.write_html(f'plotting_output/input_exploration/gompertz/log_fit_new_stocks_per_capita.html')
        ######################
        #and plot the same but wth gdp per capita in x
        fig = px.line(all_data_stocks_per_capita, x='Gdp_per_capita', y='Stocks_per_thousand_capita_value', line_dash='Stocks_per_thousand_capita', facet_col='Economy', color='Vehicle Type',facet_col_wrap=3, title='Comparitive stocks per capita vs GDP per capita', markers=True)

        #write to html
        fig.write_html(f'plotting_output/input_exploration/gompertz/log_fit_new_stocks_per_capita_gdp_per_capita.html')
    
        ######################
        #plot stocks for each economy with x as gdp per capita and then x as date. First calcualte stocks from the logistic function 
        all_data['Stocks_logistic'] = (all_data['Stocks_per_thousand_capita_logistic'] * all_data['Population'])/ 1000000
        #now melt
        all_data_stocks = all_data[['Date','Scenario','Vehicle Type','Gdp_per_capita', 'Economy', 'Stocks_logistic', 'Stocks']]
        all_data_stocks = all_data_stocks.melt(id_vars=['Date', 'Economy', 'Scenario','Vehicle Type', 'Gdp_per_capita'], value_vars=['Stocks_logistic', 'Stocks'], var_name='Stocks', value_name='Stocks_value')
        fig = px.line(all_data_stocks, x='Date', y='Stocks_value', color='Vehicle Type', line_dash = 'Stocks', facet_col='Economy', facet_col_wrap=3, title='Stocks for each economy', markers=True)
        #write to html
        fig.write_html(f'plotting_output/input_exploration/gompertz/log_fit_new_stocks.html')

        ######################
        fig = px.line(all_data_stocks, x='Gdp_per_capita', y='Stocks_value', color='Economy', facet_col='Vehicle Type', line_dash = 'Stocks',  facet_col_wrap=3, title='Stocks for each economy with x as gdp per cpita', markers=True)
        #write to html
        fig.write_html(f'plotting_output/input_exploration/gompertz/log_fit_new_stocks.html')

        ######################

        #now plot the activity growth vs the previous activity growth from the df activity_growth_estimates
                    
        #find growth rate of activity as the percentage change in activity from the previous year plus 1. make sur eto group by economy but not vehicle type (FOR NOW)
        #sum Activity_previous by economy and date #TODO, DOES THIS WORK
        all_data_activity_sum = all_data.groupby(['Economy', 'Date'])['Activity_previous'].sum().reset_index()
        all_data_activity_sum.sort_values(['Economy',  'Date'], inplace=True)
        all_data_activity_sum['Activity_growth_est_previous'] = all_data_activity_sum.groupby(['Economy'])['Activity_previous'].pct_change()+1
        #replace nan with 1
        all_data_activity_sum['Activity_growth_est_previous'].fillna(1, inplace=True)
        #merge back on to all_data
        all_data_activity = pd.merge(all_data, all_data_activity_sum[['Economy', 'Date', 'Activity_growth_est_previous']], on=['Economy', 'Date'], how='left')

        #melt
        all_data_activity_growth = all_data_activity[['Economy','Date','Vehicle Type', 'Gdp_per_capita', 'Activity_growth', 'Activity_growth_est_previous']]
        all_data_activity_growth = all_data_activity_growth.melt(id_vars=['Economy', 'Vehicle Type','Date', 'Gdp_per_capita'], value_vars=['Activity_growth', 'Activity_growth_est_previous'], var_name='Activity_growth', value_name='Activity_growth_value')
        fig = px.line(all_data_activity_growth, x='Date', y='Activity_growth_value', color='Vehicle Type',line_dash='Activity_growth', facet_col='Economy', facet_col_wrap=3, title='Comparitive activity growth', markers=True)

        #write to html
        fig.write_html(f'plotting_output/input_exploration/gompertz/log_fit_new_activity_growth.html')
        
        ######################

def plot_logistic_function_by_economy(model_data_logistic_predictions, activity_growth_estimates, parameters_estimates, model_data_passenger, show_plots, matplotlib_bool, plotly_bool):
    #we will plot the results of the logistic function fit. To cut down on the number of plots we will facet by economy and onily plot the first scenario
    #we will also plot the gamma value for each economy as a horizontal line if the data is on stock per capita
    #extact model_data_passenger that will be used
    #calcualte Stocks_per_thousand_capita for model data

    #calcualte stocks per capita
    model_data_passenger['Thousand_stocks_per_capita'] = model_data_passenger['Stocks']/model_data_passenger['Population']
    #convert to more readable units. We will convert back later if we need to #todo do we need to?
    model_data_passenger['Stocks_per_thousand_capita'] = model_data_passenger['Thousand_stocks_per_capita'] * 1000000
    model_data_passenger = model_data_passenger[['Date', 'Economy', 'Scenario', 'Vehicle Type', 'Stocks_per_thousand_capita', 'Activity']].drop_duplicates()
    #sum up
    model_data_passenger = model_data_passenger.groupby(['Date', 'Economy', 'Scenario', 'Vehicle Type']).sum().reset_index()

    #join the dataframes together
    all_data = pd.merge(model_data_logistic_predictions, model_data_passenger, on=['Date', 'Economy', 'Scenario', 'Vehicle Type'], how='left', suffixes=('_logistic', '_previous'))
    #join on activity_growth_estimates. Note that this ISNT BY VEHIcle type
    all_data = pd.merge(all_data, activity_growth_estimates, on=['Date','Economy', 'Scenario'], how='left')
    
    all_data = all_data.loc[(all_data['Scenario'] == SCENARIO_OF_INTEREST)]
    #TEMP FIX SINCE WE ONLY CAULCATED STOCKS PER CAPITA FOR LDVS
    all_data = all_data.loc[(all_data['Vehicle Type'] == 'ldv')]
    if plotly_bool:
        for economy in all_data.Economy.unique():
            #filter for that economy
            all_data_economy = all_data.loc[(all_data['Economy'] == economy)]

            #first plot will be on the comparitive stocks per capita
            #filter for that data then melt
            all_data_stocks_per_capita = all_data_economy[['Date','Scenario','Vehicle Type','Gdp_per_capita', 'Economy', 'Stocks_per_thousand_capita_logistic', 'Stocks_per_thousand_capita_previous']]
            all_data_stocks_per_capita = all_data_stocks_per_capita.melt(id_vars=['Date', 'Economy', 'Scenario','Vehicle Type', 'Gdp_per_capita'], value_vars=['Stocks_per_thousand_capita_logistic', 'Stocks_per_thousand_capita_previous'], var_name='Stocks_per_thousand_capita', value_name='Stocks_per_thousand_capita_value')

            fig = px.line(all_data_stocks_per_capita, x='Date', y='Stocks_per_thousand_capita_value', color='Vehicle Type',line_dash='Stocks_per_thousand_capita', title='Comparitive stocks per capita', markers=True)

            #write to html
            fig.write_html(f'plotting_output/input_exploration/gompertz/economy/log_fit_new_stocks_per_capita_{economy}.html')
            
            #and plot the same but wth gdp per capita in x
            fig = px.line(all_data_stocks_per_capita, x='Gdp_per_capita', y='Stocks_per_thousand_capita_value', line_dash='Stocks_per_thousand_capita', color='Vehicle Type', title='Comparitive stocks per capita vs GDP per capita', markers=True)

            #write to html
            fig.write_html(f'plotting_output/input_exploration/gompertz/economy/log_fit_new_stocks_per_capita_gdp_per_capita_{economy}.html')

            #now plot the activity growth vs the previous activity growth from the df activity_growth_estimates
                        
            #find growth rate of activity as the percentage change in activity from the previous year plus 1. make sur eto group by economy but not vehicle type (FOR NOW)
            #sum Activity_previous by economy and date #TODO, DOES THIS WORK
            all_data_activity_sum = all_data_economy.groupby(['Economy', 'Date'])['Activity_previous'].sum().reset_index()
            all_data_activity_sum.sort_values(['Economy',  'Date'], inplace=True)
            all_data_activity_sum['Activity_growth_est_previous'] = all_data_activity_sum.groupby(['Economy'])['Activity_previous'].pct_change()+1
            #replace nan with 1
            all_data_activity_sum['Activity_growth_est_previous'].fillna(1, inplace=True)
            #merge back on to all_data
            all_data_activity = pd.merge(all_data_economy, all_data_activity_sum[['Economy', 'Date', 'Activity_growth_est_previous']], on=['Economy', 'Date'], how='left')

            #melt
            all_data_activity_growth = all_data_activity[['Economy','Date','Vehicle Type', 'Gdp_per_capita', 'Activity_growth', 'Activity_growth_est_previous']]
            all_data_activity_growth = all_data_activity_growth.melt(id_vars=['Economy', 'Vehicle Type','Date', 'Gdp_per_capita'], value_vars=['Activity_growth', 'Activity_growth_est_previous'], var_name='Activity_growth', value_name='Activity_growth_value')
            fig = px.line(all_data_activity_growth, x='Date', y='Activity_growth_value', color='Vehicle Type',line_dash='Activity_growth', title='Comparitive activity growth', markers=True)

            #write to html
            fig.write_html(f'plotting_output/input_exploration/gompertz/economy/log_fit_new_activity_growth_{economy}.html')
            
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
    
def gompertz_stocks_second_derivative(gdp_per_capita, gamma, beta, alpha):
    return alpha * beta * gamma * (alpha * beta**2 * np.exp(alpha * np.exp(beta * gdp_per_capita) + 2 * beta * gdp_per_capita) + np.exp(alpha * np.exp(beta * gdp_per_capita) + beta * gdp_per_capita) * (beta + alpha * beta * np.exp(beta * gdp_per_capita))**2)

def solve_gompertz_for_gdp_per_capita(row):
    # Extract the values from the row
    stocks_per_capita = row['Stocks_per_thousand_capita']
    current_Gdp_per_capita = row['Gdp_per_capita']
    gamma = row['Gompertz_gamma']
    beta = row['Gompertz_beta']
    alpha = row['Gompertz_alpha']

    # Define the function for which we want to find the root
    func = lambda gdp_per_capita: gompertz_stocks(gdp_per_capita, gamma, beta, alpha) - stocks_per_capita

    # Initial guess for the root
    initial_guess = current_Gdp_per_capita

    # Use the Newton-Raphson method to find the root
    gdp_per_capita = newton(func, initial_guess,maxiter = 1000)

    return gdp_per_capita
# #Estimate Gdp per capita
# def solve_for_gdp_per_capita(stocks_per_capita, current_Gdp_per_capita,gamma, beta, alpha):
#     # Define the function for which we want to find the root
#     #the "root" is the value of gdp_per_capita that makes the function gompertz_stocks(gdp_per_capita, gamma, beta, alpha) - stocks_per_capita equal to zero
#     func = lambda gdp_per_capita: gompertz_stocks(gdp_per_capita, gamma, beta, alpha) - stocks_per_capita
#     # Initial guess for the root
#     initial_guess = current_Gdp_per_capita
#     # Use the Newton-Raphson method to find the root
#     gdp_per_capita = newton(func, initial_guess)
#     return gdp_per_capita

def logistic_stocks(gdp_per_capita, gamma, growth_rate, midpoint):
    #sometimes beta is used instead of growth rate and alpha is used instead of midpoint
    #gompertz funtion: gamma * np.exp(alpha * np.exp(beta * gdp_per_capita))
    #original equation: logistic_function(x, L, k, x0): L / (1 + np.exp(-k * (x - x0)))
    # L is the maximum limit (in your case, this would be the gamma value),
    # k is the growth rate,
    # x0​ is the x-value of the sigmoid's midpoint,
    # x is the input to the function (in your case, this could be time or GDP per capita).
    return gamma / (1 + np.exp(-growth_rate * (gdp_per_capita - midpoint)))

def logistic_derivative(gdp_per_capita, gamma, growth_rate, midpoint):
    exp_term = np.exp(-growth_rate * (gdp_per_capita - midpoint))
    return (growth_rate * gamma * exp_term) / (exp_term + 1)**2

def solve_logistic_for_gdp_per_capita(row):
    # Extract the values from the row
    stocks_per_capita = row['Stocks_per_thousand_capita']
    current_Gdp_per_capita = row['Gdp_per_capita']
    gamma = row['Gompertz_gamma']
    beta = row['Gompertz_beta']
    alpha = row['Gompertz_alpha']
    #sometimes beta is used instead of growth rate and alpha is used instead of midpoint
    # Define the function for which we want to find the root
    func = lambda gdp_per_capita: logistic_stocks(gdp_per_capita, gamma, beta, alpha) - stocks_per_capita

    # Initial guess for the root
    initial_guess = current_Gdp_per_capita

    # Use the Newton-Raphson method to find the root
    gdp_per_capita = newton(func, initial_guess,maxiter = 1000)

    return gdp_per_capita

