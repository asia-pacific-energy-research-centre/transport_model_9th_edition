#%%

run_path("../config/config.py")#usae this to load libraries and set variables. Feel free to edit that file as you need

#%%
######################################################################################################
#laod clean user input from intermediate file
Switching_vehicle_sales_dist = pd.read_excel('../intermediate_data/clean_user_input.xlsx', sheet_name = 'Switching_vehicle_sales_dist')
Turnover_Rate_adjustments = pd.read_excel('../intermediate_data/clean_user_input.xlsx', sheet_name = 'Turnover_Rate_adjustments')
New_vehicle_efficiency_growth = pd.read_excel('../intermediate_data/clean_user_input.xlsx', sheet_name = 'New_vehicle_efficiency_growth')
OccupanceAndLoad_growth = pd.read_excel('../intermediate_data/clean_user_input.xlsx', sheet_name = 'OccupanceAndLoad_growth')

previous_year_main_dataframe1 = pd.read_csv('../input_data/TEMP_2017_previous_year_main_dataframe.csv')

activity_growth = pd.read_csv('../intermediate_data/activity_growth.csv')
#%%

######################################################################################################
previous_year_main_dataframe = previous_year_main_dataframe1.copy()
# NOW create main dataframe as empty previous year dataframe so it jsut contains column names.
main_dataframe = pd.DataFrame(columns=previous_year_main_dataframe.columns)
#%%

#need to do fuel mixes later
# detailed_fuels_dataframe = energy_base_year.merge(biofuel_blending_ratio, on=['Economy', 'Scenario', 'Drive', 'Transport Type', 'Vehicle Type', 'Year'], how='left')

#%%
#give option to run the process on a low RAM computer. If True then the loop will be split into 10 year blocks, saving each block in a csv, then starting again with an empty main datafrmae for the next 10 years block. If False then the loop will be run on all years without saving intermediate results.
low_ram_computer = True
if low_ram_computer:
    previous_10_year_block = BASE_YEAR
    low_ram_computer_files_list = []
    #remove files from main_dataframe_10_year_blocks for previous runs
    for file in glob.glob(os.path.join('../intermediate_data/main_dataframe_10_year_blocks/', '*.csv')):
        os.remove(file)


#%%

#START MAIN PROCESS
x = False

