#take in output data and do basic visualisationh and analysis

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
#compare model output to 8th edition output. If there are any differences, print them
#laod output from 8th edition
model_output_with_fuels = pd.read_csv('output_data/model_output_with_fuels/{}'.format(model_output_file_name))
model_output_8th = pd.read_csv("intermediate_data/cleaned_input_data/energy_with_fuel.csv")
# #%%
# #keep only columns in model_output_8th
# model_output = model_output_with_fuels[model_output_with_fuels.columns.intersection(model_output_8th.columns)]

#%%
# #filter for data within the same years of each dataset
# model_output_with_fuels = model_output_with_fuels[model_output_with_fuels['Year'].isin(model_output_8th['Year'])]
# model_output_8th = model_output_8th[model_output_8th['Year'].isin(model_output_with_fuels['Year'])]

#create column in both datasets that states the dataset
model_output_with_fuels['Dataset'] = '9th'
model_output_8th['Dataset'] = '8th'

#concatenate data together
model_output_concat = pd.concat([model_output_with_fuels, model_output_8th], axis=0)
#%%
#plot energy use
#sum up data for energy use by year, medium, economy, transport type, vehicle type and drive in both scenarios for each dataset
model_output_concat_sum = model_output_concat.groupby(['Year', 'Scenario', 'Economy', 'Medium', 'Dataset', 'Transport Type', 'Vehicle Type', 'Drive', 'Fuel'], as_index=False).sum()

#join together the  'Transport Type', 'Vehicle Type', 'Drive' and 'Scenario' columns
model_output_concat_sum['TransportType_VehicleType_Drive_Scenario_Fuel'] = model_output_concat_sum['Transport Type'] + '_' + model_output_concat_sum['Vehicle Type'] + '_' + model_output_concat_sum['Drive'] + '_' + model_output_concat_sum['Scenario'] + '_' + model_output_concat_sum['Fuel']

#drop cols we joined together
# model_output_concat_sum = model_output_concat_sum.drop(['Transport Type', 'Vehicle Type', 'Drive', 'Scenario', 'Fuel'], axis=1)

#%%
################################################################################################################################################################

title='Energy use by year, economy, in both scenarios, for each drive, USA and PRC removed'

model_output_concat_sum_other_regions = model_output_concat_sum[~model_output_concat_sum['Economy'].isin(['05_PRC', '20_USA'])]

#plot
fig = px.line(model_output_concat_sum_other_regions, x="Year", y="Energy", color="TransportType_VehicleType_Drive_Scenario_Fuel", line_dash='Dataset', facet_col="Economy", facet_col_wrap=7, title=title)#, #facet_col="Economy",
             #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles

plotly.offline.plot(fig, filename='./plotting_output/' + title + '.html')
fig.write_image("./plotting_output/static/" + title + '.png', scale=1, width=2000, height=1500)

#%%
################################################################################
################################################################################
title='Energy use by year, economy, fuel in both scenarios'

#plot
fig = px.line(model_output_concat_sum, x="Year", y="Energy", color="TransportType_VehicleType_Drive_Scenario_Fuel", line_dash='Dataset', facet_col="Economy", facet_col_wrap=7, title=title)#, #facet_col="Economy",
             #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles

plotly.offline.plot(fig, filename='./plotting_output/' + title + '.html')
fig.write_image("./plotting_output/static/" + title + '.png', scale=1, width=2000, height=1500)

#%%
################################################################################################################################################################

#filter for only passenger light vehicles so the graphs are easier to read
model_output_concat_sum_lv = model_output_concat_sum[model_output_concat_sum['Vehicle Type'] == 'lv']
model_output_concat_sum_lv = model_output_concat_sum_lv[model_output_concat_sum_lv['Transport Type'] == 'passenger']

title='Energy use by year, economy, fuel in both scenarios LV only'

#plot
fig = px.line(model_output_concat_sum_lv, x="Year", y="Energy", color="TransportType_VehicleType_Drive_Scenario_Fuel", line_dash='Dataset', facet_col="Economy", facet_col_wrap=7, title=title)#, #facet_col="Economy",
             #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles

plotly.offline.plot(fig, filename='./plotting_output/' + title + '.html')
fig.write_image("./plotting_output/static/" + title + '.png', scale=1, width=2000, height=1500)
# %%
