#take in the unique fuels from the output and match them to once of the unique fuels in the Outlook data columns. Depending on the column

#load in data
#%%
#set working directory as one folder back so that config works
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
from runpy import run_path
exec(open("config/config.py").read())#usae this to load libraries and set variables. Feel free to edit that file as you need


model_output_all_with_fuels = pd.read_csv('output_data/model_output_with_fuels/{}'.format(model_output_file_name))

#load in EBT framework:
model_variables = pd.read_excel('./config/9th_EBT_schema.xlsx', sheet_name='9th_EBT_schema', header = 2)
#cols 'scenarios', 'economy', 'fuels', 'subfuels', 'sectors', 'sub1sectors', 'sub2sectors', 'sub3sectors', 'sub4sectors'
#%%
#match up transport type/vehicle type/drive combinations with sectors in model variables:

#printhem all:
unique_sectors = model_output_all_with_fuels[['Medium','Transport Type', 'Vehicle Type', 'Drive']].drop_duplicates()
#%%
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
# passenger	all	all
# passenger	2w	ice_g
# passenger	2w	ice_d
# passenger	2w	bev
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

#create a 4 tierd  dictionary to map the sectors in the model output to the sectors in the model variables
#%%

medium_mapping = {'air': '15_01_domestic_air_transport', 'road': '15_02_road', 'rail': '15_03_rail', 'ship': '15_04_domestic_navigation'}
transport_type_mapping = {'passenger': 'passenger', 'freight': 'freight'}
vehicle_type_mapping_passenger = {'suv': '15_02_01_03_sports_utility_vehicle', 'lt': '15_02_01_04_light_truck', 'car': '15_02_01_02_car', 'bus': '15_02_01_05_bus', '2w': '15_02_02_01_two_wheeler','all':'x'}
vehicle_type_mapping_freight = {'mt': '15_02_02_03_medium_truck', 'lcv': '15_02_02_02_light_commercial_vehicle', 'ht': '15_02_02_04_heavy_truck', 'all':'x'}

