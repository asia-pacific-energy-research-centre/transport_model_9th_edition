#this will apply any fuel mixing on the supply side. This is currently only biofuel mixing but could include other fuel types in the future

#this will merge a fuel sharing dataframe onto the model output, by the fuel column, and apply the shares by doing that. There will be a new fuel column after this
#%%

#set working directory as one folder back so that config works
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
from runpy import run_path
exec(open("config/config.py").read())#usae this to load libraries and set variables. Feel free to edit that file as you need
#%%
def apply_fuel_mix_supply_side(PROJECT_TO_JUST_OUTLOOK_BASE_YEAR=False,ADVANCE_BASE_YEAR=False):
    # breakpoint()
    # model_output_file_name = 'model_output_years_2017_to_2050_DATE20220824_1043.csv'
    #load user input for fuel mixing
    if ADVANCE_BASE_YEAR:
        supply_side_fuel_mixing = pd.read_csv('intermediate_data\model_inputs\supply_side_fuel_mixing_COMPGEN_base_year_adv.csv')#necessary so we dont have to re run supply side fuel mixing creation scripts every time we adjust it
    else:
        supply_side_fuel_mixing = pd.read_csv('intermediate_data\model_inputs\supply_side_fuel_mixing_COMPGEN.csv')

    model_output = pd.read_csv('intermediate_data/model_output_with_fuels/1_demand_side/{}'.format(model_output_file_name))

    if PROJECT_TO_JUST_OUTLOOK_BASE_YEAR:
        supply_side_fuel_mixing = supply_side_fuel_mixing[supply_side_fuel_mixing['Date'] <= OUTLOOK_BASE_YEAR]
        model_output = model_output[model_output['Date'] <= OUTLOOK_BASE_YEAR]
    
    BASE_YEAR_x = BASE_YEAR
    if ADVANCE_BASE_YEAR:
        BASE_YEAR_x = OUTLOOK_BASE_YEAR
    
    #to deal with historical data that may or may not have been included, jsut assume the same fuel mix as the base year for all previous years.
    supply_side_fuel_mixing_historical = supply_side_fuel_mixing[supply_side_fuel_mixing['Date'] == BASE_YEAR_x]
    # Get the unique years in model_output that are before the BASE_YEAR
    unique_years_less_than_base = model_output[model_output['Date'] < BASE_YEAR_x]['Date'].unique()
    #drop those years from the supply side fuel mixing
    supply_side_fuel_mixing = supply_side_fuel_mixing[supply_side_fuel_mixing['Date'] >= BASE_YEAR_x]

    # Initialize an empty DataFrame
    supply_side_fuel_mixing_historical_all_years = pd.DataFrame()

    # Loop over the unique years less than the base year
    for year in unique_years_less_than_base:
        # Copy the supply_side_fuel_mixing_historical DataFrame
        df_copy = supply_side_fuel_mixing_historical.copy()
        # Assign the current year to the 'Date' column
        df_copy['Date'] = year
        # concat the DataFrame copy to the overall DataFrame
        supply_side_fuel_mixing_historical_all_years = pd.concat([supply_side_fuel_mixing_historical_all_years, df_copy])

    # Reset the index of the overall DataFrame
    supply_side_fuel_mixing_historical_all_years.reset_index(drop=True, inplace=True)

    #concatenate the historical fuel mixing with the supply_side_fuel_mixing
    supply_side_fuel_mixing = pd.concat([supply_side_fuel_mixing_historical_all_years, supply_side_fuel_mixing], axis=0)
    
    #merge the supply side fuel mixing data on the fuel column. This will result in a new supply side fuel column which reflects the splitting of the fuel into many types. We will replace the value in the fuel column with the value in the supply side fuel column, and times the energy value by the share. and Where the suply side fuel column contains no value (an NA) then the fuel and its energy use will be unchanged.
    df_with_new_fuels = model_output.merge(supply_side_fuel_mixing, on=['Scenario', 'Economy', 'Transport Type', 'Medium', 'Vehicle Type', 'Drive', 'Fuel', 'Date','Frequency'], how='left')

    # #filter for where ecnomy is 08_JPN, vehicle type is car, drive is ice_d and fuel is 07_01_motor_gasoline and year is 2030
    # test = df_with_new_fuels[(df_with_new_fuels['Economy'] == '08_JPN') & (df_with_new_fuels['Vehicle Type'] == 'car') & (df_with_new_fuels['Drive'] == 'ice_g') & (df_with_new_fuels['Fuel'] == '07_01_motor_gasoline') & (df_with_new_fuels['Date'] == 2030)]
    
    #remove rows where New Fuel is nan
    df_with_new_fuels = df_with_new_fuels[df_with_new_fuels['New_fuel'].notna()]
    
    df_with_new_fuels['Energy'] = df_with_new_fuels['Energy'] * df_with_new_fuels['Supply_side_fuel_share']

    #now we will have the amount of each new fuel type being used. To find the remainign use of the original fuel we will minus the eegy of the new fuels from the original fuel. However, since some original fuels will ahve been mixed with more than one new fuel, we will need to pivot the new fuels out so that we can minus them from the original fuel, all within the same row. Then later jsut concat the rows back together.
    df_with_new_fuels_wide = df_with_new_fuels.pivot_table(index=['Scenario', 'Economy', 'Transport Type', 'Medium', 'Vehicle Type', 'Drive', 'Fuel', 'Date','Frequency'], columns='New_fuel', values='Energy').reset_index()
    #get the new columns names, they will jsut be the unique values in the new fuel column
    new_fuels_cols = df_with_new_fuels.New_fuel.unique().tolist()
    #set any nas to 0 in new_fuels_cols
    df_with_new_fuels_wide[new_fuels_cols] = df_with_new_fuels_wide[new_fuels_cols].fillna(0)
    # breakpoint()
    #drop cols except new_fuels_cols and the index cols
    df_with_new_fuels_wide = df_with_new_fuels_wide[['Scenario', 'Economy', 'Transport Type', 'Medium', 'Vehicle Type', 'Drive', 'Fuel', 'Date','Frequency'] + new_fuels_cols]
    
    #join the new fuel columns back to the original dataframe
    df_with_old_fuels = model_output.merge(df_with_new_fuels_wide, on=['Scenario', 'Economy', 'Transport Type', 'Medium', 'Vehicle Type', 'Drive', 'Fuel', 'Date','Frequency'], how='left')
    
    #minus the New fuels from the energy to get the original fuels energy use. can use new_fuels_cols as the columns to minus
    df_with_old_fuels['Energy'] = df_with_old_fuels['Energy'] - df_with_old_fuels[new_fuels_cols].sum(axis=1)
    
    #drop those cols
    df_with_old_fuels = df_with_old_fuels.drop(new_fuels_cols, axis=1)
    
    #concat the two dataframes back together
    #first edit df_with_new_fuels a bit
    df_with_new_fuels['Fuel'] = df_with_new_fuels['New_fuel']
    df_with_new_fuels.drop(['New_fuel', 'Supply_side_fuel_share'], axis=1, inplace=True)
    df_with_all_fuels  = pd.concat([df_with_old_fuels, df_with_new_fuels], axis=0)
    breakpoint()
    
    #save data
    df_with_all_fuels.to_csv('intermediate_data/model_output_with_fuels/2_supply_side/{}'.format(model_output_file_name), index=False)

    
#%%
# apply_fuel_mix_supply_side()
#%%
# # a = pd.read_csv('intermediate_data/model_output_with_fuels/2_supply_side/{}'.format(model_output_file_name))
# # #check for dupklicates:
# # dupes = a[a.duplicated()].copy()
# # # dupes2 = a[a.duplicated(subset=['Date', 'Economy', 'Scenario', 'Transport Type', 'Vehicle Type','Drive', 'Medium', 'Fuel'], keep=False)].copy()
#  a = pd.read_csv('intermediate_data/model_output_with_fuels/1_demand_side/{}'.format(model_output_file_name))
#  dupes2 = a[a.duplicated(subset=['Date', 'Economy', 'Scenario', 'Transport Type', 'Vehicle Type','Drive', 'Medium', 'Fuel'], keep=False)].copy()
#  dupes = a[a.duplicated()].copy()
# # d = df_with_new_fuels[df_with_new_fuels .duplicated(subset=['Date', 'Economy', 'Scenario', 'Transport Type', 'Vehicle Type','Drive', 'Medium', 'Fuel', 'New_fuel'], keep=False)].copy()