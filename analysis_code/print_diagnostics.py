#take in detailed output data and print out any useful metrics/statisitcs to summarise the reults of the model. the intention is that the output willbe easy to view through the command line, and that the output will be saved to a file for later viewing.

#%%
#set working directory as one folder back so that config works
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
execfile("config/config.py")#usae this to load libraries and set variables. Feel free to edit that file as you need

# pio.renderers.default = "browser"#allow plotting of graphs in the interactive notebook in vscode #or set to notebook
import matplotlib.pyplot as plt
plt.rcParams['figure.facecolor'] = 'w'
#%%

#load data in
model_output_all = pd.read_csv('output_data/model_output/{}'.format(model_output_file_name))
model_output_detailed = pd.read_csv('output_data/model_output_detailed/{}'.format(model_output_file_name))

model_output_8th = pd.read_csv('intermediate_data/activity_efficiency_energy_road_stocks.csv')

#%%
#FILTER FOR SCENARIO OF INTEREST
#this should be temporary as the scenario should be passed in as a parameter through config if it is useed elsewhere
SCENARIO_OF_INTEREST = 'Carbon Neutral'
model_output_all = model_output_all[model_output_all['Scenario']==SCENARIO_OF_INTEREST]
model_output_8th = model_output_8th[model_output_8th['Scenario']==SCENARIO_OF_INTEREST]
model_output_detailed = model_output_detailed[model_output_detailed['Scenario']==SCENARIO_OF_INTEREST]
#%%
#create a dataframe that has the 8th and 9th concatenated
#create column in both datasets that states the dataset
model_output_9th = model_output_all.copy()
model_output_9th['Dataset'] = '9th'
model_output_8th['Dataset'] = '8th'

#concatenate data together
model_output_both_scenarios = pd.concat([model_output_9th, model_output_8th], axis=0)

################################################################################################################################################################

#%%
#plot the total surplus stocks for all economy dor each year
title='Total surplus stocks for all economys for each year'
#sum surplus stocks for each economy for each year
model_output_surplus = model_output_detailed.groupby(['Year'])['Surplus_stocks'].sum().reset_index()

plt.plot(model_output_surplus['Year'], model_output_surplus['Surplus_stocks'])
plt.title(title)

################################################################################################################################################################
#%%
#plot energy use for all economys for each year, by drive type.
title = 'Total energy use for all economys for each year, drive type'
model_output_detailed_vtype = model_output_detailed.groupby(['Year', 'Drive'])['Energy'].sum().reset_index()

#plot
fig, ax = plt.subplots()
for key, grp in model_output_detailed_vtype.groupby(['Drive']):
    ax = grp.plot(ax=ax, kind='line', x='Year', y='Energy', label=key)
plt.title(title)
plt.show()

################################################################################################################################################################
#%%
#plot stocks use for all economys for each year, by drive type.
title='Total stocks for all economys for each year, drive type'
model_output_detailed_vtype = model_output_detailed.groupby(['Year', 'Drive'])['Stocks'].sum().reset_index()

#plot
fig, ax = plt.subplots()
for key, grp in model_output_detailed_vtype.groupby(['Drive']):
    ax = grp.plot(ax=ax, kind='line', x='Year', y='Stocks', label=key)
plt.title(title)
plt.show()

################################################################################################################################################################
#%%
#show the uptake of BEVs by year, per economy
title = 'Total stocks of BEVs for each year, by economy'
model_output_detailed_bevs = model_output_detailed[model_output_detailed['Drive'] == 'bev']
model_output_detailed_bevs = model_output_detailed_bevs.groupby(['Year', 'Economy'])['Stocks'].sum().reset_index()

#plot
fig, ax = plt.subplots()
for key, grp in model_output_detailed_bevs.groupby(['Economy']):
    ax = grp.plot(ax=ax, kind='line', x='Year', y='Stocks', label=key)
plt.title(title)
plt.show()
#%%
################################################################################################################################################################
#plot the average vehivle sales shares for each economy for each year, for LV's
title = 'Average vehicle sales shares for each drive for passenger LVs'
model_output_detailed_sales = model_output_detailed[model_output_detailed['Vehicle Type'] == 'lv']
# #tet out excludeing china 05_PRC
# model_output_detailed_sales = model_output_detailed_sales[model_output_detailed_sales['Economy'] != '05_PRC']
model_output_detailed_sales = model_output_detailed_sales[model_output_detailed_sales['Transport Type'] == 'passenger']
model_output_detailed_sales = model_output_detailed_sales.groupby(['Year', 'Drive'])['Vehicle_sales_share'].mean().reset_index()

#plot
fig, ax = plt.subplots()
for key, grp in model_output_detailed_sales.groupby(['Drive']):
    ax = grp.plot(ax=ax, kind='line', x='Year', y='Vehicle_sales_share', label=key)
plt.title(title)
plt.show()
#%%
################################################################################################################################################################

#plot the average vehivle sales shares for each economy for each year
title = 'Average vehicle sales shares for each drive for passenger'
model_output_detailed_sales = model_output_detailed[model_output_detailed['Transport Type'] == 'passenger']
model_output_detailed_sales = model_output_detailed_sales.groupby(['Year', 'Drive'])['Vehicle_sales_share'].mean().reset_index()

#plot
fig, ax = plt.subplots()
for key, grp in model_output_detailed_sales.groupby(['Drive']):
    ax = grp.plot(ax=ax, kind='line', x='Year', y='Vehicle_sales_share', label=key)
