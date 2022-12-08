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
#load user input data
road_user_input_and_growth_rates = pd.read_csv('intermediate_data/aggregated_model_inputs/road_user_input_and_growth_rates.csv')
#laod base year data
road_model_input = pd.read_csv('intermediate_data/model_inputs/road_model_input.csv')

#%%
#separate user inputs into different dataframes
Vehicle_sales_share = road_user_input_and_growth_rates[['Economy','Scenario', 'Vehicle Type', 'Transport Type', 'Year', 'Vehicle sales share']].drop_duplicates()
Occupancy_or_load_growth = road_user_input_and_growth_rates[['Economy','Scenario', 'Vehicle Type', 'Transport Type', 'Year', 'Occupancy_or_load_growth']].drop_duplicates()
Turnover_rate_growth = road_user_input_and_growth_rates[['Economy','Scenario', 'Vehicle Type', 'Transport Type', 'Drive', 'Year', 'Turnover_rate_growth']].drop_duplicates()
Activity_growth = road_user_input_and_growth_rates[['Economy','Scenario', 'Year', 'Activity_growth']].drop_duplicates()
New_vehicle_efficiency_growth = road_user_input_and_growth_rates[['Economy','Scenario', 'Vehicle Type', 'Transport Type', 'Drive', 'Year', 'New_vehicle_efficiency_growth']].drop_duplicates()

