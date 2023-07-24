#the point of this file is to calculate extra variables that may be needed by the model, for example travel_km_per_stock or nromalised stock sales etc.
#these varaibles are essentially the same varaibles which will be calcualted in the model as these variables act as the base year variables. 

#please note that in the current state of the input data, this file has become qite messy with hte need to fill in missing data at this stage of the creation of the input data for the model. When we have good data we can make this more clean and suit the intended porupose to fthe file.
   

#%%
###IMPORT GLOBAL VARIABLES FROM config.py
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
import sys
sys.path.append("./config")
import config
####Use this to load libraries and set variables. Feel free to edit that file as you need.
sys.path.append("./workflow")
sys.path.append("./workflow/plotting_functions")
import plot_user_input_data
import adjust_data_to_match_esto

def calculate_inputs_for_model(ADVANCE_BASE_YEAR=False, adjust_data_to_match_esto_TESTING=False, TEST_ECONOMY='19_THA'):
    
    road_model_input_wide = pd.read_csv('intermediate_data/model_inputs/{}/road_model_input_wide.csv'.format(config.FILE_DATE_ID))
    non_road_model_input_wide = pd.read_csv('intermediate_data/model_inputs/{}/non_road_model_input_wide.csv'.format(config.FILE_DATE_ID))
    
    #CALCUALTE TRAVEL KM 
    road_model_input_wide['Travel_km'] = road_model_input_wide['Activity']/road_model_input_wide['Occupancy_or_load']#TRAVEL KM is not provided by transport data system atm

    ########################################################################### 

    #set surplus stocks to 0 for now
    road_model_input_wide['Surplus_stocks'] = 0

    #calcualte Stocks_per_thousand_capita
    road_model_input_wide['Stocks_per_thousand_capita'] = (road_model_input_wide['Stocks']/road_model_input_wide['Population'])*1000000
    
    #create emptry Turnvoer rate column in both:
    road_model_input_wide['Turnover_rate'] = np.nan
    non_road_model_input_wide['Turnover_rate'] = np.nan
    
    #TEMP, set Activity_per_Stock to 1
    non_road_model_input_wide['Activity_per_Stock'] = 1
    # non_road_model_input_wide['Turnover_rate'] = 0.03
    #CREATE STOCKS FOR NON ROAD
    #this is an adjsutment to the road stocks data from 8th edition by setting stocks to 1 for all non road vehicles that have a value >0 for Energy
    non_road_model_input_wide['Stocks'] = non_road_model_input_wide['Activity'] / non_road_model_input_wide['Activity_per_Stock']

    #In Non road. It seems that intensity is getting set to 0 where there isnt enough data. probably in the data system. for now, lets set 0's to na, then average out the intensity for each drive type and set the na's to that average:
    non_road_model_input_wide.loc[(non_road_model_input_wide['Intensity']==0), 'Intensity'] = np.nan
    non_road_model_input_wide['Intensity'] = non_road_model_input_wide.groupby(['Date', 'Economy', 'Scenario', 'Transport Type', 'Drive'])['Intensity'].transform(lambda x: x.fillna(x.mean()))
    #quickly plot the average intensity across all economies and scenarios to see if it looks ok:
    plotting = True
    if plotting:
        plot_user_input_data.plot_average_intensity(non_road_model_input_wide)
    ############################################################################
    # RECALCUALTE_THESE =True#until we ahve more confidence in inputs this is the best way to do it
    # RECLAUCLATE_TO_MATCH_ESTO = False
    # if RECALCUALTE_THESE:
    #     if not RECLAUCLATE_TO_MATCH_ESTO:
    if not ADVANCE_BASE_YEAR:
        #RECALCUALTE ACTIVITY AND THEN ENERGY BASED ON THE VALUES FOR STOCKS
        road_model_input_wide['Activity'] = road_model_input_wide['Mileage'] * road_model_input_wide['Occupancy_or_load'] * road_model_input_wide['Stocks']
        road_model_input_wide['Travel_km'] = road_model_input_wide['Mileage'] * road_model_input_wide['Stocks']
        road_model_input_wide['Energy'] = road_model_input_wide['Travel_km'] / road_model_input_wide['Efficiency']
        
        #anbd i guess do the same thing for non road, except, since we are most confident in energy here, calcualte everything based off enerrgy and intensity:
        non_road_model_input_wide['Activity'] = non_road_model_input_wide['Energy'] * non_road_model_input_wide['Intensity']
        non_road_model_input_wide['Stocks'] = non_road_model_input_wide['Activity'] / non_road_model_input_wide['Activity_per_Stock']
        
    DECREASE_GROWTH_FORECASTS = False
    if DECREASE_GROWTH_FORECASTS:
        PROPORTION_OF_GROWTH = 0.5
        #we want to decrease growth by a proportion fpr each year. So we will minus one from the growth and then times by PROPORTION_OF_GROWTH
        growth_forecasts_wide['Activity_growth'] = (growth_forecasts_wide['Activity_growth'] - 1) * PROPORTION_OF_GROWTH + 1
    

    if ADVANCE_BASE_YEAR:
        #use teh funcitons in adjust_data_to_match_esto.py to adjust the energy use to match the esto data in the MODEL_BASE_YEAR. To do this we will have needed to run the model up ot htat year already, and saved the results. We will then use the results to adjust the energy use to match the esto data. This is so that we can make sure that stocks and energy are about what youd expect, i think. 
        # breakpoint()
        new_road_model_input_wide, new_non_road_model_input_wide, supply_side_fuel_mixing_new = adjust_data_to_match_esto.adjust_data_to_match_esto(road_model_input_wide,non_road_model_input_wide,ADVANCE_BASE_YEAR=ADVANCE_BASE_YEAR, TESTING=adjust_data_to_match_esto_TESTING, TEST_ECONOMY=TEST_ECONOMY)
        
        supply_side_fuel_mixing_new.to_csv('intermediate_data/model_inputs/{}/supply_side_fuel_mixing.csv'.format(config.FILE_DATE_ID), index=False)
    
        #save previous_year_main_dataframe as a temporary dataframe we can load in when we want to run the process below.
        new_road_model_input_wide.to_csv('intermediate_data/model_inputs/road_model_input_wide_BASE_YEAR_adv.csv', index=False)
        new_non_road_model_input_wide.to_csv('intermediate_data/model_inputs/non_road_model_input_wide_BASE_YEAR_adv.csv', index=False)
        growth_forecasts_wide.to_csv('intermediate_data/model_inputs/growth_forecasts_BASE_YEAR_adv.csv', index=False)
        
    else:
        
        road_model_input_wide.to_csv('intermediate_data/model_inputs/road_model_input_wide.csv', index=False)
        non_road_model_input_wide.to_csv('intermediate_data/model_inputs/non_road_model_input_wide.csv', index=False)
        growth_forecasts_wide.to_csv('intermediate_data/model_inputs/growth_forecasts.csv', index=False)
            

#%%

#%%