drive_mapping_inversed = {'x':'all',
    '15_02_01_01_01_diesel_engine': 'ice_d', 
    '15_02_01_01_02_gasoline_engine': 'ice_g', 
    '15_02_01_01_03_battery_ev': 'bev', 
    '15_02_01_01_04_compressed_natual_gas': 'cng', 
    '15_02_01_01_05_plugin_hybrid_ev_gasoline': 'phev_g', 
    '15_02_01_01_06_plugin_hybrid_ev_diesel': 'phev_d',  
    '15_02_01_01_07_liquified_petroleum_gas': 'lpg', 
    '15_02_01_01_08_fuel_cell_ev': 'fcev', 

    '15_02_01_02_01_diesel_engine': 'ice_d', 
    '15_02_01_02_02_gasoline_engine': 'ice_g', 
    '15_02_01_02_03_battery_ev': 'bev', 
    '15_02_01_02_04_compressed_natual_gas': 'cng', 
    '15_02_01_02_05_plugin_hybrid_ev_gasoline': 'phev_g', 
    '15_02_01_02_06_plugin_hybrid_ev_diesel': 'phev_d',  
    '15_02_01_02_07_liquified_petroleum_gas': 'lpg', 
    '15_02_01_02_08_fuel_cell_ev': 'fcev', 

    '15_02_01_03_01_diesel_engine': 'ice_d', 
    '15_02_01_03_02_gasoline_engine': 'ice_g', 
    '15_02_01_03_03_battery_ev': 'bev', 
    '15_02_01_03_04_compressed_natual_gas': 'cng', 
    '15_02_01_03_05_plugin_hybrid_ev_gasoline': 'phev_g', 
    '15_02_01_03_06_plugin_hybrid_ev_diesel': 'phev_d',  
    '15_02_01_03_07_liquified_petroleum_gas': 'lpg', 
    '15_02_01_03_08_fuel_cell_ev': 'fcev', 

    '15_02_01_04_01_diesel_engine': 'ice_d', 
    '15_02_01_04_02_gasoline_engine': 'ice_g', 
    '15_02_01_04_03_battery_ev': 'bev', 
    '15_02_01_04_04_compressed_natual_gas': 'cng', 
    '15_02_01_04_05_plugin_hybrid_ev_gasoline': 'phev_g', 
    '15_02_01_04_06_plugin_hybrid_ev_diesel': 'phev_d',  
    '15_02_01_04_07_liquified_petroleum_gas': 'lpg', 
    '15_02_01_04_08_fuel_cell_ev': 'fcev', 

    '15_02_02_01_01_diesel_engine': 'ice_d', 
    '15_02_02_01_02_gasoline_engine': 'ice_g', 
    '15_02_02_01_03_battery_ev': 'bev', 
    '15_02_02_01_04_compressed_natual_gas': 'cng', 
    '15_02_02_01_05_plugin_hybrid_ev_gasoline': 'phev_g', 
    '15_02_02_01_06_plugin_hybrid_ev_diesel': 'phev_d',  
    '15_02_02_01_07_liquified_petroleum_gas': 'lpg', 
    '15_02_02_01_08_fuel_cell_ev': 'fcev', 

    '15_02_02_02_01_diesel_engine': 'ice_d', 
    '15_02_02_02_02_gasoline_engine': 'ice_g', 
    '15_02_02_02_03_battery_ev': 'bev', 
    '15_02_02_02_04_compressed_natual_gas': 'cng', 
    '15_02_02_02_05_plugin_hybrid_ev_gasoline': 'phev_g', 
    '15_02_02_02_06_plugin_hybrid_ev_diesel': 'phev_d',  
    '15_02_02_02_07_liquified_petroleum_gas': 'lpg', 
    '15_02_02_02_08_fuel_cell_ev': 'fcev', 

    '15_02_02_03_01_diesel_engine': 'ice_d', 
    '15_02_02_03_02_gasoline_engine': 'ice_g', 
    '15_02_02_03_03_battery_ev': 'bev', 
    '15_02_02_03_04_compressed_natual_gas': 'cng', 
    '15_02_02_03_05_plugin_hybrid_ev_gasoline': 'phev_g', 
    '15_02_02_03_06_plugin_hybrid_ev_diesel': 'phev_d',  
    '15_02_02_03_07_liquified_petroleum_gas': 'lpg', 
    '15_02_02_03_08_fuel_cell_ev': 'fcev', 

    '15_02_02_04_01_diesel_engine': 'ice_d', 
    '15_02_02_04_02_gasoline_engine': 'ice_g', 
    '15_02_02_04_03_battery_ev': 'bev', 
    '15_02_02_04_04_compressed_natual_gas': 'cng', 
    '15_02_02_04_05_plugin_hybrid_ev_gasoline': 'phev_g', 
    '15_02_02_04_06_plugin_hybrid_ev_diesel': 'phev_d',  
    '15_02_02_04_07_liquified_petroleum_gas': 'lpg', 
    '15_02_02_04_08_fuel_cell_ev': 'fcev',

    '15_02_01_05_01_diesel_engine': 'ice_d', 
    '15_02_01_05_02_gasoline_engine': 'ice_g', 
    '15_02_01_05_03_battery_ev': 'bev', 
    '15_02_01_05_04_compressed_natual_gas': 'cng', 
    '15_02_01_05_05_plugin_hybrid_ev_gasoline': 'phev_g', 
    '15_02_01_05_06_plugin_hybrid_ev_diesel': 'phev_d',  
    '15_02_01_05_07_liquified_petroleum_gas': 'lpg', 
    '15_02_01_05_08_fuel_cell_ev': 'fcev'
}

