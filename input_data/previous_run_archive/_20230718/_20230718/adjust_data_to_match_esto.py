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

#%%
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
    energy_use_esto_wide = energy_use_esto.groupby(['Economy', 'Date', 'Fuel']).sum(numeric_only=True).reset_index()
    energy_use_esto_wide = energy_use_esto_wide.pivot(index=['Economy', 'Date'], columns='Fuel', values='Energy').reset_index()
    energy_use_esto_wide['share_of_biodiesel'] = energy_use_esto_wide['16_06_biodiesel']/(energy_use_esto_wide['07_07_gas_diesel_oil']+energy_use_esto_wide['16_06_biodiesel'])
    energy_use_esto_wide['share_of_biogasoline'] = energy_use_esto_wide['16_05_biogasoline']/(energy_use_esto_wide['07_01_motor_gasoline']+energy_use_esto_wide['16_05_biogasoline'])
    
    energy_use_esto_wide['share_of_biogas'] = energy_use_esto_wide['16_01_biogas']/(energy_use_esto_wide['16_01_biogas']+energy_use_esto_wide['07_09_lpg']+energy_use_esto_wide['08_01_natural_gas'])
    
    try:#some economys dont sue aviation gasoline or kerosene, so we need to catch the error, and just set the value to 0 before doing this:
        energy_use_esto_wide['share_of_bio_jet'] = energy_use_esto_wide['16_07_bio_jet_kerosene']/(energy_use_esto_wide['07_x_jet_fuel']+energy_use_esto_wide['16_07_bio_jet_kerosene']+energy_use_esto_wide['07_02_aviation_gasoline']+energy_use_esto_wide['07_06_kerosene'])
    except:
        if '07_02_aviation_gasoline' not in energy_use_esto_wide.columns:
            energy_use_esto_wide['07_02_aviation_gasoline'] = 0
        if '07_06_kerosene' not in energy_use_esto_wide.columns:
            energy_use_esto_wide['07_06_kerosene'] = 0
        if '07_x_jet_fuel' not in energy_use_esto_wide.columns:
            energy_use_esto_wide['07_x_jet_fuel'] = 0
        energy_use_esto_wide['share_of_bio_jet'] = energy_use_esto_wide['16_07_bio_jet_kerosene']/(energy_use_esto_wide['07_x_jet_fuel']+energy_use_esto_wide['16_07_bio_jet_kerosene']+energy_use_esto_wide['07_02_aviation_gasoline']+energy_use_esto_wide['07_06_kerosene'])

    #manually create dfs then concat them:
    share_of_biodiesel = energy_use_esto_wide[['Economy', 'Date', 'share_of_biodiesel']].copy()
    #create cols for each fuel type:
    share_of_biodiesel['Fuel'] = '07_07_gas_diesel_oil'
    share_of_biodiesel['New_fuel'] = '16_06_biodiesel'
    share_of_biodiesel = share_of_biodiesel.rename(columns={'share_of_biodiesel': 'Supply_side_fuel_share'})

    share_of_biogasoline = energy_use_esto_wide[['Economy', 'Date', 'share_of_biogasoline']].copy()
    share_of_biogasoline['Fuel'] = '07_01_motor_gasoline'
    share_of_biogasoline['New_fuel'] = '16_05_biogasoline'
    share_of_biogasoline = share_of_biogasoline.rename(columns={'share_of_biogasoline': 'Supply_side_fuel_share'})
    #now do it for the ones where we have one biofuel for multiple fuels:
    share_of_biogas = energy_use_esto_wide[['Economy', 'Date', 'share_of_biogas']].copy()
    share_of_biogas['New_fuel'] = '16_01_biogas'
    share_of_biogas = share_of_biogas.rename(columns={'share_of_biogas': 'Supply_side_fuel_share'})
    share_of_biogas_in_lpg = share_of_biogas.copy()
    share_of_biogas_in_lpg['Fuel'] = '07_09_lpg'
    share_of_biogas_in_nat_gas = share_of_biogas.copy()
    share_of_biogas_in_nat_gas['Fuel'] = '08_01_natural_gas'
    
    share_of_bio_jet = energy_use_esto_wide[['Economy', 'Date', 'share_of_bio_jet']].copy()
    share_of_bio_jet['New_fuel'] = '16_07_bio_jet_kerosene'
    share_of_bio_jet = share_of_bio_jet.rename(columns={'share_of_bio_jet': 'Supply_side_fuel_share'})
    share_of_bio_jet_in_jet = share_of_bio_jet.copy()
    share_of_bio_jet_in_jet['Fuel'] = '07_x_jet_fuel'
    share_of_bio_jet_in_aviation_gasoline = share_of_bio_jet.copy()
    share_of_bio_jet_in_aviation_gasoline['Fuel'] = '07_02_aviation_gasoline'
    share_of_bio_jet_in_kerosene = share_of_bio_jet.copy()
    share_of_bio_jet_in_kerosene['Fuel'] = '07_06_kerosene'
    
    #concat them and then join to supplu_side_fuel_mixing, then swap supply_side_fuel_share for the new one, where available:
    new_share = pd.concat([share_of_biodiesel, share_of_biogasoline, share_of_biogas_in_lpg, share_of_biogas_in_nat_gas, share_of_bio_jet_in_jet, share_of_bio_jet_in_aviation_gasoline, share_of_bio_jet_in_kerosene]).reset_index(drop=True)
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
    
    #WITH THIS I DONT THINK THERE IS ANYTHING WE NEED TO DO HERE ANBYNORE. AS THE ROWS ARE NOW IN THE DATA FROM EBT (EXCEPT anything that has changed from what i expect the ebt to have)
    # #these are fuels that arent in the esto data because they arent reported on, so we just need to make sure that their sums are 0 in the mdoel input data, 
    # model_fuels_to_ignore = ['16_x_ammonia','16_x_efuel', '16_x_hydrogen', '16_07_bio_jet_kerosene','07_x_other_petroleum_products']

    # missing_fuels = [fuel for fuel in energy_use_output.Fuel.unique() if fuel not in energy_use_esto.Fuel.unique()] + [fuel for fuel in energy_use_esto.Fuel.unique() if fuel not in energy_use_output.Fuel.unique()]

    # missing_fuels = [fuel for fuel in missing_fuels if fuel not in model_fuels_to_ignore]
    
    # if len(missing_fuels)>0:
    #     print('missing fuels in energy_use_esto')
    #     print(missing_fuels)
    #     raise ValueError('missing fuels in energy_use_esto')

    # #drop nonneeded cols
    # energy_use_esto = energy_use_esto.drop(columns=['Frequency', 'Source', 'Dataset', 'Measure', 'Vehicle Type', 'Drive', 'Transport Type', 'Unit'])

    # if not TESTING:
    #     energy_use_esto['Date'] = energy_use_esto['Date'].apply(lambda x: x[:4])
    #     energy_use_esto['Date'] = energy_use_esto['Date'].astype(int)
    # #drop economy in APEC '22_SEA', '23_NEA', '23b_ONEA', '24_OAM', '24b_OOAM', '25_OCE'
    # energy_use_esto = energy_use_esto.loc[~energy_use_esto['Economy'].isin(['22_SEA', '23_NEA', '23b_ONEA', '24_OAM', '24b_OOAM', '25_OCE', 'APEC'])].copy()
    spread_non_specified_and_separate_pipeline=False#for now ignoring this
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
            energy_use_esto_nonspecified = pd.concat([energy_use_esto_nonspecified, annoying_road_fuels_df]).groupby(['Economy', 'Date', 'Fuel', 'Medium']).sum(numeric_only=True).reset_index()
            
        #spread energy_use_esto_nonspecified among all mediums for that fuel, eocnomy and date. Use the % of each energy use to the total energy use for that fuel, economy and date to do this:
        energy_use_esto['proportion_of_group'] = energy_use_esto.groupby(['Economy', 'Date', 'Fuel'])['Energy'].transform(lambda x: x/x.sum(numeric_only=True))
        #join the nonspec col on
        energy_use_esto = energy_use_esto.merge(energy_use_esto_nonspecified, on=['Economy', 'Date', 'Fuel'], how='left', suffixes=('', '_nonspec'))
        #times the proportion of group by the nonspec energy use to get the new energy use, then add that to enegry
        energy_use_esto['Energy'] = energy_use_esto['Energy'] + (energy_use_esto['proportion_of_group']*energy_use_esto['Energy_nonspec'])
        energy_use_esto = energy_use_esto.drop(columns=['Energy_nonspec', 'proportion_of_group'])
    else:
        energy_use_esto_pipeline = pd.DataFrame()
        
        
    ##############
    
    # #Create a new DataFrame for the new fuels.
    # new_fuels = pd.DataFrame()
    # #Get unique Economy-Date combinations.
    # economy_date_combinations = energy_use_esto[['Economy', 'Date']].drop_duplicates()
    # #Iterate through each unique combination of Economy and Date.
    # for _, row in economy_date_combinations.iterrows():
    #     economy, date = row['Economy'], row['Date']
        
    #     #For each fuel to ignore, create a new row with the current Economy and Date.
    #     for fuel in model_fuels_to_ignore:
    #         new_row = {'Economy': economy, 'Date': date, 'Fuel': fuel, 
    #                 'Energy': 0} 
    #         new_fuels = pd.concat([new_fuels, pd.DataFrame(new_row, index=[0])])

    #Concatenate the new fuels with the original DataFrame.
    # energy_use_esto = pd.concat([energy_use_esto, new_fuels])
    
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
        
    energy_use_output_ref = energy_use_output_ref.drop(columns=[ 'Vehicle Type', 'Drive', 'Transport Type']).groupby(['Economy', 'Date', 'Medium', 'Fuel']).sum(numeric_only=True).reset_index()
    #GRAB DATA ONLY FOR DATES WITH WHICH WE HAVE ESTO DATA
    energy_use_output_ref = energy_use_output_ref.loc[energy_use_output_ref['Date'].isin(energy_use_esto['Date'].unique())].copy()
    #LIEKWISE FOR ESTO
    energy_use_esto = energy_use_esto.loc[energy_use_esto['Date'].isin(energy_use_output_ref['Date'].unique())].copy()
    #########################
    #NOW find the ratio between energy use in the model and energy use in the esto data. So merge the dfs and then find it
    
    energy_use_merged = energy_use_esto.merge(energy_use_output_ref, on=['Economy', 'Date', 'Medium','Fuel'], how='left', suffixes=('_esto', '_model'))
    
    #reaplce nans in  Energy_model with 0. they are nan because they arent in the model (the way the model works, it has just removed these rows, so tahts why they are nans)
    #energy_use_merged['Energy_esto'] = energy_use_merged['Energy_esto'].fillna(0)
    energy_use_merged['Energy_model'] = energy_use_merged['Energy_model'].fillna(0)
    # But , for now, if theres any nans in Energy_esto then let the uyser know sicne there shouldnt really be any there.
    if energy_use_merged['Energy_esto'].isna().sum(numeric_only=True) > 0:
        nans = energy_use_merged.loc[energy_use_merged['Energy_esto'].isna(), ['Economy', 'Date', 'Medium','Fuel']].drop_duplicates()
        raise ValueError('There are nans in energy_use_esto for the following rows: {}'.format(nans))
    # 
    # if energy_use_merged['Energy'].isna().sum(numeric_only=True) > 0:
    #     nans = energy_use_merged.loc[energy_use_merged['Energy'].isna(), ['Economy', 'Date', 'Medium','Fuel']].drop_duplicates()
    #     raise ValueError('There are nans in energy_use_model for the following rows: {}'.format(nans))
        
    #calcaulte ratio so that ratio times energy in the model = eneerhy in the esto data. Then we will timesz this ratio by energy uise in the model to get the new energy use (and the effect of timesing by the ratio will be that the total difference for that ['Economy', 'Date', 'Medium','Fuel'] spread equally among all rows for that ['Economy', 'Date', 'Medium','Fuel') (except for supply side fuel mixing fuels, which we will handle separately, and demand side fuel mixing fuels, which we will drop as they are too ahrd to handle)
    #
    energy_use_merged['ratio'] = energy_use_merged['Energy_esto']/energy_use_merged['Energy_model']
    
    #where ratio becomes inf then this means that ESTO has >0 energy use and the model has 0 energy use. This is because the model didnt assume any use at that point in time. This is a semi common occuraence. So create anotehr col and call it 'addition' and put the Energy_esto value in ther to be split among its users later:
    #but first,m print what fuel, medium, economy combos have this issue:
    inf_rows = energy_use_merged.loc[energy_use_merged['ratio'] == np.inf, ['Fuel', 'Medium', 'Economy']].drop_duplicates()
    if len(inf_rows[~inf_rows.Fuel.isin(['16_05_biogasoline', '16_06_biodiesel', '16_07_bio_jet_kerosene','16_01_biogas'])]) > 0:
        print('The following fuel, medium, economy combos have inf ratio, meaning the model had 0 energy use but the esto data had >0 energy use. This is because the model didnt assume any use at that point in time. So create anotehr col and call it addition and put the Energy_esto value in ther to be split among its users later:')
        print('There are fuels other than 16_05_biogasoline and 16_06_biodiesel that have inf ratio. This is unexpected {inf_rows}. they will be set in the addition column')
        
    
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
    
    
    
    #TODO WHY ARE WE DOING THIS. WHY NOT MERGE TO energy_use_output?
    # #we want to merge with energy_use_merged to get the ratio, however the detailed input data which we need for its efficiency data and others doesnt contain a fuel col. BUT we can map to the same index cols in energy_use_output then merge.
    # index_cols = ['Date', 'Economy', 'Vehicle Type', 'Medium', 'Transport Type', 'Drive']
    # index_cols_df = energy_use_output.loc[energy_use_output['Scenario'] == 'Reference'].copy()
    # #drop Scenario
    # index_cols_df = index_cols_df.drop(columns=['Scenario'])
    # #and drop any drive in demand side fuel mixing as its to complicated to decrease tehir energy use like we will do. (we also did this in energy_use_output_ref, but we need to do it here again too)
    # demand_side_fuel_mixing_drives = pd.read_csv('intermediate_data\model_inputs\demand_side_fuel_mixing_COMPGEN.csv')['Drive'].unique().tolist()
    # index_cols_df = index_cols_df.loc[~index_cols_df['Drive'].isin(demand_side_fuel_mixing_drives)].copy()

    # #drop nonnecessary cols from energy_use_merged
    # if not TESTING:
    #     energy_use_merged = energy_use_merged.drop(columns=['Energy_esto', 'Energy'])
    
    # #now do the merge
    # index_cols_merge = energy_use_merged.merge(index_cols_df.drop(columns=['Energy']), on=['Economy', 'Date','Medium', 'Fuel'], how='left')

    # #make sure there are no duplcaites when you drop the fuel column. thi would cause unexpected results (it occurs where there are multiple fuels for the same index cols - which can be expected because things lik rail use coal, elec and diesel)
    # index_cols_merge = index_cols_merge[index_cols_merge.Date>=BASE_YEAR]
    # dupes = index_cols_merge[index_cols_merge.duplicated(subset=index_cols)]
    # if len(dupes) > 0:
    #     
    #     raise ValueError('duplicates in index_cols_merge')

    # input_data_new = input_data_new.merge(index_cols_merge, on=index_cols, how='left')

    #drop Fuel
    # input_data_new = input_data_new.drop(columns=['Fuel'])
    ##################
    
    #merge energy_use_merged to energy_use_output using a right merge and times the ratio by the energy use in the model to get the new energy use (and the effect of timesing by the ratio will be that the total difference for that ['Economy', 'Date', 'Medium','Fuel'] spread equally among all rows for that ['Economy', 'Date', 'Medium','Fuel') (except for supply side fuel mixing fuels, which we will handle separately, and demand side fuel mixing fuels, which we will drop as they are too ahrd to handle)
    energy_use_merged_merged = energy_use_merged.merge(energy_use_output, on=['Economy', 'Date', 'Medium','Fuel'], how='right')
    #To make it a bit more simple, lets called Energy, Energy old. Then when we calcualte Energy*ratio it can be called Energy new. then rename it to energy and drop energy old before we move on:
    energy_use_merged_merged.rename(columns={'Energy': 'Energy_old'}, inplace=True)   
    
    #first, drop any supply side fuel mixing fuels as thier energy use is handled separately
    supply_side_fuel_mixing_fuels = pd.read_csv('intermediate_data\model_inputs\supply_side_fuel_mixing_COMPGEN.csv')['New_fuel'].unique().tolist()
    energy_use_merged_merged = energy_use_merged_merged.loc[~energy_use_merged_merged['Fuel'].isin(supply_side_fuel_mixing_fuels)].copy()
    #then for any phevs sum their electricity row for each economy and date, then minus that off the bev electricity. NOTE that this only works because phevs are currently a small share of use and decreaing their enegry use in elec would probably have a minimal effect. if they were bigger we'd have to find some way to handle this properly
    phev=False#i dont think i need to do this actually. the stocks for phevs will end up half what they should be if we do it, and i think it is fine to keep them in here, as well just sum their energy use like so it is not by fuel later?
    if phev:
        demand_side_fuel_mixing_drives = pd.read_csv('intermediate_data\model_inputs\demand_side_fuel_mixing_COMPGEN.csv')['Drive'].unique().tolist()
        if set(demand_side_fuel_mixing_drives) != set(['phev_d', 'phev_g']):
            raise ValueError('demand_side_fuel_mixing_drives has changed')
        phev_elec = energy_use_merged_merged.loc[energy_use_merged_merged['Drive'].isin(['phev_d', 'phev_g'])].groupby(['Economy', 'Date', 'Scenario']).sum(numeric_only=True).reset_index()
        phev_elec['decrease'] = phev_elec['Energy_old'] - (phev_elec['Energy_old'] * phev_elec['ratio'])#we will decrease bev energy use by this much after applying the ratio to it. this will effectively change bevs to make up the missing electricity use from phevs
        phev_elec['Drive'] = 'bev'
        phev_elec['Transport Type'] = 'passenger'
        #drop electiricty rows for phev
        energy_use_merged_merged = energy_use_merged_merged.loc[~(energy_use_merged_merged['Drive'].isin(['phev_d', 'phev_g'])&energy_use_merged_merged['Fuel'].isin(['17_electricity']))].copy()
        
    #lastly idenifty any nas. they are probably okay bnut useful to observe for nwo: #the nas that ive seen here are to be expected, such as for bevs and phevs. Its better just to notice potential issues elswehre.
    do_this = False
    if do_this:
        nas = energy_use_merged_merged.loc[energy_use_merged_merged.isna().any(axis=1)]
        if len(nas) > 0:
            breakpoint()
            print(nas)
    
    #not sure about this one but where ratio is na it is because we either removed it or it wasnt in the estpo data, i think? anyway, set it to 1 and later we can work out whetehr to keep it or not
    # do_this = True
    # if do_this:
    #     input_data_new['ratio'] = input_data_new['ratio'].fillna(1)
        
    #do the ratio times enegry calc":
    energy_use_merged_merged['Energy_new'] = energy_use_merged_merged['Energy_old']*energy_use_merged_merged['ratio']

    #additions need to be split equally where they are made. do this using the proprtion of each energy use out of the total energy use for that fuel, medium, economy and date to do this:
    
    #replace energy with 0 where its na for the calcualtion
    energy_use_merged_merged['Energy_new'] = energy_use_merged_merged['Energy_new'].fillna(0)
    energy_use_merged_merged['proportion_of_group'] = energy_use_merged_merged.groupby(['Economy', 'Date', 'Medium'])['Energy_new'].transform(lambda x: x/x.sum(numeric_only=True))

    energy_use_merged_merged['addition'] = energy_use_merged_merged['addition']*energy_use_merged_merged['proportion_of_group'].replace(np.nan, 0)
    #now need to add any additions to the Energy. this is where the ratio was inf because the model had 0 energy use but the esto data had >0. so we will add the esto data energy use to the model data energy use and just times by a ratio of 1
    energy_use_merged_merged['Energy_new'] = energy_use_merged_merged['Energy_new'] + energy_use_merged_merged['addition'].replace(np.nan, 0)
    if phev:
        #now change teh bev energy use by the phev electriicty amount we calculated earlier
        energy_use_merged_merged = energy_use_merged_merged.merge(phev_elec[['Economy', 'Date', 'Scenario', 'Drive', 'Transport Type', 'decrease']], on=['Economy', 'Date', 'Scenario', 'Drive', 'Transport Type'], how='left')
        #where decrease is nan, set it to 0, then decrease it
        energy_use_merged_merged['decrease'] = energy_use_merged_merged['decrease'].fillna(0)
        #if the result will be less than 0 however, then just set it to 0
        energy_use_merged_merged['Energy_new'] = np.where(energy_use_merged_merged['Energy_new'] - energy_use_merged_merged['decrease'] < 0, 0, energy_use_merged_merged['Energy_new'] - energy_use_merged_merged['decrease'])
        
        #drop decrease
        energy_use_merged_merged = energy_use_merged_merged.drop(columns=['decrease'])
        
    
    #drop unneeded cols
    energy_use_merged_merged = energy_use_merged_merged.drop(columns=['ratio','addition','proportion_of_group', 'Energy_esto', 'Energy_model', 'Energy_old', 'Fuel'])
    #and sum now that we've calclate the new enegry use for each 'Economy', 'Date', 'Medium', 'Vehicle Type', 'Transport Type', 'Drive', 'Scenario'
    energy_use_merged_merged = energy_use_merged_merged.groupby(['Economy', 'Date', 'Medium', 'Vehicle Type', 'Transport Type', 'Drive', 'Scenario']).sum(numeric_only=True).reset_index()
    breakpoint()
    # #replicate the dfs for the other scenarios
    # energy_use_merged_merged_copy = energy_use_merged_merged.copy()
    # for scenario in scenario_list:
    #     energy_use_merged_merged_copy['Scenario'] = scenario
    #     energy_use_merged_merged = pd.concat([energy_use_merged_merged, energy_use_merged_merged_copy])
    #####################################
    #Now join on the efficiency, Occupancy_or_load, Mileage, inteisntiy from the detailed data so we can calcualte the new inputs for the model:
    energy_use_merged_merged = energy_use_merged_merged.merge(input_data_new[['Economy', 'Date', 'Medium', 'Vehicle Type', 'Transport Type', 'Drive', 'Scenario', 'Efficiency', 'Occupancy_or_load', 'Mileage', 'Intensity']], on=['Economy', 'Date', 'Medium', 'Vehicle Type', 'Transport Type', 'Drive', 'Scenario'], how='left')
    #split into medium = road and not, then recalcualte the other measures. for road we will calcuialte travel km and activity and stocks, wehreas for non road we will just recalcualte energy use using itnsntiy instead of effcieincy
    #road:
    input_data_new_road = energy_use_merged_merged.loc[energy_use_merged_merged['Medium'] == 'road'].copy()

    input_data_new_road['Travel_km'] = input_data_new_road['Energy_new'] * input_data_new_road['Efficiency']

    input_data_new_road['Activity'] = input_data_new_road['Travel_km'] * input_data_new_road['Occupancy_or_load']

    input_data_new_road['Stocks'] = input_data_new_road['Activity'] / (input_data_new_road['Mileage'] * input_data_new_road['Occupancy_or_load'])

    #rename Energy_new to Energy
    input_data_new_road.rename(columns={'Energy_new': 'Energy'}, inplace=True)
    
    #########
    # non road:
    input_data_new_non_road = energy_use_merged_merged.loc[energy_use_merged_merged['Medium'] != 'road'].copy()
    input_data_new_non_road['Activity'] = input_data_new_non_road['Energy_new'] / input_data_new_non_road['Intensity']
    
    input_data_new_non_road.loc[(input_data_new_non_road['Energy_new'] > 0), 'Stocks'] = 1
    input_data_new_non_road.loc[(input_data_new_non_road['Energy_new'] == 0), 'Stocks'] = 0

    #rename Energy_new to Energy
    input_data_new_non_road.rename(columns={'Energy_new': 'Energy'}, inplace=True)
    #drop cols unneeded for non road, by filtering tfor the same cols that are in non_road_model_input_wide
    input_data_new_non_road = input_data_new_non_road.loc[:, input_data_new_non_road.columns.isin(non_road_model_input_wide.columns)].copy()
    #is this right

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
    
    #now, waht we have is meant to be the input used by run road model and non road. we nmeed ot merge it to the other inputs needed for it to be used by run_road_model.py and run_non_road_model.py. 
    # missing_cols_road = [col for col in road_model_input_wide.columns if col not in input_data_new_road.columns]#['Non_road_intensity_improvement', 'Population', 'Gdp', 'Gdp_per_capita', 'Activity_growth']
    # missing_cols_non_road = [col for col in non_road_model_input_wide.columns if col not in input_data_new_non_road.columns]#['Non_road_intensity_improvement', 'Population', 'Gdp', 'Gdp_per_capita', 'Activity_growth']
    #what if non road missing cols are empty can we jsut carry on? or probably  throw an error if NOT empty
    #merge and add tehse missing cols back on usaing the original input data:
    road_all_wide = input_data_new_road.copy()
    road_all_wide = road_all_wide.merge(road_model_input_wide, on=['Date', 'Economy', 'Medium', 'Transport Type','Vehicle Type',  'Drive', 'Scenario'], how='left', suffixes=('', '_new'))
    #check what new cols there are by seeing what cols are different between input_data_new_road and road_all_wide
    new_cols = [col for col in road_all_wide.columns if col not in input_data_new_road.columns]
    #drop cols that end with _new
    road_all_wide = road_all_wide.loc[:,~road_all_wide.columns.str.endswith('_new')].copy()
    
    #NOW FOR NON ROAD
    non_road_all_wide = input_data_new_non_road.copy()
    non_road_all_wide = non_road_all_wide.merge(non_road_model_input_wide, on=['Date', 'Economy', 'Medium','Vehicle Type', 'Transport Type', 'Drive', 'Scenario'], how='left', suffixes=('', '_new'))
    #check what new cols there are by seeing what cols are different between input_data_new_road and non_road_model_input_wide
    new_cols = [col for col in input_data_new_non_road.columns if col not in non_road_all_wide.columns]
    #drop cols that end with _new
    non_road_all_wide = non_road_all_wide.loc[:,~non_road_all_wide.columns.str.endswith('_new')].copy()
    # #so we'll melt both the new input data and the orignal input data for road and non road, so that the measures are in one col and the values are in another. then we can merge them on the measures col and  replace values where they are new, then pivot bacc to wide format
    # #
    # input_data_new_non_road = input_data_new_non_road.melt(id_vars=['Date', 'Economy', 'Medium','Vehicle Type', 'Transport Type', 'Drive'], var_name='Measure', value_name='Value')
    # non_road_model_input = non_road_model_input_wide.melt(id_vars=['Date', 'Economy', 'Medium','Vehicle Type', 'Transport Type', 'Drive', 'Scenario'], var_name='Measure', value_name='Value')
    # #join to original input data
    # non_road_all = non_road_model_input.merge(input_data_new_non_road, on=['Date', 'Economy', 'Medium','Vehicle Type', 'Transport Type', 'Drive', 'Measure'], how='left', suffixes=('', '_new'))

    # #for the measures we havent already calcualted suing new energy, we should fillna with the old values.
    # measures_to_not_fillna = ['Activity', 'Energy']
    # non_road_all_measures_to_fillna = non_road_all.loc[~non_road_all['Measure'].isin(measures_to_not_fillna)].copy()
    # non_road_all_measures_to_fillna['Value'] = non_road_all_measures_to_fillna['Value_new'].fillna(non_road_all_measures_to_fillna['Value'])
    # non_road_other = non_road_all.loc[non_road_all['Measure'].isin(measures_to_not_fillna)].copy()
    # non_road_other['Value'] = non_road_other['Value_new']
    # non_road_all = pd.concat([non_road_all_measures_to_fillna, non_road_other]).copy()
    
    # #drop Value_new
    # non_road_all = non_road_all.drop(columns=['Value_new'])
    # #pivot back to wide format
    # non_road_all_wide = non_road_all.pivot_table(index=['Date', 'Economy', 'Medium', 'Transport Type', 'Drive','Vehicle Type',  'Scenario'], columns='Measure', values='Value').reset_index()
    # # 
    # ########
    # #do same for road
    # input_data_new_road_long = input_data_new_road.melt(id_vars=['Date', 'Economy', 'Medium', 'Transport Type','Vehicle Type',  'Drive'], var_name='Measure', value_name='Value')
    # road_model_input = road_model_input_wide.melt(id_vars=['Date', 'Economy', 'Medium', 'Transport Type','Vehicle Type',  'Scenario', 'Drive'],  var_name='Measure', value_name='Value')
    # #join to original input data
    # road_all = road_model_input.merge(input_data_new_road_long, on=['Date', 'Economy', 'Medium', 'Transport Type','Vehicle Type', 'Drive', 'Measure'], how='left', suffixes=('', '_new'))

    # #for the measures we havent already calcualted suing new energy, we should fillna with the old values. otherwise only use the new values.
    # measures_to_not_fillna = ['Activity', 'Stocks', 'Travel_km', 'Energy']
    # road_all_measures_to_fillna = road_all.loc[~road_all['Measure'].isin(measures_to_not_fillna)].copy()
    # road_all_measures_to_fillna['Value'] = road_all_measures_to_fillna['Value_new'].fillna(road_all_measures_to_fillna['Value'])
    # road_other = road_all.loc[road_all['Measure'].isin(measures_to_not_fillna)].copy()
    # road_other['Value'] = road_other['Value_new']
    # road_all = pd.concat([road_all_measures_to_fillna, road_other]).copy()
    
    #drop Value_new
    # road_all = road_all.drop(columns=['Value_new'])
    #pivot back to wide format
    # road_all_wide = road_all.pivot_table(index=['Date', 'Economy', 'Medium', 'Transport Type','Vehicle Type',  'Scenario', 'Drive'], columns='Measure', values='Value').reset_index()

    ##########TESTINGOVER###############
    # #remove Activity_growth freom both road and non road as its been a bit corrupted by the above process
    # road_all_wide = road_all_wide.drop(columns=['Activity_growth'])
    # non_road_all_wide = non_road_all_wide.drop(columns=['Activity_growth'])
    #then add it back fromroad_model_input_wide amnd non_road_model_input_wide:
    # road_all_wide = road_all_wide.merge(road_model_input_wide[['Date', 'Economy', 'Medium', 'Transport Type','Vehicle Type',  'Scenario', 'Drive', 'Activity_growth']], on=['Date', 'Economy', 'Medium', 'Transport Type','Vehicle Type',  'Scenario', 'Drive'], how='left')
    # non_road_all_wide = non_road_all_wide.merge(non_road_model_input_wide[['Date', 'Economy', 'Medium', 'Transport Type','Vehicle Type',  'Scenario', 'Drive', 'Activity_growth']], on=['Date', 'Economy', 'Medium', 'Transport Type','Vehicle Type',  'Scenario', 'Drive'], how='left')
    
        
    return road_all_wide, non_road_all_wide


