#we have data from the ESTO energy data set that the output from this model needs to match. hwoever the way this model works is that its output is a function of the input data, which is activity data (the energy use is the final results). so we need to adjust the input data so that the output matches the ESTO data. because there are so many steps in teh system, this will be a bit complicated. We will do this as follows:
# - biofuels: just base it off the total esto demadn for gasoline adn diesel. calculate share of oil use that the biofuels would make up
# - gasoline/diesel: adjust road: cars and lcvs to make it easy. split the difference in half and then apply half change to each.
# - elec: just decrease ev car stocks
# - non road fuels: decrease use in non road
# - gas: bit more difficult. decrease what vehicle types?

#but also we need to know the expected energy use for the period betwen (and including) BASE_YEAR and OUTLOOK_BASE_YEAR. so we need to run the model for that period first to get the output energy use. so we need to run the model twice. once for the period between BASE_YEAR and OUTLOOK_BASE_YEAR, and then finally for the period between OUTLOOK_BASE_YEAR and OUTLOOK_END_YEAR (not base year and end year bcause its important the results in OUTLOOK_BASE_YEAR are what we expect) then we can adjust the data for the first period so that the output matches the ESTO data. then we can use the data for the second period as the input data for the outlook model.
#adjusting data will involve:
#rescaling energy use for each fuel type so that the total energy use matches the ESTO data > apply this to the most suitable drive types/vehicle types so its less complicated.
#then based on the new energy use for each vehicle type/drive  type, recalcualte the activity and stocks (given the data which should be constant for mielage/occupancy_load). 
# #done

#hwoever one thing that will be different is that for biofuels demand, we will maek the 'supplyside share of biofeusl demand equivalent to the share of biofuels in the esto data.

##########
#take in input data we will adjsut: (is this needed. can jsut use model output detailed)
# input_data_new.to_csv('intermediate_data/model_inputs/input_data_new.csv', index=False)
# non_input_data_new.to_csv('intermediate_data/model_inputs/non_input_data_new.csv', index=False)

#take in supply side fuel shares:
# supply_side_fuel_mixing = pd.read_csv('intermediate_data\model_inputs\supply_side_fuel_mixing_COMPGEN.csv')

#take in energy use by fuels
# model_output_all_with_fuels = pd.read_csv('output_data/model_output_with_fuels/{}'.format(model_output_file_name))

#take in detailed data output so we can adjsut the stocks and activity for the first period
# model_output_detailed.to_csv('output_data/model_output_detailed/{}'.format(model_output_file_name), index=False)
#take in esto data:


#aslo note that esto data is by medium. i think it ha road split into freight and passenger transport types too.
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
from runpy import run_path
import sys
sys.path.append("./workflow")
exec(open("config/config.py").read())#usae this to load libraries and set variables. Feel free to edit that file as you need

import utility_functions

#%%
date_id = utility_functions.get_latest_date_for_data_file('../transport_data_system/intermediate_data/EGEDA/', 'model_input_9th_cleaned')
energy_use_esto = pd.read_csv(f'../transport_data_system/intermediate_data/EGEDA/model_input_9th_cleanedDATE{date_id}.csv')

input_data = pd.read_csv('output_data/model_output_detailed/{}'.format(model_output_file_name))
supply_side_fuel_mixing = pd.read_csv('intermediate_data\model_inputs\supply_side_fuel_mixing_COMPGEN.csv')
energy_use_output = pd.read_csv('output_data/model_output_with_fuels/{}'.format(model_output_file_name))

