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

#%%
#load data
transport_dataset = pd.read_csv('intermediate_data/aggregated_model_inputs/{}_aggregated_model_data.csv'.format(FILE_DATE_ID))

#%%
#remove uneeded columns
transport_dataset.drop(['Unit','Final_dataset_selection_method','Dataset', 'Data_available'], axis=1, inplace=True)
INDEX_COLS.remove('Unit')
#set index cols
# INDEX_COLS = ['Date', 'Economy', 'Vehicle Type', 'Medium','Transport Type', 'Drive', 'Scenario']

#%%
#separate into road and non road
road_model_input = transport_dataset.loc[transport_dataset['Medium'] == 'road']
non_road_model_input = transport_dataset.loc[transport_dataset['Medium'].isin(['air', 'nonspecified', 'rail', 'ship'])]#TODO remove nonspec from the model or at least decide wehat to do with it
#%%
# Make wide so each unique category of the measure col is a column with the values in the value col as the values. This is how we will use the data from now on.
#create INDEX_COLS with no measure
INDEX_COLS_NO_MEASURE = INDEX_COLS.copy()
INDEX_COLS_NO_MEASURE.remove('Measure')
#%%
road_model_input = road_model_input.pivot(index=INDEX_COLS_NO_MEASURE, columns='Measure', values='Value').reset_index()
non_road_model_input = non_road_model_input.pivot(index=INDEX_COLS_NO_MEASURE, columns='Measure', values='Value').reset_index()

################################################################################
#%%
#CALCUALTE TRAVEL KM as activity/occupancy or load depending on if transport type is passenger or freight
road_model_input['Travel_km'] = np.nan
road_model_input.loc[road_model_input['Transport Type'] == 'passenger', 'Travel_km'] = road_model_input['passenger_km']/road_model_input['Occupancy']
road_model_input.loc[road_model_input['Transport Type'] == 'freight', 'Travel_km'] = road_model_input['freight_tonne_km']/road_model_input['Load']


#%%

#CALCUALTE TRAVEL KM PER STOCK
#After much deliberation it was arrived at that travel km per stock should be calculated as the average travel km per stock for each vehicle type. This was to avoid the effect of having weird ratios created by very small numbers. By averaging it also makes it easier to keep track of this variable.
average_travel_km_per_stock_of_vehicle_type = road_model_input[['Economy', 'Scenario', 'Transport Type', 'Vehicle Type', 'Date', 'Travel_km', 'Stocks']]
average_travel_km_per_stock_of_vehicle_type = average_travel_km_per_stock_of_vehicle_type.dropna().groupby(['Economy', 'Scenario', 'Transport Type', 'Vehicle Type', 'Date']).sum().reset_index()

average_travel_km_per_stock_of_vehicle_type['Travel_km_per_stock'] = average_travel_km_per_stock_of_vehicle_type['Travel_km']/average_travel_km_per_stock_of_vehicle_type['Stocks']


average_travel_km_per_stock_of_vehicle_type.drop(['Travel_km', 'Stocks'], axis=1, inplace=True)

#there are still some values where travel km per stock are na or 0 because trvlkm is 0 and in some cases stocks are also 0. 
#so where travelkm is 0, we will set travel km per stock to the average of the vehicle type/transport type fir that year
#first set all 0's to na
average_travel_km_per_stock_of_vehicle_type.loc[average_travel_km_per_stock_of_vehicle_type['Travel_km_per_stock']==0, 'Travel_km_per_stock'] = np.nan
#then replace nas
average_travel_km_per_stock_of_vehicle_type['Travel_km_per_stock'] = average_travel_km_per_stock_of_vehicle_type['Travel_km_per_stock'].fillna(average_travel_km_per_stock_of_vehicle_type.groupby(['Transport Type', 'Vehicle Type', 'Date'])['Travel_km_per_stock'].transform('mean'))

#now we have a travel km per stock for each vehicle type, we can merge this back into the original data
#%%

#'REPLACE STOCKS FOR FREIGHT LIGHT TRUCKS USING TRAVEL KM PER STOCK OF PASSENGER LIGHT TRUCKS'
#looks lik the stats for travel km per stock for lt freight is very wack, with its standard deviation being even higher than its mean. Generally, when comparing the data to NZ's ofifical stats the travel km per stock is too high and should be just a bit more than it is for LV's and lt's in passenger.
#as a temproary fix we will set the travel km per stock for lt freight to be the mean of lt passenger, for simplicity. Then cahnge the stocks using this vaue too
#note that this conclusion depends on the occupancy and load data being accurate. For now we will assume it is but it is worth looking into
#note that it is much easier to do this fix now than earlier because we have the travel km per stock for each vehicle type prepared
#only do this if we are using the 8th edition data, which we could tell by using the 'dataset' column
if EIGHTH_EDITION_DATA == True:
    lt_freight_fill = average_travel_km_per_stock_of_vehicle_type.loc[(average_travel_km_per_stock_of_vehicle_type['Vehicle Type'] == 'lt') &  (average_travel_km_per_stock_of_vehicle_type['Transport Type'] == 'passenger')]

    lt_freight_fill['Transport Type'] = 'freight'

    average_travel_km_per_stock_of_vehicle_type = average_travel_km_per_stock_of_vehicle_type.loc[~((average_travel_km_per_stock_of_vehicle_type['Vehicle Type'] == 'lt') & ( average_travel_km_per_stock_of_vehicle_type['Transport Type'] == 'freight'))]

    average_travel_km_per_stock_of_vehicle_type = pd.concat([average_travel_km_per_stock_of_vehicle_type, lt_freight_fill])

