#take in output data and do basic visualisationh and analysis

#%%
#set working directory as one folder back so that config works
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
from runpy import run_path
exec(open("config/config.py").read())#usae this to load libraries and set variables. Feel free to edit that file as you need

import plotly
import plotly.express as px
pd.options.plotting.backend = "plotly"#set pandas backend to plotly plotting instead of matplotlib
import plotly.io as pio
# pio.renderers.default = "browser"#allow plotting of graphs in the interactive notebook in vscode #or set to notebook

#%%
#compare model output to 8th edition output. If there are any differences, print them
#laod output from 8th edition
model_output = pd.read_csv('output_data/model_output_detailed/{}'.format(model_output_file_name))
model_output_8th = pd.read_csv('intermediate_data/activity_efficiency_energy_road_stocks.csv')

#%%
#keep only columns in model_output_8th
model_output = model_output[model_output.columns.intersection(model_output_8th.columns)]

#%%
#filter for data within the same years of each dataset
model_output = model_output[model_output['Year'].isin(model_output_8th['Year'])]
model_output_8th = model_output_8th[model_output_8th['Year'].isin(model_output['Year'])]

#create column in both datasets that states the dataset
model_output['Dataset'] = '9th'
model_output_8th['Dataset'] = '8th'

#concatenate data together
model_output_concat = pd.concat([model_output, model_output_8th], axis=0)
#%%
#plot energy use
#sum up data for energy use by year, medium, economy, transport type, vehicle type and drive in both scenarios for each dataset
model_output_concat_sum = model_output_concat.groupby(['Year', 'Scenario', 'Economy', 'Medium', 'Dataset', 'Transport Type', 'Vehicle Type', 'Drive'], as_index=False).sum()

#join together the  'Transport Type', 'Vehicle Type', 'Drive' and 'Scenario' columns
model_output_concat_sum['TransportType_VehicleType_Drive_Scenario'] = model_output_concat_sum['Transport Type'] + '_' + model_output_concat_sum['Vehicle Type'] + '_' + model_output_concat_sum['Drive'] + '_' + model_output_concat_sum['Scenario']

# #drop cols we joined together
# model_output_concat_sum = model_output_concat_sum.drop(['Transport Type', 'Vehicle Type', 'Drive', 'Scenario'], axis=1)

#filter out data in years that are not in both datasets
model_output_concat_sum = model_output_concat_sum[model_output_concat_sum['Year'].isin(model_output_8th['Year'])]
model_output_concat_sum = model_output_concat_sum[model_output_concat_sum['Year'].isin(model_output['Year'])]
#%%
################################################################################################################################################################

title = 'Compared to 8th Energy use by year, economy, in both scenarios, for each drive, USA and PRC removed'

model_output_concat_sum_other_regions = model_output_concat_sum[~model_output_concat_sum['Economy'].isin(['05_PRC', '20_USA'])]

#plot
fig = px.line(model_output_concat_sum_other_regions, x="Year", y="Energy", color="TransportType_VehicleType_Drive_Scenario", line_dash='Dataset', facet_col="Economy", facet_col_wrap=7, title=title)#, #facet_col="Economy",
             #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles


