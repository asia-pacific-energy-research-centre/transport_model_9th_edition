# all we need to do here is sum up activity by drive type, then join that onto the modle output with fuels columns, and calcualte efficiency as energy / activity_by_drive. There is also a long section in here for formatting.
#%%
#set working directory as one folder back so that config works
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
execfile("config/config.py")#usae this to load libraries and set variables. Feel free to edit that file as you need
#%%
# model_output_file_name = 'model_output_years_2017_to_2050_DATE20220824_1043.csv'
#load model output

model_output_all_with_fuels = pd.read_csv('output_data/model_output_with_fuels/{}'.format(model_output_file_name))

model_output_non_detailed = pd.read_csv('output_data/model_output/{}'.format(model_output_file_name))

#%%
#remvoe stocks col
model_output_non_detailed = model_output_non_detailed.drop(['Stocks'], axis=1)
#%%
#create activity by drive type df which will also be the accumulated annual demand df.
activity_by_drive = model_output_non_detailed[['Year', 'Economy', 'Scenario', 'Transport Type', 'Vehicle Type', 'Drive', 'Medium', 'Activity']]

activity_by_drive = activity_by_drive.groupby(['Year', 'Economy','Scenario',  'Transport Type', 'Vehicle Type', 'Drive', 'Medium']).sum().reset_index()
#%%
#using our model output with fuels and the activity by drive type, we will now calculate input activity efficiency by dividing energy by activity by drive type

#join activity by drive type df to model output with fuels
input_activity_ratio = model_output_all_with_fuels.merge(activity_by_drive, on=['Year', 'Economy','Scenario',  'Transport Type', 'Vehicle Type', 'Drive', 'Medium'], how='left')

#calcualte inpyt activity ratio#(INPUTACTIVITYRATIO is the ratio of energy to activity when activity is not broken down into the type of energy used, just what it is used for (eg. activity specifies drive type but not how much activity there is for electricity vs petrol in a PHEVG). also note that its diffrent from efficiency in the road model because that is valavulted as energy / travel km)

input_activity_ratio['Input_Activity_Ratio'] = input_activity_ratio['Energy'] / input_activity_ratio['Activity']

#remove unneeded columns
input_activity_ratio = input_activity_ratio.drop(['Activity', 'Energy'], axis=1)



################################################################################ 
#NEXT SECTION IS JUST FORMATTING
#%%

#then need to create TECHNOLOGY and FUELS columns/
#FUEL column is in accumulated_annual_demand, which is just activity by drive fro transport
accumulated_annual_demand = activity_by_drive.copy()
#by default set FUEL to:
accumulated_annual_demand['FUEL'] = 'd_trn_' + accumulated_annual_demand['Medium'] + '_' + accumulated_annual_demand['Transport Type'] + '_' + accumulated_annual_demand['Vehicle Type'] + '_' + accumulated_annual_demand['Drive'] # + '_' + accumulated_annual_demand['Fuel']
#if Medium is not road then set FUEL to medium and transport type #TO DO in hughs output he had set fuel for drive = nonspeicfied to the actual fuel type. but currently in the case that drive = nonspecified then fuel is also nonspecified.
accumulated_annual_demand.loc[accumulated_annual_demand.Medium != 'road', 'FUEL'] = 'd_trn_' + accumulated_annual_demand.Medium + '_' + accumulated_annual_demand['Transport Type']
#if medium is nonspecified then set FUEL to medium and fuel
accumulated_annual_demand.loc[accumulated_annual_demand.Medium == 'nonspecified', 'FUEL'] = 'd_trn_' + accumulated_annual_demand.Medium #+ '_' + accumulated_annual_demand.Fuel#TO DO in hughs output he had set fuel for drive = nonspeicfied to the actual fuel type. but currently in the case that drive = nonspecified then fuel is also nonspecified.
#%%
#remove uneeded columns
accumulated_annual_demand = accumulated_annual_demand.drop(['Transport Type', 'Vehicle Type', 'Drive', 'Medium'], axis=1)