if x:
    for year in range(BASE_YEAR, END_YEAR+1):
        
        print('Up to year {}. The loop will run until year {}'.format(year, END_YEAR+1))

        #create dataframe as a messy notepad where we will adjust values and perform most calcualtions. 
        change_dataframe = previous_year_main_dataframe.copy()

        #change year in all rows to next year
        change_dataframe.Year = year

        #start cakcualting new vaulues

        #generally this will all work on teh grouping of economy, year, v-type, drive, transport type, and scenario. Only after all values have been calcualted will we create the energy use by fuel mix dataframe, which will replicate the values from this df
        #calcualte aggregate values that 

        #ACTIVITY GROWTH
        #we will apply activity growth to the sum of activity for each transport ype, then split that growth into different stocks using our stock distribtuion, that we will adjust too.
        #join on activity growth
        change_dataframe = change_dataframe.merge(activity_growth, on=['Economy', 'Scenario', 'Year'], how='left')
        #calcualte sum of last years activity by transport type
        activity_transport_type_sum = change_dataframe.copy()[['Economy', 'Scenario', 'Transport Type', 'Year', "Activity"]]
        activity_transport_type_sum = activity_transport_type_sum.groupby(['Economy', 'Scenario', 'Transport Type', 'Year']).sum()
        activity_transport_type_sum.rename(columns={"Activity": "Activity_transport_type_sum"}, inplace=True)
        change_dataframe = change_dataframe.merge(activity_transport_type_sum, on=['Economy', 'Scenario', 'Transport Type', 'Year'], how='left')
        #apply activity growth to activity 
        change_dataframe['Activity'] = change_dataframe['Activity_growth'] * change_dataframe['Activity']
        change_dataframe['Activity_transport_type_sum'] = change_dataframe['Activity_growth'] * change_dataframe['Activity_transport_type_sum']#theres an issue where this willnot be right if the actiivty growth rate is different vetween vehicle types of the same transport type. #so keep an eye on that

        #INCORPORATE SWITHCING TO THE STOCK SALES DISTRBUTION
        #1. apply adjsutments to sales sahre
        change_dataframe = change_dataframe.merge(Switching_vehicle_sales_dist, on=['Economy', 'Scenario', 'Drive', 'Transport Type', 'Vehicle Type', 'Year'], how='left')
        change_dataframe['Vehicle_sales_share_adjusted'] = change_dataframe['Vehicle_sales_share_normalised'] + change_dataframe['Sales_adjustment']
        #2. nromalise agaisnt the total for each transport type
        vehicle_sales_share_transport_type_sum = change_dataframe.groupby(['Economy', 'Scenario', 'Transport Type', 'Year']).sum()
        vehicle_sales_share_transport_type_sum.rename(columns={"Vehicle_sales_share_adjusted": "Vehicle_sales_share_sum"}, inplace=True)
        vehicle_sales_share_transport_type_sum = vehicle_sales_share_transport_type_sum.reset_index()[['Economy', 'Scenario', 'Transport Type', 'Year', 'Vehicle_sales_share_sum']]
        change_dataframe = change_dataframe.merge(vehicle_sales_share_transport_type_sum, on=['Economy', 'Scenario', 'Transport Type', 'Year'], how='left')
        change_dataframe['Vehicle_sales_share_normalised'] = change_dataframe['Vehicle_sales_share_adjusted'] * (1 / change_dataframe['Vehicle_sales_share_sum'])#TO DO CHECK HOW THIS HAS RESULTED. ANY ISSUES?

        #CALCULATE NEW STOCK SALES IN TERMS OF ACTIVITY USING THE NEW VEHICLE SALES SHARES
        #note how the vehicle sales shares arent applied to the stocks we already have. Ths is beccause we are calcaulting what proportion of the new activity growth will be absorbed by each stock type in the new year.
        change_dataframe['New_stock_sales_activity'] = change_dataframe['Activity_transport_type_sum'] * change_dataframe['Vehicle_sales_share_normalised']

        #APPLY OCCUPANCY GROWTH TO GROWTH AND THEN THIS TO ACTIVITY TO CALCULATE TRAVEL KM. 
        change_dataframe = change_dataframe.merge(OccupanceAndLoad_growth, on=['Economy', 'Vehicle Type', 'Transport Type', 'Year'], how='left')
        change_dataframe['Occupancy_or_load'] = change_dataframe['Occupancy_or_load'] + change_dataframe['Occupancy_or_load_adjustment']

        change_dataframe['Travel_km'] = change_dataframe['Activity'] / change_dataframe['Occupancy_or_load']

        #CALCUALTE STOCKS NEEDED TO SATISFY NEW ACTIVITY DEMAND AS TRAVEL KM / TRAVEL KM PER STOCK
        #Note that this is stocks needed to satisfy demand and tehrefore includes the current stock.
        change_dataframe['Stocks_needed'] = change_dataframe['Travel_km'] / change_dataframe['Travel_km_per_stock']
        #set Stocks as original Stocks
        change_dataframe['Stocks_original'] = change_dataframe['Stocks']
        #stocks needed is equivalent to stocks now
        change_dataframe['Stocks'] = change_dataframe['Stocks_needed']

        #CALCUALTE NEW TURNOVER RATE.
        # First merge turnover rate adjustment to the change dataframe 
        # #TO DO#wats going on with the turnover rate adjustment df?
        change_dataframe = change_dataframe.merge(Turnover_Rate_adjustments, on=['Economy', 'Scenario', 'Drive', 'Transport Type', 'Vehicle Type', 'Year'], how='left')
        #now apply adjustment to turnover rate
        change_dataframe['Turnover_rate'] = change_dataframe['Turnover_rate'] + change_dataframe['Turnover_rate_adjustment']
        #calcualte stock tyrnover as stocks from last year * turnover rate.
        change_dataframe['Stock_turnover'] = change_dataframe['Stocks_original'] * change_dataframe['Turnover_rate']

        #CALCUALTE STOCKS AFTER TURNOVER AND SUPLUS STOCKS
        # Note that this si the amount of preexisiting stocks, based on stocks from last year
        change_dataframe['Original_stocks_after_turnover_and_surplus'] = change_dataframe['Stocks_original'] - change_dataframe['Stock_turnover'] + change_dataframe['Surplus_stocks']

        #CALCUALTE NEW STOCKS NEEDED AS NEW STOCKS NEEDED MINUS STOCKS AFTER TURNOVER AND SURPLUS
        change_dataframe['New_stocks_needed'] = change_dataframe['Stocks_needed'] - change_dataframe['Original_stocks_after_turnover_and_surplus']
        
        #CALCUALTE SURPLUS STOCKS
        #If new stocks needed is negative then we actually have too many preexisint gstocks. in this case, we will assume that some stocks will sit in surplus. this is done by setting surplus stocks to either the new stocks needed or 0 if new stocks needed is positive. 
        change_dataframe['Surplus_stocks'] = np.where(change_dataframe['New_stocks_needed'] < 0, change_dataframe['New_stocks_needed'], 0)

        #APPLY EFFICIENCY GROWTH TO EFFICIENCY AND THEN THIS TO ACTIVITY TO CALCULATE ENERGY USE
        #note that this will then be split into different fuel types when we appply the fuel mix varaible later on.
        change_dataframe = change_dataframe.merge(New_vehicle_efficiency_growth, on=['Economy', 'Scenario', 'Transport Type', 'Drive', 'Vehicle Type', 'Year'], how='left')
        change_dataframe['New_vehicle_efficiency'] = change_dataframe['Efficiency'] * change_dataframe['New_vehicle_efficiency_growth']

        #CALCUALTE AVERAGE VEHICLE EFFICIENCY
        #calcaulte avg vehicle eff using teh number of stocks  left from last year times their avg eff rating, then the number of new stocks needed times the new eff rating. divided by the number of stocks left from last year plus the number of new stocks needed. 
        change_dataframe['Efficiency_numerator'] = (change_dataframe['New_stocks_needed'] * change_dataframe['New_vehicle_efficiency'] + change_dataframe['Original_stocks_after_turnover_and_surplus'] * change_dataframe['Efficiency'])

        change_dataframe['Original_efficiency'] = change_dataframe['Efficiency']

        change_dataframe['Efficiency'] = change_dataframe['Efficiency_numerator'] / change_dataframe['Stocks']

        #if the denominator and numerator are 0, then efficiency ends up as nan, so we will set this to the same values as last year
        change_dataframe.loc[(change_dataframe['Efficiency_numerator'] == 0) & (change_dataframe['Stocks'] == 0), 'Efficiency'] = change_dataframe['Original_efficiency']

        #######################################################################
        #FOR NOW thats all we need!

        #now start applying changes to be read for adding the df onto the main dataframe . we will remove uselsess cols and calcualte aggregate values (i think this is necessary)
        addition_to_main_dataframe = change_dataframe.copy()#cols to keep: 
        
        addition_to_main_dataframe = addition_to_main_dataframe[['Economy', 'Scenario', 'Transport Type', 'Vehicle Type', 'Year', 'Drive', 'Activity', 'Stocks', 'Efficiency', 'Energy_no_fuel', 'Activity_per_stock', 'Surplus_stocks', 'Travel_km', 'Travel_km_per_stock',  'Occupancy_or_load', 'Vehicle_sales_share_normalised','Turnover_rate']]#to do, how to incor[orate fuel mixing?]
        
        main_dataframe = pd.concat([main_dataframe, addition_to_main_dataframe])
        previous_year_main_dataframe = main_dataframe.copy()
        previous_year_main_dataframe = previous_year_main_dataframe[previous_year_main_dataframe['Year'] == year]

        #if we have a low ram computer then we will save the dataframe to a csv file at 10 year intervals. this is to save memory.
        if low_ram_computer == True:
            year_counter = year - BASE_YEAR
            if year_counter % 10 == 0:
                print('The year is at the end of a ten year block, in year {}, saving interemediate results to csv.'.format(year))
                low_ram_file_name = '../intermediate_data/main_dataframe_10_year_blocks/main_dataframe_years_{}_to_{}.csv'.format(previous_10_year_block, year)
                main_dataframe.to_csv(low_ram_file_name, index=False)
                low_ram_computer_files_list.append(low_ram_file_name)

                previous_10_year_block = year
                main_dataframe = pd.DataFrame(columns=main_dataframe.columns)#remove data we just saved from main datafrmae

            elif year == END_YEAR:
                print('The year is at the end of the simulation, saving intermediate results to csv.')
                low_ram_file_name = '../intermediate_data/main_dataframe_10_year_blocks/main_dataframe_years_{}_to_{}.csv'.format(previous_10_year_block, year)
                main_dataframe.to_csv(low_ram_file_name, index=False)
                low_ram_computer_files_list.append(low_ram_file_name)

    #%%
    new_output_file = '../output_data/road_model/main_dataframe_years_{}_to_{}_DATE{}.csv'.format(BASE_YEAR, END_YEAR, datetime.datetime.now().strftime("%Y%m%d_%H%M"))
    #now, we will save the main dataframe to a csv file. if the computer is low ram, we will create the file from the already saved 10 year block interval files
    if low_ram_computer == True:
        print('The computer is low ram, stitching together the main dataframe from the 10 year block files.')
        #WE HAVE A CHOICE HERE WHETHER WE WANT TO STITCH ALL THE FILES ONTO A DATAFRAME THEN SAVE TO A CSV, OR SEQUENTIALLY WRITE THEM TO A CSV. ONE OTHER ISSUE IS THAT IF WE WILL STILL AHVE ONE GIANT CSV AT THE END, PERHAPS ITS BEST TO SAVE THE DATA IN GROUPS DEPDNING ON THE DATATYPE OR ITS USEFULNESS?
        #FOR NOW LETS JUST WRITE THEM TO A CSV SEQUENTIALLY
        
        for file_i in low_ram_computer_files_list:
            print('Reading file {}'.format(file_i))
            low_ram_dataframe = pd.read_csv(file_i)
            #write to csv
            low_ram_dataframe.to_csv(new_output_file,mode='a', header=not os.path.exists(new_output_file),index=False)
        print('The main dataframe has been written to {}'.format(new_output_file))
    else:
        print('The computer is not low ram, saving the main dataframe to a csv.')
        main_dataframe.to_csv(new_output_file, index=False)


