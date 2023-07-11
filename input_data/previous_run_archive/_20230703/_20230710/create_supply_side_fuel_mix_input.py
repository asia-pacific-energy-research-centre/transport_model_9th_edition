#this will apply any fuel mixing on the supply side. This is currently only biofuel mixing to petroleum products but could include other fuel types in the future

#this will merge a fuel sharing dataframe onto the model output, by the fuel column, and apply the shares by doing that. There will be a new fuel column after this

#%%
# FILE_DATE_ID='_20230615'
#set working directory as one folder back so that config works
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
from runpy import run_path
exec(open("config/config.py").read())#usae this to load libraries and set variables. Feel free to edit that file as you need
import sys
sys.path.append("./config/utilities")
import archiving_scripts
import user_input_creation_functions

sys.path.append("./workflow/plotting")
import plot_user_input_data
#%%
#create fake user input for demand side fuel mixes using model concordances
def create_supply_side_fuel_mixing_input():
        
    # #load model concordances
    # supply_side_fuel_mixing = pd.read_csv('config/concordances_and_config_data/computer_generated_concordances/{}'.format(supply_side_fuel_mixing_file_name_fuels))

    #take in demand side fuel mixes
    demand_side_fuel_mixing = pd.read_csv('intermediate_data\model_inputs\demand_side_fuel_mixing_COMPGEN.csv')

    #take in fuel mixing assumptions and prepare them

    #extract dictionary from csv
    #for later, load in vehicle_type_growth_regions sheet and vehicle_type_growth sheet
    mixing_assumptions = pd.read_excel('input_data/fuel_mixing_assumptions.xlsx',sheet_name='supply_side')
    #cols Region	Fuel	New_fuel	Date	Reference	Target

    regions = pd.read_excel('input_data/fuel_mixing_assumptions.xlsx',sheet_name='regions')

    #####################################
    #TEST
    #check the regions in regions_passenger and regions_freight are the same as in passenger_drive_shares and freight_drive_shares, also check that the regions in vehicle_type_growth_regions are the same as in vehicle_type_growth
    user_input_creation_functions.check_region(regions, mixing_assumptions)
    
    #####################################
    #convert regions to economys
    mixing_assumptions = pd.merge(mixing_assumptions, regions, how='left', on='Region')
    #check for any nas, which will be caused by regions not being in the regions sheet:
    if mixing_assumptions.Region.isna().any():
        #get the regions that are not in the regions sheet
        missing_region = mixing_assumptions.Region[mixing_assumptions.Region.isna()].unique().tolist()
        raise ValueError('The following regions are not in the regions sheet for fuel mixing on supply side: {}'.format(missing_region))
    #drop region
    mixing_assumptions.drop(columns=['Region'], inplace=True)

    #melt so Scenario is a column
    mixing_assumptions = pd.melt(mixing_assumptions, id_vars=['Economy', 'Fuel', 'New_fuel', 'Date'], var_name='Scenario', value_name='Supply_side_fuel_share')
    #drop nas
    mixing_assumptions.dropna(inplace=True)
    mixing_assumptions.drop_duplicates(inplace=True)

    #Start filling in fuel mixing using the demand side fuel mixes to start with
    supply_side_fuel_mixing = demand_side_fuel_mixing.copy()
    #drop Demand_side_fuel_share column
    supply_side_fuel_mixing = supply_side_fuel_mixing.drop(columns=['Demand_side_fuel_share']).drop_duplicates()

    # #join on the fuel mixing assumptions
    # supply_side_fuel_mixing_old = supply_side_fuel_mixing.copy()
    # old_cols = supply_side_fuel_mixing_old.columns.tolist()

    #first join so we have the New Fuels col, non dependent of Date
    supply_side_fuel_mixing = pd.merge(supply_side_fuel_mixing, mixing_assumptions[['Economy', 'Fuel', 'New_fuel', 'Scenario']], how='inner', on=['Economy', 'Fuel', 'Scenario']).drop_duplicates()

    supply_side_fuel_mixing_intermediate = supply_side_fuel_mixing.copy()
    
    #then join so we have the Supply Side fuel share col, so join on the Date
    supply_side_fuel_mixing = pd.merge(supply_side_fuel_mixing, mixing_assumptions, how='left', on=['Economy', 'Fuel', 'Date', 'New_fuel','Scenario'])

    cols = supply_side_fuel_mixing.columns.tolist()
    cols.remove('Supply_side_fuel_share')

    #now we need to fill in missing dates. we will interpolate between the first and last date for each economy and fuel type

    # #first join on the missing dates by doing another merge. but we also need to remove uneccessary rows before we do this:
    # dates = supply_side_fuel_mixing_intermediate[cols].drop_duplicates()
    # dates = dates.merge(mixing_assumptions[['Economy', 'Fuel', 'Scenario','New_fuel']].drop_duplicates(), how='inner', on=['Economy', 'Fuel', 'Scenario','New_fuel'])
    # #now we have the missing dates, we can join them to the supply side fuel mixing
    # supply_side_fuel_mixing = pd.merge(supply_side_fuel_mixing, dates, how='outer', on=cols)

    #now sort by economy, fuel,New_fuel, scenario, date and fill Supply_side_fuel_share using an interpoaltion and a bfill
    supply_side_fuel_mixing.sort_values(by=cols, inplace=True)

    #backfill on earliest date so we have something to start with. So make sure to bfill only the data before the earliest avialable date is missing
    #earliest dates:
    cols_no_date = cols.copy()
    cols_no_date.remove('Date')
    earliest_dates = supply_side_fuel_mixing.dropna(subset=['Supply_side_fuel_share']).groupby(cols_no_date)['Date'].min().reset_index()
    #create a col called earliest date
    earliest_dates.rename(columns={'Date':'Earliest_date'}, inplace=True)
    #join and then filter for where Date is less than Earliest_date
    supply_side_fuel_mixing_earliest_dates = pd.merge(supply_side_fuel_mixing, earliest_dates, how='left', on=cols_no_date)
    supply_side_fuel_mixing_earliest_dates = supply_side_fuel_mixing_earliest_dates[supply_side_fuel_mixing_earliest_dates['Date'] <= supply_side_fuel_mixing_earliest_dates['Earliest_date']]
    #now backfill
    supply_side_fuel_mixing_earliest_dates['Supply_side_fuel_share'] = supply_side_fuel_mixing_earliest_dates.groupby(cols_no_date)['Supply_side_fuel_share'].fillna(method='bfill')
    #drop Earliest_date
    supply_side_fuel_mixing_earliest_dates.drop(columns=['Earliest_date'], inplace=True)
    
    #set index of both supply_side_fuel_mixing and supply_side_fuel_mixing_earliest_dates to be based on the cols list, rather than the default index, so we can compare them directly
    supply_side_fuel_mixing.set_index(cols, inplace=True)
    supply_side_fuel_mixing_earliest_dates.set_index(cols, inplace=True)
    
    supply_side_fuel_mixing.drop(supply_side_fuel_mixing_earliest_dates.index, inplace=True)
    
    #reset index for both
    supply_side_fuel_mixing.reset_index(inplace=True)
    supply_side_fuel_mixing_earliest_dates.reset_index(inplace=True)
    
    supply_side_fuel_mixing = pd.concat([supply_side_fuel_mixing_earliest_dates, supply_side_fuel_mixing], axis=0)
    
    #do interpolation using spline adn order = X
    
    supply_side_fuel_mixing.sort_values(by=cols, inplace=True)
    
    #use linear
    # supply_side_fuel_mixing['Supply_side_fuel_share'] = supply_side_fuel_mixing.groupby(cols_no_date)['Supply_side_fuel_share'].apply(lambda group: group.interpolate(method='linear'))
    
    #for some reason when we do the itnerpolation by group iteration it works. so we'll jsut do that for now:
    new_supply_side_fuel_mixing = pd.DataFrame()
    for group in supply_side_fuel_mixing.groupby(cols_no_date):
        supply_side_fuel_mixing_e = group[1].copy()
        
        supply_side_fuel_mixing_e['Supply_side_fuel_share'] = supply_side_fuel_mixing_e.groupby(cols_no_date)['Supply_side_fuel_share'].apply(lambda group: group.interpolate(method='linear'))#, order=X_order))
        
        new_supply_side_fuel_mixing = pd.concat([new_supply_side_fuel_mixing, supply_side_fuel_mixing_e], axis=0)
    
    supply_side_fuel_mixing = new_supply_side_fuel_mixing.copy()
    
    #archive previous results:
    archiving_folder = archiving_scripts.create_archiving_folder_for_FILE_DATE_ID(FILE_DATE_ID)
    #save previous datra
    shutil.copy('intermediate_data\model_inputs\supply_side_fuel_mixing_COMPGEN.csv', archiving_folder + '/supply_side_fuel_mixing_COMPGEN.csv')
    #save the variables we used to calculate the data by savinbg the 'input_data/vehicle_sales_share_inputs.xlsx' file
    shutil.copy('input_data/fuel_mixing_assumptions.xlsx', archiving_folder + '/fuel_mixing_assumptions.xlsx')

    #save as user input csv
    supply_side_fuel_mixing.to_csv('intermediate_data\model_inputs\supply_side_fuel_mixing_COMPGEN.csv', index=False)
    
    plot_user_input_data.plot_supply_side_fuel_mixing(supply_side_fuel_mixing)
    
