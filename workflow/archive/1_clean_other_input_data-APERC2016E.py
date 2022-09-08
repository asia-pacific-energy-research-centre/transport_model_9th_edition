#this is intended to be where all data that is used in the model is cleaned before being adjusted to be used in the model.
#%%
#set working directory as one folder back so that config works
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
execfile("config/config.py")#usae this to load libraries and set variables. Feel free to edit that file as you need

#%%
#now save
BASE_YEAR= 2017
END_YEAR = 2050

#%%
#adjustments
turnover_rate = pd.read_excel('input_data/adjustments_spreadsheet.xlsx', sheet_name='Turnover_Rate')#do we want this to be  agrowth rate or the actual value?

occupance_load = pd.read_excel('input_data/adjustments_spreadsheet.xlsx', sheet_name='OccupanceAndLoad')

# new_vehicle_eff = pd.read_excel('input_data/adjustments_spreadsheet.xlsx', sheet_name='New_vehicle_efficiency')#do we want this to be  agrowth rate or the actual value? worth considering how user will enter new values. perhaps at least we provide them a spreadsheet which shows the resulting values if its just a growth rate

non_road_split_percent_2017 = pd.read_excel('input_data/adjustments_spreadsheet.xlsx', sheet_name='non_road_split_percent_2017')#probably good to work out later if this is worth using or replacing

biofuel_blending_ratio = pd.read_excel('input_data/adjustments_spreadsheet.xlsx', sheet_name='biofuel_blending_ratio')

road_bio_fuel_use = pd.read_excel('input_data/adjustments_spreadsheet.xlsx', sheet_name='road_bio_fuel_use')

# avtivity = pd.read_excel('input_data/adjustments_spreadsheet.xlsx', sheet_name='avtivity')

vehicle_sales_share = pd.read_excel('input_data/adjustments_spreadsheet.xlsx', sheet_name='Vehicle_sales_share')

#load model concordances for filling in missing dates where needed
model_concordances = pd.read_csv('config/model_concordances_20220822_1204.csv')

#%%
#adjust adjustments data
#make Vehicle Type and Drive cols lowercase 
vehicle_sales_share['Vehicle Type'] = vehicle_sales_share['Vehicle Type'].str.lower()
vehicle_sales_share['Drive'] = vehicle_sales_share['Drive'].str.lower()

occupance_load['Vehicle Type'] = occupance_load['Vehicle Type'].str.lower()

# new_vehicle_eff['Vehicle Type'] = new_vehicle_eff['Vehicle Type'].str.lower()
# new_vehicle_eff['Drive'] = new_vehicle_eff['Drive'].str.lower()

turnover_rate['Vehicle Type'] = turnover_rate['Vehicle Type'].str.lower()
turnover_rate['Drive'] = turnover_rate['Drive'].str.lower()

#%%
#replicate data so we have data for each scneario in the adjustments data. We can dcide later if we want to explicitly create diff data for the scenrios later or always replicate,, or even rpovdie a switch

occupance_load_CN = occupance_load.copy()
occupance_load_CN['Scenario'] = 'Carbon Neutral'
occupance_load['Scenario'] = 'Reference'
occupance_load = pd.concat([occupance_load, occupance_load_CN])

#rename cols
occupance_load.rename(columns={"Value": "Occupancy_or_load"}, inplace=True)
turnover_rate.rename(columns={"Value": "Turnover_rate"}, inplace=True)
#ideal to change spreadhseet than renae here

#i decided to mve the below to 3_prepare_data because it is estiamting data from the previous data and therefore not really a alcenaing action
##temp fixes
#make 2016 data also data for 2017 in occ_load. we may have to do this for subsequent years too . iDEALLY WE'D DOI THIS BY USING A LINEAR MODEL AND PROIJECTING BUT CAN SAVE THAT FOR WHEN IM DFOING ACTIVITRY POROJECTIONS. FOR NOW WELL SET 2016 VALUE TO 2017
# occupance_load_2016 = occupance_load.loc[occupance_load.Year == 2016,:]
# occupance_load_2016.drop(columns=['Year'], inplace=True)
# occupance_load.merge(occupance_load_2016, on=['Vehicle Type', 'Transport Type', 'Economy', 'Scenario'], how='left')

# occupance_load = occupance_load.append(occupance_load_2017)

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
#SAVE
turnover_rate.to_csv('intermediate_data/cleaned_input_data/turnover_rate.csv', index=False)
occupance_load.to_csv('intermediate_data/cleaned_input_data/occupance_load.csv', index=False)
vehicle_sales_share_normalised.to_csv('intermediate_data/cleaned_input_data/vehicle_sales_share_normalised.csv', index=False)
#%%