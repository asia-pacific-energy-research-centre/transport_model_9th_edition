#this is intended to be where all data that is used in the model is cleaned before being adjusted to be used in the model.

#CLEANING IS anything that involves changing the format of the data. The next step is filling in missing values. 

#set working directory as one folder back so that config works
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
from runpy import run_path
exec(open("config/config.py").read())#usae this to load libraries and set variables. Feel free to edit that file as you need
import sys

sys.path.append("./config/utilities")
import archiving_scripts
sys.path.append("./workflow/create_user_inputs")
from create_vehicle_sales_share_data import create_vehicle_sales_share_input

# data_available
def create_and_clean_user_input():
    
    ######################################################################################################
    #laod concordances for checking later
    model_concordances_user_input_and_growth_rates = pd.read_csv('config/concordances_and_config_data/computer_generated_concordances/{}'.format(model_concordances_user_input_and_growth_rates_file_name))

    if NEW_SALES_SHARES:
        create_vehicle_sales_share_input(INDEX_COLS,SCENARIOS_LIST)

    if NEW_FUEL_MIXING_DATA:
        #note that this wont be saved to user input, as it has a different data structure.
        import create_demand_side_fuel_mix_input
        import concordance_scripts
        import create_supply_side_fuel_mix_input

        create_demand_side_fuel_mix_input.create_demand_side_fuel_mixing_input()
        create_supply_side_fuel_mix_input.create_supply_side_fuel_mixing_input()
        concordance_scripts.create_fuel_mixing_concordances()
    
    #first, prepare user input 
    #load these files in and concat them
    user_input = pd.DataFrame()
    print(f'There are {len(os.listdir("input_data/user_input_spreadsheets"))} user input files to import')
    for file in os.listdir('input_data/user_input_spreadsheets'):
        #check its a csv
        if file[-4:] != '.csv':
            continue
        print('Importing user input file: {}'.format(file))
        user_input = pd.concat([user_input, pd.read_csv('input_data/user_input_spreadsheets/{}'.format(file))])
    
    #print then remove any measures not in model_concordances_user_input_and_growth_rates
    print('Measures in user input that are not in the model concordances:', user_input[~user_input.Measure.isin(model_concordances_user_input_and_growth_rates.Measure)].Measure.unique())
    user_input = user_input[user_input.Measure.isin(model_concordances_user_input_and_growth_rates.Measure)]

    
    ################################################################################

    
    #drop any rows in user input that are for the base year (why? i geuss there arent any base year values in the user inputanyway, but could be useful not to rmeove them ?)
    user_input = user_input[user_input.Date != BASE_YEAR]
    
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

    
    # use the difference method to find:
    #missing_index_values1 :  the index values that are missing from the user_input 
    #missing_index_values2 : and also the index values that are present in the user_input but not in the concordance 
    # # this is a lot faster than looping through each index row in the concordance and checking if it is in the user_input
    missing_index_values1 = model_concordances_user_input_and_growth_rates.index.difference(user_input.index)
    missing_index_values2 = user_input.index.difference(model_concordances_user_input_and_growth_rates.index)

    if missing_index_values1.empty:
        print('All rows are present in the user input')
    else:
        #add these rows to the user_input and set them to row_and_data_not_available
        missing_index_values1 = pd.DataFrame(index=missing_index_values1).reset_index()
        missing_index_values1['Data_available'] = 'row_and_data_not_available'
        missing_index_values1['Value'] = np.nan
        #then append to transport_data_system_df
        user_input = user_input.reset_index()
        user_input = pd.concat([missing_index_values1, user_input], sort=False)
        print('Missing rows in our user input dataset when we compare it to the concordance:', missing_index_values1)
        user_input.set_index(INDEX_COLS, inplace=True)

    
    if missing_index_values2.empty:
        pass#this is to be expected as the cocnordance should always have everything we need in it!
    else:
        #we want to make sure user is aware of this as we will be removing rows from the user input
        #remove these rows from the user_input
        user_input.drop(missing_index_values2, inplace=True)
        #convert missing_index_values to df
        missing_index_values2 = pd.DataFrame(index=missing_index_values2).reset_index()
        print('Missing rows in the user input concordance: {}'.format(missing_index_values2))
        print('We will remove these rows from the user input dataset. If you intended to have data for these rows, please add them to the concordance table.')

        # #print the unique Vehicle types and drives that are missing
        # print('Unique Vehicle types and drives that are missing: {}'.format(missing_index_values2[['Vehicle Type', 'Drive']].drop_duplicates()))#as of /4 we ha




    
    user_input = user_input.reset_index()
    
    # # a= user_input.copy()
    # user_input = a.copy()
    
    #we may be missing user inputs because the END_YEAR was extended. So just fill in missing values with the last available value when grouping by the index cols
    #so first insert all the missing years
    #make sure to print strong wanrings so the user is aware that they could be filling in missing data where it should be missing
    #also, jsut to be safe, only do thisstep if the missing data is for years greater than 2050
    if (user_input[user_input.Data_available == 'row_and_data_not_available'].Date.max() > 2050) or (user_input[user_input.Data_available == 'data_not_available'].Date.max() > 2050):
        print('WARNING: You are filling in missing data for years greater than 2050. Please check that this is what you want to do.')
        #check that where Value is NA that Data_available is row_and_data_not_available or data_not_available for all cases
        if len(user_input[(user_input.Value.isna()) & ((user_input.Data_available != 'row_and_data_not_available') & (user_input.Data_available != 'data_not_available'))]) >0:
            #raise error if this is not the case
            raise ValueError('There are some rows where Value is NA but Data_available is not row_and_data_not_available or data_not_available. Please check this.')
        #and check the opposite, i.e. that where Data_available is row_and_data_not_available or data_not_available that Value is NA
        if len(user_input[(user_input.Value.notna()) & ((user_input.Data_available == 'row_and_data_not_available') | (user_input.Data_available == 'data_not_available'))]) >0:
            #raise error if this is not the case
            raise ValueError('There are some rows where Value is not NA but Data_available is row_and_data_not_available or data_not_available. Please check this.')
        #create new df that contains dates that are less than 2050 and the values are NA
        user_input_missing_values_dont_change = user_input.loc[(user_input.Date <= 2050) & (user_input.Value.isna())]

        #create new df that contains dates that are greater than 2050 and the values are NA
        user_input_missing_values_change = user_input.loc[~((user_input.Date <= 2050) & (user_input.Value.isna()))]

        # first sort by date
        user_input_missing_values_change.sort_values('Date', inplace=True)

        # now ffill na on Value col when grouping by the index cols
        user_input_missing_values_change['Value'] = user_input_missing_values_change.groupby(INDEX_COLS_no_date)['Value'].apply(lambda group: group.ffill())

        # reset index
        user_input_missing_values_change.reset_index(drop=True, inplace=True)

        #now concat the two dfs
        user_input_new = pd.concat([user_input_missing_values_dont_change, user_input_missing_values_change], sort=False)

        #check for nas and throw error if so. might need to utilise the commented out code below (that i didnt finish gettting working) to do this
        if len(user_input_new[user_input_new.Value.isna()]) >0:
            raise ValueError('There are still some rows where Value is NA. Please check this.')
        # #there will be soe cases where there are still nas because there are nas for every year in the group of INDEX_COLS_no_date. We will check for these cases and separate them for analysis. THen identify any extra cases where there are still nas in the Value col. these are problematic and we will raise an error
        # user_input_new_groups_with_all_nas = user_input_new.groupby(INDEX_COLS_no_date).apply(lambda group: group.isna().all()).reset_index()

        # #drop tehse rwos from the user_input_new so we can check for any other cases where there are still nas in the Value col:
        # user_input_new = user_input_new.loc[~user_input_new_groups_with_all_nas[0]]
        # #then identify the other cases where there are still nas in the Value col:
        # user_input_new_groups_with_nas_in_value = user_input_new.groupby(INDEX_COLS_no_date).apply(lambda group: group.Value.isna().any()).reset_index()
    else:
        user_input_new = user_input.copy()
    
    #resvae tehse values back to the user_input df, by measure
    #now save the sheet to the excel file
    save_progress=False
    if save_progress:
        file_date = datetime.datetime.now().strftime("%Y%m%d")
        FILE_DATE_ID_x = '_{}'.format(file_date)
        #save the original user_input_spreadsheet to the archive with the File date
        shutil.copy('input_data/user_input_spreadsheet.xlsx', 'input_data/archive/user_input_spreadsheet{}.xlsx'.format(FILE_DATE_ID_x))
        #remove the original user_input_spreadsheet
        os.remove('input_data/user_input_spreadsheet.xlsx')
        with pd.ExcelWriter('input_data/user_input_spreadsheet.xlsx') as writer:
            for sheet in user_input_new.Measure.unique():
                print('Saving user input sheet: {}'.format(sheet))
                sheet_data = user_input_new[user_input_new.Measure == sheet]
                sheet_data.to_excel(writer, sheet_name=sheet, index=False)

    
    #save the new_user_inputs
    user_input_new.to_csv('intermediate_data/{}_user_inputs_and_growth_rates.csv'.format(FILE_DATE_ID), index=False)


    













