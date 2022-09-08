#take in detailed output data and print out any useful metrics/statisitcs to summarise the reults of the model. the intention is that the output willbe easy to view through the command line, and that the output will be saved to a file for later viewing.

#%%
#set working directory as one folder back so that config works
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
execfile("config/config.py")#usae this to load libraries and set variables. Feel free to edit that file as you need

# pio.renderers.default = "browser"#allow plotting of graphs in the interactive notebook in vscode #or set to notebook
import plotly
import plotly.express as px
pd.options.plotting.backend = "matplotlib"
import plotly.io as pio
pio.renderers.default = "browser"#allow plotting of graphs in the interactive notebook in vscode #or set to notebook

import matplotlib.pyplot as plt
plt.rcParams['figure.facecolor'] = 'w'
#%%
#load data in
model_output_detailed = pd.read_csv('output_data/model_output_detailed/{}'.format(model_output_file_name))

#%%
#%%
#%%
#%%
#FILTER FOR SCENARIO OF INTEREST
model_output_detailed = model_output_detailed[model_output_detailed['Scenario']==SCENARIO_OF_INTEREST]
#%%

#for all the following, filter only for medium = road since the input data of interest is only for road
model_output_detailed = model_output_detailed[model_output_detailed['Medium'] == 'road']
################################################################################################################################################################

#%%
#plot the average OCCUPANCY RATE by year, transport type and vehicel type 

#avergae occupancy rate for each transport type and vehicle type for each year
model_output_occ = model_output_detailed.groupby(['Year', 'Transport Type', 'Vehicle Type'])['Occupancy_or_load'].mean().reset_index()
model_output_occ_PASS = model_output_occ[model_output_occ['Transport Type']=='passenger']
model_output_occ_FR = model_output_occ[model_output_occ['Transport Type']=='freight']

title='Average OCCUPANCY RATE by year and vehicle type for passenger'
#plot
fig, ax = plt.subplots()
for key, grp in model_output_occ_PASS.groupby(['Vehicle Type']):
    ax = grp.plot(ax=ax, kind='line', x='Year', y='Occupancy_or_load', label=key)
plt.title(title)
plt.show()

title='Average OCCUPANCY RATE by year and vehicle type for freight'
#plot
fig, ax = plt.subplots()
for key, grp in model_output_occ_PASS.groupby(['Vehicle Type']):
    ax = grp.plot(ax=ax, kind='line', x='Year', y='Occupancy_or_load', label=key)
plt.title(title)
plt.show()

#%%
################################################################################################################################################################
title = 'OCCUPANCY RATE by year, transport type, vehicle type and economy'

model_output_occ = model_output_detailed.groupby(['Economy', 'Year', 'Transport Type', 'Vehicle Type'])['Occupancy_or_load'].mean().reset_index()

#plot
fig = px.line(model_output_occ, x="Year", y="Occupancy_or_load", color="Vehicle Type", line_dash='Transport Type', facet_col="Economy", facet_col_wrap=7, title=title)#, #facet_col="Economy",
             #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles

plotly.offline.plot(fig, filename='./plotting_output/' + title + '.html')
fig.write_image("./plotting_output/static/" + title + '.png', scale=1, width=2000, height=800)

################################################################################################################################################################
#%%
#plot the average Turnover RATE by year, transport type and vehicel type 

#avergae Turnover rate for each transport type and vehicle type for each year
model_output_t = model_output_detailed.groupby(['Year', 'Transport Type', 'Vehicle Type'])['Turnover_rate'].mean().reset_index()
model_output_t_PASS = model_output_t[model_output_t['Transport Type']=='passenger']
model_output_t_FR = model_output_t[model_output_t['Transport Type']=='freight']

title='Average Turnover_rate by year and vehicle type for passenger'
#plot
fig, ax = plt.subplots()
for key, grp in model_output_t_PASS.groupby(['Vehicle Type']):
    ax = grp.plot(ax=ax, kind='line', x='Year', y='Turnover_rate', label=key)
plt.title(title)
plt.show()