#%%
#Now do TECHNOLOGY which is the same as FUEL except that it is a different column name, used in the inputactivityratio output and has TRN at the start
input_activity_ratio['TECHNOLOGY'] = 'TRN_' + input_activity_ratio['Medium'] + '_' + input_activity_ratio['Transport Type'] + '_' + input_activity_ratio['Vehicle Type'] + '_' + input_activity_ratio['Drive'] # + '_' + input_activity_ratio['Fuel']

#by default set FUEL to:
input_activity_ratio['TECHNOLOGY'] = 'TRN_' + input_activity_ratio['Medium'] + '_' + input_activity_ratio['Transport Type'] + '_' + input_activity_ratio['Vehicle Type'] + '_' + input_activity_ratio['Drive'] # + '_' + input_activity_ratio['Fuel']
#if Medium is not road then set FUEL to medium and transport type
input_activity_ratio.loc[input_activity_ratio.Medium != 'road', 'TECHNOLOGY'] = 'TRN_' + input_activity_ratio.Medium + '_' + input_activity_ratio['Transport Type']
#if medium is nonspecified then set FUEL to medium and fuel
input_activity_ratio.loc[input_activity_ratio.Medium == 'nonspecified', 'TECHNOLOGY'] = 'TRN_' + input_activity_ratio.Medium #+ '_' + input_activity_ratio.Fuel#TO DO

#%%
#remove medium, transport type, vehicle type, drive from input_activity_ratio
input_activity_ratio = input_activity_ratio.drop(['Medium', 'Transport Type', 'Vehicle Type', 'Drive'], axis=1)

#%%
#little fixes to replicate exxactly:
#make all columns in uppercase
input_activity_ratio.columns = input_activity_ratio.columns.str.upper()
#rename Economy to region
input_activity_ratio.rename(columns={'ECONOMY':'REGION'}, inplace=True)
#create MODE_OF_OPERATION column with value set to 1
input_activity_ratio['MODE_OF_OPERATION'] = 1
#create unit column with value set to np.nan
input_activity_ratio['UNITS'] = np.nan
#create NOTES column with value set to np.nan
input_activity_ratio['NOTES'] = np.nan
#%%
#make all columns in uppercase
accumulated_annual_demand.columns = accumulated_annual_demand.columns.str.upper()
#rename Economy to region
accumulated_annual_demand.rename(columns={'ECONOMY':'REGION'}, inplace=True)
#create MODE_OF_OPERATION column with value set to 1
accumulated_annual_demand['MODE_OF_OPERATION'] = 1
#create unit column with value set to np.nan
accumulated_annual_demand['UNITS'] = np.nan
#create NOTES column with value set to np.nan
accumulated_annual_demand['NOTES'] = np.nan
#%%
#make years to wide output
input_activity_ratio_wide = input_activity_ratio.pivot(index=['SCENARIO', 'REGION', 'TECHNOLOGY', 'FUEL', 'MODE_OF_OPERATION', 'UNITS', 'NOTES'], columns='YEAR', values='INPUT_ACTIVITY_RATIO').reset_index()
#make years to wide output
accumulated_annual_demand_wide = accumulated_annual_demand.pivot(index=['SCENARIO', 'REGION', 'FUEL', 'MODE_OF_OPERATION', 'UNITS', 'NOTES'], columns='YEAR', values='ACTIVITY').reset_index()
#%%
spreadsheet_file_name = model_output_file_name.replace('.csv', '.xlsx')
#SAVE all in one spreradsheet
with pd.ExcelWriter('output_data/osemosys_output/{}'.format(os.path.basename(spreadsheet_file_name))) as writer:  
    accumulated_annual_demand_wide.to_excel(writer, sheet_name='AccumulatedAnnualDemand',index = False)
    input_activity_ratio_wide.to_excel(writer, sheet_name='InputActivityRatio',index = False)

#%%