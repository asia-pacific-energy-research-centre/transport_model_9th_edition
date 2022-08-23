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
Switching_vehicle_sales_dist = pd.read_excel('input_data/user_input_spreadsheet.xlsx', sheet_name='Switching_vehicle_sales_dist')

Turnover_Rate_adjustments = pd.read_excel('input_data/user_input_spreadsheet.xlsx', sheet_name='Turnover_Rate_adjustments')

OccupanceAndLoad_growth = pd.read_excel('input_data/user_input_spreadsheet.xlsx', sheet_name='OccupanceAndLoad_growth')

New_vehicle_efficiency_growth = pd.read_excel('input_data/user_input_spreadsheet.xlsx', sheet_name='New_vehicle_efficiency_growth')


#%%


#set 2017 values to 1 so that any calculations for growth times base year remain the same
OccupanceAndLoad_growth.loc[OccupanceAndLoad_growth.Year == BASE_YEAR, 'Value'] = 1

#%%
#set vehicle type and drive to lower case
Switching_vehicle_sales_dist['Vehicle Type'] = Switching_vehicle_sales_dist['Vehicle Type'].str.lower()
Switching_vehicle_sales_dist['Drive'] = Switching_vehicle_sales_dist['Drive'].str.lower()
Turnover_Rate_adjustments['Vehicle Type'] = Turnover_Rate_adjustments['Vehicle Type'].str.lower()
Turnover_Rate_adjustments['Drive'] = Turnover_Rate_adjustments['Drive'].str.lower()
New_vehicle_efficiency_growth['Vehicle Type'] = New_vehicle_efficiency_growth['Vehicle Type'].str.lower()
New_vehicle_efficiency_growth['Drive'] = New_vehicle_efficiency_growth['Drive'].str.lower()
OccupanceAndLoad_growth['Vehicle Type'] = OccupanceAndLoad_growth['Vehicle Type'].str.lower()

#%%
#for now jsut create a value for 2017 in the dataframe, and set it to 1
New_vehicle_efficiency_growth_base_year = New_vehicle_efficiency_growth.loc[New_vehicle_efficiency_growth.Year == 2018,:]
New_vehicle_efficiency_growth_base_year['Value'] = 1
New_vehicle_efficiency_growth_base_year['Year'] = BASE_YEAR
New_vehicle_efficiency_growth = pd.concat([New_vehicle_efficiency_growth, New_vehicle_efficiency_growth_base_year])

#%%
#TEMP FIX
# OccupanceAndLoad_growth is not split by scenario so create some scenarios
OccupanceAndLoad_growth_CN = OccupanceAndLoad_growth.copy()
OccupanceAndLoad_growth_CN['Scenario'] = 'Carbon Neutral'
OccupanceAndLoad_growth['Scenario'] = 'Reference'
OccupanceAndLoad_growth = pd.concat([OccupanceAndLoad_growth, OccupanceAndLoad_growth_CN])

#%%
#adjsut user input values
Switching_vehicle_sales_dist.rename(columns={"Value": "Sales_adjustment"}, inplace=True)
Turnover_Rate_adjustments.rename(columns={"Value": "Turnover_rate_adjustment"}, inplace=True)
New_vehicle_efficiency_growth.rename(columns={"Value": "New_vehicle_efficiency_growth"}, inplace=True)
OccupanceAndLoad_growth.rename(columns={"Value": "Occupancy_or_load_adjustment"}, inplace=True)


#%%
with pd.ExcelWriter('intermediate_data/model_inputs/clean_user_input.xlsx') as writer: 
    #save cleaned user input to intemediate file
    Switching_vehicle_sales_dist.to_excel(writer, sheet_name='Switching_vehicle_sales_dist', index=False)
    Turnover_Rate_adjustments.to_excel(writer, sheet_name='Turnover_Rate_adjustments', index=False)
    New_vehicle_efficiency_growth.to_excel(writer, sheet_name='New_vehicle_efficiency_growth', index=False)
    OccupanceAndLoad_growth.to_excel(writer, sheet_name='OccupanceAndLoad_growth', index=False)

#%%