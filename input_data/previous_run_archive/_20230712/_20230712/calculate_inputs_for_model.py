#the point of this file is to calculate extra variables that may be needed by the model, for example travel_km_per_stock or nromalised stock sales etc.
#these varaibles are essentially the same varaibles which will be calcualted in the model as these variables act as the base year variables. 

#please note that in the current state of the input data, this file has become qite messy with hte need to fill in missing data at this stage of the creation of the input data for the model. When we have good data we can make this more clean and suit the intended porupose to fthe file.
   

#%%
#set working directory as one folder back so that config works
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
from runpy import run_path
exec(open("config/config.py").read())#usae this to load libraries and set variables. Feel free to edit that file as you need
# FILE_DATE_ID = '_20230606'

import sys
sys.path.append("./workflow")
import utility_functions

def calculate_inputs_for_model(INDEX_COLS):
    #load data
    transport_dataset = pd.read_csv('intermediate_data/aggregated_model_inputs/{}_aggregated_model_data.csv'.format(FILE_DATE_ID))

    
    #remove uneeded columns
    unneeded_cols =['Unit','Dataset', 'Data_available', 'Frequency']
    transport_dataset.drop(unneeded_cols, axis=1, inplace=True)
    transport_dataset.drop_duplicates(inplace=True)
    #remove those cols from INDEX_COLS
    INDEX_COLS = [x for x in INDEX_COLS if x not in unneeded_cols]
    #set index cols
    # INDEX_COLS = ['Date', 'Economy', 'Vehicle Type', 'Medium','Transport Type', 'Drive', 'Scenario']

    
    #separate into road, non road asnd everything else
    road_model_input = transport_dataset.loc[transport_dataset['Medium'] == 'road']
    non_road_model_input = transport_dataset.loc[transport_dataset['Medium'].isin(['air', 'rail', 'ship'])]#TODO remove nonspec from the model or at least decide wehat to do with it
    growth_forecasts = transport_dataset.loc[~transport_dataset['Medium'].isin(['road', 'air', 'rail', 'ship'])]

    
    # Make wide so each unique category of the measure col is a column with the values in the value col as the values. This is how we will use the data from now on.
    #create INDEX_COLS with no measure
    INDEX_COLS_NO_MEASURE = INDEX_COLS.copy()
    INDEX_COLS_NO_MEASURE.remove('Measure')

    
    # #check for duplicates when subset by INDEX_COLS_NO_MEASURE
    # road_model_input[INDEX_COLS_NO_MEASURE].duplicated().sum()
    # x = non_road_model_input[non_road_model_input[INDEX_COLS].duplicated(keep=False)]
    
    road_model_input_wide = road_model_input.pivot(index=INDEX_COLS_NO_MEASURE, columns='Measure', values='Value').reset_index()
    non_road_model_input_wide = non_road_model_input.pivot(index=INDEX_COLS_NO_MEASURE, columns='Measure', values='Value').reset_index()
    growth_forecasts_wide = growth_forecasts.pivot(index=INDEX_COLS_NO_MEASURE, columns='Measure', values='Value').reset_index()
    ################################################################################

    #join on the Population, GDP and activity_growth cols from growth_forecasts to the otehrs
    road_model_input_wide = road_model_input_wide.merge(growth_forecasts_wide[['Date', 'Economy', 'Population', 'Gdp','Gdp_per_capita', 'Activity_growth']].drop_duplicates(), on=['Date', 'Economy'], how='left')
    non_road_model_input_wide = non_road_model_input_wide.merge(growth_forecasts_wide[['Date', 'Economy', 'Population', 'Gdp','Gdp_per_capita', 'Activity_growth']].drop_duplicates(), on=['Date', 'Economy'], how='left')

    
    #CALCUALTE TRAVEL KM 
    road_model_input_wide['Travel_km'] = road_model_input_wide['Activity']/road_model_input_wide['Occupancy_or_load']#TRAVEL KM is not provided by transport data system atm

    ################################################################################
    # 

    #set surplus stocks to 0 for now
    road_model_input_wide['Surplus_stocks'] = 0

    #calcualte Stocks_per_thousand_capita
    road_model_input_wide['Stocks_per_thousand_capita'] = (road_model_input_wide['Stocks']/road_model_input_wide['Population'])*1000000
    # road_model_input_wide.loc[(road_model_input_wide['Vehicle_sales_share'].isna()), 'Vehicle_sales_share'] = 0#TO DO THIS SHOULD BE FIXED EARLIER IN THE PROCESS
    ################################################################################

    
    #CREATE STOCKS FOR NON ROAD
    #this is an adjsutment to the road stocks data from 8th edition by setting stocks to 1 for all non road vehicles that have a value >0 for Energy
    non_road_model_input_wide.loc[(non_road_model_input_wide['Energy'] > 0), 'Stocks'] = 1
    non_road_model_input_wide.loc[(non_road_model_input_wide['Energy'] == 0), 'Stocks'] = 0


    
    test = False
    if test:
        #check that road stocks and activity match each other when usign  (change_dataframe['Activity']/( change_dataframe['Mileage'] * change_dataframe['Occupancy_or_load'])). 
        #if they arent then plot the average difference for each vehicle type and drve type. (ignore economy or scenario). THen later on we can decide how we fix it:
        test_road_model_input_wide = road_model_input_wide.copy()
        test_road_model_input_wide['Activity_check'] = test_road_model_input_wide['Mileage'] * test_road_model_input_wide['Occupancy_or_load'] * test_road_model_input_wide['Stocks']
        test_road_model_input_wide['Activity_check_diff'] = test_road_model_input_wide['Activity_check'] - test_road_model_input_wide['Activity']
        test_road_model_input_wide['Activity_check_diff_abs'] = test_road_model_input_wide['Activity_check_diff'].abs()
        #calcaulte average difference for each vehicle type and drive type and plot it
        test_road_model_input_wide['Activity_check_diff_abs_mean'] = test_road_model_input_wide['Activity_check_diff_abs'].groupby([test_road_model_input_wide['Vehicle Type'], test_road_model_input_wide['Drive']]).transform('mean')
        #drop duplicates
        test_road_model_input_wide = test_road_model_input_wide.drop_duplicates(subset=['Vehicle Type', 'Drive'])

        #plot using plotly
        import plotly.express as px
        fig = px.bar(test_road_model_input_wide, x="Vehicle Type", y="Activity_check_diff_abs_mean", color="Drive", barmode="group")
        fig.show()

        print('If the bar is postive then it means the activity is lower than the calculated activity from stocks, mileage and occupancy. Essentially Stocks are too high. ')
        #test if efficiency * Energy = activity
        test_road_model_input_wide['Energy_check'] = test_road_model_input_wide['Activity'] / test_road_model_input_wide['Efficiency']
        test_road_model_input_wide['Energy_check_diff'] = test_road_model_input_wide['Energy_check'] - test_road_model_input_wide['Energy']
        test_road_model_input_wide['Energy_check_diff_abs'] = test_road_model_input_wide['Energy_check_diff'].abs()
        #calcaulte average difference for each vehicle type and drive type and plot it
        test_road_model_input_wide['Energy_check_diff_abs_mean'] = test_road_model_input_wide['Energy_check_diff_abs'].groupby([test_road_model_input_wide['Vehicle Type'], test_road_model_input_wide['Drive']]).transform('mean')
        #drop duplicates
        test_road_model_input_wide = test_road_model_input_wide.drop_duplicates(subset=['Vehicle Type', 'Drive'])

        #plot using plotly
        import plotly.express as px
        fig = px.bar(test_road_model_input_wide, x="Vehicle Type", y="Energy_check_diff_abs_mean", color="Drive", barmode="group")
        fig.show()
        print('If the bar is postive then it means the energy is lower than the calculated energy from activity and efficiency. Essentially efficiency is too low or the activity is too high')
    RECALCUALTE_THESE =True#until we ahve more confidence in inputs this is the best way to do it
    RECLAUCLATE_TO_MATCH_ESTO = True
    if RECALCUALTE_THESE:
        if not RECLAUCLATE_TO_MATCH_ESTO:
            #RECALCUALTE ACTIVITY AND THEN ENERGY BASED ON THE VALUES FOR STOCKS
            road_model_input_wide['Activity'] = road_model_input_wide['Mileage'] * road_model_input_wide['Occupancy_or_load'] * road_model_input_wide['Stocks']
            road_model_input_wide['Travel_km'] = road_model_input_wide['Mileage'] * road_model_input_wide['Stocks']
            road_model_input_wide['Energy'] = road_model_input_wide['Travel_km'] / road_model_input_wide['Efficiency']
            #PLEASE NOTE THAT THIS NAY END UP RESULTING IN WACKY NUMBERS.ITS A QUICK FIX FOR NOW
        else:
            breakpoint()
            #pull in esto data and recalcualte activity and energy based on esto data. we will just get the sum of energy use for each medium and scale against the esto data:
            #find latest date for our energy data that was cleaned in transpoirt data system:
            # mean_energy_before = road_model_input_wide[(road_model_input_wide.Economy=='19_THA')&(road_model_input_wide.Date==2017)].groupby(['Medium']).mean().reset_index()
            date_id = utility_functions.get_latest_date_for_data_file('../transport_data_system/intermediate_data/EGEDA/', 'model_input_9th_cleaned')
            energy_use_esto = pd.read_csv(f'../transport_data_system/intermediate_data/EGEDA/model_input_9th_cleanedDATE{date_id}.csv')
            energy_use = energy_use_esto[energy_use_esto['Fuel_Type'] == '19_total']
            energy_use = energy_use[['Date','Economy','Medium', 'Value']]
            #reformat date to be in year only
            energy_use['Date'] = energy_use['Date'].apply(lambda x: x[:4])
            #make into int
            energy_use['Date'] = energy_use['Date'].astype(int)

            total_road_energy_use = road_model_input_wide[road_model_input_wide['Scenario'] == 'Reference'].groupby(['Date','Economy','Scenario', 'Medium']).sum().reset_index().copy()
            #JOIN TO ROAD_MODEL_INPUT_WIDE 
            energy_use_adjustment = pd.merge(energy_use, total_road_energy_use, how='right', left_on=['Date', 'Economy', 'Medium'], right_on=['Date', 'Economy', 'Medium'])
            #calculate adjustment factor as Value_esto / Energy (so that we can multiply the road_model_input_wide by this factor)
            energy_use_adjustment['adjustment_factor'] = energy_use_adjustment['Value'] / energy_use_adjustment['Energy']
            #repalce nas with 1s
            energy_use_adjustment['adjustment_factor'] = energy_use_adjustment['adjustment_factor'].fillna(1)
            #same for infs
            energy_use_adjustment['adjustment_factor'] = energy_use_adjustment['adjustment_factor'].replace([np.inf, -np.inf], 1)
            #drop columns we dont need then merge back to road_model_input_wide to do the adjustment
            energy_use_adjustment = energy_use_adjustment[['Date', 'Economy', 'Medium', 'adjustment_factor']]
            road_model_input_wide = pd.merge(road_model_input_wide, energy_use_adjustment, how='left', left_on=['Date', 'Economy', 'Medium'], right_on=['Date', 'Economy', 'Medium'])
            breakpoint()
            #adjust energy
            road_model_input_wide['Energy'] = road_model_input_wide['Energy'] * road_model_input_wide['adjustment_factor']
            #drop adjustment factor
            road_model_input_wide = road_model_input_wide.drop(columns=['adjustment_factor'])
            
            road_model_input_wide['Travel_km'] = road_model_input_wide['Energy'] * road_model_input_wide['Efficiency']
            road_model_input_wide['Activity'] = road_model_input_wide['Travel_km'] * road_model_input_wide['Occupancy_or_load']
            road_model_input_wide['Stocks'] = road_model_input_wide['Activity'] / (road_model_input_wide['Mileage'] * road_model_input_wide['Occupancy_or_load'])
            
            # mean_energy_after = road_model_input_wide[(road_model_input_wide.Economy=='19_THA')&(road_model_input_wide.Date==2017)].groupby(['Medium']).mean().reset_index()
    ##########
    #TEMPORARY UNTIL WE KNOW IT WORKS: (AVGERAGE AGE ADJSUTMENTS TO TURNOVER RATE)
    #insert average age column in road_model_input_wide. the average age will be set to 10 for all vehicles except those where drive is bev, phev_g, phev_d and fcev. Those will have an average age of 1
    #depening on the economy make it younger or older:
    old_vehicle_economies = ['19_THA']
    old_age = 10
    new_age = 5
    road_model_input_wide['Average_age'] = road_model_input_wide['Economy'].map(lambda x: old_age if x in old_vehicle_economies else new_age)
    road_model_input_wide.loc[(road_model_input_wide['Drive'].isin(['bev', 'phev_g', 'phev_d', 'fcev'])), 'Average_age'] = 1  
    
    #TEMPORARY UNTIL WE KNOW IT WORKS: (AVGERAGE AGE ADJSUTMENTS TO TURNOVER RATE)
    ##########
    # #join population and gdp per cpita to road model input
    # gdp_cap = growth_forecasts[['Date', 'Economy', 'Transport Type', 'Population', 'Gdp_per_capita']].drop_duplicates()

    # road_model_input_wide =  pd.merge(road_model_input_wide, gdp_cap, how='left', on=['Date', 'Transport Type', 'Economy'])

    breakpoint()
    #save previous_year_main_dataframe as a temporary dataframe we can load in when we want to run the process below.
    road_model_input_wide.to_csv('intermediate_data/model_inputs/road_model_input_wide.csv', index=False)
    non_road_model_input_wide.to_csv('intermediate_data/model_inputs/non_road_model_input_wide.csv', index=False)
    growth_forecasts_wide.to_csv('intermediate_data/model_inputs/growth_forecasts.csv', index=False)
    

    

#%%

# calculate_inputs_for_model(INDEX_COLS)
#%%