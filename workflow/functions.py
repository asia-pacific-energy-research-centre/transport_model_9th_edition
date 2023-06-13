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
#%%


def run_road_model_for_year_y(year, previous_year_main_dataframe, main_dataframe, user_inputs_df_dict, growth_forecasts, change_dataframe_aggregation, gompertz_function_diagnostics_dataframe, low_ram_computer_files_list, low_ram_computer, ANALYSE_CHANGE_DATAFRAME,previous_10_year_block, testing = False):
    print('Up to year {}. The loop will run until year {}'.format(year, END_YEAR))
    
    #extract the user inputs dataframes from the dictionary
    Vehicle_sales_share = user_inputs_df_dict['Vehicle_sales_share']
    Occupancy_or_load_growth = user_inputs_df_dict['Occupancy_or_load_growth']
    Turnover_rate_growth = user_inputs_df_dict['Turnover_rate_growth']
    New_vehicle_efficiency_growth = user_inputs_df_dict['New_vehicle_efficiency_growth']
    Mileage_growth = user_inputs_df_dict['Mileage_growth']
    # gompertz_parameters = user_inputs_df_dict['gompertz_parameters']

    #create change dataframe. This is like a messy notepad where we will adjust the last years values values and perform most calcualtions. 
    change_dataframe = previous_year_main_dataframe.copy()

    #change year in all rows to the next year. For now we will refer to the previous year as the original or base year. And values calculcated for the next year may sometimes be refered to as 'new'.
    change_dataframe.Date = year

    #start calcualting new values using the orignal values and adjustments as stated/forecasted by the user.

    #generally this will all work on the grouping of economy, year, v-type, drive, transport type, and scenario. There is a model simulation excel workbook in the documentation folder to more easily understand the operations here.
        
    #NOTE that there is still the fuel mixing operation that is not in this file of code. 

    #######################################################################
    #do some quick checks on data:
    
    #check if activity matches sum of activity when you calcualte it as (change_dataframe['Activity']/( change_dataframe['Mileage'] * change_dataframe['Occupancy_or_load']))
    test_data_frame = change_dataframe.copy()
    test_data_frame['Activity_check'] = test_data_frame['Mileage'] * test_data_frame['Occupancy_or_load'] * test_data_frame['Stocks']
    if not np.allclose(test_data_frame['Activity_check'], test_data_frame['Activity']):
        raise ValueError('ERROR: Activity does not match sum of activity when you calcualte it as (change_dataframe[\'Activity\']/( change_dataframe[\'Mileage\'] * change_dataframe[\'Occupancy_or_load\']))') 
    #######################################################################

    #First do adjustments:

    #######################################################################

    #CALCUALTE NEW OCCUPANCY and LOAD VALUEs BY APPLYING THE OCCUPANCY GROWTH RATE
    change_dataframe = change_dataframe.merge(Occupancy_or_load_growth, on=['Economy','Scenario','Drive','Vehicle Type', 'Transport Type', 'Date'], how='left')
    change_dataframe['Occupancy_or_load'] = change_dataframe['Occupancy_or_load'] * change_dataframe['Occupancy_or_load_growth']

    #CALCUALTE NEW TURNOVER RATE AND THEN TURNOVER OF OLD STOCKS
    change_dataframe = change_dataframe.merge(Turnover_rate_growth, on=['Economy', 'Scenario', 'Drive', 'Transport Type', 'Vehicle Type', 'Date'], how='left')
    #now apply turnover growth rate to turnover rate
    change_dataframe['Turnover_rate'] = change_dataframe['Turnover_rate'] * change_dataframe['Turnover_rate_growth']

    #ERROR CHECK double check that turnover rate isnt greater than 1 (in which case the growth rate is too high)
    if change_dataframe['Turnover_rate'].max() > 1:
        raise ValueError('ERROR: Turnover rate is greater than 1. This means that the turnover rate growth rate is too high. Turnover rate cannot be greater than 1.')
        # return 

    #calcualte stock turnover as stocks from last year * turnover rate.
    change_dataframe['Stock_turnover'] = - change_dataframe['Stocks'] * change_dataframe['Turnover_rate']

    #calculate stock turnover plus surplus
    change_dataframe['Stock_turnover_and_surplus_total'] = change_dataframe['Stock_turnover'] + change_dataframe['Surplus_stocks'] 

    #if 'Activity_growth', 'Gdp_per_capita', 'Population' is in df, drop em
    change_dataframe = change_dataframe.drop(['Activity_growth', 'Gdp_per_capita','Gdp', 'Population'], axis=1, errors='ignore')
    # breakpoint()
    # print('check if there aRE any nans in activity grwoth. t seems there are fro freight but i cant find any patterns')
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

    change_dataframe = change_dataframe.merge(Vehicle_sales_share, on=['Economy', 'Scenario', 'Drive', 'Transport Type', 'Vehicle Type', 'Date'], how='left')

    #CALCULATE STOCK SALES TO BE SATISFIED BY EACH VEHICLETYPE/DRIVETYPE COMBINATION USING THE NEW VEHICLE SALES SHARES
    #Note that if Activity worth of extra stocks needed can be 0, and if so then this will be 0 too.
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

    #CALCUALTE NEW STOCKS NEEDED AS STOCKS NEEDED TO SATISFY NEW SALES WORTH OF ACTIVITY
    change_dataframe['New_stocks_needed'] = change_dataframe['Travel_km_of_new_stocks'] / change_dataframe['Mileage']

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

    change_dataframe['Efficiency'] = np.where(change_dataframe['New_stocks_needed'] < 0, change_dataframe['Original_efficiency'], change_dataframe['Efficiency_numerator'] / change_dataframe['Stocks'])

    #if the denominator and numerator are 0 (which will occur if we dont have any stocks in this year [and therefore the last]), then efficiency ends up as nan, so we will set this to the efficiency value for new vehicles even though it doesnt really matter what it is set to, it just helps with aggregates.
    change_dataframe.loc[(change_dataframe['Stocks'] == 0), 'Efficiency'] = change_dataframe['New_vehicle_efficiency']

    #CALCUALTE NEW ENERGY CONSUMPTION. 
    #note that this is not split by fuel yet, it is just the total energy consumption for the vehicle/drive type.
    change_dataframe['Energy'] = change_dataframe['Travel_km'] / change_dataframe['Efficiency'] 

    #if numerator and denominator are 0, then energy ends up as nan, so we will set this to 0
    change_dataframe.loc[(change_dataframe['Travel_km'] == 0) & (change_dataframe['Efficiency'] == 0), 'Energy'] = 0

    #######################################################################

    #finalisation processes

    #######################################################################
        
    #calcualte stocks per capita as its a useful metric
    change_dataframe['Thousand_stocks_per_capita'] = change_dataframe['Stocks']/change_dataframe['Population']
    change_dataframe['Stocks_per_thousand_capita'] = change_dataframe['Thousand_stocks_per_capita'] * 1000000

    #Now start cleaning up the changes dataframe to create the dataframe for the new year.
    addition_to_main_dataframe = change_dataframe.copy()
    addition_to_main_dataframe = addition_to_main_dataframe[['Economy', 'Scenario', 'Transport Type', 'Vehicle Type', 'Medium','Date', 'Drive', 'Activity', 'Stocks', 'Efficiency', 'Energy', 'Surplus_stocks', 'Travel_km', 'Mileage', 'Vehicle_sales_share', 'Occupancy_or_load', 'Turnover_rate', 'New_vehicle_efficiency','Stocks_per_thousand_capita', 'Activity_growth', 'Gdp_per_capita','Gdp', 'Population']]
    

    # breakpoint()
    #add new year to the main dataframe.
    main_dataframe = pd.concat([main_dataframe, addition_to_main_dataframe])
    previous_year_main_dataframe = addition_to_main_dataframe.copy()

    #if you want to analyse what is hapening in th model then set this to true and the model will output a dataframe with all the variables that are being calculated.
    if ANALYSE_CHANGE_DATAFRAME:
        if year == BASE_YEAR+1:
            change_dataframe_aggregation = change_dataframe.copy()
        else:
            change_dataframe_aggregation = pd.concat([change_dataframe, change_dataframe_aggregation])

    #if we have a low ram computer then we will save the dataframe to a csv file at 10 year intervals. this is to save memory. during the proecss we will save a list of the file names that we have saved to, from which to stitch the new dataframe togehter from
    if low_ram_computer == True:
        year_counter = year - BASE_YEAR
        if year_counter % 10 == 0:
            print('The year is at the end of a ten year block, in year {}, saving interemediate results to csv.'.format(year))
            low_ram_file_name = 'intermediate_data/main_dataframe_10_year_blocks/main_dataframe_years_{}_to_{}.csv'.format(previous_10_year_block, year)
            main_dataframe.to_csv(low_ram_file_name, index=False)
            low_ram_computer_files_list.append(low_ram_file_name)

            previous_10_year_block = year
            main_dataframe = pd.DataFrame(columns=main_dataframe.columns)#remove data we just saved from main datafrmae

        elif year == END_YEAR:
            print('The year is at the end of the simulation, saving intermediate results to csv.')
            low_ram_file_name = 'intermediate_data/main_dataframe_10_year_blocks/main_dataframe_years_{}_to_{}.csv'.format(previous_10_year_block, year)
            main_dataframe.to_csv(low_ram_file_name, index=False)
            low_ram_computer_files_list.append(low_ram_file_name)
    else:
        
        if testing:
            # a = main_dataframe.merge(growth_forecasts[['Economy','Date','Activity_growth']].drop_duplicates(), on=['Economy','Date'], how='left')
            # a = a[['Activity','Activity_growth','Date', 'Economy', 'Vehicle Type', 'Medium', 'Transport Type', 'Drive','Scenario']]
            # #     #grab vehicle type = ldv, transport type = passenger, drive = bev, scenario = Target
            # a = a[(a['Economy']=='20_USA') & (a['Vehicle Type'] == 'ldv') & (a['Transport Type'] == 'passenger') & (a['Drive'] == 'bev') & (a['Scenario'] == 'Target')].drop_duplicates()
            breakpoint()
    #     #plot the sum of activity of 20_USA  for transport ype = passenger, with the activity growth on the right axis. 
    #     import plotly.express as px
    #     fig = px.line(a, x="Date", y="Activity", color='Drive', title='Activity of 20_USA for transport type = passenger')
    #     #and include the activity growth on the right axis
    #     fig.add_scatter(x=a['Date'].drop_duplicates(), y=a['Activity_growth'].drop_duplicates(), mode='lines', name='Activity growth', yaxis='y2')
    #     fig.update_layout(yaxis=dict(title='Activity'), yaxis2=dict(title='Activity growth', overlaying='y', side='right'))
    #     #write to html
    #     fig.write_html(f"20_USA_activity_{year}.html")

    return main_dataframe,previous_year_main_dataframe, low_ram_computer_files_list, change_dataframe_aggregation, gompertz_function_diagnostics_dataframe, previous_10_year_block
    

