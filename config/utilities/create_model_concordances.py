
#%%
#set working directory as one folder back so that config works
from datetime import datetime
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
from runpy import run_path
exec(open("config/config.py").read())#usae this to load libraries and set variables. Feel free to edit that file as you need

#%%
#create set of categories of data that will be output by the model. 
osemosys_concordances = pd.read_csv('config/concordances/OSEMOSYS_concordances.csv')
osemosys_concordances.drop(['FUEL', 'TECHNOLOGY'], axis=1, inplace=True)
#drop duplicates
osemosys_concordances.drop_duplicates(inplace=True)

#could create concordances for each year, economy and scenario and then cross that with the osemosys_concordances to get the final concordances
model_concordances = pd.DataFrame(columns=osemosys_concordances.columns)
for year in range(BASE_YEAR, END_YEAR+1):
    for economy in Economy_list:
        for scenario in Scenario_list:
            #create concordances for each year, economy and scenario
            osemosys_concordances_year = osemosys_concordances.copy()
            osemosys_concordances_year['Year'] = str(year)
            osemosys_concordances_year['Economy'] = economy
            osemosys_concordances_year['Scenario'] = scenario
            #merge with osemosys_concordances
            model_concordances = pd.concat([model_concordances, osemosys_concordances_year])

#save model_concordances with date
model_concordances.to_csv('config/concordances/{}'.format(model_concordances_file_name), index=False)

#%%
#create model concordances with a fuel column. 
model_concordances_fuels = model_concordances.copy()
model_concordances_fuels_NO_BIOFUELS = model_concordances.copy()
#every drive type has associated fuel/s. We will create a dicvtonary of drive types and fuels and then use that to create the fuel column
#drive types: 'air', 'nonspecified', 'rail', 'bev', 'cng', 'd', 'fcev', 'g','lpg', 'phevg', 'ship', 'phevd'
#fuel types: 16_5_biogasoline, 16_7_bio_jet_kerosene, 16_x_hydrogen, 7_2_aviation_gasoline, 7_x_jet_fuel, 17_electricity, 8_1_natural_gas, 16_6_biodiesel, 7_7_gas_diesel_oil, 7_1_motor_gasoline, 7_9_lpg, 7_6_kerosene, 7_8_fuel_oil, 7_x_other_petroleum_products, 1_x_coal_thermal

#this one contains biofuels. PLEASE note that it may not contain all possible fuel uses. It would be good to add new ones if there are. These are jsut the ones that finn could think of. 
#thsi is important to keep up to date because it will be used to create the user input spreadsheet for the demand side fuel mixing (involving removing the biofuels as they will be stated in the supply sdide fuel mixing)
drive_type_to_fuel_dict = {'air': ['7_x_jet_fuel', '16_7_bio_jet_kerosene', '7_6_kerosene'],
                        'nonspecified': ['nonspecified'],
                        'rail': ['7_7_gas_diesel_oil', '16_6_biodiesel', '17_electricity', '1_x_coal_thermal'],
                        'bev': ['17_electricity'],
                        'cng': ['8_1_natural_gas'],
                        'd': ['7_7_gas_diesel_oil', '16_6_biodiesel'],
                        'fcev': ['16_x_hydrogen'],
                        'g': ['7_1_motor_gasoline', '16_5_biogasoline'],
                        'lpg': ['7_9_lpg'],
                        'phevg': ['17_electricity', '7_1_motor_gasoline', '16_5_biogasoline'],
                        'ship': ['7_7_gas_diesel_oil', '7_8_fuel_oil', '7_x_other_petroleum_products', '16_6_biodiesel'],
                        'phevd': ['7_7_gas_diesel_oil', '17_electricity', '16_6_biodiesel']
                        }

#make the dict 1 to 1 by going through the lists for each key and creating a new row in a df
drive_type_to_fuel_df = pd.DataFrame(columns=['Drive', 'Fuel'])
for k,v in drive_type_to_fuel_dict.items():
    for x in v:
        drive_type_to_fuel_df = drive_type_to_fuel_df.append({'Drive': k, 'Fuel': x}, ignore_index=True)

#make a version of the df with no biofuels
drive_type_to_fuel_df_NO_BIOFUELS = drive_type_to_fuel_df[~drive_type_to_fuel_df['Fuel'].str.contains('bio')]

#merge the dict to our model concordances
model_concordances_fuels = pd.merge(model_concordances_fuels, drive_type_to_fuel_df, how='left', on=['Drive'])

model_concordances_fuels_NO_BIOFUELS = pd.merge(model_concordances_fuels_NO_BIOFUELS, drive_type_to_fuel_df_NO_BIOFUELS, how='left', on=['Drive'])

#save
model_concordances_fuels.to_csv('config/concordances/{}'.format(model_concordances_file_name_fuels), index=False)
model_concordances_fuels_NO_BIOFUELS.to_csv('config/concordances/{}'.format(model_concordances_file_name_fuels_NO_BIOFUELS), index=False)
# #%%
# #create a user input spreadsheet using the model concordances above
# #we want the year column to become wide, so we'll use pivot_table
# model_concordances_wide = model_concordances.copy()
# model_concordances_wide['Value'] = 1
# # model_concordances_wide['Year'] = str(model_concordances_wide['Year'])
# model_concordances_wide = model_concordances_wide.pivot_table(index=['Medium',	'Transport Type',	'Vehicle Type',	'Drive', 'Economy',	'Scenario'
# ], columns='Year', values='Value').reset_index()

# #save model_concordances_wide with date
# model_concordances_wide.to_csv('config/concordances/model_concordances_wide_{}.csv'.format(datetime.datetime.now().strftime("%Y%m%d")), index=False)
#%%