def adjust_supply_side_fuel_share(energy_use_esto,supply_side_fuel_mixing):
    #find portion of '16_06_biodiesel', '16_05_biogasoline', '16_07_bio_jet_kerosene' out of the toal '07_07_gas_diesel_oil', '07_01_motor_gasoline', '07_x_jet_fuel' in the esto data so we can change the supply side fuel mixing to match:
    energy_use_esto_wide = energy_use_esto.pivot(index=['Economy', 'Date'], columns='Fuel', values='Energy').reset_index()
    energy_use_esto_wide['share_of_gas_diesel_oil'] = energy_use_esto_wide['07_07_gas_diesel_oil']/(energy_use_esto_wide['07_07_gas_diesel_oil']+energy_use_esto_wide['16_06_biodiesel'])
    energy_use_esto_wide['share_of_motor_gasoline'] = energy_use_esto_wide['07_01_motor_gasoline']/(energy_use_esto_wide['07_01_motor_gasoline']+energy_use_esto_wide['16_05_biogasoline'])
    # energy_use_esto_wide['share_of_jet_fuel'] = energy_use_esto_wide['07_x_jet_fuel']/(energy_use_esto_wide['07_x_jet_fuel']+energy_use_esto_wide['16_07_bio_jet_kerosene'])

    #manually create dfs then concat them:
    share_of_gas_diesel_oil = energy_use_esto_wide[['Economy', 'Date', 'share_of_gas_diesel_oil']].copy()
    #create cols for each fuel type:
    share_of_gas_diesel_oil['Fuel'] = '07_07_gas_diesel_oil'
    share_of_gas_diesel_oil['New_fuel'] = '16_06_biodiesel'
    share_of_gas_diesel_oil = share_of_gas_diesel_oil.rename(columns={'share_of_gas_diesel_oil': 'Supply_side_fuel_share'})

    share_of_motor_gasoline = energy_use_esto_wide[['Economy', 'Date', 'share_of_motor_gasoline']].copy()
    share_of_motor_gasoline['Fuel'] = '07_01_motor_gasoline'
    share_of_motor_gasoline['New_fuel'] = '16_05_biogasoline'
    share_of_motor_gasoline = share_of_motor_gasoline.rename(columns={'share_of_motor_gasoline': 'Supply_side_fuel_share'})

    # share_of_jet_fuel = energy_use_esto_wide[['Economy', 'Date', 'share_of_jet_fuel']].copy()
    # share_of_jet_fuel['Fuel'] = '07_x_jet_fuel'
    # share_of_jet_fuel['New_fuel'] = '16_07_bio_jet_kerosene'
    #rename share_of_jet_fuel to Supply_side_fuel_share
    # share_of_jet_fuel = share_of_jet_fuel.rename(columns={'share_of_jet_fuel': 'Supply_side_fuel_share'})

    #concat them and then join to supplu_side_fuel_mixing, then swap supply_side_fuel_share for the new one, where available:
    new_share = pd.concat([share_of_gas_diesel_oil, share_of_motor_gasoline])#, share_of_jet_fuel])
    supply_side_fuel_mixing_new = supply_side_fuel_mixing.merge(new_share, on=['Economy', 'Date', 'Fuel','New_fuel'], how='left', suffixes=('', '_new')).copy()
    #where there is a new share, use that, otherwise use the old one
    supply_side_fuel_mixing_new['Supply_side_fuel_share'] = supply_side_fuel_mixing_new['Supply_side_fuel_share_new'].fillna(supply_side_fuel_mixing_new['Supply_side_fuel_share'])
    #drop Supply_side_fuel_share_new
    supply_side_fuel_mixing_new = supply_side_fuel_mixing_new.drop(columns=['Supply_side_fuel_share_new'])
    
    return supply_side_fuel_mixing_new
#filter for REF only in input data (since we want both scnearios to have matching input data)
# ['Scenario'] == 'Reference']

#make energy_use_esto match the format of energy_use_output for ref scenario
#drop any aggregate fuels from energy_use_esto

