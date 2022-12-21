

#%%

#set working directory as one folder back so that config works
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
from runpy import run_path
exec(open("config/config.py").read())#usae this to load libraries and set variables. Feel free to edit that file as you need


#%%
#import data from the transport data system and extract what we need from it.
# We can use the model_concordances_measures concordance file to determine what we need to extract from the transport data system. This way we dont rely on things like dataset names.


#%%
model_concordances_measures = pd.read_csv('config/concordances_and_config_data/computer_generated_concordances/{}'.format(model_concordances_base_year_measures_file_name))


#%%
#load transport data  from the transport data system which is out of this repo but is in the same folder as this repo #file name is like DATE20221214_interpolated_combined_data_concordance

#transport datasystem currently usees a diff file date id structure where it ahs no _ at  the start so we need to remove that#TODO: change the transport data system to use the same file date id structure as the model
FILE_DATE_ID2 = FILE_DATE_ID.replace('_','')
FILE_DATE_ID2 = 'DATE20221214'

transport_data_system_folder = '../transport_data_system'
transport_data_system_df = pd.read_csv('{}/output_data/{}_interpolated_combined_data_concordance.csv'.format(transport_data_system_folder,FILE_DATE_ID2))

#%%
#TEMPORARY FIX, CHANGE THE MEASURE IN TRANSPORT DATA SYSTEM FOR passenger_km and freight_tonne_km to Activity so that it matches the model concordance. It is undecided whether it would be best to change the model to use the measure of passenger_km and freight_tonne_km or to change the transport data system to use activity. Or keep this here. There are pros and cons to each approach #TODO: decide on the best approach
transport_data_system_df.loc[transport_data_system_df['Measure']=='passenger_km','Measure'] = 'Activity'
transport_data_system_df.loc[transport_data_system_df['Measure']=='freight_tonne_km','Measure'] = 'Activity'

#%%
#filter for the same years as are in the model concordances in the transport data system (should just be base year)
transport_data_system_df = transport_data_system_df[transport_data_system_df.Year.isin(model_concordances_measures.Year.unique())]

#filter for the same measures as are in the model concordances in the transport data system
transport_data_system_df = transport_data_system_df[transport_data_system_df.Measure.isin(model_concordances_measures.Measure.unique())]

#now we have filtered out the majority of rows we dont need from the transport data system, we can use pandas difference() function to find out what rows we are missing from the transport data system. This will be useful for debugging and for the user to know what data is missing from the transport data system (as its expected that no data will be missing for the model to actually run))
#%%

INDEX_COLS = ['Year', 'Economy', 'Measure', 'Vehicle Type', 'Medium',
       'Transport Type','Drive']

#set index
transport_data_system_df.set_index(INDEX_COLS, inplace=True)
model_concordances_measures.set_index(INDEX_COLS, inplace=True)

#create empty df which is a copy of the transport_data_system_df to store the data we extract from the transport data system using an iterative loop
new_transport_dataset = []

#create column which will be used to indicate whether the data is available in the transport system, or not
#options will be:
#1. data_available
#2. data_not_available
#3. row_and_data_not_available

#we can determine data available and not available now, and then find out option 3 by comparing to the model concordances:

#where vlaues arent na, set the data_available column to 1, else set to 2
transport_data_system_df.loc[transport_data_system_df.Value.notna(), 'Data_available'] = 'data_available'
transport_data_system_df.loc[transport_data_system_df.Value.isna(), 'Data_available'] = 'data_not_available'

#%%
# use the difference method to find the index values that are missing from the transport system dataset # this is a lot faster than looping through each index row in the concordance and checking if it is in the user_input
# we will not print out what values are in the dataset but missing from the concordance as this is expected to be a lot of values (but we will remove them from the dataset as they are not needed for the model to run)
missing_index_values1 = model_concordances_measures.index.difference(transport_data_system_df.index)
missing_index_values2 = transport_data_system_df.index.difference(model_concordances_measures.index)

if missing_index_values1.empty:
    print('All rows we need are present in the transport system dataset')
else:
    print('Missing rows in our user transport system dataset when we compare it to the concordance:', missing_index_values1)
    #add these rows to the user_input and set them to row_and_data_not_available
    new_transport_data_system_df = transport_data_system_df.reindex(missing_index_values1)
    new_transport_data_system_df['Data_available'] = 'row_and_data_not_available'
    new_transport_data_system_df['Value'] = np.nan

    #now append to user_input
    transport_data_system_df = transport_data_system_df.append(new_transport_data_system_df)

if missing_index_values2.empty:
    #this is unexpected so create an error
    raise ValueError('All rows in the transport system dataset are present in the concordance. This is unexpected. Please check the code.')
else:
    #we just want to make sure the user is aware that we will be removing rows from the user input
    print('Removing unnecessary rows from the user input dataset. If you intended to have new data in the dataset, please make sure you have added them to the concordance table as well.')
    #remove these rows from the user_input
    transport_data_system_df.drop(missing_index_values2, inplace=True)

#%%
#create a scenario column in the transport data system dataset which will have a scenario for each in teh scenarios list in config
i = 0
for scenario in SCENARIOS_LIST:
    if i == 0:
        #create copy df
        new_df = transport_data_system_df.copy()
        new_df['Scenario'] = scenario
        i += 1
    else:
        transport_data_system_df['Scenario'] = scenario
        new_df = new_df.append(transport_data_system_df)
    

#%%
#save the new transport dataset
transport_data_system_df.to_csv('intermediate_data/{}_transport_data_system_extract.csv'.format(FILE_DATE_ID))
#%%

# #we are misising a lot of valaues lets inspect the data to see what is missing
# x = transport_data_system_df.loc[transport_data_system_df.Data_available=='row_and_data_not_available']
# x = x.reset_index()
# x = x.groupby(['Measure', 'Vehicle Type', 'Medium', 'Transport Type', 'Drive']).count()
# x = x.reset_index()
# x


#%%














# #%%
# ##load 8th edition data
# road_stocks= pd.read_csv('intermediate_data/8th_edition_transport_model/road_stocks.csv')
# activity= pd.read_csv('intermediate_data/8th_edition_transport_model/activity.csv')
# energy= pd.read_csv('intermediate_data/8th_edition_transport_model/energy.csv')

# turnover_rate = pd.read_csv('intermediate_data/8th_edition_transport_model/turnover_rate.csv')
# new_vehicle_efficiency = pd.read_csv('intermediate_data/8th_edition_transport_model/new_vehicle_efficiency.csv')
# occupance_load = pd.read_csv('intermediate_data/8th_edition_transport_model/occupance_load.csv')
# # 
# # SAVE
# turnover_rate.to_csv('intermediate_data/cleaned_input_data/turnover_rate.csv', index=False)
# occupance_load.to_csv('intermediate_data/cleaned_input_data/occupance_load.csv', index=False)

# new_vehicle_efficiency.to_csv('intermediate_data/cleaned_input_data/new_vehicle_efficiency.csv', index=False)


# final_combined_data_concordance.to_csv('output_data/{}_interpolated_combined_data_concordance.csv'.format(FILE_DATE_ID))

# #%%