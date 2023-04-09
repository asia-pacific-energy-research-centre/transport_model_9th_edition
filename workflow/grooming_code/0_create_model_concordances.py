#this file is intended to help with creating a set of 'concordances' which as i see it are blueprints of exactly what data for what categories we need for the model. Perhaps concordances are teh wrong name but for now we use that (can replace-all later).

#teh concordances are useful for systematically defining what data we need and what data we have. They are also useful for understanding exactly what to call different categories in teh data.

#One issue is that the process requires the model and data preparation to be run to create the concordances which use the inputs into the model. This is because they use the inputs to easily determine what measures were used. So if the user defines a new set of measures then at minimum they will need to create some dummy data and edit the code to use that dummy data. 


#tghe concordances created, in order are:
#model_concordances_fuels
#model_concordances_measures
#model_concordances_user_input_and_growth_rates
#model_concordances_demand_side_fuel_mixing
#model_concordances_supply_side_fuel_mixing
#model_concordances_all


#%%
#set working directory as one folder back so that config works
from datetime import datetime
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
exec(open("config/config.py").read())#usae this to load libraries and set variables. Feel free to edit that file as you need


################################################################################################################################################################

#%%
#PLEASE NOTE THAT ALL MODEL CONCORDANCE FILE NAMES VARIABLES ARE STORED AND SET IN ./config/config.py


################################################################################################################################################################
#%%
#create set of categories of data that will be output by the model. 
#update this with the transport categories you want to use in the transport model and they should flow through so that the inputs and outputs of the model need to be like that.
manually_defined_transport_categories = pd.read_csv('config/concordances_and_config_data/manually_defined_transport_categories.csv')

#drop duplicates
manually_defined_transport_categories.drop_duplicates(inplace=True)

#could create concordances for each year, economy and scenario and then cross that with the osemosys_concordances to get the final concordances
model_concordances = pd.DataFrame(columns=manually_defined_transport_categories.columns)
for Date in range(BASE_YEAR, END_YEAR+1):
    for economy in ECONOMY_LIST:#get economys from economy_code_to_name concordance in config.py
        for scenario in SCENARIOS_LIST:
            #create concordances for each year, economy and scenario
            manually_defined_transport_categories_year = manually_defined_transport_categories.copy()
            manually_defined_transport_categories_year['Date'] = int(Date)
            manually_defined_transport_categories_year['Economy'] = economy
            manually_defined_transport_categories_year['Scenario'] = scenario
            #merge with manually_defined_transport_categories_year
            model_concordances = pd.concat([model_concordances, manually_defined_transport_categories_year])

#convert year to int
model_concordances['Date'] = model_concordances['Date'].astype(int)
#create 'Frequency col which is set to 'Yearly'
model_concordances['Frequency'] = 'Yearly'
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
#now for each measure create a copy of the model concordance for that medium and the base year only and add the measure to the copy (where non road is all non road mediums)
base_year_model_concordances_ROAD = model_concordances[(model_concordances['Medium'] == 'road') & (model_concordances['Date'] == BASE_YEAR)]
base_year_model_concordances_NON_ROAD = model_concordances[(model_concordances['Medium'] != 'road') & (model_concordances['Date'] == BASE_YEAR)]
#remove scenarios column
base_year_model_concordances_ROAD.drop(columns=['Scenario'], inplace=True)
base_year_model_concordances_ROAD.drop_duplicates(inplace=True)
base_year_model_concordances_NON_ROAD.drop(columns=['Scenario'], inplace=True)
base_year_model_concordances_NON_ROAD.drop_duplicates(inplace=True)

#create empty dataframes
base_year_non_road_measures = pd.DataFrame()
base_year_road_measures = pd.DataFrame()

for measure in base_year_measures_list_ROAD:
    base_year_model_concordances_ROAD_copy = base_year_model_concordances_ROAD.copy()
    base_year_model_concordances_ROAD_copy['Measure'] = measure
    base_year_road_measures = pd.concat([base_year_road_measures, base_year_model_concordances_ROAD_copy])  

for measure in base_year_measures_list_NON_ROAD:
    base_year_model_concordances_NON_ROAD_copy = base_year_model_concordances_NON_ROAD.copy()
    base_year_model_concordances_NON_ROAD_copy['Measure'] = measure
    base_year_non_road_measures = pd.concat([base_year_non_road_measures, base_year_model_concordances_NON_ROAD_copy])

#join the two dfs using concat
model_concordances_base_year_measures = pd.concat([base_year_road_measures, base_year_non_road_measures])
#%%
#Measure to Unit concordance (load it in and merge it to the model concordances)
measure_to_unit_concordance = pd.read_csv('config/concordances_and_config_data/measure_to_unit_concordance.csv')
#keep only Measure and Unit columns
measure_to_unit_concordance = measure_to_unit_concordance[['Measure', 'Unit']]

#merge the dict to our model concordances
model_concordances_base_year_measures = model_concordances_base_year_measures.merge(measure_to_unit_concordance, how='left', on=['Measure'])
#%%
# #TEMP
# #where measure is Occupancy_growth, remove rows where transport type is freight
# model_concordances_base_year_measures = model_concordances_base_year_measures[~((model_concordances_base_year_measures['Measure'] == 'Occupancy') & (model_concordances_base_year_measures['Transport Type'] == 'freight'))]
# #and measure is Load_growth, remove rows where transport type is passenger
# model_concordances_base_year_measures = model_concordances_base_year_measures[~((model_concordances_base_year_measures['Measure'] == 'Load') & (model_concordances_base_year_measures['Transport Type'] == 'passenger'))]