#%%











#%%
#issues to solve below. 
#some efficiency values are NA. it seems this is because they were missed in previous file
#get rid of unnamed x cols
#eff still na

#%%
year = 2017

print('Up to year {}. The loop will run until year {}'.format(year, END_YEAR+1))

#create dataframe as a messy notepad where we will adjust values and perform most calcualtions. 
change_dataframe = previous_year_main_dataframe1.copy()

#change year in all rows to next year
change_dataframe.Year = year

#start cakcualting new vaulues

#generally this will all work on teh grouping of economy, year, v-type, drive, transport type, and scenario. Only after all values have been calcualted will we create the energy use by fuel mix dataframe, which will replicate the values from this df
#calcualte aggregate values that 

#ACTIVITY GROWTH
#we will apply activity growth to the sum of activity for each transport ype, then split that growth into different stocks using our stock distribtuion, that we will adjust too.
#join on activity growth
change_dataframe = change_dataframe.merge(activity_growth, on=['Economy', 'Scenario', 'Year'], how='left')
#calcualte sum of last years activity by transport type
activity_transport_type_sum = change_dataframe.copy()[['Economy', 'Scenario', 'Transport Type', 'Year', "Activity"]]
activity_transport_type_sum = activity_transport_type_sum.groupby(['Economy', 'Scenario', 'Transport Type', 'Year']).sum()
activity_transport_type_sum.rename(columns={"Activity": "Activity_transport_type_sum"}, inplace=True)
change_dataframe = change_dataframe.merge(activity_transport_type_sum, on=['Economy', 'Scenario', 'Transport Type', 'Year'], how='left')
#apply activity growth to activity 
change_dataframe['Activity'] = change_dataframe['Activity_growth'] * change_dataframe['Activity']
change_dataframe['Activity_transport_type_sum'] = change_dataframe['Activity_growth'] * change_dataframe['Activity_transport_type_sum']#theres an issue where this willnot be right if the actiivty growth rate is different vetween vehicle types of the same transport type. #so keep an eye on that

