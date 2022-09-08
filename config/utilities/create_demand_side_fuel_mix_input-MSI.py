#this will apply any fuel mixing on the demand side. This is can include, the use of different fule types for each drive type, for example, electricity vs oil in phev's, or even treating rail as a drive type, and splitting demand into electricity, coal and dieel rpoprtions. 

#as such, this will merge a fuel mixing dataframe onto the model output, by the Drive column, and apply the shares by doing that, resulting in a fuel column.
#this means that the supply side fuel mixing needs to occur after this script, because it will be merging on the fuel column.

#%% 
#set working directory as one folder back so that config works
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
execfile("config/config.py")#usae this to load libraries and set variables. Feel free to edit that file as you need

#%%
#create fake user input for demand side fuel mixes using model concordances

#load model concordances for filling in 
model_concordances_fuels = pd.read_csv('config/concordances/model_concordances_fuels_20220824_1256.csv')

#%%
#the process will run like:
#load in fuel concrdacnes, filter for drive type and then pivot so each fuel is a column. then manually set the fuels columns to the shares you want. if a column is missing, it will be assumed to be 0. this allows for biofuels to be excluded and handled by the supply side fuel mixing.
#first create a dummy value col for when pivoting
model_concordances_fuels['dummy'] = np.nan
#%%

#startwith the model concordances, filter for drive == PHEVG or PHEVD and create a col for PHEV elec and PHEV non-elec, fill them with 0.5. The icct paper indicates that for europe its more like 0.4 for elec and 0.6 for oil, but this doesnt include expeted growth. easier and simpler to assume 0.5

#PHEVG
model_concordances_PHEVG = model_concordances_fuels.loc[(model_concordances_fuels['Drive'] == 'phevg')]
#make wide
model_concordances_PHEVG = model_concordances_PHEVG.pivot(index=['Scenario', 'Economy', 'Transport Type', 'Medium', 'Vehicle Type', 'Drive', 'Year'], columns='Fuel', values='dummy').reset_index()
#fill cols with values
model_concordances_PHEVG['17_electricity'] = 0.5
model_concordances_PHEVG['7_1_motor_gasoline'] = 0.5
#fill na with 0
model_concordances_PHEVG = model_concordances_PHEVG.fillna(0)
#now melt so we have a tall dataframe
model_concordances_PHEVG_melt = pd.melt(model_concordances_PHEVG, id_vars=['Scenario', 'Economy', 'Transport Type',  'Medium','Vehicle Type', 'Drive', 'Year'], var_name='Fuel', value_name='Demand_side_fuel_share')

# #drop medium 
# model_concordances_PHEV_melt = model_concordances_PHEV_melt.drop(['Medium'], axis=1)

#PHEVD
model_concordances_PHEVD = model_concordances_fuels.loc[(model_concordances_fuels['Drive'] == 'phevd')]
#make wide
model_concordances_PHEVD = model_concordances_PHEVD.pivot(index=['Scenario', 'Economy', 'Transport Type', 'Medium', 'Vehicle Type', 'Drive', 'Year'], columns='Fuel', values='dummy').reset_index()
#fill cols with values
model_concordances_PHEVD['17_electricity'] = 0.5
model_concordances_PHEVD['7_7_gas_diesel_oil'] = 0.5
#fill na with 0
model_concordances_PHEVD = model_concordances_PHEVD.fillna(0)
#now melt so we have a tall dataframe
model_concordances_PHEVD_melt = pd.melt(model_concordances_PHEVD, id_vars=['Scenario', 'Economy', 'Transport Type',  'Medium','Vehicle Type', 'Drive', 'Year'], var_name='Fuel', value_name='Demand_side_fuel_share')

#RAIL
model_concordances_rail = model_concordances_fuels.loc[model_concordances_fuels['Drive'] == 'rail']
#make wide
model_concordances_rail = model_concordances_rail.pivot(index=['Scenario', 'Economy', 'Transport Type', 'Medium', 'Vehicle Type', 'Drive', 'Year'], columns='Fuel', values='dummy').reset_index()
#fill cols with values
model_concordances_rail['7_7_gas_diesel_oil'] = 1/3
model_concordances_rail['17_electricity'] = 1/3
model_concordances_rail['1_x_coal_thermal'] = 1/3
#fill na with 0
model_concordances_rail = model_concordances_rail.fillna(0)
#now melt so we have a tall dataframe
model_concordances_rail_melt = pd.melt(model_concordances_rail, id_vars=['Scenario', 'Economy', 'Transport Type', 'Medium', 'Vehicle Type', 'Drive', 'Year'], var_name='Fuel', value_name='Demand_side_fuel_share')


#AIR
model_concordances_air = model_concordances_fuels.loc[model_concordances_fuels['Drive'] == 'air']
#make wide
model_concordances_air = model_concordances_air.pivot(index=['Scenario', 'Economy', 'Transport Type', 'Medium', 'Vehicle Type', 'Drive', 'Year'], columns='Fuel', values='dummy').reset_index()
#fill cols with values
model_concordances_air['7_2_aviation_gasoline'] = 0.05
model_concordances_air['7_x_jet_fuel'] = 0.95
#fill na with 0
model_concordances_air = model_concordances_air.fillna(0)
#now melt so we have a tall dataframe
model_concordances_air_melt = pd.melt(model_concordances_air, id_vars=['Scenario', 'Economy', 'Transport Type', 'Medium', 'Vehicle Type', 'Drive', 'Year'], var_name='Fuel', value_name='Demand_side_fuel_share')

#SHIP
model_concordances_ship = model_concordances_fuels.loc[model_concordances_fuels['Drive'] == 'ship']
#make wide
model_concordances_ship = model_concordances_ship.pivot(index=['Scenario', 'Economy', 'Transport Type', 'Medium', 'Vehicle Type', 'Drive', 'Year'], columns='Fuel', values='dummy').reset_index()
#fill cols with values
model_concordances_ship['7_7_gas_diesel_oil'] = 0.95
model_concordances_ship['7_8_fuel_oil'] = 0.025
model_concordances_ship['7_x_other_petroleum_products']= 0.025
#fill na with 0
model_concordances_ship = model_concordances_ship.fillna(0)
#now melt so we have a tall dataframe
model_concordances_ship_melt = pd.melt(model_concordances_ship, id_vars=['Scenario', 'Economy', 'Transport Type', 'Medium', 'Vehicle Type', 'Drive', 'Year'], var_name='Fuel', value_name='Demand_side_fuel_share')

#%%
#CONCATENATE all
model_concordances_all = pd.concat([model_concordances_PHEVG_melt, model_concordances_PHEVD_melt, model_concordances_rail_melt, model_concordances_air_melt, model_concordances_ship_melt])

#%%
#save as user input csv
model_concordances_all.to_csv('intermediate_data\model_inputs\demand_side_fuel_mixing_COMPGEN.csv', index=False)
#%%

