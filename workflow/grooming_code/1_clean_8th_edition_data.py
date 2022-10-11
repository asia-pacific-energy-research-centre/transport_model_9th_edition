#this file is intended for gathering the most useful data from the 8th edition model and fromatting it so that it can be used in this model. the code is long by nature, but an effort has been made to keep it in parts. so look for stocks, efficiency or wahtever data type you need if you need to make a fix or something. 

#CLEANING IS anything that involves changing the format of the data. The next step is filling in missing values. 
#%%
#set working directory as one folder back so that config works
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
from runpy import run_path
exec(open("config/config.py").read())#usae this to load libraries and set variables. Feel free to edit that file as you need

#%%

#STOCKS DATA
#this data is laoded from the original source finn found it. see the NOTES sheet in the file for more details
stocks_ref = pd.read_excel('input_data/from_8th/raw_data/TransportStocks.xlsx', sheet_name='stocks_Reference')
stocks_cn = pd.read_excel('input_data/from_8th/raw_data/TransportStocks.xlsx', sheet_name='stocks_Net-zero')

#add scenario column to differentiate the two scenarios when we stakc the data
stocks_ref['Scenario'] = 'Reference'
stocks_cn['Scenario'] = 'Carbon Neutral'

#make long format for use with other data
stocks_ref_long = pd.melt(stocks_ref, id_vars=['Economy', 'Scenario', 'Transport Type', 'Vehicle Type', 'Drive'], var_name='Year', value_name='Stocks')
stocks_cn_long = pd.melt(stocks_cn, id_vars=['Economy', 'Scenario', 'Transport Type', 'Vehicle Type', 'Drive'], var_name='Year', value_name='Stocks')

#stack the data so it can be used together.
stocks_long = pd.concat([stocks_ref_long,stocks_cn_long], axis=0).dropna()

#make the categorical data except scenario all in lowercase. This simplifies things.
stocks_long['Transport Type'] = stocks_long['Transport Type'].str.lower()
stocks_long['Vehicle Type'] = stocks_long['Vehicle Type'].str.lower()
stocks_long['Drive'] = stocks_long['Drive'].str.lower()

stocks_long['Medium'] = 'road'

#%%
#save
stocks_long.to_csv("intermediate_data/cleaned_input_data/road_stocks.csv", index=False)

#%%
################################################################################################################################################################
#%%

#ACTIVITY and INPUTACTIVITYRATIO :
#(INPUTACTIVITYRATIO is the ratio of energy to activity when activity is not broken down into the type of energy used, just what it is used for (eg. activity specifies drive type but not how much activity there is for electricity vs petrol in a PHEVG))

#this data is from the osemsys AccumulatedAnnualDemand output for the osemosys model from 8th edition. 
#the code is also used in aperc-transport\workflow\7_build_simplified_output_sheets.py to convert the data in the same way, just keeping it here helps the user so they dont need to use two sets of code

#this process will convert the data so it has a column for year, scenario economy, medium, transport type, drive and vehilce type

#load in osemosys data
spreadsheet_name = 'OSEMOSYS-hughslast'
output_file_name = "input_data/from_8th/raw_data/{}.xlsx".format(spreadsheet_name)
# output_file_name = 'output_data/OSEMOSYS_TransoprtReference_06-16-2022-36.xlsx'
AccumulatedAnnualDemand_df = pd.read_excel(output_file_name, sheet_name = "AccumulatedAnnualDemand", header=0)
InputActivityRatio_df = pd.read_excel(output_file_name, sheet_name = "InputActivityRatio", header=0)

#SPLIT THE TECHNOLOGY COL BASED ON THE UNDERSCORES. 
#will do this for AccumulatedAnnualDemand, and then a similar thing for InputActivityRatio after
AccumulatedAnnualDemand  = AccumulatedAnnualDemand_df.copy()
#remove d_trn from FUEL
AccumulatedAnnualDemand['FUEL'] = AccumulatedAnnualDemand['FUEL'].str.replace('d_trn_','')

