#this file is intended to help with creating a set of 'concordances' which as i see it are blueprints of exactly what data for what categories we need for the model. Perhaps concordances are teh wrong name but for now we use that (can replace-all later).
#teh concordances are useful for systematically defining what data we need and what data we have. They are also useful for understanding exactly what to call different categories in teh data.
#One issue is that the process requires the model and data preparation to be run to create the concordances which use the inputs into the model. This is because they use the inputs to easily determine what measures were used. So if the user defines a new set of measures then at minimum they will need to create some dummy data and edit the code to use that dummy data. 

#%%
#set working directory as one folder back so that config works
from datetime import datetime
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
exec(open("config/config.py").read())#usae this to load libraries and set variables. Feel free to edit that file as you need


################################################################################################################################################################

#%%
#state model concordances file names for concordances we create manually
model_concordances_version = FILE_DATE_ID#'20220824_1256'
model_concordances_file_name  = 'model_concordances{}.csv'.format(model_concordances_version)
model_concordances_file_name_fuels = 'model_concordances_fuels{}.csv'.format(model_concordances_version)
model_concordances_file_name_fuels_NO_BIOFUELS = 'model_concordances_fuels_NO_BIOFUELS{}.csv'.format(model_concordances_version)

#state model concordances file names for concordances we create using inputs into the model. these model concordances state what measures are used in the model
model_concordances_measures_file_name = 'model_concordances_measures{}.csv'.format(model_concordances_version)
model_concordances_file_name_measures = 'model_concordances_measures{}.csv'.format(model_concordances_version)
model_concordances_user_input_and_growth_rates_file_name = 'model_concordances_user_input_and_growth_rates{}.csv'.format(model_concordances_version)
model_concordances_supply_side_fuel_mixing_file_name = 'model_concordances_supply_side_fuel_mixing{}.csv'.format(model_concordances_version)
model_concordances_demand_side_fuel_mixing_file_name = 'model_concordances_demand_side_fuel_mixing{}.csv'.format(model_concordances_version)

#AND A model_concordances_all_file_name
model_concordances_all_file_name = 'model_concordances_all{}.csv'.format(model_concordances_version)
################################################################################################################################################################
#%%
#create set of categories of data that will be output by the model. 
#update this with the transport categories you want to use in the transport model and they should flow through so that the inputs and outputs of the model need to be like that.
manually_defined_transport_categories = pd.read_csv('config/concordances_and_config_data/manually_defined_transport_categories.csv')

#drop duplicates
manually_defined_transport_categories.drop_duplicates(inplace=True)

#could create concordances for each year, economy and scenario and then cross that with the osemosys_concordances to get the final concordances
model_concordances = pd.DataFrame(columns=manually_defined_transport_categories.columns)
for year in range(BASE_YEAR, END_YEAR+1):
    for economy in ECONOMY_LIST:#get economys from economy_code_to_name concordance in config.py
        for scenario in SCENARIOS_LIST:
            #create concordances for each year, economy and scenario
            manually_defined_transport_categories_year = manually_defined_transport_categories.copy()
            manually_defined_transport_categories_year['Year'] = str(year)
            manually_defined_transport_categories_year['Economy'] = economy
            manually_defined_transport_categories_year['Scenario'] = scenario
            #merge with manually_defined_transport_categories_year
            model_concordances = pd.concat([model_concordances, manually_defined_transport_categories_year])

#save model_concordances with date
model_concordances.to_csv('config/concordances_and_config_data/computer_generated_concordances/{}'.format(model_concordances_file_name), index=False)

################################################################################################################################################################
#%%
#create model concordances with a fuel column. 
model_concordances_fuels = model_concordances.copy()
model_concordances_fuels_NO_BIOFUELS = model_concordances.copy()

#thsi is important to keep up to date because it will be used to create the user input spreadsheet for the demand side fuel mixing (involving removing the biofuels as they will be stated in the supply sdide fuel mixing)
#load csv of drive_type_to_fuel
drive_type_to_fuel_df = pd.read_csv('config/concordances_and_config_data/drive_type_to_fuel.csv')

