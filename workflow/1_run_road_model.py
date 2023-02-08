#generally this will all work on the grouping of economy, year, v-type, drive, transport type, and scenario. There is a model simulation excel workbook in the documentation folder to more easily understand the operations here.

#NOTE that there is still the fuel mixing operation that is not in this file of code. 
#%%
#set working directory as one folder back so that config works
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
from runpy import run_path
exec(open("config/config.py").read())#usae this to load libraries and set variables. Feel free to edit that file as you need

#%%
#load all data except activity data (which is calcualteed separately to other calcualted inputs)
activity_growth = pd.read_csv('intermediate_data/model_inputs/activity_growth.csv')

#laod all other data
road_model_input = pd.read_csv('intermediate_data/model_inputs/road_model_input.csv')

#%%
#separate user inputs into different dataframes
Vehicle_sales_share = road_model_input[['Economy','Scenario', 'Drive', 'Vehicle Type', 'Transport Type', 'Date', 'Vehicle_sales_share']].drop_duplicates()
Occupancy_or_load_growth = road_model_input[['Economy','Scenario', 'Drive','Vehicle Type', 'Transport Type', 'Date', 'Occupancy_growth','Load_growth']].drop_duplicates()
Turnover_rate_growth = road_model_input[['Economy','Scenario','Vehicle Type', 'Transport Type', 'Drive', 'Date', 'Turnover_rate_growth']].drop_duplicates()
# Activity_growth = road_model_input[['Economy','Scenario', 'Date', 'Activity_growth']].drop_duplicates()
New_vehicle_efficiency_growth = road_model_input[['Economy','Scenario', 
'Vehicle Type', 'Transport Type', 'Drive', 'Date', 'New_vehicle_efficiency_growth']].drop_duplicates()

#drop those cols
road_model_input = road_model_input.drop(['Vehicle_sales_share', 'Occupancy_growth','Load_growth', 'Turnover_rate_growth', 'New_vehicle_efficiency_growth'], axis=1)
#%%
#create main dataframe as previous Date dataframe, so that currently it only holds the base Date's data. This will have each Dates data added to it at the end of each loop.
previous_year_main_dataframe = road_model_input.loc[road_model_input.Date == BASE_YEAR,:]
main_dataframe = previous_year_main_dataframe.copy()

#%%
#give option to run the process on a low RAM computer. If True then the loop will be split into 10 year blocks, saving each block in a csv, then starting again with an empty main datafrmae for the next 10 years block. If False then the loop will be run on all years without saving intermediate results.
low_ram_computer = True
if low_ram_computer:
    previous_10_year_block = BASE_YEAR
    low_ram_computer_files_list = []
    #remove files from main_dataframe_10_year_blocks for previous runs
    for file in glob.glob(os.path.join('intermediate_data/main_dataframe_10_year_blocks/', '*.csv')):
        os.remove(file)
#%%
#if you want to analyse what is hapening in th model then set this to true and the model will output a dataframe wioth all the variables that are being calculated.
ANALYSE_CHANGE_DATAFRAME = True
#######################################################################
#######################################################################

