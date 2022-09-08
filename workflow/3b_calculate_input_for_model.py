#the point of this file is to calculate extra variables that may be needed by the model, for example travel_km_per_stock or nromalised stock sales etc.
#these varaibles are essentially the same varaibles which will be calcualted in the model as these variables act as the base year variables. 
#%%
#set working directory as one folder back so that config works
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
execfile("config/config.py")#usae this to load libraries and set variables. Feel free to edit that file as you need


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

#'REPLACE STOCKS FOR FREIGHT LIGHT TRUCKS USING TRAVEL KM PER STOCK OF PASSENGER LIGHT TRUCKS'
#looks lik the stats for travel km per stock for lt freight is very wack, with its standard deviation being even higher than its mean. Generally, when comparing the data to NZ's ofifical stats the travel km per stock is too high and should be just a bit more than it is for LV's and lt's in passenger.
#as a temproary fix we will set the travel km per stock for lt freight to be the mean of lt passenger, for simplicity. Then cahnge the stocks using this vaue too
#note that this conclusion depends on the occupancy and load data being accurate. For now we will assume it is but it is worth looking into
#note that it is much easier to do this fix now than earlier because we have the travel km per stock for each vehicle type prepared
if EIGHTH_EDITION_DATA:
    lt_freight_fill = average_travel_km_per_stock_of_vehicle_type.loc[(average_travel_km_per_stock_of_vehicle_type['Vehicle Type'] == 'lt') &  (average_travel_km_per_stock_of_vehicle_type['Transport Type'] == 'passenger')]
    lt_freight_fill['Transport Type'] = 'freight'

    average_travel_km_per_stock_of_vehicle_type = average_travel_km_per_stock_of_vehicle_type.loc[~((average_travel_km_per_stock_of_vehicle_type['Vehicle Type'] == 'lt') & ( average_travel_km_per_stock_of_vehicle_type['Transport Type'] == 'freight'))]

    average_travel_km_per_stock_of_vehicle_type = average_travel_km_per_stock_of_vehicle_type.append(lt_freight_fill)

    road_model_input = road_model_input.merge(average_travel_km_per_stock_of_vehicle_type, on=['Economy', 'Scenario', 'Transport Type', 'Vehicle Type', 'Year'], how='left')

    road_model_input['Stocks'] = road_model_input['Travel_km'] / road_model_input['Travel_km_per_stock']#calculate stocks again?
# #quick analysis. lets average the travel km per stock for each vehicle type and see what the average is.
# road_model_input[['Travel_km_per_stock', 'Transport Type', 'Vehicle Type']].groupby(['Transport Type', 'Vehicle Type']).agg([np.mean, np.std, np.var, np.median]).reset_index()
################################################################################
#%%

#set surplus stocks to 0 for now
road_model_input['Surplus_stocks'] = 0

# road_model_input.loc[(road_model_input['Vehicle_sales_share'].isna()), 'Vehicle_sales_share'] = 0#TO DO THIS SHOULD BE FIXED EARLIER IN THE PROCESS
################################################################################

#%%
#CREATE STOCKS FOR NON ROAD
#this is an adjsutment to the road stocks data from 8th edition by setting stocks to 1 for all non road vehicles that have a value >0 for activity
non_road_model_input.loc[(non_road_model_input['Medium'] != 'Road') & (non_road_model_input['Activity'] > 0), 'Stocks'] = 1

#%%
road_model_input = road_model_input[['Economy', 'Scenario', 'Transport Type','Vehicle Type', 'Year', 'Drive', 'Activity', 'Stocks', 'Efficiency', 'Energy', 'Surplus_stocks', 'Travel_km', 'Travel_km_per_stock', 'Vehicle_sales_share', 'Occupancy_or_load', 'Turnover_rate', 'New_vehicle_efficiency']]#'Activity_per_stock',

#%%
#save previous_year_main_dataframe as a temporary dataframe we can load in when we want to run the process below.
road_model_input.to_csv('intermediate_data/model_inputs/road_model_input.csv', index=False)
non_road_model_input.to_csv('intermediate_data/model_inputs/non_road_model_input.csv', index=False)

#%%



# #CALCUALTE reVERSE NORMALISED SALES SHARE (this is used when activity growth is negative, and we wat to see what vehicle types see the least activity)
# #to calculate reVERSE vehicle sales dist we want to reVERSE THE nromalised SALES SHARE (calcualte 1 - x where x is the sales share) then normalise the sales share to 1, up to each tranbsport type 
# #ot do this we will first reverse, then sum by transport type (and year and economy and scenario), then divde one by this sum
# road_model_input['Vehicle_sales_share_reversed'] = 1 - road_model_input['Vehicle_sales_share']#reversed probably isnt the correct word here, the first intention was to use 'inverse', but inverse has issues with 0 values, so i used reversed instead

# vehicle_sales_share_transport_type_sum = road_model_input[['Economy', 'Scenario', 'Transport Type', 'Year', 'Vehicle_sales_share_reversed']]

# vehicle_sales_share_transport_type_sum = vehicle_sales_share_transport_type_sum.groupby(['Economy', 'Scenario', 'Transport Type', 'Year']).sum()

# vehicle_sales_share_transport_type_sum.rename(columns={"Vehicle_sales_share_reversed": "Vehicle_sales_share_reversed_sum"}, inplace=True)

# road_model_input = road_model_input.merge(vehicle_sales_share_transport_type_sum, on=['Economy', 'Scenario', 'Transport Type', 'Year'], how='left')

# road_model_input['Vehicle_sales_share_reversed'] = road_model_input['Vehicle_sales_share_reversed'] * (1 / road_model_input['Vehicle_sales_share_reversed_sum'])

# #drop non useufl data cols
# road_model_input.drop(['Vehicle_sales_share_reversed_sum', 'Vehicle_sales_share_reversed'], axis=1, inplace=True)
#'Vehicle_sales_share_reversed',