def adjust_data_to_match_esto(road_model_input_wide,non_road_model_input_wide,advance_base_year=True, TESTING=False, TEST_ECONOMY='19_THA'):
    energy_use_esto = format_9th_input_energy_from_esto()
    
    input_data_based_on_previous_model_run = pd.read_csv('output_data/model_output_detailed/NON_ROAD_DETAILED_{}'.format(model_output_file_name))
    supply_side_fuel_mixing = pd.read_csv('intermediate_data\model_inputs\supply_side_fuel_mixing_COMPGEN.csv')
    energy_use_output = pd.read_csv('output_data/model_output_with_fuels/NON_ROAD_DETAILED_{}'.format(model_output_file_name))
    
    if TESTING:
        
        #filter for only 01_AUS and year <= 2025 to make it run faster
        road_model_input_wide = road_model_input_wide[(road_model_input_wide['Economy'] == TEST_ECONOMY ) & (road_model_input_wide['Date'] <= 2025)]
        non_road_model_input_wide = non_road_model_input_wide[(non_road_model_input_wide['Economy'] == TEST_ECONOMY) & (non_road_model_input_wide['Date'] <= 2025)]
        
        #filter for only 01_AUS to make it run faster  and year <= 2025 
        supply_side_fuel_mixing = supply_side_fuel_mixing[supply_side_fuel_mixing['Economy'] == TEST_ECONOMY].copy()
        input_data_based_on_previous_model_run = input_data_based_on_previous_model_run[input_data_based_on_previous_model_run['Economy'] == TEST_ECONOMY].copy()
        #filter for only 01_AUS to make it run faster  and year <= 2025 
        energy_use_output = energy_use_output[energy_use_output['Economy'] == TEST_ECONOMY].copy()
        energy_use_esto = energy_use_esto[energy_use_esto['Economy'] == TEST_ECONOMY].copy()
        #  and year <= 2025 
        supply_side_fuel_mixing = supply_side_fuel_mixing[supply_side_fuel_mixing['Date'] <= 2025].copy()
        input_data_based_on_previous_model_run = input_data_based_on_previous_model_run[input_data_based_on_previous_model_run['Date'] <= 2025].copy()
        
        energy_use_esto = energy_use_esto[energy_use_esto['Date'] <= 2025].copy()
        energy_use_output = energy_use_output[energy_use_output['Date'] <= 2025].copy()
        
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
    #calcauklte total energy use by year and economy for both road and non road.
    #first rmeove the supply_side_fuel_mixing_fuels from esto data!
    supply_side_fuel_mixing_fuels = pd.read_csv('intermediate_data\model_inputs\supply_side_fuel_mixing_COMPGEN.csv')['New_fuel'].unique().tolist()
    energy_use_merged = energy_use_merged.loc[~energy_use_merged['Fuel'].isin(supply_side_fuel_mixing_fuels)].copy()
    ################
    road_all_wide_total_energy_use = road_all_wide.groupby(['Economy','Scenario', 'Date'])['Energy'].sum(numeric_only=True).reset_index()
    non_road_all_wide_total_energy_use = non_road_all_wide.groupby(['Economy','Scenario', 'Date'])['Energy'].sum(numeric_only=True).reset_index()
    esto_total_energy_use_non_road = energy_use_merged.loc[(energy_use_merged['Medium'] != 'road')].groupby(['Economy', 'Date'])['Energy_esto'].sum(numeric_only=True).reset_index()
    esto_total_energy_use_road = energy_use_merged.loc[(energy_use_merged['Medium'] == 'road')].groupby(['Economy', 'Date'])['Energy_esto'].sum(numeric_only=True).reset_index()
    #print the differentce between total energy in the years 2017 to 2022
    print('road energy use difference (PJ)')
    diff = road_all_wide_total_energy_use.merge(esto_total_energy_use_road, on=['Economy', 'Date'], how='left', suffixes=('', '_esto'))
    if advance_base_year:
        diff = diff.loc[(diff.Date>BASE_YEAR) & (diff.Date<=OUTLOOK_BASE_YEAR)]
    else:
        diff = diff.loc[(diff.Date>=BASE_YEAR) & (diff.Date<=OUTLOOK_BASE_YEAR)]
    print(diff['Energy'].sum(numeric_only=True) - diff['Energy_esto'].sum(numeric_only=True))
    
    diff2 = non_road_all_wide_total_energy_use.merge(esto_total_energy_use_non_road, on=['Economy', 'Date'], how='left', suffixes=('', '_esto'))
    if advance_base_year:
        diff2 = diff2.loc[(diff2.Date>BASE_YEAR) & (diff2.Date<=OUTLOOK_BASE_YEAR)]
    else:
        diff2 = diff2.loc[(diff2.Date>=BASE_YEAR) & (diff2.Date<=OUTLOOK_BASE_YEAR)]
    print('non road energy use difference (PJ)')
    print(diff2['Energy'].sum(numeric_only=True) - diff2['Energy_esto'].sum(numeric_only=True))
    ###################TESTING###############
    #Another test using the proportion difference between teh two:
    total_road_energy_use = road_all_wide.groupby(['Economy','Scenario', 'Date']).sum(numeric_only=True).reset_index()
    total_esto_road_energy_use = energy_use_merged.loc[(energy_use_merged['Medium'] == 'road')].groupby(['Economy', 'Date']).sum(numeric_only=True).reset_index()
    
    total_non_road_energy_use = non_road_all_wide.groupby(['Economy','Scenario', 'Date']).sum(numeric_only=True).reset_index()
    total_esto_non_road_energy_use = energy_use_merged.loc[(energy_use_merged['Medium'] != 'road')].groupby(['Economy', 'Date']).sum(numeric_only=True).reset_index()

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

