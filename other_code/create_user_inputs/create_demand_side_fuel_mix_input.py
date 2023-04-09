#this will apply any fuel mixing on the demand side. It contains the use of different fule types for each drive type, for example, electricity vs oil in phev's, or even treating rail as a drive type, and splitting demand into electricity, coal and dieel rpoprtions. 
#This could include any mixing, even biofuels, but is intended for use from the perspective of the demand side only. If you do include biofuels in this mix, you will have to remove it from the supply side mixing.
#Once finished this will merge a fuel mixing dataframe onto the model output, by the Drive column, and apply the shares by doing that, resulting in a fuel column.
#this means that the supply side fuel mixing needs to occur after this script, because it will be merging on the fuel column.

#%% 
#set working directory as one folder back so that config works
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
from runpy import run_path
exec(open("config/config.py").read())#usae this to load libraries and set variables. Feel free to edit that file as you need

#%%
#create fake user input for demand side fuel mixes using model concordances

#load model concordances for filling in 
model_concordances_fuels = pd.read_csv('config/concordances_and_config_data/computer_generated_concordances/{}'.format(model_concordances_file_name_fuels))

#%%
#the process will run like:
#load in fuel concrdacnes, filter for drive type and then pivot so each fuel is a column. then manually set the fuels columns to the shares you want. if a column is missing, it will be assumed to be 0. this allows for biofuels to be excluded and handled by the supply side fuel mixing.
#first create a dummy value col for when pivoting
model_concordances_fuels['dummy'] = np.nan

INDEX_COLS_no_measure = INDEX_COLS.copy()
INDEX_COLS_no_measure.remove('Measure')
INDEX_COLS_no_measure.remove('Unit')

#%%
#startwith the model concordances, filter for drive == PHEVG or PHEVD and create a col for PHEV elec and PHEV non-elec, fill them with 0.5. The icct paper indicates that for europe its more like 0.4 for elec and 0.6 for oil, but this doesnt include expeted growth. easier and simpler to assume 0.5

#NOTE THAT ICE IS DELAT WITH IN other_code\create_user_inputs\estimate_ice_fuel_splits.py through estimate_ice_fuel_splits(demand_side_fuel_mixing)

#PHEV bus or ht
model_concordances_PHEVD = model_concordances_fuels.loc[(model_concordances_fuels['Drive'] == 'phev') & (model_concordances_fuels['Vehicle Type'].isin(['bus','ht']))]
#make wide
model_concordances_PHEVD = model_concordances_PHEVD.pivot(index=INDEX_COLS_no_measure, columns='Fuel', values='dummy').reset_index()
#fill cols with values
model_concordances_PHEVD['17_electricity'] = 0.5
model_concordances_PHEVD['07_07_gas_diesel_oil'] = 0.5
#fill na with 0
model_concordances_PHEVD = model_concordances_PHEVD.fillna(0)
#now melt so we have a tall dataframe
model_concordances_PHEVD_melt = pd.melt(model_concordances_PHEVD, id_vars=INDEX_COLS_no_measure, var_name='Fuel', value_name='Demand_side_fuel_share')

#PHEV ldv
model_concordances_PHEVG = model_concordances_fuels.loc[(model_concordances_fuels['Drive'] == 'phev') & (model_concordances_fuels['Vehicle Type'] == 'ldv')]
#make wide
model_concordances_PHEVG = model_concordances_PHEVG.pivot(index=INDEX_COLS_no_measure, columns='Fuel', values='dummy').reset_index()
#fill cols with values
model_concordances_PHEVG['17_electricity'] = 0.5
model_concordances_PHEVG['07_01_motor_gasoline'] = 0.5
#fill na with 0
model_concordances_PHEVG = model_concordances_PHEVG.fillna(0)
#now melt so we have a tall dataframe
model_concordances_PHEVG_melt = pd.melt(model_concordances_PHEVG, id_vars=INDEX_COLS_no_measure, var_name='Fuel', value_name='Demand_side_fuel_share')

#bev
model_concordances_BEV = model_concordances_fuels.loc[model_concordances_fuels['Drive'] == 'bev']
#make wide
model_concordances_BEV = model_concordances_BEV.pivot(index=INDEX_COLS_no_measure, columns='Fuel', values='dummy').reset_index()
#fill cols with values
model_concordances_BEV['17_electricity'] = 1
#fill na with 0
model_concordances_BEV = model_concordances_BEV.fillna(0)
#now melt so we have a tall dataframe
model_concordances_BEV_melt = pd.melt(model_concordances_BEV, id_vars=INDEX_COLS_no_measure, var_name='Fuel', value_name='Demand_side_fuel_share')