#medium is the first word before underscore
AccumulatedAnnualDemand['Medium'] = AccumulatedAnnualDemand['FUEL'].str.split('_').str[0]

#transport type is the second word before underscore unless medium is unspecified. in which case unspecifeid final words are fuels. #WE 'LL JUST IGNORE THOSE FOR NOW
AccumulatedAnnualDemand['Transport Type'] = AccumulatedAnnualDemand['FUEL'].str.split('_').str[1]
AccumulatedAnnualDemand.loc[AccumulatedAnnualDemand['Medium'] == 'nonspecified', 'Transport Type'] = np.nan

#now set drive, if the medium is road. if not it will ddefault to na
AccumulatedAnnualDemand.loc[AccumulatedAnnualDemand['Medium'] == 'road', 'Drive'] = AccumulatedAnnualDemand['FUEL'].str.split('_').str[3] 

#now set vehicle type, sexccept in case of nonspec when it will be nan
AccumulatedAnnualDemand['Vehicle Type'] = AccumulatedAnnualDemand['FUEL'].str.split('_').str[2]
AccumulatedAnnualDemand.loc[AccumulatedAnnualDemand['Medium'] == 'nonspecified', 'Vehicle Type'] = np.nan

#move the all above created columns to the beginning of the dataframe and then remove unneccesary ones
AccumulatedAnnualDemand.insert(loc=5, column='Medium', value=AccumulatedAnnualDemand.pop('Medium'))
AccumulatedAnnualDemand.insert(loc=5, column='Transport Type', value=AccumulatedAnnualDemand.pop('Transport Type'))
AccumulatedAnnualDemand.insert(loc=5, column='Vehicle Type', value=AccumulatedAnnualDemand.pop('Vehicle Type'))
AccumulatedAnnualDemand.insert(loc=5, column='Drive', value=AccumulatedAnnualDemand.pop('Drive'))

AccumulatedAnnualDemand = AccumulatedAnnualDemand.drop(columns=['FUEL', 'UNITS', 'NOTES'])
#%%
#NOW DO THE SAME FOR EFF DATA
InputActivityRatio  = InputActivityRatio_df.copy()

#remove d_trn
InputActivityRatio['TECHNOLOGY'] = InputActivityRatio['TECHNOLOGY'].str.replace('TRN_','')

#medium is the first word before underscore
InputActivityRatio['Medium'] = InputActivityRatio['TECHNOLOGY'].str.split('_').str[0]

#transport type is the second word before underscore unless medium is unspecified. in which case unspecifeid final words are fuels. #WE 'LL JUST IGNORE THOSE FOR NOW
InputActivityRatio['Transport Type'] = InputActivityRatio['TECHNOLOGY'].str.split('_').str[1]
InputActivityRatio.loc[InputActivityRatio['Medium'] == 'nonspecified', 'Transport Type'] = np.nan

#now set drive, if the medium is road. if not it will ddefault to na
InputActivityRatio.loc[InputActivityRatio['Medium'] == 'road', 'Drive'] = InputActivityRatio['TECHNOLOGY'].str.split('_').str[3] 

#now set vehicle type, sexccept in case of nonspec when it will be nan
InputActivityRatio['Vehicle Type'] = InputActivityRatio['TECHNOLOGY'].str.split('_').str[2]
InputActivityRatio.loc[InputActivityRatio['Medium'] == 'nonspecified', 'Vehicle Type'] = np.nan

#recreate fuel col with lower case
InputActivityRatio['Fuel'] = InputActivityRatio['FUEL']

#move the all above created columns to the beginning of the dataframe and then remove unneccesary ones
InputActivityRatio.insert(loc=5, column='Medium', value=InputActivityRatio.pop('Medium'))
InputActivityRatio.insert(loc=5, column='Transport Type', value=InputActivityRatio.pop('Transport Type'))
InputActivityRatio.insert(loc=5, column='Vehicle Type', value=InputActivityRatio.pop('Vehicle Type'))
InputActivityRatio.insert(loc=5, column='Drive', value=InputActivityRatio.pop('Drive'))