#INCORPORATE SWITHCING TO THE STOCK SALES DISTRBUTION
#1. apply adjsutments to sales sahre
change_dataframe = change_dataframe.merge(Switching_vehicle_sales_dist, on=['Economy', 'Scenario', 'Drive', 'Transport Type', 'Vehicle Type', 'Year'], how='left')
change_dataframe['Vehicle_sales_share_adjusted'] = change_dataframe['Vehicle_sales_share_normalised'] + change_dataframe['Sales_adjustment']
#2. nromalise agaisnt the total for each transport type
vehicle_sales_share_transport_type_sum = change_dataframe.groupby(['Economy', 'Scenario', 'Transport Type', 'Year']).sum()
vehicle_sales_share_transport_type_sum.rename(columns={"Vehicle_sales_share_adjusted": "Vehicle_sales_share_sum"}, inplace=True)
vehicle_sales_share_transport_type_sum = vehicle_sales_share_transport_type_sum.reset_index()[['Economy', 'Scenario', 'Transport Type', 'Year', 'Vehicle_sales_share_sum']]
change_dataframe = change_dataframe.merge(vehicle_sales_share_transport_type_sum, on=['Economy', 'Scenario', 'Transport Type', 'Year'], how='left')
change_dataframe['Vehicle_sales_share_normalised'] = change_dataframe['Vehicle_sales_share_adjusted'] * (1 / change_dataframe['Vehicle_sales_share_sum'])#TO DO CHECK HOW THIS HAS RESULTED. ANY ISSUES?

