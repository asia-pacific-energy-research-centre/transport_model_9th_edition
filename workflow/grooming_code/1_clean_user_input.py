#this is intended to be where all data that is used in the model is cleaned before being adjusted to be used in the model.

#CLEANING IS anything that involves changing the format of the data. The next step is filling in missing values. 
#%%
#set working directory as one folder back so that config works
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
from runpy import run_path
exec(open("config/config.py").read())#usae this to load libraries and set variables. Feel free to edit that file as you need

#%%
######################################################################################################
#laod concordances for checking later
model_concordances_user_input_and_growth_rates = pd.read_csv('config/concordances_and_config_data/computer_generated_concordances/{}'.format(model_concordances_user_input_and_growth_rates_file_name))

#%%
#first, prepare user input (in the future it may be smart ot aggregate this data in another file but for now it is ok)

#Load user input from 'input_data/user_input_spreadsheet.xlsx' by looping through the sheets in the excel file and then concat them together
#first load the sheets
user_input_file = pd.ExcelFile('input_data/user_input_spreadsheet.xlsx')
for sheet in user_input_file.sheet_names:
    print('Importing user input sheet: {}'.format(sheet))
    if sheet == user_input_file.sheet_names[0]:
        user_input = pd.read_excel('input_data/user_input_spreadsheet.xlsx', sheet_name=sheet)
    else:
        user_input = pd.concat([user_input, pd.read_excel('input_data/user_input_spreadsheet.xlsx', sheet_name=sheet)])


################################################################################
################################################################################
################################################################################


#%%
#then filter for the same rows that are in the concordance table for user inputs and  grwoth rates. these rows will be based on a set of index columns as defined below. Once we have done this we can print out what data is unavailable (its expected that no data will be missing for the model to actually run)

#set index
user_input.set_index(INDEX_COLS, inplace=True)
model_concordances_user_input_and_growth_rates.set_index(INDEX_COLS, inplace=True)

#create empty list which we will append the data we extract from the user_inputs using an iterative loop. Then we will concat it all together into one dataframe
new_user_inputs = []

#create column which will be used to indicate whether the data is available in the user_inputs, or not
#options will be:
#1. data_available
#2. data_not_available
#3. row_and_data_not_available

#we can determine data available and not available now, and then find out option 3 by comparing to the model concordances:

#where vlaues arent na, set the data_available column to 1, else set to 2
user_input.loc[user_input.Value.notna(), 'Data_available'] = 'data_available'
user_input.loc[user_input.Value.isna(), 'Data_available'] = 'data_not_available'

#%%
# use the difference method to find the index values that are missing from the user_input and also the index values that are present in the user_input but not in the concordance # this is a lot faster than looping through each index row in the concordance and checking if it is in the user_input
missing_index_values1 = model_concordances_user_input_and_growth_rates.index.difference(user_input.index)
missing_index_values2 = user_input.index.difference(model_concordances_user_input_and_growth_rates.index)

if missing_index_values1.empty:
    print('All rows are present in the user input')
else:
    print('Missing rows in our user input dataset when we compare it to the concordance:', missing_index_values1)
    #add these rows to the user_input and set them to row_and_data_not_available
    new_user_input = user_input.reindex(missing_index_values1)
    new_user_input['Data_available'] = 'row_and_data_not_available'
    new_user_input['Value'] = np.nan

    #now append to user_input
    user_input = user_input.append(new_user_input)

if missing_index_values2.empty:
    pass#this is to be expected as the cocnordance should always have everything we need in it!
else:
    #we want to make sure user is aware of this as we will be removing rows from the user input
    print('Missing rows in the user input concordance: {}'.format(missing_index_values2))
    print('We will remove these rows from the user input dataset. If you intended to have data for these rows, please add them to the concordance table.')
    #remove these rows from the user_input
    user_input.drop(missing_index_values2, inplace=True)

#%%
#save the new_user_inputs
user_input.to_csv('intermediate_data/{}_user_inputs_and_growth_rates.csv'.format(FILE_DATE_ID))


#%%


















