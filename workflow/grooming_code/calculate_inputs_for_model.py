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
sys.path.append("./workflow/plotting")
import utility_functions
import plot_user_input_data
import adjust_data_to_match_esto

def calculate_inputs_for_model(INDEX_COLS,RECALCULATE_ENERGY_USING_ESTO_AND_PREVIOUS_MODEL_RUN,ADVANCE_BASE_YEAR=False, adjust_data_to_match_esto_TESTING=False, TEST_ECONOMY='19_THA'):
    #load data
    transport_dataset = pd.read_csv('intermediate_data/aggregated_model_inputs/{}_aggregated_model_data.csv'.format(FILE_DATE_ID))

    # if PROJECT_TO_JUST_OUTLOOK_BASE_YEAR:#dont think i should do this because it doesnt matter to the output. better to jsut do it later so we the output suits whatever you need
    #     #filter so the data is from OUTLOOK_BASE_YEAR and back
    #     transport_dataset = transport_dataset[transport_dataset['Date'] <= OUTLOOK_BASE_YEAR]
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
        
        #PLEASE NOTE THAT THIS NAY END UP RESULTING IN WACKY NUMBERS.ITS A QUICK FIX FOR NOW
        # else:
        #     breakpoint()
        #     #pull in esto data and recalcualte activity and energy based on esto data. we will just get the sum of energy use for each medium and scale against the esto data:
        #     #find latest date for our energy data that was cleaned in transpoirt data system:
        #     mean_energy_before = road_model_input_wide[(road_model_input_wide.Economy=='19_THA')&(road_model_input_wide.Date==2017)].groupby(['Medium']).mean().reset_index()
        #     date_id = utility_functions.get_latest_date_for_data_file('../transport_data_system/intermediate_data/EGEDA/', 'model_input_9th_cleaned')
        #     energy_use_esto = pd.read_csv(f'../transport_data_system/intermediate_data/EGEDA/model_input_9th_cleanedDATE{date_id}.csv')
        #     energy_use = energy_use_esto[energy_use_esto['Fuel_Type'] == '19_total']
        #     energy_use = energy_use[['Date','Economy','Medium', 'Value']]
        #     #reformat date to be in year only
        #     energy_use['Date'] = energy_use['Date'].apply(lambda x: x[:4])
        #     #make into int
        #     energy_use['Date'] = energy_use['Date'].astype(int)

        #     total_road_energy_use = road_model_input_wide[road_model_input_wide['Scenario'] == 'Reference'].groupby(['Date','Economy','Scenario', 'Medium']).sum().reset_index().copy()
        #     #JOIN TO ROAD_MODEL_INPUT_WIDE 
        #     energy_use_adjustment = pd.merge(energy_use, total_road_energy_use, how='right', left_on=['Date', 'Economy', 'Medium'], right_on=['Date', 'Economy', 'Medium'])
        #     #calculate adjustment factor as Value_esto / Energy (so that we can multiply the road_model_input_wide by this factor)
        #     energy_use_adjustment['adjustment_factor'] = energy_use_adjustment['Value'] / energy_use_adjustment['Energy']
        #     #repalce nas with 1s
        #     energy_use_adjustment['adjustment_factor'] = energy_use_adjustment['adjustment_factor'].fillna(1)
        #     #same for infs
        #     energy_use_adjustment['adjustment_factor'] = energy_use_adjustment['adjustment_factor'].replace([np.inf, -np.inf], 1)
        #     #drop columns we dont need then merge back to road_model_input_wide to do the adjustment
        #     energy_use_adjustment = energy_use_adjustment[['Date', 'Economy', 'Medium', 'adjustment_factor']]
        #     road_model_input_wide = pd.merge(road_model_input_wide, energy_use_adjustment, how='left', left_on=['Date', 'Economy', 'Medium'], right_on=['Date', 'Economy', 'Medium'])
        #     breakpoint()
        #     #adjust energy
        #     road_model_input_wide['Energy'] = road_model_input_wide['Energy'] * road_model_input_wide['adjustment_factor']
        #     #drop adjustment factor
        #     road_model_input_wide = road_model_input_wide.drop(columns=['adjustment_factor'])
            
        #     road_model_input_wide['Travel_km'] = road_model_input_wide['Energy'] * road_model_input_wide['Efficiency']
        #     road_model_input_wide['Activity'] = road_model_input_wide['Travel_km'] * road_model_input_wide['Occupancy_or_load']
        #     road_model_input_wide['Stocks'] = road_model_input_wide['Activity'] / (road_model_input_wide['Mileage'] * road_model_input_wide['Occupancy_or_load'])
            
        #     mean_energy_after = road_model_input_wide[(road_model_input_wide.Economy=='19_THA')&(road_model_input_wide.Date==2017)].groupby(['Medium']).mean().reset_index()
    ##########
    #TEMPORARY UNTIL WE KNOW IT WORKS: (AVGERAGE AGE ADJSUTMENTS TO TURNOVER RATE)
    #insert average age column in road_model_input_wide. the average age will be set to 10 for all vehicles except those where drive is bev, phev_g, phev_d and fcev. Those will have an average age of 1
    # #depening on the economy make it younger or older:
    # old_vehicle_economies = ['19_THA']
    # old_age = 10
    # new_age = 5
    # road_model_input_wide['Average_age'] = road_model_input_wide['Economy'].map(lambda x: old_age if x in old_vehicle_economies else new_age)
    # road_model_input_wide.loc[(road_model_input_wide['Drive'].isin(['bev', 'phev_g', 'phev_d', 'fcev'])), 'Average_age'] = 1  
    
    # #do the same for non road but dont worry about new or old vehicle economies. set to 15 for all
    # non_road_model_input_wide['Average_age'] = 15
    
    
    #TEMPORARY UNTIL WE KNOW IT WORKS: (AVGERAGE AGE ADJSUTMENTS TO TURNOVER RATE)
    ##########
    # #join population and gdp per cpita to road model input
    # gdp_cap = growth_forecasts[['Date', 'Economy', 'Transport Type', 'Population', 'Gdp_per_capita']].drop_duplicates()

    # road_model_input_wide =  pd.merge(road_model_input_wide, gdp_cap, how='left', on=['Date', 'Transport Type', 'Economy'])
    
    DECREASE_GROWTH_FORECASTS = False
    if DECREASE_GROWTH_FORECASTS:
        PROPORTION_OF_GROWTH = 0.5
        #we want to decrease growth by a proportion fpr each year. So we will minus one from the growth and then times by PROPORTION_OF_GROWTH
        growth_forecasts_wide['Activity_growth'] = (growth_forecasts_wide['Activity_growth'] - 1) * PROPORTION_OF_GROWTH + 1
    

    if ADVANCE_BASE_YEAR:
        #use teh funcitons in adjust_data_to_match_esto.py to adjust the energy use to match the esto data in the MODEL_BASE_YEAR. To do this we will have needed to run the model up ot htat year already, and saved the results. We will then use the results to adjust the energy use to match the esto data. This is so that we can make sure that stocks and energy are about what youd expect, i think. 
        # breakpoint()
        new_road_model_input_wide, new_non_road_model_input_wide, supply_side_fuel_mixing_new = adjust_data_to_match_esto.adjust_data_to_match_esto(road_model_input_wide,non_road_model_input_wide,ADVANCE_BASE_YEAR=ADVANCE_BASE_YEAR, TESTING=adjust_data_to_match_esto_TESTING, TEST_ECONOMY=TEST_ECONOMY)
        #test if the output contains dates greater than the outlook base year. if it doesnt then the previous model run probably was only to the Outlook base year to savbe time. So we need to add data fpor this, using road_model_input_wide and non_road_model_input_wide:
        if (new_road_model_input_wide['Date'].max() == OUTLOOK_BASE_YEAR):
            if (new_non_road_model_input_wide['Date'].max() == OUTLOOK_BASE_YEAR):
                new_data_road = road_model_input_wide[road_model_input_wide['Date'] > OUTLOOK_BASE_YEAR].copy()
                new_data_non_road = non_road_model_input_wide[non_road_model_input_wide['Date'] > OUTLOOK_BASE_YEAR].copy()
                #concatenate
                new_road_model_input_wide = pd.concat([new_road_model_input_wide, new_data_road])
                new_non_road_model_input_wide = pd.concat([new_non_road_model_input_wide, new_data_non_road])
                
            else:
                raise ValueError('the non road model output has dates greater than the outlook base year but the road model output doesnt. This is not expected. Please check the data')
        breakpoint()
        supply_side_fuel_mixing_new.to_csv('intermediate_data\model_inputs\supply_side_fuel_mixing_COMPGEN_base_year_adv.csv', index=False)#TODO WHY IS THIS FOR LESS YEARS THAN THE OTHERS?
    
        #apply growth rates up to the outlook base year for all the growth rates that are in the model
        growth_columns_dict = {'New_vehicle_efficiency_growth':'New_vehicle_efficiency', 
        'Occupancy_or_load_growth':'Occupancy_or_load'}
        new_road_model_input_wide = apply_growth_up_to_outlook_base_year(new_road_model_input_wide,growth_columns_dict)
        growth_columns_dict = {'Non_road_intensity_improvement':'Intensity'}
        new_non_road_model_input_wide = apply_growth_up_to_outlook_base_year(new_non_road_model_input_wide,growth_columns_dict)
    
        #save previous_year_main_dataframe as a temporary dataframe we can load in when we want to run the process below.
        new_road_model_input_wide.to_csv('intermediate_data/model_inputs/road_model_input_wide_base_year_adv.csv', index=False)
        new_non_road_model_input_wide.to_csv('intermediate_data/model_inputs/non_road_model_input_wide_base_year_adv.csv', index=False)
        growth_forecasts_wide.to_csv('intermediate_data/model_inputs/growth_forecasts_base_year_adv.csv', index=False)
        
    else:
        
        road_model_input_wide.to_csv('intermediate_data/model_inputs/road_model_input_wide.csv', index=False)
        non_road_model_input_wide.to_csv('intermediate_data/model_inputs/non_road_model_input_wide.csv', index=False)
        growth_forecasts_wide.to_csv('intermediate_data/model_inputs/growth_forecasts.csv', index=False)
            