plt.title(title)
plt.show()

#%%
#Plot the ratio of BEVs and PHEVs to ICEs by year, and economy
model_output_detailed_ratio_drive = model_output_detailed.groupby(['Year', 'Economy', 'Drive'])['Stocks'].sum().reset_index()

model_output_detailed_ratio_drive = model_output_detailed_ratio_drive.pivot(index=['Year', 'Economy'], columns='Drive', values='Stocks')

#replace any nan's with 0's
model_output_detailed_ratio_drive = model_output_detailed_ratio_drive.fillna(0)

model_output_detailed_ratio_drive['BEV_ICE_ratio'] = model_output_detailed_ratio_drive['bev'] / (model_output_detailed_ratio_drive['bev'] + model_output_detailed_ratio_drive['g'] + model_output_detailed_ratio_drive['d'])

model_output_detailed_ratio_drive['PHEV_ICE_ratio'] = (model_output_detailed_ratio_drive['phevg'] +  model_output_detailed_ratio_drive['phevd']) / (model_output_detailed_ratio_drive['phevg'] +  model_output_detailed_ratio_drive['phevd'] + model_output_detailed_ratio_drive['g'] + model_output_detailed_ratio_drive['d'])

model_output_detailed_ratio_drive = model_output_detailed_ratio_drive[['BEV_ICE_ratio', 'PHEV_ICE_ratio']]

model_output_detailed_ratio_drive = model_output_detailed_ratio_drive.reset_index()
#plot
fig, ax = plt.subplots()
for key, grp in model_output_detailed_ratio_drive.groupby(['Economy']):
    ax = grp.plot(ax=ax, kind='line', x='Year', y='BEV_ICE_ratio', label=key)
plt.title('Ratio of BEVs to ICEs for each year, by economy')
plt.show()

#plot
fig, ax = plt.subplots()
for key, grp in model_output_detailed_ratio_drive.groupby(['Economy']):
    ax = grp.plot(ax=ax, kind='line', x='Year', y='PHEV_ICE_ratio', label=key)
plt.title('Ratio of PHEVs to ICEs for each year, by economy')

################################################################################################################################################################
#%%
#plot total energy use, activity and stocks compared to the 8th edition
title = 'Total energy use compared to the 8th edition'
#sum energy use for each dataset for each year
model_output_energy = model_output_both_scenarios.groupby(['Year', 'Dataset'])['Energy'].sum().reset_index()
#plot
fig, ax = plt.subplots()
for key, grp in model_output_energy.groupby(['Dataset']):
    ax = grp.plot(ax=ax, kind='line', x='Year', y='Energy', label=key)
plt.title(title)
plt.show()

title = 'Total activity compared to the 8th edition'
#sum activity for each dataset for each year
model_output_activity = model_output_both_scenarios.groupby(['Year', 'Dataset'])['Activity'].sum().reset_index()
#plot
fig, ax = plt.subplots()
for key, grp in model_output_activity.groupby(['Dataset']):
    ax = grp.plot(ax=ax, kind='line', x='Year', y='Activity', label=key)
plt.title(title)
plt.show()

title = 'Total stocks compared to the 8th edition'
#sum stocks for each dataset for each year
model_output_stocks = model_output_both_scenarios.groupby(['Year', 'Dataset'])['Stocks'].sum().reset_index()
#plot
fig, ax = plt.subplots()
for key, grp in model_output_stocks.groupby(['Dataset']):
    ax = grp.plot(ax=ax, kind='line', x='Year', y='Stocks', label=key)
plt.title(title)
plt.show()


################################################################################################################################################################

################################################################################################################################################################
# #analysis
# #check for duplicates
# duplicates = model_output_all.duplicated().sum()
# if duplicates > 0:
#     print('There are {} duplicates in the model output'.format(duplicates))
# #check for missing values
# NAs = model_output_all.isna().sum().sum()
# if NAs > 0:
#     print('There are {} missing values in the model output'.format(NAs))





# #%%
# #compare model output to 8th edition output. If there are any differences, print them
# #laod output from 8th edition
# model_output = pd.read_csv('output_data/model_output_detailed/{}'.format(model_output_file_name))
# model_output_8th = pd.read_csv('output_data/model_output_detailed/activity_efficiency_energy_road_stocks.csv')

# #%%
# #plot energy use
# #get data for energy use by year, economy, in both scenarios

# #%%
# title='Surplus stocks use by year, economy, in both scenarios'

# data_3_select_years_other_regions = data_3_select_years[data_3_select_years['ECON_Sub_Category'] != 'China_USA']

# #plot
# fig = px.line(data_3_select_years_other_regions, x="Year", y="PJ", color="Scenario", line_dash='Scenario', facet_col="Economy_name", facet_col_wrap=7, title=title)#, #facet_col="Economy",
#              #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
# fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles

# #fig.show()  
# import plotly
# plotly.offline.plot(fig, filename='./plotting_output/' + title + '.html')
# fig.write_image("./plotting_output/static/" + title + '.png')


# #%%


# #%%
# title='Energy use by year, economy, in both scenarios'

# #plot
# fig = px.line(data_3_select_years, x="Year", y="PJ", color="Scenario", line_dash='Scenario', facet_col="Economy_name", facet_col_wrap=7, title=title)#, #facet_col="Economy",
#              #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
# fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles

# #fig.show()  
# import plotly
# plotly.offline.plot(fig, filename='./plotting_output/' + title + '.html')
# fig.write_image("./plotting_output/static/" + title + '.png')


# #%%