#%%
#edit user input vehicle types and drive because we ahve updated them,,. 
#however make sure to ignore vehicle sales share sheet

#for vehicle type:
#basically, where there is data for ldv passenger, replicate it twice and call it suv and car for each new set.
# then rename freight ldv to lcv
#replicated ht and call it mt
#for drive:
#replicate ice and call it ice_g and ice_d
#replicate phev and call it phev_g and phev_d
# def edit_user_input()
#     #first, prepare user input 
#     #load these files in and concat them
#     user_input = pd.DataFrame()
#     print(f'There are {len(os.listdir("input_data/user_input_spreadsheets"))} user input files to import')
#     for file in os.listdir('input_data/user_input_spreadsheets'):
#         #check its a csv
#         if file[-4:] != '.csv':
#             continue
#         if file == 'Vehicle_sales_share.csv':
#             continue
#         print('Importing user input file: {}'.format(file))
#         user_input = pd.read_csv('input_data/user_input_spreadsheets/{}'.format(file))

#         #now edit the vehicle type and drive cols
#         #for vehicle type:
#         #basically, where there is data for ldv passenger, replicate it twice and call it suv and car for each new set.
#         suv = user_input.loc[(user_input['Vehicle Type'] == 'ldv') & (user_input['Transport Type']=='passenger')].copy()
#         suv['Vehicle Type'] = 'suv'