#make a version of the df with no biofuels
drive_type_to_fuel_df_NO_BIOFUELS = drive_type_to_fuel_df[~drive_type_to_fuel_df['Fuel'].str.contains('bio')]

#merge the dict to our model concordances
model_concordances_fuels = pd.merge(model_concordances_fuels, drive_type_to_fuel_df, how='left', on=['Drive'])

model_concordances_fuels_NO_BIOFUELS = pd.merge(model_concordances_fuels_NO_BIOFUELS, drive_type_to_fuel_df_NO_BIOFUELS, how='left', on=['Drive'])

#save
model_concordances_fuels.to_csv('config/concordances_and_config_data/computer_generated_concordances/{}'.format(model_concordances_file_name_fuels), index=False)
model_concordances_fuels_NO_BIOFUELS.to_csv('config/concordances_and_config_data/computer_generated_concordances/{}'.format(model_concordances_file_name_fuels_NO_BIOFUELS), index=False)

########################################################################################################################################################################
#%%
#create a model concordance with a measure column so that we can state exactly what measures we need for base year data. this is from inputs into the model
model_concordances_measures = model_concordances.copy()

#to do this we will take in the input data for the model and format it to merge with the model concordances:
road_model_input = pd.read_csv('intermediate_data/model_inputs/road_model_input.csv')

#laod clean user input from intermediate file
non_road_model_input = pd.read_csv('intermediate_data/model_inputs/non_road_model_input.csv')

#create a medium col in road with the value 'road'
road_model_input['Medium'] = 'road'
#set Medium col in nonroad to Vehicle type
non_road_model_input['Medium'] = non_road_model_input['Vehicle Type']

#remove scenarios columns
road_model_input = road_model_input.drop(columns=['Scenario'])
non_road_model_input = non_road_model_input.drop(columns=['Scenario'])

#melt to create a measure and vlaue column, keeping 'Medium',	'Transport Type',	'Vehicle Type',	'Drive', 'Economy',	
road_model_input_long = road_model_input.melt(id_vars=['Medium',	'Transport Type','Year',	'Vehicle Type',	'Drive', 'Economy'], var_name='Measure', value_name='Value')
non_road_model_input_long = non_road_model_input.melt(id_vars=['Medium',	'Transport Type','Year','Vehicle Type',	'Drive', 'Economy'], var_name='Measure', value_name='Value')

#drop value column
road_model_input_long = road_model_input_long.drop(columns=['Value'])
non_road_model_input_long = non_road_model_input_long.drop(columns=['Value'])
#drop duplicates
road_model_input_long.drop_duplicates(inplace=True)
non_road_model_input_long.drop_duplicates(inplace=True)

#join the two dfs using concat
model_concordances_measures = pd.concat([road_model_input_long, non_road_model_input_long], ignore_index=True)

#now save
model_concordances_measures.to_csv('config/concordances_and_config_data/computer_generated_concordances/{}'.format(model_concordances_measures_file_name), index=False)

########################################################################################################################################################################
# %%
#create a model concordance for growth rates and user defined inputs from inputs into the model
non_road_user_input_and_growth_rates = pd.read_csv('intermediate_data/aggregated_model_inputs/non_road_user_input_and_growth_rates.csv')
road_user_input_and_growth_rates = pd.read_csv('intermediate_data/aggregated_model_inputs/road_user_input_and_growth_rates.csv')

#add a medium column
non_road_user_input_and_growth_rates['Medium'] = non_road_user_input_and_growth_rates['Vehicle Type']    
road_user_input_and_growth_rates['Medium'] = 'road'

