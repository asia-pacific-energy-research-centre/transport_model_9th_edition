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
# turnover_rate = pd.read_excel('../input_data/adjustments_spreadsheet.xlsx', sheet_name='Turnover_Rate')#do we want this to be  agrowth rate or the actual value?

# occupance_load = pd.read_excel('../input_data/adjustments_spreadsheet.xlsx', sheet_name='OccupanceAndLoad')

# new_vehicle_eff = pd.read_excel('../input_data/adjustments_spreadsheet.xlsx', sheet_name='New_vehicle_efficiency')#do we want this to be  agrowth rate or the actual value? worth considering how user will enter new values. perhaps at least we provide them a spreadsheet which shows the resulting values if its just a growth rate

# non_road_split_percent_2017 = pd.read_excel('../input_data/adjustments_spreadsheet.xlsx', sheet_name='non_road_split_percent_2017')#probably good to work out later if this is worth using or replacing

# biofuel_blending_ratio = pd.read_excel('../input_data/adjustments_spreadsheet.xlsx', sheet_name='biofuel_blending_ratio')

# road_bio_fuel_use = pd.read_excel('../input_data/adjustments_spreadsheet.xlsx', sheet_name='road_bio_fuel_use')

# # avtivity = pd.read_excel('../input_data/adjustments_spreadsheet.xlsx', sheet_name='avtivity')

# vehicle_sales_share = pd.read_excel('../input_data/adjustments_spreadsheet.xlsx', sheet_name='Vehicle_sales_share')

adjustments = pd.read_csv('../intermediate_data/model_inputs/adjustments_merged.csv')

#%%
#DATA FIXES
#check if tehre are any duplicates of rows in activity and stocks after removing the values columns

#identify the kind of rows where we are getting these duplicates.
# activity[activity.duplicated(subset=['Economy', 'Scenario', 'Drive', 'Medium', 'Transport Type',
#        'Vehicle Type', 'Measure', 'Fuel', 'Year'], keep=False)]
# print(len(road_stocks)-len(road_stocks.drop(columns=['Value']).drop_duplicates()))
#we only have duplicates in nonspecified. just sum them here. but be speicifc
activity_nonspec = activity.loc[(activity['Vehicle Type']=='nonspecified') & (activity['Transport Type']=='Nonspecified') & (activity['Medium']=='Nonspecified') & (activity['Drive']=='nonspecified')].groupby(['Economy', 'Scenario', 'Drive', 'Medium', 'Transport Type', 'Vehicle Type', 'Measure', 'Fuel', 'Year']).sum().reset_index()
activity = activity.loc[~((activity['Vehicle Type']=='nonspecified') & (activity['Transport Type']=='Nonspecified') & (activity['Medium']=='Nonspecified') & (activity['Drive']=='nonspecified'))]
activity = activity.append(activity_nonspec)

#check if there are any duplicates of rows in any of our input data
print('tehre are this many duplicates in efficiency dataframe: ', len(efficiency)-len(efficiency.drop(columns=['Value']).drop_duplicates()))
print('tehre are this many duplicates in energy dataframe: ', len(energy)-len(energy.drop(columns=['Value']).drop_duplicates()))
print('tehre are this many duplicates in road_stocks dataframe: ', len(road_stocks)-len(road_stocks.drop(columns=['Value']).drop_duplicates()))
print('tehre are this many duplicates in activity dataframe: ', len(activity)-len(activity.drop(columns=['Value']).drop_duplicates()))