#%%
#START MAIN PROCESS
for year in range(BASE_YEAR+1, END_YEAR+1):
    
    print('Up to year {}. The loop will run until year {}'.format(year, END_YEAR))

    #create change dataframe. This is like a messy notepad where we will adjust the last years values values and perform most calcualtions. 
    change_dataframe = previous_year_main_dataframe.copy()

    #change year in all rows to the next year. For now we will refer to the previous year as the original or base year. And values calculcated for the next year may sometimes be refered to as 'new'.
    change_dataframe.Date = year

    #start calcualting new values using the orignal values and adjustments as stated/forecasted by the user.

    #generally this will all work on the grouping of economy, year, v-type, drive, transport type, and scenario. There is a model simulation excel workbook in the documentation folder to more easily understand the operations here.
        
    #NOTE that there is still the fuel mixing operation that is not in this file of code. 

    #######################################################################

    #First do adjustments:

    #######################################################################

    #CALCUALTE NEW OCCUPANCY and LOAD VALUEs BY APPLYING THE OCCUPANCY GROWTH RATE
    change_dataframe = change_dataframe.merge(Occupancy_or_load_growth, on=['Economy','Scenario','Drive','Vehicle Type', 'Transport Type', 'Date'], how='left')
    change_dataframe['Occupancy'] = change_dataframe['Occupancy'] * change_dataframe['Occupancy_growth']
    change_dataframe['Load'] = change_dataframe['Load'] * change_dataframe['Load_growth']

    #CALCUALTE NEW TURNOVER RATE AND THEN TURNOVER OF OLD STOCKS
    change_dataframe = change_dataframe.merge(Turnover_rate_growth, on=['Economy', 'Scenario', 'Drive', 'Transport Type', 'Vehicle Type', 'Date'], how='left')
    #now apply turnover growth rate to turnover rate
    change_dataframe['Turnover_rate'] = change_dataframe['Turnover_rate'] * change_dataframe['Turnover_rate_growth']

    #ERROR CHECK double check that turnover rate isnt greater than 1 (in which case the growth rate is too high)
    if change_dataframe['Turnover_rate'].max() > 1:
        print('ERROR: Turnover rate is greater than 1. This is not possible. Please check the Turnover rate growth data. Breaking the loop.')
        break

    #calcualte stock turnover as stocks from last year * turnover rate.
    change_dataframe['Stock_turnover'] = - change_dataframe['Stocks'] * change_dataframe['Turnover_rate']

    #calculate stock turnover plus surplus
    change_dataframe['Stock_turnover_and_surplus_total'] = change_dataframe['Stock_turnover'] + change_dataframe['Surplus_stocks'] 

    #SPLIT FREIGHT AND PASSENGER TRANSPORT TYPES:
    #THEN CALC RELATED VARIABLES FOR EACH TRANSPORT TYPE




    #######################################################################

    #FREIGHT

    #######################################################################




    
    #Filter for freight transport types
    freight_change_dataframe = change_dataframe.loc[change_dataframe['Transport Type'] == 'freight',:]

    #CALCUALTE ACTIVITY WORTH OF STOCK TURNOVER AND SURPLUS
    freight_change_dataframe['Activity_worth_of_stock_turnover_and_surplus'] = freight_change_dataframe['Stock_turnover_and_surplus_total'] * freight_change_dataframe['Travel_km_per_stock'] * freight_change_dataframe['Load']

    #Stocks after turnover and surplus total 
    freight_change_dataframe['Stocks_after_turnover_and_surplus_total'] = freight_change_dataframe['Stocks'] + freight_change_dataframe['Stock_turnover_and_surplus_total']

    #Activity worth of stocks after turnover and surplus total
    freight_change_dataframe['Activity_worth_of_stocks_after_turnover_and_surplus_total'] = freight_change_dataframe['Stocks_after_turnover_and_surplus_total'] * freight_change_dataframe['Travel_km_per_stock'] * freight_change_dataframe['Load']

    #Transport type sum of activity worth of stocks after turnover and surplus total
    freight_change_dataframe['Transport_type_sum_of_activity_worth_of_stocks_after_turnover_and_surplus_total'] = freight_change_dataframe.groupby(['Economy', 'Scenario', 'Transport Type', 'Date'])['Activity_worth_of_stocks_after_turnover_and_surplus_total'].transform('sum')

    #######################################################################
    #Now calcualte changes as a result of growth (and other things)
    #We will be working in terms of transport type sums for this section:
    #######################################################################

    #CALCULATE NEW ACTIVITY WORTH OF STOCK SALES
    #we will apply activity growth to the sum of activity for each transport type to find the activity worth of new sales from activity growth. Note that activity growth is assumed to be the same for all vehicle types of the same transport type (and probably for all transport types in early stages of this models development!)
    #We will also calcualte total turnover and surplus activity for the transport type to be satisfied by new stock sales, based on the new sales dist.

    #calcualte sum of activity (by default is summed by transport type but will keep original code to make it easier to change later)
    freight_change_dataframe['Transport_type_sum_of_activity'] = freight_change_dataframe.groupby(['Economy', 'Scenario', 'Transport Type', 'Date'])['freight_tonne_km'].transform('sum')

    #Now we will apply activity growth to original activity summed by transport type to find new activity to be satisfied by new veh
    # icles according to the stock dist.
    #join on activity growth
    freight_change_dataframe = freight_change_dataframe.merge(activity_growth, on=['Economy', 'Scenario', 'Date'], how='left')#one day if growth is determined by transport type, add transport type ot this grouping

    #calc
    freight_change_dataframe['Transport_type_sum_of_activity_growth'] = (freight_change_dataframe['Activity_growth'] * freight_change_dataframe['Transport_type_sum_of_activity'])

    #Activity worth of extra stocks needed
    #if the growth in activity plus last years activity is greater than the activity worth of leftover stocks then this will be postiive
    freight_change_dataframe['Transport_type_sum_of_activity_worth_of_extra_stocks_needed'] =  np.where(freight_change_dataframe['Transport_type_sum_of_activity_worth_of_stocks_after_turnover_and_surplus_total'] - freight_change_dataframe['Transport_type_sum_of_activity'] - freight_change_dataframe['Transport_type_sum_of_activity_growth'] < 0, - (freight_change_dataframe['Transport_type_sum_of_activity_worth_of_stocks_after_turnover_and_surplus_total'] - freight_change_dataframe['Transport_type_sum_of_activity'] - freight_change_dataframe['Transport_type_sum_of_activity_growth']) ,0)#note the use of miunus for calcualting it

    #Activity worth of extra stocks remaining
    #if the growth in activity plus last years activity is less than the activity worth of leftover stocks then this will be postiive
    freight_change_dataframe['Transport_type_sum_of_activity_worth_of_extra_stocks_remaining'] =  np.where(freight_change_dataframe['Transport_type_sum_of_activity_worth_of_stocks_after_turnover_and_surplus_total'] - freight_change_dataframe['Transport_type_sum_of_activity'] - freight_change_dataframe['Transport_type_sum_of_activity_growth'] > 0, freight_change_dataframe['Transport_type_sum_of_activity_worth_of_stocks_after_turnover_and_surplus_total'] - freight_change_dataframe['Transport_type_sum_of_activity'] - freight_change_dataframe['Transport_type_sum_of_activity_growth'] ,0)

    #% of transport type stocks worth of activity not used (transport type)
    freight_change_dataframe['Percent_of_transport_type_stocks_worth_of_activity_not_used'] = freight_change_dataframe['Transport_type_sum_of_activity_worth_of_extra_stocks_remaining'] / freight_change_dataframe['Transport_type_sum_of_activity_worth_of_stocks_after_turnover_and_surplus_total']
    #replace na's where there is 0/0 above
    freight_change_dataframe['Percent_of_transport_type_stocks_worth_of_activity_not_used'] = freight_change_dataframe['Percent_of_transport_type_stocks_worth_of_activity_not_used'].replace(np.nan, 0)

    #######################################################################
    #Now we will start working with inidivudal rows, for each vehicle type and drive combination.
    #######################################################################

    #Total surplus stocks worth of activity 
    freight_change_dataframe['Total_surplus_stocks_worth_of_activity'] = freight_change_dataframe['Activity_worth_of_stocks_after_turnover_and_surplus_total'] * freight_change_dataframe['Percent_of_transport_type_stocks_worth_of_activity_not_used']

    #VEHICLE SALES SHARE(also referreed to as Sales/Stock Dist)
    #New Activity worth of sales will be satisfied by different vehicle type / drive type combinations, as specified by the Vehicle_sales_share (stock/sales dist). Each year there is a new sales share, created by the user before running the model
    #1. merge onto the main df the vehicle sales share that user has specified 
    #Also, if there is already a Vehicle_sales_share column from the prev year, remove it (we keep the vehicle sales shbare in the change dataframe because its an extra interesting output)
    if 'Vehicle_sales_share' in freight_change_dataframe.columns:
        freight_change_dataframe.drop(columns=['Vehicle_sales_share'], inplace=True)

    freight_change_dataframe = freight_change_dataframe.merge(Vehicle_sales_share, on=['Economy', 'Scenario', 'Drive', 'Transport Type', 'Vehicle Type', 'Date'], how='left')

    #CALCULATE STOCK SALES TO BE SATISFIED BY EACH VEHICLETYPE/DRIVETYPE COMBINATION USING THE NEW VEHICLE SALES SHARES
    #Note that if Activity worth of extra stocks needed can be 0, and if so then this will be 0 too.
    freight_change_dataframe['Activity_worth_of_new_stock_sales'] = freight_change_dataframe['Transport_type_sum_of_activity_worth_of_extra_stocks_needed'] * freight_change_dataframe['Vehicle_sales_share']

    #CALCULATE NEW activity total of stocks being used as ACTIVITY
    freight_change_dataframe['freight_tonne_km'] = freight_change_dataframe['Activity_worth_of_new_stock_sales'] + freight_change_dataframe['Activity_worth_of_stocks_after_turnover_and_surplus_total'] - freight_change_dataframe['Total_surplus_stocks_worth_of_activity']

    #CALCUALTE NEW TOTAL TRAVEL_KM PER VEHICLE/DRIVE-TYPE FROM NEW activity total of stocks being useD
    freight_change_dataframe['Travel_km'] = freight_change_dataframe['freight_tonne_km'] / freight_change_dataframe['Load']

    #CALCUALTE NEW TOTAL TRAVEL_KM PER VEHICLE/DRIVE-TYPE FROM NEW STOCKS
    freight_change_dataframe['Travel_km_of_new_stocks'] = freight_change_dataframe['Activity_worth_of_new_stock_sales'] / freight_change_dataframe['Load']

    #CALCUALTE NEW TRAVEL_KM PER NEW VEHICLE/DRIVE-TYPE FROM NEW SALES WORTH OF ACTIVITY
    freight_change_dataframe['Travel_km_of_surplus_stocks'] = freight_change_dataframe['Total_surplus_stocks_worth_of_activity'] / freight_change_dataframe['Load']

    #CALCUALTE STOCKS BEING USED
    #Note that this is the new level of stocks in the economy
    freight_change_dataframe['Stocks'] = freight_change_dataframe['Travel_km'] / freight_change_dataframe['Travel_km_per_stock']

    #CALCUALTE NEW STOCKS NEEDED AS STOCKS NEEDED TO SATISFY NEW SALES WORTH OF ACTIVITY
    freight_change_dataframe['New_stocks_needed'] = freight_change_dataframe['Travel_km_of_new_stocks'] / freight_change_dataframe['Travel_km_per_stock']

    #CALCUALTE SURPLUS STOCKS
    #If we have too many stocks these go into surplus
    freight_change_dataframe['Surplus_stocks'] = freight_change_dataframe['Travel_km_of_surplus_stocks'] / freight_change_dataframe['Travel_km_per_stock']

    #CALCULATE STOCKS IN USE REMAINING FROM PREVIOUS YEAR
    freight_change_dataframe['Stocks_in_use_from_last_period'] = freight_change_dataframe['Stocks'] - freight_change_dataframe['New_stocks_needed']

    #SET EFFICIENCY OF SURPLUS STOCKS TO PREVIOUS YEARS AVG EFF LEVEL
    #Note that we assume that the efficiency of surplus stocks is the same as the efficiency of the stocks that were in use last year
    freight_change_dataframe['Efficiency_of_surplus_stocks'] = freight_change_dataframe['Efficiency']

    #APPLY EFFICIENCY GROWTH TO NEW VEHICLE EFFICIENCY
    #note that this will then be split into different fuel types when we appply the fuel mix varaible later on.
    #also note that new vehicle eff is independent of the current eff level of the eocnomys stocks. it could be much higher than them
    freight_change_dataframe = freight_change_dataframe.merge(New_vehicle_efficiency_growth, on=['Economy', 'Scenario', 'Transport Type', 'Drive', 'Vehicle Type', 'Date'], how='left')
    freight_change_dataframe['New_vehicle_efficiency'] = freight_change_dataframe['New_vehicle_efficiency'] * freight_change_dataframe['New_vehicle_efficiency_growth'] 

    #CALCUALTE WEIGHTED AVERAGE VEHICLE EFFICIENCY
    #calcaulte weighted avg vehicle eff using the number of stocks left from last year times their avg eff, then the number of new stocks needed times their new eff. Then divide these by the number of stocks left from last year plus the number of new stocks needed. 
    #however if new stocks needed is <0, but there are still stocks remaining in the economy then efficiency will remain the same as original efficiency.
    #also have to note that this is the avg eff of stocks in use, this is in case there is a large amount of surplus stocks, so that the avg eff of the economy is not skewed by the efficiency of the surplus stocks, and instead new stocks efficiency has the right effect on the avg eff of the economy.
    freight_change_dataframe['Efficiency_numerator'] = (freight_change_dataframe['New_stocks_needed'] * freight_change_dataframe['New_vehicle_efficiency'] + freight_change_dataframe['Stocks_in_use_from_last_period'] * freight_change_dataframe['Efficiency'])

    freight_change_dataframe['Original_efficiency'] = freight_change_dataframe['Efficiency']

    freight_change_dataframe['Efficiency'] = np.where(freight_change_dataframe['New_stocks_needed'] < 0, freight_change_dataframe['Original_efficiency'], freight_change_dataframe['Efficiency_numerator'] / freight_change_dataframe['Stocks'])

    #if the denominator and numerator are 0 (which will occur if we dont have any stocks in this year [and therefore the last]), then efficiency ends up as nan, so we will set this to the efficiency value for new vehicles even though it doesnt really matter what it is set to, it just helps with aggregates.
    freight_change_dataframe.loc[(freight_change_dataframe['Stocks'] == 0), 'Efficiency'] = freight_change_dataframe['New_vehicle_efficiency']

    #CALCUALTE NEW ENERGY CONSUMPTION. 
    #note that this is not split by fuel yet, it is just the total energy consumption for the vehicle/drive type.
    freight_change_dataframe['Energy'] = freight_change_dataframe['Travel_km'] / freight_change_dataframe['Efficiency'] 

    #if numerator and denominator are 0, then energy ends up as nan, so we will set this to 0
    freight_change_dataframe.loc[(freight_change_dataframe['Travel_km'] == 0) & (freight_change_dataframe['Efficiency'] == 0), 'Energy'] = 0




    #######################################################################

    #Passenger

    #######################################################################



    #Filter for freight transport types
    passenger_change_dataframe = change_dataframe.loc[change_dataframe['Transport Type'] == 'passenger',:]

    #CALCUALTE ACTIVITY WORTH OF STOCK TURNOVER AND SURPLUS
    passenger_change_dataframe['Activity_worth_of_stock_turnover_and_surplus'] = passenger_change_dataframe['Stock_turnover_and_surplus_total'] * passenger_change_dataframe['Travel_km_per_stock'] * passenger_change_dataframe['Occupancy']

    #Stocks after turnover and surplus total 
    passenger_change_dataframe['Stocks_after_turnover_and_surplus_total'] = passenger_change_dataframe['Stocks'] + passenger_change_dataframe['Stock_turnover_and_surplus_total']

    #Activity worth of stocks after turnover and surplus total
    passenger_change_dataframe['Activity_worth_of_stocks_after_turnover_and_surplus_total'] = passenger_change_dataframe['Stocks_after_turnover_and_surplus_total'] * passenger_change_dataframe['Travel_km_per_stock'] * passenger_change_dataframe['Occupancy']

    #Transport type sum of activity worth of stocks after turnover and surplus total
    passenger_change_dataframe['Transport_type_sum_of_activity_worth_of_stocks_after_turnover_and_surplus_total'] = passenger_change_dataframe.groupby(['Economy', 'Scenario', 'Transport Type', 'Date'])['Activity_worth_of_stocks_after_turnover_and_surplus_total'].transform('sum')

    #######################################################################
    #Now calcualte changes as a result of growth (and other things)
    #We will be working in terms of transport type sums for this section:
    #######################################################################

    #CALCULATE NEW ACTIVITY WORTH OF STOCK SALES
    #we will apply activity growth to the sum of activity for each transport type to find the activity worth of new sales from activity growth. Note that activity growth is assumed to be the same for all vehicle types of the same transport type (and probably for all transport types in early stages of this models development!)
    #We will also calcualte total turnover and surplus activity for the transport type to be satisfied by new stock sales, based on the new sales dist.

    #calcualte sum of activity (by default is summed by transport type but will keep original code to make it easier to change later)
    passenger_change_dataframe['Transport_type_sum_of_activity'] = passenger_change_dataframe.groupby(['Economy', 'Scenario', 'Transport Type', 'Date'])['passenger_km'].transform('sum')

    #Now we will apply activity growth to original activity summed by transport type to find new activity to be satisfied by new veh
    # icles according to the stock dist.
    #join on activity growth
    passenger_change_dataframe = passenger_change_dataframe.merge(activity_growth, on=['Economy', 'Scenario', 'Date'], how='left')#one day if growth is determined by transport type, add transport type ot this grouping

    #calc
    passenger_change_dataframe['Transport_type_sum_of_activity_growth'] = (passenger_change_dataframe['Activity_growth'] * passenger_change_dataframe['Transport_type_sum_of_activity'])

    #Activity worth of extra stocks needed
    #if the growth in activity plus last years activity is greater than the activity worth of leftover stocks then this will be postiive
    passenger_change_dataframe['Transport_type_sum_of_activity_worth_of_extra_stocks_needed'] =  np.where(passenger_change_dataframe['Transport_type_sum_of_activity_worth_of_stocks_after_turnover_and_surplus_total'] - passenger_change_dataframe['Transport_type_sum_of_activity'] - passenger_change_dataframe['Transport_type_sum_of_activity_growth'] < 0, - (passenger_change_dataframe['Transport_type_sum_of_activity_worth_of_stocks_after_turnover_and_surplus_total'] - passenger_change_dataframe['Transport_type_sum_of_activity'] - passenger_change_dataframe['Transport_type_sum_of_activity_growth']) ,0)#note the use of miunus for calcualting it

    #Activity worth of extra stocks remaining
    #if the growth in activity plus last years activity is less than the activity worth of leftover stocks then this will be postiive
    passenger_change_dataframe['Transport_type_sum_of_activity_worth_of_extra_stocks_remaining'] =  np.where(passenger_change_dataframe['Transport_type_sum_of_activity_worth_of_stocks_after_turnover_and_surplus_total'] - passenger_change_dataframe['Transport_type_sum_of_activity'] - passenger_change_dataframe['Transport_type_sum_of_activity_growth'] > 0, passenger_change_dataframe['Transport_type_sum_of_activity_worth_of_stocks_after_turnover_and_surplus_total'] - passenger_change_dataframe['Transport_type_sum_of_activity'] - passenger_change_dataframe['Transport_type_sum_of_activity_growth'] ,0)

    #% of transport type stocks worth of activity not used (transport type)
    passenger_change_dataframe['Percent_of_transport_type_stocks_worth_of_activity_not_used'] = passenger_change_dataframe['Transport_type_sum_of_activity_worth_of_extra_stocks_remaining'] / passenger_change_dataframe['Transport_type_sum_of_activity_worth_of_stocks_after_turnover_and_surplus_total']
    #replace na's where there is 0/0 above
    passenger_change_dataframe['Percent_of_transport_type_stocks_worth_of_activity_not_used'] = passenger_change_dataframe['Percent_of_transport_type_stocks_worth_of_activity_not_used'].replace(np.nan, 0)

    #######################################################################
    #Now we will start working with inidivudal rows, for each vehicle type and drive combination.
    #######################################################################

    #Total surplus stocks worth of activity 
    passenger_change_dataframe['Total_surplus_stocks_worth_of_activity'] = passenger_change_dataframe['Activity_worth_of_stocks_after_turnover_and_surplus_total'] * passenger_change_dataframe['Percent_of_transport_type_stocks_worth_of_activity_not_used']

    #VEHICLE SALES SHARE(also referreed to as Sales/Stock Dist)
    #New Activity worth of sales will be satisfied by different vehicle type / drive type combinations, as specified by the Vehicle_sales_share (stock/sales dist). Each year there is a new sales share, created by the user before running the model
    #1. merge onto the main df the vehicle sales share that user has specified 
    #Also, if there is already a Vehicle_sales_share column from the prev year, remove it (we keep the vehicle sales shbare in the change dataframe because its an extra interesting output)
    if 'Vehicle_sales_share' in passenger_change_dataframe.columns:
        passenger_change_dataframe.drop(columns=['Vehicle_sales_share'], inplace=True)

    passenger_change_dataframe = passenger_change_dataframe.merge(Vehicle_sales_share, on=['Economy', 'Scenario', 'Drive', 'Transport Type', 'Vehicle Type', 'Date'], how='left')

    #CALCULATE STOCK SALES TO BE SATISFIED BY EACH VEHICLETYPE/DRIVETYPE COMBINATION USING THE NEW VEHICLE SALES SHARES
    #Note that if Activity worth of extra stocks needed can be 0, and if so then this will be 0 too.
    passenger_change_dataframe['Activity_worth_of_new_stock_sales'] = passenger_change_dataframe['Transport_type_sum_of_activity_worth_of_extra_stocks_needed'] * passenger_change_dataframe['Vehicle_sales_share']

    #CALCULATE NEW activity total of stocks being used as ACTIVITY
    passenger_change_dataframe['passenger_km'] = passenger_change_dataframe['Activity_worth_of_new_stock_sales'] + passenger_change_dataframe['Activity_worth_of_stocks_after_turnover_and_surplus_total'] - passenger_change_dataframe['Total_surplus_stocks_worth_of_activity']

    #CALCUALTE NEW TOTAL TRAVEL_KM PER VEHICLE/DRIVE-TYPE FROM NEW activity total of stocks being useD
    passenger_change_dataframe['Travel_km'] = passenger_change_dataframe['passenger_km'] / passenger_change_dataframe['Occupancy']

    #CALCUALTE NEW TOTAL TRAVEL_KM PER VEHICLE/DRIVE-TYPE FROM NEW STOCKS
    passenger_change_dataframe['Travel_km_of_new_stocks'] = passenger_change_dataframe['Activity_worth_of_new_stock_sales'] / passenger_change_dataframe['Occupancy']

    #CALCUALTE NEW TRAVEL_KM PER NEW VEHICLE/DRIVE-TYPE FROM NEW SALES WORTH OF ACTIVITY
    passenger_change_dataframe['Travel_km_of_surplus_stocks'] = passenger_change_dataframe['Total_surplus_stocks_worth_of_activity'] / passenger_change_dataframe['Occupancy']

    #CALCUALTE STOCKS BEING USED
    #Note that this is the new level of stocks in the economy
    passenger_change_dataframe['Stocks'] = passenger_change_dataframe['Travel_km'] / passenger_change_dataframe['Travel_km_per_stock']

    #CALCUALTE NEW STOCKS NEEDED AS STOCKS NEEDED TO SATISFY NEW SALES WORTH OF ACTIVITY
    passenger_change_dataframe['New_stocks_needed'] = passenger_change_dataframe['Travel_km_of_new_stocks'] / passenger_change_dataframe['Travel_km_per_stock']

    #CALCUALTE SURPLUS STOCKS
    #If we have too many stocks these go into surplus
    passenger_change_dataframe['Surplus_stocks'] = passenger_change_dataframe['Travel_km_of_surplus_stocks'] / passenger_change_dataframe['Travel_km_per_stock']

    #CALCULATE STOCKS IN USE REMAINING FROM PREVIOUS YEAR
    passenger_change_dataframe['Stocks_in_use_from_last_period'] = passenger_change_dataframe['Stocks'] - passenger_change_dataframe['New_stocks_needed']

    #SET EFFICIENCY OF SURPLUS STOCKS TO PREVIOUS YEARS AVG EFF LEVEL
    #Note that we assume that the efficiency of surplus stocks is the same as the efficiency of the stocks that were in use last year
    passenger_change_dataframe['Efficiency_of_surplus_stocks'] = passenger_change_dataframe['Efficiency']

    #APPLY EFFICIENCY GROWTH TO NEW VEHICLE EFFICIENCY
    #note that this will then be split into different fuel types when we appply the fuel mix varaible later on.
    #also note that new vehicle eff is independent of the current eff level of the eocnomys stocks. it could be much higher than them
    passenger_change_dataframe = passenger_change_dataframe.merge(New_vehicle_efficiency_growth, on=['Economy', 'Scenario', 'Transport Type', 'Drive', 'Vehicle Type', 'Date'], how='left')
    passenger_change_dataframe['New_vehicle_efficiency'] = passenger_change_dataframe['New_vehicle_efficiency'] * passenger_change_dataframe['New_vehicle_efficiency_growth'] 

    #CALCUALTE WEIGHTED AVERAGE VEHICLE EFFICIENCY
    #calcaulte weighted avg vehicle eff using the number of stocks left from last year times their avg eff, then the number of new stocks needed times their new eff. Then divide these by the number of stocks left from last year plus the number of new stocks needed. 
    #however if new stocks needed is <0, but there are still stocks remaining in the economy then efficiency will remain the same as original efficiency.
    #also have to note that this is the avg eff of stocks in use, this is in case there is a large amount of surplus stocks, so that the avg eff of the economy is not skewed by the efficiency of the surplus stocks, and instead new stocks efficiency has the right effect on the avg eff of the economy.
    passenger_change_dataframe['Efficiency_numerator'] = (passenger_change_dataframe['New_stocks_needed'] * passenger_change_dataframe['New_vehicle_efficiency'] + passenger_change_dataframe['Stocks_in_use_from_last_period'] * passenger_change_dataframe['Efficiency'])

    passenger_change_dataframe['Original_efficiency'] = passenger_change_dataframe['Efficiency']

    passenger_change_dataframe['Efficiency'] = np.where(passenger_change_dataframe['New_stocks_needed'] < 0, passenger_change_dataframe['Original_efficiency'], passenger_change_dataframe['Efficiency_numerator'] / passenger_change_dataframe['Stocks'])

    #if the denominator and numerator are 0 (which will occur if we dont have any stocks in this year [and therefore the last]), then efficiency ends up as nan, so we will set this to the efficiency value for new vehicles even though it doesnt really matter what it is set to, it just helps with aggregates.
    passenger_change_dataframe.loc[(passenger_change_dataframe['Stocks'] == 0), 'Efficiency'] = passenger_change_dataframe['New_vehicle_efficiency']

    #CALCUALTE NEW ENERGY CONSUMPTION. 
    #note that this is not split by fuel yet, it is just the total energy consumption for the vehicle/drive type.
    passenger_change_dataframe['Energy'] = passenger_change_dataframe['Travel_km'] / passenger_change_dataframe['Efficiency'] 

    #if numerator and denominator are 0, then energy ends up as nan, so we will set this to 0
    passenger_change_dataframe.loc[(passenger_change_dataframe['Travel_km'] == 0) & (passenger_change_dataframe['Efficiency'] == 0), 'Energy'] = 0




    #######################################################################

    #finalisation processes

    #######################################################################




    #join together freight and passenger km
    change_dataframe = pd.concat([passenger_change_dataframe, freight_change_dataframe])

    #Now start cleaning up the changes dataframe to create the dataframe for the new year.
    addition_to_main_dataframe = change_dataframe.copy() 
    
    addition_to_main_dataframe = addition_to_main_dataframe[['Economy', 'Scenario', 'Transport Type', 'Vehicle Type', 'Date', 'Drive', 'freight_tonne_km','passenger_km', 'Stocks', 'Efficiency', 'Energy', 'Surplus_stocks', 'Travel_km', 'Travel_km_per_stock', 'Vehicle_sales_share', 'Occupancy','Load', 'Turnover_rate', 'New_vehicle_efficiency']]
    
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

#%%
#######################################################################

#finalisation processes

#######################################################################

#this will be the name of the output file
new_output_file = 'intermediate_data/road_model/{}'.format(model_output_file_name)

#now, we will save the main dataframe to a csv file. if the computer is low ram, we will create the file from the already saved 10 year block interval files
if low_ram_computer == True:
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
    print('The main dataframe has been written to {}'.format(new_output_file))
else:
    print('The computer is not low ram, saving the main dataframe to a csv.')
    main_dataframe.to_csv(new_output_file, index=False)

if ANALYSE_CHANGE_DATAFRAME:
    #save dataframe
    change_dataframe_aggregation.to_csv('intermediate_data/road_model/change_dataframe_aggregation.csv', index=False)
#%%
#######################################################################
#######################################################################