#melt to create a measure and vlaue column, keeping 'Medium',	'Economy', 'Transport Type', 'Vehicle Type', 'Drive'
non_road_user_input_and_growth_rates_long = non_road_user_input_and_growth_rates.melt(id_vars=['Medium',	'Transport Type',	'Year', 'Scenario','Vehicle Type',	'Drive', 'Economy'], var_name='Measure', value_name='Value')
road_user_input_and_growth_rates_long = road_user_input_and_growth_rates.melt(id_vars=['Year', 'Scenario','Medium',	'Transport Type',	'Vehicle Type',	'Drive', 'Economy'], var_name='Measure', value_name='Value')

#drop value column
non_road_user_input_and_growth_rates_long = non_road_user_input_and_growth_rates_long.drop(columns=['Value'])

#drop duplicates
non_road_user_input_and_growth_rates_long = non_road_user_input_and_growth_rates_long.drop_duplicates()
road_user_input_and_growth_rates_long = road_user_input_and_growth_rates_long.drop_duplicates()

#join the two dfs using concat
model_concordances_user_input_and_growth_rates = pd.concat([road_user_input_and_growth_rates_long, non_road_user_input_and_growth_rates_long], ignore_index=True)

#now save
model_concordances_user_input_and_growth_rates.to_csv('config/concordances_and_config_data/computer_generated_concordances/{}'.format(model_concordances_user_input_and_growth_rates_file_name), index=False)


########################################################################################################################################################
#%%
#create concordances for fuel mixxing measures. These are kept separate from the others because the tables they are in are different. this is from inputs into the model

#load user input for fuel mixing 
demand_side_fuel_mixing = pd.read_csv('intermediate_data\model_inputs\demand_side_fuel_mixing_COMPGEN.csv')
supply_side_fuel_mixing = pd.read_csv('intermediate_data\model_inputs\supply_side_fuel_mixing_COMPGEN.csv')

#replace fuel_share column measure and make the value the original col name
supply_side_fuel_mixing = supply_side_fuel_mixing.rename(columns={'Supply_side_fuel_share': 'Measure'})
supply_side_fuel_mixing['Measure'] = 'Supply_side_fuel_share'
demand_side_fuel_mixing = demand_side_fuel_mixing.rename(columns={'Demand_side_fuel_share': 'Measure'})
demand_side_fuel_mixing['Measure'] = 'Demand_side_fuel_share'

#drop duplicates
demand_side_fuel_mixing = demand_side_fuel_mixing.drop_duplicates()
supply_side_fuel_mixing = supply_side_fuel_mixing.drop_duplicates()

#save
demand_side_fuel_mixing.to_csv('config/concordances_and_config_data/computer_generated_concordances/{}'.format(model_concordances_demand_side_fuel_mixing_file_name), index=False)
supply_side_fuel_mixing.to_csv('config/concordances_and_config_data/computer_generated_concordances/{}'.format(model_concordances_supply_side_fuel_mixing_file_name), index=False)

#%%

########################################################################################################################################################
#LASTLY CREATE A MODEL CONCORDANCE WHICH CONTAINS ALL THE DETAILS FROM ABOVE, TOGETHER
model_concordances_all = model_concordances_fuels.merge(model_concordances_measures, on=['Year', 'Medium', 'Transport Type', 'Vehicle Type', 'Drive', 'Economy'], how='outer')
model_concordances_all = model_concordances_all.merge(model_concordances_user_input_and_growth_rates, on=['Year', 'Scenario','Medium', 'Transport Type', 'Vehicle Type', 'Drive', 'Economy'], how='outer')
model_concordances_all = model_concordances_all.merge(demand_side_fuel_mixing, on=['Year', 'Scenario','Medium', 'Transport Type', 'Vehicle Type', 'Drive','Fuel', 'Economy'], how='outer')
model_concordances_all = model_concordances_all.merge(supply_side_fuel_mixing, on=['Year', 'Scenario','Medium', 'Transport Type', 'Vehicle Type', 'Drive','Fuel', 'Economy'], how='outer')

#save
model_concordances_all.to_csv('config/concordances_and_config_data/computer_generated_concordances/{}'.format(model_concordances_all_file_name), index=False)