print('tehre are this many duplicates in turnover_rate dataframe: ', len(turnover_rate)-len(turnover_rate.drop(columns=['Value']).drop_duplicates()))
print('tehre are this many duplicates in occupance_load dataframe: ', len(occupance_load)-len(occupance_load.drop(columns=['Value']).drop_duplicates()))
print('tehre are this many duplicates in new_vehicle_eff dataframe: ', len(new_vehicle_eff)-len(new_vehicle_eff.drop(columns=['Value']).drop_duplicates()))
print('tehre are this many duplicates in non_road_split_percent_2017 dataframe: ', len(non_road_split_percent_2017)-len(non_road_split_percent_2017.drop(columns=['Value']).drop_duplicates()))
print('tehre are this many duplicates in biofuel_blending_ratio dataframe: ', len(biofuel_blending_ratio)-len(biofuel_blending_ratio.drop(columns=['Value']).drop_duplicates()))
print('tehre are this many duplicates in road_bio_fuel_use dataframe: ', len(road_bio_fuel_use)-len(road_bio_fuel_use.drop(columns=['Value']).drop_duplicates()))
# print('tehre are this many duplicates in avtivity dataframe: ', len(avtivity)-len(avtivity.drop(columns=['Value']).drop_duplicates()))
print('tehre are this many duplicates in vehicle_sales_share dataframe: ', len(vehicle_sales_share)-len(vehicle_sales_share.drop(columns=['Value']).drop_duplicates()))


#%%
#set stocks for medium =! road to 1. just to see how it affects things if we try with medium is anything
road_stocks.loc[(road_stocks['Medium']!='road'), 'Value'] = 1
#%%
#filter for only road data
#We probably only need to replicate a portion of these operations for non road data. Would be good to have them be the same so its easy to understand
activity = activity.loc[activity.Medium == 'road',:]
efficiency = efficiency.loc[efficiency.Medium == 'road',:]
energy = energy.loc[energy.Medium == 'road',:]
road_stocks = road_stocks.loc[road_stocks.Medium == 'road',:]

#%%
#remove unnecessary columns. For now we will assume that we wiull calcaulte fuel use after everuything else. 
activity.drop(['Medium', 'Fuel','Measure'], axis=1, inplace=True)#fuel is only unspecified for activity here
efficiency.drop(['Medium','Measure'], axis=1, inplace=True)
energy.drop(['Medium','Measure'], axis=1, inplace=True)
road_stocks.drop(['Medium', 'Fuel','Measure'], axis=1, inplace=True)

#fuel is only unspecified for stocks here
#%%
#DATA FIXES
#for sdome reason activity for aus 2017 and 2018 cng buses is >0 while stocks is 0. To fix this, just set activity to 0, as its too difficult to estimate what stocks should be.
#in some weird casses (seems like just  aus 2017 and 2018 cng buses), we get activity or stocks being 0 while the other is >0. So we will just set them to 0 if this happens and notify user of it. Over time we can iron out the probelm.
#first merge the datasets, then identify issues and unmerge
activity_stocks = activity.merge(road_stocks, on=['Economy', 'Scenario', 'Drive', 'Transport Type', 'Vehicle Type', 'Year'], how='outer').rename(columns={'Value_x':'Activity', 'Value_y':'Stocks'})
activity_stocks['Activity'] = activity_stocks['Activity'].fillna(0)
activity_stocks['Stocks'] = activity_stocks['Stocks'].fillna(0)
#%%
#we will create a new column to store the new activity value
activity_stocks['Activity_new'] = 1
#if st5ocks is 0 and activity is >0 then set Activity_new to 0
activity_stocks.loc[(activity_stocks['Stocks']==0) & (activity_stocks['Activity']>0), 'Activity_new'] = 0
#now do the reverse
activity_stocks['Stocks_new'] = 1
#if activity is 0 and stocks is >0 then set Stocks_new to 0
activity_stocks.loc[(activity_stocks['Activity']==0) & (activity_stocks['Stocks']>0), 'Stocks_new'] = 0
#now print out the number of cases where these issues occur
print('the number of cases where thjere are mismatches of activity and stocks is ', activity_stocks.loc[(activity_stocks['Activity_new']==0) | (activity_stocks['Stocks_new']==0)].shape[0])

#check for the some specific cases which matter most to us right now (since we only want to model using data for road, 2017 atm). #may want to do this for non road as well later but the issue is that stocks for non road are in the air.
activity_stocks_road_2017 = activity_stocks.loc[(activity_stocks['Year']==2017)].copy()
activity_stocks_road_2017 = activity_stocks_road_2017.loc[((activity_stocks_road_2017['Activity_new']==0) | (activity_stocks_road_2017['Stocks_new']==0))]
print('the number of cases where thjere are mismatches of activity and stocks in 2017 for road is ', activity_stocks_road_2017.shape[0])