#%%
# #%%
# run = False
# if run:
#     with pd.ExcelWriter('intermediate_data/cleaned_input_data/clean_user_input.xlsx') as writer: 
#         #save cleaned user input to intemediate file
#         Vehicle_sales_share.to_excel(writer, sheet_name='Vehicle_sales_share', index=False)
#         Turnover_rate_growth.to_excel(writer, sheet_name='Turnover_rate_growth', index=False)
#         New_vehicle_efficiency_growth.to_excel(writer, sheet_name='New_vehicle_efficiency_growth', index=False)
#         OccupanceAndLoad_growth.to_excel(writer, sheet_name='OccupanceAndLoad_growth', index=False)
#         non_road_efficiency_growth.to_excel(writer, sheet_name='non_road_efficiency_growth', index=False)
    
#%%

# #%%
# #create option to add missing rows to the user input spreadsheet
# #frist get the missing rows and then separate them by measure
# #then add those rows to each measures orgiianl data set with a vlaue of 1
# #and then save all the data sets to the original excel file again
# new_user_input = user_input.reindex(missing_index_values1).reset_index()

# #%%
# #separate the new user input by measure
# Vehicle_sales_share_new = new_user_input.loc[new_user_input.Measure == 'Vehicle sales share']
# Turnover_rate_growth_new = new_user_input.loc[new_user_input.Measure == 'Turnover rate growth']
# New_vehicle_efficiency_growth_new = new_user_input.loc[new_user_input.Measure == 'New vehicle efficiency growth']
# non_road_efficiency_growth_new = new_user_input.loc[new_user_input.Measure == 'non-road efficiency growth']
# OccupanceAndLoad_growth_new = new_user_input.loc[new_user_input.Measure == 'OccupanceAndLoad growth']



# # save all the new data sets to the oringal excel file (with multiple sheets)
# write = pd.ExcelWriter('input_data/user_input_spreadsheet.xlsx', engine='xlsxwriter')
# Vehicle_sales_share.to_excel(write, sheet_name='Vehicle_sales_share', index=False)
# Turnover_rate_growth.to_excel(write, sheet_name='Turnover_rate_growth', index=False)
# New_vehicle_efficiency_growth.to_excel(write, sheet_name='New_vehicle_efficiency_growth', index=False)
# non_road_efficiency_growth.to_excel(write, sheet_name='non_road_efficiency_growth', index=False)
# OccupanceAndLoad_growth.to_excel(write, sheet_name='OccupanceAndLoad_growth', index=False)
# write.save()





#DELETE IN 2023:

#%%
# #%%
# #set vehicle type and drive to lower case
# Vehicle_sales_share['Vehicle Type'] = Vehicle_sales_share['Vehicle Type'].str.lower()
# Vehicle_sales_share['Drive'] = Vehicle_sales_share['Drive'].str.lower()

# Turnover_rate_growth['Vehicle Type'] = Turnover_rate_growth['Vehicle Type'].str.lower()
# Turnover_rate_growth['Drive'] = Turnover_rate_growth['Drive'].str.lower()

# New_vehicle_efficiency_growth['Vehicle Type'] = New_vehicle_efficiency_growth['Vehicle Type'].str.lower()
# New_vehicle_efficiency_growth['Drive'] = New_vehicle_efficiency_growth['Drive'].str.lower()

# non_road_efficiency_growth['Vehicle Type'] = non_road_efficiency_growth['Vehicle Type'].str.lower()
# non_road_efficiency_growth['Drive'] = non_road_efficiency_growth['Drive'].str.lower()
# non_road_efficiency_growth['Medium'] = non_road_efficiency_growth['Medium'].str.lower()

# OccupanceAndLoad_growth['Vehicle Type'] = OccupanceAndLoad_growth['Vehicle Type'].str.lower()

# #create a Measure column for each data set
# Vehicle_sales_share['Measure'] ='Vehicle_sales_share'
# Turnover_rate_growth['Measure'] = 'Turnover_rate_growth'
# New_vehicle_efficiency_growth['Measure'] = 'New_vehicle_efficiency_growth'
# non_road_efficiency_growth['Measure'] = 'Non_road_efficiency_growth'
# OccupanceAndLoad_growth['Measure'] = 'Occupancy_or_load_growth'

# #TEMP FIX
# # OccupanceAndLoad_growth is not split by scenario so create some scenarios
# OccupanceAndLoad_growth_CN = OccupanceAndLoad_growth.copy()
# OccupanceAndLoad_growth_CN['Scenario'] = 'Carbon Neutral'
# OccupanceAndLoad_growth['Scenario'] = 'Reference'
# OccupanceAndLoad_growth = pd.concat([OccupanceAndLoad_growth, OccupanceAndLoad_growth_CN])