def prepare_road_model_inputs(road_model_input,low_ram_computer=True):
        
    #separate user inputs into different dataframes
    gompertz_parameters = road_model_input[['Economy','Scenario','Date', 'Transport Type','Vehicle Type', 'Gompertz_gamma']].drop_duplicates().dropna()#note we keep gamma in main df,. 'Gompertz_alpha', 'Gompertz_beta',
    #add values for BASE YEAR. THey can be the values from the first year of the model
    gompertz_parameters = pd.concat([gompertz_parameters, gompertz_parameters[gompertz_parameters['Date']==BASE_YEAR+1].replace(BASE_YEAR+1, BASE_YEAR)], ignore_index=True)
    Vehicle_sales_share = road_model_input[['Economy','Scenario', 'Drive', 'Vehicle Type', 'Transport Type', 'Date', 'Vehicle_sales_share']].drop_duplicates()
    Occupancy_or_load_growth = road_model_input[['Economy','Scenario', 'Drive','Vehicle Type', 'Transport Type', 'Date', 'Occupancy_or_load_growth']].drop_duplicates()
    Turnover_rate_growth = road_model_input[['Economy','Scenario','Vehicle Type', 'Transport Type', 'Drive', 'Date', 'Turnover_rate_growth']].drop_duplicates()
    New_vehicle_efficiency_growth = road_model_input[['Economy','Scenario', 
    'Vehicle Type', 'Transport Type', 'Drive', 'Date', 'New_vehicle_efficiency_growth']].drop_duplicates()
    Mileage_growth = road_model_input[['Economy','Scenario', 'Drive', 'Vehicle Type', 'Transport Type', 'Date', 'Mileage_growth']].drop_duplicates()

    #put the dataframes into a dictionary to pass into the funciton togetehr:
    user_inputs_df_dict = {'Vehicle_sales_share':Vehicle_sales_share, 'Occupancy_or_load_growth':Occupancy_or_load_growth, 'Turnover_rate_growth':Turnover_rate_growth, 'New_vehicle_efficiency_growth':New_vehicle_efficiency_growth, 'Mileage_growth':Mileage_growth, 'gompertz_parameters':gompertz_parameters}

    #drop those cols
    road_model_input = road_model_input.drop(['Vehicle_sales_share', 'Occupancy_or_load_growth', 'Turnover_rate_growth', 'New_vehicle_efficiency_growth','Mileage_growth',  'Gompertz_gamma'], axis=1)#'Gompertz_alpha', 'Gompertz_beta',

    #create main dataframe as previous Date dataframe, so that currently it only holds the base Date's data. This will have each Dates data added to it at the end of each loop.
    previous_year_main_dataframe = road_model_input.loc[road_model_input.Date == BASE_YEAR,:]
    main_dataframe = previous_year_main_dataframe.copy()
    change_dataframe_aggregation = pd.DataFrame()
    gompertz_function_diagnostics_dataframe = pd.DataFrame()

    #give option to run the process on a low RAM computer. If True then the loop will be split into 10 year blocks, saving each block in a csv, then starting again with an empty main datafrmae for the next 10 years block. If False then the loop will be run on all years without saving intermediate results.
    if low_ram_computer:
        previous_10_year_block = BASE_YEAR
        low_ram_computer_files_list = []
        #remove files from main_dataframe_10_year_blocks for previous runs
        for file in glob.glob(os.path.join('intermediate_data/main_dataframe_10_year_blocks/', '*.csv')):
            os.remove(file)
    else:
        previous_10_year_block = None
        low_ram_computer_files_list = None

    return main_dataframe,previous_year_main_dataframe, low_ram_computer_files_list, change_dataframe_aggregation, gompertz_function_diagnostics_dataframe,previous_10_year_block, user_inputs_df_dict,low_ram_computer