#%%
#now merge with original dataframes and replace the values
activity_fixed = activity.merge(activity_stocks, on=['Economy', 'Scenario', 'Drive', 'Transport Type', 'Vehicle Type',  'Year'], how='left')
activity_fixed.loc[(activity_fixed['Activity_new']==0), 'Value'] = 0
activity_fixed = activity_fixed.drop(columns=['Activity_new', 'Stocks_new','Activity', 'Stocks'])
road_stocks_fixed = road_stocks.merge(activity_stocks, on=['Economy', 'Scenario', 'Drive', 'Transport Type', 'Vehicle Type', 'Year'], how='left')
road_stocks_fixed.loc[(road_stocks_fixed['Stocks_new']==0), 'Value'] = 0
road_stocks_fixed = road_stocks_fixed.drop(columns=['Activity_new', 'Stocks_new', 'Activity', 'Stocks'])

#%%
#we also have a lot of NAs in stocks. we will just set them to 0. it is a bit suss that we have so many NAs, but we will just set them to 0 for now
road_stocks_fixed['Value'] = road_stocks_fixed['Value'].fillna(0)

#%%
#renmame data columns to amke merging easier
activity_fixed.rename(columns={"Value": "Activity"}, inplace=True)
efficiency.rename(columns={"Value": "Efficiency"}, inplace=True)
energy.rename(columns={"Value": "Energy"}, inplace=True)
road_stocks_fixed.rename(columns={"Value": "Stocks"}, inplace=True)
#%%
#get base year data
activity_base_year = activity_fixed.loc[activity_fixed.Year == BASE_YEAR,:]
efficiency_base_year = efficiency.loc[efficiency.Year == BASE_YEAR,:]
energy_base_year = energy.loc[energy.Year == BASE_YEAR,:]
road_stocks_base_year = road_stocks_fixed.loc[road_stocks_fixed.Year == BASE_YEAR,:]

#%%
#adjust adjustments data
#make Vehicle Type and Drive cols lowercase 
vehicle_sales_share['Vehicle Type'] = vehicle_sales_share['Vehicle Type'].str.lower()
vehicle_sales_share['Drive'] = vehicle_sales_share['Drive'].str.lower()

occupance_load['Vehicle Type'] = occupance_load['Vehicle Type'].str.lower()

new_vehicle_eff['Vehicle Type'] = new_vehicle_eff['Vehicle Type'].str.lower()
new_vehicle_eff['Drive'] = new_vehicle_eff['Drive'].str.lower()

turnover_rate['Vehicle Type'] = turnover_rate['Vehicle Type'].str.lower()
turnover_rate['Drive'] = turnover_rate['Drive'].str.lower()

#%%
#replicate data so we have data for each scneario in the adjustments data. We can dcide later if we want to explicitly create diff data for the scenrios later or always replicate,, or even rpovdie a switch
vehicle_sales_share_CN = vehicle_sales_share.copy()
vehicle_sales_share_CN['Scenario'] = 'Carbon Neutral'
vehicle_sales_share['Scenario'] = 'Reference'
vehicle_sales_share = pd.concat([vehicle_sales_share, vehicle_sales_share_CN])

occupance_load_CN = occupance_load.copy()
occupance_load_CN['Scenario'] = 'Carbon Neutral'
occupance_load['Scenario'] = 'Reference'
occupance_load = pd.concat([occupance_load, occupance_load_CN])

turnover_rate_CN = turnover_rate.copy()
turnover_rate_CN['Scenario'] = 'Carbon Neutral'
turnover_rate['Scenario'] = 'Reference'
turnover_rate = pd.concat([turnover_rate, turnover_rate_CN])

#rename cols
occupance_load.rename(columns={"Value": "Occupancy_or_load"}, inplace=True)
turnover_rate.rename(columns={"Value": "Turnover_rate"}, inplace=True)
#ideal to change spreadhseet than renae here

#%%
##temp fixes
#make 2016 data also data for 2017 in occ_load 
occupance_load_2017 = occupance_load.loc[occupance_load.Year == 2016,:]
occupance_load_2017['Year'] = BASE_YEAR
occupance_load = occupance_load.append(occupance_load_2017)

