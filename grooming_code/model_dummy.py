#create a replica of the model in model_simulation using the data we have
# Required data
# Activity (base year and forecasted[base on pop and gdp])
# Energy (base year)
# eff (base year)
# stocks (base year)
# occ rate (base year)
# fuel mixing (base year)
# sales distribution (base year)
# turnover rate (base year)

#%%
execfile("../config/config.py")#usae this to load libraries and set variables. Feel free to edit that file as you need

#%%
#now save
BASE_YEAR= 2017
END_YEAR = 2050
#%%
#data
activity = pd.read_csv('../input_data/from_8th_output/activity.csv')
efficiency = pd.read_csv('../input_data/from_8th_output/efficiency_by_drive.csv')
energy = pd.read_csv('../input_data/from_8th_output/energy.csv')
road_stocks = pd.read_csv('../input_data/from_8th_output/road_stocks.csv')

#%%
#adjustments
turnover_rate = pd.read_excel('../input_data/adjustments_spreadsheet.xlsx', sheet_name='Turnover_Rate')

occupance_load = pd.read_excel('../input_data/adjustments_spreadsheet.xlsx', sheet_name='OccupanceAndLoad')

new_vehicle_eff = pd.read_excel('../input_data/adjustments_spreadsheet.xlsx', sheet_name='New_vehicle_efficiency')

non_road_split_percent_2017 = pd.read_excel('../input_data/adjustments_spreadsheet.xlsx', sheet_name='non_road_split_percent_2017')

biofuel_blending_ratio = pd.read_excel('../input_data/adjustments_spreadsheet.xlsx', sheet_name='biofuel_blending_ratio')

road_bio_fuel_use = pd.read_excel('../input_data/adjustments_spreadsheet.xlsx', sheet_name='road_bio_fuel_use')

avtivity = pd.read_excel('../input_data/adjustments_spreadsheet.xlsx', sheet_name='avtivity')

vehicle_sales_share = pd.read_excel('../input_data/adjustments_spreadsheet.xlsx', sheet_name='Vehicle_sales_share')
#%%
#get base year data
activity_base_year = activity.loc[activity.Year == BASE_YEAR,:]
efficiency_base_year = efficiency.loc[efficiency.Year == BASE_YEAR,:]
energy_base_year = energy.loc[energy.Year == BASE_YEAR,:]
road_stocks_base_year = road_stocks.loc[road_stocks.Year == BASE_YEAR,:]

#%%
#filter for only road data
#We probably only need to replicate a portion of these operations for non road data. Would be good to have them be the same so its easy to understand
activity_base_year = activity_base_year.loc[activity_base_year.Medium == 'road',:]
efficiency_base_year = efficiency_base_year.loc[efficiency_base_year.Medium == 'road',:]
energy_base_year = energy_base_year.loc[energy_base_year.Medium == 'road',:]

#%%
#remove unnecessary columns. For now we will assume that we wiull calcaulte fuel use after everuything else. 
activity_base_year.drop(['Medium', 'Fuel','Measure'], axis=1, inplace=True)#fuel is only unspecified for activity here
efficiency_base_year.drop(['Medium','Measure'], axis=1, inplace=True)
energy_base_year.drop(['Medium','Measure'], axis=1, inplace=True)
road_stocks_base_year.drop(['Medium', 'Fuel','Measure'], axis=1, inplace=True)

#renmame data columns to amke merging easier
activity_base_year.rename(columns={"Value": "Activity"}, inplace=True)
efficiency_base_year.rename(columns={"Value": "Efficiency"}, inplace=True)
energy_base_year.rename(columns={"Value": "Energy"}, inplace=True)
road_stocks_base_year.rename(columns={"Value": "Stocks"}, inplace=True)
#fuel is only unspecified for stocks here

#%%
#adjust adjustments data
#make Vehicle Type and Drive cols lowercase 
vehicle_sales_share['Vehicle Type'] = vehicle_sales_share['Vehicle Type'].str.lower()
vehicle_sales_share['Drive'] = vehicle_sales_share['Drive'].str.lower()

occupance_load['Vehicle Type'] = occupance_load['Vehicle Type'].str.lower()
#%%
##temp fixes
#make 2016 data also data for 2017 in occ_load 
occupance_load_2017 = occupance_load.loc[occupance_load.Year == 2016,:]
occupance_load_2017['Year'] = 2017
occupance_load = occupance_load.append(occupance_load_2017)

#%%
#calccualte useful data

#%%
#now start replicating the model 
# #keep a lot of non-useful cols for now as they make it easier to work with other datasets later.
#first sum the activity total for transport type (so ignore drive, v-type, and fuel in grouping). 
activity_transport_type_sum = activity_base_year.groupby(['Economy', 'Scenario',  'Transport Type', 'Year']).sum()

#%%
activity_per_stock = activity_base_year.merge(road_stocks_base_year, on=['Economy', 'Scenario', 'Drive', 'Transport Type', 'Vehicle Type', 'Year'], how='outer')
activity_per_stock['Activity_per_stock'] = activity_per_stock['Activity']/activity_per_stock['Stocks']
activity_per_stock.drop(['Activity', 'Stocks'], axis=1, inplace=True)
#THERE IS AN ISSUE WEHRE SOME VALUES ARE NAN. ITS HARD TO TELL IF THIS IS A LEGIT ISSUE YET