InputActivityRatio = InputActivityRatio.drop(columns=['FUEL', 'UNITS', 'NOTES', 'MODE_OF_OPERATION', 'TECHNOLOGY'])

#%%
#ADDITIONAL FIXES

#first do input activity ratio (will clearly indicate where a fix is not the aame for the following acc annual demand df)

#rename SCENARIO and REGION cols
InputActivityRatio.rename(columns={'SCENARIO': 'Scenario', 'REGION': 'Economy'}, inplace=True)
#fill NANs in Drive, vehicle type and transport type cols with the valu in medium col
InputActivityRatio.loc[InputActivityRatio['Drive'].isna(), 'Drive'] = InputActivityRatio['Medium']
InputActivityRatio.loc[InputActivityRatio['Vehicle Type'].isna(), 'Vehicle Type'] = InputActivityRatio['Medium']
InputActivityRatio.loc[InputActivityRatio['Transport Type'].isna(), 'Transport Type'] = InputActivityRatio['Medium']
#rename Net-Zero to Carbon Neutral in Scenario col
InputActivityRatio.loc[InputActivityRatio['Scenario'] == 'Net-zero', 'Scenario'] = 'Carbon Neutral'
#set drive and vehicle type category to lower case ##NOTE THAT THIS IS ONLY FOR INPUT ACTIVITY RATIO
InputActivityRatio['Drive'] = InputActivityRatio['Drive'].str.lower()
InputActivityRatio['Vehicle Type'] = InputActivityRatio['Vehicle Type'].str.lower()
#make the data in long format
InputActivityRatio = InputActivityRatio.melt(id_vars=['Scenario', 'Economy', 'Medium', 'Transport Type', 'Vehicle Type', 'Drive', 'Fuel'], var_name='Year', value_name='Input Activity Ratio')

#ADDITIONAL FIXES
#For accumulated annual demand
#rename SCENARIO and REGION cols
AccumulatedAnnualDemand.rename(columns={'SCENARIO': 'Scenario', 'REGION': 'Economy'}, inplace=True)
#fill NANs in Drive, vehicle type and transport type cols with the valu in medium col
AccumulatedAnnualDemand.loc[AccumulatedAnnualDemand['Drive'].isna(), 'Drive'] = AccumulatedAnnualDemand['Medium']
AccumulatedAnnualDemand.loc[AccumulatedAnnualDemand['Vehicle Type'].isna(), 'Vehicle Type'] = AccumulatedAnnualDemand['Medium']
AccumulatedAnnualDemand.loc[AccumulatedAnnualDemand['Transport Type'].isna(), 'Transport Type'] = AccumulatedAnnualDemand['Medium']
#rename Net-Zero to Carbon Neutral in Scenario col
AccumulatedAnnualDemand.loc[AccumulatedAnnualDemand['Scenario'] == 'Net-zero', 'Scenario'] = 'Carbon Neutral'

#make the data in long format
AccumulatedAnnualDemand = AccumulatedAnnualDemand.melt(id_vars=['Scenario', 'Economy', 'Medium', 'Transport Type', 'Vehicle Type', 'Drive'], var_name='Year', value_name='Activity')

#%%
#search fr any NANs, print them out in case they are important, but by default drop them
print('There are ', sum(AccumulatedAnnualDemand.isna().sum()), 'NANs in the Accumulated Annual Demand dataframe. These are in the following columns:', pd.isnull(AccumulatedAnnualDemand).sum()[pd.isnull(AccumulatedAnnualDemand).sum() > 0], ' \n We will delte these by default. Take a look if you think it seems suspect \n\n')
AccumulatedAnnualDemand = AccumulatedAnnualDemand.dropna()