# #remove years 2017 and all years after 2050
# Vehicle_sales_share = Vehicle_sales_share[Vehicle_sales_share['Year'] <= 2050]
# Turnover_rate_growth = Turnover_rate_growth[Turnover_rate_growth['Year'] <= 2050]
# New_vehicle_efficiency_growth = New_vehicle_efficiency_growth[New_vehicle_efficiency_growth['Year'] <= 2050]
# non_road_efficiency_growth = non_road_efficiency_growth[non_road_efficiency_growth['Year'] <= 2050]
# OccupanceAndLoad_growth = OccupanceAndLoad_growth[OccupanceAndLoad_growth['Year'] <= 2050]
# #remove 2017
# Vehicle_sales_share = Vehicle_sales_share[Vehicle_sales_share['Year'] != 2017]
# Turnover_rate_growth = Turnover_rate_growth[Turnover_rate_growth['Year'] != 2017]
# New_vehicle_efficiency_growth = New_vehicle_efficiency_growth[New_vehicle_efficiency_growth['Year'] != 2017]
# non_road_efficiency_growth = non_road_efficiency_growth[non_road_efficiency_growth['Year'] != 2017]
# OccupanceAndLoad_growth = OccupanceAndLoad_growth[OccupanceAndLoad_growth['Year'] != 2017]

# #temp
# #remove Medium and Data_available from missing_index_values1_df
# missing_index_values1_df = missing_index_values1_df.reset_index().drop(columns=['Medium','Data_available'])
# #set Value to 1
# missing_index_values1_df.Value = 1
# # print dataframe
# missing_index_values1_df

# #%%
# #add to turnover rate growth
# Turnover_rate_growth = pd.concat([Turnover_rate_growth, missing_index_values1_df])

# # Vehicle_sales_share.to_excel('input_data/user_input_spreadsheet.xlsx', sheet_name='Vehicle_sales_share', index=False)
# # Turnover_rate_growth.to_excel('input_data/user_input_spreadsheet.xlsx', sheet_name='Turnover_rate_growth', index=False)
# # New_vehicle_efficiency_growth.to_excel('input_data/user_input_spreadsheet.xlsx', sheet_name='New_vehicle_efficiency_growth', index=False)
# # non_road_efficiency_growth.to_excel('input_data/user_input_spreadsheet.xlsx', sheet_name='non_road_efficiency_growth', index=False)
# # OccupanceAndLoad_growth.to_excel('input_data/user_input_spreadsheet.xlsx', sheet_name='OccupanceAndLoad_growth', index=False)




# #%%
# #cant work out what is the reason for so many missing rows from Turnover_rate_growth measure. lets inspect
# x = user_input.reset_index().loc[user_input.reset_index().Measure == 'Turnover_rate_growth']
# #create copy of Turnover_rate_growth when we have no 2017 or values after 2050
# y = Turnover_rate_growth.loc[Turnover_rate_growth.Year != 2017]
# y = y.loc[y.Year <= 2050]
# #now need to find what is the column that is frequently missing in missing_index_values1
# #so first create a dataframe out of missing_index_values1
# missing_index_values1_df = user_input.reindex(missing_index_values1)
# #now look for patterns in the missing_index_values1_df
# missing_index_values1_df.reset_index().groupby(['Measure', 'Vehicle Type', 'Medium', 'Transport Type', 'Drive', 'Scenario']).count().sort_values(by='Year', ascending=False)
# #it seems like we're missing all sorts of rows. So we will have to add them back in, set them and replace the data in the original spreadsheet. 





# # #%%
# ##TEMP FIX
# Vehicle_sales_share = pd.read_excel('input_data/user_input_spreadsheet.xlsx', sheet_name='Vehicle_sales_share')

# Turnover_rate_growth = pd.read_excel('input_data/user_input_spreadsheet.xlsx', sheet_name='Turnover_rate_growth')

# OccupanceAndLoad_growth = pd.read_excel('input_data/user_input_spreadsheet.xlsx', sheet_name='OccupanceAndLoad_growth')

# New_vehicle_efficiency_growth = pd.read_excel('input_data/user_input_spreadsheet.xlsx', sheet_name='New_vehicle_efficiency_growth')

# non_road_efficiency_growth = pd.read_excel('input_data/user_input_spreadsheet.xlsx', sheet_name='non_road_efficiency_growth')

