#this is intended to be where all data that is used in the model is cleaned before being adjusted to be used in the model.

#CLEANING IS anything that involves changing the format of the data. The next step is filling in missing values. 
#%%
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
#%%
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
    #we need intensity improvement for all new non road drive types. so filter for non road in user input then merge with the concordance table to get the new drive types, and replicate the intensity improvement for all. 
    
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
            #identify the rows where there are still nas in the Value col:
            user_input_new_nas = user_input_new[user_input_new.Value.isna()]
            #save them to csv
            user_input_new_nas.to_csv('intermediate_data/errors/user_input_new_nas.csv', index=False)
            breakpoint()
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
    user_input_new.to_csv('intermediate_data/model_inputs/user_inputs_and_growth_rates.csv', index=False)


    
#%%
create_and_clean_user_input()
#%%

