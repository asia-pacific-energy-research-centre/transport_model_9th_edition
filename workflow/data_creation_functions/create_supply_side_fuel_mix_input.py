#this will apply any fuel mixing on the supply side. This is currently only biofuel mixing to petroleum products but could include other fuel types in the future

#this will merge a fuel sharing dataframe onto the model output, by the fuel column, and apply the shares by doing that. There will be a new fuel column after this

#%%
###IMPORT GLOBAL VARIABLES FROM config.py
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
import sys
sys.path.append("./config")
import config
####Use this to load libraries and set variables. Feel free to edit that file as you need.
import user_input_creation_functions
sys.path.append("./workflow/plotting_functions")
import plot_user_input_data
#%%
#create fake user input for demand side fuel mixes using model concordances
def create_supply_side_fuel_mixing_input():
            
    #load model concordances with fuels
    model_concordances_fuels = pd.read_csv('config/concordances_and_config_data/computer_generated_concordances/{}'.format(config.model_concordances_file_name_fuels))
    
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
    supply_side_fuel_mixing = model_concordances_fuels.copy()
    #first join so we have the New Fuels col, non dependent of Date
    supply_side_fuel_mixing = pd.merge(supply_side_fuel_mixing, mixing_assumptions[['Economy', 'Fuel', 'New_fuel', 'Scenario']], how='inner', on=['Economy', 'Fuel', 'Scenario']).drop_duplicates()

    supply_side_fuel_mixing_intermediate = supply_side_fuel_mixing.copy()

    #then join so we have the Supply Side fuel share col, so join on the Date
    supply_side_fuel_mixing = pd.merge(supply_side_fuel_mixing, mixing_assumptions, how='left', on=['Economy', 'Fuel', 'Date', 'New_fuel','Scenario'])

    cols = supply_side_fuel_mixing.columns.tolist()
    cols.remove('Supply_side_fuel_share')

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

    #for some reason when we do the itnerpolation by group iteration it works. so we'll jsut do that for now:
    new_supply_side_fuel_mixing = pd.DataFrame()
    for group in supply_side_fuel_mixing.groupby(cols_no_date):
        supply_side_fuel_mixing_e = group[1].copy()
        
        supply_side_fuel_mixing_e['Supply_side_fuel_share'] = supply_side_fuel_mixing_e.groupby(cols_no_date,group_keys=False)['Supply_side_fuel_share'].apply(lambda group: group.interpolate(method='linear'))#, order=X_order))
        
        new_supply_side_fuel_mixing = pd.concat([new_supply_side_fuel_mixing, supply_side_fuel_mixing_e], axis=0)

    supply_side_fuel_mixing = new_supply_side_fuel_mixing.copy()

    #archive previous results:
    archiving_folder = archiving_scripts.create_archiving_folder_for_FILE_DATE_ID(config.FILE_DATE_ID)
    
    #save the variables we used to calculate the data by savinbg the 'input_data/vehicle_sales_share_inputs.xlsx' file
    shutil.copy('input_data/fuel_mixing_assumptions.xlsx', archiving_folder + '/fuel_mixing_assumptions.xlsx')

    #save as user input csv
    supply_side_fuel_mixing.to_csv('intermediate_data/model_inputs/{}/supply_side_fuel_mixing.csv'.format(config.FILE_DATE_ID), index=False)

    plot_user_input_data.plot_supply_side_fuel_mixing(supply_side_fuel_mixing)
    
