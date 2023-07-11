#take in output data and do basic visualisationh and analysis

#%%
#set working directory as one folder back so that config works
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
from runpy import run_path
run_path("config/config.py")#usae this to load libraries and set variables. Feel free to edit that file as you need

import plotly
import plotly.express as px
pd.options.plotting.backend = "plotly"#set pandas backend to plotly plotting instead of matplotlib
import plotly.io as pio
# pio.renderers.default = "browser"#allow plotting of graphs in the interactive notebook in vscode #or set to notebook

#%%
#compare model output to 8th edition output. If there are any differences, print them
#laod output from 8th edition
model_output = pd.read_csv('output_data/model_output_detailed/{}'.format(model_output_file_name))
change_dataframe_road = pd.read_csv('intermediate_data/road_model/change_dataframe_aggregation.csv')
change_dataframe_non_road = pd.read_csv('intermediate_data/non_road_model/change_dataframe_aggregation.csv')

#%%
# plot activity growth
a_growth = change_dataframe_road[['Economy', 'Scenario', 'Date', 'Transport Type', 'Activity_growth', 'Activity']].drop_duplicates()


title='Activity growth by Date,Scenario, economy,for each transport type'

#plot
fig = px.line(a_growth, x="Date", y="Activity_growth", color="Transport Type", line_dash='Scenario', facet_col="Economy", facet_col_wrap=7, title=title)#, #facet_col="Economy",
             #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles


plotly.offline.plot(fig, filename='./plotting_output/change_dataframe/' + title + '.html')
fig.write_image("./plotting_output/change_dataframe/static/" + title + '.png', scale=1, width=2000, height=800)

################################################################################################################################################################
#%%
#calcualte activity growth from the activity value for each Date in case the activity growth isnt being calculated correctly

new_a_growth1 = a_growth[['Economy', 'Scenario', 'Transport Type', 'Date', 'Activity']]
#sum up activity by economy, scenario, transport type
new_a_growth1 = new_a_growth1.groupby(['Economy', 'Scenario', 'Transport Type', 'Date']).sum().reset_index()
#sort values by Date
new_a_growth1 = new_a_growth1.sort_values(by=['Economy', 'Scenario', 'Transport Type', 'Date'])

#calc growth rate. set index so that the growth rate is calc only for Value col
new_a_growth2 = new_a_growth1.set_index(['Economy', 'Scenario', 'Transport Type', 'Date']).pct_change().reset_index()

#rename to 'a_growth_recalcualted'
new_a_growth2 = new_a_growth2.rename(columns={'Activity': 'Activity_growth'})

#join back on the absoutle activity growth
new_a_growth = new_a_growth1.merge(new_a_growth2, on=['Economy', 'Scenario', 'Transport Type', 'Date'], how='left')


#before concat we need to sum up activity for each Date, economy, scenario, transport type in original df. (but not a_growth, but luckily we can just group by this since it is the same for the categories we need )
a_growth_old = a_growth[['Economy', 'Scenario', 'Transport Type', 'Date', 'Activity_growth', 'Activity']]
a_growth_old = a_growth_old.groupby(['Economy', 'Scenario', 'Transport Type', 'Date', 'Activity_growth']).sum().reset_index()#not 100% it will work

#create label
new_a_growth['dataset'] = 'recalculated'
a_growth_old['dataset'] = 'original'

#concat back into original df
a_growth2 = pd.concat([new_a_growth,a_growth_old])

#join together the transport tyep and scenario cols
a_growth2['TransportType_scenario'] = a_growth2['Transport Type'] + ' ' + a_growth2['Scenario']

#PLOT
title='COMPARISON Activity growth by Date,Scenario, economy,for each transport type'

#plot
fig = px.line(a_growth2, x="Date", y="Activity_growth", color="TransportType_scenario", line_dash='dataset', facet_col="Economy", facet_col_wrap=7, title=title)#, #facet_col="Economy",
             #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles

plotly.offline.plot(fig, filename='./plotting_output/change_dataframe/' + title + '.html')
fig.write_image("./plotting_output/change_dataframe/static/" + title + '.png', scale=1, width=2000, height=800)


#PLOT
title='COMPARISON Activity by Date,Scenario, economy,for each transport type'

#plot
fig = px.line(a_growth2, x="Date", y="Activity", color="TransportType_scenario", line_dash='dataset', facet_col="Economy", facet_col_wrap=7, title=title)#, #facet_col="Economy",
             #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles

plotly.offline.plot(fig, filename='./plotting_output/change_dataframe/' + title + '.html')
fig.write_image("./plotting_output/change_dataframe/static/" + title + '.png', scale=1, width=2000, height=800)
################################################################################################################################################################
#%%

# #take a look at vehicle sales share normalised and see whether it causes activity to grow faster than we intended it to.
# #for simplicity lets jsut look at datafor NZ in scneario = reference.
# change_dataframe_road_nz_ref = change_dataframe_road[(change_dataframe_road['Economy']=='12_NZ') & (change_dataframe_road['Scenario']=='Reference')]

# #filter for only interesting data points
# change_dataframe_road_nz_ref = change_dataframe_road_nz_ref[['Economy', 'Scenario', 'Date', 'Transport Type','Vehicle Type','Drive', 'Activity_growth', 'Activity', 'Original_activity', 'Vehicle_sales_share_normalised', 'New_stock_sales_activity', 'Activity_transport_type_sum', 'Activity_transport_type_growth_abs', 'Vehicle_sales_share_adjusted', 'Vehicle_sales_share_sum' ]]

# #sort by Date and transport type
# change_dataframe_road_nz_ref = change_dataframe_road_nz_ref.sort_values(by=['Date', 'Transport Type'])
# #save as csv and look at it
# change_dataframe_road_nz_ref.to_csv('intermediate_data/analysis_single_use/change_dataframe_road_nz_ref.csv', index=False)
# os.startfile(os.path.normpath('intermediate_data/analysis_single_use/change_dataframe_road_nz_ref.csv'))
# %%