#         car = user_input.loc[(user_input['Vehicle Type'] == 'ldv') & (user_input['Transport Type']=='passenger')].copy()
#         car['Vehicle Type'] = 'car'

#         lcv = user_input.loc[(user_input['Vehicle Type'] == 'ldv') & (user_input['Transport Type']=='freight')].copy()
#         lcv['Vehicle Type'] = 'lcv'

#         mt = user_input.loc[(user_input['Vehicle Type'] == 'ht')].copy()
#         mt['Vehicle Type'] = 'mt'

#         #now append these to the user_input
#         user_input = user_input.append([suv, car, lcv, mt], ignore_index=True)

#         #now edit the drive cols
#         #replicate ice and call it ice_g and ice_d
#         ice_g = user_input.loc[(user_input['Drive'] == 'ice')].copy()
#         ice_g['Drive'] = 'ice_g'
#         user_input.loc[(user_input['Drive'] == 'ice'), 'Drive'] = 'ice_d'

#         phev_g = user_input.loc[(user_input['Drive'] == 'phev')].copy()
#         phev_g['Drive'] = 'phev_g'
#         user_input.loc[(user_input['Drive'] == 'phev'), 'Drive'] = 'phev_d'

#         #now append these to the user_input
#         user_input = user_input.append([ice_g, phev_g], ignore_index=True)


#         #resave the user input
#         user_input.to_csv('input_data/user_input_spreadsheets/{}'.format(file), index=False)
    #%%


# 
# run = False
# if run:
#     with pd.ExcelWriter('intermediate_data/cleaned_input_data/clean_user_input.xlsx') as writer: 
#         #save cleaned user input to intemediate file
#         Vehicle_sales_share.to_excel(writer, sheet_name='Vehicle_sales_share', index=False)
#         Turnover_rate_growth.to_excel(writer, sheet_name='Turnover_rate_growth', index=False)
#         New_vehicle_efficiency_growth.to_excel(writer, sheet_name='New_vehicle_efficiency_growth', index=False)
#         OccupanceAndLoad_growth.to_excel(writer, sheet_name='OccupanceAndLoad_growth', index=False)
#         non_road_efficiency_growth.to_excel(writer, sheet_name='non_road_efficiency_growth', index=False)
    


# 
# #create option to add missing rows to the user input spreadsheet
# #frist get the missing rows and then separate them by measure
# #then add those rows to each measures orgiianl data set with a vlaue of 1
# #and then save all the data sets to the original excel file again
# new_user_input = user_input.reindex(missing_index_values1).reset_index()

