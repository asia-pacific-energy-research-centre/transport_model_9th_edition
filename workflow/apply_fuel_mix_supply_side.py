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
def apply_fuel_mix_supply_side():
    # model_output_file_name = 'model_output_years_2017_to_2050_DATE20220824_1043.csv'
    #load user input for fuel mixing
    supply_side_fuel_mixing = pd.read_csv('intermediate_data\model_inputs\supply_side_fuel_mixing_COMPGEN.csv')

    model_output = pd.read_csv('intermediate_data/model_output_with_fuels/1_demand_side/{}'.format(model_output_file_name))

    
    #to deal with historical data that may or may not have been included, jsut assume the same fuel mix as the base year for all previous years.
    supply_side_fuel_mixing_historical = supply_side_fuel_mixing[supply_side_fuel_mixing['Date'] == BASE_YEAR]
    # Get the unique years in model_output that are before the BASE_YEAR
    unique_years = model_output[model_output['Date'] < BASE_YEAR]['Date'].unique()

    # Initialize an empty DataFrame
    supply_side_fuel_mixing_historical_all_years = pd.DataFrame()

    # Loop over the unique years
    for year in unique_years:
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

    df_with_fuels = model_output.merge(supply_side_fuel_mixing, on=['Scenario', 'Economy', 'Transport Type', 'Medium', 'Vehicle Type', 'Drive', 'Fuel', 'Date','Frequency'], how='left')

    
    #replace the fuel column with the supply side fuel column if the supply side fuel column is not NA
    df_with_fuels['Fuel'] = np.where(df_with_fuels['New_fuel'].isna(), df_with_fuels['Fuel'], df_with_fuels['New_fuel'])
    #times the energy column by the supply side fuel share if the supply side fuel share is not NA
    df_with_fuels['Energy'] = np.where(df_with_fuels['Supply_side_fuel_share'].isna(), df_with_fuels['Energy'], df_with_fuels['Energy'] * df_with_fuels['Supply_side_fuel_share'])

    
    #remove the supply side fuel and supply side fuel share columns
    df_with_fuels = df_with_fuels.drop(['New_fuel', 'Supply_side_fuel_share'], axis=1)

    #sum up the energy by fuel since some casses will result in the same fuel being split into many fuels and there might be an intersection, for excample biofuels used in multiple drive types for the same vehjicle, eg. air
    df_with_fuels = df_with_fuels.groupby(['Scenario', 'Economy', 'Transport Type', 'Medium', 'Vehicle Type', 'Drive', 'Fuel', 'Date','Frequency']).sum().reset_index()
    breakpoint()
    #save data
    df_with_fuels.to_csv('intermediate_data/model_output_with_fuels/2_supply_side/{}'.format(model_output_file_name), index=False)

    
#%%
# apply_fuel_mix_supply_side()
#%%