else: 
    print('lt freight travel km per stock not replaced with lt passenger travel km per stock because EIGHTH_EDITION_DATA = False in config.py... Please check that this is appropriate')

#%%
#AND MERGE BACK INTO THE ORIGINAL DATA
road_model_input = road_model_input.merge(average_travel_km_per_stock_of_vehicle_type, on=['Economy', 'Scenario', 'Transport Type', 'Vehicle Type', 'Date'], how='left')

road_model_input['Stocks'] = road_model_input['Travel_km'] / road_model_input['Travel_km_per_stock']#calculate stocks again?

# #quick analysis. lets average the travel km per stock for each vehicle type and see what the average is.
# road_model_input[['Travel_km_per_stock', 'Transport Type', 'Vehicle Type']].groupby(['Transport Type', 'Vehicle Type']).agg([np.mean, np.std, np.var, np.median]).reset_index()
################################################################################
#%%
#currently calculating efficiency as travel km / energy use buyt it may be good to have actual efficiency values to scale this properly (i.e. not having efficiency values means that we may be getting this wrong because of issues with the underlying data)
road_model_input['Efficiency'] = road_model_input['Travel_km']/road_model_input['Energy']
#note that there are na's created by 0/0 here. for those we fix them by using the average efficiency of the vehicle type in the prcoess below. If the process below is replaced, need to make sure to fix the na's in new process

#there is a problem where the efficiency is very large for some vehicle types. This seems to occur for cases where there is very small use of that vehicle type. This is because the efficiency is calculated as travel km/energy use, and if there is very little energy use and the travel km is a little incrorect in absolute terms, then the efficiency will be incorrect by the same magnitude, which can be large proportionally, and since it is a ratio, it will be seem in absolute terms when yuou compare it to otehr ratios
#FOR NOW, where the efficiency value is obv wrong we will set the efficiency to be the mean of the efficiency for that vehicle type, we will then set the energy use to be the travel km divided by this efficiency. I think it will be okay to do this like this, the only consideraton is where we are presenting base year and input data by fuel type, since that data is already split into fuel type and wont be affected by this, but that seems unliekly.

#we will seaprarte the incorrect data and replace it with the mean of the correct data

rows_to_fix = road_model_input.loc[(road_model_input['Efficiency'] > 10) | (road_model_input['Efficiency'].isna())]
rows_to_fix.drop(['Efficiency'], axis=1, inplace=True)

road_model_input_correct_eff = road_model_input.loc[road_model_input['Efficiency'] <= 10]

if len(road_model_input_correct_eff) == 0:
    print('WARNING: no efficiency values are correct, check that this is correct')

else:
    #recalcualte eff for incorrect rows using avgs from correct rows
    new_values_eff = road_model_input_correct_eff.groupby(['Scenario', 'Transport Type', 'Vehicle Type', 'Date', 'Drive']).sum().reset_index()
    new_values_eff['Efficiency'] = new_values_eff['Travel_km']/new_values_eff['Energy']
    new_values_eff = new_values_eff[['Scenario', 'Transport Type', 'Vehicle Type', 'Date', 'Drive', 'Efficiency']]

    if EIGHTH_EDITION_DATA == True:
        #FIX FOR FCEV HT's:
        #avg diff between EV and FCEV in the same vehicle type
        #first filter for only fcev and bev in non ht vehicle types
        avg_diff = new_values_eff.loc[(new_values_eff['Drive'].isin(['bev', 'fcev'])) & (new_values_eff['Vehicle Type'] != 'ht')]
        #then pivot so we ahve an eff col for each drive type.
        avg_diff = avg_diff.pivot(index=['Scenario', 'Transport Type', 'Vehicle Type', 'Date'], columns='Drive', values='Efficiency').reset_index()
        #remvove any na's (eg 2w have no value for fcev)
        avg_diff.dropna(inplace=True)
        #then divide the two and avg to create a singular value for the difference between the two
        avg_diff['diff'] = avg_diff['bev']/avg_diff['fcev']
        avg_diff = avg_diff['diff'].mean()
        #then divide the bev value for ht's by this value to get an est of fcev value for ht's.
        fcev_ht = new_values_eff.loc[(new_values_eff['Drive'] == 'bev') & (new_values_eff['Vehicle Type'] == 'ht')]
        fcev_ht['Drive'] = 'fcev'
        fcev_ht['Efficiency'] = fcev_ht['Efficiency'] / avg_diff
        #then concat this onto the new values eff df
        new_values_eff = pd.concat([new_values_eff, fcev_ht])
        #done

    #attach new values for missing/incorrect eff values to rows to fix
    rows_to_fix = rows_to_fix.merge(new_values_eff, on=['Scenario', 'Transport Type', 'Vehicle Type', 'Date', 'Drive'], how='left')

    #concatenate with correct rows in orgiinal df
    road_model_input = pd.concat([road_model_input, rows_to_fix])

    #now recalcualte travel km and activity for these rows:
    road_model_input['Travel_km'] = road_model_input['Energy'] * road_model_input['Efficiency']
    #where transport type is freight, activity is travel km *  load, where transport type is passenger activity is travel km * occupancy
    road_model_input.loc[road_model_input['Transport Type'] == 'passenger', 'passenger_km'] = road_model_input['Travel_km'] * road_model_input['Occupancy']
    road_model_input.loc[road_model_input['Transport Type'] == 'freight', 'freight_tonne_km'] = road_model_input['Travel_km'] * road_model_input['Load']
    # road_model_input['Activity'] = road_model_input['Travel_km'] * road_model_input['Occupancy_or_load']