def join_and_save_road_model_outputs(main_dataframe, low_ram_computer, low_ram_computer_files_list,ANALYSE_CHANGE_DATAFRAME,change_dataframe_aggregation, gompertz_function_diagnostics_dataframe):
    #this will be the name of the output file
    new_output_file = 'intermediate_data/road_model/{}'.format(model_output_file_name)

    #now, we will save the main dataframe to a csv file. if the computer is low ram, we will create the file from the already saved 10 year block interval files
    if low_ram_computer == True:
        main_dataframe = pd.DataFrame()
        print('The computer is low ram, stitching together the main dataframe from the 10 year block files.')

        #TO CONSIDER, IF WE ARE STILL HAVING MEMORY ISSUES:
        # WE HAVE A CHOICE HERE WHETHER WE WANT TO STITCH ALL THE FILES ONTO A DATAFRAME THEN SAVE TO A CSV, OR ONLY OPEN ONE DATAFRAME AT A TIME, SEQUENTIALLY WRITING THEM TO A CSV WITHOUT OPENING THE CSV USING APPEND OPTION. ONE OTHER ISSUE IS THAT IF WE WILL STILL HAVE ONE GIANT CSV AT THE END, IT WILL CAUSE WHICHEVER COMPUTER LOADS IT TO BE SLOW SO PERHAPS ITS BEST TO SAVE THE DATA IN GROUPS DEPDNING ON THE DATATYPE OR ITS USEFULNESS?

        #FOR NOW LETS JUST WRITE THEM TO A CSV SEQUENTIALLY AS THAT SEEMS TO BE WORKING

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

    #save gompertz_function_diagnostics_dataframe to csv
    gompertz_function_diagnostics_dataframe.to_csv('intermediate_data/road_model/{}'.format(gompertz_function_diagnostics_dataframe_file_name), index=False)

    plot_gompertz_function_diagnostics_dataframe = False
    if plot_gompertz_function_diagnostics_dataframe:
        import plot_gompertz_data
        plot_gompertz_data(gompertz_function_diagnostics_dataframe)

    return main_dataframe
