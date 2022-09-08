#this is intended to be where all data that is used in the model is cleaned before being adjusted to be used in the model.

#CLEANING IS anything that involves changing the format of the data. The next step is filling in missing values. 
#%%
#set working directory as one folder back so that config works
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
execfile("config/config.py")#usae this to load libraries and set variables. Feel free to edit that file as you need

######################################################################################################

#%%
#first, prepare user input (in the future it may be smart ot aggregate this data in another file but for now it is ok)

#Load user input
Vehicle_sales_share = pd.read_excel('input_data/user_input_spreadsheet.xlsx', sheet_name='Vehicle_sales_share')

Turnover_rate_growth = pd.read_excel('input_data/user_input_spreadsheet.xlsx', sheet_name='Turnover_rate_growth')

OccupanceAndLoad_growth = pd.read_excel('input_data/user_input_spreadsheet.xlsx', sheet_name='OccupanceAndLoad_growth')

New_vehicle_efficiency_growth = pd.read_excel('input_data/user_input_spreadsheet.xlsx', sheet_name='New_vehicle_efficiency_growth')

non_road_efficiency_growth = pd.read_excel('input_data/user_input_spreadsheet.xlsx', sheet_name='non_road_efficiency_growth')


#%%
#set vehicle type and drive to lower case
Vehicle_sales_share['Vehicle Type'] = Vehicle_sales_share['Vehicle Type'].str.lower()
Vehicle_sales_share['Drive'] = Vehicle_sales_share['Drive'].str.lower()

Turnover_rate_growth['Vehicle Type'] = Turnover_rate_growth['Vehicle Type'].str.lower()
Turnover_rate_growth['Drive'] = Turnover_rate_growth['Drive'].str.lower()

New_vehicle_efficiency_growth['Vehicle Type'] = New_vehicle_efficiency_growth['Vehicle Type'].str.lower()
New_vehicle_efficiency_growth['Drive'] = New_vehicle_efficiency_growth['Drive'].str.lower()

non_road_efficiency_growth['Vehicle Type'] = non_road_efficiency_growth['Vehicle Type'].str.lower()
non_road_efficiency_growth['Drive'] = non_road_efficiency_growth['Drive'].str.lower()
non_road_efficiency_growth['Medium'] = non_road_efficiency_growth['Medium'].str.lower()

OccupanceAndLoad_growth['Vehicle Type'] = OccupanceAndLoad_growth['Vehicle Type'].str.lower()

# #%%
# #for now jsut create a value for 2017 in the dataframe, and set it to 1
# New_vehicle_efficiency_growth_base_year = New_vehicle_efficiency_growth.loc[New_vehicle_efficiency_growth.Year == 2018,:]
# New_vehicle_efficiency_growth_base_year['Value'] = 1
# New_vehicle_efficiency_growth_base_year['Year'] = BASE_YEAR
# New_vehicle_efficiency_growth = pd.concat([New_vehicle_efficiency_growth, New_vehicle_efficiency_growth_base_year])

#%%
#TEMP FIX
# OccupanceAndLoad_growth is not split by scenario so create some scenarios
OccupanceAndLoad_growth_CN = OccupanceAndLoad_growth.copy()
OccupanceAndLoad_growth_CN['Scenario'] = 'Carbon Neutral'
OccupanceAndLoad_growth['Scenario'] = 'Reference'
OccupanceAndLoad_growth = pd.concat([OccupanceAndLoad_growth, OccupanceAndLoad_growth_CN])

#%%
#rename
Vehicle_sales_share.rename(columns={"Value": "Vehicle_sales_share"}, inplace=True)
Turnover_rate_growth.rename(columns={"Value": "Turnover_rate_growth"}, inplace=True)
New_vehicle_efficiency_growth.rename(columns={"Value": "New_vehicle_efficiency_growth"}, inplace=True)
OccupanceAndLoad_growth.rename(columns={"Value": "Occupancy_or_load_growth"}, inplace=True)
non_road_efficiency_growth.rename(columns={"Value": "Efficiency_growth"}, inplace=True)

#%%
with pd.ExcelWriter('intermediate_data/cleaned_input_data/clean_user_input.xlsx') as writer: 
    #save cleaned user input to intemediate file
    Vehicle_sales_share.to_excel(writer, sheet_name='Vehicle_sales_share', index=False)
    Turnover_rate_growth.to_excel(writer, sheet_name='Turnover_rate_growth', index=False)
    New_vehicle_efficiency_growth.to_excel(writer, sheet_name='New_vehicle_efficiency_growth', index=False)
    OccupanceAndLoad_growth.to_excel(writer, sheet_name='OccupanceAndLoad_growth', index=False)
    non_road_efficiency_growth.to_excel(writer, sheet_name='non_road_efficiency_growth', index=False)
    
#%%