#use this file to kind of plan the creation of database for input data for the model. For now it will jsut take in the same data that hugh did, but the plan is to allow for it to take in other data in the future. 

#the file will take in all of hugs input data and create data that i can reuse. The aim is to keep the data that seems difficult to re-estimate, but intend to resestimate forecasted data that isnt difficult.
#%%
#import modules

execfile("../config/config.py")#usae this to load libraries and set variables. Feel free to edit that file as you need
#%%
###ACTIVITY DATA


#load data from demand_split.xlsx
xls = pd.ExcelFile('../input_data/Demand_split.xlsx')
#create empty dtfs to save data from each sheet in df to
activity_2 = pd.DataFrame()
covid_adjustments = pd.DataFrame()

for econ in  Economy_list:
    df1 = pd.read_excel(xls, econ, usecols="A:BL" , nrows =29,skiprows=30  )#above is activity
    df2 = pd.read_excel(xls, econ, usecols="B:BL" , nrows =14,skiprows=77  )
    #aboe is covid adjustments to apply toa ctivity

    #manually specifcy the rows where the data is found
    activity_2 = pd.concat([df1,activity_2])
    covid_adjustments = pd.concat([df2,covid_adjustments])

activity_2 = activity_2.dropna(how = "all")	
covid_adjustments = covid_adjustments.dropna(how = "all")

non_road_split_percent_2017 = pd.read_excel('../input_data/dummy_database.xlsx', sheet_name='non_road_split_percent_2017')#splits non-road transport activity between pass and freight. is timesed by energy for 2017 and then some sort of activity split?. 

#%%
#apply covid adjustments to all activity data
#first create indexes
activity_2 = activity_2.set_index(['Economy', 'Scenario', 'Activity'])
covid_adjustments = covid_adjustments.set_index(['Economy', 'Activity'])
activity_3 = activity_2 * covid_adjustments #apply covid adjustments to activity data using the Econmoy and activity indexes to make sure that the factors are applied correctly (I also double checked it worked as i expected)

#now save
activity_3.to_csv('../intermediate_data/activity.csv')


#%%


#NOTES
#basically it seems that we are going to have to 'work with what data we have'
#in activity we have:

# non_road_split_percent_2017
#     - split of pass to freight in non road energy and activity.
#     - it seems the data in demand_split already contains this though? need to check hughs code i think
#       - for now we will leave this until we undetrstand akk the ither data types. eg. stocks

# Demand_split - activity per medium/transport type, even for non-road. quite close to the values in output for activity. wonder how much effect the splits have
# -this was adjusted using the covid adjustments in the same file. I think it would be a good plan to apply these covid adjustments and then treat the resulting data as the input data from now on.


# activity_1 (avtivity) - this is road activity for some single year? split into vehicle type and drive types. i wonder how it was caclualted?

# #to think about:
# -why do we have non-road-split-percent.csv
# -how is avtivity calculated and what is it (moved it to stocks section)



#%%
###ENERGY DATA


APEC_transport = pd.read_csv('../input_data/00APEC_transport.csv')

#%%
#NOTES
#it seems like no energy data is actually used, except for to split the blending ratios?
#would be good to keep an eye out for the answer to this
#will do this later
#%%
###EFFICIENCY/Inpout_activty_ratio DATA
#i want to know if New_vehicle_efficiency ois actually eff or input_activity_ratio. its not very clear from the stock model
New_vehicle_efficiency = pd.read_excel('../input_data/dummy_database.xlsx', sheet_name='New_vehicle_efficiency',index_col=[0,1],header = [0,1,2])

New_vehicle_efficiency_NZS = pd.read_excel('../input_data/dummy_database.xlsx', sheet_name='New_vehicle_efficiency_NZS',index_col=[0,1],header = [0,1,2])

efficiency_3 = pd.read_excel('../input_data/input_calculations.xlsx', sheet_name='Efficiency')

efficiency_4 = pd.read_excel('../input_data/input_calculations.xlsx', sheet_name='Intensity_diff')

efficiency_5 = pd.read_excel('../input_data/input_calculations.xlsx', sheet_name='Switch')

biofuel_blending_ratio = pd.read_excel('../input_data/dummy_database.xlsx', sheet_name='biofuel_blending_ratio')#this is applied kind of like the swtiching data. it will times the input_activity_ratio for agsoline and/or diesel by the blending ratio to get input activity ratio for biogasoline and/or diesel, then do the same but using 1-biofuel blending ratio to get the new input_activty ratio for the original fuel. 
#%%
non_road_eff = efficiency_3
#so we have eff data for all categories. but how did hugh use the intensity diff?