#search fr any NANs, print them out in case they are important, but by default drop them
print('There are ', sum(InputActivityRatio.isna().sum()), 'NANs in the Input Activity Ratio dataframe. These are in the following columns:', pd.isnull(InputActivityRatio).sum()[pd.isnull(InputActivityRatio).sum() > 0], ' \n We will delte these by default. Take a look if you think it seems suspect\n\n')
InputActivityRatio = InputActivityRatio.dropna()#note that if it is 1242 rows in every column except year then its fine, these are just weird NA rows

#count and remove duplicates when you consider the Value column
print('There are ', InputActivityRatio.duplicated().sum(), 'duplicated rows in the Input Activity Ratio dataframe. We will delte these by default. Take a look if you think it seems suspect\n\n')
InputActivityRatio = InputActivityRatio.drop_duplicates()

#sum up duplicated rows when you remove the value column 
print('There are ', InputActivityRatio.drop(columns=['Input Activity Ratio']).duplicated().sum(), 'duplicated rows in the Input Activity Ratio dataframe. We will sum these by default. Take a look if you think it seems suspect\n\n')
InputActivityRatio = InputActivityRatio.groupby(['Scenario', 'Economy', 'Medium', 'Transport Type', 'Vehicle Type', 'Drive', 'Fuel', 'Year']).sum().reset_index()

#count and remove duplicates when you consider the Value column
print('There are ', AccumulatedAnnualDemand.duplicated().sum(), 'duplicated rows in the Accumulated Annual Demand dataframe. We will delte these by default. Take a look if you think it seems suspect\n\n')#note that the 226 rows are no specified. to be safe i think we should delete these.
AccumulatedAnnualDemand = AccumulatedAnnualDemand.drop_duplicates()

#sum up duplicated rows when you remove the value column
print('There are ', AccumulatedAnnualDemand.drop(columns=['Activity']).duplicated().sum(), 'duplicated rows in the Accumulated Annual Demand dataframe. We will sum these by default. Take a look if you think it seems suspect\n\n')
AccumulatedAnnualDemand = AccumulatedAnnualDemand.groupby(['Scenario', 'Economy', 'Medium', 'Transport Type', 'Vehicle Type', 'Drive', 'Year']).sum().reset_index()#note that the 2914 duplicated rows are all nonspecified ones 


#%%
#SAVE all 
AccumulatedAnnualDemand.to_csv('intermediate_data/cleaned_input_data/activity_from_{}.csv'.format(spreadsheet_name), index=False)
InputActivityRatio.to_csv('intermediate_data/cleaned_input_data/inputactivityratio_from_{}.csv'.format(spreadsheet_name), index=False)

#%%
############################################################################################################################################################


#ENERGY DATA
#calculate this using the activity data and the input activity ratio data which is fromatted above. we will specify the input data, but this can be set to the file saved in the process above.

#want to calcualte data from the eff and activity data from osemosys system
activity_file_name = 'intermediate_data/cleaned_input_data/activity_from_{}.csv'.format(spreadsheet_name)
InputActivityRatio_file_name = "intermediate_data/cleaned_input_data/inputactivityratio_from_{}.csv".format(spreadsheet_name)

activity = pd.read_csv(activity_file_name)
InputActivityRatio = pd.read_csv(InputActivityRatio_file_name)

#%%
#FORMAT
# # # #rename befroe merge the value cols
# # # activity.rename(columns={'Value': 'Activity'}, inplace=True)
# # # InputActivityRatio.rename(columns={'Value': 'InputActivityRatio'}, inplace=True)
#merge. this is quite an important operation that probably will be resused in the future. it will keep the fuel column of InputActivityRatio and duplicate rows of the activity df for each fuel in the same drive
new_df = InputActivityRatio.merge(activity, how='left', on=['Economy', 'Scenario', 'Drive', 'Medium', 'Transport Type', 'Vehicle Type', 'Year'])

#%%
#OPERATION
#calculate enrgy as eff times act
new_df['Energy'] = new_df['Input Activity Ratio'] * new_df['Activity']

