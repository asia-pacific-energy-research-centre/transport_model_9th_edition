#%%
#set working directory as one folder back so that config works
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
execfile("config/config.py")#usae this to load libraries and set variables. Feel free to edit that file as you need

#%%
#data
activity = pd.read_csv('intermediate_data/cleaned_input_data/activity_from_OSEMOSYS-hughslast.csv')

#%%
# TEMP
#calcualte activity growth from the activity data that ahs been forecasted already
#in the future this may already be part of the activity data input
# activity_growth = activity.loc[activity.Medium == 'road',:]
#may needto think about what subsets of data to use for this but for now no 


#sum up to transport type
activity_growth = activity.groupby(['Economy', 'Scenario', 'Transport Type','Year', 'Medium']).sum().reset_index()

#sort by year and everything else in ascending order
activity_growth = activity_growth.sort_values(by=['Economy', 'Scenario', 'Transport Type', 'Medium', 'Year'])

#calc growth rate. set index so that the growth rate is calc only for Value col
activity_growth2 = activity_growth.set_index(['Economy', 'Scenario', 'Transport Type', 'Medium', 'Year']).pct_change()

# #add 1 tpo the percentage cahnge to calcualte the growth rate
# activity_growth2 = activity_growth2 + 1 #removed as i relaised that this intereacted weirdly with negatives

#now set all vlaues during the base year to 1 as the growth rate is not defined for the base year (in the code its actually using the row above for 2050 currently)
activity_growth2.loc[activity_growth2.index.get_level_values('Year') == BASE_YEAR, 'Activity'] = 0

#replace NAN with 0 
activity_growth2 = activity_growth2.fillna(0)

#rename col to Activity_growth
activity_growth2.rename(columns={"Activity": "Activity_growth"}, inplace=True)

#merge back on the activity data
activity_growth = activity_growth.merge(activity_growth2, on=['Economy', 'Scenario', 'Transport Type', 'Medium', 'Year'], how='left')

economy_growth = True
if economy_growth == True:

    #sum up by economy
    activity_growth = activity.groupby(['Economy', 'Scenario', 'Year']).sum().reset_index()

    #sort by year and everything else in ascending order
    activity_growth = activity_growth.sort_values(by=['Economy', 'Scenario', 'Year'])

    #calc growth rate. set index so that the growth rate is calc only for Value col
    activity_growth2 = activity_growth.set_index(['Economy', 'Scenario', 'Year']).pct_change()

    # #add 1 tpo the percentage cahnge to calcualte the growth rate
    # activity_growth2 = activity_growth2 + 1

    #now set all vlaues during the base year to 1 as the growth rate is not defined for the base year
    activity_growth2.loc[activity_growth2.index.get_level_values('Year') == BASE_YEAR, 'Activity'] = 0

    #replace NAN with 0
    activity_growth2 = activity_growth2.fillna(0)

    #rename col to Activity_growth
    activity_growth2.rename(columns={"Activity": "Activity_growth"}, inplace=True)

    #merge back on the activity data
    activity_growth = activity_growth.merge(activity_growth2, on=['Economy', 'Scenario', 'Year'], how='left')

#%%
#drop cols
activity_growth.drop(['Activity'], axis=1, inplace=True)

#%%
#i wuoldve thought that the activity growth rate would be the same for all groups ? Perhaps that is what i should aim for in the future, but keep this code the same as it is so it can be more flexible? I guess it raises question of how i want to calcualte activity growth? Should it be simplified to 'ecnony activity griwth' or more complex like transport type activity growth or even medium/trans[porttype activity growth
#or even pct change by econmy since the rate should be the same?

#%%
#save
activity_growth.to_csv('intermediate_data/model_inputs/activity_growth.csv', index=False)

#%%