#######################################################################
#######################################################################
#######################################################################
#######################################################################
#LOGISTIC FITTING FUNCTIONS
#######################################################################
#######################################################################
#######################################################################
#######################################################################


def logistic_fitting_function_handler(model_data,show_plots=False,matplotlib_bool=False, plotly_bool=False):
    """Take in output of stocks,occupancy, travel_km, activity and mileage from running road model on a gdp per cpita based growth rate. Then fit a logistic curve to the stocks data with the gamma value from each economy provided. 
    Then with this curve, extract the expected activity per year based on the expected stocks per year and the expected mileage per year. Then recalculate the growth rate over time based on this. We will then use this to rerun the road model with the new growth rate.
    This will be done for each economy and vehicle type in passenger vehicles. 
    
    Perhaps the simplest case will be to calcualte it for only the ldv's and then use the same growth rate for the other vehicle types in passenger transport. 
    This will be done for each scenario too because movement between vehicle types might change the growth rate."""
    #grab only passenger data 
    model_data = model_data.loc[(model_data['Transport Type'] == 'passenger')]
    #EXTRACT PARAMETERS FOR LOGISTIC FUNCTION:
    parameters_estimates = find_parameters_for_logistic_function(model_data, show_plots, matplotlib_bool, plotly_bool)
    #some parameters will be np.nan because we dont need to fit the curve for all economies. We will drop these and not recalculate the growth rate for these economies
    parameters_estimates = parameters_estimates.dropna(subset=['Gompertz_gamma'])

    #CREATE NEW DATAFRAME WITH LOGISTIC FUNCTION PREDICTIONS
    #FILTER FOR LDVS ONLY (TODO: DO THIS FOR ALL VEHICLE TYPES)
    model_data_ldvs = model_data.loc[(model_data['Vehicle Type'] == 'ldv')]
    #grab only cols we need
    model_data_ldvs = model_data_ldvs[['Date', 'Economy', 'Scenario','Vehicle Type', 'Stocks', 'Occupancy_or_load', 'Mileage', 'Population', 'Gdp_per_capita','Activity', 'Travel_km']]
    #join the params on: #PLEASE NOTE THAT WE ARE ASSUMING WE HAVENT CHANGD GAMMA IN THE PARAMETERS ESTIMATES. AS SUCH WE JOIN IT IN HERE. THIS MAY CHANGE IN THE FUTURE
    model_data_ldvs = model_data_ldvs.merge(parameters_estimates, on=['Economy', 'Scenario','Vehicle Type'], how='inner')

    #sum stocks,'Activity', Travel_km, , with any NAs set to 0
    model_data_ldvs['Stocks'] = model_data_ldvs['Stocks'].fillna(0)
    model_data_ldvs['Activity'] = model_data_ldvs['Activity'].fillna(0)
    model_data_ldvs['Travel_km'] = model_data_ldvs['Travel_km'].fillna(0)
    
    summed_values = model_data_ldvs.groupby(['Date','Economy', 'Vehicle Type'])['Stocks','Activity', 'Travel_km'].sum().reset_index()
    #join stocks with other data
    model_data_ldvs.drop(columns=['Stocks','Activity', 'Travel_km'], inplace=True)
    model_data_ldvs.drop_duplicates(inplace=True)
    model_data_ldvs = model_data_ldvs.merge(summed_values, on=['Date','Economy', 'Vehicle Type'], how='left')
    # breakpoint()
    model_data_logistic_predictions = create_new_dataframe_with_logistic_predictions(model_data_ldvs)

    #find growth rate of activity as the percentage change in activity from the previous year plus 1. make sur eto group by economy and scenario BUT NOT BY VEHICLE TYPE (PLEASE NOTE THAT THIS MAY CHANGE IN THE FUTURE)
    activity_growth_estimates = model_data_logistic_predictions[['Date', 'Economy', 'Scenario', 'Activity']].drop_duplicates().groupby(['Date', 'Economy', 'Scenario'])['Activity'].sum().reset_index()

    activity_growth_estimates.sort_values(['Economy', 'Scenario', 'Date'], inplace=True)
    activity_growth_estimates['Activity_growth'] = activity_growth_estimates.groupby(['Economy', 'Scenario'])['Activity'].pct_change()+1
    #replace nan with 1
    activity_growth_estimates['Activity_growth'] = activity_growth_estimates['Activity_growth'].fillna(1)

    #if matplotlib_bool or plotly_bool:
    if matplotlib_bool or plotly_bool:
        plot_logistic_function_all_economies(model_data_logistic_predictions, activity_growth_estimates, parameters_estimates, model_data, show_plots, matplotlib_bool, plotly_bool)
        plot_logistic_function_by_economy(model_data_logistic_predictions, activity_growth_estimates, parameters_estimates, model_data, show_plots, matplotlib_bool, plotly_bool)

    #drop Activity from activity_growth_estimates
    activity_growth_estimates.drop(columns=['Activity'], inplace=True)
    
    return activity_growth_estimates, parameters_estimates

