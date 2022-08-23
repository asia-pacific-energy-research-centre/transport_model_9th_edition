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
#load model output
road_model_output = pd.read_csv('intermediate_data/road_model/{}'.format(model_output_file_name))
# non_road_model_output = pd.read_csv('intermediate_data/non_road_model/main_dataframe_years_2017_to_2030_DATE20220822_2124.csv')
#%%
road_model_output['Medium'] = 'road'
non_road_model_output = road_model_output.loc[(road_model_output['Medium'] != 'road')]#TEMPORARY, replace with non road model output later

#concatenate road and non road models output
model_output_all = pd.concat([road_model_output, non_road_model_output])

#%%
#save
model_output_all.to_csv('intermediate_data/model_output_concatenated/{}'.format(model_output_file_name), index=False)

#%%