# #Remove cases so we dont have passenger_km measure where the transport type is freight and vice versa for freight_tonne_km
# model_concordances_base_year_measures = model_concordances_base_year_measures[~((model_concordances_base_year_measures['Measure'] == 'passenger_km') & (model_concordances_base_year_measures['Transport Type'] == 'freight'))]
# model_concordances_base_year_measures = model_concordances_base_year_measures[~((model_concordances_base_year_measures['Measure'] == 'freight_tonne_km') & (model_concordances_base_year_measures['Transport Type'] == 'passenger'))]
# #TEMP Over
#%%
#now save
model_concordances_base_year_measures.to_csv('config/concordances_and_config_data/computer_generated_concordances/{}'.format(model_concordances_base_year_measures_file_name), index=False)

########################################################################################################################################################################
# %%
#create a model concordance for growth rates and user defined inputs 

#now for each measure create a copy of the model concordance for that medium and add the measure to the copy (where non road is all non road mediums)
model_concordances_ROAD = model_concordances[model_concordances['Medium'] == 'road']
model_concordances_NON_ROAD = model_concordances[model_concordances['Medium'] != 'road']
#create empty dataframes
non_road_user_input_and_growth_rates = pd.DataFrame()
road_user_input_and_growth_rates = pd.DataFrame()

for measure in user_input_measures_list_ROAD:
    model_concordances_ROAD_copy = model_concordances_ROAD.copy()
    model_concordances_ROAD_copy['Measure'] = measure
    road_user_input_and_growth_rates = pd.concat([road_user_input_and_growth_rates, model_concordances_ROAD_copy])  
for measure in user_input_measures_list_NON_ROAD:
    model_concordances_NON_ROAD_copy = model_concordances_NON_ROAD.copy()
    model_concordances_NON_ROAD_copy['Measure'] = measure
    non_road_user_input_and_growth_rates = pd.concat([non_road_user_input_and_growth_rates, model_concordances_NON_ROAD_copy])

#%
#join the two dfs using concat
model_concordances_user_input_and_growth_rates = pd.concat([non_road_user_input_and_growth_rates, road_user_input_and_growth_rates], ignore_index=True)
#remove the BASE year as we don't need it. 
model_concordances_user_input_and_growth_rates = model_concordances_user_input_and_growth_rates[model_concordances_user_input_and_growth_rates['Date'] != BASE_YEAR]
#make units = %
model_concordances_user_input_and_growth_rates['Unit'] = '%'
#%%
# #where measure is Occupancy_growth, remove rows where transport type is freight
# model_concordances_user_input_and_growth_rates = model_concordances_user_input_and_growth_rates[~((model_concordances_user_input_and_growth_rates['Measure'] == 'Occupancy_growth') & (model_concordances_user_input_and_growth_rates['Transport Type'] == 'freight'))]
# #and measure is Load_growth, remove rows where transport type is passenger
# model_concordances_user_input_and_growth_rates = model_concordances_user_input_and_growth_rates[~((model_concordances_user_input_and_growth_rates['Measure'] == 'Load_growth') & (model_concordances_user_input_and_growth_rates['Transport Type'] == 'passenger'))]
#now save
#%%
model_concordances_user_input_and_growth_rates.to_csv('config/concordances_and_config_data/computer_generated_concordances/{}'.format(model_concordances_user_input_and_growth_rates_file_name), index=False)

########################################################################################################################################################
#%%
#create concordances for fuel mixxing measures. These are kept separate from the others because the tables they are in are different. this is from inputs into the model

#load user input for fuel mixing 
demand_side_fuel_mixing = pd.read_csv('intermediate_data\model_inputs\demand_side_fuel_mixing_COMPGEN.csv')
supply_side_fuel_mixing = pd.read_csv('intermediate_data\model_inputs\supply_side_fuel_mixing_COMPGEN.csv')

#TEMP
#add Frequency column of 'Yearly'
demand_side_fuel_mixing['Frequency'] = 'Yearly'
supply_side_fuel_mixing['Frequency'] = 'Yearly'
#rename Year to Date
demand_side_fuel_mixing = demand_side_fuel_mixing.rename(columns={'Year': 'Date'})
supply_side_fuel_mixing = supply_side_fuel_mixing.rename(columns={'Year': 'Date'})
#Unit = %
demand_side_fuel_mixing['Unit'] = '%'
supply_side_fuel_mixing['Unit'] = '%'
#TEMP OVER

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
#PERHAPS THIS SINT SO USEFUL BECAUSE COMBINING ALL THE MEASURES CREATES PRTOBLEMS WITH HOW THE MIXES HAVE DIFFERENT TIME PERIODS AND CATEGORIES AND SAUCH., KEEPING THEM IN THEIR OWN FILES IS PROBABLY BETTER?
#note that im 99% that we dont need to include model_concordances_fuels in here because it doesnt have any measures in it. The way we use fuels are in demand/supply side fuel mixing to determine the amount of fuel used in each transport category. Splitting the other measures by fuel will be silly so to have that in the concordance would be a waste of time.
# model_concordances_all = model_concordances_fuels.merge(model_concordances_measures, on=['Date', 'Medium', 'Transport Type', 'Vehicle Type', 'Drive', 'Economy'], how='outer')
#%%
#concat model_concordances_measures and model_concordances_user_input_and_growth_rates
model_concordances_all = pd.concat([model_concordances_base_year_measures, model_concordances_user_input_and_growth_rates], ignore_index=True)

#concat on demand and supply side fuel mixing
model_concordances_all = model_concordances_all.append(demand_side_fuel_mixing, ignore_index=True)
model_concordances_all = model_concordances_all.append(supply_side_fuel_mixing, ignore_index=True)

#save
model_concordances_all.to_csv('config/concordances_and_config_data/computer_generated_concordances/{}'.format(model_concordances_all_file_name), index=False)

#TODO do we want scenario col in model_con_all for fuel shares?
#%%