#%%
#NON ROAD DATA:
#also calc non road eff here, but this is just a placeholder for now, as it seems it would be better to also calcualte non road eff as efficiency = travel km / energy not activity /energy

#where transport type is freight, activity is freight_tonne_km, where transport type is passenger activity is  passenger_km
non_road_model_input.loc[non_road_model_input['Transport Type'] == 'passenger', 'Efficiency'] = non_road_model_input['passenger_km']/non_road_model_input['Energy']
non_road_model_input.loc[non_road_model_input['Transport Type'] == 'freight', 'Efficiency'] = non_road_model_input['freight_tonne_km']/non_road_model_input['Energy']

#if activity and energy are 0 then we will get na. In this case we will replace the efficiency with the average efficiency of the whole of apec
non_road_model_input_avg_eff = non_road_model_input.groupby(['Medium', 'Transport Type', 'Vehicle Type', 'Drive', 'Date','Scenario']).sum().reset_index()

#where transport type is freight, activity is freight_tonne_km, where transport type is passenger activity is  passenger_km
non_road_model_input_avg_eff.loc[non_road_model_input_avg_eff['Transport Type'] == 'passenger', 'Efficiency_avg'] = non_road_model_input_avg_eff['passenger_km']/non_road_model_input_avg_eff['Energy']
non_road_model_input_avg_eff.loc[non_road_model_input_avg_eff['Transport Type'] == 'freight', 'Efficiency_avg'] = non_road_model_input_avg_eff['freight_tonne_km']/non_road_model_input_avg_eff['Energy']


non_road_model_input = non_road_model_input.merge(non_road_model_input_avg_eff[['Medium', 'Transport Type', 'Vehicle Type', 'Drive', 'Date','Scenario', 'Efficiency_avg']], on=['Medium', 'Transport Type', 'Vehicle Type', 'Drive', 'Date','Scenario'], how='left')
non_road_model_input.loc[non_road_model_input['Efficiency'].isnull(), 'Efficiency'] = non_road_model_input['Efficiency_avg']
non_road_model_input.drop(['Efficiency_avg'], axis=1, inplace=True)
################################################################################
#%%

#set surplus stocks to 0 for now
road_model_input['Surplus_stocks'] = 0

# road_model_input.loc[(road_model_input['Vehicle_sales_share'].isna()), 'Vehicle_sales_share'] = 0#TO DO THIS SHOULD BE FIXED EARLIER IN THE PROCESS
################################################################################

#%%
#CREATE STOCKS FOR NON ROAD
#this is an adjsutment to the road stocks data from 8th edition by setting stocks to 1 for all non road vehicles that have a value >0 for Energy
non_road_model_input.loc[(non_road_model_input['Energy'] > 0), 'Stocks'] = 1
non_road_model_input.loc[(non_road_model_input['Energy'] == 0), 'Stocks'] = 0
#%%
road_model_input_new = road_model_input[INDEX_COLS_NO_MEASURE + base_year_measures_list_ROAD + user_input_measures_list_ROAD + calculated_measures_ROAD]
non_road_model_input_new = non_road_model_input[INDEX_COLS_NO_MEASURE + base_year_measures_list_NON_ROAD + user_input_measures_list_NON_ROAD + calculated_measures_NON_ROAD]

#%%
#save previous_year_main_dataframe as a temporary dataframe we can load in when we want to run the process below.
road_model_input_new.to_csv('intermediate_data/model_inputs/road_model_input.csv', index=False)
non_road_model_input_new.to_csv('intermediate_data/model_inputs/non_road_model_input.csv', index=False)

#%%

# #%%
# if run:
#     road_model_input = pd.read_csv('intermediate_data/aggregated_model_inputs/aggregated_road_model_input.csv')
#     non_road_model_input= pd.read_csv('intermediate_data/aggregated_model_inputs/aggregated_non_road_model_input.csv')