#%%
def format_9th_input_energy_from_esto():
    #take in data from the EBT system of 9th and format it so that it can be used to create the energy data to whcih the model will be rescaled:
    #load the 9th data
    date_id = utility_functions.get_latest_date_for_data_file('input_data/9th_model_inputs', 'model_df_wide_')
    energy_use_esto = pd.read_csv(f'input_data/9th_model_inputs/model_df_wide_{date_id}.csv')
    #TEMP replace 15_PHL with 15_RP and 17_SGP with 17_SIN in the eocnomy col. make sure to let user know they can klet hyguga know:
    if len(energy_use_esto.loc[energy_use_esto['economy'].isin(['15_PHL', '17_SGP'])]) > 0:
        print('########################\n\n there are some economies in the esto data that are not in the model data. we will replace 15_PHL with 15_RP and 17_SGP with 17_SIN. AKA TELL HYUGA wats up \n\n########################')
    energy_use_esto['economy'] = energy_use_esto['economy'].replace({'15_PHL': '15_RP', '17_SGP': '17_SIN'})
    
    #reverse the mappings:
    medium_mapping_reverse = {v: k for k, v in medium_mapping.items()}

    #now format it so we only have the daata we need:
    # cols:'scenarios', 'economy', 'sectors', 'sub1sectors', 'sub2sectors',
    #    'sub3sectors', 'sub4sectors', 'fuels', 'subfuels', '1980'...
    #first filter so teh sector is transport:
    energy_use_esto = energy_use_esto.loc[energy_use_esto['sectors'] == '15_transport_sector'].copy()
    #and fiulter for ref scenario:
    energy_use_esto = energy_use_esto.loc[energy_use_esto['scenarios'] == 'reference'].copy()
    #and drop aggregate fuels:
    aggregate_cols = ['19_total', '20_total_renewables', '21_modern_renewables']
    energy_use_esto = energy_use_esto.loc[~energy_use_esto['fuels'].isin(aggregate_cols)].copy()
    #then do the mappings:
    #map the subfuel to the fuel
    #now map the subfuels to the subfuels in the esto data
    energy_use_esto['Fuel'] = energy_use_esto['subfuels'].map(temp_esto_subfuels_to_new_subfuels_mapping)
    #where subfuel is x then set Fuel to the value in fuels column:
    energy_use_esto.loc[energy_use_esto['subfuels'] == 'x', 'Fuel'] = energy_use_esto['fuels'].map(x_subfuel_mappings)
    if len(energy_use_esto.loc[energy_use_esto['Fuel'].isna()]) > 0:
        
        # drop anyrows where the fuels column is 06_crude_oil_and_ngl, as we are going to remove that column on the input data side anyway (i.e. tell hyuga to drop it)
        nas = energy_use_esto.loc[energy_use_esto['Fuel'].isna()].loc[~energy_use_esto['fuels'].isin(['06_crude_oil_and_ngl'])]
        if len(nas) > 0:
            raise ValueError('there are nans in Fuel because there was an x in subfuel and the fuel was not in the x_subfuel_mapping, {}'.format(energy_use_esto.loc[energy_use_esto['Fuel'].isna(), 'fuels'].unique()))
        else:
            #write big warnign just to rmeind you to remind hyuga to drop 06_crude_oil_and_ngl!
            print('##########################\n\n there are nans in Fuel because there was an x in subfuel and the fuel was not in the x_subfuel_mapping, but they are all 06_crude_oil_and_ngl, so we will drop that column on the input data side. AKA TELL HYUGA TO DROP 06_crude_oil_and_ngl\n\n##########################')

    #map the medium to the sub1sector then drop the fuel and sectors cols since weve dfone all the mapping we can:
    energy_use_esto['Medium'] = energy_use_esto['sub1sectors'].map(medium_mapping_reverse)
    energy_use_esto = energy_use_esto.drop(columns=['sub1sectors', 'sub2sectors', 'sub3sectors', 'sub4sectors', 'sectors', 'fuels','subfuels', 'scenarios'])

    #then sum up the energy use by scenarios, economy, medium and subfuel:
    energy_use_esto = energy_use_esto.groupby(['economy', 'Medium', 'Fuel']).sum(numeric_only=True).reset_index()
    #melt so that the years are in one col and the energy use is in another:
    energy_use_esto = energy_use_esto.melt(id_vars=['economy', 'Medium', 'Fuel'], var_name='Date', value_name='Energy_esto')

    #rename economy to Economy, 
    energy_use_esto.rename(columns={'economy': 'Economy'}, inplace=True)

    # #drop any 0's or nas:
    energy_use_esto = energy_use_esto.loc[energy_use_esto['Energy_esto'] > 0].copy()

    #drop data that is less than the BASE_YEAR and more than OUTLOOK_BASE_YEAR
    energy_use_esto['Date'] = energy_use_esto['Date'].apply(lambda x: x[:4])
    energy_use_esto['Date'] = energy_use_esto['Date'].astype(int)
    energy_use_esto = energy_use_esto.loc[energy_use_esto['Date'] >= BASE_YEAR].copy()
    energy_use_esto = energy_use_esto.loc[energy_use_esto['Date'] <= OUTLOOK_BASE_YEAR].copy()

    #drop '22_SEA', '23_NEA', '23b_ONEA', '24_OAM','24b_OOAM', '25_OCE', 'APEC' Economys
    energy_use_esto = energy_use_esto.loc[~energy_use_esto['Economy'].isin(['22_SEA', '23_NEA', '23b_ONEA', '24_OAM','24b_OOAM', '25_OCE', 'APEC'])].copy()

    #lastly, using the concordances, we will identify any fuel/medium combinations that arent in either and notify the user. for ones that are dealt with in the dicitonary below, do that, for the others, throw an error:
    missing_fuels_and_mediums_to_new_fuels_and_mediums = {
        'road':{
            '07_x_other_petroleum_products': ('07_x_other_petroleum_products', 'nonspecified'),
            '16_09_other_sources':
            ('16_09_other_sources', 'nonspecified'),
            '07_02_aviation_gasoline': ('07_02_aviation_gasoline', 'nonspecified'),
            '07_06_kerosene': ('07_06_kerosene', 'nonspecified'),
            '07_08_fuel_oil': ('07_08_fuel_oil', 'nonspecified'), 
        },
        'rail':{
            '07_x_other_petroleum_products': ('07_x_other_petroleum_products', 'nonspecified'),
            '16_09_other_sources':
            ('16_09_other_sources', 'nonspecified'),
        },
        'air':{
            '07_x_other_petroleum_products': ('07_x_other_petroleum_products', 'nonspecified')
        },
        'ship':{
            '16_09_other_sources':
            ('16_09_other_sources', 'nonspecified')
    }}
        
    #dso mapping now ewith the new fuels and mediums:
    for medium, fuels in missing_fuels_and_mediums_to_new_fuels_and_mediums.items():
        for fuel, new_fuel_and_medium in fuels.items():
            energy_use_esto.loc[(energy_use_esto['Medium'] == medium) & (energy_use_esto['Fuel'] == fuel), 'Fuel'] = new_fuel_and_medium[0]
            energy_use_esto.loc[(energy_use_esto['Medium'] == medium) & (energy_use_esto['Fuel'] == fuel), 'Medium'] = new_fuel_and_medium[1]
    
    concordances_fuels = pd.read_csv('config/concordances_and_config_data/computer_generated_concordances/{}'.format(model_concordances_file_name_fuels))
    concordances_fuels = concordances_fuels[['Fuel', 'Medium']].drop_duplicates()
    energy_use_esto_fuel_medium = energy_use_esto[['Fuel', 'Medium']].drop_duplicates()
    #drop nonspecified and pipeline from energy_use_esto_fuel_medium
    energy_use_esto_fuel_medium = energy_use_esto_fuel_medium.loc[~energy_use_esto_fuel_medium['Medium'].isin(['nonspecified', 'pipeline'])].copy()

    #do an outer join and then identify any nans:
    outer_join = concordances_fuels.merge(energy_use_esto_fuel_medium, on=['Fuel', 'Medium'], how='outer', indicator=True)

    #TODO MAKE THIS ACTIVIE ONCE WE HAVE THE CONCORDANCES FOR THE NEW FUELS AND MEDIUMS
    # #where merge is 'left_only' then throw an error. this is wherte a fuel is used in tthe model but isnt in esto. for now we will add these as 0 rows to the data but let the user now with a very visible message!
    left_only = outer_join.loc[outer_join['_merge'] == 'left_only']
    # ignored_fuels_and_mediums = ['07_x_other_petroleum_products', '16_09_other_sources', '07_02_aviation_gasoline', '07_06_kerosene', '07_08_fuel_oil']
    if len(left_only) > 0:
        # energy_use_esto_new = energy_use_esto.copy()
        #for each row in left_only, add a row to energy_use_esto_new with the fuel and medium and energy set to 0, for every economy and date:
        for index, row in left_only.iterrows():
            for economy in energy_use_esto['Economy'].unique():
                for date in energy_use_esto['Date'].unique():
                    energy_use_esto_new_df_row = pd.DataFrame({'Economy': [economy], 'Date': [date], 'Medium': [row['Medium']], 'Fuel': [row['Fuel']], 'Energy_esto': [0]})
                    #concat to energy_use_esto
                    energy_use_esto = pd.concat([energy_use_esto, energy_use_esto_new_df_row])
            print('###############################\n')
            print('there is a fuel/medium combination in the model that is not in the esto data. These should at least have values = to 0. it is {} and {}'.format(row['Fuel'], row['Medium']))
            
        
    #     raise ValueError('there are some fuel/medium combinations in energy_use_esto that are not in the concordances_fuels {}'.format(left_only))
    #where merge is right only, this is where a fuel is used in esto but not asccoiunted for in the model. The suer will have to deal with it manually:
    # right_only = outer_join.loc[outer_join['_merge'] == 'right_only']
    # if len(right_only) > 0:
    #     breakpoint()
    #     raise ValueError('there are some fuel/medium combinations in concordances_fuels that are not in the energy_use_esto {}'.format(right_only))

    #and now drop pipeline and nonspecified from energy_use_esto:
    energy_use_esto = energy_use_esto.loc[~energy_use_esto['Medium'].isin(['nonspecified', 'pipeline'])].copy()
    energy_use_esto = energy_use_esto.groupby(['Economy', 'Medium','Date', 'Fuel']).sum(numeric_only=True).reset_index()
    #reame Energy_esto to Energy:
    energy_use_esto.rename(columns={'Energy_esto': 'Energy'}, inplace=True)
    return energy_use_esto


#%%