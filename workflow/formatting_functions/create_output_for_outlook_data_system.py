#take in the unique fuels from the output and match them to once of the unique fuels in the Outlook data columns. Depending on the column

#load in data
#%%
###IMPORT GLOBAL VARIABLES FROM config.py
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
import sys
sys.path.append("./config/utilities")
import config

import pandas as pd 
import numpy as np
import yaml
import datetime
import shutil
import sys
import os 
import re
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go
import matplotlib
import matplotlib.pyplot as plt
###

#%%
def create_output_for_outlook_data_system(ECONOMY_ID):

    model_output_all_with_fuels = pd.read_csv('output_data/model_output_with_fuels/{}_NON_ROAD_DETAILED_{}'.format(ECONOMY_ID, config.model_output_file_name))

    #drop dates after 2070
    model_output_all_with_fuels = model_output_all_with_fuels.loc[model_output_all_with_fuels['Date']<=2070].copy()
    #drop dates bnefore the config.OUTLOOK_BASE_YEAR
    model_output_all_with_fuels = model_output_all_with_fuels.loc[model_output_all_with_fuels['Date']>=config.OUTLOOK_BASE_YEAR].copy()
    #load in EBT framework:
    model_variables = pd.read_excel('./config/9th_EBT_schema.xlsx', sheet_name='9th_EBT_schema', header = 2)
    #cols 'scenarios', 'economy', 'fuels', 'subfuels', 'sectors', 'sub1sectors', 'sub2sectors', 'sub3sectors', 'sub4sectors'
    
    #match up transport type/vehicle type/drive combinations with sectors in model variables:

    #printhem all:
    unique_sectors = model_output_all_with_fuels[['Medium','Transport Type', 'Vehicle Type', 'Drive']].drop_duplicates()
    
    #and then match them up with the sectors in the model variables. 
    # unique sub4sectors: (matches to drive)
    # 15_02_01_01_01_diesel_engine
    # 15_02_01_01_02_gasoline_engine
    # 15_02_01_01_03_battery_ev
    # 15_02_01_01_04_compressed_natual_gas
    # 15_02_01_01_05_plugin_hybrid_ev_gasoline
    # 15_02_01_01_06_plugin_hybrid_ev_diesel
    # 15_02_01_02_01_diesel_engine
    # 15_02_01_02_02_gasoline_engine
    # 15_02_01_02_03_battery_ev
    # 15_02_01_02_04_compressed_natual_gas
    # 15_02_01_02_05_plugin_hybrid_ev_gasoline
    # 15_02_01_02_06_plugin_hybrid_ev_diesel
    # 15_02_01_03_01_diesel_engine
    # 15_02_01_03_02_gasoline_engine
    # 15_02_01_03_03_battery_ev
    # 15_02_01_03_04_compressed_natual_gas
    # 15_02_01_03_05_plugin_hybrid_ev_gasoline
    # 15_02_01_03_06_plugin_hybrid_ev_diesel
    # 15_02_01_04_01_diesel_engine
    # 15_02_01_04_02_gasoline_engine
    # 15_02_01_04_03_battery_ev
    # 15_02_01_04_04_compressed_natual_gas
    # 15_02_01_04_05_plugin_hybrid_ev_gasoline
    # 15_02_01_04_06_plugin_hybrid_ev_diesel
    # 15_02_02_01_01_diesel_engine
    # 15_02_02_01_02_gasoline_engine
    # 15_02_02_01_03_battery_ev
    # 15_02_02_01_04_compressed_natual_gas
    # 15_02_02_01_05_plugin_hybrid_ev_gasoline
    # 15_02_02_01_06_plugin_hybrid_ev_diesel
    # 15_02_02_02_01_diesel_engine
    # 15_02_02_02_02_gasoline_engine
    # 15_02_02_02_03_battery_ev
    # 15_02_02_02_04_compressed_natual_gas
    # 15_02_02_02_05_plugin_hybrid_ev_gasoline
    # 15_02_02_02_06_plugin_hybrid_ev_diesel
    # 15_02_02_03_01_diesel_engine
    # 15_02_02_03_02_gasoline_engine
    # 15_02_02_03_03_battery_ev
    # 15_02_02_03_04_compressed_natual_gas
    # 15_02_02_03_05_plugin_hybrid_ev_gasoline
    # 15_02_02_03_06_plugin_hybrid_ev_diesel
    # 15_02_02_04_01_diesel_engine
    # 15_02_02_04_02_gasoline_engine
    # 15_02_02_04_03_battery_ev
    # 15_02_02_04_04_compressed_natual_gas
    # 15_02_02_04_05_plugin_hybrid_ev_gasoline
    # 15_02_01_05_06_plugin_hybrid_ev_diesel
    # 15_02_01_05_01_diesel_engine
    # 15_02_01_05_02_gasoline_engine
    # 15_02_01_05_03_battery_ev
    # 15_02_01_05_04_compressed_natual_gas
    # 15_02_01_05_05_plugin_hybrid_ev_gasoline
    # 15_02_01_05_06_plugin_hybrid_ev_diesel
    # 15_02_01_01_07_liquified_petroleum_gas
    # 15_02_01_02_07_liquified_petroleum_gas
    # 15_02_01_03_07_liquified_petroleum_gas
    # 15_02_01_04_07_liquified_petroleum_gas
    # 15_02_01_05_07_liquified_petroleum_gas
    # 15_02_02_01_07_liquified_petroleum_gas
    # 15_02_02_02_07_liquified_petroleum_gas
    # 15_02_02_03_07_liquified_petroleum_gas
    # 15_02_02_04_07_liquified_petroleum_gas

    # unique sub3sectors: (deodnind on if the 3rd 2 digit code is 01 or 02 (which corresponds to passenger or freight)) then map it to vehicle type
    # 15_02_01_01_two_wheeler
    # 15_02_01_02_car
    # 15_02_01_03_sports_utility_vehicle
    # 15_02_01_04_light_truck
    # 15_02_01_05_bus
    # 15_02_02_01_two_wheeler
    # 15_02_02_02_light_commercial_vehicle
    # 15_02_02_03_medium_truck
    # 15_02_02_04_heavy_truck
    #sub2sectors (matches to transport type)
    # 15_01_01_passenger
    # 15_01_02_freight
    # 15_02_01_passenger
    # 15_02_02_freight
    # 15_03_01_passenger
    # 15_03_02_freight
    # 15_04_01_passenger
    # 15_04_02_freight
    #sub1sectors (matches to medium)
    # 15_01_domestic_air_transport
    # 15_02_road
    # 15_03_rail
    # 15_04_domestic_navigation
    # 15_05_pipeline_transport
    # 15_06_nonspecified_transport
    # 17_03_transport_sector
    #subsectors: (everything shoudl be in 15_transport_sector)
    # 15_transport_sector
    # 17_nonenergy_use

    #print unique sectors i nthe model output:
    # Transport Type	Vehicle Type	Drive
    # passenger	suv	phev_g
    # passenger	suv	phev_d
    # passenger	suv	lpg
    # passenger	suv	ice_g
    # passenger	suv	ice_d
    # passenger	suv	fcev
    # passenger	suv	cng
    # passenger	suv	bev
    # passenger	lt	phev_g
    # passenger	lt	phev_d
    # passenger	lt	lpg
    # passenger	lt	ice_g
    # passenger	lt	ice_d
    # passenger	lt	fcev
    # passenger	lt	cng
    # passenger	lt	bev
    # passenger	car	phev_g
    # passenger	car	phev_d
    # passenger	car	lpg
    # passenger	car	ice_g
    # passenger	car	ice_d
    # passenger	car	fcev
    # passenger	car	cng
    # passenger	car	bev
    # passenger	bus	phev_g
    # passenger	bus	phev_d
    # passenger	bus	lpg
    # passenger	bus	ice_g
    # passenger	bus	ice_d
    # passenger	bus	fcev
    # passenger	bus	cng
    # passenger	bus	bev
    # passenger	2w	ice_g
    # passenger	2w	ice_d
    # passenger	2w	bev
    # freight	2w	ice_g
    # freight	2w	ice_d
    # freight	2w	bev
    # freight	mt	phev_g
    # freight	mt	phev_d
    # freight	mt	lpg
    # freight	mt	ice_g
    # freight	mt	ice_d
    # freight	mt	fcev
    # freight	mt	cng
    # freight	mt	bev
    # freight	lcv	phev_g
    # freight	lcv	phev_d
    # freight	lcv	lpg
    # freight	lcv	ice_g
    # freight	lcv	ice_d
    # freight	lcv	fcev
    # freight	lcv	cng
    # freight	lcv	bev
    # freight	ht	phev_g
    # freight	ht	phev_d
    # freight	ht	lpg
    # freight	ht	ice_g
    # freight	ht	ice_d
    # freight	ht	fcev
    # freight	ht	cng
    # freight	ht	bev
    # freight	all	all
    # passenger	all	all

    #NON ROAD DRIVE MAPPINGS:
    #since we had to make the non road drives specific to the fuel they use, we just need to map them all to whether they are ship, rail, or air

    #create a 4 tierd  dictionary to map the sectors in the model output to the sectors in the model variables
    

    for row in unique_sectors.iterrows():
        transport_type = row[1]['Transport Type']
        vehicle_type = row[1]['Vehicle Type']
        drive = row[1]['Drive']
        medium = row[1]['Medium']
        
        new_medium = config.medium_mapping[medium]
        new_transport_type = config.transport_type_mapping[transport_type]
        if transport_type == 'passenger':
            new_vehicle_type = config.vehicle_type_mapping_passenger[vehicle_type]
        elif transport_type == 'freight':
            new_vehicle_type = config.vehicle_type_mapping_freight[vehicle_type]
        else:
            raise ValueError('transport type not found')
        
        if medium != 'road':#if its a non road type then we dont need to map the drive, can jsut set it to x
            new_drive_type = 'x'
        else:
            #find drives this could be by finding all keys where the value is the same as the drive
            drive_keys = [key for key, value in config.drive_mapping_inversed.items() if value == drive]
            if len(drive_keys) == 0:
                raise ValueError('drive not found, the drive was {} for the row {}'.format(drive, row))
            else:
                #find the key for which it's first 12 characters match the vehicle types numbers: eg. 15_02_02_04_ in 15_02_02_04_01_diesel_engine corresponds to the vehicle type 15_02_02_04_heavy_truck!
                first_12 = new_vehicle_type[:12]
                for key in drive_keys:
                    if key[:12] == first_12:
                        new_drive_type = key
                        break
                else:
                    raise ValueError('drive not found, the drive was {} for the row {}'.format(drive, row))
        
        #Use the first 5 characters of medium and add them to transport type: eg. in 15_03_rail, 15_01_domestic_air_transport, and put that at start of transport type
        new_transport_type = new_medium[:5]+'_'+new_transport_type
        
        #add those to the dataframe for that row:
        unique_sectors.loc[row[0], 'sub4sectors'] = new_drive_type
        unique_sectors.loc[row[0], 'sub3sectors'] = new_vehicle_type
        unique_sectors.loc[row[0], 'sub2sectors'] = new_transport_type
        unique_sectors.loc[row[0], 'sub1sectors'] = new_medium
        
    unique_sectors_mapping_df = unique_sectors.copy()   
        
    unique_sectors_mapping_df['subsectors'] ='15_transport_sector'
        

     
        
    #now do the same thing but map the fuels to unqiue fuels
    #first get the unique fuels
    # model_output_all_with_fuels.Fuel.unique()
    # array(['17_electricity', '07_07_gas_diesel_oil', '07_01_motor_gasoline',
    #        '08_01_natural_gas', '16_x_hydrogen', '07_09_lpg',
    #        '07_02_aviation_gasoline', '07_x_jet_fuel', '01_x_coal_thermal',
    #        '07_08_fuel_oil', '07_x_other_petroleum_products',
    #        '16_06_biodiesel', '16_05_biogasoline', '16_x_efuel',
    #        '16_07_bio_jet_kerosene'], dtype=object)

    # subfuels
    # 01_01_coking_coal
    # 01_x_thermal_coal
    # 01_05_lignite
    # 06_01_crude_oil
    # 06_02_natural_gas_liquids
    # 06_x_other_hydrocarbons
    # 07_01_motor_gasoline
    # 07_02_aviation_gasoline
    # 07_03_naphtha
    # 07_x_jet_fuel
    # 07_06_kerosene
    # 07_07_gas_diesel_oil
    # 07_08_fuel_oil
    # 07_09_lpg
    # 07_10_refinery_gas_not_liquefied
    # 07_11_ethane
    # 07_x_other_petroleum_products
    # 08_01_natural_gas
    # 08_02_lng
    # 08_03_gas_works_gas
    # 12_01_of_which_photovoltaics
    # 12_x_other_solar
    # 15_01_fuelwood_and_woodwaste
    # 15_02_bagasse
    # 15_03_charcoal
    # 15_04_black_liquor
    # 15_05_other_biomass
    # 16_01_biogas
    # 16_02_industrial_waste
    # 16_03_municipal_solid_waste_renewable
    # 16_04_municipal_solid_waste_nonrenewable
    # 16_05_biogasoline
    # 16_06_biodiesel
    # 16_07_bio_jet_kerosene
    # 16_08_other_liquid_biofuels
    # 16_09_other_sources
    # 16_x_ammonia
    # 16_x_hydrogen
    # 16_x_efuel
    # x


    # fuels
    # 01_coal
    # 02_coal_products
    # 03_peat
    # 04_peat_products
    # 05_oil_shale_and_oil_sands
    # 06_crude_oil_and_ngl
    # 07_petroleum_products
    # 08_gas
    # 09_nuclear
    # 10_hydro
    # 11_geothermal
    # 12_solar
    # 13_tide_wave_ocean
    # 14_wind
    # 15_solid_biomass
    # 16_others
    # 17_electricity
    # 18_heat
    # 19_total
    # 20_total_renewables
    # 21_modern_renewables

    fuels_df = model_output_all_with_fuels.Fuel.unique()
    fuels_df = pd.DataFrame(fuels_df, columns=['Fuel'])
    #now map the fuels to the unique fuels. Note that most fuels have a directly corresponding subfuels. THose that dont should have a directly correpsnong fuels (in this case set their subfuel to x). Those that dont should raise a wanring.

    # fuels
    # 01_coal
    # 02_coal_products
    # 03_peat
    # 04_peat_products
    # 05_oil_shale_and_oil_sands
    # 06_crude_oil_and_ngl
    # 07_petroleum_products
    # 08_gas
    # 09_nuclear
    # 10_hydro
    # 11_geothermal
    # 12_solar
    # 13_tide_wave_ocean
    # 14_wind
    # 15_solid_biomass
    # 16_others
    # 17_electricity
    # 18_heat
    # 19_total
    # 20_total_renewables
    # 21_modern_renewables

    #now map the df to these:
    fuels_df['subfuels'] = fuels_df['Fuel'].map(config.subfuels_mapping)
    fuels_df['fuels'] = fuels_df['Fuel'].map(config.fuels_mapping)

    #check for Fuels that are not mapped:
    if fuels_df.isna().sum().sum() > 0:
        print('WARNING: There are fuels that are not mapped to a subfuel or fuel. Please check the mapping {} and add them to the mapping if needed'.format(fuels_df[fuels_df.isna().any(axis=1)]))
    
    #now merge both fuels df and unique_sectors_mapping_df to the model_output_all_with_fuels df on the Fuel and Transport Type	Vehicle Type	Drive	 columns respectively:
    new_final_df = model_output_all_with_fuels.copy()
    new_final_df = new_final_df.merge(fuels_df, on='Fuel', how='left')
    new_final_df = new_final_df.merge(unique_sectors_mapping_df, on=['Medium','Transport Type', 'Vehicle Type', 'Drive'], how='left')
    
    show_nas = True
    if show_nas:
        # # new_final_df.columns Index(['Date', 'Economy', 'Scenario', 'Transport Type', 'Vehicle Type',
        #        'Drive', 'Medium', 'Fuel', 'Energy', 'subfuels', 'fuels', 'sub4sectors',
        #        'sub3sectors', 'sub2sectors', 'sub1sectors', 'subsectors'],
        #       dtype='object')
        #separate rows where Enegy is Nan and show stats about them
        nan_energy_df = new_final_df[new_final_df['Energy'].isna()]
        #print unique medium, vehivle type drive cols for these rows:
        print(nan_energy_df[['Medium', 'Transport Type', 'Vehicle Type', 'Drive']].drop_duplicates())
        #print count of nans for each economy
        print(nan_energy_df.groupby('Economy').count()['Date'])
    

    #set nas to 0s
    new_final_df['Energy'] = new_final_df['Energy'].fillna(0)
    #finalise df:
    #drop unneccesary cols 'Transport Type', 'Vehicle Type',
    #        'Drive', 'Medium', 'Fuel'
    new_final_df = new_final_df.drop(['Fuel', 'Transport Type', 'Vehicle Type', 'Drive', 'Medium'], axis=1)

    #sum up, now that weve dropped the cols (there will be duplicates for biofuels in non road definitely:
    new_final_df = new_final_df.groupby(['Date', 'Economy', 'Scenario', 'fuels', 'subfuels', 'subsectors', 'sub1sectors', 'sub2sectors', 'sub3sectors', 'sub4sectors']).sum().reset_index()

    #check for duplicates:
    if new_final_df.duplicated().sum() > 0:
        duplicates = new_final_df[new_final_df.duplicated()]
        raise ValueError(f'There are duplicates in the final df. Please check {duplicates}')
    #and check for uplcaites when you ignore energy col
    if new_final_df.drop('Energy', axis=1).duplicated().sum() > 0:
        duplicates = new_final_df[new_final_df.drop('Energy', axis=1).duplicated()]
        raise ValueError(f'There are duplicates in the final df when you remove energy col. Please check {duplicates}')
    #set nas to 0s
    new_final_df['Energy'] = new_final_df['Energy'].fillna(0)
    #find any nans in other cols
    if new_final_df.isna().sum().sum() > 0:
        nans = new_final_df[new_final_df.isna().any(axis=1)]
        raise ValueError(f'There are nans in the final df. Please check {nans}')
    

    #and sum up the values since some mappings will be many to one (eg non road drives are all set to x)
    new_final_df = new_final_df.groupby(['Date', 'Economy', 'Scenario', 'fuels', 'subfuels', 'subsectors', 'sub1sectors', 'sub2sectors', 'sub3sectors', 'sub4sectors']).sum().reset_index()

    #pivot the date column and order/rename the columns liek: 'scenarios', 'economy', 'fuels', 'subfuels', 'sectors', 'sub1sectors', 'sub2sectors', 'sub3sectors', 'sub4sectors'
    new_final_df = new_final_df.pivot(index=['Economy', 'Scenario', 'fuels', 'subfuels', 'subsectors', 'sub1sectors', 'sub2sectors', 'sub3sectors', 'sub4sectors'], columns='Date', values='Energy').reset_index()
    new_final_df.rename(columns={'Economy':'economy', 'Scenario':'scenarios', 'subsectors':'sectors'}, inplace=True)

    #QUICK FIXES:
    #make names in scenario lowercase:
    new_final_df['scenarios'] = new_final_df['scenarios'].str.lower()
    #change Economys 15_RP, and 17_SIN to 15_PHL, 17_SGP
    new_final_df['economy'] = new_final_df['economy'].replace({'15_RP':'15_PHL', '17_SIN':'17_SGP'})


    #save this file to output_data\for_other_modellers
    new_final_df.to_csv(f'output_data/for_other_modellers/{ECONOMY_ID}_{config.FILE_DATE_ID}_transport_energy_use.csv', index=False)
    
    
def concatenate_outlook_data_system_outputs():
    #take in all outlook data system outputs for teh same FILE DATE ID and concatenate them into one file. if an economy is missing throw an error
    #load in all files:
    final_df = pd.DataFrame()
    for file in os.listdir('output_data/for_other_modellers'):
        if file.endswith('_{}_transport_energy_use.csv'.format(config.FILE_DATE_ID)):
            df = pd.read_csv(f'output_data/for_other_modellers/{file}')
            final_df = pd.concat([final_df, df])
    #check that all economies are there:
    if len(final_df['economy'].unique()) != len(config.ECONOMY_LIST):
        missing_economies = [e for e in config.ECONOMY_LIST if e not in final_df['economy'].unique()]
        raise ValueError(f'The following economies are missing from the outlook data system outputs: {missing_economies}')
    #save the final df:
    final_df.to_csv(f'output_data/for_other_modellers/output_for_outlook_data_system/{config.FILE_DATE_ID}_transport_energy_use.csv', index=False)