#%%
def format_energy_use_for_rescaling(energy_use_esto, energy_use_output):
    #FORMAT ENERGY USE DFS
    #rename Fuel_Type to Fuel in energy_use_all_fuels
    energy_use_esto = energy_use_esto.rename(columns={'Fuel_Type': 'Fuel', 'Value': 'Energy'})
    #drop these fuels and then check for any otehrs that are missing
    esto_fuels_to_remove = ['01_coal',
    '07_petroleum_products',
    '19_total',
    '21_modern_renewables',
    '08_gas',
    '07_06_kerosene',
    '02_coal_products',
    '01_01_coking_coal',
    '01_05_lignite',
    '06_01_crude_oil',
    '06_crude_oil_and_ngl',
    '03_peat',
    '08_03_gas_works_gas',
    '16_others',
    '20_total_renewables',
    '06_02_natural_gas_liquids']
    energy_use_esto = energy_use_esto[~energy_use_esto['Fuel'].isin(esto_fuels_to_remove)]

    #these are fuels that arent in the esto data because they arent reported on, so we just need to make sure that their sums are 0 in the mdoel input data
    model_fuels_to_ignore = ['16_x_hydrogen', '01_x_coal_thermal', '16_x_efuel', '16_07_bio_jet_kerosene', '01_x_thermal_coal']

    missing_fuels = [fuel for fuel in energy_use_output.Fuel.unique() if fuel not in energy_use_esto.Fuel.unique()] + [fuel for fuel in energy_use_esto.Fuel.unique() if fuel not in energy_use_output.Fuel.unique()]

    missing_fuels = [fuel for fuel in missing_fuels if fuel not in model_fuels_to_ignore]
    
    if len(missing_fuels)>0:
        print('missing fuels in energy_use_esto')
        print(missing_fuels)
        raise ValueError('missing fuels in energy_use_esto')

    #drop nonneeded cols
    energy_use_esto = energy_use_esto.drop(columns=['Frequency', 'Source', 'Medium','Dataset', 'Measure', 'Vehicle Type', 'Drive', 'Transport Type', 'Unit'])

    energy_use_esto['Date'] = energy_use_esto['Date'].apply(lambda x: x[:4])
    energy_use_esto['Date'] = energy_use_esto['Date'].astype(int)
    #drop economy in APEC '22_SEA', '23_NEA', '23b_ONEA', '24_OAM', '24b_OOAM', '25_OCE'
    energy_use_esto = energy_use_esto.loc[~energy_use_esto['Economy'].isin(['22_SEA', '23_NEA', '23b_ONEA', '24_OAM', '24b_OOAM', '25_OCE', 'APEC'])].copy()
    
    ##############
    #add the fuels in model_fuels_to_ignore for each unique Economy and Date:
    #Create a new DataFrame for the new fuels.
    new_fuels = pd.DataFrame()
    #Get unique Economy-Date combinations.
    economy_date_combinations = energy_use_esto[['Economy', 'Date']].drop_duplicates()
    #Iterate through each unique combination of Economy and Date.
    for _, row in economy_date_combinations.iterrows():
        economy, date = row['Economy'], row['Date']
        
        #For each fuel to ignore, create a new row with the current Economy and Date.
        for fuel in model_fuels_to_ignore:
            new_row = {'Economy': economy, 'Date': date, 'Fuel': fuel, 
                    'Energy': 0} 
            new_fuels = pd.concat([new_fuels, pd.DataFrame(new_row, index=[0])])

    #Concatenate the new fuels with the original DataFrame.
    energy_use_esto = pd.concat([energy_use_esto, new_fuels])
    
    energy_use_esto = energy_use_esto.groupby(['Economy', 'Date', 'Fuel']).sum().reset_index()
    ##############
    
    #NOW CLEAN UP ENERGY_USE_OUTPUT
    energy_use_output_ref = energy_use_output.loc[energy_use_output['Scenario'] == 'Reference'].copy()
    energy_use_output_ref = energy_use_output_ref.drop(columns=[ 'Vehicle Type', 'Drive', 'Transport Type']).groupby(['Economy', 'Date', 'Fuel']).sum().reset_index()
    #GRAB DATA ONLY FOR DATES WITH WHICH WE HAVE ESTO DATA
    energy_use_output_ref = energy_use_output_ref.loc[energy_use_output_ref['Date'].isin(energy_use_esto['Date'].unique())].copy()
    #LIEKWISE FOR ESTO
    energy_use_esto = energy_use_esto.loc[energy_use_esto['Date'].isin(energy_use_output_ref['Date'].unique())].copy()
    #NOW find the ratio between energy use in the model and energy use in the esto data. So merge the dfs and then find it
    
    breakpoint()
    energy_use_merged = energy_use_esto.merge(energy_use_output_ref, on=['Economy', 'Date', 'Fuel'], how='left', suffixes=('_esto', '_model'))
    #reaplce nans in Energy_esto and Energy	_model with 0
    energy_use_merged['Energy_esto'] = energy_use_merged['Energy_esto'].fillna(0)
    energy_use_merged['Energy_model'] = energy_use_merged['Energy_model'].fillna(0)
    #calcaulte ratio so that ratio times energy in the model = eneerhy in the esto data
    energy_use_merged['ratio'] = energy_use_merged['Energy_esto']/energy_use_merged['Energy_model']
    
    # #set the biofuels ratio to 1 as they are ahdnled by supply side fuel mixing
    # energy_use_merged.loc[energy_use_merged['Fuel'].isin(['16_06_biodiesel', '16_05_biogasoline']), 'ratio'] = 1
    #drop biofuels as they are handled by supply side fuel mixing
    energy_use_merged = energy_use_merged.loc[~energy_use_merged['Fuel'].isin(['16_06_biodiesel', '16_05_biogasoline'])].copy()
    #and drop any fuels we want to ignore
    #where ratio becomes inf then this means that ESTO has >0 energy use and the model has 0 energy use. This is because the model didnt assume any use at that point in time. So create anotehr col and call it 'addition' and put the Energy_esto value in ther to be split among its users later:
    energy_use_merged['addition'] = 0
    energy_use_merged.loc[energy_use_merged['ratio'] == np.inf, 'addition'] = energy_use_merged.loc[energy_use_merged['ratio'] == np.inf, 'Energy_esto']
    
    #also where ratio is na, its because both values are 0, so just set ratio to 0
    energy_use_merged['ratio'] = energy_use_merged['ratio'].fillna(0)
    
    return energy_use_merged, energy_use_esto, energy_use_output_ref