#%%
#TEMP
#theres an issue where we ahve NA values in the efficency data. Since we can expect that we could estiamte tehse values if we looked online, we will jsut create dummy values that are averages of teh other values for teh same vehicle type.

efficiency_vehicle_type_avgs = efficiency_base_year.groupby(['Economy', 'Scenario', 'Transport Type', 'Vehicle Type', 'Year']).mean()
efficiency_vehicle_type_avgs.reset_index(inplace=True)
#rename
efficiency_vehicle_type_avgs.rename(columns={"Efficiency": "Efficiency_mean"}, inplace=True)

#join back onto efficiency data
efficiency_base_year = efficiency_vehicle_type_avgs.merge(efficiency_base_year, on=['Economy', 'Scenario', 'Transport Type', 'Vehicle Type', 'Year'], how='left')
#fillna's with the mean values
efficiency_base_year['Efficiency'].fillna(efficiency_base_year['Efficiency_mean'], inplace=True)
efficiency_base_year.drop(['Efficiency_mean'], axis=1, inplace=True)

#also tehre is no eff data for FCEV in 2017 Carbon Neutral in 21_VN. 
efficiency_base_year_vn = efficiency_base_year.loc[(efficiency_base_year.Drive == 'fcev') & (efficiency_base_year.Year == 2017) & (efficiency_base_year.Scenario == 'Reference') & (efficiency_base_year.Economy == '21_VN') ,:]
efficiency_base_year_vn['Scenario'] = 'Carbon Neutral'
efficiency_base_year = efficiency_base_year.append(efficiency_base_year_vn)

#%%
# #Filling in data for vehicles where there is no use, yet or even in future:
# # #we casn assume that there would at least be 1 of these vehicles in someones  where stocks are equal to NA or 0, set it to 1, so we dont have issues there, for now.
# #this is a temporary fix until we can figure out how to deal with this issue
# road_stocks_base_year['Stocks'].fillna(1, inplace=True)
# #replace 0's too
# road_stocks_base_year['Stocks'].replace(0, 1, inplace=True)

#i decided that it might be better to try to impllement the introduction of new vehicle/drive typoes when stock dist cahgnes from 0 to >0 as a result of switching.
#issues we could meet are: trying to accurately estimate the number of vehicles that are introduced (in terms of activity). 
#making sure that stocks are set to > 0 for first year oif introduction
#reducing complexity of code
#IN THE FIrst year, if we have stocks and activity = 0 but stock dist is >0 then we wont be able to use the above solution. so perhaps jsut anytime stocks and activity are 0 and stock dist is >0 we set stocks and activity to a ?small number?


#%%
#calccualte useful data

#%%
#now start replicating the model 
# #keep a lot of non-useful cols for now as they make it easier to work with other datasets later.

#REMOVED ACTIVITY PER STOC K AS IT IS NOT USEFUL AND CAUSED EXTRA CONFUSION. CVAN CALCULATE IT AFTER MODEL RUNS IF IT IS DEEEMED A USEFUL INDICATOR
# activity_per_stock = activity_base_year.merge(road_stocks_base_year, on=['Economy', 'Scenario', 'Drive', 'Transport Type', 'Vehicle Type', 'Year'], how='outer')
# activity_per_stock['Activity_per_stock'] = activity_per_stock['Activity']/activity_per_stock['Stocks']

#if deonminator and numerator are 0 then of course we get NAn, so we will fill these with 0 #BUT WHAT HAPPPENS WHEN the DENOMINATOR IS 0 BUT NUEMRATOR IS > 0?(INF?, SHOULD FIX THAT)
#also, is this right? if activity per stock is 0 then any future stocks will be 0 as 0 * >0 = 0. what if we make activity per stock the average of all others in the same vehicle type? .. can u assume that activity per stock of any vechiel type is the same across all drive types and fuyel types? Perhaps too much of an assumption? But if we dont make this assumption then?
# activity_per_stock.loc[(activity_per_stock['Activity'] == 0) & (activity_per_stock['Stocks'] == 0), 'Activity_per_stock'] = 0