title='Average Turnover_rate by year and vehicle type for freight'
#plot
fig, ax = plt.subplots()
for key, grp in model_output_t_PASS.groupby(['Vehicle Type']):
    ax = grp.plot(ax=ax, kind='line', x='Year', y='Turnover_rate', label=key)
plt.title(title)
plt.show()

#%%
################################################################################################################################################################
title = 'Turnover RATE by year, transport type, vehicle type and economy'

model_output_t = model_output_detailed.groupby(['Economy', 'Year', 'Transport Type', 'Vehicle Type'])['Turnover_rate'].mean().reset_index()

#plot
fig = px.line(model_output_t, x="Year", y="Turnover_rate", color="Vehicle Type", line_dash='Transport Type', facet_col="Economy", facet_col_wrap=7, title=title)#, #facet_col="Economy",
             #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles


plotly.offline.plot(fig, filename='./plotting_output/' + title + '.html')
fig.write_image("./plotting_output/static/" + title + '.png', scale=1, width=2000, height=800)

#%%
################################################################################################################################################################
#plot the average New_vehicle_efficiency by year, transport type, vehicel type and drive type
model_output_new_v_eff = model_output_detailed.groupby(['Year', 'Transport Type', 'Vehicle Type', 'Drive'])['New_vehicle_efficiency'].mean().reset_index()

for v_type in model_output_new_v_eff['Vehicle Type'].unique():
    
    #plot transport type = pass
    model_output_new_v_eff_pass = model_output_new_v_eff[(model_output_new_v_eff['Transport Type']=='passenger') & (model_output_new_v_eff['Vehicle Type']==v_type)]
    if len(model_output_new_v_eff_pass) > 0:
        title='Average New_vehicle_efficiency for passenger, {}'.format(v_type)
        
        #plot
        fig, ax = plt.subplots()
        for key, grp in model_output_new_v_eff_pass.groupby(['Drive']):

            ax = grp.plot(ax=ax, kind='line', x='Year', y='New_vehicle_efficiency', label=key)
        plt.title(title)
        plt.show()

    #plot transport type = freight
    model_output_new_v_eff_freight = model_output_new_v_eff[(model_output_new_v_eff['Transport Type']=='freight') & (model_output_new_v_eff['Vehicle Type']==v_type)]
    if len(model_output_new_v_eff_freight) > 0:
        title='Average New_vehicle_efficiency for freight, {}'.format(v_type)

        #plot
        fig, ax = plt.subplots()
        for key, grp in model_output_new_v_eff_freight.groupby(['Drive']):
            if len(grp) == 0:
                continue
            ax = grp.plot(ax=ax, kind='line', x='Year', y='New_vehicle_efficiency', label=key)
        plt.title(title)
        plt.show()


#%%
################################################################################################################################################################
title = 'New_vehicle_efficiency by year, transport type, vehicle type, drive and economy'

model_output_v_eff = model_output_detailed.groupby(['Economy', 'Year', 'Drive', 'Transport Type', 'Vehicle Type'])['New_vehicle_efficiency'].mean().reset_index()

model_output_v_eff['Transport_Vehicle_type'] = model_output_v_eff['Transport Type'] + '_' + model_output_v_eff['Vehicle Type']

#plot
fig = px.line(model_output_v_eff, x="Year", y="New_vehicle_efficiency", color="Transport_Vehicle_type", line_dash='Drive', facet_col="Economy", facet_col_wrap=7, title=title)#, #facet_col="Economy",
             #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles

plotly.offline.plot(fig, filename='./plotting_output/' + title + '.html')
fig.write_image("./plotting_output/static/" + title + '.png', scale=1, width=2000, height=800)

################################################################################################################################################################

#%%
#plot avged Vehicle_sales_share by vehicle type by drive 
model_output_v_sales_share = model_output_detailed.groupby(['Year', 'Transport Type', 'Vehicle Type', 'Drive'])['Vehicle_sales_share'].mean().reset_index()

