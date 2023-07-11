#use this file to kind of plan the creation of database for input data for the model. For now it will jsut take in the same data that hugh did, but the plan is to allow for it to take in other data in the future. 
#%%
#import modules


from numpy import percentile


run_path("../config/config.py")#usae this to load libraries and set variables. Feel free to edit that file as you need
#%%
###ACTIVITY DATA
#not sure what this data is
activity_1 = pd.read_excel('../input_data/dummy_database.xlsx', sheet_name='avtivity')

#load data from demand_split.xlsx
big_df = pd.DataFrame()
activity_2 = pd.DataFrame()
xls = pd.ExcelFile('../input_data/Demand_split.xlsx')#this file is 
for econ in  Economy_list:
    df1 = pd.read_excel(xls, econ, usecols="A:BL" , nrows =29,skiprows=30  )#manually specifcy the rows where the data is found
    activity_2 = pd.concat([df1,activity_2])
activity_2 = activity_2.dropna(how = "all")	

non_road_split_percent_2017 = pd.read_excel('../input_data/dummy_database.xlsx', sheet_name='non_road_split_percent_2017')#splits non-road transport activity between pass and freight

#%%
#HOW TO MAKE ON OF THESE CELLS MARKDOWN?
#NOTES
#basically it seems that we are going to have to 'work with what data we have'
#in activity we have:
non_road_split_percent_2017 - split of pass to freight in non road energy and activity.
    - it seems the data in demand_split already contains this though? need to check hughs code i think
Demand_split - activity per medium/transport type, even for non-road

activity_1 (avtivity) - this is road activity! split into vehicle type and drive types. i wonder how it was caclualted?

#to think about:
-why do we have non-road-split-percent.csv
-how is avtivity calculated



#%%
###ENERGY DATA
biofuel_blending_ratio = pd.read_excel('../input_data/dummy_database.xlsx', sheet_name='biofuel_blending_ratio')
road_bio_fuel_use = pd.read_excel('../input_data/dummy_database.xlsx', sheet_name='road_bio_fuel_use')

APEC_transport = pd.read_csv('../input_data/00APEC_transport.csv')

#%%
#NOTES
#it seems like no energy data is actually used, except for to split the blending ratios?
#would be good to keep an eye out for the answer to this

#%%
###EFFICIENCY DATA
New_vehicle_efficiency = pd.read_excel('../input_data/dummy_database.xlsx', sheet_name='New_vehicle_efficiency')

New_vehicle_efficiency_NZS = pd.read_excel('../input_data/dummy_database.xlsx', sheet_name='New_vehicle_efficiency_NZS')

efficiency_3 = pd.read_excel('../input_data/input_calculations.xlsx', sheet_name='Efficiency')

efficiency_4 = pd.read_excel('../input_data/input_calculations.xlsx', sheet_name='Intensity_diff')

efficiency_5 = pd.read_excel('../input_data/input_calculations.xlsx', sheet_name='Switch')

#%%
#NOTES
anything in input_calculations.xlsx is only for non-road data. I dont understand intensity diff and switch sheets that well. I would guess switch values are for changes in stocks? so ive put them down there too.

New_vehicle_efficiency_NZS and New_vehicle_efficiency are for road vehicle eff

#%%
###STOCKS
#Import vehicle sales data 
df_Vehicle_sales_share_ref = pd.read_excel("../input_data/Vehicle_sales_share_mod.xlsx",sheet_name_name= 'Reference' ,skiprows=32, usecols="C:BH",index_col=[0,1,2,3])
df_Vehicle_sales_share_cn = pd.read_excel("../input_data/Vehicle_sales_share_mod.xlsx",sheet_name_name= 'Net-zero' ,skiprows=32, usecols="C:BH",index_col=[0,1,2,3])

turnover_rate = pd.read_excel('../input_data/dummy_database.xlsx', sheet_name='Turnover_Rate')

efficiency_5 = pd.read_excel('../input_data/input_calculations.xlsx', sheet_name='Switch')
#%%
Vehicle_sales_share_mod - sales shares for road by drive type / V-type
turnover_rate - turnover rates

efficiency_5 seems like these ones are actually for non-road stocks?

#%%
###OTHER
Occupance_load = pd.read_excel('../input_data/input_calculations.xlsx', sheet_name='OccupanceAndLoad')

#%%
it seems likely that occupance load is just the amount of each people in each vehicle?
but then again, the variation of load for Passenger LT/2W and LV are quite intense. I doubt that this data could be accurate?
-will need to work out how to convert this data into a useful dataframe. Perhaps python will be easy to use for thsi, wereas pivot table function in excel doesnt work.and
-and when was this actually sued?


#%%
so what re we missing?
-need eff_5 (switch) to be for non-road stocks