# activity_per_stock.drop(['Activity', 'Stocks'], axis=1, inplace=True)


#%%
#calcualte travel km by merging stocks with occupancy
#IMPORTANT NOTE!!!!
# BEFORE DOING THIS WE NBEED TO MNAKE OCCPANCY LOAD HAVE YEARS GREATER THAN 2016. iDEALLY WE'D DOI THIS BY USING A LINEAR MODEL AND PROIJECTING BUT CAN SAVE THAT FOR WHEN IM DFOING ACTIVITRY POROJECTIONS. FOR NOW WELL SET 2016 VALUE TO 2017
travel_km = activity_base_year.merge(occupance_load, on=['Economy', 'Scenario','Transport Type', 'Vehicle Type', 'Year'], how='left')

travel_km['Travel_km'] = travel_km['Activity']/travel_km['Occupancy_or_load']

travel_km_per_stock = travel_km.merge(road_stocks_base_year, on=['Economy', 'Scenario', 'Drive', 'Transport Type', 'Vehicle Type', 'Year'], how='left')

travel_km_per_stock['Travel_km_per_stock'] = travel_km_per_stock['Travel_km']/travel_km_per_stock['Stocks']

#%%

##
#if deonminator and numerator are 0 then of course we get NAn, so we will fill these with the average of other values for the same vehicle type, using stocks as the denominator for the average
average_travel_km_per_stock_of_vehicle_type = travel_km_per_stock.dropna().groupby(['Economy', 'Scenario', 'Transport Type', 'Vehicle Type', 'Year']).mean()
average_travel_km_per_stock_of_vehicle_type.reset_index(inplace=True)
average_travel_km_per_stock_of_vehicle_type.rename(columns={"Travel_km_per_stock": "Travel_km_per_stock_mean"}, inplace=True)
average_travel_km_per_stock_of_vehicle_type.drop(['Activity', 'Occupancy_or_load', 'Travel_km', 'Stocks'], axis=1, inplace=True)

travel_km_per_stock = travel_km_per_stock.merge(average_travel_km_per_stock_of_vehicle_type, on=['Economy', 'Scenario', 'Transport Type', 'Vehicle Type', 'Year'], how='left')

travel_km_per_stock.loc[(travel_km_per_stock['Travel_km'] == 0) & (travel_km_per_stock['Stocks'] == 0), 'Travel_km_per_stock'] = travel_km_per_stock['Travel_km_per_stock_mean']
##

#%%

#remove unneeded cols. while these could be useful, it is more simple to keep dfs that arent central, being as simple as possible to make creating the central dfs more easy
travel_km_per_stock.drop(['Activity', 'Occupancy_or_load', 'Stocks', 'Travel_km'], axis=1, inplace=True)
travel_km.drop(['Activity', 'Occupancy_or_load'],axis=1, inplace=True)

#%%
#ADDED TO FUNCTION. Still needed for calcualitng base year values at least until we adjsut them permanently (which doesnt seem like a strict oimrpovement)
#to calculate vehicle sales dist we want to normalise the sales share to 1, up to each tranbsport type 
#ot do this we will sum by transport type (and year and economy and scenario), then divde one by this sum
vehicle_sales_share_transport_type_sum = vehicle_sales_share.groupby(['Economy', 'Scenario', 'Transport Type', 'Year']).sum()
vehicle_sales_share_transport_type_sum.rename(columns={"Value": "Vehicle_sales_share_sum"}, inplace=True)

vehicle_sales_share_normalised = vehicle_sales_share.merge(vehicle_sales_share_transport_type_sum, on=['Economy', 'Scenario', 'Transport Type', 'Year'], how='left')

vehicle_sales_share_normalised['Vehicle_sales_share_normalised'] = vehicle_sales_share_normalised['Value'] * (1 / vehicle_sales_share_normalised['Vehicle_sales_share_sum'])#TO DO CHECK HOW THIS HAS RESULTED. ANY ISSUES?

#filter so we only have base year values
vehicle_sales_share_normalised = vehicle_sales_share_normalised.loc[vehicle_sales_share_normalised.Year == BASE_YEAR,:]
#drop non useufl data cols
vehicle_sales_share_normalised.drop(['Value', 'Vehicle_sales_share_sum'], axis=1, inplace=True)