# # OccupanceAndLoad_growth are not split by Drive because they dont need to be. But it will be easier to understand the code if they are. So we will merge on the drive column from the Vehicle_sales_share data set using the vehicle type as the key and an outer join
# OccupanceAndLoad_growth = OccupanceAndLoad_growth.merge(Vehicle_sales_share[['Vehicle Type', 'Drive']].drop_duplicates(), on='Vehicle Type', how='inner')

# #fill in the medium column in all user input data sets
# #create mapping between vehicle type and medium from the concordance table and use that to set medium in user input
# #first create a mapping
# vehicle_type_to_medium_mapping = model_concordances_user_input_and_growth_rates[['Vehicle Type', 'Medium']].drop_duplicates().set_index('Vehicle Type').to_dict()['Medium']
# #then use that mapping to set medium in user input
# Vehicle_sales_share['Medium'] = Vehicle_sales_share['Vehicle Type'].map(vehicle_type_to_medium_mapping)
# Turnover_rate_growth['Medium']  = Turnover_rate_growth['Vehicle Type'].map(vehicle_type_to_medium_mapping)
# New_vehicle_efficiency_growth['Medium']  = New_vehicle_efficiency_growth['Vehicle Type'].map(vehicle_type_to_medium_mapping)
# non_road_efficiency_growth['Medium']  = non_road_efficiency_growth['Vehicle Type'].map(vehicle_type_to_medium_mapping)
# OccupanceAndLoad_growth['Medium']  = OccupanceAndLoad_growth['Vehicle Type'].map(vehicle_type_to_medium_mapping)


# Vehicle_sales_share['Measure'] =  'Vehicle_sales_share'
# Turnover_rate_growth['Measure'] =  'Turnover_rate_growth'
# New_vehicle_efficiency_growth['Measure'] =  'New_vehicle_efficiency_growth'
# non_road_efficiency_growth['Measure'] =  'Non_road_efficiency_growth'
# OccupanceAndLoad_growth['Measure'] =  'Occupancy_or_load_growth'

# #make teh order of all the columns the same. it should go: Year	Economy		Medium	Transport Type	Vehicle Type	Drive Scenario	Value
# Vehicle_sales_share = Vehicle_sales_share[['Year', 'Economy', 'Medium', 'Transport Type', 'Vehicle Type', 'Drive', 'Scenario','Measure', 'Value']]
# Turnover_rate_growth = Turnover_rate_growth[['Year', 'Economy', 'Medium', 'Transport Type', 'Vehicle Type', 'Drive', 'Scenario', 'Measure','Value']]
# New_vehicle_efficiency_growth = New_vehicle_efficiency_growth[['Year', 'Economy', 'Medium', 'Transport Type', 'Vehicle Type', 'Drive', 'Scenario', 'Measure','Value']]
# non_road_efficiency_growth = non_road_efficiency_growth[['Year', 'Economy', 'Medium', 'Transport Type', 'Vehicle Type', 'Drive', 'Scenario', 'Measure','Value']]
# OccupanceAndLoad_growth = OccupanceAndLoad_growth[['Year', 'Economy', 'Medium', 'Transport Type', 'Vehicle Type', 'Drive', 'Scenario','Measure', 'Value']]

# # #%%
# #%%
# # save all the new data sets to the oringal excel file (with multiple sheets)
# write = pd.ExcelWriter('input_data/user_input_spreadsheet.xlsx', engine='xlsxwriter')
# Vehicle_sales_share.to_excel(write, sheet_name='Vehicle_sales_share', index=False)
# Turnover_rate_growth.to_excel(write, sheet_name='Turnover_rate_growth', index=False)
# New_vehicle_efficiency_growth.to_excel(write, sheet_name='New_vehicle_efficiency_growth', index=False)
# non_road_efficiency_growth.to_excel(write, sheet_name='non_road_efficiency_growth', index=False)
# OccupanceAndLoad_growth.to_excel(write, sheet_name='OccupanceAndLoad_growth', index=False)
# write.save()



#%%

# #join all together
# user_input = pd.concat([Vehicle_sales_share, Turnover_rate_growth, New_vehicle_efficiency_growth, non_road_efficiency_growth, OccupanceAndLoad_growth])


# #%%
# ##TEMP FIX
# Vehicle_sales_share = pd.read_excel('input_data/user_input_spreadsheet.xlsx', sheet_name='Vehicle_sales_share')