#CALCULATE NEW STOCK SALES IN TERMS OF ACTIVITY USING THE NEW VEHICLE SALES SHARES
#note how the vehicle sales shares arent applied to the stocks we already have. Ths is beccause we are calcaulting what proportion of the new activity growth will be absorbed by each stock type in the new year.
change_dataframe['New_stock_sales_activity'] = change_dataframe['Activity_transport_type_sum'] * change_dataframe['Vehicle_sales_share_normalised']

#APPLY OCCUPANCY GROWTH TO GROWTH AND THEN THIS TO ACTIVITY TO CALCULATE TRAVEL KM. 
change_dataframe = change_dataframe.merge(OccupanceAndLoad_growth, on=['Economy', 'Vehicle Type', 'Transport Type', 'Year'], how='left')
change_dataframe['Occupancy_or_load'] = change_dataframe['Occupancy_or_load'] + change_dataframe['Occupancy_or_load_adjustment']

change_dataframe['Travel_km'] = change_dataframe['Activity'] / change_dataframe['Occupancy_or_load']
    
#check this is the same as the travel km per stock in the main dataframe, and activity per stock similarly
## TO DO WRITE CHECKS

# #CALCULATE Activity_per_stock 
# change_dataframe['Activity_per_stock'] = change_dataframe['Activity'] / change_dataframe['Stocks']

#CALCUALTE STOCKS NEEDED TO SATISFY NEW ACTIVITY DEMAND AS TRAVEL KM / TRAVEL KM PER STOCK
#Note that this is stocks needed to satisfy demand and tehrefore includes the current stock.
change_dataframe['Stocks_needed'] = change_dataframe['Travel_km'] / change_dataframe['Travel_km_per_stock']

#CALCUALTE STOCKS NEEDED TO SATISFY NEW ACTIVITY DEMAND AS TRAVEL KM / TRAVEL KM PER STOCK
#Note that this is stocks needed to satisfy demand and tehrefore includes the current stock.
#set Stocks as original Stocks
change_dataframe['Stocks_original'] = change_dataframe['Stocks']
#stocks needed is equivalent to stocks now
change_dataframe['Stocks'] = change_dataframe['Stocks_needed']