#%%
energy_use_no_fuel_base_year = energy_base_year.groupby(['Economy', 'Scenario', 'Drive', 'Transport Type', 'Vehicle Type', 'Year']).sum().reset_index()
#rename
energy_use_no_fuel_base_year.rename(columns={"Energy": "Energy_no_fuel"}, inplace=True)
#%%
#REPLICATE NEW YEAR CHANGE
#create dataframe for all data. It will be added to for every year in the range
# user_input_dataframe = pd.DataFrame() #dont think this is more useful than indiviula dfs. Switching_vehicle_sales_dist,Turnover_Rate_adjustments,OccupanceAndLoad_growth,New_vehicle_efficiency_growth
change_dataframe = pd.DataFrame()
previous_year_main_dataframe = pd.DataFrame()#this will contain forecasted data and data that is carried through to the next yeAR as adjustments
detailed_fuels_dataframe = pd.DataFrame()#for now we will keep this data separate from activity because it will incorporate calcuation of energy use using the energy mix data. the main dataframe will contain more aggregated sums of energy use. 
#for now

previous_year_main_dataframe = activity_base_year.merge(road_stocks_base_year, on=['Economy', 'Scenario', 'Drive', 'Transport Type', 'Vehicle Type', 'Year'], how='left')
previous_year_main_dataframe = previous_year_main_dataframe.merge(travel_km_per_stock, on=['Economy', 'Scenario', 'Drive', 'Transport Type', 'Vehicle Type', 'Year'], how='left')
previous_year_main_dataframe = previous_year_main_dataframe.merge(travel_km, on=['Economy', 'Scenario', 'Drive', 'Transport Type', 'Vehicle Type', 'Year'], how='left')
previous_year_main_dataframe = previous_year_main_dataframe.merge(vehicle_sales_share_normalised, on=['Economy', 'Scenario', 'Drive', 'Transport Type', 'Vehicle Type', 'Year'], how='left')
previous_year_main_dataframe = previous_year_main_dataframe.merge(energy_use_no_fuel_base_year, on=['Economy', 'Scenario', 'Drive', 'Transport Type', 'Vehicle Type', 'Year'], how='left')
previous_year_main_dataframe = previous_year_main_dataframe.merge(occupance_load, on=['Economy', 'Scenario', 'Transport Type', 'Vehicle Type', 'Year'], how='left')
previous_year_main_dataframe = previous_year_main_dataframe.merge(efficiency_base_year, on=['Economy', 'Scenario', 'Drive', 'Transport Type', 'Vehicle Type', 'Year'], how='left')
previous_year_main_dataframe = previous_year_main_dataframe.merge(turnover_rate, on=['Economy', 'Scenario', 'Transport Type', 'Drive','Vehicle Type', 'Year'], how='left')
# previous_year_main_dataframe = previous_year_main_dataframe.merge(activity_per_stock, on=['Economy', 'Scenario', 'Drive', 'Transport Type', 'Vehicle Type', 'Year'], how='left')
#%%
#set surplus stocks to 0 for now
previous_year_main_dataframe['Surplus_stocks'] = 0

#TO DO check that the above only contians only tehse cols 
previous_year_main_dataframe = previous_year_main_dataframe[['Economy', 'Scenario', 'Transport Type','Vehicle Type', 'Year', 'Drive', 'Activity', 'Stocks', 'Efficiency', 'Energy_no_fuel', 'Surplus_stocks', 'Travel_km', 'Travel_km_per_stock', 'Occupancy_or_load', 'Vehicle_sales_share_normalised','Turnover_rate']]#'Activity_per_stock', 

#AND CHECK YEAR IS BASE YEAR
previous_year_main_dataframe['Year'] = BASE_YEAR#remove this soon

#%%
#save previous_year_main_dataframe as a temporary dataframe we can load in when we want to run the process below.
previous_year_main_dataframe.to_csv('../input_data/TEMP_2017_previous_year_main_dataframe.csv', index=False)

#%%
#save stuff to ../intermediate_data/model_inputs/