#CREATE NEW DATAFRAME WITH LOGISTIC FUNCTION PREDICTIONS
def create_new_dataframe_with_logistic_predictions(model_data):
    """ Take in the model data and the parameters estimates and create a new dataframe with the logistic function predictions for the stocks, activity and mileage basedon the parameters and the gdp per cpita. This will first calcualte the stocks, then using mileage, calcualte the travel km, then calcualte activity based on the occupancy rate"""
    #calculate new stocks:
    model_data_logistic_predictions = model_data.copy()
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

def find_parameters_for_logistic_function(model_data, show_plots, matplotlib_bool, plotly_bool, proportion_below_gamma= 0.05):
    
    #loop through economies and vehicle types
    #create empty dataframe to store results

    #filter for only ldv for now
    model_data = model_data.loc[(model_data['Vehicle Type'] == 'ldv')]

    parameters_estimates = pd.DataFrame(columns=['Gompertz_beta', 'Gompertz_alpha', 'Gompertz_gamma', 'Economy', 'Vehicle Type', 'Scenario'])
    for economy in model_data['Economy'].unique():
        for scenario in model_data['Scenario'].unique():
            for vehicle_type in model_data['Vehicle Type'].unique():

                economy_vtype_scenario = economy + '_' + vehicle_type + '_' + scenario

                #filter for economy and vehicle type
                model_data_economy_scenario_vtype = model_data[(model_data['Economy']==economy) & (model_data['Vehicle Type']==vehicle_type) & (model_data['Scenario']==scenario)]

                #filter for cols we need:
                model_data_economy_scenario_vtype = model_data_economy_scenario_vtype[['Date', 'Vehicle Type', 'Stocks', 'Gdp_per_capita','Population', 'Gompertz_gamma', 'Travel_km', 'Mileage', 'Activity']].drop_duplicates()

                #sum stocks,'Activity', Travel_km, , with any NAs set to 0
                model_data_economy_scenario_vtype['Stocks'] = model_data_economy_scenario_vtype['Stocks'].fillna(0)
                model_data_economy_scenario_vtype['Activity'] = model_data_economy_scenario_vtype['Activity'].fillna(0)
                model_data_economy_scenario_vtype['Travel_km'] = model_data_economy_scenario_vtype['Travel_km'].fillna(0)

                summed_values = model_data_economy_scenario_vtype.groupby(['Date', 'Vehicle Type'])['Stocks','Activity', 'Travel_km'].sum().reset_index()
                #join stocks with other data
                model_data_economy_scenario_vtype.drop(columns=['Stocks','Activity', 'Travel_km'], inplace=True)
                model_data_economy_scenario_vtype.drop_duplicates(inplace=True)
                model_data_economy_scenario_vtype = model_data_economy_scenario_vtype.merge(summed_values, on=['Date', 'Vehicle Type'], how='left')

                #calcualte stocks per capita
                model_data_economy_scenario_vtype['Thousand_stocks_per_capita'] = model_data_economy_scenario_vtype['Stocks']/model_data_economy_scenario_vtype['Population']
                #convert to more readable units. We will convert back later if we need to #todo do we need to?
                model_data_economy_scenario_vtype['Stocks_per_thousand_capita'] = model_data_economy_scenario_vtype['Thousand_stocks_per_capita'] * 1000000

                #find date where stocks per cpaita passes gamma, then find a proportion below that and set that as the point where we plot remaining stocks per capita, going linearly to gamma by the end of the time period
                #find the date where stocks per capita passes gamma
                gamma = model_data_economy_scenario_vtype['Gompertz_gamma'].unique()[0]
                date_where_stocks_per_capita_passes_gamma = model_data_economy_scenario_vtype[model_data_economy_scenario_vtype['Stocks_per_thousand_capita'] > gamma]['Date'].min()

                #sometimes the date is not found. in which case we ahve no issue with the stocks per capita going aobve gamma. So we dont need to adjsut growth rates for this economy. 
                if np.isnan(date_where_stocks_per_capita_passes_gamma):
                    #set parameters to nan so that we can filter them out later
                    params = pd.DataFrame({'Gompertz_beta':np.nan, 'Gompertz_alpha':np.nan, 'Gompertz_gamma':np.nan, 'Economy': economy, 'Vehicle Type': vehicle_type, 'Scenario': scenario}, index=[0])
                    #concat to parameters_estimates
                    parameters_estimates = pd.concat([parameters_estimates, params], axis=0).reset_index(drop=True)

                else:
                    #extract data after this date and set the stocks per capita to be a linear line from the gamma - gamma*proportion_below_gamma to gamma over the time period
                    data_to_change = model_data_economy_scenario_vtype[model_data_economy_scenario_vtype['Date'] >= date_where_stocks_per_capita_passes_gamma]
                    data_to_change['Stocks_per_thousand_capita'] = [gamma - (gamma * proportion_below_gamma) + ((gamma * proportion_below_gamma) / len(data_to_change['Stocks_per_thousand_capita'])) * i for i in range(len(data_to_change['Stocks_per_thousand_capita']))]#todo check this is correct

                    #add this back to the main dataframe
                    model_data_economy_scenario_vtype[model_data_economy_scenario_vtype['Date'] >= date_where_stocks_per_capita_passes_gamma] = data_to_change

                    #fit a logistic curve to the stocks per capita data
                    gamma, growth_rate, midpoint = logistic_fitting_function(model_data_economy_scenario_vtype, gamma, economy_vtype_scenario, show_plots,matplotlib_bool=matplotlib_bool, plotly_bool=plotly_bool)
                    
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
    