#%%
energy_use_merged, energy_use_esto, energy_use_output_ref = format_energy_use_for_rescaling(energy_use_esto, energy_use_output)
#%%
supply_side_fuel_mixing_new = adjust_supply_side_fuel_share(energy_use_esto,supply_side_fuel_mixing)
#now use this on the detailed data to get the new energy use and resulting stocks/activity

#CLEAN INPUT DATA 
#get dates that match the esto data:
input_data_new = input_data.loc[input_data['Date'].isin(energy_use_merged['Date'].unique())].copy()
input_data_new = input_data_new.loc[input_data_new['Scenario'] == 'Reference'].copy()
#we want to merge with energy_use_merged to get the ratio, however input datadoesnt contain a fuel col. BUT we can map to the same index cols in energy_use_output then merge.
index_cols = ['Date', 'Economy', 'Vehicle Type', 'Medium', 'Transport Type', 'Drive']
index_cols_df = energy_use_output.loc[energy_use_output['Scenario'] == 'Reference'].copy()
index_cols_merge = energy_use_merged.merge(index_cols_df.drop(columns=['Energy']), on=['Economy', 'Date', 'Fuel'], how='left')

#to fix issues where some index cols use multiple fuels, drop some :
#for rail, keep only 01_x_thermal_coal
# index_cols_merge = index_cols_merge.loc[~((index_cols_merge['Transport Type'] == 'Rail') & (index_cols_merge['Fuel'] != '01_x_thermal_coal'))].copy()

#we need to find a way to handle fuels in rail and ship. mayve can name rail and ship as rail_fuel_oil or ship_fuel_oil and so on. Would need to hadnle this from th start 

# #make sure there are no duplcaites when you drop the fuel column. thi would cause unexpected results (it occurs where there are multiple fuels for the same index cols - which can be expected because things lik rail use coal, elec and diesel)
dupes = index_cols_merge[index_cols_merge.duplicated(subset=index_cols)]
if len(dupes) > 0:
    raise ValueError('duplicates in index_cols_merge')
input_data_new = input_data_new.merge(index_cols_merge, on=index_cols, how='left')
#%%
#times the Energy sue by the ratio to get new energy use then recalcaulte the stocks and activity and other values
input_data_new['Energy'] = input_data_new['Energy']*input_data_new['ratio']

input_data_new['Travel_km'] = input_data_new['Energy'] * input_data_new['Efficiency']

input_data_new['Activity'] = input_data_new['Travel_km'] * input_data_new['Occupancy_or_load']

input_data_new['Stocks'] = input_data_new['Activity'] / (input_data_new['Mileage'] * input_data_new['Occupancy_or_load'])

#drop unneeded cols
input_data_new = input_data_new.drop(columns=['ratio', 'Energy_esto','Energy_model'])

#check for nas and stiff
# input_data = pd.read_csv('output_data/model_output_detailed/{}'.format(model_output_file_name))
# supply_side_fuel_mixing = pd.read_csv('intermediate_data\model_inputs\supply_side_fuel_mixing_COMPGEN.csv')

#%%
def split_non_road_into_drive_types():
    