plotly.offline.plot(fig, filename='./plotting_output/' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
fig.write_image("./plotting_output/static/" + title + '.png', scale=1, width=2000, height=800)


#%%
################################################################################
################################################################################
title = 'Compared to 8th Energy use by year, economy, drive in both scenarios'

#plot
fig = px.line(model_output_concat_sum, x="Year", y="Energy", color="TransportType_VehicleType_Drive_Scenario", line_dash='Dataset', facet_col="Economy", facet_col_wrap=7, title=title)#, #facet_col="Economy",
             #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles

plotly.offline.plot(fig, filename='./plotting_output/' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
fig.write_image("./plotting_output/static/" + title + '.png', scale=1, width=2000, height=800)

#%%
################################################################################################################################################################
title = 'Compared to 8th Activity by year, economy, in both scenarios, for each drive, USA and PRC removed'

model_output_concat_sum_other_regions = model_output_concat_sum[~model_output_concat_sum['Economy'].isin(['05_PRC', '20_USA'])]

#plot
fig = px.line(model_output_concat_sum_other_regions, x="Year", y="Activity", color="TransportType_VehicleType_Drive_Scenario", line_dash='Dataset', facet_col="Economy", facet_col_wrap=7, title=title)#, #facet_col="Economy",
             #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles


plotly.offline.plot(fig, filename='./plotting_output/' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
fig.write_image("./plotting_output/static/" + title + '.png', scale=1, width=2000, height=800)

#%%
################################################################################
################################################################################
title = 'Compared to 8th Activity use by year, economy, drive in both scenarios'

#plot
fig = px.line(model_output_concat_sum, x="Year", y="Activity", color="TransportType_VehicleType_Drive_Scenario", line_dash='Dataset', facet_col="Economy", facet_col_wrap=7, title=title)#, #facet_col="Economy",
             #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles


plotly.offline.plot(fig, filename='./plotting_output/' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
fig.write_image("./plotting_output/static/" + title + '.png', scale=1, width=2000, height=800)


#%%
################################################################################################################################################################
title = 'Compared to 8th Stocks by year, economy, in both scenarios, for each drive, USA and PRC removed'

#filte rfor road only
model_output_concat_sum_stocks = model_output_concat_sum[model_output_concat_sum['Medium'].isin(['road'])]

model_output_concat_sum_stocks_other_regions = model_output_concat_sum_stocks[~model_output_concat_sum_stocks['Economy'].isin(['05_PRC', '20_USA'])]

#plot
fig = px.line(model_output_concat_sum_stocks_other_regions, x="Year", y="Stocks", color="TransportType_VehicleType_Drive_Scenario", line_dash='Dataset', facet_col="Economy", facet_col_wrap=7, title=title)#, #facet_col="Economy",
             #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles

plotly.offline.plot(fig, filename='./plotting_output/' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
fig.write_image("./plotting_output/static/" + title + '.png', scale=1, width=2000, height=800)

#%%
################################################################################################################################################################
title = 'Compared to 8th Stocks by year, economy, in both scenarios, for each drive'

#plot
fig = px.line(model_output_concat_sum_stocks, x="Year", y="Stocks", color="TransportType_VehicleType_Drive_Scenario", line_dash='Dataset', facet_col="Economy", facet_col_wrap=7, title=title)#, #facet_col="Economy",
             #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles

plotly.offline.plot(fig, filename='./plotting_output/' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
fig.write_image("./plotting_output/static/" + title + '.png', scale=1, width=2000, height=800)

#%%
#TO DO
################################################################################################################################################################
#plot the data for the whole of apec to try understand what we are over/under exagerating compare to 8th.
#first plot energy use by drive type, vehicle type split into transport types

title = 'Compared to 8th Energy use by year, drive, vehicle in each ttype'
#filter for scenario = reference
model_output_concat_sum_ref = model_output_concat_sum[model_output_concat_sum['Scenario'] == 'Reference']
#remove non specified from transport type
model_output_concat_sum_ref = model_output_concat_sum_ref[model_output_concat_sum_ref['Transport Type'] != 'nonspecified']
#sum data
model_output_concat_sum_ref = model_output_concat_sum_ref.groupby(['Year', 'Dataset', 'Transport Type', 'Drive', 'Vehicle Type'], as_index=False).sum()

#create a column which concats the drive type and fuel type
model_output_concat_sum_ref['Drive_Vehicle'] = model_output_concat_sum_ref['Vehicle Type'] + '_' + model_output_concat_sum_ref['Drive']

#plot
fig = px.line(model_output_concat_sum_ref, x="Year", y="Energy", color="Drive_Vehicle", line_dash='Dataset', facet_col="Transport Type", facet_col_wrap=3, title=title)

plotly.offline.plot(fig, filename='./plotting_output/' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
fig.write_image("./plotting_output/static/" + title + '.png', scale=1, width=2000, height=1500)

#%%
title = 'Compared to 8th Activity by year, drive, vehicle in each ttype'

#plot
fig = px.line(model_output_concat_sum_ref, x="Year", y="Activity", color="Drive_Vehicle", line_dash='Dataset', facet_col="Transport Type", facet_col_wrap=3, title=title)

plotly.offline.plot(fig, filename='./plotting_output/' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
fig.write_image("./plotting_output/static/" + title + '.png', scale=1, width=2000, height=1500)

#%%
title = 'Compared to 8th Stocks by year, drive, vehicle in each ttype'

#plot
fig = px.line(model_output_concat_sum_ref, x="Year", y="Stocks", color="Drive_Vehicle", line_dash='Dataset', facet_col="Transport Type", facet_col_wrap=3, title=title)

plotly.offline.plot(fig, filename='./plotting_output/' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
fig.write_image("./plotting_output/static/" + title + '.png', scale=1, width=2000, height=1500)

#%%