#%%
#set working directory as one folder back so that config works
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
execfile("config/config.py")#usae this to load libraries and set variables. Feel free to edit that file as you need
#%%
# model_output_file_name = 'model_output_years_2017_to_2050_DATE20220823_1701.csv'
#take in model ouput and clean ready to use in analysis
model_output_all = pd.read_csv('intermediate_data/model_output_with_fuels/2_supply_side/{}'.format(model_output_file_name))

#%%
#create a detailed and non detailed output
#detailed output can jsut be the current output, the non_deetailed can just have stocks, energy and activity data
model_output_detailed = model_output_all.copy()
model_output_non_detailed = model_output_all.copy().loc[:, ['Year', 'Economy', 'Scenario', 'Transport Type', 'Vehicle Type', 'Drive', 'Medium', 'Fuel', 'Stocks', 'Activity', 'Energy']]

#%%
#save data
model_output_detailed.to_csv('output_data/model_output_detailed/{}'.format(model_output_file_name), index=False)

model_output_non_detailed.to_csv('output_data/model_output/{}'.format(model_output_file_name), index=False)

#%%