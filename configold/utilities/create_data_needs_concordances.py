
#%%
#set working directory as one folder back so that config works
from datetime import datetime
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
from runpy import run_path
exec(open("config/config.py").read())#usae this to load libraries and set variables. Feel free to edit that file as you need

#%%
#laod model output detailed
model_output_detailed = pd.read_csv('output_data/model_output_detailed/{}'.format(model_output_file_name))
#%%

#CREATE DATA NEEDS CONCORDANCES
#TEST
#create a dataset we can use to show what data we need based on the variables in the detailed model output:
#filter for year = 2019
model_output_detailed_data_needs_list = model_output_detailed[model_output_detailed['Year'] == 2019]

#filter for medium = road
model_output_detailed_data_needs_list = model_output_detailed_data_needs_list[model_output_detailed_data_needs_list['Medium'] == 'road']

#drop non useful cols
#we need to make it clear whether activity is passenger or freight so we will change transport type to 'activity type' to make this clear
#so if transport type is 'passenger' then set Activity type to passenger km and if transport type is 'freight' then set Activity type to freight tonne km
model_output_detailed_data_needs_list['Activity type'] = model_output_detailed_data_needs_list['Transport Type'].apply(lambda x: 'passenger km' if x == 'passenger' else 'freight tonne km')

#now drop non useful cols
model_output_detailed_data_needs_list = model_output_detailed_data_needs_list.drop(['Scenario', 'Year', 'Transport Type', 'Efficiency', 'Surplus_stocks', 'Travel_km_per_stock', 'Medium'], axis = 1)

#rename vehicle sales share to vehicle sales
model_output_detailed_data_needs_list.rename({'Vehicle sales share': 'Vehicle sales'}, inplace=True)

#its quite large still. How to simplify it? Need to think outside box

#remove drive trype
model_output_detailed_data_needs_list = model_output_detailed_data_needs_list.drop(['Drive'], axis = 1)

#%%
#sum to rmeove dupes
model_output_detailed_data_needs_list_no_drive = model_output_detailed_data_needs_list.groupby(['Economy', 'Vehicle Type']).sum().reset_index()

# %%
#also remove measures we are less interested in getting 100% accurate:(eg. because their accuracy is less signifciant to the model)
# model_output_detailed_data_needs_list_no_drive = model_output_detailed_data_needs_list_no_drive.drop([''], axis = 1)