for row in unique_sectors.iterrows():
    transport_type = row[1]['Transport Type']
    vehicle_type = row[1]['Vehicle Type']
    drive = row[1]['Drive']
    medium = row[1]['Medium']
    
    new_medium = medium_mapping[medium]
    new_transport_type = transport_type_mapping[transport_type]
    if new_transport_type == 'passenger':
        new_vehicle_type = vehicle_type_mapping_passenger[vehicle_type]
    elif new_transport_type == 'freight':
        new_vehicle_type = vehicle_type_mapping_freight[vehicle_type]
    else:
        raise ValueError('transport type not found')
    
    if drive =='all':
        new_drive_type = 'x'
    else:
        #find drives this could be by finding all keys where the value is the same as the drive
        drive_keys = [key for key, value in drive_mapping_inversed.items() if value == drive]
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
        
    #add those to the dataframe for that row:
    unique_sectors.loc[row[0], 'sub4sectors'] = new_drive_type
    unique_sectors.loc[row[0], 'sub3sectors'] = new_vehicle_type
    unique_sectors.loc[row[0], 'sub2sectors'] = new_transport_type
    unique_sectors.loc[row[0], 'sub1sectors'] = new_medium
    
unique_sectors_mapping_df = unique_sectors.copy()   
    
unique_sectors_mapping_df['subsectors'] ='15_transport_sector'
    

#%% 
    
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

subfuels_mapping = {'17_electricity':'x', '07_07_gas_diesel_oil':'07_07_gas_diesel_oil', '07_01_motor_gasoline':'07_01_motor_gasoline',
       '08_01_natural_gas':'08_01_natural_gas', '16_x_hydrogen':'16_x_hydrogen', '07_09_lpg':'07_09_lpg',
       '07_02_aviation_gasoline':'07_02_aviation_gasoline', '07_x_jet_fuel':'07_x_jet_fuel', '01_x_coal_thermal':'01_x_coal_thermal',
       '07_08_fuel_oil':'07_08_fuel_oil', '07_x_other_petroleum_products':'07_x_other_petroleum_products',
       '16_06_biodiesel':'16_06_biodiesel', '16_05_biogasoline':'16_05_biogasoline', '16_x_efuel':'16_x_efuel',
       '16_07_bio_jet_kerosene':'16_07_bio_jet_kerosene'}
    
#now map fuels to subfuels. All will need to be mapped, but in most cases it will be to a more broad category than it currently is. eg. 07_07_gas_diesel_oil will be mapped to 07_petroleum_products just like 07_01_motor_gasoline is.
fuels_mapping = {'17_electricity': '17_electricity', '07_07_gas_diesel_oil':'07_petroleum_products', '07_01_motor_gasoline':'07_petroleum_products',
       '08_01_natural_gas':'08_gas', '16_x_hydrogen':'16_others', '07_09_lpg':'07_petroleum_products',
       '07_02_aviation_gasoline':'07_petroleum_products', '07_x_jet_fuel':'07_petroleum_products', '01_x_coal_thermal':'01_coal',
       '07_08_fuel_oil':'07_petroleum_products', '07_x_other_petroleum_products':'07_petroleum_products',
       '16_06_biodiesel':'16_others', '16_05_biogasoline':'16_others', '16_x_efuel':'16_others',
       '16_07_bio_jet_kerosene':'16_others'}

#now map the df to these:
fuels_df['subfuels'] = fuels_df['Fuel'].map(subfuels_mapping)
fuels_df['fuels'] = fuels_df['Fuel'].map(fuels_mapping)

#check for Fuels that are not mapped:
if fuels_df.isna().sum().sum() > 0:
    print('WARNING: There are fuels that are not mapped to a subfuel or fuel. Please check the mapping')
#%%
#now merge both fuels df and unique_sectors_mapping_df to the model_output_all_with_fuels df on the Fuel and Transport Type	Vehicle Type	Drive	 columns respectively:
new_final_df = model_output_all_with_fuels.copy()
new_final_df = new_final_df.merge(fuels_df, on='Fuel', how='left')
new_final_df = new_final_df.merge(unique_sectors_mapping_df, on=['Medium','Transport Type', 'Vehicle Type', 'Drive'], how='left')

#%%
show_nas = False
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
# %%
#finalise df:
#drop unneccesary cols 'Transport Type', 'Vehicle Type',
#        'Drive', 'Medium', 'Fuel'
new_final_df = new_final_df.drop(['Fuel', 'Transport Type', 'Vehicle Type', 'Drive', 'Medium'], axis=1)
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
# %%

#save this file to output_data\for_other_modellers
new_final_df.to_csv(r'output_data\for_other_modellers\transport_energy_use{FILE_DATE_ID}.csv', index=False)