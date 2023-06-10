#this will apply any fuel mixing on the supply side. This is currently only biofuel mixing to petroleum products but could include other fuel types in the future

#this will merge a fuel sharing dataframe onto the model output, by the fuel column, and apply the shares by doing that. There will be a new fuel column after this

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
#%%
#create fake user input for demand side fuel mixes using model concordances
def create_supply_side_fuel_mixing_input():
    # #load model concordances
    # supply_side_fuel_mixing = pd.read_csv('config/concordances_and_config_data/computer_generated_concordances/{}'.format(supply_side_fuel_mixing_file_name_fuels))
    
    #take in demand side fuel mixes
    demand_side_fuel_mixing = pd.read_csv('intermediate_data\model_inputs\demand_side_fuel_mixing_COMPGEN.csv')

    
    INDEX_COLS_no_measure = INDEX_COLS.copy()
    INDEX_COLS_no_measure.remove('Measure')
    INDEX_COLS_no_measure.remove('Unit')

    supply_side_fuel_mixing = demand_side_fuel_mixing.copy()
    #drop Demand_side_fuel_share column
    supply_side_fuel_mixing = supply_side_fuel_mixing.drop(columns=['Demand_side_fuel_share']).drop_duplicates()
    
    #startwith the model concordances with fuel types, filter for each fuel type, and split it into biofuel and fuel type. have to do each fuel type separately depnding on the resulting biofuel mix.
    #split all 07_petroleum_products into a mix of biofuels and petroleum products. Note that 07_petroleum_products is currently being used to represent general oil use in ice engines. This just 

    #Remember this allows for the option of not splitting all diesel use into biofuels. you can set it so vehicle type doesnt equal rail for example
    supply_side_fuel_mixing_diesel = supply_side_fuel_mixing.loc[(supply_side_fuel_mixing['Fuel'] == '07_07_gas_diesel_oil')]
    supply_side_fuel_mixing_diesel['16_06_biodiesel'] = 0.05
    supply_side_fuel_mixing_diesel['07_07_gas_diesel_oil'] = 0.95
    #now melt so we have a tall dataframe
    supply_side_fuel_mixing_diesel_melt = pd.melt(supply_side_fuel_mixing_diesel, id_vars=INDEX_COLS_no_measure + ['Fuel'], var_name='New_fuel', value_name='Supply_side_fuel_share')

    supply_side_fuel_mixing_petrol = supply_side_fuel_mixing.loc[(supply_side_fuel_mixing['Fuel'] == '07_01_motor_gasoline')]
    supply_side_fuel_mixing_petrol['16_05_biogasoline'] = 0.05
    supply_side_fuel_mixing_petrol['07_01_motor_gasoline'] = 0.95
    #now melt so we have a tall dataframe
    supply_side_fuel_mixing_petrol_melt = pd.melt(supply_side_fuel_mixing_petrol, id_vars=INDEX_COLS_no_measure + ['Fuel'], var_name='New_fuel', value_name='Supply_side_fuel_share')

    supply_side_fuel_mixing_jet_fuel = supply_side_fuel_mixing.loc[(supply_side_fuel_mixing['Fuel'] == '07_x_jet_fuel')]
    supply_side_fuel_mixing_jet_fuel['16_07_bio_jet_kerosene'] = 0.05
    supply_side_fuel_mixing_jet_fuel['07_x_jet_fuel'] = 0.95
    #now melt so we have a tall dataframe
    supply_side_fuel_mixing_jet_fuel_melt = pd.melt(supply_side_fuel_mixing_jet_fuel, id_vars=INDEX_COLS_no_measure + ['Fuel'], var_name='New_fuel', value_name='Supply_side_fuel_share')

    supply_side_fuel_mixing_avgas = supply_side_fuel_mixing.loc[(supply_side_fuel_mixing['Fuel'] == '07_02_aviation_gasoline')]
    supply_side_fuel_mixing_avgas['16_07_bio_jet_kerosene'] = 0.05
    supply_side_fuel_mixing_avgas['07_02_aviation_gasoline'] = 0.95
    #now melt so we have a tall dataframe
    supply_side_fuel_mixing_avgas_melt = pd.melt(supply_side_fuel_mixing_avgas, id_vars=INDEX_COLS_no_measure + ['Fuel'], var_name='New_fuel', value_name='Supply_side_fuel_share')

    
    #CONCATENATE all
    supply_side_fuel_mixing_all = pd.concat([supply_side_fuel_mixing_petrol_melt, supply_side_fuel_mixing_diesel_melt, supply_side_fuel_mixing_jet_fuel_melt, supply_side_fuel_mixing_avgas_melt])

    #archive previous results:
    archiving_folder = archiving_scripts.create_archiving_folder_for_FILE_DATE_ID(FILE_DATE_ID)
    #save previous datra
    shutil.copy('intermediate_data\model_inputs\supply_side_fuel_mixing_COMPGEN.csv', archiving_folder + '/supply_side_fuel_mixing_COMPGEN.csv')
    # #save the variables we used to calculate the data by savinbg the 'input_data/vehicle_sales_share_inputs.xlsx' file
    # shutil.copy('input_data/vehicle_sales_share_inputs.xlsx', archiving_folder + '/vehicle_sales_share_inputs.xlsx')

    breakpoint()
    #save as user input csv
    supply_side_fuel_mixing_all.to_csv('intermediate_data\model_inputs\supply_side_fuel_mixing_COMPGEN.csv', index=False)
    
#%%
# create_supply_side_fuel_mixing_input()
#%%