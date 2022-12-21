#%%
#PLEASE NOTE THAT THIS IS A TEMPORARY VERSION OF THE ACTIVITY GROWTH CALCULATION WHICH CALCULATES ACTIVITY GROWTH BASED ON THE TRANSPORT_8TH EDITION. tHE INTENTION IS THAT THIS WILL INSTEAD BE CALCULATED USING GDP PER CAPCITA FORECASTS AND QAULITATIVE ADJUSTMENTS FOR EACH ECONOMY. 

#%%
#set working directory as one folder back so that config works
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
from runpy import run_path
exec(open("config/config.py").read())#usae this to load libraries and set variables. Feel free to edit that file as you need

#%%
#data
#take in activity data from 8th edition up to 2050 (activity_from_OSEMOSYS-hughslast.csv)
activity = pd.read_csv('intermediate_data/cleaned_input_data/activity_from_OSEMOSYS-hughslast.csv')#TODO, keeping this input for now because we intend to calculate activity growth using a more complex method in the future (not just importing activity from transport data system)

#RENAME Activity to Value
activity.rename(columns={'Activity': 'Value'}, inplace=True)

#define index cols
INDEX_COLS = ['Economy','Year']

#remove unnecessary cols and remove duplicates (all cols that arent INDEX_COLS or Value)
activity.drop([col for col in activity.columns if col not in INDEX_COLS + ['Value']], axis=1, inplace=True)
activity.drop_duplicates(inplace=True)
    
#%%
#sum up Value col by index cols
activity_growth = activity.groupby(INDEX_COLS).sum().reset_index()

#sort by year and everything else in ascending order
activity_growth = activity_growth.sort_values(by=INDEX_COLS)

#calc growth rate. set index so that the growth rate is calc only for Value col
activity_growth = activity_growth.set_index(INDEX_COLS).pct_change()

#now set all vlaues during the base year to 1 as the growth rate is not defined for the base year (in the code its actually using the row above for 2050 currently)
activity_growth.loc[activity_growth.index.get_level_values('Year') == BASE_YEAR, 'Value'] = 0

#replace NAN with 0 
activity_growth = activity_growth.fillna(0)

#Create measure col and name it Activity_growth
# activity_growth['Measure'] = 'Activity_growth'

#rename value to Activity_growth
activity_growth.rename(columns={'Value': 'Activity_growth'}, inplace=True)
#TEMP FIX UNTIL WE DICIDE HOW/IF WE WANT TO DIFFERENTIATE ACTIVITY GROWTH BY SCENARIOS 
#create scenario column and replicate the activity data for each scenario in SCENARIOS_LIST

#reset index so that scenario col can be added
activity_growth = activity_growth.reset_index()
frist_iteration=True
for scenario in SCENARIOS_LIST:
    activity_growth_scenario = activity_growth.copy()
    activity_growth_scenario['Scenario'] = scenario
    if frist_iteration==True:
        activity_growth = activity_growth_scenario.copy()
        frist_iteration=False
    else:
        activity_growth = activity_growth.append(activity_growth_scenario, ignore_index=True)
#%%
#i wuoldve thought that the activity growth rate would be the same for all groups ? Perhaps that is what i should aim for in the future, but keep this code the same as it is so it can be more flexible? I guess it raises question of how i want to calcualte activity growth? Should it be simplified to 'ecnony activity griwth' or more complex like transport type activity growth or even medium/trans[porttype activity growth
#or even pct change by econmy since the rate should be the same?

#%%
#save
activity_growth.to_csv('intermediate_data/model_inputs/activity_growth.csv', index=False)


#%%