#road eff data is in a weird format.
df_fuel_switch_lost = 1-df_fuel_switch.groupby(["Economy","Scenario","Mode","Transport Type","Fuel"]).sum()
df_fuel_switch_lost = df_fuel_switch_lost.clip(lower=0)#lower: Minimum threshold value. All values below this threshold will be set to it. A missing threshold (e.g NA) will not clip the value.
df_fuel_switch_piv = df_fuel_switch.stack().unstack(level =-2)# = df_fuel_switch.loc["11_MEX"].reset_index(leve"l =-1)"
df_fuel_switch_piv = df_fuel_switch_piv.rename_axis(index= {None:"Year"})
#this is then timesed by activity with the data in tall format, with index columns for Economy', 'Scenario', 'Mode', 'Transport Type', 'Fuel', 'Year'
new_fuels = df_fuel_switch_piv.mul(inputs_activity_non_road_eff,axis =0 ).stack().unstack(level =-2)

#after the above, intensity_diff is used:
new_fuels = new_fuels.mul(Intensity_diff["Intensity"].iloc[:], axis=0 ).dropna(how = "all")
inputs_activity_non_road_eff= inputs_activity_non_road_eff.unstack(level = -1 ).mul(df_fuel_switch_lost,fill_value = 1)
inputs_activity_non_road_eff = pd.concat([new_fuels,inputs_activity_non_road_eff])
#Sum to remove duplicates
inputs_activity_non_road_eff = inputs_activity_non_road_eff.groupby(["Economy","Scenario","Mode","Transport Type","Fuel"]).sum().iloc[:,:]
inputs_activity_non_road_eff = inputs_activity_non_road_eff.clip(lower=0)
#and it seems like somehow this is the new efficviencvy. 
#maybe this new value is activity instead of efficiency? thios would explainm why hugh is decreasing the value if there is switching to other fuels. after all, the dataframe is saved as inputs_activity_non_road.pkl. ACTUALLY NO BECAUSE IF YOU LOOK IN 6_BUILD INPUTS_ACTIVITY IS SHORT FOR INPUTS ACTIVITY RATIO.

#%%




#%%
#NOTES
anything in input_calculations.xlsx is only for non-road data. I dont understand intensity diff and switch sheets that well. I would guess switch values are for changes in stocks? so ive put them down there too.

New_vehicle_efficiency_NZS and New_vehicle_efficiency are for road vehicle eff

#%%
###STOCKS
#Import vehicle sales data 
existing_stocks = pd.read_csv("{}/Fleet_Composition_2017.csv".format(input_data_path), index_col= [0,1],header=[0,1,2])

df_Vehicle_sales_share_ref = pd.read_excel("../input_data/Vehicle_sales_share_mod.xlsx",sheet_name= 'Reference' ,skiprows=32, usecols="C:BH",index_col=[0,1,2,3])

df_Vehicle_sales_share_cn = pd.read_excel("../input_data/Vehicle_sales_share_mod.xlsx",sheet_name= 'Net-zero' ,skiprows=32, usecols="C:BH",index_col=[0,1,2,3])

turnover_rate = pd.read_excel('../input_data/dummy_database.xlsx', sheet_name='Turnover_Rate')

#avtivity: not sure what this data is. this is a recurring problem with this file. But it was used in road stock model as follows:
#calculate ??? Establish the number of vehicles required based on travel and Occupancy trends Through to 2050???
# stock_new  = ((df_demand_road_projection_diff.mul(df_Vehicle_sales_share.stack(level = [0,1,2]))).dropna()).div(avtivity[0],axis = 0 ).reorder_levels([0,4,1,2,3]).dropna()
activity_1 = pd.read_excel('../input_data/dummy_database.xlsx', sheet_name='avtivity')

#%%

#%%
Vehicle_sales_share_mod - sales shares for road by drive type / V-type
turnover_rate - turnover rates

efficiency_5 seems like these ones are actually for non-road stocks?

#%%
###OTHER
Occupance_load = pd.read_excel('../input_data/dummy_database.xlsx', sheet_name='OccupanceAndLoad',index_col=[0,1],header = [0,1])

#%%
it seems likely that occupance load is just the amount of each people in each vehicle?
but then again, the variation of load for Passenger LT/2W and LV are quite intense. I doubt that this data could be accurate?
-will need to work out how to convert this data into a useful dataframe. Perhaps python will be easy to use for thsi, wereas pivot table function in excel doesnt work.and
-and when was this actually sued?


#%%
so what re we missing?
-need eff_5 (switch) to be for non-road stocks

