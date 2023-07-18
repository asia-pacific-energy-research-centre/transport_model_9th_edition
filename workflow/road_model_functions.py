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


def run_road_model_for_year_y(year, previous_year_main_dataframe, main_dataframe, user_inputs_df_dict, growth_forecasts, change_dataframe_aggregation, gompertz_function_diagnostics_dataframe, low_ram_computer_files_list, low_ram_computer, ANALYSE_CHANGE_DATAFRAME,previous_10_year_block, testing = False, old_vehicle_economies = ['19_THA']):
    print('Up to year {}. The loop will run until year {}'.format(year, END_YEAR))
    # breakpoint()
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
    #check for nas?
    breakpoint()#think i should
    #check if activity matches sum of activity when you calcualte it as (change_dataframe['Activity']/( change_dataframe['Mileage'] * change_dataframe['Occupancy_or_load']))
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
    #######################################################################

    #First do adjustments:

    #######################################################################

    #CALCUALTE NEW OCCUPANCY and LOAD VALUEs BY APPLYING THE OCCUPANCY GROWTH RATE
    change_dataframe = change_dataframe.merge(Occupancy_or_load_growth, on=['Economy','Scenario','Drive','Vehicle Type', 'Transport Type', 'Date'], how='left')
    change_dataframe['Occupancy_or_load'] = change_dataframe['Occupancy_or_load'] * change_dataframe['Occupancy_or_load_growth']

    #CALCUALTE NEW TURNOVER RATE AND THEN TURNOVER OF OLD STOCKS
    change_dataframe = change_dataframe.merge(Turnover_rate_growth, on=['Economy', 'Scenario', 'Drive', 'Transport Type', 'Vehicle Type', 'Date'], how='left')
    # #now apply turnover growth rate to turnover rate
    if not USE_MEAN_AGES:
        change_dataframe['Turnover_rate'] = change_dataframe['Turnover_rate'] * change_dataframe['Turnover_rate_growth']
    else:
        #####################TESTING TURNOVER RATE GROWTH AND AGE ADJUSTMENT
        #repalce nas in change_dataframe['Average_age'] with 1, as it occurs when tehre are no stocks, and we want to set the average age to 1. Im not 100% on this fix but it seems like tis important to do as im getting 0s for stocks for all years when i dont do it.
        change_dataframe['Average_age'] = change_dataframe['Average_age'].replace(np.nan, 1)
        #and replace 0s too
        change_dataframe['Average_age'] = change_dataframe['Average_age'].replace(0, 1)
        #####################
        #set midpoint in the df based on whether the economy is old or new
        #old_vehicle_economies = ['19_THA']increase x0 (midpoint) for these economies to make the turnover rate growth start later in the life of the vehicle
        midpoint_new = 12.5
        midpoint_old = midpoint_new+5
        #put the midpoint in the df
        change_dataframe['Midpoint_age'] = midpoint_new
        change_dataframe['Midpoint_age'] = change_dataframe['Midpoint_age'].map(lambda x: midpoint_old if x in old_vehicle_economies else midpoint_new)

        def calculate_turnover_rate(avg_age, midpoint, k=0.7):
            
            # k = 0.7 #this is the steepness of the curve (increase it to speed up the turnover rate growth with age)
            # x0 = 12.5 #this is the midpoint of the curve (increase it to make the turnover rate growth start later in the life of the vehicle)
            return 1 / (1 + np.exp(-k * (avg_age - midpoint)))
        # Calculate turnover rates based on average age
        # ev_turnover = calculate_turnover_rate(ev_mean_age, k, x0)
        # ice_turnover = calculate_turnover_rate(ice_mean_age, k, x0)
        new_economies_df = change_dataframe[change_dataframe['Economy'].isin(old_vehicle_economies) == False].copy()  
        new_economies_df['Turnover_rate'] = new_economies_df['Average_age'].map(lambda x: calculate_turnover_rate(x, midpoint_new))

        old_economies_df = change_dataframe[change_dataframe['Economy'].isin(old_vehicle_economies)].copy()
        old_economies_df['Turnover_rate'] = old_economies_df['Average_age'].map(lambda x: calculate_turnover_rate(x, midpoint_old))

        change_dataframe = pd.concat([new_economies_df, old_economies_df])

        #CALCULATE PREVIOUSLY AVAILABLE STOCKS AS SUM OF STOCKS AND SURPLUS STOCKS
        change_dataframe['Original_stocks'] = change_dataframe['Stocks'] + change_dataframe['Surplus_stocks']
    #####################TESTING TURNOVER RATE GROWTH AND AGE ADJUSTMENT
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
    # 
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

    #########TESTING TURNOVER RATE GROWTH AND AGE ADJUSTMENT
    if USE_MEAN_AGES:
        # Calculate new mean age after turnover by assuming that the cars being removed are x * standard deviation above the mean. The new average age after turnover can be calculated as follows:
        std_deviation_share = 0.5#1 was a bit high
        change_dataframe['Average_age'] = change_dataframe['Average_age'] - (std_deviation_share * change_dataframe['Average_age'] * change_dataframe['Turnover_rate'])
        
        change_dataframe['Average_age'] = (change_dataframe['Average_age'] * (change_dataframe['Original_stocks'] - change_dataframe['Original_stocks'] * change_dataframe['Turnover_rate']) + 0 * change_dataframe['New_stocks_needed']) / (change_dataframe['Original_stocks'] - change_dataframe['Original_stocks'] * change_dataframe['Turnover_rate'] + change_dataframe['New_stocks_needed'])
        #increase age by 1 year to simulate the fact that the cars are 1 year older
        change_dataframe['Average_age'] = change_dataframe['Average_age'] + 1
        
    #########TESTING TURNOVER RATE GROWTH AND AGE ADJUSTMENT
    
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
    breakpoint() #can new stocks needed ever be na?
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
    breakpoint() #can new stocks needed ever be na?
    #calcualte stocks per capita as its a useful metric
    change_dataframe['Thousand_stocks_per_capita'] = change_dataframe['Stocks']/change_dataframe['Population']
    change_dataframe['Stocks_per_thousand_capita'] = change_dataframe['Thousand_stocks_per_capita'] * 1000000

    #Now start cleaning up the changes dataframe to create the dataframe for the new year.
    addition_to_main_dataframe = change_dataframe.copy()
    
    if USE_MEAN_AGES:
        addition_to_main_dataframe = addition_to_main_dataframe[['Economy', 'Scenario', 'Transport Type', 'Vehicle Type', 'Medium','Date', 'Drive', 'Activity', 'Stocks', 'Efficiency', 'Energy', 'Surplus_stocks', 'Travel_km', 'Mileage', 'Vehicle_sales_share', 'Occupancy_or_load', 'Turnover_rate', 'New_vehicle_efficiency','Stocks_per_thousand_capita', 'Activity_growth', 'Gdp_per_capita','Gdp', 'Population', 'Average_age']]
    else:
        addition_to_main_dataframe = addition_to_main_dataframe[['Economy', 'Scenario', 'Transport Type', 'Vehicle Type', 'Medium','Date', 'Drive', 'Activity', 'Stocks', 'Efficiency', 'Energy', 'Surplus_stocks', 'Travel_km', 'Mileage', 'Vehicle_sales_share', 'Occupancy_or_load', 'Turnover_rate', 'New_vehicle_efficiency','Stocks_per_thousand_capita', 'Activity_growth', 'Gdp_per_capita','Gdp', 'Population']]

    # 
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
            breakpoint()
            # a = main_dataframe.merge(growth_forecasts[['Economy','Date','Activity_growth']].drop_duplicates(), on=['Economy','Date'], how='left')
            # a = a[['Activity','Activity_growth','Date', 'Economy', 'Vehicle Type', 'Medium', 'Transport Type', 'Drive','Scenario']]
            # #     #grab vehicle type = ldv, transport type = passenger, drive = bev, scenario = Target
            # a = a[(a['Economy']=='20_USA') & (a['Vehicle Type'] == 'ldv') & (a['Transport Type'] == 'passenger') & (a['Drive'] == 'bev') & (a['Scenario'] == 'Target')].drop_duplicates()
            
    #     #plot the sum of activity of 20_USA  for transport ype = passenger, with the activity growth on the right axis. 
    #     import plotly.express as px
    #     fig = px.line(a, x="Date", y="Activity", color='Drive', title='Activity of 20_USA for transport type = passenger')
    #     #and include the activity growth on the right axis
    #     fig.add_scatter(x=a['Date'].drop_duplicates(), y=a['Activity_growth'].drop_duplicates(), mode='lines', name='Activity growth', yaxis='y2')
    #     fig.update_layout(yaxis=dict(title='Activity'), yaxis2=dict(title='Activity growth', overlaying='y', side='right'))
    #     #write to html
    #     fig.write_html(f"20_USA_activity_{year}.html")

    return main_dataframe,previous_year_main_dataframe, low_ram_computer_files_list, change_dataframe_aggregation, gompertz_function_diagnostics_dataframe, previous_10_year_block
    

