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
road_model_input = pd.read_csv('intermediate_data/aggregated_model_inputs/aggregated_road_model_input.csv')
non_road_model_input= pd.read_csv('intermediate_data/aggregated_model_inputs/aggregated_non_road_model_input.csv')

################################################################################
#%%
#CALCUALTE TRAVEL KM
road_model_input['Travel_km'] = road_model_input['Activity']/road_model_input['Occupancy_or_load']

#%%

#CALCUALTE TRAVEL KM PER STOCK
#After much deliberation it was arrived at that travel km per stock should be calculated as the average travel km per stock for each vehicle type. This was to avoid the effect of having weird ratios created by very small numbers. By averaging it also makes it easier to keep track of this variable.
average_travel_km_per_stock_of_vehicle_type = road_model_input[['Economy', 'Scenario', 'Transport Type', 'Vehicle Type', 'Year', 'Travel_km', 'Stocks']]
average_travel_km_per_stock_of_vehicle_type = average_travel_km_per_stock_of_vehicle_type.dropna().groupby(['Economy', 'Scenario', 'Transport Type', 'Vehicle Type', 'Year']).sum().reset_index()

average_travel_km_per_stock_of_vehicle_type['Travel_km_per_stock'] = average_travel_km_per_stock_of_vehicle_type['Travel_km']/average_travel_km_per_stock_of_vehicle_type['Stocks']


average_travel_km_per_stock_of_vehicle_type.drop(['Travel_km', 'Stocks'], axis=1, inplace=True)

#there are still some values where travel km per stock are na or 0 because trvlkm is 0 and in some cases stocks are also 0. 
#so where travelkm is 0, we will set travel km per stock to the average of the vehicle type/transport type fir that year
#first set all 0's to na
average_travel_km_per_stock_of_vehicle_type.loc[average_travel_km_per_stock_of_vehicle_type['Travel_km_per_stock']==0, 'Travel_km_per_stock'] = np.nan
#then replace nas
average_travel_km_per_stock_of_vehicle_type['Travel_km_per_stock'] = average_travel_km_per_stock_of_vehicle_type['Travel_km_per_stock'].fillna(average_travel_km_per_stock_of_vehicle_type.groupby(['Transport Type', 'Vehicle Type', 'Year'])['Travel_km_per_stock'].transform('mean'))

#now we have a travel km per stock for each vehicle type, we can merge this back into the original data
#%%

#'REPLACE STOCKS FOR FREIGHT LIGHT TRUCKS USING TRAVEL KM PER STOCK OF PASSENGER LIGHT TRUCKS'
#looks lik the stats for travel km per stock for lt freight is very wack, with its standard deviation being even higher than its mean. Generally, when comparing the data to NZ's ofifical stats the travel km per stock is too high and should be just a bit more than it is for LV's and lt's in passenger.
#as a temproary fix we will set the travel km per stock for lt freight to be the mean of lt passenger, for simplicity. Then cahnge the stocks using this vaue too
#note that this conclusion depends on the occupancy and load data being accurate. For now we will assume it is but it is worth looking into
#note that it is much easier to do this fix now than earlier because we have the travel km per stock for each vehicle type prepared
if EIGHTH_EDITION_DATA:
    lt_freight_fill = average_travel_km_per_stock_of_vehicle_type.loc[(average_travel_km_per_stock_of_vehicle_type['Vehicle Type'] == 'lt') &  (average_travel_km_per_stock_of_vehicle_type['Transport Type'] == 'passenger')]
    lt_freight_fill['Transport Type'] = 'freight'

    average_travel_km_per_stock_of_vehicle_type = average_travel_km_per_stock_of_vehicle_type.loc[~((average_travel_km_per_stock_of_vehicle_type['Vehicle Type'] == 'lt') & ( average_travel_km_per_stock_of_vehicle_type['Transport Type'] == 'freight'))]

    average_travel_km_per_stock_of_vehicle_type = pd.concat([average_travel_km_per_stock_of_vehicle_type, lt_freight_fill])

    road_model_input = road_model_input.merge(average_travel_km_per_stock_of_vehicle_type, on=['Economy', 'Scenario', 'Transport Type', 'Vehicle Type', 'Year'], how='left')

    road_model_input['Stocks'] = road_model_input['Travel_km'] / road_model_input['Travel_km_per_stock']#calculate stocks again?
# #quick analysis. lets average the travel km per stock for each vehicle type and see what the average is.
# road_model_input[['Travel_km_per_stock', 'Transport Type', 'Vehicle Type']].groupby(['Transport Type', 'Vehicle Type']).agg([np.mean, np.std, np.var, np.median]).reset_index()
################################################################################
#%%
#since we dont have a value for efficiency in travel lkm per unit of energy use for the input data based on 8th edition, we calcualte it now. In the future it would be good if this value was somehow cross refeenced and scaled with actual numbers, not numbers calcualted based on the estimates of travle km and energy.
road_model_input['Efficiency'] = road_model_input['Travel_km']/road_model_input['Energy']
#note that there are na's created by 0/0 here. for those we fix them by using the average efficiency of the vehicle type in the prcoess below. If the process below is replaced, need to make sure to fix the na's in new process

