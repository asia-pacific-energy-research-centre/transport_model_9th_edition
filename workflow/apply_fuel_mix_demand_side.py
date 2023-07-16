#TODO implement data coverage plotting for this and supply side fuel mixing

#this will apply any fuel mixing on the demand side. This is can include, the use of different fule types for each drive type, for example, electricity vs oil in phev's, or even treating rail as a drive type, and splitting demand into electricity, coal and dieel rpoprtions. 

#as such, this will merge a fuel mixing dataframe onto the model output, by the Drive column, and apply the shares by doing that, resulting in a fuel column.
#this means that the supply side fuel mixing needs to occur after this script, because it will be merging on the fuel column.
 
#%%
#set working directory as one folder back so that config works
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
from runpy import run_path
exec(open("config/config.py").read())#usae this to load libraries and set variables. Feel free to edit that file as you need
 #%%
def apply_fuel_mix_demand_side(filter_to_just_base_year=False):
    
    # model_output_file_name = 'model_output_years_2017_to_2050_DATE20220824_1043.csv'
    #load model output
    model_output = pd.read_csv('intermediate_data/model_output_concatenated/{}'.format(model_output_file_name))

    #load user input for fuel mixing 
    demand_side_fuel_mixing = pd.read_csv('intermediate_data\model_inputs\demand_side_fuel_mixing_COMPGEN.csv')
    #load model concordances with fuels
    model_concordances_fuels = pd.read_csv('config/concordances_and_config_data/computer_generated_concordances/{}'.format(model_concordances_file_name_fuels))
    
    supply_side_fuel_mixing_fuels =  pd.read_csv('intermediate_data\model_inputs\supply_side_fuel_mixing_COMPGEN.csv')['New_fuel'].unique().tolist()
    #drop supply_side_fuel_mixing_fuels from model_concordances_fuels
    model_concordances_fuels = model_concordances_fuels[~model_concordances_fuels['Fuel'].isin(supply_side_fuel_mixing_fuels)]
    
    if filter_to_just_base_year:
        #filter so the data is from OUTLOOK_BASE_YEAR and back
        demand_side_fuel_mixing = demand_side_fuel_mixing[demand_side_fuel_mixing['Date'] <= OUTLOOK_BASE_YEAR]
        model_concordances_fuels = model_concordances_fuels[model_concordances_fuels['Date'] <= OUTLOOK_BASE_YEAR]
        
        
    #to deal with historical data that may or may not have been included, jsut assume the same fuel mix as the base year for all previous years.
    demand_side_fuel_mixing_historical = demand_side_fuel_mixing[demand_side_fuel_mixing['Date'] == BASE_YEAR]
    # Get the unique years in model_output that are before the BASE_YEAR
    unique_years = model_output[model_output['Date'] < BASE_YEAR]['Date'].unique()

    # Initialize an empty DataFrame
    demand_side_fuel_mixing_historical_all_years = pd.DataFrame()

    # Loop over the unique years
    for year in unique_years:
        if year in demand_side_fuel_mixing['Date'].unique():
            continue
        # Copy the demand_side_fuel_mixing_historical DataFrame
        df_copy = demand_side_fuel_mixing_historical.copy()
        # Assign the current year to the 'Date' column
        df_copy['Date'] = year
        # concat the DataFrame copy to the overall DataFrame
        demand_side_fuel_mixing_historical_all_years = pd.concat([demand_side_fuel_mixing_historical_all_years, df_copy])

    # Reset the index of the overall DataFrame
    demand_side_fuel_mixing_historical_all_years.reset_index(drop=True, inplace=True)

    #concatenate the historical fuel mixing with the demand_side_fuel_mixing
    demand_side_fuel_mixing = pd.concat([demand_side_fuel_mixing_historical_all_years, demand_side_fuel_mixing], axis=0)
    
    #single out the rows for which we need to do demand side fuel mixing. they are the rows where there are two or more fuels for every  row when we join to model_concordances_fuels, that arent inserted via supply side fuel mixing either:
    
    # model_output = model_output.merge(model_concordances_fuels[['Fuel','Drive']].drop_duplicates(), on='Drive', how='left')


    # #drop any rows where there is only one fuel for that drive type
    # cols = model_output_to_mix.columns.tolist()
    # cols.remove('Fuel')    
    # model_output_to_mix = model_output_to_mix[model_output_to_mix.duplicated(cols, keep=False)]
    # breakpoint()
    #or jsut ifnd where the fdrive is in demand side fuel mixing. this may eb a temp fix but works for nwo
    
    model_output = model_output.merge(model_concordances_fuels[['Fuel','Drive']].drop_duplicates(), on='Drive', how='left')

    model_output_to_mix = model_output[model_output['Drive'].isin(demand_side_fuel_mixing['Drive'].unique().tolist())]
    # #and now drop those demand side fuel mixing rows from the model output
    model_output = model_output[~model_output['Drive'].isin(demand_side_fuel_mixing['Drive'].unique().tolist())]
    breakpoint()
    #join the fuel mixing data to the model output. This will result in a new fuel column. Note that there can be multiple fuels per drive, so this could also create new rows for each drive. 
    df_with_fuels = model_output_to_mix.merge(demand_side_fuel_mixing, on=['Scenario', 'Economy', 'Transport Type', 'Medium', 'Vehicle Type','Drive', 'Date','Fuel'], how='left')
    
    #identify any nas in Demand_side_fuel_share column. If so make the user add them to other_code\create_user_inputs\create_demand_side_fuel_mix_input.py.
    #this is because the user needs to specify what the fuel share is for each medium/vehicletype/drive type, and if it is not specified it will cause an error.
    
    if df_with_fuels['Demand_side_fuel_share'].isna().sum() > 0:
        breakpoint()
        print('There are {} rows with a missing fuel share. Please add them to other_code\create_user_inputs\create_demand_side_fuel_mix_input.py'.format(df_with_fuels['Demand_side_fuel_share'].isna().sum()))
        raise Exception('Missing fuel shares')
    
    #times teh fuel sahres by energy. This will result in a new energy value, reflecting the share of fuel used in each drive type.
    df_with_fuels['Energy'] = df_with_fuels['Energy'] * df_with_fuels['Demand_side_fuel_share']

    
    #remove the demand side fuel share column, as it is no longer needed
    df_with_fuels = df_with_fuels.drop(columns=['Demand_side_fuel_share'])
    breakpoint()
    
    new_df_with_fuels = pd.concat([df_with_fuels, model_output], axis=0)
    #save data
    new_df_with_fuels.to_csv('intermediate_data/model_output_with_fuels/1_demand_side/{}'.format(model_output_file_name), index=False)

    
#%%
# apply_fuel_mix_demand_side()
#%%