#%%
# create_supply_side_fuel_mixing_input()
#%%

#%%







# #####################################
# #PREPARE INPUT DATA
# #####################################

# #first we need to separate the sales share of vehicle types from the sales share of drives, by transport type. Since the way the values were created was simply mutliplication, we can jsut reverse that, i think.
# #so sum by vehicle type to get the total sales share of each vehicle type
# #then if we divide this by the final sales share values for each v-type/drive we can recreate the shares by drive type, witihin each vehicle type.
# #now for shares by drive type, witihin each vehicle type, we can create the shares we want.
# #sum by vtype economy year and scenario
# new_sales_shares_sum = sales.copy()

# #sum all up in case we have multiple rows for the same economy, vehicle type, drive type, transport type and date
# new_sales_shares_sum = new_sales_shares_sum.groupby(['Economy', 'Scenario', 'Vehicle Type', 'Transport Type','Drive', 'Date']).sum().reset_index()
    
# #now doulbe check we have therequired categories that are in the concordances
# model_concordances_user_input_and_growth_rates = pd.read_csv('config/concordances_and_config_data/computer_generated_concordances/{}'.format(model_concordances_user_input_and_growth_rates_file_name))
# #drop all measures that are not vehicle sales share
# model_concordances_user_input_and_growth_rates = model_concordances_user_input_and_growth_rates[model_concordances_user_input_and_growth_rates['Measure']=='Vehicle_sales_share']
# #drop any cols not in the new_sales_shares_sum
# cols = [col for col in model_concordances_user_input_and_growth_rates.columns if col in new_sales_shares_sum.columns]
# model_concordances_user_input_and_growth_rates = model_concordances_user_input_and_growth_rates[cols]
# model_concordances_user_input_and_growth_rates.drop_duplicates(inplace=True)
# INDEX_COLS = [col for col in INDEX_COLS if col in model_concordances_user_input_and_growth_rates.columns]