def apply_growth_up_to_outlook_base_year(road_model_input_wide,growth_columns_dict):
    #calcualte values from BASE YEAR up to OUTLOOK BASE YEAR just in case they are needed. that is, calcualte New Vehicle Efficienecy as the prodcut of the New Vehicle Efficienecy Growth of range(BASE_YEAR, OUTLOOK_BASE_YEAR-1) * the New Vehicle Efficienecy in the BASE_YEAR. Do this for all the other growth rates too.

    for growth, value in growth_columns_dict.items():
        
        new_values = road_model_input_wide[(road_model_input_wide['Date'] >= BASE_YEAR) & (road_model_input_wide['Date'] <= OUTLOOK_BASE_YEAR)].copy()
        base_year_values = road_model_input_wide[road_model_input_wide['Date'] == BASE_YEAR].copy()
        
        # replace any nans with 1
        new_values[growth] = new_values[growth].fillna(1)
        
        # Calculate cumulative product
        new_values[growth] = new_values.groupby(['Economy', 'Vehicle Type', 'Transport Type', 'Drive', 'Scenario'])[growth].transform('cumprod')
        #filter for latest Date only
        new_values = new_values[new_values['Date'] == OUTLOOK_BASE_YEAR]
        # Match base year value for each group and multiply with cumulative growth
        cum_growth = new_values[['Economy', 'Vehicle Type', 'Transport Type', 'Drive', 'Scenario', growth]].merge(base_year_values[['Economy', 'Vehicle Type', 'Transport Type', 'Drive', 'Scenario', value]], on=['Economy', 'Vehicle Type', 'Transport Type', 'Drive', 'Scenario'])
        if value == 'New_vehicle_efficiency':
            breakpoint()
        # Multiply cumulative growth with base year value
        cum_growth[value] = cum_growth[growth] * cum_growth[value]

        #make Date = OUTLOOK_BASE_YEAR as we want to save this value as the value used for the OUTLOOK_BASE_YEAR, so that in the first year forecasted (OUTLOOK_BASE_YEAR+1) we can use this value as the base year value
        cum_growth['Date'] = OUTLOOK_BASE_YEAR
        
        #merge and replace original value column with adjusted growth
        road_model_input_wide = road_model_input_wide.merge(cum_growth[['Economy', 'Vehicle Type', 'Transport Type', 'Drive', 'Scenario', 'Date', value]],on=['Economy', 'Vehicle Type', 'Transport Type', 'Drive', 'Scenario', 'Date'], how='left', suffixes=('', '_y'))

        # Replace original value column with adjusted growth
        road_model_input_wide[value] = road_model_input_wide[value+'_y'].fillna(road_model_input_wide[value])
        road_model_input_wide = road_model_input_wide.drop(columns=[value+'_y'])
    return road_model_input_wide

#%%

# # calculate_inputs_for_model(INDEX_COLS,RECALCULATE_ENERGY_USING_ESTO_AND_PREVIOUS_MODEL_RUN=False,ADVANCE_BASE_YEAR=False, adjust_data_to_match_esto_TESTING=False)
# calculate_inputs_for_model(INDEX_COLS,RECALCULATE_ENERGY_USING_ESTO_AND_PREVIOUS_MODEL_RUN=True,ADVANCE_BASE_YEAR=True)

# # calculate_inputs_for_model(INDEX_COLS,RECALCULATE_ENERGY_USING_ESTO_AND_PREVIOUS_MODEL_RUN=True,ADVANCE_BASE_YEAR=True,adjust_data_to_match_esto_TESTING=True,TEST_ECONOMY='20_USA')
#%%