def logistic_fitting_function(model_data_economy_scenario_vtype, gamma, economy_vtype_scenario, show_plots, matplotlib_bool, plotly_bool):
    #grab data we need
    date = model_data_economy_scenario_vtype['Date']
    stocks_per_capita = model_data_economy_scenario_vtype['Stocks_per_thousand_capita']
    #TODO NOT SURE IF WE WANT TO GRAB GDP PER CPITA OR FIT THE MODEL TO THE YEAR NOW? IM GOING TO TRY USING GDP PER CPAITA SO THAT AT ELAST THE PARAMETER ESTIMATES CAN BE SHARED BETWEEN ECONOMIES IN TERMS OF GDP PER CAPITA
    gdp_per_capita = model_data_economy_scenario_vtype['Gdp_per_capita']
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
        
def plot_logistic_function_all_economies(model_data_logistic_predictions, activity_growth_estimates, parameters_estimates, model_data, show_plots, matplotlib_bool, plotly_bool):
    #we will plot the results of the logistic function fit. To cut down on the number of plots we will facet by economy and onily plot the first scenario
    #we will also plot the gamma value for each economy as a horizontal line if the data is on stock per capita
    #extact model_data that will be used
    #calcualte Stocks_per_thousand_capita for model data

    #calcualte stocks per capita
    model_data['Thousand_stocks_per_capita'] = model_data['Stocks']/model_data['Population']
    #convert to more readable units. We will convert back later if we need to #todo do we need to?
    model_data['Stocks_per_thousand_capita'] = model_data['Thousand_stocks_per_capita'] * 1000000
    model_data = model_data[['Date', 'Economy', 'Scenario', 'Vehicle Type', 'Stocks_per_thousand_capita', 'Activity']].drop_duplicates()
    #sum up
    model_data = model_data.groupby(['Date', 'Economy', 'Scenario', 'Vehicle Type']).sum().reset_index()

    #join the dataframes together
    all_data = pd.merge(model_data_logistic_predictions, model_data, on=['Date', 'Economy', 'Scenario', 'Vehicle Type'], how='left', suffixes=('_logistic', '_previous'))
    #join on activity_growth_estimates. Note that this ISNT BY VEHIcle type
    all_data = pd.merge(all_data, activity_growth_estimates, on=['Date','Economy', 'Scenario'], how='left')
    
    all_data = all_data.loc[(all_data['Scenario'] == SCENARIO_OF_INTEREST)]
    #TEMP FIX SINCE WE ONLY CAULCATED STOCKS PER CAPITA FOR LDVS
    all_data = all_data.loc[(all_data['Vehicle Type'] == 'ldv')]
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