# #add BASE YEAR to the concordances which canb be a copy of the BASE_YEAR +1
# model_concordances_user_input_and_growth_rates_base = model_concordances_user_input_and_growth_rates.loc[model_concordances_user_input_and_growth_rates['Date']==BASE_YEAR+1].copy()
# model_concordances_user_input_and_growth_rates_base['Date'] = BASE_YEAR
# model_concordances_user_input_and_growth_rates = pd.concat([model_concordances_user_input_and_growth_rates,model_concordances_user_input_and_growth_rates_base])

# #set index for both dfs
# new_sales_shares_sum.set_index(INDEX_COLS, inplace=True)
# model_concordances_user_input_and_growth_rates.set_index(INDEX_COLS, inplace=True)

# # use the difference method to find:
# #missing_index_values1 :  the index values that are missing from the new_sales_shares_sum 
# # #missing_index_values2 : and also the index values that are present in the new_sales_shares_sum but not in the concordance 
# # this method is a lot faster than looping through each index row in the concordance and checking if it is in the new_sales_shares_sum
# missing_index_values1 = model_concordances_user_input_and_growth_rates.index.difference(new_sales_shares_sum.index)
# missing_index_values2 = new_sales_shares_sum.index.difference(model_concordances_user_input_and_growth_rates.index)

# if missing_index_values1.empty:
#     print('All rows are present in the user input')
# else:
#     #add these rows to the new_sales_shares_sum and set them to row_and_data_not_available
#     missing_index_values1 = pd.DataFrame(index=missing_index_values1).reset_index()
#     missing_index_values1['Value'] = np.nan
#     #then append to transport_data_system_df
#     new_sales_shares_sum = new_sales_shares_sum.reset_index()
#     new_sales_shares_sum = pd.concat([missing_index_values1, new_sales_shares_sum], sort=False)
#     print('Missing rows in our user input dataset when we compare it to the concordance:', missing_index_values1)
#     new_sales_shares_sum.set_index(INDEX_COLS, inplace=True)

# if missing_index_values2.empty:
#     pass#this is to be expected as the cocnordance should always have everything we need in it!
# else:
#     #we want to make sure user is aware of this as we will be removing rows from the user input
#     #remove these rows from the new_sales_shares_sum
#     new_sales_shares_sum.drop(missing_index_values2, inplace=True)
#     #convert missing_index_values to df
#     missing_index_values2 = pd.DataFrame(index=missing_index_values2).reset_index()
#     print('Missing rows in the user input concordance: {}'.format(missing_index_values2))
#     print('We will remove these rows from the user input dataset. If you intended to have data for these rows, please add them to the concordance table.')

#     # #print the unique Vehicle types and drives that are missing
#     # print('Unique Vehicle types and drives that are missing: {}'.format(missing_index_values2[['Vehicle Type', 'Drive']].drop_duplicates()))#as of /4 we ha

# #replace all nan values with 0 now
# # new_sales_shares_sum.fillna(0, inplace=True)

# #reset index
# new_sales_shares_sum.reset_index(inplace=True)





# %%
