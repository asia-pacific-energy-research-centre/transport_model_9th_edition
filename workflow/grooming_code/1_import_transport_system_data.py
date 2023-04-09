

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
# FILE_DATE_ID2 = FILE_DATE_ID.replace('_','')
FILE_DATE_ID2 =1# 'DATE20230216'

transport_data_system_folder = '../transport_data_system'
transport_data_system_df = pd.read_csv('{}/output_data/combined_data_{}.csv'.format(transport_data_system_folder,FILE_DATE_ID2))

#%%
#if they are there, remove cols called index, level_0
if 'index' in transport_data_system_df.columns:
    transport_data_system_df = transport_data_system_df.drop(columns=['index'])
if 'level_0' in transport_data_system_df.columns:
    transport_data_system_df = transport_data_system_df.drop(columns=['level_0'])
if 'Unnamed: 0' in transport_data_system_df.columns:
    transport_data_system_df = transport_data_system_df.drop(columns=['Unnamed: 0'])

#%%
#TEMP
#change the column names to be in capital letters with spaces instead of underscores
transport_data_system_df.columns = [x.title().replace('_',' ') for x in transport_data_system_df.columns]
#change some of the columns to have capitals in the first letter of their names (the columns are: Frequency, Measure, Unit ). BUT MAKE SURE ALL THE OTEHR LETTERS ARE LOWER CASE
transport_data_system_df['Frequency'] = transport_data_system_df['Frequency'].str.capitalize()
transport_data_system_df['Scope'] = transport_data_system_df['Scope'].str.capitalize()
transport_data_system_df['Measure'] = transport_data_system_df['Measure'].str.capitalize()
transport_data_system_df['Unit'] = transport_data_system_df['Unit'].str.capitalize()
#TEMP
#%%
#TEMPORARY FIX, CHANGE THE MEASURE IN TRANSPORT DATA SYSTEM FOR passenger_km and freight_tonne_km to Activity so that it matches the model concordance.
# transport_data_system_df.loc[transport_data_system_df['Measure']=='passenger_km','Measure'] = 'Activity'
# transport_data_system_df.loc[transport_data_system_df['Measure']=='freight_tonne_km','Measure'] = 'Activity'

# #change Date to year and filter out all non yearly data
# transport_data_system_df['Date'] = transport_data_system_df['Date'].str.split('-').str[0].astype(int)
transport_data_system_df = transport_data_system_df[transport_data_system_df['Frequency']=='Yearly']
#make sure scope is National
transport_data_system_df = transport_data_system_df[transport_data_system_df['Scope']=='National']

#%%
#drop unneccessary columns: 'Dataset', 'Source', 'Fuel', 'Comment', 'Scope'
transport_data_system_df = transport_data_system_df.drop(columns=[ 'Source', 'Fuel', 'Comment', 'Scope'])
#%%
#filter for the same years as are in the model concordances in the transport data system (should just be base Date)
transport_data_system_df = transport_data_system_df[transport_data_system_df.Date.isin(model_concordances_measures.Date.unique())]

#filter for the same measures as are in the model concordances in the transport data system
transport_data_system_df = transport_data_system_df[transport_data_system_df.Measure.isin(model_concordances_measures.Measure.unique())]

#now we have filtered out the majority of rows we dont need from the transport data system, we can use pandas difference() function to find out what rows we are missing from the transport data system. This will be useful for debugging and for the user to know what data is missing from the transport data system (as its expected that no data will be missing for the model to actually run))

#%%

INDEX_COLS_NO_SCENARIO = INDEX_COLS.copy()
INDEX_COLS_NO_SCENARIO.remove('Scenario')

#set index
transport_data_system_df.set_index(INDEX_COLS_NO_SCENARIO, inplace=True)
model_concordances_measures.set_index(INDEX_COLS_NO_SCENARIO, inplace=True)


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

    #now we need to add these rows to the transport_data_system_df
    #first create a df with the missing index values
    missing_index_values1 = pd.DataFrame(index=missing_index_values1)
    missing_index_values1['Data_available'] = 'row_and_data_not_available'
    missing_index_values1['Value'] = 0
    #then append to transport_data_system_df
    transport_data_system_df = pd.concat([missing_index_values1, transport_data_system_df], sort=False)

if missing_index_values2.empty:
    #this is unexpected so create an error
    # raise ValueError('All rows in the transport system dataset are present in the concordance. This is unexpected. Please check the code.')
    pass
else:
    #we just want to make sure the user is aware that we will be removing rows from the user input
    print('Removing unnecessary rows from the transport datasystem dataset. If you intended to have new data in the dataset, please make sure you have added them to the concordance table as well.')
    #remove these rows from the user_input
    transport_data_system_df.drop(missing_index_values2, inplace=True)

#%%
#TEMP
#if any of the missing values were for turnover rate then set it to 0.03
transport_data_system_df.loc[((transport_data_system_df.index.get_level_values('Measure')=='Turnover_rate') & (transport_data_system_df.Data_available=='row_and_data_not_available')), 'Value'] = 0.03
#%%



# #test what values in x dont equal the values in missing_index_values1
# for col in x.columns:
#     print(col)
#     print(x[col].equals(missing_index_values1[col]))
#%%
if not missing_index_values1.empty:
    missing_index_values1.reset_index(inplace=True)
    #save the missing values to a csv for use separately:
    missing_index_values1.to_csv('output_data/for_other_modellers/missing_values/{}_missing_input_values.csv'.format(FILE_DATE_ID), index=False)
else:
    print('No missing values in the transport data system dataset')
#%%
#create a scenario column in the transport data system dataset which will have a scenario for each in teh scenarios list in config

i = 0
for scenario in SCENARIOS_LIST:
    if i == 0:
        #create copy df
        new_transport_data_system_df = transport_data_system_df.copy()
        new_transport_data_system_df['Scenario'] = scenario
        i += 1
    else:
        transport_data_system_df['Scenario'] = scenario
        new_transport_data_system_df = new_transport_data_system_df.append(transport_data_system_df)
    
#%%
#save the new transport dataset
new_transport_data_system_df.to_csv('intermediate_data/{}_transport_data_system_extract.csv'.format(FILE_DATE_ID))
#%%