# Turnover_rate_growth = pd.read_excel('input_data/user_input_spreadsheet.xlsx', sheet_name='Turnover_rate_growth')

# OccupanceAndLoad_growth = pd.read_excel('input_data/user_input_spreadsheet.xlsx', sheet_name='OccupanceAndLoad_growth')

# New_vehicle_efficiency_growth = pd.read_excel('input_data/user_input_spreadsheet.xlsx', sheet_name='New_vehicle_efficiency_growth')

# non_road_efficiency_growth = pd.read_excel('input_data/user_input_spreadsheet.xlsx', sheet_name='non_road_efficiency_growth')

# #create a row for 2w in freight transport for all years. this will be the exact same row as the 2w in passenger transport but with transport type = freight
# #first create a copy of the 2w in passenger transport row
# two_wheeler_in_freight = Vehicle_sales_share[(Vehicle_sales_share['Vehicle Type'] == '2w') & (Vehicle_sales_share['Transport Type'] == 'passenger')].copy()
# #then change the transport type to freight
# two_wheeler_in_freight['Transport Type'] = 'freight'
# #then add it to the dataframe
# Vehicle_sales_share = Vehicle_sales_share.append(two_wheeler_in_freight, ignore_index=True)

# #now do that for every df
# #first create a copy of the 2w in passenger transport row
# two_wheeler_in_freight = Turnover_rate_growth[(Turnover_rate_growth['Vehicle Type'] == '2w') & (Turnover_rate_growth['Transport Type'] == 'passenger')].copy()
# #then change the transport type to freight
# two_wheeler_in_freight['Transport Type'] = 'freight'
# #then add it to the dataframe
# Turnover_rate_growth = Turnover_rate_growth.append(two_wheeler_in_freight, ignore_index=True)

# #now do that for every df
# #first create a copy of the 2w in passenger transport row
# two_wheeler_in_freight = OccupanceAndLoad_growth[(OccupanceAndLoad_growth['Vehicle Type'] == '2w') & (OccupanceAndLoad_growth['Transport Type'] == 'passenger')].copy()
# #then change the transport type to freight
# two_wheeler_in_freight['Transport Type'] = 'freight'
# #then add it to the dataframe
# OccupanceAndLoad_growth = OccupanceAndLoad_growth.append(two_wheeler_in_freight, ignore_index=True)

# #now do that for every df
# #first create a copy of the 2w in passenger transport row
# two_wheeler_in_freight = New_vehicle_efficiency_growth[(New_vehicle_efficiency_growth['Vehicle Type'] == '2w') & (New_vehicle_efficiency_growth['Transport Type'] == 'passenger')].copy()
# #then change the transport type to freight
# two_wheeler_in_freight['Transport Type'] = 'freight'
# #then add it to the dataframe
# New_vehicle_efficiency_growth = New_vehicle_efficiency_growth.append(two_wheeler_in_freight, ignore_index=True)

# # # save all the new data sets to the oringal excel file (with multiple sheets)
# write = pd.ExcelWriter('input_data/user_input_spreadsheet.xlsx', engine='xlsxwriter')
# Vehicle_sales_share.to_excel(write, sheet_name='Vehicle_sales_share', index=False)
# Turnover_rate_growth.to_excel(write, sheet_name='Turnover_rate_growth', index=False)
# New_vehicle_efficiency_growth.to_excel(write, sheet_name='New_vehicle_efficiency_growth', index=False)
# non_road_efficiency_growth.to_excel(write, sheet_name='non_road_efficiency_growth', index=False)
# OccupanceAndLoad_growth.to_excel(write, sheet_name='OccupanceAndLoad_growth', index=False)
# write.save()


# # # %%
# OccupanceAndLoad_growth = pd.read_excel('input_data/user_input_spreadsheet.xlsx', sheet_name='OccupanceAndLoad_growth')
# #remove duplicates
# OccupanceAndLoad_growth = OccupanceAndLoad_growth.drop_duplicates()
# #save
# write = pd.ExcelWriter('input_data/user_input_spreadsheet.xlsx', engine='xlsxwriter')
# OccupanceAndLoad_growth.to_excel(write, sheet_name='OccupanceAndLoad_growth', index=False)
# write.save()
# #%%
# #check for duplocates
# OccupanceAndLoad_growth[OccupanceAndLoad_growth.duplicated()]
# # %%