for v_type in model_output_v_sales_share['Vehicle Type'].unique():
    
    #plot transport type = pass
    model_output_v_sales_share_pass = model_output_v_sales_share[(model_output_v_sales_share['Transport Type']=='passenger') & (model_output_v_sales_share['Vehicle Type']==v_type)]
    if len(model_output_v_sales_share_pass) > 0:
        title='Average Vehicle_sales_share for passenger, {}'.format(v_type)

        #plot
        fig, ax = plt.subplots()
        for key, grp in model_output_v_sales_share_pass.groupby(['Drive']):
            if len(grp) == 0:
                continue
            ax = grp.plot(ax=ax, kind='line', x='Year', y='Vehicle_sales_share', label=key)
        plt.title(title)
        plt.show()

    #plot transport type = freight
    model_output_v_sales_share_freight = model_output_v_sales_share[(model_output_v_sales_share['Transport Type']=='freight') & (model_output_v_sales_share['Vehicle Type']==v_type)]

    if len(model_output_v_sales_share_freight) > 0:
        title='Average Vehicle_sales_share for freight, {}'.format(v_type)

        #plot
        fig, ax = plt.subplots()
        for key, grp in model_output_v_sales_share_freight.groupby(['Drive']):
            if len(grp) == 0:
                continue
            ax = grp.plot(ax=ax, kind='line', x='Year', y='Vehicle_sales_share', label=key)
        plt.title(title)
        plt.show()

#%%
################################################################################################################################################################
title = 'Vehicle_sales_share by year, transport type, vehicle type, drive and economy'

model_output_sales = model_output_detailed.groupby(['Economy', 'Year', 'Drive', 'Transport Type', 'Vehicle Type'])['Vehicle_sales_share'].mean().reset_index()

model_output_sales['Transport_Vehicle_type'] = model_output_sales['Transport Type'] + '_' + model_output_sales['Vehicle Type']

#plot
fig = px.line(model_output_sales, x="Year", y="Vehicle_sales_share", color="Transport_Vehicle_type", line_dash='Drive', facet_col="Economy", facet_col_wrap=7, title=title)#, #facet_col="Economy",
             #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles

plotly.offline.plot(fig, filename='./plotting_output/' + title + '.html')
fig.write_image("./plotting_output/static/" + title + '.png', scale=1, width=2000, height=800)

################################################################################################################################################################
#%%
#plot travel km per stock by year, transport type, vehicle type
model_output_travel_km_per_stock = model_output_detailed.groupby(['Year', 'Transport Type', 'Vehicle Type'])['Travel_km_per_stock'].mean().reset_index()

model_output_travel_km_per_stock_pass = model_output_travel_km_per_stock[model_output_travel_km_per_stock['Transport Type']=='passenger']
model_output_travel_km_per_stock_freight = model_output_travel_km_per_stock[model_output_travel_km_per_stock['Transport Type']=='freight']

title='Average Travel_km_per_stock by year, vehicle type and drive type for passenger'

#plot
fig, ax = plt.subplots()
for key, grp in model_output_travel_km_per_stock_pass.groupby(['Vehicle Type']):
    ax = grp.plot(ax=ax, kind='line', x='Year', y='Travel_km_per_stock', label=key)
plt.title(title)
plt.show()

title='Average Travel_km_per_stock by year, vehicle type and drive type for freight'

#plot
fig, ax = plt.subplots()
for key, grp in model_output_travel_km_per_stock_freight.groupby(['Vehicle Type']):
    ax = grp.plot(ax=ax, kind='line', x='Year', y='Travel_km_per_stock', label=key)
plt.title(title)
plt.show()

#%%
################################################################################################################################################################
title = 'Average Travel_km_per_stock by year, transport type, vehicle type and economy'

model_output_trav_p_stock = model_output_detailed.groupby(['Economy', 'Year',  'Transport Type', 'Vehicle Type'])['Travel_km_per_stock'].mean().reset_index()

#plot
fig = px.line(model_output_trav_p_stock, x="Year", y="Travel_km_per_stock", color="Vehicle Type", line_dash='Transport Type', facet_col="Economy", facet_col_wrap=7, title=title)#, #facet_col="Economy",
             #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles

plotly.offline.plot(fig, filename='./plotting_output/' + title + '.html')
fig.write_image("./plotting_output/static/" + title + '.png', scale=1, width=2000, height=800)


################################################################################################################################################################


#%%