#%%
#calcualte travel km by merging stocks with occupancy
#IMPORTANT NOTE!!!!
# BEFORE DOING THIS WE NBEED TO MNAKE OCCPANCY LOAD HAVE YEARS GREATER THAN 2016. iDEALLY WE'D DOI THIS BY USING A LINEAR MODEL AND PROIJECTING BUT CAN SAVE THAT FOR WHEN IM DFOING ACTIVITRY POROJECTIONS. FOR NOW WELL SET 2016 VALUE TO 2017
occupance_load.rename(columns={"Value": "Occupancy or Load"}, inplace=True)
travel_km = activity_base_year.merge(occupance_load, on=['Economy', 'Transport Type', 'Vehicle Type', 'Year'], how='left')

travel_km['Travel_km'] = travel_km['Activity']/travel_km['Occupancy or Load']

travel_km_per_stock = travel_km.merge(road_stocks_base_year, on=['Economy', 'Transport Type', 'Vehicle Type', 'Year'], how='left')

travel_km_per_stock['Travel_km_per_stock'] = travel_km_per_stock['Travel_km']/travel_km_per_stock['Stocks']

#%%
#to calculate vehicle sales dist we want to normalise the sales share to 1, up to each tranbsport type 
#ot do this we will sum by transport type (and year and economy and scenario), then divde one by this sum
vehicle_sales_share_transport_type_sum = vehicle_sales_share.groupby(['Economy', 'Scenario', 'Transport Type', 'Year']).sum()
vehicle_sales_share_transport_type_sum.rename(columns={"Value": "Vehicle_sales_share_sum"}, inplace=True)

vehicle_sales_share_normalised = vehicle_sales_share.merge(vehicle_sales_share_transport_type_sum, on=['Economy', 'Scenario', 'Transport Type', 'Year'], how='left')

vehicle_sales_share_normalised['Vehicle_sales_share_normalised'] = vehicle_sales_share_normalised['Value'] * (1 / vehicle_sales_share_normalised['Vehicle_sales_share_sum'])#TO DO CHECK HOW THIS HAS RESULTED. ANY ISSUES?

#%%
# TEMP
#calcualte activity growth from the activity data that ahs been forecasted already
#in the future this may already be part of the activity data input
# activity_growth = activity.loc[activity.Medium == 'road',:]
#may needto think about what subsets of data to use for this but for now no 

activity_growth = activity.drop(['Measure'], axis=1)

#sum up to transport type
activity_growth = activity_growth.groupby(['Economy', 'Scenario', 'Transport Type','Year', 'Medium']).sum().reset_index()

#sort by year and everything else in ascending order
activity_growth = activity_growth.sort_values(by=['Economy', 'Scenario', 'Transport Type', 'Medium', 'Year'])

#calc growth rate. set index so that the growth rate is calc only for Value col
activity_growth2 = activity_growth.set_index(['Economy', 'Scenario', 'Transport Type', 'Medium', 'Year']).pct_change()

#rename col to Activity_growth
activity_growth2.rename(columns={"Value": "Activity_growth"}, inplace=True)

#merge back on the activity data
activity_growth = activity_growth.merge(activity_growth2, on=['Economy', 'Scenario', 'Transport Type', 'Medium', 'Year'], how='left')

#set 2017 values to 1 so that any calculations for pct_cahgne times base year remain the same
activity_growth.reset_index(inplace=True)
activity_growth.loc[activity_growth.Year == 2017, 'Activity_growth'] = 1


#i wuoldve thought that the activity growth rate would be the same for all groups ? Perhaps that is what i should aim for in the future, but keep this code the same as it is more flexible?
#or even pct change by econmy since the rate should be the same?
#%%
#REPLICATE NEW YEAR CHANGE
#create dataframe for all data. It will be added to for every year in the range
change_dataframe = pd.DataFrame()
forecasted_dataframe = pd.DataFrame()

#add 2017 data to the dataframe
#add 
for year in len(range(BASE_YEAR, END_YEAR)):
    #wen done should go over the dfs and make sure no cols are in there that we dont need.


new_stock_sales_activity = activity_base_year.merge(vehicle_sales_share_normalised, on=['Economy', 'Transport Type', 'Vehicle Type', 'Drive', 'Year', 'Scenario'] , how='left')

new_stock_sales_activity['New_stock_sales_activity'] = new_stock_sales_activity['Activity'] * new_stock_sales_activity['Vehicle_sales_share_normalised']
#%%

#somehow we will need to make fuel mix work. Perhaps the best way to do this is to have energy use calculated last always. So you calculate activity, stocks, total energy use and efficiency by drive type, then split ttoal energy use into its fuel types. Then using this calculate the corresponding input activity ratio (which is the ratio of activity per drive type to the output of energy per fuel type). 
#Also, interesingly all values are independent of fuel mix, so perhaps we can caluclate everything in one function then create a seaparte function for incorporating fuel mix? and even emissions.



# %%

activity_growth.to_csv('intermediate_data/activity_growth.csv')#keep this for now as it is useful for debugging
#%%
#.groupby(['Economy', 'Scenario', 'Transport Type', 'Vehicle Type','Drive','Year', 'Fuel'])