#fcev
model_concordances_FCEV = model_concordances_fuels.loc[model_concordances_fuels['Drive'] == 'fcev']
#make wide
model_concordances_FCEV = model_concordances_FCEV.pivot(index=INDEX_COLS_no_measure, columns='Fuel', values='dummy').reset_index()
#fill cols with values
model_concordances_FCEV['16_x_hydrogen'] = 1
#fill na with 0
model_concordances_FCEV = model_concordances_FCEV.fillna(0)
#now melt so we have a tall dataframe
model_concordances_FCEV_melt = pd.melt(model_concordances_FCEV, id_vars=INDEX_COLS_no_measure, var_name='Fuel', value_name='Demand_side_fuel_share')
#%%
#RAIL
model_concordances_rail = model_concordances_fuels.loc[model_concordances_fuels['Medium'] == 'rail']
#make wide
model_concordances_rail = model_concordances_rail.pivot(index=INDEX_COLS_no_measure, columns='Fuel', values='dummy').reset_index()
#fill cols with values
model_concordances_rail['7_7_gas_diesel_oil'] = 1/3
model_concordances_rail['17_electricity'] = 1/3
model_concordances_rail['1_x_coal_thermal'] = 1/3
#fill na with 0
model_concordances_rail = model_concordances_rail.fillna(0)
#now melt so we have a tall dataframe
model_concordances_rail_melt = pd.melt(model_concordances_rail, id_vars=INDEX_COLS_no_measure, var_name='Fuel', value_name='Demand_side_fuel_share')

#AIR
model_concordances_air = model_concordances_fuels.loc[model_concordances_fuels['Medium'] == 'air']
#make wide
model_concordances_air = model_concordances_air.pivot(index=INDEX_COLS_no_measure, columns='Fuel', values='dummy').reset_index()
#fill cols with values
model_concordances_air['7_2_aviation_gasoline'] = 0.05
model_concordances_air['7_x_jet_fuel'] = 0.95
#fill na with 0
model_concordances_air = model_concordances_air.fillna(0)
#now melt so we have a tall dataframe
model_concordances_air_melt = pd.melt(model_concordances_air, id_vars=INDEX_COLS_no_measure, var_name='Fuel', value_name='Demand_side_fuel_share')

#SHIP
model_concordances_ship = model_concordances_fuels.loc[model_concordances_fuels['Medium'] == 'ship']
#make wide
model_concordances_ship = model_concordances_ship.pivot(index=INDEX_COLS_no_measure, columns='Fuel', values='dummy').reset_index()
#fill cols with values
model_concordances_ship['7_7_gas_diesel_oil'] = 0.95
model_concordances_ship['7_8_fuel_oil'] = 0.025
model_concordances_ship['7_x_other_petroleum_products']= 0.025
#fill na with 0
model_concordances_ship = model_concordances_ship.fillna(0)
#now melt so we have a tall dataframe
model_concordances_ship_melt = pd.melt(model_concordances_ship, id_vars=INDEX_COLS_no_measure, var_name='Fuel', value_name='Demand_side_fuel_share')

#%%
#CONCATENATE all
demand_side_fuel_mixing = pd.concat([model_concordances_PHEVD_melt, model_concordances_PHEVG_melt, model_concordances_rail_melt, model_concordances_air_melt, model_concordances_ship_melt,model_concordances_BEV_melt,model_concordances_FCEV_melt], axis=0)

#remove any rows where demand side fuel share is 0 as they are just fuels where there is no use of the fuel
demand_side_fuel_mixing = demand_side_fuel_mixing[demand_side_fuel_mixing['Demand_side_fuel_share'] != 0]

#load in ice data:
import estimate_ice_fuel_splits
demand_side_fuel_mixing = estimate_ice_fuel_splits.estimate_ice_fuel_splits(demand_side_fuel_mixing)
#%%
#save as user input csv
demand_side_fuel_mixing.to_csv('intermediate_data\model_inputs\demand_side_fuel_mixing_COMPGEN.csv', index=False)
#%%