def prepare_road_model_inputs(BASE_YEAR_x,road_model_input,low_ram_computer=True):
        
    #separate user inputs into different dataframes
    gompertz_parameters = road_model_input[['Economy','Scenario','Date', 'Transport Type','Vehicle Type', 'Gompertz_gamma']].drop_duplicates().dropna().copy()#note we keep gamma in main df,. 'Gompertz_alpha', 'Gompertz_beta',
    #add values for BASE YEAR. THey can be the values from the first year of the model
    gompertz_parameters = pd.concat([gompertz_parameters, gompertz_parameters[gompertz_parameters['Date']==BASE_YEAR_x+1].replace(BASE_YEAR_x+1, BASE_YEAR_x)], ignore_index=True)
    Vehicle_sales_share = road_model_input[['Economy','Scenario', 'Drive', 'Vehicle Type', 'Transport Type', 'Date', 'Vehicle_sales_share']].drop_duplicates().copy()
    Occupancy_or_load_growth = road_model_input[['Economy','Scenario', 'Drive','Vehicle Type', 'Transport Type', 'Date', 'Occupancy_or_load_growth']].drop_duplicates().copy()
    Turnover_rate_growth = road_model_input[['Economy','Scenario','Vehicle Type', 'Transport Type', 'Drive', 'Date', 'Turnover_rate_growth']].drop_duplicates().copy()
    New_vehicle_efficiency_growth = road_model_input[['Economy','Scenario', 
    'Vehicle Type', 'Transport Type', 'Drive', 'Date', 'New_vehicle_efficiency_growth']].drop_duplicates().copy()
    Mileage_growth = road_model_input[['Economy','Scenario', 'Drive', 'Vehicle Type', 'Transport Type', 'Date', 'Mileage_growth']].drop_duplicates().copy()

    #put the dataframes into a dictionary to pass into the funciton togetehr:
    user_inputs_df_dict = {'Vehicle_sales_share':Vehicle_sales_share, 'Occupancy_or_load_growth':Occupancy_or_load_growth, 'Turnover_rate_growth':Turnover_rate_growth, 'New_vehicle_efficiency_growth':New_vehicle_efficiency_growth, 'Mileage_growth':Mileage_growth, 'gompertz_parameters':gompertz_parameters}

    #drop those cols
    road_model_input = road_model_input.drop(['Vehicle_sales_share', 'Occupancy_or_load_growth', 'Turnover_rate_growth', 'New_vehicle_efficiency_growth','Mileage_growth',  'Gompertz_gamma'], axis=1)#'Gompertz_alpha', 'Gompertz_beta',

    #create main dataframe as previous Date dataframe, so that currently it only holds the base Date's data. This will have each Dates data added to it at the end of each loop.
    previous_year_main_dataframe = road_model_input.loc[road_model_input.Date == BASE_YEAR_x,:].copy()
    main_dataframe = previous_year_main_dataframe.copy()
    change_dataframe_aggregation = pd.DataFrame()
    gompertz_function_diagnostics_dataframe = pd.DataFrame()

    #give option to run the process on a low RAM computer. If True then the loop will be split into 10 year blocks, saving each block in a csv, then starting again with an empty main datafrmae for the next 10 years block. If False then the loop will be run on all years without saving intermediate results.
    if low_ram_computer:
        previous_10_year_block = BASE_YEAR_x
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