#%%
#FORMAT
#create a standalone energy dataframe
energy = new_df[['Economy', 'Scenario', 'Drive', 'Medium', 'Transport Type', 'Vehicle Type', 'Year', 'Energy', 'Fuel']]

#create the dataframe with no fuel column
energy_nofuel = energy.drop(columns=['Fuel'])
#sum
energy_nofuel = energy_nofuel.groupby(['Economy', 'Scenario', 'Drive', 'Medium', 'Transport Type', 'Vehicle Type', 'Year']).sum().reset_index()

#%%
#count and remove duplicates when you consider the Energy column
print('There are ', energy.duplicated().sum(), 'duplicated rows in the energy dataframe. We will delte these by default. Take a look if you think it seems suspect\n\n')
#sum up duplicated rows when you remove the value column
print('There are ', energy.drop(columns=['Energy']).duplicated().sum(), 'duplicated rows in the energy dataframe. We will sum these by default. Take a look if you think it seems suspect\n\n')
energy = energy.groupby(['Scenario', 'Economy', 'Medium', 'Transport Type', 'Vehicle Type', 'Drive', 'Year', 'Fuel']).sum().reset_index()

#%%
#SAVE
energy_nofuel.to_csv("intermediate_data/cleaned_input_data/energy.csv", index=False)
energy.to_csv("intermediate_data/cleaned_input_data/energy_with_fuel.csv", index=False)
#%%
##############################################################################################################

# #EFFICIENCY BY DRIVE
# #calcualte efficiency by drive, since we cannot possible estimate activity by fuel type when they are mixed together 
# #but have to note that this is only efficiency per unit of activity,not unit of travel km, so might not be useful.
# #%%
# #load energy and activity data
# energy = pd.read_csv("intermediate_data/cleaned_input_data/energy.csv")
# activity = pd.read_csv(activity_file_name)   
# #%%
# #group by all but fuel type, then sum
# activity = activity.groupby(['Economy', 'Scenario', 'Drive', 'Medium', 'Transport Type', 'Vehicle Type', 'Year']).sum()
# energy = energy.groupby(['Economy', 'Scenario', 'Drive', 'Medium', 'Transport Type', 'Vehicle Type', 'Year']).sum()

# #merge data 
# eff_df = energy.merge(activity, how='left', on=['Economy', 'Scenario', 'Drive', 'Medium', 'Transport Type', 'Vehicle Type', 'Year']).reset_index()

# #%%
# #calculate eff as energy / activity
# eff_df['Efficiency'] = eff_df['Activity'] /  eff_df['Energy']

# # in some cases it seems like eff is being set to nan because activity and energy are 0. We will fix those by setting the eff to 0. this would be better solved by setting eff
# eff_df.loc[(eff_df['Activity'] == 0) & (eff_df['Energy'] == 0), 'Efficiency'] = 0

# #but now it seems there are cases when activity is NAN but energy is >0
# #%%
# #remove energy and activity cols
# efficiency_by_drive = eff_df.drop(columns=['Energy', 'Activity'])

# #count and remove duplicates when you consider the Value column
# print('There are ', efficiency_by_drive.duplicated().sum(), 'duplicated rows in the efficiency by drive dataframe. We will delte these by default. Take a look if you think it seems suspect\n\n')
# #sum up duplicated rows when you remove the value column
# print('There are ', efficiency_by_drive.drop(columns=['Efficiency']).duplicated().sum(), 'duplicated rows in the efficiency by drive dataframe. We will sum these by default. Take a look if you think it seems suspect\n\n')
# efficiency_by_drive = efficiency_by_drive.groupby(['Scenario', 'Economy', 'Medium', 'Transport Type', 'Vehicle Type', 'Drive', 'Year']).sum().reset_index()


# #%%
# #save
# efficiency_by_drive.to_csv("intermediate_data/cleaned_input_data/efficiency_by_drive.csv", index=False)


# #%%