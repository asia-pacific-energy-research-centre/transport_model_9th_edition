#%%
#set working directory as one folder back so that config works
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
from runpy import run_path
exec(open("config/config.py").read())#usae this to load libraries and set variables. Feel free to edit that file as you need
#%%
# model_output_file_name = 'model_output_years_2017_to_2050_DATE20220824_1043.csv'
#take in model ouput and clean ready to use in analysis
model_output_all_with_fuels = pd.read_csv('intermediate_data/model_output_with_fuels/2_supply_side/{}'.format(model_output_file_name))
model_output_all = pd.read_csv('intermediate_data/model_output_concatenated/{}'.format(model_output_file_name))
#%%
#remove any rows where the energy use is 0 from the 'with fuels' dataset.
model_output_all_with_fuels = model_output_all_with_fuels[model_output_all_with_fuels['Energy'] > 0]

#%%
#create a detailed and non detailed output from the 'without fuels' dataframes. Then create a model output which is jsut energy use, with the fuels. 
#detailed output can jsut be the current output, the non_deetailed can just have stocks, energy and activity data
model_output_detailed = model_output_all.copy()
model_output_non_detailed = model_output_all.copy()
model_output_non_detailed = model_output_non_detailed[['Date', 'Economy', 'Scenario', 'Transport Type', 'Vehicle Type', 'Drive', 'Medium','Stocks', 'passenger_km','freight_tonne_km', 'Energy']]

#now create 'with fuels' output which will only contain energy use. This is to avoid any confusion because the 'with fuels' output contians activity and stocks replicated for each fuel type within a vehicel type / drive combination. 
model_output_all_with_fuels = model_output_all_with_fuels[['Date', 'Economy', 'Scenario', 'Transport Type', 'Vehicle Type', 'Drive', 'Medium', 'Fuel',  'Energy']]

#%%
#save data
model_output_detailed.to_csv('output_data/model_output_detailed/{}'.format(model_output_file_name), index=False)

model_output_non_detailed.to_csv('output_data/model_output/{}'.format(model_output_file_name), index=False)

model_output_all_with_fuels.to_csv('output_data/model_output_with_fuels/{}'.format(model_output_file_name), index=False)
#%%