#%%
#create main dataframe as previous year dataframe, so that currently it only holds the base year's data. This will have each years data added to it at the end of each loop.
previous_year_main_dataframe = road_model_input.loc[road_model_input.Year == BASE_YEAR,:]
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
    change_dataframe.Year = year

    #start calcualting new values using the orignal values and adjustments as stated/forecasted by the user.

    #generally this will all work on the grouping of economy, year, v-type, drive, transport type, and scenario. There is a model simulation excel workbook in the documentation folder to more easily understand the operations here.
        
    #NOTE that there is still the fuel mixing operation that is not in this file of code. 

    #######################################################################

    #First do adjustments:

    #######################################################################

    #CALCUALTE NEW OCCUPANCY VALUE BY APPLYING THE OCCUPANCY GROWTH RATE
    change_dataframe = change_dataframe.merge(Occupancy_or_load_growth, on=['Economy','Scenario', 'Vehicle Type', 'Transport Type', 'Year'], how='left')
    change_dataframe['Occupancy_or_load'] = change_dataframe['Occupancy_or_load'] * change_dataframe['Occupancy_or_load_growth']

    #CALCUALTE NEW TURNOVER RATE AND THEN TURNOVER OF OLD STOCKS
    change_dataframe = change_dataframe.merge(Turnover_rate_growth, on=['Economy', 'Scenario', 'Drive', 'Transport Type', 'Vehicle Type', 'Year'], how='left')
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

    #CALCUALTE ACTIVITY WORTH OF STOCK TURNOVER AND SURPLUS
    change_dataframe['Activity_worth_of_stock_turnover_and_surplus'] = change_dataframe['Stock_turnover_and_surplus_total'] * change_dataframe['Travel_km_per_stock'] * change_dataframe['Occupancy_or_load']

    #Stocks after turnover and surplus total 
    change_dataframe['Stocks_after_turnover_and_surplus_total'] = change_dataframe['Stocks'] + change_dataframe['Stock_turnover_and_surplus_total']

    #Activity worth of stocks after turnover and surplus total
    change_dataframe['Activity_worth_of_stocks_after_turnover_and_surplus_total'] = change_dataframe['Stocks_after_turnover_and_surplus_total'] * change_dataframe['Travel_km_per_stock'] * change_dataframe['Occupancy_or_load']

    #Transport type sum of activity worth of stocks after turnover and surplus total
    change_dataframe['Transport_type_sum_of_activity_worth_of_stocks_after_turnover_and_surplus_total'] = change_dataframe.groupby(['Economy', 'Scenario', 'Transport Type', 'Year'])['Activity_worth_of_stocks_after_turnover_and_surplus_total'].transform('sum')

    #######################################################################

    #Now calcualte changes as a result of growth (and other things)
    #We will be working in terms of transport type sums for this section:

    #######################################################################

    #CALCULATE NEW ACTIVITY WORTH OF STOCK SALES
    #we will apply activity growth to the sum of activity for each transport type to find the activity worth of new sales from activity growth. Note that activity growth is assumed to be the same for all vehicle types of the same transport type (and probably for all transport types in early stages of this models development!)
    #We will also calcualte total turnover and surplus activity for the transport type to be satisfied by new stock sales, based on the new sales dist.

    #calcualte sum of activity by transport type
    change_dataframe['Transport_type_sum_of_activity'] = change_dataframe.groupby(['Economy', 'Scenario', 'Transport Type', 'Year'])['Activity'].transform('sum')

    #Now we will apply activity growth to original activity summed by transport type to find new activity to be satisfied by new vehicles according to the stock dist.
    #join on activity growth
    change_dataframe = change_dataframe.merge(Activity_growth, on=['Economy', 'Scenario', 'Year'], how='left')#one day if growth is determined by transport type, add transport type ot this grouping

    #calc
    change_dataframe['Transport_type_sum_of_activity_growth'] = (change_dataframe['Activity_growth'] * change_dataframe['Transport_type_sum_of_activity'])

    #Activity worth of extra stocks needed
    #if the growth in activity plus last years activity is greater than the activity worth of leftover stocks then this will be postiive
    change_dataframe['Transport_type_sum_of_activity_worth_of_extra_stocks_needed'] =  np.where(change_dataframe['Transport_type_sum_of_activity_worth_of_stocks_after_turnover_and_surplus_total'] - change_dataframe['Transport_type_sum_of_activity'] - change_dataframe['Transport_type_sum_of_activity_growth'] < 0, - (change_dataframe['Transport_type_sum_of_activity_worth_of_stocks_after_turnover_and_surplus_total'] - change_dataframe['Transport_type_sum_of_activity'] - change_dataframe['Transport_type_sum_of_activity_growth']) ,0)#note the use of miunus for calcualting it

    #Activity worth of extra stocks remaining
    #if the growth in activity plus last years activity is less than the activity worth of leftover stocks then this will be postiive
    change_dataframe['Transport_type_sum_of_activity_worth_of_extra_stocks_remaining'] =  np.where(change_dataframe['Transport_type_sum_of_activity_worth_of_stocks_after_turnover_and_surplus_total'] - change_dataframe['Transport_type_sum_of_activity'] - change_dataframe['Transport_type_sum_of_activity_growth'] > 0, change_dataframe['Transport_type_sum_of_activity_worth_of_stocks_after_turnover_and_surplus_total'] - change_dataframe['Transport_type_sum_of_activity'] - change_dataframe['Transport_type_sum_of_activity_growth'] ,0)

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
    #since there is already a Vehicle_sales_share column from the prev year, remove it (we keep the vehicle sales shbare in the change dataframe because its an extra interesting output)
    change_dataframe.drop(columns=['Vehicle_sales_share'], inplace=True)
    change_dataframe = change_dataframe.merge(Vehicle_sales_share, on=['Economy', 'Scenario', 'Drive', 'Transport Type', 'Vehicle Type', 'Year'], how='left')

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
    change_dataframe['Stocks'] = change_dataframe['Travel_km'] / change_dataframe['Travel_km_per_stock']

    #CALCUALTE NEW STOCKS NEEDED AS STOCKS NEEDED TO SATISFY NEW SALES WORTH OF ACTIVITY
    change_dataframe['New_stocks_needed'] = change_dataframe['Travel_km_of_new_stocks'] / change_dataframe['Travel_km_per_stock']

    #CALCUALTE SURPLUS STOCKS
    #If we have too many stocks these go into surplus
    change_dataframe['Surplus_stocks'] = change_dataframe['Travel_km_of_surplus_stocks'] / change_dataframe['Travel_km_per_stock']

    #CALCULATE STOCKS IN USE REMAINING FROM PREVIOUS YEAR
    change_dataframe['Stocks_in_use_from_last_period'] = change_dataframe['Stocks'] - change_dataframe['New_stocks_needed']

    #SET EFFICIENCY OF SURPLUS STOCKS TO PREVIOUS YEARS AVG EFF LEVEL
    #Note that we assume that the efficiency of surplus stocks is the same as the efficiency of the stocks that were in use last year
    change_dataframe['Efficiency_of_surplus_stocks'] = change_dataframe['Efficiency']

    #APPLY EFFICIENCY GROWTH TO NEW VEHICLE EFFICIENCY
    #note that this will then be split into different fuel types when we appply the fuel mix varaible later on.
    #also note that new vehicle eff is independent of the current eff level of the eocnomys stocks. it could be much higher than them
    change_dataframe = change_dataframe.merge(New_vehicle_efficiency_growth, on=['Economy', 'Scenario', 'Transport Type', 'Drive', 'Vehicle Type', 'Year'], how='left')
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

    #Now start cleaning up the changes dataframe to create the dataframe for the new year.
    addition_to_main_dataframe = change_dataframe.copy() 
    
    addition_to_main_dataframe = addition_to_main_dataframe[['Economy', 'Scenario', 'Transport Type', 'Vehicle Type', 'Year', 'Drive', 'Activity', 'Stocks', 'Efficiency', 'Energy', 'Surplus_stocks', 'Travel_km', 'Travel_km_per_stock', 'Vehicle_sales_share', 'Occupancy_or_load', 'Turnover_rate', 'New_vehicle_efficiency']]
    
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