#CHECKING
#there is an issue where if activity is 0 then thefroe travel km is 0 and therefore stocks needed is calcualted as NAN. This is a problem because we want to be able to identify NAN's as errors, not as a result of the calcualtion. So to fix this we will set sotcks needed to 0 if the two values are 0. 
change_dataframe.loc[(change_dataframe['Travel_km'] == 0) & (change_dataframe['Travel_km_per_stock'] == 0), 'Stocks_needed'] = 0
#%%
#CALCUALTE NEW TURNOVER RATE.
# First merge turnover rate adjustment to the change dataframe 
# #TO DO#wats going on with the turnover rate adjustment df?
change_dataframe = change_dataframe.merge(Turnover_Rate_adjustments, on=['Economy', 'Scenario', 'Drive', 'Transport Type', 'Vehicle Type', 'Year'], how='left')
#now apply adjustment to turnover rate
change_dataframe['Turnover_rate'] = change_dataframe['Turnover_rate'] + change_dataframe['Turnover_rate_adjustment']
#calcualte stock tyrnover as stocks from last year * turnover rate.
change_dataframe['Stock_turnover'] = change_dataframe['Stocks_original'] * change_dataframe['Turnover_rate']

#CALCUALTE STOCKS AFTER TURNOVER AND SUPLUS STOCKS
# Note that this si the amount of preexisiting stocks, based on stocks from last year
change_dataframe['Original_stocks_after_turnover_and_surplus'] = change_dataframe['Stocks_original'] - change_dataframe['Stock_turnover'] + change_dataframe['Surplus_stocks']

#CALCUALTE NEW STOCKS NEEDED AS NEW STOCKS NEEDED MINUS STOCKS AFTER TURNOVER AND SURPLUS
change_dataframe['New_stocks_needed'] = change_dataframe['Stocks_needed'] - change_dataframe['Original_stocks_after_turnover_and_surplus']

#CALCUALTE SURPLUS STOCKS
#If new stocks needed is negative then we actually have too many preexisint gstocks. in this case, we will assume that some stocks will sit in surplus. this is done by setting surplus stocks to either the new stocks needed or 0 if new stocks needed is positive. 
change_dataframe['Surplus_stocks'] = np.where(change_dataframe['New_stocks_needed'] < 0, change_dataframe['New_stocks_needed'], 0)

#APPLY EFFICIENCY GROWTH TO EFFICIENCY AND THEN THIS TO ACTIVITY TO CALCULATE ENERGY USE
#note that this will then be split into different fuel types when we appply the fuel mix varaible later on.
change_dataframe = change_dataframe.merge(New_vehicle_efficiency_growth, on=['Economy', 'Scenario', 'Transport Type', 'Drive', 'Vehicle Type', 'Year'], how='left')
change_dataframe['New_vehicle_efficiency'] = change_dataframe['Efficiency'] * change_dataframe['New_vehicle_efficiency_growth']

#%%
#CALCUALTE AVERAGE VEHICLE EFFICIENCY
#calcaulte avg vehicle eff using teh number of stocks  left from last year times their avg eff rating, then the number of new stocks needed times the new eff rating. divided by the number of stocks left from last year plus the number of new stocks needed. 
#why does efficiency end up being nan in some acases?
change_dataframe['Efficiency_numerator'] = (change_dataframe['New_stocks_needed'] * change_dataframe['New_vehicle_efficiency'] + change_dataframe['Original_stocks_after_turnover_and_surplus'] * change_dataframe['Efficiency'])

change_dataframe['Original_efficiency'] = change_dataframe['Efficiency']

change_dataframe['Efficiency'] = change_dataframe['Efficiency_numerator'] / change_dataframe['Stocks']

#if the denominator and numerator are 0, then efficiency ends up as nan, so we will set this to the same values as last year
change_dataframe.loc[(change_dataframe['Efficiency_numerator'] == 0) & (change_dataframe['Stocks'] == 0), 'Efficiency'] = change_dataframe['Original_efficiency']
# %%
