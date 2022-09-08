#take in detailed output data and print out any useful metrics/statisitcs to summarise the reults of the model. the intention is that the output willbe easy to view through the command line, and that the output will be saved to a file for later viewing.

#%%
#set working directory as one folder back so that config works
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
execfile("config/config.py")#usae this to load libraries and set variables. Feel free to edit that file as you need

import plotly
import plotly.express as px
pd.options.plotting.backend = "plotly"#set pandas backend to plotly plotting instead of matplotlib
import plotly.io as pio
# pio.renderers.default = "browser"#allow plotting of graphs in the interactive notebook in vscode #or set to notebook
#%%

#load data in
model_output_all = pd.read_csv('output_data/model_output/{}'.format(model_output_file_name))
model_output_detailed = pd.read_csv('output_data/model_output_detailed/{}'.format(model_output_file_name))
change_dataframe_aggregation = pd.read_csv('intermediate_data/road_model/change_dataframe_aggregation.csv')
#%%
#FILTER FOR SCENARIO OF INTEREST
#this should be temporary as the scenario should be passed in as a parameter through config if it is useed elsewhere

model_output_all = model_output_all[model_output_all['Scenario']==SCENARIO_OF_INTEREST]
model_output_detailed = model_output_detailed[model_output_detailed['Scenario']==SCENARIO_OF_INTEREST]
change_dataframe_aggregation = change_dataframe_aggregation[change_dataframe_aggregation['Scenario']==SCENARIO_OF_INTEREST]
#%%

################################################################################################################################################################

#when we look at stocks and sales of bevs vs ices we see that the stock of bevs doesnt rise at all even when its sales are higher than ices, and ice stocks are rising fast.
#lets dig into it. lets look at nz lv sales

model_output_detailed_nz_lv = model_output_detailed[model_output_detailed['Economy']=='12_NZ']
model_output_detailed_nz_lv = model_output_detailed_nz_lv[model_output_detailed_nz_lv['Vehicle Type']=='lv']
model_output_detailed_nz_lv = model_output_detailed_nz_lv[model_output_detailed_nz_lv['Drive'].isin(['g', 'bev'])]

#for this we will use matplotlib
import matplotlib.pyplot as plt
plt.rcParams['figure.facecolor'] = 'w'
pd.options.plotting.backend = "matplotlib"


#plot stocks
fig, ax = plt.subplots()
for key, grp in model_output_detailed_nz_lv.groupby(['Drive']):
    ax = grp.plot(ax=ax, kind='line', x='Year', y='Stocks', label=key)
plt.show()

#plot sales share
fig, ax = plt.subplots()
for key, grp in model_output_detailed_nz_lv.groupby(['Drive']):
    ax = grp.plot(ax=ax, kind='line', x='Year', y='Vehicle_sales_share', label=key)

#plot Travel_km_per_stock
fig, ax = plt.subplots()
for key, grp in model_output_detailed_nz_lv.groupby(['Drive']):
    ax = grp.plot(ax=ax, kind='line', x='Year', y='Travel_km_per_stock', label=key)

#############################################
#%%
#look at change_dataframe_aggregation
change_dataframe_aggregation_nz_lv = change_dataframe_aggregation[change_dataframe_aggregation['Economy']=='12_NZ']
change_dataframe_aggregation_nz_lv = change_dataframe_aggregation_nz_lv[change_dataframe_aggregation_nz_lv['Vehicle Type']=='lv']
change_dataframe_aggregation_nz_lv = change_dataframe_aggregation_nz_lv[change_dataframe_aggregation_nz_lv['Drive'].isin(['g', 'bev'])]

#plot Activity_growth
fig, ax = plt.subplots()
for key, grp in change_dataframe_aggregation_nz_lv.groupby(['Drive']):
    ax = grp.plot(ax=ax, kind='line', x='Year', y='Activity_growth', label=key)

#plot New_stock_sales_activity
fig, ax = plt.subplots()
for key, grp in change_dataframe_aggregation_nz_lv.groupby(['Drive']):
    ax = grp.plot(ax=ax, kind='line', x='Year', y='New_stock_sales_activity', label=key)

#%%