#there is a problem where the efficiency is very large for some vehicle types. This seems to occur for cases where there is very small use of that vehicle type. This is because the efficiency is calculated as travel km/energy use, and if there is very little energy use and the travel km is a little incrorect in absolute terms, then the efficiency will be incorrect by the same magnitude, which can be large proportionally, and since it is a ratio, it will be seem in absolute terms when yuou compare it to otehr ratios
#FOR NOW, where the efficiency value is obv wrong we will set the efficiency to be the mean of the efficiency for that vehicle type, we will then set the energy use to be the travel km divided by this efficiency. I think it will be okay to do this like this, the only consideraton is where we are presenting base year and input data by fuel type, since that data is already split into fuel type and wont be affected by this, but that seems unliekly.

#we will seaprarte the incorrect data and replace it with the mean of the correct data
rows_to_fix = road_model_input.loc[(road_model_input['Efficiency'] > 10) | (road_model_input['Efficiency'].isna())]
rows_to_fix.drop(['Efficiency'], axis=1, inplace=True)

road_model_input = road_model_input.loc[road_model_input['Efficiency'] <= 10]
#recalcualte eff for incorrect rows using avgs from correct rows
new_values_eff = road_model_input.groupby(['Scenario', 'Transport Type', 'Vehicle Type', 'Year', 'Drive']).sum().reset_index()
new_values_eff['Efficiency'] = new_values_eff['Travel_km']/new_values_eff['Energy']
new_values_eff = new_values_eff[['Scenario', 'Transport Type', 'Vehicle Type', 'Year', 'Drive', 'Efficiency']]

#%%
#FIX FOR FCEV HT's:
#avg diff between EV and FCEV in the same vehicle type
#first filter for only fcev and bev in non ht vehicle types
avg_diff = new_values_eff.loc[(new_values_eff['Drive'].isin(['bev', 'fcev'])) & (new_values_eff['Vehicle Type'] != 'ht')]
#then pivot so we ahve an eff col for each drive type.
avg_diff = avg_diff.pivot(index=['Scenario', 'Transport Type', 'Vehicle Type', 'Year'], columns='Drive', values='Efficiency').reset_index()
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
#%%

#attach new values for missing/incorrect eff values to rows to fix
rows_to_fix = rows_to_fix.merge(new_values_eff, on=['Scenario', 'Transport Type', 'Vehicle Type', 'Year', 'Drive'], how='left')

#concatenate with correct rows in orgiinal df
road_model_input = pd.concat([road_model_input, rows_to_fix])

#now recalcualte travel km and activity for these rows:
road_model_input['Travel_km'] = road_model_input['Energy'] * road_model_input['Efficiency']
road_model_input['Activity'] = road_model_input['Travel_km'] * road_model_input['Occupancy_or_load']
#%%
#also calc non road eff here, but this is just a placeholder for now, as it seems it would be better to also calcualte non road eff as efficiency = travel km / energy not activity /energy
non_road_model_input['Efficiency'] = non_road_model_input['Activity']/non_road_model_input['Energy']

#if activity and energy are 0 then we will get na. In this case we will replace the efficiency with the average efficiency of the whole of apec
non_road_model_input_avg_eff = non_road_model_input.groupby(['Medium', 'Transport Type', 'Vehicle Type', 'Drive', 'Year','Scenario']).sum().reset_index()
non_road_model_input_avg_eff['Efficiency_avg'] = non_road_model_input_avg_eff['Activity']/non_road_model_input_avg_eff['Energy']
non_road_model_input = non_road_model_input.merge(non_road_model_input_avg_eff[['Medium', 'Transport Type', 'Vehicle Type', 'Drive', 'Year','Scenario', 'Efficiency_avg']], on=['Medium', 'Transport Type', 'Vehicle Type', 'Drive', 'Year','Scenario'], how='left')
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
#this is an adjsutment to the road stocks data from 8th edition by setting stocks to 1 for all non road vehicles that have a value >0 for activity
non_road_model_input.loc[(non_road_model_input['Activity'] > 0), 'Stocks'] = 1
non_road_model_input.loc[(non_road_model_input['Activity'] == 0), 'Stocks'] = 0
#%%
road_model_input = road_model_input[['Economy', 'Scenario', 'Transport Type','Vehicle Type', 'Year', 'Drive', 'Activity','Energy', 'Stocks', 'Efficiency','Surplus_stocks', 'Travel_km', 'Travel_km_per_stock', 'Vehicle_sales_share', 'Occupancy_or_load', 'Turnover_rate', 'New_vehicle_efficiency']]#'Activity_per_stock',

#%%
#save previous_year_main_dataframe as a temporary dataframe we can load in when we want to run the process below.
road_model_input.to_csv('intermediate_data/model_inputs/road_model_input.csv', index=False)
non_road_model_input.to_csv('intermediate_data/model_inputs/non_road_model_input.csv', index=False)

#%%