# #RESAVE
# new_user_input = user_input.copy()
# # #separate the new user input by measure
# Vehicle_sales_share_new = new_user_input.loc[new_user_input.Measure == 'Vehicle_sales_share']
# Turnover_rate_growth_new = new_user_input.loc[new_user_input.Measure == 'Turnover_rate_growth']
# New_vehicle_efficiency_growth_new = new_user_input.loc[new_user_input.Measure == 'New_vehicle_efficiency_growth']
# non_road_efficiency_growth_new = new_user_input.loc[new_user_input.Measure == 'Non_road_efficiency_growth']
# Occupance_growth_new = new_user_input.loc[new_user_input.Measure == 'Occupancy_growth']
# Load_growth_new = new_user_input.loc[new_user_input.Measure == 'Load_growth']


# # save all the new data sets to the oringal excel file (with multiple sheets)
# write = pd.ExcelWriter('input_data/user_input_spreadsheet.xlsx', engine='xlsxwriter')
# Vehicle_sales_share_new.to_excel(write, sheet_name='Vehicle_sales_share', index=False)
# Turnover_rate_growth_new.to_excel(write, sheet_name='Turnover_rate_growth', index=False)
# New_vehicle_efficiency_growth_new.to_excel(write, sheet_name='New_vehicle_efficiency_growth', index=False)
# non_road_efficiency_growth_new.to_excel(write, sheet_name='non_road_efficiency_growth', index=False)
# Occupance_growth_new.to_excel(write, sheet_name='Occupancy_growth', index=False)
# Load_growth_new.to_excel(write, sheet_name='Load_growth', index=False)
# write.save()



#DELETE IN 2023:


# 
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

# 
# #add to turnover rate growth
# Turnover_rate_growth = pd.concat([Turnover_rate_growth, missing_index_values1_df])

# # Vehicle_sales_share.to_excel('input_data/user_input_spreadsheet.xlsx', sheet_name='Vehicle_sales_share', index=False)
# # Turnover_rate_growth.to_excel('input_data/user_input_spreadsheet.xlsx', sheet_name='Turnover_rate_growth', index=False)
# # New_vehicle_efficiency_growth.to_excel('input_data/user_input_spreadsheet.xlsx', sheet_name='New_vehicle_efficiency_growth', index=False)
# # non_road_efficiency_growth.to_excel('input_data/user_input_spreadsheet.xlsx', sheet_name='non_road_efficiency_growth', index=False)
# # OccupanceAndLoad_growth.to_excel('input_data/user_input_spreadsheet.xlsx', sheet_name='OccupanceAndLoad_growth', index=False)




# 
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





# # 
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

# # 
# 
# # save all the new data sets to the oringal excel file (with multiple sheets)
# write = pd.ExcelWriter('input_data/user_input_spreadsheet.xlsx', engine='xlsxwriter')
# Vehicle_sales_share.to_excel(write, sheet_name='Vehicle_sales_share', index=False)
# Turnover_rate_growth.to_excel(write, sheet_name='Turnover_rate_growth', index=False)
# New_vehicle_efficiency_growth.to_excel(write, sheet_name='New_vehicle_efficiency_growth', index=False)
# non_road_efficiency_growth.to_excel(write, sheet_name='non_road_efficiency_growth', index=False)
# OccupanceAndLoad_growth.to_excel(write, sheet_name='OccupanceAndLoad_growth', index=False)
# write.save()





# #join all together
# user_input = pd.concat([Vehicle_sales_share, Turnover_rate_growth, New_vehicle_efficiency_growth, non_road_efficiency_growth, OccupanceAndLoad_growth])


# 
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


# # 
# OccupanceAndLoad_growth = pd.read_excel('input_data/user_input_spreadsheet.xlsx', sheet_name='OccupanceAndLoad_growth')
# #remove duplicates
# OccupanceAndLoad_growth = OccupanceAndLoad_growth.drop_duplicates()
# #save
# write = pd.ExcelWriter('input_data/user_input_spreadsheet.xlsx', engine='xlsxwriter')
# OccupanceAndLoad_growth.to_excel(write, sheet_name='OccupanceAndLoad_growth', index=False)
# write.save()
# 
# #check for duplocates
# OccupanceAndLoad_growth[OccupanceAndLoad_growth.duplicated()]
# 