def plot_logistic_function_by_economy(model_data_logistic_predictions, activity_growth_estimates, parameters_estimates, model_data, show_plots, matplotlib_bool, plotly_bool):
    #we will plot the results of the logistic function fit. To cut down on the number of plots we will facet by economy and onily plot the first scenario
    #we will also plot the gamma value for each economy as a horizontal line if the data is on stock per capita
    #extact model_data that will be used
    #calcualte Stocks_per_thousand_capita for model data

    #calcualte stocks per capita
    model_data['Thousand_stocks_per_capita'] = model_data['Stocks']/model_data['Population']
    #convert to more readable units. We will convert back later if we need to #todo do we need to?
    model_data['Stocks_per_thousand_capita'] = model_data['Thousand_stocks_per_capita'] * 1000000
    model_data = model_data[['Date', 'Economy', 'Scenario', 'Vehicle Type', 'Stocks_per_thousand_capita', 'Activity']].drop_duplicates()
    #sum up
    model_data = model_data.groupby(['Date', 'Economy', 'Scenario', 'Vehicle Type']).sum().reset_index()

    #join the dataframes together
    all_data = pd.merge(model_data_logistic_predictions, model_data, on=['Date', 'Economy', 'Scenario', 'Vehicle Type'], how='left', suffixes=('_logistic', '_previous'))
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

