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



def adjust_supply_side_fuel_share(energy_use_esto,supply_side_fuel_mixing):
    #find portion of '16_06_biodiesel', '16_05_biogasoline', '16_07_bio_jet_kerosene' out of the toal '07_07_gas_diesel_oil', '07_01_motor_gasoline', '07_x_jet_fuel' in the esto data so we can change the supply side fuel mixing to match:
    energy_use_esto_wide = energy_use_esto.groupby(['Economy', 'Date', 'Fuel']).sum().reset_index()
    energy_use_esto_wide = energy_use_esto_wide.pivot(index=['Economy', 'Date'], columns='Fuel', values='Energy').reset_index()
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


def format_energy_use_for_rescaling(energy_use_esto, energy_use_output, spread_non_specified_and_separate_pipeline = True, remove_annoying_fuels = True, TESTING=False):
    #FORMAT ENERGY USE DFS
    #rename Fuel_Type to Fuel in energy_use_all_fuels
    energy_use_esto = energy_use_esto.rename(columns={'Fuel_Type': 'Fuel', 'Value': 'Energy'})
    #drop these fuels and then check for any otehrs that are missing
    esto_fuels_to_remove = ['01_coal',
    '07_petroleum_products',
    '19_total',
    '21_modern_renewables',
    '08_gas',
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
    model_fuels_to_ignore = ['16_x_ammonia','16_x_efuel', '16_x_hydrogen', '16_07_bio_jet_kerosene']

    missing_fuels = [fuel for fuel in energy_use_output.Fuel.unique() if fuel not in energy_use_esto.Fuel.unique()] + [fuel for fuel in energy_use_esto.Fuel.unique() if fuel not in energy_use_output.Fuel.unique()]

    missing_fuels = [fuel for fuel in missing_fuels if fuel not in model_fuels_to_ignore]
    
    if len(missing_fuels)>0:
        print('missing fuels in energy_use_esto')
        print(missing_fuels)
        raise ValueError('missing fuels in energy_use_esto')

    #drop nonneeded cols
    energy_use_esto = energy_use_esto.drop(columns=['Frequency', 'Source', 'Dataset', 'Measure', 'Vehicle Type', 'Drive', 'Transport Type', 'Unit'])

    if not TESTING:
        energy_use_esto['Date'] = energy_use_esto['Date'].apply(lambda x: x[:4])
        energy_use_esto['Date'] = energy_use_esto['Date'].astype(int)
    #drop economy in APEC '22_SEA', '23_NEA', '23b_ONEA', '24_OAM', '24b_OOAM', '25_OCE'
    energy_use_esto = energy_use_esto.loc[~energy_use_esto['Economy'].isin(['22_SEA', '23_NEA', '23b_ONEA', '24_OAM', '24b_OOAM', '25_OCE', 'APEC'])].copy()
    if spread_non_specified_and_separate_pipeline:
        #separate pipeline and nonspecified mediums in energy use esto. they will be dealt with by the transport model at a later date
        energy_use_esto_pipeline = energy_use_esto.loc[energy_use_esto['Medium'] == 'pipeline'].copy()
        energy_use_esto_nonspecified = energy_use_esto.loc[energy_use_esto['Medium'] == 'nonspecified'].copy()
        energy_use_esto = energy_use_esto.loc[~energy_use_esto['Medium'].isin(['pipeline', 'nonspecified'])].copy()
        
        #add Fuel 07_08_fuel_oil and 07_06_kerosene use in road to the non specified amount and spread it with nonspecifieds energy use. This is because we dont have any info on these uses and they are minmimal so mimght as well drop them in with the nonspecifieds
        if remove_annoying_fuels:
            annoying_road_fuels_df = energy_use_esto.loc[(energy_use_esto['Medium'] == 'road') & (energy_use_esto['Fuel'].isin(['07_08_fuel_oil', '07_06_kerosene']))].copy()
            energy_use_esto = energy_use_esto.loc[~((energy_use_esto['Medium'] == 'road') & (energy_use_esto['Fuel'].isin(['07_08_fuel_oil', '07_06_kerosene'])))].copy()
            #set meidum to nonspecified
            annoying_road_fuels_df['Medium'] = 'nonspecified'
            energy_use_esto_nonspecified = pd.concat([energy_use_esto_nonspecified, annoying_road_fuels_df]).groupby(['Economy', 'Date', 'Fuel', 'Medium']).sum().reset_index()
            
        #spread energy_use_esto_nonspecified among all mediums for that fuel, eocnomy and date. Use the % of each energy use to the total energy use for that fuel, economy and date to do this:
        energy_use_esto['proportion_of_group'] = energy_use_esto.groupby(['Economy', 'Date', 'Fuel'])['Energy'].transform(lambda x: x/x.sum())
        #join the nonspec col on
        energy_use_esto = energy_use_esto.merge(energy_use_esto_nonspecified, on=['Economy', 'Date', 'Fuel'], how='left', suffixes=('', '_nonspec'))
        #times the proportion of group by the nonspec energy use to get the new energy use, then add that to enegry
        energy_use_esto['Energy'] = energy_use_esto['Energy'] + (energy_use_esto['proportion_of_group']*energy_use_esto['Energy_nonspec'])
        energy_use_esto = energy_use_esto.drop(columns=['Energy_nonspec', 'proportion_of_group'])
    else:
        energy_use_esto_pipeline = pd.DataFrame()
        
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
    
    energy_use_esto = energy_use_esto.groupby(['Economy', 'Medium','Date', 'Fuel']).sum().reset_index()
    ##############NOW HANDLE THE OUTPUT FROM MODEL
    
    # #We have to adjust the non road mediums drive type to its more specific verison. So pull in model concordances and adjsut them:
    # #load model concordances with fuels
    # model_concordances_fuels = pd.read_csv('config/concordances_and_config_data/computer_generated_concordances/{}'.format(model_concordances_file_name_fuels))
    # #and based on the Fuel and medium col, replace the drive type with the new one, for non road only:
    # model_concordances_fuels = model_concordances_fuels.loc[model_concordances_fuels['Medium'] != 'road'].copy()
    # model_concordances_fuels = model_concordances_fuels[['Fuel', 'Medium', 'Drive']].drop_duplicates()
    # model_concordances_fuels.rename(columns={'Drive': 'New_drive'}, inplace=True)
    # energy_use_output = energy_use_output.merge(model_concordances_fuels, on=['Fuel', 'Medium'], how='left')
    # energy_use_output['Drive'] = energy_use_output['New_drive'].fillna(energy_use_output['Drive']).copy()
    # #drop New_drive
    # energy_use_output = energy_use_output.drop(columns=['New_drive'])
    
    
    #NOW CLEAN UP ENERGY_USE_OUTPUT
    energy_use_output_ref = energy_use_output.loc[energy_use_output['Scenario'] == 'Reference'].copy()
    
    #and drop any drive in demand side fuel mixing as its to complicated to decrease tehir energy use like we will do. 
    demand_side_fuel_mixing_drives = pd.read_csv('intermediate_data\model_inputs\demand_side_fuel_mixing_COMPGEN.csv')['Drive'].unique().tolist()
    energy_use_output_ref = energy_use_output_ref.loc[~energy_use_output_ref['Drive'].isin(demand_side_fuel_mixing_drives)].copy()
    
    energy_use_output_ref = energy_use_output_ref.drop(columns=[ 'Vehicle Type', 'Drive', 'Transport Type']).groupby(['Economy', 'Date', 'Medium', 'Fuel']).sum().reset_index()
    #GRAB DATA ONLY FOR DATES WITH WHICH WE HAVE ESTO DATA
    energy_use_output_ref = energy_use_output_ref.loc[energy_use_output_ref['Date'].isin(energy_use_esto['Date'].unique())].copy()
    #LIEKWISE FOR ESTO
    energy_use_esto = energy_use_esto.loc[energy_use_esto['Date'].isin(energy_use_output_ref['Date'].unique())].copy()
    #########################
    #NOW find the ratio between energy use in the model and energy use in the esto data. So merge the dfs and then find it
    
    energy_use_merged = energy_use_esto.merge(energy_use_output_ref, on=['Economy', 'Date', 'Medium','Fuel'], how='left', suffixes=('_esto', '_model'))
    #reaplce nans in Energy_esto and Energy	_model with 0
    energy_use_merged['Energy_esto'] = energy_use_merged['Energy_esto'].fillna(0)
    energy_use_merged['Energy_model'] = energy_use_merged['Energy_model'].fillna(0)
    #calcaulte ratio so that ratio times energy in the model = eneerhy in the esto data. Then we will timesz this ratio by energy uise in the model to get the new energy use (and the effect of timesing by the ratio will be that the total difference for that ['Economy', 'Date', 'Medium','Fuel'] spread equally among all rows for that ['Economy', 'Date', 'Medium','Fuel') (except for supply side fuel mixing fuels, which we will handle separately, and demand side fuel mixing fuels, which we will drop as they are too ahrd to handle)
    #breakpoint()
    energy_use_merged['ratio'] = energy_use_merged['Energy_esto']/energy_use_merged['Energy_model']
    
    # #set the biofuels ratio to 1 as they are ahdnled by supply side fuel mixing
    # energy_use_merged.loc[energy_use_merged['Fuel'].isin(['16_06_biodiesel', '16_05_biogasoline']), 'ratio'] = 1
    #drop any supply side fuel mixing fuels:
    supply_side_fuel_mixing_fuels = pd.read_csv('intermediate_data\model_inputs\supply_side_fuel_mixing_COMPGEN.csv')['New_fuel'].unique().tolist()
    energy_use_merged = energy_use_merged.loc[~energy_use_merged['Fuel'].isin(supply_side_fuel_mixing_fuels)].copy()
    
    #and drop any fuels we want to ignore
    #where ratio becomes inf then this means that ESTO has >0 energy use and the model has 0 energy use. This is because the model didnt assume any use at that point in time. So create anotehr col and call it 'addition' and put the Energy_esto value in ther to be split among its users later:
    energy_use_merged['addition'] = 0
    energy_use_merged.loc[energy_use_merged['ratio'] == np.inf, 'addition'] = energy_use_merged.loc[energy_use_merged['ratio'] == np.inf, 'Energy_esto']
    #then replace the inf with 1
    energy_use_merged.loc[energy_use_merged['ratio'] == np.inf, 'ratio'] = 1
    
    #also where ratio is na, its because both values are 0, so just set ratio to 0
    energy_use_merged['ratio'] = energy_use_merged['ratio'].fillna(0)
    ()
    return energy_use_merged, energy_use_esto, energy_use_output_ref, energy_use_esto_pipeline,energy_use_output


#############

def adjust_energy_use_in_input_data(input_data_based_on_previous_model_run,energy_use_merged,road_model_input_wide,non_road_model_input_wide,energy_use_output,TESTING):
    breakpoint()
    #CLEAN INPUT DATA 
    #get dates that match the esto data:
    input_data_new = input_data_based_on_previous_model_run.loc[input_data_based_on_previous_model_run['Date'].isin(energy_use_merged['Date'].unique())].copy()
    input_data_new = input_data_new.loc[input_data_new['Scenario'] == 'Reference'].copy()
    #Edit the Drives for mediums base don fuel, using concordances:
    #thjois wont work because this df doesnt ahve fuel col
    # #We have to adjust the non road mediums drive type to its more specific verison. So pull in model concordances and adjsut them:
    # #load model concordances with fuels
    # model_concordances_fuels = pd.read_csv('config/concordances_and_config_data/computer_generated_concordances/{}'.format(model_concordances_file_name_fuels))
    # #and based on the Fuel and medium col, replace the drive type with the new one, for non road only:
    # model_concordances_fuels = model_concordances_fuels.loc[model_concordances_fuels['Medium'] != 'road'].copy()
    # model_concordances_fuels = model_concordances_fuels[['Fuel', 'Medium', 'Drive']].drop_duplicates()
    # model_concordances_fuels.rename(columns={'Drive': 'New_drive'}, inplace=True)
    # input_data_new = input_data_new.merge(model_concordances_fuels, on=['Fuel', 'Medium'], how='left')
    # input_data_new['Drive'] = input_data_new['New_drive'].fillna(input_data_new['Drive']).copy()
    # #drop New_drive
    # input_data_new = input_data_new.drop(columns=['New_drive'])
    
    
    
    
    #we want to merge with energy_use_merged to get the ratio, however input data doesnt contain a fuel col. BUT we can map to the same index cols in energy_use_output then merge.
    index_cols = ['Date', 'Economy', 'Vehicle Type', 'Medium', 'Transport Type', 'Drive']
    index_cols_df = energy_use_output.loc[energy_use_output['Scenario'] == 'Reference'].copy()
    #drop Scenario
    index_cols_df = index_cols_df.drop(columns=['Scenario'])
    #and drop any drive in demand side fuel mixing as its to complicated to decrease tehir energy use like we will do. (we also did this in energy_use_output_ref, but we need to do it here again too)
    demand_side_fuel_mixing_drives = pd.read_csv('intermediate_data\model_inputs\demand_side_fuel_mixing_COMPGEN.csv')['Drive'].unique().tolist()
    index_cols_df = index_cols_df.loc[~index_cols_df['Drive'].isin(demand_side_fuel_mixing_drives)].copy()

    #drop nonnecessary cols from energy_use_merged
    if not TESTING:
        energy_use_merged = energy_use_merged.drop(columns=['Energy_esto', 'Energy_model'])
    
    #now do the merge
    index_cols_merge = energy_use_merged.merge(index_cols_df.drop(columns=['Energy']), on=['Economy', 'Date','Medium', 'Fuel'], how='left')

    # #make sure there are no duplcaites when you drop the fuel column. thi would cause unexpected results (it occurs where there are multiple fuels for the same index cols - which can be expected because things lik rail use coal, elec and diesel)
    index_cols_merge = index_cols_merge[index_cols_merge.Date>=BASE_YEAR]
    dupes = index_cols_merge[index_cols_merge.duplicated(subset=index_cols)]
    if len(dupes) > 0:
        breakpoint()
        raise ValueError('duplicates in index_cols_merge')

    input_data_new = input_data_new.merge(index_cols_merge, on=index_cols, how='left')

    #drop Fuel
    input_data_new = input_data_new.drop(columns=['Fuel'])

    #not sure about this one but where ratio is na it is because we either removed it or it wasnt in the estpo data, i think? anyway, set it to 1 and later we can work out whetehr to keep it or not
    do_this = True
    if do_this:
        input_data_new['ratio'] = input_data_new['ratio'].fillna(1)
        
    #do the ratio times enegry calc":
    input_data_new['Energy'] = input_data_new['Energy']*input_data_new['ratio']

    #additions need to be split equally where they are made. do this using the proprtion of each energy use out of the total energy use for that fuel, medium, economy and date to do this:
    input_data_new['proportion_of_group'] = input_data_new.groupby(['Economy', 'Date', 'Medium'])['Energy'].transform(lambda x: x/x.sum())

    input_data_new['addition'] = input_data_new['addition']*input_data_new['proportion_of_group'].replace(np.nan, 0)
    #now need to add any additions to the Energy. this is where the ratio was inf because the model had 0 energy use but the esto data had >0. so we will add the esto data energy use to the model data energy use and just times by a ratio of 1
    input_data_new['Energy'] = input_data_new['Energy'] + input_data_new['addition'].replace(np.nan, 0)



    #split into medium = road and not, then recalcualte the other measures. for road we will calcuialte travel km and activity and stocks, wehreas for non road we will just recalcualte energy use using itnsntiy instead of effcieincy
    #road:
    input_data_new_road = input_data_new.loc[input_data_new['Medium'] == 'road'].copy()

    input_data_new_road['Travel_km'] = input_data_new_road['Energy'] * input_data_new_road['Efficiency']

    input_data_new_road['Activity'] = input_data_new_road['Travel_km'] * input_data_new_road['Occupancy_or_load']

    input_data_new_road['Stocks'] = input_data_new_road['Activity'] / (input_data_new_road['Mileage'] * input_data_new_road['Occupancy_or_load'])

    #drop unneeded cols
    input_data_new_road = input_data_new_road.drop(columns=['ratio','addition','proportion_of_group'])
    
    #non road:
    input_data_new_non_road = input_data_new.loc[input_data_new['Medium'] != 'road'].copy()
    input_data_new_non_road = input_data_new_non_road.drop(columns=['ratio','addition','proportion_of_group'])
    input_data_new_non_road['Activity'] = input_data_new_non_road['Energy'] * input_data_new_non_road['Intensity']
    
    input_data_new_non_road.loc[(input_data_new_non_road['Energy'] > 0), 'Stocks'] = 1
    input_data_new_non_road.loc[(input_data_new_non_road['Energy'] == 0), 'Stocks'] = 0

    #drop cols unneeded for non road, by filtering tfor the same cols that are in non_road_model_input_wide
    input_data_new_non_road = input_data_new_non_road.loc[:, input_data_new_non_road.columns.isin(non_road_model_input_wide.columns)].copy()

    ###############
    #replicate the dfs for the other scenarios
    
    # for scenario in SCENARIOS_LIST:
        
    
    # #check for nas and stiff
    # nas = input_data_new_road.loc[input_data_new_road.isna().any(axis=1)]
    # if len(nas) > 0:
    #     #show where they are
    #     print(nas)

    # nas = input_data_new_non_road.loc[input_data_new_non_road.isna().any(axis=1)]
    # if len(nas) > 0:
    #     #show where they are
    #     print(nas)
    ##########
    #now, this is meant to be the output used by run road model and non road. we nmeed ot merge it inot the outputs from calculate_inputs_for_model.py so that it can be used by run_road_model.py and run_non_road_model.py. 
    #so we'll melt both the new input data and the orignal input data for road and non road, so that the measures are in one col and the values are in another. then we can merge them on the measures col and  replace values where they are new, then pivot bacc to wide format
    #breakpoint()
    input_data_new_non_road = input_data_new_non_road.melt(id_vars=['Date', 'Economy', 'Medium','Vehicle Type', 'Transport Type', 'Drive'], var_name='Measure', value_name='Value')
    non_road_model_input = non_road_model_input_wide.melt(id_vars=['Date', 'Economy', 'Medium','Vehicle Type', 'Transport Type', 'Drive', 'Scenario'], var_name='Measure', value_name='Value')
    #join to original input data
    non_road_all = non_road_model_input.merge(input_data_new_non_road, on=['Date', 'Economy', 'Medium','Vehicle Type', 'Transport Type', 'Drive', 'Measure'], how='left', suffixes=('', '_new'))

    #for the measures we havent already calcualted suing new energy, we should fillna with the old values.
    measures_to_not_fillna = ['Activity', 'Energy']
    non_road_all_measures_to_fillna = non_road_all.loc[~non_road_all['Measure'].isin(measures_to_not_fillna)].copy()
    non_road_all_measures_to_fillna['Value'] = non_road_all_measures_to_fillna['Value_new'].fillna(non_road_all_measures_to_fillna['Value'])
    non_road_other = non_road_all.loc[non_road_all['Measure'].isin(measures_to_not_fillna)].copy()
    non_road_other['Value'] = non_road_other['Value_new']
    non_road_all = pd.concat([non_road_all_measures_to_fillna, non_road_other]).copy()
    
    #drop Value_new
    non_road_all = non_road_all.drop(columns=['Value_new'])
    #pivot back to wide format
    non_road_all_wide = non_road_all.pivot_table(index=['Date', 'Economy', 'Medium', 'Transport Type', 'Drive','Vehicle Type',  'Scenario'], columns='Measure', values='Value').reset_index()
    # breakpoint()
    ########
    #do same for road
    input_data_new_road_long = input_data_new_road.melt(id_vars=['Date', 'Economy', 'Medium', 'Transport Type','Vehicle Type',  'Drive'], var_name='Measure', value_name='Value')
    road_model_input = road_model_input_wide.melt(id_vars=['Date', 'Economy', 'Medium', 'Transport Type','Vehicle Type',  'Scenario', 'Drive'],  var_name='Measure', value_name='Value')
    #join to original input data
    road_all = road_model_input.merge(input_data_new_road_long, on=['Date', 'Economy', 'Medium', 'Transport Type','Vehicle Type', 'Drive', 'Measure'], how='left', suffixes=('', '_new'))

    #for the measures we havent already calcualted suing new energy, we should fillna with the old values. otherwise only use the new values.
    measures_to_not_fillna = ['Activity', 'Stocks', 'Travel_km', 'Energy']
    road_all_measures_to_fillna = road_all.loc[~road_all['Measure'].isin(measures_to_not_fillna)].copy()
    road_all_measures_to_fillna['Value'] = road_all_measures_to_fillna['Value_new'].fillna(road_all_measures_to_fillna['Value'])
    road_other = road_all.loc[road_all['Measure'].isin(measures_to_not_fillna)].copy()
    road_other['Value'] = road_other['Value_new']
    road_all = pd.concat([road_all_measures_to_fillna, road_other]).copy()
    
    #drop Value_new
    road_all = road_all.drop(columns=['Value_new'])
    #pivot back to wide format
    road_all_wide = road_all.pivot_table(index=['Date', 'Economy', 'Medium', 'Transport Type','Vehicle Type',  'Scenario', 'Drive'], columns='Measure', values='Value').reset_index()

    ##########TESTINGOVER###############
    #remove Activity_growth freom both road and non road as its been a bit corrupted by the above process
    road_all_wide = road_all_wide.drop(columns=['Activity_growth'])
    non_road_all_wide = non_road_all_wide.drop(columns=['Activity_growth'])
    #then add it back fromroad_model_input_wide amnd non_road_model_input_wide:
    road_all_wide = road_all_wide.merge(road_model_input_wide[['Date', 'Economy', 'Medium', 'Transport Type','Vehicle Type',  'Scenario', 'Drive', 'Activity_growth']], on=['Date', 'Economy', 'Medium', 'Transport Type','Vehicle Type',  'Scenario', 'Drive'], how='left')
    non_road_all_wide = non_road_all_wide.merge(non_road_model_input_wide[['Date', 'Economy', 'Medium', 'Transport Type','Vehicle Type',  'Scenario', 'Drive', 'Activity_growth']], on=['Date', 'Economy', 'Medium', 'Transport Type','Vehicle Type',  'Scenario', 'Drive'], how='left')
    
        
    return road_all_wide, non_road_all_wide


def adjust_data_to_match_esto(road_model_input_wide,non_road_model_input_wide,advance_base_year=True,TESTING=False):
    # breakpoint()
    date_id = utility_functions.get_latest_date_for_data_file('../transport_data_system/intermediate_data/EGEDA/', 'model_input_9th_cleaned')
    energy_use_esto = pd.read_csv(f'../transport_data_system/intermediate_data/EGEDA/model_input_9th_cleanedDATE{date_id}.csv')
    
    input_data_based_on_previous_model_run = pd.read_csv('output_data/model_output_detailed/NON_ROAD_DETAILED_{}'.format(model_output_file_name))
    supply_side_fuel_mixing = pd.read_csv('intermediate_data\model_inputs\supply_side_fuel_mixing_COMPGEN.csv')
    energy_use_output = pd.read_csv('output_data/model_output_with_fuels/NON_ROAD_DETAILED_{}'.format(model_output_file_name))
    
    if TESTING:
        
        #filter for only 01_AUS and year <= 2025 to make it run faster
        road_model_input_wide = road_model_input_wide[(road_model_input_wide['Economy'] == '01_AUS' ) & (road_model_input_wide['Date'] <= 2025)]
        non_road_model_input_wide = non_road_model_input_wide[(non_road_model_input_wide['Economy'] == '01_AUS') & (non_road_model_input_wide['Date'] <= 2025)]
        
        #filter for only 01_AUS to make it run faster  and year <= 2025 
        supply_side_fuel_mixing = supply_side_fuel_mixing[supply_side_fuel_mixing['Economy'] == '01_AUS'].copy()
        input_data_based_on_previous_model_run = input_data_based_on_previous_model_run[input_data_based_on_previous_model_run['Economy'] == '01_AUS'].copy()
        #filter for only 01_AUS to make it run faster  and year <= 2025 
        energy_use_output = energy_use_output[energy_use_output['Economy'] == '01_AUS'].copy()
        energy_use_esto = energy_use_esto[energy_use_esto['Economy'] == '01_AUS'].copy()
        #  and year <= 2025 
        supply_side_fuel_mixing = supply_side_fuel_mixing[supply_side_fuel_mixing['Date'] <= 2025].copy()
        input_data_based_on_previous_model_run = input_data_based_on_previous_model_run[input_data_based_on_previous_model_run['Date'] <= 2025].copy()
        
        energy_use_esto['Date'] = energy_use_esto['Date'].apply(lambda x: x[:4])
        energy_use_esto['Date'] = energy_use_esto['Date'].astype(int)
        energy_use_esto = energy_use_esto[energy_use_esto['Date'] <= 2025].copy()
        energy_use_output = energy_use_output[energy_use_output['Date'] <= 2025].copy()
    
        breakpoint()
    energy_use_merged, energy_use_esto, energy_use_output_ref,energy_use_esto_pipeline,energy_use_output = format_energy_use_for_rescaling(energy_use_esto, energy_use_output,spread_non_specified_and_separate_pipeline = True, remove_annoying_fuels = True, TESTING=TESTING)

    supply_side_fuel_mixing_new = adjust_supply_side_fuel_share(energy_use_esto,supply_side_fuel_mixing)

    road_all_wide, non_road_all_wide = adjust_energy_use_in_input_data(input_data_based_on_previous_model_run,energy_use_merged,road_model_input_wide,non_road_model_input_wide,energy_use_output,TESTING)
    
    #########
    #now do tests to check data matches expectations:
    #test that the total road enegry use matches the total energy use in the esto data:
    test_output_matches_expectations(road_all_wide, non_road_all_wide, energy_use_merged, advance_base_year=True)
    
    
    return road_all_wide, non_road_all_wide, supply_side_fuel_mixing_new


#why is ratio so high in places? maybe need to fix.
def test_output_matches_expectations(road_all_wide, non_road_all_wide, energy_use_merged, advance_base_year=True):
    breakpoint()
    #calcauklte total energy use by year and economy for both road and non road
    road_all_wide_total_energy_use = road_all_wide.groupby(['Economy','Scenario', 'Date'])['Energy'].sum().reset_index()
    non_road_all_wide_total_energy_use = non_road_all_wide.groupby(['Economy','Scenario', 'Date'])['Energy'].sum().reset_index()
    esto_total_energy_use_non_road = energy_use_merged.loc[(energy_use_merged['Medium'] != 'road')].groupby(['Economy', 'Date'])['Energy_esto'].sum().reset_index()
    esto_total_energy_use_road = energy_use_merged.loc[(energy_use_merged['Medium'] == 'road')].groupby(['Economy', 'Date'])['Energy_esto'].sum().reset_index()
    
    #print the differentce between total energy in the years 2017 to 2022
    print('road energy use difference')
    diff = road_all_wide_total_energy_use.merge(esto_total_energy_use_road, on=['Economy', 'Date'], how='left', suffixes=('', '_esto'))
    if advance_base_year:
        diff = diff.loc[(diff.Date>BASE_YEAR) & (diff.Date<=OUTLOOK_BASE_YEAR)]
    else:
        diff = diff.loc[(diff.Date>=BASE_YEAR) & (diff.Date<=OUTLOOK_BASE_YEAR)]
    print(diff['Energy'].sum() - diff['Energy_esto'].sum())
    diff2 = non_road_all_wide_total_energy_use.merge(esto_total_energy_use_non_road, on=['Economy', 'Date'], how='left', suffixes=('', '_esto'))
    if advance_base_year:
        diff2 = diff2.loc[(diff2.Date>BASE_YEAR) & (diff2.Date<=OUTLOOK_BASE_YEAR)]
    else:
        diff2 = diff2.loc[(diff2.Date>=BASE_YEAR) & (diff2.Date<=OUTLOOK_BASE_YEAR)]
    print('non road energy use difference')
    print(diff2['Energy'].sum() - diff2['Energy_esto'].sum())
    breakpoint()
    ###################TESTING###############
    #now do tests to check data matches expectations:
    #test that the total road enegry use matches the total energy use in the esto data:
    total_road_energy_use = road_all_wide.groupby(['Economy','Scenario', 'Date']).sum().reset_index()
    total_esto_road_energy_use = energy_use_merged.loc[(energy_use_merged['Medium'] == 'road')].groupby(['Economy', 'Date']).sum().reset_index()
    
    total_non_road_energy_use = non_road_all_wide.groupby(['Economy','Scenario', 'Date']).sum().reset_index()
    total_esto_non_road_energy_use = energy_use_merged.loc[(energy_use_merged['Medium'] != 'road')].groupby(['Economy', 'Date']).sum().reset_index()

    diff_road = total_road_energy_use.merge(total_esto_road_energy_use, on=['Economy', 'Date'], how='left', suffixes=('', '_esto'))
    #filter for dates after base year
    if advance_base_year:
        diff_road = diff_road.loc[diff_road.Date>=OUTLOOK_BASE_YEAR]
    else:
        diff_road = diff_road.loc[diff_road.Date>=BASE_YEAR]
    diff_road_proportion = sum(diff_road['Energy'].dropna()) / sum(diff_road['Energy_esto'].dropna())
    
    diff_non_road = total_non_road_energy_use.merge(total_esto_non_road_energy_use, on=['Economy', 'Date'], how='left', suffixes=('', '_esto'))
    if advance_base_year:
        diff_non_road = diff_non_road.loc[diff_non_road.Date>=OUTLOOK_BASE_YEAR]
    else:
        diff_non_road = diff_non_road.loc[diff_non_road.Date>=BASE_YEAR]
    diff_non_road_proportion = sum(diff_non_road['Energy'].dropna()) / sum(diff_non_road['Energy_esto'].dropna())
    if diff_road_proportion > 1.01 or diff_road_proportion < 0.99:
        breakpoint()
        #saev output to csv
        diff_road.to_csv('intermediate_data/errors/ajust_data_to_match_esto_road_energy_use_diff.csv')
        raise ValueError('road energy use does not match esto')
    if diff_non_road_proportion > 1.01 or diff_non_road_proportion < 0.99:
        breakpoint()
        diff_non_road.to_csv('intermediate_data/errors/ajust_data_to_match_esto_non_road_energy_use_diff.csv')
        raise ValueError('non road energy use does not match esto')
    ##########TESTING###############
        